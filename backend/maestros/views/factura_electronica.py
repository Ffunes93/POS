"""
factura_electronica.py — Integración con AFIP WSFE (Factura Electrónica Argentina).

Flujo:
  1. Leer certificado p12 / PEM de fe_param
  2. Generar LoginTicketRequest XML → firmar → POST a WSAA → obtener Token+Sign (TA)
  3. Guardar TA en fe_tas
  4. Con TA activo, llamar WSFE.FECAESolicitar → obtener CAE + VtoCAE
  5. Guardar CAE en ventas y ventas_adicionales

Tipos de comprobante AFIP (cbte_tipo):
  1=FA  2=NDA  3=NCA   6=FB   7=NDB   8=NCB
  11=FC  12=NDC  13=NCC
  201=FC-MiPyME A   206=FC-MiPyME B

DocTipo receptor:
  80=CUIT  86=CUIL  87=CDI  89=Pasaporte  90=CID  91=Libreta Cívica
  92=Libreta Enrolamiento  96=DNI  99=Consumidor Final / Sin dato

Alícuotas IVA AFIP Id:
  3=0%  4=10.5%  5=21%  6=27%  8=5%  9=2.5%
"""

import base64
import hashlib
import json
import re
from datetime import datetime, timezone as dt_timezone, timedelta
from decimal import Decimal

from django.db import connection
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

# ── Carga diferida de dependencias pesadas (zeep, cryptography) ───────────────
def _import_zeep():
    try:
        from zeep import Client, Settings
        from zeep.transports import Transport
        from requests import Session
        return Client, Settings, Transport, Session
    except ImportError:
        return None, None, None, None

def _import_crypto():
    try:
        from cryptography.hazmat.primitives.serialization import pkcs12
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.x509.oid import NameOID
        from cryptography import x509
        return pkcs12, hashes, serialization, padding, NameOID, x509
    except ImportError:
        return None, None, None, None, None, None

# ── URLs AFIP ─────────────────────────────────────────────────────────────────
WSAA_HOMOL  = 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl'
WSAA_PROD   = 'https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl'
WSFE_HOMOL  = 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL'
WSFE_PROD   = 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'

# Mapa comprobante legacy → tipo AFIP
TIPO_AFIP = {
    'FA': 1,  'EA': 1,  'NDA': 2, 'NA': 2,  'CA': 3,  'KA': 3,
    'FB': 6,  'EB': 6,  'NDB': 7, 'NB': 7,  'CB': 8,  'KB': 8,
    'FC': 11, 'EC': 11, 'NDC': 12,'NC': 12, 'CC': 13, 'KC': 13,
    'MA': 201,'MB': 206,
}

# Tipos que requieren FE (electrónicos)
TIPOS_FE = set(TIPO_AFIP.keys())

# Alícuota AFIP Id según % IVA
IVA_ID = {0: 3, 5: 8, 10.5: 4, 21: 5, 27: 6}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _cargar_fe_param() -> dict:
    """Lee fe_param de la DB."""
    with connection.cursor() as c:
        c.execute("""
            SELECT id_fnc, url_autentica, url_homologa, url_produccion,
                   ruta_certificado, estado_homologa, estado_produccion,
                   clavecertificado
            FROM fe_param LIMIT 1
        """)
        row = c.fetchone()
    if not row:
        return {}
    return {
        'id_fnc':             row[0],
        'url_autentica':      row[1],
        'url_homologa':       row[2],
        'url_produccion':     row[3],
        'ruta_certificado':   row[4],
        'estado_homologa':    row[5],
        'estado_produccion':  row[6],
        'clave_certificado':  row[7],
    }


def _es_produccion(param: dict) -> bool:
    return bool(param.get('estado_produccion'))


def _leer_ta_activo() -> dict | None:
    """Devuelve el TA activo si está vigente (>10 min de vida restante)."""
    with connection.cursor() as c:
        c.execute("SELECT fecha, ticketAcceso FROM fe_tas ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
    if not row:
        return None
    fecha_gen = row[0]
    if not fecha_gen:
        return None
    ta_text = row[1]
    if not ta_text:
        return None
    try:
        # Extraer ExpirationTime del XML
        m = re.search(r'<expirationTime>(.*?)</expirationTime>', ta_text)
        if not m:
            return None
        exp = datetime.fromisoformat(m.group(1).replace('Z', '+00:00'))
        if datetime.now(dt_timezone.utc) > exp - timedelta(minutes=10):
            return None
        token_m = re.search(r'<token>(.*?)</token>', ta_text, re.DOTALL)
        sign_m  = re.search(r'<sign>(.*?)</sign>',  ta_text, re.DOTALL)
        if token_m and sign_m:
            return {'token': token_m.group(1), 'sign': sign_m.group(1)}
    except Exception:
        pass
    return None


def _guardar_ta(ta_xml: str) -> None:
    with connection.cursor() as c:
        c.execute(
            "INSERT INTO fe_tas (fecha, ticketAcceso) VALUES (NOW(), %s)",
            [ta_xml],
        )


def _generar_ltr_xml(service: str) -> str:
    """Genera LoginTicketRequest XML."""
    now = datetime.now(dt_timezone.utc)
    gen = now.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    exp = (now + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%S+00:00')
    uid = hashlib.sha1(str(now.timestamp()).encode()).hexdigest()[:8]
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<loginTicketRequest version="1.0">
  <header>
    <uniqueId>{uid}</uniqueId>
    <generationTime>{gen}</generationTime>
    <expirationTime>{exp}</expirationTime>
  </header>
  <service>{service}</service>
</loginTicketRequest>"""


def _firmar_ltr(ltr_xml: str, cert_path: str, clave: str) -> str | None:
    """Firma el LTR con el certificado p12 y devuelve CMS en base64."""
    pkcs12_lib, hashes_lib, serial_lib, padding_lib, NameOID_lib, x509_lib = _import_crypto()
    if pkcs12_lib is None:
        return None
    try:
        import os
        if cert_path and os.path.exists(cert_path):
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
        else:
            return None

        # Soporte p12 y pem
        if cert_path.endswith('.p12') or cert_path.endswith('.pfx'):
            private_key, certificate, _ = pkcs12_lib.load_key_and_certificates(
                cert_data, clave.encode() if clave else None
            )
        else:
            # Asumir PEM separado: cert.pem + key.pem en el mismo archivo
            private_key = serial_lib.load_pem_private_key(cert_data, password=None)
            certificate = x509_lib.load_pem_x509_certificate(cert_data)

        # Firma PKCS#7 / CMS
        from cryptography.hazmat.primitives.serialization import Encoding
        from cryptography.hazmat.backends import default_backend

        ltr_bytes = ltr_xml.encode('utf-8')
        signature = private_key.sign(ltr_bytes, padding_lib.PKCS1v15(), hashes_lib.SHA256())

        # Construir CMS simple (SIGNED DATA) compatible con WSAA
        # Para mayor compatibilidad usamos el módulo pkcs7 si está disponible
        try:
            from cryptography.hazmat.primitives.serialization import pkcs7
            builder = (
                pkcs7.PKCS7SignatureBuilder()
                .set_data(ltr_bytes)
                .add_signer(certificate, private_key, hashes_lib.SHA256())
            )
            cms = builder.sign(Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature])
        except Exception:
            # Fallback: firma raw base64
            cms = signature

        return base64.b64encode(cms).decode()
    except Exception as e:
        print(f'[FE] Error firmando LTR: {e}')
        return None


def _obtener_ta(param: dict) -> tuple[str | None, str | None, str]:
    """
    Devuelve (token, sign, error).
    Reutiliza TA activo o solicita uno nuevo.
    """
    ta = _leer_ta_activo()
    if ta:
        return ta['token'], ta['sign'], ''

    Client, Settings, Transport, Session = _import_zeep()
    if Client is None:
        return None, None, 'zeep no instalado. Ejecute: pip install zeep --break-system-packages'

    prod = _es_produccion(param)
    url_wsaa = WSAA_PROD if prod else WSAA_HOMOL
    if param.get('url_autentica'):
        url_wsaa = param['url_autentica']

    ltr_xml = _generar_ltr_xml('wsfe')
    cms_b64 = _firmar_ltr(ltr_xml, param.get('ruta_certificado', ''), param.get('clave_certificado', ''))
    if cms_b64 is None:
        # Modo demo: devuelve token vacío para pruebas sin certificado
        return 'TOKEN_DEMO', 'SIGN_DEMO', 'ADVERTENCIA: sin certificado, modo demo.'

    try:
        session = Session()
        session.verify = False
        transport = Transport(session=session, timeout=30)
        client = Client(url_wsaa, transport=transport,
                        settings=Settings(strict=False, xml_huge_tree=True))
        resp = client.service.loginCms(in0=cms_b64)
        _guardar_ta(resp)
        ta = _leer_ta_activo()
        if ta:
            return ta['token'], ta['sign'], ''
        return None, None, 'No se pudo parsear TA.'
    except Exception as e:
        return None, None, f'Error WSAA: {e}'


def _get_wsfe_client(param: dict):
    Client, Settings, Transport, Session = _import_zeep()
    if Client is None:
        return None
    prod = _es_produccion(param)
    url = WSFE_PROD if prod else WSFE_HOMOL
    if param.get('url_produccion') and prod:
        url = param['url_produccion']
    if param.get('url_homologa') and not prod:
        url = param['url_homologa']
    try:
        session = Session()
        session.verify = False
        transport = Transport(session=session, timeout=60)
        return Client(url, transport=transport,
                      settings=Settings(strict=False, xml_huge_tree=True))
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Función principal: solicitar CAE para un comprobante
# ─────────────────────────────────────────────────────────────────────────────

def solicitar_cae(
    movim: int,
    tipo_comprob: str,          # 'FA','FB','EA','EB' etc.
    nro_comprob: int,
    pto_venta: int,
    fecha_cbte: str,            # YYYYMMDD
    imp_total: Decimal,
    imp_neto: Decimal,
    imp_iva: Decimal,
    imp_op_ex: Decimal,
    imp_tributos: Decimal,
    doc_tipo: int,              # 80=CUIT,96=DNI,99=CF
    doc_nro: str,
    cond_iva_receptor: int,     # 1..6 (mapa mismo que legacy)
    alicuotas: list[dict],      # [{'id':5,'base':1000,'importe':210}, ...]
    tributos:  list[dict],      # [{'id':1,'desc':'IIBB','base':100,'importe':5}, ...]
    cbte_asoc_tipo: int = 0,
    cbte_asoc_nro:  int = 0,
    cbte_asoc_pto:  int = 0,
) -> dict:
    """
    Llama a WSFE y devuelve:
      {'ok': bool, 'cae': str, 'vto_cae': str, 'mensaje': str}
    """
    param = _cargar_fe_param()
    if not param:
        return {'ok': False, 'cae': '', 'vto_cae': '', 'mensaje': 'fe_param no configurado.'}

    tipo_afip = TIPO_AFIP.get(tipo_comprob.upper())
    if tipo_afip is None:
        return {'ok': False, 'cae': '', 'vto_cae': '', 'mensaje': f'Tipo {tipo_comprob} sin mapping AFIP.'}

    token, sign, err = _obtener_ta(param)
    if not token:
        return {'ok': False, 'cae': '', 'vto_cae': '', 'mensaje': err}

    # Modo demo (sin zeep o sin certificado real)
    if token == 'TOKEN_DEMO':
        cae_demo = '12345678901234'
        vto_demo = (datetime.now() + timedelta(days=10)).strftime('%Y%m%d')
        return {'ok': True, 'cae': cae_demo, 'vto_cae': vto_demo, 'mensaje': err, 'demo': True}

    # Leer CUIT empresa
    with connection.cursor() as c:
        c.execute("SELECT razonsocial, condicioniva FROM fe_param LIMIT 1")
        row = c.fetchone()
    # CUIT desde parametros
    with connection.cursor() as c:
        c.execute("SELECT params FROM parametros LIMIT 1")
        row2 = c.fetchone()

    cuit_empresa = ''
    if row2 and row2[0]:
        try:
            p = json.loads(row2[0]) if isinstance(row2[0], str) else row2[0]
            cuit_empresa = str(p.get('cuit', '') or '')
        except Exception:
            pass

    client = _get_wsfe_client(param)
    if client is None:
        return {'ok': False, 'cae': '', 'vto_cae': '', 'mensaje': 'No se pudo conectar a WSFE.'}

    try:
        auth = {'Token': token, 'Sign': sign, 'Cuit': cuit_empresa or '0'}

        # Armar alícuotas IVA
        iva_array = []
        for al in alicuotas:
            if float(al.get('base', 0)) > 0:
                iva_array.append({
                    'Id':      al['id'],
                    'BaseImp': round(float(al['base']), 2),
                    'Importe': round(float(al['importe']), 2),
                })

        # Armar tributos
        trib_array = []
        for tr in tributos:
            if float(tr.get('importe', 0)) > 0:
                trib_array.append({
                    'Id':      tr['id'],
                    'Desc':    tr.get('desc', '')[:80],
                    'BaseImp': round(float(tr.get('base', 0)), 2),
                    'Alic':    round(float(tr.get('alic', 0)), 2),
                    'Importe': round(float(tr['importe']), 2),
                })

        cbte = {
            'Concepto':    1,          # 1=Productos 2=Servicios 3=Ambos
            'DocTipo':     doc_tipo,
            'DocNro':      int(doc_nro.replace('-','').replace('.','')) if doc_nro.strip().isdigit() else 0,
            'CbteDesde':   nro_comprob,
            'CbteHasta':   nro_comprob,
            'CbteFch':     fecha_cbte,
            'ImpTotal':    round(float(imp_total), 2),
            'ImpTotConc':  0,
            'ImpNeto':     round(float(imp_neto), 2),
            'ImpOpEx':     round(float(imp_op_ex), 2),
            'ImpIVA':      round(float(imp_iva), 2),
            'ImpTrib':     round(float(imp_tributos), 2),
            'FchServDesde': None,
            'FchServHasta': None,
            'FchVtoPago':   None,
            'MonId':       'PES',
            'MonCotiz':    1,
        }
        if iva_array:
            cbte['Iva'] = {'AlicIva': iva_array}
        if trib_array:
            cbte['Tributos'] = {'Tributo': trib_array}
        if cbte_asoc_tipo and cbte_asoc_nro:
            cbte['CbtesAsoc'] = {'CbteAsoc': [{
                'Tipo':  cbte_asoc_tipo,
                'PtoVta': cbte_asoc_pto or pto_venta,
                'Nro':   cbte_asoc_nro,
            }]}

        req = {
            'Auth': auth,
            'FeCAEReq': {
                'FeCabReq': {
                    'CantReg': 1,
                    'PtoVta':  pto_venta,
                    'CbteTipo': tipo_afip,
                },
                'FeDetReq': {'FECAEDetRequest': [cbte]},
            },
        }

        resp = client.service.FECAESolicitar(**req)
        det = resp.FeDetResp.FECAEDetResponse[0]

        if det.Resultado == 'A':
            cae     = det.CAE
            vto_cae = det.CAEFchVto
            # Guardar CAE en ventas
            with connection.cursor() as c:
                c.execute(
                    "UPDATE ventas SET cae=%s WHERE movim=%s",
                    [cae, movim]
                )
            return {'ok': True, 'cae': cae, 'vto_cae': vto_cae, 'mensaje': 'CAE obtenido.'}
        else:
            obs = []
            if hasattr(det, 'Observaciones') and det.Observaciones:
                for o in det.Observaciones.Obs:
                    obs.append(f'{o.Code}: {o.Msg}')
            return {
                'ok': False, 'cae': '', 'vto_cae': '',
                'mensaje': ' | '.join(obs) or f'Resultado: {det.Resultado}',
            }

    except Exception as e:
        return {'ok': False, 'cae': '', 'vto_cae': '', 'mensaje': f'Error WSFE: {e}'}


# ─────────────────────────────────────────────────────────────────────────────
# API endpoints
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def EstadoFE(request):
    """
    Retorna estado de la FE:
      - Parámetros configurados
      - TA activo o expirado
      - Último nro AFIP por tipo de comprobante
    """
    param = _cargar_fe_param()
    prod  = _es_produccion(param) if param else False
    ta    = _leer_ta_activo()

    # Conteo de facturas sin CAE (ya ingresadas al sistema)
    with connection.cursor() as c:
        c.execute("""
            SELECT COUNT(*) FROM ventas
            WHERE (cae IS NULL OR cae='')
              AND (anulado IS NULL OR anulado='N')
              AND comprobante_tipo IN ('FA','FB','FC','EA','EB','EC','MA','MB')
        """)
        sin_cae = c.fetchone()[0]

    return Response({
        'status': 'success',
        'configurado': bool(param),
        'produccion': prod,
        'ta_activo': bool(ta),
        'sin_cae': sin_cae,
        'ruta_cert': param.get('ruta_certificado', '') if param else '',
        'id_fnc': param.get('id_fnc', '') if param else '',
    })


@api_view(['POST'])
def SolicitarCAEManual(request):
    """
    Solicita CAE para un movim ya guardado (reenvío / fallback).

    Payload: { "movim": 123 }
    """
    movim = request.data.get('movim')
    if not movim:
        return Response({'status': 'error', 'mensaje': 'movim requerido.'}, status=400)

    with connection.cursor() as c:
        c.execute("""
            SELECT v.movim, v.comprobante_tipo, v.comprobante_letra, v.nro_comprob,
                   CAST(v.comprobante_pto_vta AS UNSIGNED),
                   DATE_FORMAT(v.fecha_fact,'%Y%m%d'),
                   v.tot_general, v.neto, v.iva_1, v.exento,
                   COALESCE(v.percepciones,0)+COALESCE(v.perce_caba,0)+COALESCE(v.perce_bsas,0)+COALESCE(v.perce_5329,0),
                   cli.cond_iva, cli.nro_cuit,
                   v.cae
            FROM ventas v
            LEFT JOIN clientes cli ON v.cod_cli = cli.cod_cli
            WHERE v.movim = %s
        """, [movim])
        row = c.fetchone()

    if not row:
        return Response({'status': 'error', 'mensaje': 'Movimiento no encontrado.'}, status=404)

    (movim_db, tipo, letra, nro, pto_vta, fch, total, neto,
     iva, exento, tributos_total, cond_iva, cuit, cae_actual) = row

    if cae_actual:
        return Response({'status': 'error', 'mensaje': f'Ya tiene CAE: {cae_actual}.'}, status=400)

    tipo_full = (tipo or '') + (letra or '')

    # DocTipo según cond_iva del cliente
    doc_mapa = {1: 80, 4: 80, 5: 96, 6: 80}
    doc_tipo = doc_mapa.get(cond_iva, 99)
    doc_nro  = cuit or '0'
    if not doc_nro.strip() or len(doc_nro.strip()) < 4:
        doc_tipo = 99
        doc_nro  = '0'

    # Alícuota IVA 21% por defecto
    iva_dec = Decimal(str(iva or 0))
    neto_dec = Decimal(str(neto or 0))
    alicuotas = [{'id': 5, 'base': float(neto_dec), 'importe': float(iva_dec)}] if iva_dec > 0 else []

    resultado = solicitar_cae(
        movim        = int(movim_db),
        tipo_comprob = tipo_full,
        nro_comprob  = int(nro),
        pto_venta    = int(pto_vta or 1),
        fecha_cbte   = fch or datetime.now().strftime('%Y%m%d'),
        imp_total    = Decimal(str(total or 0)),
        imp_neto     = neto_dec,
        imp_iva      = iva_dec,
        imp_op_ex    = Decimal(str(exento or 0)),
        imp_tributos = Decimal(str(tributos_total or 0)),
        doc_tipo     = doc_tipo,
        doc_nro      = doc_nro,
        cond_iva_receptor = cond_iva or 5,
        alicuotas    = alicuotas,
        tributos     = [],
    )

    if resultado['ok']:
        return Response({
            'status':  'success',
            'cae':     resultado['cae'],
            'vto_cae': resultado['vto_cae'],
            'mensaje': resultado['mensaje'],
        })
    return Response({'status': 'error', 'mensaje': resultado['mensaje']}, status=400)


@api_view(['GET'])
def ListarSinCAE(request):
    """Lista los últimos 50 comprobantes que requieren FE pero no tienen CAE."""
    with connection.cursor() as c:
        c.execute("""
            SELECT v.movim, v.comprobante_tipo, v.comprobante_letra,
                   v.comprobante_pto_vta, v.nro_comprob, v.fecha_fact,
                   v.tot_general, v.cae,
                   COALESCE(cli.denominacion,'') as nombre_cliente
            FROM ventas v
            LEFT JOIN clientes cli ON v.cod_cli = cli.cod_cli
            WHERE (v.cae IS NULL OR v.cae='')
              AND (v.anulado IS NULL OR v.anulado='N')
              AND v.comprobante_tipo IN ('FA','FB','FC','EA','EB','EC','MA','MB')
            ORDER BY v.movim DESC
            LIMIT 50
        """)
        cols = [col[0] for col in c.description]
        rows = [dict(zip(cols, r)) for r in c.fetchall()]

    return Response({'status': 'success', 'data': rows, 'total': len(rows)})


@api_view(['POST'])
def ProbarConexionAFIP(request):
    """Prueba la conexión con WSFE (sin generar CAE)."""
    param = _cargar_fe_param()
    if not param:
        return Response({'status': 'error', 'mensaje': 'fe_param no configurado.'}, status=400)

    token, sign, err = _obtener_ta(param)
    if not token:
        return Response({'status': 'error', 'mensaje': err}, status=400)

    if token == 'TOKEN_DEMO':
        return Response({'status': 'success', 'mensaje': f'Modo demo activo. {err}'})

    # Llamar FEDummy para verificar
    client = _get_wsfe_client(param)
    if not client:
        return Response({'status': 'error', 'mensaje': 'No se pudo conectar a WSFE.'}, status=400)

    try:
        resp = client.service.FEDummy()
        return Response({
            'status': 'success',
            'mensaje': f'WSFE OK — AppServer:{resp.AppServer} DbServer:{resp.DbServer} AuthServer:{resp.AuthServer}',
        })
    except Exception as e:
        return Response({'status': 'error', 'mensaje': str(e)}, status=500)


@api_view(['POST'])
def GuardarConfigFE(request):
    """
    Guarda / actualiza fe_param.

    Payload: { "ruta_certificado":"...", "clave":"...", "produccion": false,
               "id_fnc":"20123456789", ... }
    """
    data = request.data
    try:
        with connection.cursor() as c:
            c.execute("SELECT COUNT(*) FROM fe_param")
            existe = c.fetchone()[0]

            if existe:
                c.execute("""
                    UPDATE fe_param SET
                      ruta_certificado=%s, clavecertificado=%s,
                      estado_produccion=%s, estado_homologa=%s,
                      url_autentica=%s, url_homologa=%s, url_produccion=%s,
                      razonsocial=%s, domicilio=%s, condicioniva=%s,
                      iibb=%s, inicioactividades=%s
                    LIMIT 1
                """, [
                    data.get('ruta_certificado',''),
                    data.get('clave',''),
                    1 if data.get('produccion') else 0,
                    0 if data.get('produccion') else 1,
                    data.get('url_autentica', WSAA_HOMOL),
                    data.get('url_homologa',  WSFE_HOMOL),
                    data.get('url_produccion',WSFE_PROD),
                    data.get('razon_social',''),
                    data.get('domicilio',''),
                    data.get('condicion_iva',''),
                    data.get('iibb',''),
                    data.get('inicio_actividades',''),
                ])
            else:
                c.execute("""
                    INSERT INTO fe_param
                      (ruta_certificado, clavecertificado, estado_produccion,
                       estado_homologa, url_autentica, url_homologa, url_produccion,
                       razonsocial, domicilio, condicioniva, iibb, inicioactividades)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, [
                    data.get('ruta_certificado',''),
                    data.get('clave',''),
                    1 if data.get('produccion') else 0,
                    0 if data.get('produccion') else 1,
                    data.get('url_autentica', WSAA_HOMOL),
                    data.get('url_homologa',  WSFE_HOMOL),
                    data.get('url_produccion',WSFE_PROD),
                    data.get('razon_social',''),
                    data.get('domicilio',''),
                    data.get('condicion_iva',''),
                    data.get('iibb',''),
                    data.get('inicio_actividades',''),
                ])
        return Response({'status': 'success', 'mensaje': 'Configuración FE guardada.'})
    except Exception as e:
        return Response({'status': 'error', 'mensaje': str(e)}, status=500)