"""
impositivo.py — Módulo Informes Impositivos (Bejerman Web → Django/React)

Cubre:
  - Libro IVA Ventas / Compras (CRUD + generación de datos)
  - Libro IVA Digital (TXT para AFIP)
  - Comparación con AFIP (cruce de comprobantes)
  - Declaraciones Juradas Mensuales (V1 R.C.3685 y V2 Estándar)
  - Análisis de Operaciones Compras/Ventas
  - Exportaciones a Aplicativos: SICORE, SIFERE, e-ARCIBA y genérico
  - Monotributistas: Ventas por PDV, Ranking Clientes/Proveedores
  - ITC — Impuesto a la Transferencia de Combustibles
  - Auxiliares: puntos de registración, regímenes especiales

Integración con el proyecto existente:
  - Ventas / VentasDet / VentasRegimenes → datos IVA ventas
  - Compras / ComprasDet               → datos IVA compras
  - Clientes / Proveedores             → CUIT para presentaciones
  - Parametros                         → datos de la empresa
"""

import base64
import io
from datetime import date
from decimal import Decimal

from django.db import connection
from django.db.models import Sum, Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import (
    Ventas, VentasDet, VentasRegimenes,
    Compras, ComprasDet,
    Clientes, Proveedores, Parametros,
)
from ..impositivo_models import (
    ImpLibroIVA, ImpDeclaracionJurada, ImpExportacionAplicativo,
    ImpPuntoRegistracion, ImpRegimenEspecial,
    APLICATIVO_CHOICES,
)
from .utils import aplicar_rango_fechas


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _fmt_cuit(cuit_raw: str) -> str:
    """Devuelve CUIT sin guiones y con exactamente 11 dígitos."""
    if not cuit_raw:
        return '00000000000'
    limpio = ''.join(c for c in str(cuit_raw) if c.isdigit())
    return limpio.zfill(11)[:11]


def _periodo_a_rango(periodo_str: str):
    """
    Convierte 'YYYY-MM' a (date_desde, date_hasta) de ese mes.
    Acepta también 'MM/YYYY'.
    """
    try:
        if '/' in periodo_str:
            mm, yyyy = periodo_str.split('/')
        else:
            yyyy, mm = periodo_str.split('-')
        anio, mes = int(yyyy), int(mm)
        desde = date(anio, mes, 1)
        if mes == 12:
            hasta = date(anio + 1, 1, 1)
        else:
            hasta = date(anio, mes + 1, 1)
        from datetime import timedelta
        hasta = hasta - timedelta(days=1)
        return desde, hasta
    except Exception:
        return None, None


def _empresa_cuit() -> str:
    """Lee el CUIT de la empresa desde Parametros.params."""
    try:
        p = Parametros.objects.first()
        if p and p.params:
            return _fmt_cuit(str(p.params.get('cuit', '') or ''))
    except Exception:
        pass
    return '00000000000'


# ─────────────────────────────────────────────────────────────────────────────
# AUXILIARES — Puntos de Registración y Regímenes
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def PuntosRegistracion(request):
    if request.method == 'GET':
        data = list(ImpPuntoRegistracion.objects.values('codigo', 'descripcion', 'activo'))
        return Response({"status": "success", "data": data})

    d = request.data
    codigo = str(d.get('codigo', '')).strip().zfill(4)
    if not codigo:
        return Response({"status": "error", "mensaje": "Código requerido."}, status=400)
    obj, created = ImpPuntoRegistracion.objects.update_or_create(
        codigo=codigo,
        defaults={'descripcion': d.get('descripcion', ''), 'activo': bool(d.get('activo', True))}
    )
    return Response({"status": "success", "mensaje": "Guardado.", "codigo": obj.codigo,
                     "creado": created})


@api_view(['GET'])
def RegimenesEspeciales(request):
    tipo = request.query_params.get('tipo', '')
    qs   = ImpRegimenEspecial.objects.filter(activo=True)
    if tipo:
        qs = qs.filter(tipo=tipo)
    data = list(qs.values('codigo', 'descripcion', 'tipo'))
    return Response({"status": "success", "data": data})


# ─────────────────────────────────────────────────────────────────────────────
# LIBRO IVA VENTAS / COMPRAS — CRUD
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def LibrosIVA(request):
    """
    GET  → lista libros existentes (filtra por circuito: V o C)
    POST → crea un nuevo registro de libro IVA
    """
    circuito = request.query_params.get('circuito', '')

    if request.method == 'GET':
        qs = ImpLibroIVA.objects.all()
        if circuito:
            qs = qs.filter(circuito=circuito)
        data = list(qs.values(
            'id', 'circuito', 'fecha_desde', 'tipo',
            'punto_registracion_id', 'primer_numero', 'creado_en', 'creado_por',
        ))
        return Response({"status": "success", "data": data})

    # POST — crear
    d = request.data
    try:
        libro = ImpLibroIVA.objects.create(
            circuito           = d.get('circuito', 'V'),
            fecha_desde        = d.get('fecha_desde'),
            fecha_hasta        = d.get('fecha_hasta'),
            tipo               = d.get('tipo', 'P'),
            punto_registracion_id = d.get('punto_registracion') or None,
            primer_numero      = int(d.get('primer_numero', 1)),
            mostrar_cert_ret   = bool(d.get('mostrar_cert_ret', False)),
            mostrar_iibb       = bool(d.get('mostrar_iibb', True)),
            mostrar_comp_b_agrup = bool(d.get('mostrar_comp_b_agrup', False)),
            mostrar_anulados_agrup = bool(d.get('mostrar_anulados_agrup', False)),
            margen_superior    = bool(d.get('margen_superior', False)),
            lineas_separadoras = bool(d.get('lineas_separadoras', True)),
            imprime_encabezado = bool(d.get('imprime_encabezado', False)),
            texto_encabezado   = str(d.get('texto_encabezado', '')),
            creado_por         = str(d.get('usuario', 'admin')),
        )
        return Response({"status": "success", "id": libro.id,
                         "mensaje": "Libro IVA registrado."}, status=201)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=400)


@api_view(['DELETE'])
def EliminarLibroIVA(request, libro_id):
    try:
        ImpLibroIVA.objects.filter(id=libro_id).delete()
        return Response({"status": "success", "mensaje": "Eliminado."})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=400)


@api_view(['GET'])
def DatosLibroIVA(request, libro_id):
    """
    Genera los datos del libro IVA consultando Ventas o Compras según el circuito.
    Devuelve los comprobantes del período con totales de IVA.
    """
    try:
        libro = ImpLibroIVA.objects.get(id=libro_id)
    except ImpLibroIVA.DoesNotExist:
        return Response({"status": "error", "mensaje": "Libro no encontrado."}, status=404)

    desde = libro.fecha_desde
    hasta = libro.fecha_hasta or date.today()

    if libro.circuito == 'V':
        # ── Ventas ────────────────────────────────────────────────────────────
        qs = Ventas.objects.filter(
            fecha_fact__date__gte=desde,
            fecha_fact__date__lte=hasta,
            anulado='N',
        ).exclude(cod_comprob__in=['PR', 'IS', 'SS'])

        if libro.punto_registracion_id:
            qs = qs.filter(comprobante_pto_vta=libro.punto_registracion_id)

        comprobantes = list(qs.values(
            'fecha_fact', 'cod_comprob', 'comprobante_letra',
            'comprobante_pto_vta', 'nro_comprob', 'cod_cli',
            'neto', 'iva_1', 'exento', 'percepciones',
            'perce_caba', 'perce_bsas', 'perce_5329',
            'impuestos_internos', 'tot_general',
        ).order_by('fecha_fact', 'nro_comprob'))

        # Enriquecer con CUIT del cliente
        cli_ids = {c['cod_cli'] for c in comprobantes}
        clientes_dict = {
            c.cod_cli: (c.denominacion, c.nro_cuit or '')
            for c in Clientes.objects.filter(cod_cli__in=cli_ids)
        }
        for c in comprobantes:
            nom, cuit = clientes_dict.get(c['cod_cli'], ('', ''))
            c['denominacion'] = nom
            c['nro_cuit'] = cuit

        totales = qs.aggregate(
            suma_neto=Sum('neto'),
            suma_iva=Sum('iva_1'),
            suma_exento=Sum('exento'),
            suma_percepciones=Sum('percepciones'),
            suma_total=Sum('tot_general'),
        )
    else:
        # ── Compras ───────────────────────────────────────────────────────────
        qs = Compras.objects.filter(
            fecha_comprob__date__gte=desde,
            fecha_comprob__date__lte=hasta,
        ).filter(
            Q(anulado__isnull=True) | Q(anulado='')
        ).filter(cod_comprob__in=['FA', 'FB', 'FC', 'FX', 'NDA', 'NDB', 'NCA', 'NCB'])

        if libro.punto_registracion_id:
            qs = qs.filter(comprobante_pto_vta=libro.punto_registracion_id)

        comprobantes = list(qs.values(
            'fecha_comprob', 'cod_comprob', 'comprobante_letra',
            'comprobante_pto_vta', 'nro_comprob', 'cod_prov',
            'neto', 'iva_1', 'total', 'tot_general',
            'ret_iva', 'ret_gan', 'ret_iibb',
        ).order_by('fecha_comprob', 'nro_comprob'))

        # Enriquecer con razón social del proveedor
        prov_ids = {c['cod_prov'] for c in comprobantes}
        provs_dict = {
            p.cod_prov: (p.nomfantasia, p.nro_cuit or '')
            for p in Proveedores.objects.filter(cod_prov__in=prov_ids)
        }
        for c in comprobantes:
            nom, cuit = provs_dict.get(c['cod_prov'], ('', ''))
            c['denominacion'] = nom
            c['nro_cuit'] = cuit

        totales = qs.aggregate(
            suma_neto=Sum('neto'),
            suma_iva=Sum('iva_1'),
            suma_total=Sum('tot_general'),
        )

    return Response({
        "status": "success",
        "libro": {
            "id": libro.id,
            "circuito": libro.circuito,
            "tipo": libro.tipo,
            "fecha_desde": str(desde),
            "fecha_hasta": str(hasta),
        },
        "totales": {k: float(v or 0) for k, v in (totales or {}).items()},
        "comprobantes": comprobantes,
        "cantidad": len(comprobantes),
    })


# ─────────────────────────────────────────────────────────────────────────────
# LIBRO IVA DIGITAL (TXT para AFIP)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def GenerarIVADigital(request):
    """
    Genera el archivo TXT del Libro IVA Digital para presentar a AFIP.
    Formato: Registro de Compras / Registro de Ventas (R.G. 3685).

    Payload: { "periodo": "YYYY-MM", "circuito": "V"|"C", "prorratea": false }
    """
    periodo_str = request.data.get('periodo', '')
    circuito    = request.data.get('circuito', 'V')
    prorratea   = bool(request.data.get('prorratea', False))

    desde, hasta = _periodo_a_rango(periodo_str)
    if not desde:
        return Response({"status": "error", "mensaje": "Período inválido. Use YYYY-MM."}, status=400)

    cuit_empresa = _empresa_cuit()
    lines = []

    if circuito == 'V':
        ventas = Ventas.objects.filter(
            fecha_fact__gte=desde, fecha_fact__lte=hasta, anulado='N',
        ).exclude(cod_comprob__in=['PR', 'IS', 'SS'])

        for v in ventas.order_by('fecha_fact', 'nro_comprob'):
            neto   = Decimal(str(v.neto    or 0))
            iva    = Decimal(str(v.iva_1   or 0))
            exento = Decimal(str(v.exento  or 0))
            total  = Decimal(str(v.tot_general or 0))

            cli = Clientes.objects.filter(cod_cli=v.cod_cli).first()
            cuit_cli = _fmt_cuit(cli.nro_cuit if cli else '')
            nom_cli  = (cli.denominacion if cli else 'CONSUMIDOR FINAL')[:30].ljust(30)

            tipo_cbte = (str(v.cod_comprob or '') + str(v.comprobante_letra or '')).ljust(3)[:3]
            pto  = str(v.comprobante_pto_vta or '0001').zfill(4)
            nro  = str(v.nro_comprob or 0).zfill(8)
            fec  = v.fecha_fact.strftime('%Y%m%d') if v.fecha_fact else '00000000'

            line = (
                f"{fec}"
                f"{tipo_cbte}"
                f"{pto}"
                f"{nro}"
                f"{'80':>2}"           # doc_tipo: CUIT
                f"{cuit_cli}"
                f"{nom_cli}"
                f"{int(neto  * 100):>15}"
                f"{int(iva   * 100):>15}"
                f"{int(exento* 100):>15}"
                f"{int(total * 100):>15}"
            )
            lines.append(line)
    else:
        compras = Compras.objects.filter(
            fecha_comprob__date__gte=desde,
            fecha_comprob__date__lte=hasta,
        ).filter(Q(anulado__isnull=True) | Q(anulado=''))

        for c in compras.order_by('fecha_comprob', 'nro_comprob'):
            neto  = Decimal(str(c.neto  or 0))
            iva   = Decimal(str(c.iva_1 or 0))
            total = Decimal(str(c.tot_general or 0))

            prov = Proveedores.objects.filter(cod_prov=c.cod_prov).first()
            cuit_prov = _fmt_cuit(prov.nro_cuit if prov else '')
            nom_prov  = (prov.nomfantasia if prov else 'PROVEEDOR')[:30].ljust(30)

            tipo_cbte = str(c.cod_comprob or '').ljust(3)[:3]
            pto = str(c.comprobante_pto_vta or '0001').zfill(4)
            nro = str(c.nro_comprob or 0).zfill(8)
            fec_raw = c.fecha_comprob
            fec = fec_raw.strftime('%Y%m%d') if hasattr(fec_raw, 'strftime') else '00000000'

            line = (
                f"{fec}"
                f"{tipo_cbte}"
                f"{pto}"
                f"{nro}"
                f"{'80':>2}"
                f"{cuit_prov}"
                f"{nom_prov}"
                f"{int(neto  * 100):>15}"
                f"{int(iva   * 100):>15}"
                f"{'0':>15}"           # exento
                f"{int(total * 100):>15}"
            )
            lines.append(line)

    contenido = '\r\n'.join(lines)
    contenido_b64 = base64.b64encode(contenido.encode('latin-1', errors='replace')).decode()
    nombre = f"IVA_DIGITAL_{circuito}_{desde.strftime('%Y%m')}.txt"

    return Response({
        "status":   "success",
        "nombre":   nombre,
        "contenido_b64": contenido_b64,
        "registros": len(lines),
        "periodo":  periodo_str,
        "circuito": circuito,
        "prorratea": prorratea,
    })


# ─────────────────────────────────────────────────────────────────────────────
# DECLARACIONES JURADAS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def DeclaracionesJuradas(request):
    """
    GET  → lista todas las DDJJ (filtra por version: V1 o V2)
    POST → genera una nueva DDJJ para el período indicado
    """
    version = request.query_params.get('version', '')

    if request.method == 'GET':
        qs = ImpDeclaracionJurada.objects.all()
        if version:
            qs = qs.filter(version=version)
        data = list(qs.values(
            'id', 'periodo', 'version', 'tipo_emision', 'pasado_cg',
            'total_debito_fiscal', 'total_credito_fiscal', 'saldo_a_pagar',
            'emitido_en', 'emitido_por',
        ))
        return Response({"status": "success", "data": data})

    # POST — crear DDJJ
    d = request.data
    periodo_str = d.get('periodo', '')
    desde, hasta = _periodo_a_rango(periodo_str)
    if not desde:
        return Response({"status": "error", "mensaje": "Período inválido."}, status=400)

    version_val = d.get('version', 'V2')
    tipo_emision = d.get('tipo_emision', 'O')

    # Calcular débito fiscal (IVA ventas)
    ventas_mes = Ventas.objects.filter(
        fecha_fact__gte=desde, fecha_fact__lte=hasta, anulado='N',
    ).exclude(cod_comprob__in=['PR', 'IS', 'SS'])

    debito = ventas_mes.aggregate(s=Sum('iva_1'))['s'] or Decimal('0')

    # Calcular crédito fiscal (IVA compras)
    compras_mes = Compras.objects.filter(
        fecha_comprob__date__gte=desde,
        fecha_comprob__date__lte=hasta,
    ).filter(Q(anulado__isnull=True) | Q(anulado=''))

    credito = compras_mes.aggregate(s=Sum('iva_1'))['s'] or Decimal('0')
    saldo   = Decimal(str(debito)) - Decimal(str(credito))

    try:
        ddjj = ImpDeclaracionJurada.objects.create(
            periodo              = desde,
            version              = version_val,
            tipo_emision         = tipo_emision,
            total_debito_fiscal  = debito,
            total_credito_fiscal = credito,
            saldo_a_pagar        = max(saldo, Decimal('0')),
            emitido_por          = str(d.get('usuario', 'admin')),
        )
        return Response({
            "status":  "success",
            "id":      ddjj.id,
            "periodo": str(desde),
            "version": version_val,
            "debito_fiscal":  float(debito),
            "credito_fiscal": float(credito),
            "saldo_a_pagar":  float(max(saldo, Decimal('0'))),
            "mensaje": f"DDJJ {version_val} {periodo_str} generada."
        }, status=201)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=400)


@api_view(['POST'])
def RectificarDDJJ(request, ddjj_id):
    """Genera una rectificativa de la DDJJ indicada."""
    try:
        original = ImpDeclaracionJurada.objects.get(id=ddjj_id)
    except ImpDeclaracionJurada.DoesNotExist:
        return Response({"status": "error", "mensaje": "DDJJ no encontrada."}, status=404)

    # Determinar número de rectificativa
    ultimas = ImpDeclaracionJurada.objects.filter(
        periodo=original.periodo,
        version=original.version,
    ).exclude(tipo_emision='O').count()

    mapa_rect = {0: 'R1', 1: 'R2', 2: 'R3'}
    nueva_emision = mapa_rect.get(ultimas, f'R{ultimas + 1}')

    nueva = ImpDeclaracionJurada.objects.create(
        periodo              = original.periodo,
        version              = original.version,
        tipo_emision         = nueva_emision,
        total_debito_fiscal  = original.total_debito_fiscal,
        total_credito_fiscal = original.total_credito_fiscal,
        saldo_a_pagar        = original.saldo_a_pagar,
        emitido_por          = str(request.data.get('usuario', 'admin')),
    )
    return Response({
        "status":  "success",
        "id":      nueva.id,
        "tipo_emision": nueva_emision,
        "mensaje": f"Rectificativa {nueva_emision} creada."
    }, status=201)


@api_view(['POST'])
def MarcarPasadoCG(request, ddjj_id):
    """Marca la DDJJ como pasada a Contabilidad General."""
    updated = ImpDeclaracionJurada.objects.filter(id=ddjj_id).update(pasado_cg=True)
    if updated:
        return Response({"status": "success", "mensaje": "DDJJ marcada como pasada a CG."})
    return Response({"status": "error", "mensaje": "DDJJ no encontrada."}, status=404)


# ─────────────────────────────────────────────────────────────────────────────
# ANÁLISIS DE OPERACIONES COMPRAS / VENTAS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def AnalisisOperaciones(request):
    """
    Análisis de operaciones de compras o ventas para un rango de períodos.

    Payload:
    {
      "circuito": "V" | "C",
      "periodo_desde": "YYYY-MM",
      "periodo_hasta": "YYYY-MM",
      "formato": "R" | "D"    (Resumido o Detallado)
    }
    """
    d           = request.data
    circuito    = d.get('circuito', 'V')
    per_desde   = d.get('periodo_desde', '')
    per_hasta   = d.get('periodo_hasta', per_desde)
    formato     = d.get('formato', 'R')

    desde, _ = _periodo_a_rango(per_desde)
    _, hasta  = _periodo_a_rango(per_hasta)

    if not desde or not hasta:
        return Response({"status": "error", "mensaje": "Períodos inválidos."}, status=400)

    if circuito == 'V':
        qs = Ventas.objects.filter(
            fecha_fact__gte=desde, fecha_fact__lte=hasta, anulado='N',
        ).exclude(cod_comprob__in=['PR', 'IS', 'SS'])

        if formato == 'R':
            # Resumido: totales por tipo de comprobante
            resumen = qs.values('cod_comprob', 'comprobante_letra').annotate(
                cantidad=Count('movim'),
                suma_neto=Sum('neto'),
                suma_iva=Sum('iva_1'),
                suma_total=Sum('tot_general'),
            ).order_by('cod_comprob')
            data_out = list(resumen)
        else:
            # Detallado: por comprobante
            data_out = list(qs.values(
                'fecha_fact', 'cod_comprob', 'comprobante_letra',
                'comprobante_pto_vta', 'nro_comprob', 'cod_cli',
                'neto', 'iva_1', 'exento', 'tot_general',
            ).order_by('fecha_fact', 'nro_comprob')[:500])

        totales = qs.aggregate(
            suma_neto=Sum('neto'), suma_iva=Sum('iva_1'), suma_total=Sum('tot_general')
        )
    else:
        qs = Compras.objects.filter(
            fecha_comprob__date__gte=desde,
            fecha_comprob__date__lte=hasta,
        ).filter(Q(anulado__isnull=True) | Q(anulado=''))

        if formato == 'R':
            resumen = qs.values('cod_comprob').annotate(
                cantidad=Count('movim'),
                suma_neto=Sum('neto'),
                suma_iva=Sum('iva_1'),
                suma_total=Sum('tot_general'),
            ).order_by('cod_comprob')
            data_out = list(resumen)
        else:
            data_out = list(qs.values(
                'fecha_comprob', 'cod_comprob', 'comprobante_letra',
                'comprobante_pto_vta', 'nro_comprob', 'cod_prov',
                'neto', 'iva_1', 'tot_general',
            ).order_by('fecha_comprob', 'nro_comprob')[:500])

        totales = qs.aggregate(
            suma_neto=Sum('neto'), suma_iva=Sum('iva_1'), suma_total=Sum('tot_general')
        )

    return Response({
        "status":   "success",
        "circuito": circuito,
        "formato":  formato,
        "desde":    str(desde),
        "hasta":    str(hasta),
        "totales":  {k: float(v or 0) for k, v in (totales or {}).items()},
        "data":     data_out,
        "cantidad": len(data_out),
    })


# ─────────────────────────────────────────────────────────────────────────────
# EXPORTACIONES A APLICATIVOS — Genérico + SICORE + SIFERE
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def ListarExportaciones(request):
    aplicativo = request.query_params.get('aplicativo', '')
    qs = ImpExportacionAplicativo.objects.all()
    if aplicativo:
        qs = qs.filter(aplicativo=aplicativo)
    data = list(qs.values(
        'id', 'aplicativo', 'circuito', 'fecha_desde', 'fecha_hasta',
        'estado', 'nombre_archivo', 'generado_en', 'generado_por',
        'cantidad_registros', 'error_mensaje',
    )[:100])
    return Response({"status": "success", "data": data})


@api_view(['GET'])
def DescargarExportacion(request, expo_id):
    try:
        expo = ImpExportacionAplicativo.objects.get(id=expo_id)
    except ImpExportacionAplicativo.DoesNotExist:
        return Response({"status": "error", "mensaje": "Exportación no encontrada."}, status=404)

    if expo.estado != 'COMPLETADO' or not expo.contenido_b64:
        return Response({"status": "error", "mensaje": "El archivo no está disponible aún."}, status=400)

    return Response({
        "status":   "success",
        "nombre":   expo.nombre_archivo,
        "contenido_b64": expo.contenido_b64,
        "aplicativo": expo.aplicativo,
        "registros": expo.cantidad_registros,
    })


def _registrar_exportacion(aplicativo, circuito, desde, hasta, usuario, parametros, lines, nombre):
    """Helper para guardar el resultado de una exportación."""
    contenido = '\r\n'.join(lines)
    contenido_b64 = base64.b64encode(contenido.encode('latin-1', errors='replace')).decode()
    expo = ImpExportacionAplicativo.objects.create(
        aplicativo        = aplicativo,
        circuito          = circuito,
        fecha_desde       = desde,
        fecha_hasta       = hasta,
        estado            = 'COMPLETADO',
        parametros        = parametros,
        nombre_archivo    = nombre,
        contenido_b64     = contenido_b64,
        generado_por      = usuario,
        cantidad_registros= len(lines),
    )
    return expo, contenido_b64


@api_view(['POST'])
def GenerarSICORE(request):
    """
    Genera el archivo .txt compatible con el aplicativo AFIP SICORE.
    Formato: retenciones y percepciones de IVA e IIBB sobre ventas/compras.

    Payload:
    {
      "circuito": "V",
      "fecha_desde": "YYYY-MM-DD",
      "fecha_hasta": "YYYY-MM-DD",
      "regimenes": ["067", "217"],   // vacío = todos
      "usuario": "admin"
    }
    """
    d           = request.data
    circuito    = d.get('circuito', 'V')
    fecha_desde = d.get('fecha_desde', '')
    fecha_hasta = d.get('fecha_hasta', fecha_desde)
    regimenes   = d.get('regimenes', [])
    usuario     = str(d.get('usuario', 'admin'))

    if not fecha_desde:
        return Response({"status": "error", "mensaje": "fecha_desde requerido."}, status=400)

    try:
        from datetime import datetime
        desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    except ValueError:
        return Response({"status": "error", "mensaje": "Formato de fecha inválido (YYYY-MM-DD)."}, status=400)

    lines = []

    if circuito == 'V':
        # Percepciones de ventas → VentasRegimenes
        qs = VentasRegimenes.objects.filter(
            comprobante_tipo__in=['EA', 'FA', 'EB', 'FB', 'EC', 'FC'],
        ).select_related()

        # Filtrar por fecha via join con ventas
        ventas_ids = list(
            Ventas.objects.filter(
                fecha_fact__gte=desde,
                fecha_fact__lte=hasta,
                anulado='N',
            ).values_list('movim', flat=True)
        )
        qs = qs.filter(movim__in=ventas_ids, importe__gt=0)

        if regimenes:
            qs = qs.filter(regimen__in=regimenes)

        for reg in qs:
            venta = Ventas.objects.filter(movim=reg.movim).first()
            if not venta:
                continue
            cli = Clientes.objects.filter(cod_cli=venta.cod_cli).first()
            cuit_ret = _fmt_cuit(cli.nro_cuit if cli else '')
            tipo_cbte = str(reg.comprobante_tipo or '').zfill(2)
            pto  = str(reg.comprobante_pto_vta or '0001').zfill(4)
            nro  = str(reg.nro_comprob or 0).zfill(8)
            fec  = venta.fecha_fact.strftime('%Y%m%d') if venta.fecha_fact else '00000000'
            imp  = int(Decimal(str(reg.importe or 0)) * 100)
            base = int(Decimal(str(reg.base_imponible or 0)) * 100)
            regimen_cod = str(reg.regimen or '').zfill(3)[:3]

            line = (
                f"{tipo_cbte:>2}"
                f"{fec:>8}"
                f"{pto:>4}{nro:>8}"
                f"{cuit_ret:>11}"
                f"{imp:>14}"
                f"{base:>14}"
                f"{regimen_cod:>3}"
            )
            lines.append(line)
    else:
        # Retenciones en compras
        compras_ids = list(
            Compras.objects.filter(
                fecha_comprob__date__gte=desde,
                fecha_comprob__date__lte=hasta,
            ).filter(Q(anulado__isnull=True) | Q(anulado='')).values_list('movim', flat=True)
        )

        for movim in compras_ids:
            compra = Compras.objects.filter(movim=movim).first()
            if not compra:
                continue
            prov = Proveedores.objects.filter(cod_prov=compra.cod_prov).first()
            cuit_ret = _fmt_cuit(prov.nro_cuit if prov else '')

            for ret_field, val in [
                ('ret_iva', compra.ret_iva),
                ('ret_gan', compra.ret_gan),
                ('ret_iibb', compra.ret_iibb),
            ]:
                if not val or val <= 0:
                    continue
                fec_raw = compra.fecha_comprob
                fec = fec_raw.strftime('%Y%m%d') if hasattr(fec_raw, 'strftime') else '00000000'
                tipo_cbte = str(compra.cod_comprob or '').zfill(2)
                pto  = str(compra.comprobante_pto_vta or '0001').zfill(4)
                nro  = str(compra.nro_comprob or 0).zfill(8)
                imp  = int(Decimal(str(val)) * 100)
                regimen_cod = {'ret_iva': '067', 'ret_gan': '217', 'ret_iibb': '217'}.get(ret_field, '000')
                line = (
                    f"{tipo_cbte:>2}"
                    f"{fec:>8}"
                    f"{pto:>4}{nro:>8}"
                    f"{cuit_ret:>11}"
                    f"{imp:>14}"
                    f"{'0':>14}"
                    f"{regimen_cod:>3}"
                )
                lines.append(line)

    nombre = f"SICORE_{circuito}_{desde.strftime('%Y%m%d')}_{hasta.strftime('%Y%m%d')}.txt"
    expo, contenido_b64 = _registrar_exportacion(
        'SICORE', circuito, desde, hasta, usuario,
        {'regimenes': regimenes}, lines, nombre
    )

    return Response({
        "status":        "success",
        "id":            expo.id,
        "nombre":        nombre,
        "contenido_b64": contenido_b64,
        "registros":     len(lines),
        "mensaje":       f"SICORE generado: {len(lines)} registros.",
    })


@api_view(['POST'])
def GenerarSIFERE(request):
    """
    Genera el archivo .txt compatible con SIFERE (Convenio Multilateral COMARB).
    Tipo de impuesto: Retenciones / Percepciones / Recaudaciones Bancarias.

    Payload:
    {
      "tipo_impuesto": "P",   // R=Retenciones, P=Percepciones, B=Banc., A=Perc.Aduaneras
      "fecha_desde": "YYYY-MM-DD",
      "fecha_hasta": "YYYY-MM-DD",
      "provincia": "01",      // código provincia AFIP, vacío = todas
      "usuario": "admin"
    }
    """
    d             = request.data
    tipo_impuesto = d.get('tipo_impuesto', 'P')
    fecha_desde   = d.get('fecha_desde', '')
    fecha_hasta   = d.get('fecha_hasta', fecha_desde)
    provincia     = d.get('provincia', '')
    usuario       = str(d.get('usuario', 'admin'))

    if not fecha_desde:
        return Response({"status": "error", "mensaje": "fecha_desde requerido."}, status=400)

    try:
        from datetime import datetime
        desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    except ValueError:
        return Response({"status": "error", "mensaje": "Formato de fecha inválido."}, status=400)

    cuit_empresa = _empresa_cuit()
    lines = []

    # Percepciones IIBB sobre ventas → perce_caba, perce_bsas
    ventas = Ventas.objects.filter(
        fecha_fact__gte=desde,
        fecha_fact__lte=hasta,
        anulado='N',
    ).exclude(cod_comprob__in=['PR', 'IS', 'SS'])

    for v in ventas:
        cli = Clientes.objects.filter(cod_cli=v.cod_cli).first()
        cuit_cli = _fmt_cuit(cli.nro_cuit if cli else '')
        fec = v.fecha_fact.strftime('%d/%m/%Y') if v.fecha_fact else '01/01/2000'

        percepciones_por_prov = []
        if v.perce_caba and v.perce_caba > 0:
            percepciones_por_prov.append(('901', float(v.perce_caba)))
        if v.perce_bsas and v.perce_bsas > 0:
            percepciones_por_prov.append(('01', float(v.perce_bsas)))

        for cod_prov, monto in percepciones_por_prov:
            if provincia and cod_prov != provincia:
                continue
            tipo_cbte = str(v.cod_comprob or '').ljust(2)[:2]
            pto = str(v.comprobante_pto_vta or '0001').zfill(4)
            nro = str(v.nro_comprob or 0).zfill(8)
            line = (
                f"{tipo_impuesto}"
                f"{cod_prov:>3}"
                f"{fec}"
                f"{tipo_cbte}"
                f"{pto}-{nro}"
                f"{cuit_cli}"
                f"{monto:>15.2f}"
            )
            lines.append(line)

    nombre = f"SIFERE_{tipo_impuesto}_{desde.strftime('%Y%m%d')}_{hasta.strftime('%Y%m%d')}.txt"
    expo, contenido_b64 = _registrar_exportacion(
        'SIFERE', 'V', desde, hasta, usuario,
        {'tipo_impuesto': tipo_impuesto, 'provincia': provincia}, lines, nombre
    )

    return Response({
        "status":        "success",
        "id":            expo.id,
        "nombre":        nombre,
        "contenido_b64": contenido_b64,
        "registros":     len(lines),
        "mensaje":       f"SIFERE generado: {len(lines)} registros.",
    })


@api_view(['POST'])
def GenerarExportacionGenerica(request):
    """
    Exportación genérica para aplicativos con formato simple (SIACER, SICOL, ARBA, ITC, etc.).
    Genera un reporte de los comprobantes del período sin formato específico.

    Payload:
    {
      "aplicativo": "SIACER",
      "circuito": "V",
      "fecha_desde": "YYYY-MM-DD",
      "fecha_hasta": "YYYY-MM-DD",
      "usuario": "admin"
    }
    """
    d           = request.data
    aplicativo  = d.get('aplicativo', 'OTRO')
    circuito    = d.get('circuito', 'V')
    fecha_desde = d.get('fecha_desde', '')
    fecha_hasta = d.get('fecha_hasta', fecha_desde)
    usuario     = str(d.get('usuario', 'admin'))

    # Validar aplicativo
    aplicativos_validos = {k for k, _ in APLICATIVO_CHOICES}
    if aplicativo not in aplicativos_validos:
        return Response({"status": "error",
                         "mensaje": f"Aplicativo '{aplicativo}' no reconocido."}, status=400)

    if not fecha_desde:
        return Response({"status": "error", "mensaje": "fecha_desde requerido."}, status=400)

    try:
        from datetime import datetime
        desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    except ValueError:
        return Response({"status": "error", "mensaje": "Formato de fecha inválido."}, status=400)

    lines = []

    if circuito in ('V', 'A'):
        ventas = Ventas.objects.filter(
            fecha_fact__gte=desde, fecha_fact__lte=hasta, anulado='N',
        ).exclude(cod_comprob__in=['PR', 'IS', 'SS'])

        for v in ventas.order_by('fecha_fact', 'nro_comprob'):
            fec = v.fecha_fact.strftime('%Y%m%d') if v.fecha_fact else '00000000'
            tipo = str(v.cod_comprob or '').ljust(3)[:3]
            pto  = str(v.comprobante_pto_vta or '0001').zfill(4)
            nro  = str(v.nro_comprob or 0).zfill(8)
            total = int(Decimal(str(v.tot_general or 0)) * 100)
            lines.append(f"{fec}{tipo}{pto}{nro}{total:>14}")

    if circuito in ('C', 'A'):
        compras = Compras.objects.filter(
            fecha_comprob__date__gte=desde,
            fecha_comprob__date__lte=hasta,
        ).filter(Q(anulado__isnull=True) | Q(anulado=''))

        for c in compras.order_by('fecha_comprob', 'nro_comprob'):
            fec_raw = c.fecha_comprob
            fec  = fec_raw.strftime('%Y%m%d') if hasattr(fec_raw, 'strftime') else '00000000'
            tipo = str(c.cod_comprob or '').ljust(3)[:3]
            pto  = str(c.comprobante_pto_vta or '0001').zfill(4)
            nro  = str(c.nro_comprob or 0).zfill(8)
            total = int(Decimal(str(c.tot_general or 0)) * 100)
            lines.append(f"{fec}{tipo}{pto}{nro}{total:>14}")

    nombre = f"{aplicativo}_{circuito}_{desde.strftime('%Y%m%d')}_{hasta.strftime('%Y%m%d')}.txt"
    expo, contenido_b64 = _registrar_exportacion(
        aplicativo, circuito, desde, hasta, usuario,
        d, lines, nombre
    )

    return Response({
        "status":        "success",
        "id":            expo.id,
        "nombre":        nombre,
        "contenido_b64": contenido_b64,
        "registros":     len(lines),
        "mensaje":       f"{aplicativo} generado: {len(lines)} registros.",
    })


# ─────────────────────────────────────────────────────────────────────────────
# MONOTRIBUTISTAS — Presentación Semestral
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def VentasPorPuntoDeVenta(request):
    """
    Informe de ventas por punto de venta para presentación semestral monotributistas.
    """
    d           = request.data
    fecha_desde = d.get('fecha_desde', '')
    fecha_hasta = d.get('fecha_hasta', fecha_desde)

    if not fecha_desde:
        return Response({"status": "error", "mensaje": "fecha_desde requerido."}, status=400)

    from datetime import datetime
    try:
        desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    except ValueError:
        return Response({"status": "error", "mensaje": "Formato inválido."}, status=400)

    qs = Ventas.objects.filter(
        fecha_fact__gte=desde, fecha_fact__lte=hasta, anulado='N',
    ).exclude(cod_comprob__in=['PR', 'IS', 'SS'])

    resumen = qs.values('comprobante_pto_vta').annotate(
        cantidad=Count('movim'),
        total=Sum('tot_general'),
        neto=Sum('neto'),
        iva=Sum('iva_1'),
    ).order_by('comprobante_pto_vta')

    data = list(resumen)
    gran_total = sum(float(r['total'] or 0) for r in data)

    return Response({
        "status":     "success",
        "desde":      str(desde),
        "hasta":      str(hasta),
        "data":       data,
        "gran_total": gran_total,
    })


@api_view(['POST'])
def RankingClientes(request):
    """Top 5 clientes por monto total — presentación semestral monotributistas."""
    d           = request.data
    fecha_desde = d.get('fecha_desde', '')
    fecha_hasta = d.get('fecha_hasta', fecha_desde)
    top_n       = int(d.get('top_n', 5))

    if not fecha_desde:
        return Response({"status": "error", "mensaje": "fecha_desde requerido."}, status=400)

    from datetime import datetime
    try:
        desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    except ValueError:
        return Response({"status": "error", "mensaje": "Formato inválido."}, status=400)

    qs = Ventas.objects.filter(
        fecha_fact__gte=desde, fecha_fact__lte=hasta, anulado='N',
    ).exclude(cod_comprob__in=['PR', 'IS', 'SS'])

    ranking = qs.values('cod_cli').annotate(
        total=Sum('tot_general'),
        cantidad=Count('movim'),
    ).order_by('-total')[:top_n]

    result = list(ranking)
    cli_ids = [r['cod_cli'] for r in result]
    clientes_dict = {
        c.cod_cli: (c.denominacion, c.nro_cuit or '')
        for c in Clientes.objects.filter(cod_cli__in=cli_ids)
    }
    for r in result:
        nom, cuit = clientes_dict.get(r['cod_cli'], ('', ''))
        r['denominacion'] = nom
        r['nro_cuit']     = cuit

    return Response({"status": "success", "desde": str(desde), "hasta": str(hasta), "data": result})


@api_view(['POST'])
def RankingProveedores(request):
    """Top 5 proveedores por monto total — presentación semestral monotributistas."""
    d           = request.data
    fecha_desde = d.get('fecha_desde', '')
    fecha_hasta = d.get('fecha_hasta', fecha_desde)
    top_n       = int(d.get('top_n', 5))

    if not fecha_desde:
        return Response({"status": "error", "mensaje": "fecha_desde requerido."}, status=400)

    from datetime import datetime
    try:
        desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    except ValueError:
        return Response({"status": "error", "mensaje": "Formato inválido."}, status=400)

    qs = Compras.objects.filter(
        fecha_comprob__date__gte=desde,
        fecha_comprob__date__lte=hasta,
    ).filter(Q(anulado__isnull=True) | Q(anulado=''))

    ranking = qs.values('cod_prov').annotate(
        total=Sum('tot_general'),
        cantidad=Count('movim'),
    ).order_by('-total')[:top_n]

    result = list(ranking)
    prov_ids = [r['cod_prov'] for r in result]
    provs_dict = {
        p.cod_prov: (p.nomfantasia, p.nro_cuit or '')
        for p in Proveedores.objects.filter(cod_prov__in=prov_ids)
    }
    for r in result:
        nom, cuit = provs_dict.get(r['cod_prov'], ('', ''))
        r['denominacion'] = nom
        r['nro_cuit']     = cuit

    return Response({"status": "success", "desde": str(desde), "hasta": str(hasta), "data": result})