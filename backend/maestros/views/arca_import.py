"""
arca_import.py — Importación masiva de "Mis Comprobantes" desde ARCA.

ARCA expone dos archivos Excel descargables desde Mis Comprobantes:
  - "Mis Comprobantes Recibidos" → Compras (lo que la empresa recibió de proveedores)
  - "Mis Comprobantes Emitidos"  → Ventas  (lo que la empresa emitió a clientes)

Ambos tienen IDÉNTICA estructura de 30 columnas:
  fila 0: título "Mis Comprobantes Recibidos|Emitidos - CUIT XXX"
  fila 1: cabeceras
  fila 2+: datos

Mapeo de columnas → campos del sistema:

  Excel ARCA                          → Compras / Ventas
  ───────────────────────────────────────────────────────────
  Fecha (dd/mm/yyyy)                  → fecha_comprob / fecha_fact
  Tipo ("1 - Factura A", etc.)        → cod_comprob (mapeado) + comprobante_letra
  Punto de Venta                      → comprobante_pto_vta (zfill 4)
  Número Desde                        → nro_comprob
  Cód. Autorización (CAE)             → observac (Compras) / cae (Ventas)
  Nro. Doc. Emisor (Compras)          → cod_prov via Proveedores.nro_cuit
  Nro. Doc. Receptor (Ventas)         → cod_cli  via Clientes.nro_cuit
  Denominación                        → Proveedores.nomfantasia / Clientes.denominacion
  Neto Gravado Total                  → neto
  Total IVA                           → iva_1
  Op. Exentas                         → exento (solo Ventas; Compras no tiene)
  Otros Tributos                      → percepciones (Ventas) / 0 (Compras)
  Imp. Total                          → tot_general (= total)
  Moneda + Tipo Cambio                → si USD, convierte a pesos y deja nota

Reglas de negocio:
  - Si el proveedor/cliente NO existe → se crea automáticamente con CUIT y denominación.
  - Si el comprobante ya existe (mismo tipo+pto_vta+nro+cuit) → se descarta como duplicado.
  - Stock NO se modifica (estos son comprobantes históricos solo a fines impositivos).
  - Costo NO se actualiza por la misma razón.
  - Comprobantes en USD se convierten a pesos al importar usando el tipo de cambio del Excel.
    El monto original se preserva en `observac` para auditoría.
  - Errores fila por fila — un error no detiene el batch. Se devuelve un reporte detallado.

⚠️ Limitaciones conocidas:
  - El Excel NO trae detalle de items, así que las compras importadas no tienen
    `compras_det` asociado. El Libro IVA y la DDJJ funcionan igual porque leen
    cabeceras, pero la rentabilidad por artículo no aplica a estos comprobantes.
  - "Otros Tributos" en compras se descarta (no hay campo equivalente útil).
    El contador puede consultarlo en el Excel original si lo necesita.
"""

from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from ..models import Compras, Ventas, Proveedores, Clientes, Parametros, TipocompCli
from .ventas import _siguiente_movim, _registrar_en_bitacora


# ═════════════════════════════════════════════════════════════════════════════
# MAPEO DE TIPOS DE COMPROBANTE ARCA → SISTEMA
# ═════════════════════════════════════════════════════════════════════════════
#
# ARCA usa códigos numéricos oficiales (RG 1415/03 y modificatorias).
# El sistema usa siglas cortas. El mapeo busca compatibilidad con el resto del
# código (filtros del libro IVA, anulaciones, etc.).
#
# Letra:
#   - A: Responsable Inscripto vendiendo a Resp. Inscripto
#   - B: Responsable Inscripto vendiendo a Consumidor Final / Monotributista
#   - C: Monotributista emitiendo
#   - M: Sujetos a controles fiscales especiales (RG 3668)
#   - E: Operaciones de exportación
# ─────────────────────────────────────────────────────────────────────────────

MAPA_TIPO_ARCA = {
    # Facturas
    1:  ('FA', 'A'),          # Factura A
    6:  ('FB', 'B'),          # Factura B
    11: ('FC', 'C'),          # Factura C  — monotributistas (sin IVA)
    51: ('MA', 'M'),          # Factura M
    19: ('FE', 'E'),          # Factura E (exportación)
    # Notas de Débito
    2:  ('NDA', 'A'),         # Nota de Débito A
    7:  ('NDB', 'B'),         # Nota de Débito B
    12: ('NDC', 'C'),         # Nota de Débito C
    52: ('NDM', 'M'),
    20: ('NDE', 'E'),
    # Notas de Crédito
    3:  ('NCA', 'A'),         # Nota de Crédito A
    8:  ('NCB', 'B'),         # Nota de Crédito B
    13: ('NCC', 'C'),         # Nota de Crédito C
    53: ('NCM', 'M'),
    21: ('NCE', 'E'),
    # Tiques (controlador fiscal) — se asimilan a su factura equivalente
    81: ('FA', 'A'),          # Tique Factura A
    82: ('FB', 'B'),          # Tique Factura B
    83: ('FC', 'C'),          # Tique Factura C  (raro pero posible)
    111: ('TI', 'A'),         # Tique
    112: ('TI', 'A'),         # Tique Nota de Crédito
    113: ('TI', 'A'),         # Tique Nota de Débito
    # Recibos (no van al libro IVA pero los aceptamos para no romper el batch)
    4:  ('RA', 'A'),
    9:  ('RB', 'B'),
    15: ('RC', 'C'),
}


def _parsear_tipo_arca(tipo_str: str):
    """
    Convierte 'N - Descripción' (ej: '1 - Factura A') a (cod_sistema, letra).
    Devuelve (None, None) si no está mapeado.
    """
    if not tipo_str:
        return None, None
    try:
        codigo_arca = int(str(tipo_str).split('-')[0].strip())
    except (ValueError, IndexError):
        return None, None
    return MAPA_TIPO_ARCA.get(codigo_arca, (None, None))


def _parsear_fecha_arca(fecha_str):
    """
    Acepta dd/mm/yyyy (formato ARCA) o un objeto date/datetime.
    Devuelve un objeto date o None si no se puede parsear.
    """
    if isinstance(fecha_str, (date, datetime)):
        return fecha_str if isinstance(fecha_str, date) else fecha_str.date()
    if not fecha_str:
        return None
    try:
        return datetime.strptime(str(fecha_str).strip(), '%d/%m/%Y').date()
    except ValueError:
        try:
            return datetime.strptime(str(fecha_str).strip(), '%Y-%m-%d').date()
        except ValueError:
            return None


def _to_decimal(val, default=Decimal('0')):
    """Convierte cualquier cosa a Decimal, manejando NaN, None, str con coma, etc."""
    if val is None:
        return default
    s = str(val).strip()
    if not s or s.lower() in ('nan', 'none', ''):
        return default
    s = s.replace(',', '.')
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return default


def _to_int(val, default=0):
    """Convierte a int, manejando float, str, None, NaN."""
    try:
        if val is None:
            return default
        s = str(val).strip()
        if not s or s.lower() in ('nan', 'none'):
            return default
        return int(float(s))
    except (ValueError, TypeError):
        return default


def _fmt_cuit_simple(cuit_raw) -> str:
    """11 dígitos con padding. NO valida DV (eso lo hace el contador después)."""
    if cuit_raw is None:
        return ''
    s = ''.join(c for c in str(cuit_raw) if c.isdigit())
    return s.zfill(11)[:11] if s else ''


# ═════════════════════════════════════════════════════════════════════════════
# RESOLUCIÓN DE PROVEEDORES / CLIENTES
# ═════════════════════════════════════════════════════════════════════════════

def _buscar_o_crear_proveedor(cuit: str, denominacion: str) -> int:
    """
    Busca un proveedor por CUIT exacto. Si no existe, lo crea con un nuevo cod_prov.
    Devuelve el cod_prov.
    """
    if not cuit:
        return 0
    prov = Proveedores.objects.filter(nro_cuit=cuit).first()
    if prov:
        return prov.cod_prov

    nuevo_cod = (Proveedores.objects.aggregate(Max('cod_prov'))['cod_prov__max'] or 0) + 1
    Proveedores.objects.create(
        cod_prov     = nuevo_cod,
        nomfantasia  = (denominacion or 'IMPORTADO ARCA')[:60],
        nomtitular   = (denominacion or 'IMPORTADO ARCA')[:60],
        nro_cuit     = cuit,
        cond_iva     = 1,
        estado       = 0,
        usuario      = 'arca_import',
        fecha_mod    = timezone.now(),
        observac     = 'Creado automáticamente desde importación de ARCA.',
    )
    return nuevo_cod


def _buscar_o_crear_cliente(cuit: str, denominacion: str) -> int:
    """
    Busca cliente por CUIT exacto. Si no existe, lo crea.
    Si CUIT vacío (consumidor final sin documento), devuelve 1 (cliente "varios").
    """
    if not cuit or cuit == '00000000000':
        return 1
    cli = Clientes.objects.filter(nro_cuit=cuit).first()
    if cli:
        return cli.cod_cli

    nuevo_cod = (Clientes.objects.aggregate(Max('cod_cli'))['cod_cli__max'] or 0) + 1
    Clientes.objects.create(
        cod_cli       = nuevo_cod,
        denominacion  = (denominacion or 'IMPORTADO ARCA')[:60],
        nro_cuit      = cuit,
        cond_iva      = 1,
        estado_baja   = 0,
        usuario       = 'arca_import',
        fecha_mod     = timezone.now(),
        observac      = 'Creado automáticamente desde importación de ARCA.',
    )
    return nuevo_cod


# ═════════════════════════════════════════════════════════════════════════════
# IMPORTADOR
# ═════════════════════════════════════════════════════════════════════════════

def _empresa_cuit_simple() -> str:
    """Lee CUIT de Parametros para validar coincidencia con el archivo."""
    try:
        p = Parametros.objects.first()
        if p and p.params:
            return _fmt_cuit_simple(p.params.get('cuit', ''))
    except Exception:
        pass
    return ''


def _procesar_fila_compras(fila: dict, usuario: str) -> dict:
    """
    Procesa una fila del Excel ARCA Recibidos → crea un registro en `compras`.
    Devuelve un dict con el resultado: {'estado': 'ok'|'duplicado'|'error', ...}
    """
    cod_arca, letra = _parsear_tipo_arca(fila.get('Tipo'))
    if not cod_arca:
        return {'estado': 'error', 'motivo': f"Tipo no reconocido: {fila.get('Tipo')!r}"}

    fecha = _parsear_fecha_arca(fila.get('Fecha'))
    if not fecha:
        return {'estado': 'error', 'motivo': f"Fecha inválida: {fila.get('Fecha')!r}"}

    cuit_emisor = _fmt_cuit_simple(fila.get('Nro. Doc. Emisor'))
    if not cuit_emisor:
        return {'estado': 'error', 'motivo': 'CUIT del emisor vacío'}

    pto_vta_int = _to_int(fila.get('Punto de Venta'))
    pto_vta_str = str(pto_vta_int).zfill(4)
    nro_factura = _to_int(fila.get('Número Desde'))
    if not nro_factura:
        return {'estado': 'error', 'motivo': 'Número de comprobante inválido'}

    # nro_comprob legacy = pto_vta * 100M + nro_factura (formato del sistema)
    nro_comprob_legacy = pto_vta_int * 100_000_000 + nro_factura

    cod_prov = _buscar_o_crear_proveedor(cuit_emisor, str(fila.get('Denominación Emisor', '')))

    # Anti-duplicado: mismo tipo + nro_legacy + proveedor
    if Compras.objects.filter(
        cod_comprob=cod_arca,
        nro_comprob=nro_comprob_legacy,
        cod_prov=cod_prov,
    ).exists():
        return {
            'estado': 'duplicado',
            'tipo': cod_arca, 'pto': pto_vta_str, 'nro': nro_factura,
            'cuit': cuit_emisor,
        }

    # Importes
    neto  = _to_decimal(fila.get('Neto Gravado Total'))
    iva   = _to_decimal(fila.get('Total IVA'))
    total = _to_decimal(fila.get('Imp. Total'))
    cae   = str(fila.get('Cód. Autorización') or '').strip()
    if cae and cae != 'nan':
        # ARCA exporta CAE en notación científica a veces (7.601317e+13)
        try:
            cae = str(int(float(cae)))
        except (ValueError, TypeError):
            pass
    else:
        cae = ''

    # Conversión USD → pesos
    moneda_excel = str(fila.get('Moneda') or '$').strip()
    tipo_cambio  = _to_decimal(fila.get('Tipo Cambio'), Decimal('1'))
    obs_extra = ''
    if moneda_excel.upper() == 'USD' and tipo_cambio > 1:
        obs_extra = f" | Original USD: {total} @ {tipo_cambio}"
        neto  = neto  * tipo_cambio
        iva   = iva   * tipo_cambio
        total = total * tipo_cambio

    observac = f"Importado ARCA{f' (CAE {cae})' if cae else ''}{obs_extra}".strip()

    # movim — usamos el helper de ventas.py que serializa con bitacora
    nuevo_movim = _siguiente_movim()
    _registrar_en_bitacora(nuevo_movim, 1, pto_vta_str, usuario)

    Compras.objects.create(
        movim                = nuevo_movim,
        id_comprob           = 0,
        cod_comprob          = cod_arca,
        nro_comprob          = nro_comprob_legacy,
        cod_prov             = cod_prov,
        fecha_comprob        = fecha,
        fecha_recep          = fecha,
        fecha_vto            = fecha,
        neto                 = neto,
        iva_1                = iva,
        total                = total,
        tot_general          = total,
        actualiz_stock       = 'N',
        observac             = observac,
        moneda               = 1,
        valordolar           = tipo_cambio if moneda_excel.upper() == 'USD' else Decimal('1'),
        ret_iibb             = 0,
        ret_iva              = 0,
        ret_gan              = 0,
        anulado              = None,
        comprobante_tipo     = cod_arca,
        comprobante_letra    = letra,
        comprobante_pto_vta  = pto_vta_str,
        usuario              = usuario,
        fecha_mod            = timezone.now(),
        cajero               = 1,
        procesado            = 0,
    )

    return {
        'estado': 'ok',
        'tipo': cod_arca, 'pto': pto_vta_str, 'nro': nro_factura,
        'proveedor': cod_prov, 'cuit': cuit_emisor,
        'total': float(total),
    }


def _procesar_fila_ventas(fila: dict, usuario: str) -> dict:
    """
    Procesa una fila del Excel ARCA Emitidos → crea un registro en `ventas`.
    Igual al de compras pero contra Ventas/Clientes.
    Una venta importada se marca como `anulado='N'` y `procesado=0`.
    """
    cod_arca, letra = _parsear_tipo_arca(fila.get('Tipo'))
    if not cod_arca:
        return {'estado': 'error', 'motivo': f"Tipo no reconocido: {fila.get('Tipo')!r}"}

    fecha = _parsear_fecha_arca(fila.get('Fecha'))
    if not fecha:
        return {'estado': 'error', 'motivo': f"Fecha inválida: {fila.get('Fecha')!r}"}

    # En "Mis Comprobantes Emitidos" el receptor es el CLIENTE (no el emisor)
    cuit_cli = _fmt_cuit_simple(fila.get('Nro. Doc. Receptor'))
    cod_cli = _buscar_o_crear_cliente(cuit_cli, str(fila.get('Denominación Receptor', '')))

    pto_vta_int = _to_int(fila.get('Punto de Venta'))
    pto_vta_str = str(pto_vta_int).zfill(4)
    nro_factura = _to_int(fila.get('Número Desde'))
    if not nro_factura:
        return {'estado': 'error', 'motivo': 'Número de comprobante inválido'}

    # En ventas, nro_comprob es solo el número de factura (no el formato legacy de compras).
    # Verificamos duplicados por (cod_comprob, nro_comprob, comprobante_pto_vta).
    if Ventas.objects.filter(
        cod_comprob=cod_arca,
        nro_comprob=nro_factura,
        comprobante_pto_vta=pto_vta_str,
    ).exists():
        return {
            'estado': 'duplicado',
            'tipo': cod_arca, 'pto': pto_vta_str, 'nro': nro_factura,
        }

    neto  = _to_decimal(fila.get('Neto Gravado Total'))
    iva   = _to_decimal(fila.get('Total IVA'))
    total = _to_decimal(fila.get('Imp. Total'))
    exento = _to_decimal(fila.get('Op. Exentas'))
    perce = _to_decimal(fila.get('Otros Tributos'))
    cae   = str(fila.get('Cód. Autorización') or '').strip()
    if cae and cae != 'nan':
        try:
            cae = str(int(float(cae)))
        except (ValueError, TypeError):
            pass
    else:
        cae = ''

    moneda_excel = str(fila.get('Moneda') or '$').strip()
    tipo_cambio  = _to_decimal(fila.get('Tipo Cambio'), Decimal('1'))
    if moneda_excel.upper() == 'USD' and tipo_cambio > 1:
        neto  = neto  * tipo_cambio
        iva   = iva   * tipo_cambio
        total = total * tipo_cambio
        exento = exento * tipo_cambio
        perce = perce * tipo_cambio

    nuevo_movim = _siguiente_movim()
    _registrar_en_bitacora(nuevo_movim, 1, pto_vta_str, usuario)

    Ventas.objects.create(
        movim                = nuevo_movim,
        id_comprob           = 0,
        cod_comprob          = cod_arca,
        nro_comprob          = nro_factura,
        cod_cli              = cod_cli,
        fecha_fact           = fecha,
        fecha_vto            = fecha,
        neto                 = neto,
        iva_1                = iva,
        exento               = exento,
        total                = neto,                 # base neta
        tot_general          = total,                # total cliente
        descuento            = 0,
        percepciones         = perce,
        impuestos_internos   = 0,
        cae                  = cae[:20],
        observac             = f"Importado ARCA{(' USD @ ' + str(tipo_cambio)) if moneda_excel == 'USD' else ''}"[:100],
        moneda               = 1,
        comprobante_tipo     = cod_arca[:2],
        comprobante_letra    = letra,
        comprobante_pto_vta  = pto_vta_str,
        cond_venta           = '1',
        anulado              = 'N',
        procesado            = 0,
        usuario              = usuario,
        fecha_mod            = timezone.now(),
        cajero               = 1,
        vendedor             = 1,
    )

    return {
        'estado': 'ok',
        'tipo': cod_arca, 'pto': pto_vta_str, 'nro': nro_factura,
        'cliente': cod_cli, 'cuit': cuit_cli,
        'total': float(total),
    }


# ═════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def ImportarMisComprobantesARCA(request):
    """
    Importa un archivo Excel descargado desde "Mis Comprobantes" de ARCA.

    Form-data:
        archivo:   .xlsx (requerido)
        circuito:  'C' (Recibidos→Compras) o 'V' (Emitidos→Ventas)
        usuario:   string (default 'admin')
        modo:      'previsualizar' o 'confirmar' (default 'confirmar')

    Devuelve:
        {
          status: success,
          totales: {leidos, ok, duplicados, errores},
          ok: [...],
          duplicados: [...],
          errores: [{fila, motivo, ...}],
          cuit_archivo: '30715885723',
          cuit_empresa: '30715885723',
          coincide_cuit: true
        }
    """
    archivo = request.FILES.get('archivo')
    circuito = str(request.data.get('circuito', 'C')).upper()
    usuario  = str(request.data.get('usuario', 'admin'))[:50]
    modo     = str(request.data.get('modo', 'confirmar')).lower()

    if not archivo:
        return Response({"status": "error", "mensaje": "Archivo .xlsx requerido."}, status=400)

    if circuito not in ('C', 'V'):
        return Response({"status": "error",
                         "mensaje": "circuito debe ser 'C' (Recibidos) o 'V' (Emitidos)."}, status=400)

    # Lectura del Excel — pandas + openpyxl
    try:
        import pandas as pd
        # Leemos primero la fila 0 para extraer el CUIT del título
        try:
            cabecera_df = pd.read_excel(archivo, header=None, nrows=1)
            titulo = str(cabecera_df.iloc[0, 0] or '')
        except Exception:
            titulo = ''
        # Volvemos al inicio del file pointer y leemos los datos con header en fila 1
        archivo.seek(0)
        df = pd.read_excel(archivo, header=1)
    except Exception as e:
        return Response({"status": "error",
                         "mensaje": f"No se pudo leer el archivo Excel: {e}"}, status=400)

    if df.empty:
        return Response({"status": "error",
                         "mensaje": "El archivo no tiene datos."}, status=400)

    # Validación: CUIT del título debe coincidir con el de la empresa
    cuit_archivo = ''.join(c for c in titulo if c.isdigit())[-11:].zfill(11)
    cuit_empresa = _empresa_cuit_simple()
    coincide_cuit = bool(cuit_empresa) and (cuit_archivo == cuit_empresa)

    # Validación adicional: tipo de archivo debe coincidir con el circuito elegido
    titulo_lower = titulo.lower()
    archivo_es_recibidos = 'recibidos' in titulo_lower
    archivo_es_emitidos  = 'emitidos'  in titulo_lower
    if archivo_es_recibidos and circuito == 'V':
        return Response({
            "status": "error",
            "mensaje": "El archivo es de Comprobantes RECIBIDOS pero seleccionaste circuito Ventas. "
                       "Cambiá el circuito a Compras o subí el archivo de Emitidos."
        }, status=400)
    if archivo_es_emitidos and circuito == 'C':
        return Response({
            "status": "error",
            "mensaje": "El archivo es de Comprobantes EMITIDOS pero seleccionaste circuito Compras. "
                       "Cambiá el circuito a Ventas o subí el archivo de Recibidos."
        }, status=400)

    procesador = _procesar_fila_compras if circuito == 'C' else _procesar_fila_ventas

    resultados_ok = []
    resultados_dup = []
    resultados_err = []

    # ── Procesamiento fila por fila ──────────────────────────────────────────
    # Patrón clave: cada fila en su PROPIO `transaction.atomic()` (savepoint).
    # Si una fila falla en MySQL, Django hace rollback solo de ese savepoint
    # y la transacción exterior sigue viva → la siguiente fila puede seguir.
    #
    # En modo previsualizar, envolvemos todo en otra atomic exterior y forzamos
    # rollback al final con _PreviewRollback. Resultado: nada se persiste.

    class _PreviewRollback(Exception):
        pass

    def _procesar_lote():
        for idx, fila_serie in df.iterrows():
            fila = fila_serie.to_dict()
            try:
                with transaction.atomic():        # ← savepoint por fila
                    r = procesador(fila, usuario)
            except Exception as e:
                r = {'estado': 'error', 'motivo': f'Excepción: {e}'}
            r['fila'] = int(idx) + 3   # +3 = título + header + base 1
            if r['estado'] == 'ok':          resultados_ok.append(r)
            elif r['estado'] == 'duplicado': resultados_dup.append(r)
            else:                            resultados_err.append(r)

    if modo == 'previsualizar':
        try:
            with transaction.atomic():
                _procesar_lote()
                raise _PreviewRollback()      # fuerza rollback de toda la atomic exterior
        except _PreviewRollback:
            pass                              # rollback ya ejecutado por Django
    else:
        _procesar_lote()

    return Response({
        "status":   "success",
        "modo":     modo,
        "circuito": circuito,
        "cuit_archivo": cuit_archivo,
        "cuit_empresa": cuit_empresa,
        "coincide_cuit": coincide_cuit,
        "titulo_archivo": titulo[:120],
        "totales": {
            "leidos":     int(df.shape[0]),
            "ok":         len(resultados_ok),
            "duplicados": len(resultados_dup),
            "errores":    len(resultados_err),
        },
        "ok":         resultados_ok,
        "duplicados": resultados_dup,
        "errores":    resultados_err,
    })