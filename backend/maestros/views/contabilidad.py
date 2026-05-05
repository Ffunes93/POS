"""
contabilidad.py  (Sprint A — Mayo 2026)

Cambios vs versión anterior:
  ★ A1 ★ Reemplaza dict CA={...} por ContabConfigCuenta (parametrizable)
  ★ A2 ★ Generador de venta usa ImpIVAAlicuotas (discriminación por alícuota)
  ★ A3 ★ Idempotencia robusta con captura de IntegrityError
  ★ A4 ★ Apertura/Cierre filtran por ejercicio anterior (no toda la historia)
  ★ A5 ★ Autenticación opt-in vía ContabAuth + get_usuario_actual

Compatibilidad:
  - El dict CA_FALLBACK conserva los códigos originales como red de seguridad.
  - Si ImpIVAAlicuotas está vacío para una venta, fallback al cálculo legacy
    (todo a VENTAS_21 / IVA_DF_21).
  - Asientos de compra y recibo refactorizados parcialmente; soporte completo
    de retenciones llega en Sprint B.
"""
from decimal import Decimal
from django.db import transaction, IntegrityError
from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from ..models import (
    Ventas, Compras, Recibos,
    ContabPlanCuentas,
    ContabAsiento,
    ContabAsientoDet,
    ContabTipoAsiento,
    ContabSerieAsiento,
    ContabEjercicio,
    ContabModeloAsiento,
    ContabModeloAsientoDet,
    ContabConfigCuenta,         # ★ Sprint A · A1 ★
)
from ..impositivo_models import ImpIVAAlicuotas   # ★ Sprint A · A2 ★
from ..permissions import ContabAuth, get_usuario_actual   # ★ Sprint A · A5 ★


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────

D = Decimal('0.00')
TOL_AUTOMATICO = Decimal('0.02')   # tolerancia de cuadre para asientos auto
TOL_MANUAL     = Decimal('0.01')   # tolerancia más estricta para asientos manuales

# Fallback histórico (compat con versión pre-Sprint A).
# Sólo se usa si ContabConfigCuenta no tiene una entrada para el concepto.
CA_FALLBACK = {
    'CAJA':                    '1.1.01.001',
    'BANCO_DEFAULT':           '1.1.01.002',
    'DEUDORES_CC':             '1.1.03.001',
    'IVA_CF_21':               '1.1.04.001',
    'MERCADERIAS_DEFAULT':     '1.1.05.001',
    'PROVEEDORES':             '2.1.01.001',
    'IVA_DF_21':               '2.1.02.001',
    'VENTAS_21':               '4.1.01.001',
    'VENTAS_10_5':             '4.1.01.002',
    'VENTAS_EXENTAS':          '4.1.01.003',
    'RESULTADO_NO_ASIGNADO':   '3.3.01.001',
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de configuración (★ A1 ★)
# ─────────────────────────────────────────────────────────────────────────────

def _config():
    """
    Devuelve dict {concepto: codigo_cuenta} fusionando fallback + DB.
    DB pisa al fallback. Si un concepto no existe en ninguno, devuelve None.
    """
    mapa = dict(CA_FALLBACK)
    mapa.update(ContabConfigCuenta.cargar_mapa())
    return mapa


def _cuenta(config, concepto, requerida=False):
    """
    Resuelve un concepto a código de cuenta.
      - Si está, retorna el código.
      - Si NO está y requerida=False → retorna None (skip silencioso).
      - Si NO está y requerida=True  → lanza ValueError (rechaza el asiento).
    """
    cod = config.get(concepto)
    if not cod and requerida:
        raise ValueError(
            f"Concepto contable '{concepto}' no configurado. "
            f"Asigne una cuenta en /api/contab/Config/Cuentas/."
        )
    return cod


def _key_alicuota(alicuota):
    """
    Convierte un Decimal de alícuota a sufijo de concepto.
      21.00  → '21'
      10.50  → '10_5'
      27.00  → '27'
      2.50   → '2_5'
      0.00   → '0'
    """
    al = Decimal(str(alicuota or 0))
    if al == al.to_integral_value():
        return str(int(al))
    # Tiene decimales — usamos formato con underscore
    s = format(al.normalize(), 'f')      # "10.5", "2.5"
    return s.replace('.', '_')


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de asientos
# ─────────────────────────────────────────────────────────────────────────────

def _linea(asiento, codigo_cuenta, debe=D, haber=D, desc=''):
    """Crea una línea del asiento. Si codigo_cuenta es None, no hace nada."""
    if not codigo_cuenta:
        return None
    return ContabAsientoDet.objects.create(
        asiento=asiento, cuenta_id=codigo_cuenta,
        debe=Decimal(str(debe or 0)), haber=Decimal(str(haber or 0)),
        descripcion=desc[:100],
    )


def _ya_tiene_asiento(origen, movim_id):
    return ContabAsiento.objects.filter(
        origen=origen, origen_movim=movim_id, anulado=False
    ).exists()


def _get_ejercicio_para_fecha(fecha):
    """Devuelve el ejercicio (abierto) que contiene la fecha dada."""
    return (ContabEjercicio.objects
            .filter(fecha_inicio__lte=fecha, fecha_fin__gte=fecha)
            .order_by('-anio_inicio')
            .first())


def _get_ejercicio_activo():
    return ContabEjercicio.objects.filter(estado='A').order_by('-anio_inicio').first()


def _get_serie(codigo='DIA'):
    try:
        return ContabSerieAsiento.objects.get(pk=codigo)
    except ContabSerieAsiento.DoesNotExist:
        return None


def _siguiente_nro_serie(serie):
    """Incrementa atómicamente y retorna el próximo número."""
    if not serie:
        return None
    return serie.siguiente_numero()


def _crear_asiento(fecha, descripcion, origen, origen_movim=None,
                   usuario='', tipo_pk='001', serie_pk='DIA', estado='M'):
    """
    Crea el cabezal del asiento. La asignación de ejercicio se hace por la
    fecha del comprobante (NO por el ejercicio activo, para evitar que un
    asiento de noviembre 2024 caiga en el ejercicio 2025 abierto).
    """
    ejercicio    = _get_ejercicio_para_fecha(fecha) or _get_ejercicio_activo()
    tipo_asiento = ContabTipoAsiento.objects.filter(pk=tipo_pk).first()
    serie        = _get_serie(serie_pk)
    numero       = _siguiente_nro_serie(serie) if serie else None

    return ContabAsiento.objects.create(
        fecha        = fecha,
        descripcion  = descripcion[:255],
        origen       = origen,
        origen_movim = origen_movim,
        usuario      = (usuario or '')[:20],
        ejercicio    = ejercicio,
        tipo_asiento = tipo_asiento,
        serie        = serie,
        numero       = numero,
        estado       = estado,
    )


def _ajustar_redondeo(asiento, total_esperado, config):
    """
    Compara total del DEBE vs HABER y compensa la diferencia contra
    DIFERENCIA_REDONDEO. No falla si la cuenta no está configurada — en ese
    caso prefiere desbalancear con tolerancia laxa antes que romper.
    """
    td = sum((l.debe  for l in asiento.lineas.all()), D)
    th = sum((l.haber for l in asiento.lineas.all()), D)
    diff = td - th

    if abs(diff) <= Decimal('0.005'):
        return  # cuadra dentro de tolerancia

    cuenta_redondeo = _cuenta(config, 'DIFERENCIA_REDONDEO')
    if not cuenta_redondeo:
        return  # no configurado → quedará la pequeña diferencia

    if diff > 0:
        # Sobra debe → compensar con haber
        _linea(asiento, cuenta_redondeo, haber=diff, desc='Diferencia de redondeo')
    else:
        _linea(asiento, cuenta_redondeo, debe=abs(diff), desc='Diferencia de redondeo')


# ═════════════════════════════════════════════════════════════════════════════
# GENERADORES DE ASIENTOS AUTOMÁTICOS
# ═════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# ★ A2 ★  Asiento de venta — usa ImpIVAAlicuotas + percepciones + exentas
# ─────────────────────────────────────────────────────────────────────────────

def _generar_asiento_venta(venta, config=None):
    """
    Genera asiento contable a partir de un registro de Ventas.

    Mejoras Sprint A:
      • Usa ImpIVAAlicuotas para discriminar 21 / 10.5 / 27 / 5 / 2.5 / 0
        (cuentas separadas por alícuota tanto en ventas como en IVA DF).
      • Reconoce ventas exentas (campo Ventas.exento).
      • Reconoce percepciones IIBB (CABA, Bs.As.) y RG 5329.
      • Reconoce impuestos internos.
      • Diferencia de redondeo va a DIFERENCIA_REDONDEO (no a VENTAS_21).

    Fallback:
      • Si no hay filas en ImpIVAAlicuotas, usa el comportamiento legacy
        (todo el neto a VENTAS_21, todo el IVA a IVA_DF_21).
    """
    if _ya_tiene_asiento('VTA', venta.movim):
        return None

    if config is None:
        config = _config()

    total = Decimal(str(venta.tot_general or 0))
    if total <= 0:
        return None

    cond_venta = str(getattr(venta, 'cond_venta', '') or '')
    cuenta_activo = (
        _cuenta(config, 'DEUDORES_CC', requerida=True) if cond_venta == '2'
        else _cuenta(config, 'CAJA',     requerida=True)
    )

    desc_venta = f"Venta {getattr(venta, 'cod_comprob', '')} N° {venta.nro_comprob}"

    try:
        with transaction.atomic():
            a = _crear_asiento(
                venta.fecha_fact, desc_venta, 'VTA', venta.movim,
                getattr(venta, 'usuario', '') or ''
            )

            # 1. DEBE: lo que entra (efectivo o crédito)
            _linea(a, cuenta_activo, debe=total, desc='Cobro/Crédito por venta')

            # 2. HABER: ingresos discriminados por alícuota (★ A2 fix ★)
            filas_iva = list(
                ImpIVAAlicuotas.objects.filter(circuito='V', movim=venta.movim)
            )

            if filas_iva:
                for fila in filas_iva:
                    sufijo = _key_alicuota(fila.alicuota)
                    cta_venta = _cuenta(config, f'VENTAS_{sufijo}')
                    cta_iva   = _cuenta(config, f'IVA_DF_{sufijo}')

                    # Si no hay cuenta específica para esta alícuota, fallback a 21
                    if not cta_venta:
                        cta_venta = _cuenta(config, 'VENTAS_21', requerida=True)
                    if not cta_iva and fila.iva > 0:
                        cta_iva = _cuenta(config, 'IVA_DF_21', requerida=True)

                    if fila.neto_gravado > 0:
                        _linea(a, cta_venta, haber=fila.neto_gravado,
                               desc=f"Ventas {fila.alicuota}%")
                    if fila.iva > 0:
                        _linea(a, cta_iva, haber=fila.iva,
                               desc=f"IVA Débito Fiscal {fila.alicuota}%")
            else:
                # Fallback legacy: todo a 21%
                neto = Decimal(str(venta.neto  or 0))
                iva  = Decimal(str(venta.iva_1 or 0))
                if neto > 0:
                    _linea(a, _cuenta(config, 'VENTAS_21', requerida=True),
                           haber=neto, desc='Ventas (sin discriminar alícuota)')
                if iva > 0:
                    _linea(a, _cuenta(config, 'IVA_DF_21', requerida=True),
                           haber=iva, desc='IVA Débito Fiscal (sin discriminar)')

            # 3. Ventas exentas
            exento = Decimal(str(getattr(venta, 'exento', 0) or 0))
            if exento > 0:
                cta_ex = _cuenta(config, 'VENTAS_EXENTAS')
                if cta_ex:
                    _linea(a, cta_ex, haber=exento, desc='Ventas exentas')

            # 4. Percepciones practicadas (pasivos a depositar)
            for campo, concepto, label in [
                ('perce_caba', 'PERCEPCION_IIBB_CABA_PRACTICADA', 'Percepción IIBB CABA'),
                ('perce_bsas', 'PERCEPCION_IIBB_BSAS_PRACTICADA', 'Percepción IIBB Bs.As.'),
                ('perce_5329', 'PERCEPCION_5329_PRACTICADA',      'Percepción RG 5329'),
            ]:
                valor = Decimal(str(getattr(venta, campo, 0) or 0))
                if valor > 0:
                    cta = _cuenta(config, concepto)
                    if cta:
                        _linea(a, cta, haber=valor, desc=label)

            # 5. Impuestos internos
            ii = Decimal(str(getattr(venta, 'impuestos_internos', 0) or 0))
            if ii > 0:
                cta_ii = _cuenta(config, 'IMPUESTOS_INTERNOS')
                if cta_ii:
                    _linea(a, cta_ii, haber=ii, desc='Impuestos Internos')

            # 6. Cuadre con cuenta de redondeo
            _ajustar_redondeo(a, total, config)

        return a

    except IntegrityError:
        # ★ A3 ★ Otro proceso ya creó el asiento mientras corríamos.
        # Devolvemos el existente sin error.
        return ContabAsiento.objects.filter(
            origen='VTA', origen_movim=venta.movim, anulado=False
        ).first()


# ─────────────────────────────────────────────────────────────────────────────
# Asiento de compra (versión Sprint A — sin retenciones todavía)
# ─────────────────────────────────────────────────────────────────────────────

def _generar_asiento_compra(compra, config=None):
    """
    Versión Sprint A — incorpora discriminación por alícuota IVA_CF.
    Soporte completo de retenciones practicadas → Sprint B.
    """
    if _ya_tiene_asiento('CMP', compra.movim):
        return None

    if config is None:
        config = _config()

    total = Decimal(str(compra.tot_general or 0))
    if total <= 0:
        return None

    cuenta_pasivo = (
        _cuenta(config, 'CAJA', requerida=True)
        if (getattr(compra, 'observac', '') or '').upper() == 'CONTADO'
        else _cuenta(config, 'PROVEEDORES', requerida=True)
    )

    desc = f"Compra {getattr(compra, 'cod_comprob', '')} N° {compra.nro_comprob}"

    try:
        with transaction.atomic():
            a = _crear_asiento(
                compra.fecha_comprob, desc, 'CMP', compra.movim,
                getattr(compra, 'usuario', '') or ''
            )

            # IVA Crédito Fiscal por alícuota (★ A2 ★)
            filas_iva = list(
                ImpIVAAlicuotas.objects.filter(circuito='C', movim=compra.movim)
            )

            if filas_iva:
                neto_total = D
                for fila in filas_iva:
                    sufijo = _key_alicuota(fila.alicuota)
                    cta_iva = _cuenta(config, f'IVA_CF_{sufijo}')
                    if not cta_iva and fila.iva > 0:
                        cta_iva = _cuenta(config, 'IVA_CF_21', requerida=True)

                    neto_total += fila.neto_gravado
                    if fila.iva > 0:
                        _linea(a, cta_iva, debe=fila.iva,
                               desc=f"IVA Crédito Fiscal {fila.alicuota}%")

                if neto_total > 0:
                    _linea(a, _cuenta(config, 'MERCADERIAS_DEFAULT', requerida=True),
                           debe=neto_total, desc='Compra de mercaderías')
            else:
                # Fallback legacy: todo 21%
                neto = Decimal(str(compra.neto  or 0))
                iva  = Decimal(str(compra.iva_1 or 0))
                if neto > 0:
                    _linea(a, _cuenta(config, 'MERCADERIAS_DEFAULT', requerida=True),
                           debe=neto, desc='Compra de mercaderías')
                if iva > 0:
                    _linea(a, _cuenta(config, 'IVA_CF_21', requerida=True),
                           debe=iva, desc='IVA Crédito Fiscal')

            # Pasivo
            _linea(a, cuenta_pasivo, haber=total, desc='Obligación de compra')

            # Cuadre
            _ajustar_redondeo(a, total, config)

        return a

    except IntegrityError:
        return ContabAsiento.objects.filter(
            origen='CMP', origen_movim=compra.movim, anulado=False
        ).first()


# ─────────────────────────────────────────────────────────────────────────────
# Asiento de recibo (versión Sprint A — simplificado, mejoras en Sprint B)
# ─────────────────────────────────────────────────────────────────────────────

def _generar_asiento_recibo(recibo, config=None):
    """
    Versión Sprint A — usa cuentas configurables.
    Soporte completo de cheques/tarjetas/retenciones sufridas → Sprint B.
    """
    if _ya_tiene_asiento('REC', recibo.numero):
        return None

    if config is None:
        config = _config()

    importe = Decimal(str(recibo.importe or 0))
    if importe <= 0:
        return None

    try:
        with transaction.atomic():
            a = _crear_asiento(
                recibo.fecha,
                f"Recibo N° {recibo.numero} - Cliente {recibo.cliente}",
                'REC', recibo.numero,
                getattr(recibo, 'usuario', '') or '',
            )
            _linea(a, _cuenta(config, 'CAJA', requerida=True),
                   debe=importe, desc='Cobro de cta. cte.')
            _linea(a, _cuenta(config, 'DEUDORES_CC', requerida=True),
                   haber=importe, desc='Cancelación deuda cliente')
        return a

    except IntegrityError:
        return ContabAsiento.objects.filter(
            origen='REC', origen_movim=recibo.numero, anulado=False
        ).first()


# ─────────────────────────────────────────────────────────────────────────────
# Anulación con contraasiento
# ─────────────────────────────────────────────────────────────────────────────

def _anular_asiento(origen, origen_movim, usuario='sistema'):
    """Genera contraasiento sin mutar el asiento original (anulado=True solo)."""
    original = ContabAsiento.objects.filter(
        origen=origen, origen_movim=origen_movim, anulado=False
    ).first()
    if not original:
        return None

    with transaction.atomic():
        # Marcar original (esto libera el origen_movim_activo via save())
        original.anulado = True
        original.estado  = 'A'
        original.save(update_fields=['anulado', 'estado', 'origen_movim_activo'])

        inv = _crear_asiento(
            timezone.now().date(),
            f"ANULACIÓN de Asiento #{original.id} — {original.descripcion}"[:255],
            'ANU', original.id, usuario,
        )
        inv.asiento_origen = original
        inv.save(update_fields=['asiento_origen'])
        for linea in original.lineas.all():
            ContabAsientoDet.objects.create(
                asiento=inv, cuenta=linea.cuenta,
                debe=linea.haber, haber=linea.debe,
                descripcion=f"Anulación: {linea.descripcion}"[:100],
            )
    return inv


# ═════════════════════════════════════════════════════════════════════════════
# API — Configuración: Tipos de Asiento / Series / Ejercicios / Modelos
# (Sin cambios funcionales vs versión anterior; sólo se agrega @permission)
# ═════════════════════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([ContabAuth])
def GestionTiposAsiento(request):
    if request.method == 'GET':
        data = list(ContabTipoAsiento.objects.values(
            'codigo', 'descripcion', 'habilitado', 'excluye_eecc'
        ))
        return Response(data)

    d = request.data
    codigo = d.get('codigo', '').strip()
    if not codigo:
        return Response({'error': 'Código requerido'}, status=400)
    obj, created = ContabTipoAsiento.objects.update_or_create(
        codigo=codigo,
        defaults={
            'descripcion':  d.get('descripcion', ''),
            'habilitado':   bool(d.get('habilitado', True)),
            'excluye_eecc': bool(d.get('excluye_eecc', False)),
        }
    )
    return Response({'ok': True, 'creado': created, 'codigo': obj.codigo})


@api_view(['PUT', 'DELETE'])
@permission_classes([ContabAuth])
def DetalleTipoAsiento(request, pk):
    try:
        obj = ContabTipoAsiento.objects.get(pk=pk)
    except ContabTipoAsiento.DoesNotExist:
        return Response({'error': 'No encontrado'}, status=404)

    if request.method == 'DELETE':
        if ContabAsiento.objects.filter(tipo_asiento=obj).exists():
            return Response({'error': 'No se puede eliminar: tiene asientos asociados'}, status=400)
        obj.delete()
        return Response({'ok': True})

    d = request.data
    obj.descripcion  = d.get('descripcion', obj.descripcion)
    obj.habilitado   = bool(d.get('habilitado', obj.habilitado))
    obj.excluye_eecc = bool(d.get('excluye_eecc', obj.excluye_eecc))
    obj.save()
    return Response({'ok': True})


@api_view(['GET', 'POST'])
@permission_classes([ContabAuth])
def GestionSeries(request):
    if request.method == 'GET':
        data = list(ContabSerieAsiento.objects.values(
            'codigo', 'descripcion', 'ultimo_nro', 'habilitada'
        ))
        return Response(data)

    d = request.data
    codigo = d.get('codigo', '').strip()
    if not codigo:
        return Response({'error': 'Código requerido'}, status=400)
    obj, created = ContabSerieAsiento.objects.update_or_create(
        codigo=codigo,
        defaults={
            'descripcion': d.get('descripcion', ''),
            'ultimo_nro':  int(d.get('ultimo_nro', 0)),
            'habilitada':  bool(d.get('habilitada', True)),
        }
    )
    return Response({'ok': True, 'creado': created, 'codigo': obj.codigo})


@api_view(['PUT'])
@permission_classes([ContabAuth])
def DetalleSerie(request, pk):
    try:
        obj = ContabSerieAsiento.objects.get(pk=pk)
    except ContabSerieAsiento.DoesNotExist:
        return Response({'error': 'No encontrado'}, status=404)
    d = request.data
    obj.descripcion = d.get('descripcion', obj.descripcion)
    obj.ultimo_nro  = int(d.get('ultimo_nro', obj.ultimo_nro))
    obj.habilitada  = bool(d.get('habilitada', obj.habilitada))
    obj.save()
    return Response({'ok': True})


@api_view(['GET', 'POST'])
@permission_classes([ContabAuth])
def GestionEjercicios(request):
    if request.method == 'GET':
        data = list(ContabEjercicio.objects.values(
            'id', 'anio_inicio', 'anio_fin', 'fecha_inicio', 'fecha_fin',
            'estado', 'descripcion', 'usa_ajuste_inflacion'
        ))
        return Response(data)

    d = request.data
    try:
        obj = ContabEjercicio.objects.create(
            anio_inicio  = int(d['anio_inicio']),
            anio_fin     = int(d['anio_fin']),
            fecha_inicio = d['fecha_inicio'],
            fecha_fin    = d['fecha_fin'],
            estado       = d.get('estado', 'A'),
            descripcion  = d.get('descripcion', ''),
            usa_ajuste_inflacion = bool(d.get('usa_ajuste_inflacion', False)),
        )
        return Response({'ok': True, 'id': obj.id}, status=201)
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([ContabAuth])
def DetalleEjercicio(request, pk):
    try:
        obj = ContabEjercicio.objects.get(pk=pk)
    except ContabEjercicio.DoesNotExist:
        return Response({'error': 'No encontrado'}, status=404)

    if request.method == 'GET':
        return Response({
            'id': obj.id, 'anio_inicio': obj.anio_inicio, 'anio_fin': obj.anio_fin,
            'fecha_inicio': obj.fecha_inicio, 'fecha_fin': obj.fecha_fin,
            'estado': obj.estado, 'descripcion': obj.descripcion,
            'usa_ajuste_inflacion': obj.usa_ajuste_inflacion,
        })

    if request.method == 'DELETE':
        if obj.asientos.exists():
            return Response({'error': 'No se puede eliminar: tiene asientos asociados'}, status=400)
        obj.delete()
        return Response({'ok': True})

    d = request.data
    obj.descripcion           = d.get('descripcion', obj.descripcion)
    obj.estado                = d.get('estado', obj.estado)
    obj.usa_ajuste_inflacion  = bool(d.get('usa_ajuste_inflacion', obj.usa_ajuste_inflacion))
    if 'fecha_inicio' in d:
        obj.fecha_inicio = d['fecha_inicio']
    if 'fecha_fin' in d:
        obj.fecha_fin = d['fecha_fin']
    obj.save()
    return Response({'ok': True})


@api_view(['GET', 'POST'])
@permission_classes([ContabAuth])
def GestionModelos(request):
    if request.method == 'GET':
        modelos = ContabModeloAsiento.objects.prefetch_related('lineas__cuenta').all()
        data = []
        for m in modelos:
            data.append({
                'codigo':       m.codigo,
                'descripcion':  m.descripcion,
                'habilitado':   m.habilitado,
                'tipo_asiento': m.tipo_asiento_id,
                'lineas': [
                    {
                        'id':          l.id,
                        'orden':       l.orden,
                        'cuenta':      l.cuenta_id,
                        'nombre':      l.cuenta.nombre,
                        'tipo':        l.tipo,
                        'importe':     float(l.importe),
                        'descripcion': l.descripcion,
                    }
                    for l in m.lineas.all()
                ]
            })
        return Response(data)

    d = request.data
    codigo = d.get('codigo', '').strip()
    if not codigo:
        return Response({'error': 'Código requerido'}, status=400)

    with transaction.atomic():
        modelo, _ = ContabModeloAsiento.objects.update_or_create(
            codigo=codigo,
            defaults={
                'descripcion':  d.get('descripcion', ''),
                'habilitado':   bool(d.get('habilitado', True)),
                'tipo_asiento_id': d.get('tipo_asiento') or None,
            }
        )
        ContabModeloAsientoDet.objects.filter(modelo=modelo).delete()
        for i, l in enumerate(d.get('lineas', [])):
            ContabModeloAsientoDet.objects.create(
                modelo=modelo,
                orden=i,
                cuenta_id=l['cuenta'],
                tipo=l['tipo'],
                importe=Decimal(str(l.get('importe', 0))),
                descripcion=l.get('descripcion', ''),
            )
    return Response({'ok': True, 'codigo': modelo.codigo})


@api_view(['GET', 'DELETE'])
@permission_classes([ContabAuth])
def DetalleModelo(request, pk):
    try:
        modelo = ContabModeloAsiento.objects.get(pk=pk)
    except ContabModeloAsiento.DoesNotExist:
        return Response({'error': 'No encontrado'}, status=404)

    if request.method == 'DELETE':
        modelo.delete()
        return Response({'ok': True})

    lineas = [
        {'id': l.id, 'orden': l.orden, 'cuenta': l.cuenta_id,
         'nombre': l.cuenta.nombre, 'tipo': l.tipo,
         'importe': float(l.importe), 'descripcion': l.descripcion}
        for l in modelo.lineas.all()
    ]
    return Response({
        'codigo': modelo.codigo, 'descripcion': modelo.descripcion,
        'habilitado': modelo.habilitado, 'tipo_asiento': modelo.tipo_asiento_id,
        'lineas': lineas,
    })


# ═════════════════════════════════════════════════════════════════════════════
# ★ A4 ★  Asientos automáticos (Apertura, Cierre, Inflación, Dif. Cambio)
# ═════════════════════════════════════════════════════════════════════════════

TIPOS_AUTO = {
    'apertura':     ('APE', 'Asiento de Apertura'),
    'cierre':       ('CIE', 'Asiento de Cierre'),
    'inflacion':    ('INF', 'Asiento de Ajuste por Inflación'),
    'dif_cambio':   ('DIF', 'Asiento de Diferencia de Cambio'),
    'refundicion':  ('AJU', 'Refundición de Cuentas de Resultado'),
}


@api_view(['POST'])
@permission_classes([ContabAuth])
def GenerarAsientoAutomatico(request):
    """
    Genera un asiento automático. Mejoras Sprint A:
      • Apertura ahora REQUIERE ejercicio_id y filtra los movimientos del
        ejercicio anterior (no acumula toda la historia).
      • Cierre REQUIERE ejercicio_id y procesa solo ese ejercicio.

    Payload:
    {
      "tipo": "apertura" | "cierre" | "inflacion" | "dif_cambio" | "refundicion",
      "ejercicio_id": 5,         (REQUERIDO para apertura/cierre)
      "fecha": "2026-01-01",
      "lineas": [...]            (opcional para tipos personalizados)
    }
    """
    d    = request.data
    tipo = d.get('tipo', '').lower()

    if tipo not in TIPOS_AUTO:
        return Response({'error': f'Tipo inválido. Válidos: {list(TIPOS_AUTO.keys())}'},
                        status=400)

    origen_code, desc_default = TIPOS_AUTO[tipo]
    fecha     = d.get('fecha', timezone.now().date().isoformat())
    usuario   = get_usuario_actual(request, 'sistema')   # ★ A5 ★
    lineas_in = d.get('lineas', [])

    if tipo == 'cierre' and not lineas_in:
        return _asiento_cierre(fecha, usuario, d.get('ejercicio_id'))

    if tipo == 'apertura' and not lineas_in:
        return _asiento_apertura(fecha, usuario, d.get('ejercicio_id'))

    if not lineas_in:
        return Response({'error': 'Se requieren lineas para este tipo de asiento'},
                        status=400)

    total_debe  = sum(Decimal(str(l.get('debe', 0)))  for l in lineas_in)
    total_haber = sum(Decimal(str(l.get('haber', 0))) for l in lineas_in)
    if abs(total_debe - total_haber) > TOL_AUTOMATICO:
        return Response({'error': f'No cuadra: D={total_debe} H={total_haber}'},
                        status=400)

    with transaction.atomic():
        a = _crear_asiento(fecha, desc_default, origen_code, usuario=usuario)
        for l in lineas_in:
            _linea(a, l['cuenta'],
                   debe=Decimal(str(l.get('debe', 0))),
                   haber=Decimal(str(l.get('haber', 0))),
                   desc=l.get('descripcion', ''))

    return Response({'ok': True, 'id': a.id, 'descripcion': desc_default})


def _asiento_apertura(fecha, usuario, ejercicio_id):
    """
    ★ A4 fix ★ Genera apertura tomando saldos SOLO del ejercicio anterior
    al indicado en `ejercicio_id`. Antes traía todos los movimientos de la
    historia, lo cual duplicaba aperturas previas.
    """
    if not ejercicio_id:
        return Response({'error': 'apertura requiere ejercicio_id (el ejercicio NUEVO que se abre)'},
                        status=400)

    try:
        ej_nuevo = ContabEjercicio.objects.get(pk=ejercicio_id)
    except ContabEjercicio.DoesNotExist:
        return Response({'error': f'Ejercicio {ejercicio_id} no existe'}, status=404)

    # Encontrar el ejercicio anterior cronológicamente
    ej_anterior = (ContabEjercicio.objects
                   .filter(fecha_fin__lt=ej_nuevo.fecha_inicio)
                   .order_by('-fecha_fin')
                   .first())

    if not ej_anterior:
        return Response({
            'error': 'No hay ejercicio anterior cerrado. La apertura del primer '
                     'ejercicio debe cargarse manualmente con saldos iniciales.'
        }, status=400)

    # Saldos al cierre del ejercicio anterior — solo Activo, Pasivo y PN
    qs = (
        ContabAsientoDet.objects
        .filter(
            asiento__anulado=False,
            asiento__estado='M',
            asiento__fecha__gte=ej_anterior.fecha_inicio,
            asiento__fecha__lte=ej_anterior.fecha_fin,
            cuenta__tipo__in=['A', 'P', 'PN'],
        )
        .values('cuenta_id', 'cuenta__tipo', 'cuenta__saldo_tipo')
        .annotate(suma_debe=Sum('debe'), suma_haber=Sum('haber'))
    )

    if not qs.exists():
        return Response({'error': f'No hay movimientos en el ejercicio {ej_anterior} '
                                  'para generar apertura'}, status=400)

    lineas_ape = []
    for row in qs:
        sd = Decimal(str(row['suma_debe']  or 0))
        sh = Decimal(str(row['suma_haber'] or 0))
        saldo = sd - sh if row['cuenta__saldo_tipo'] == 'D' else sh - sd
        if abs(saldo) > Decimal('0.01'):
            if row['cuenta__saldo_tipo'] == 'D':
                lineas_ape.append({'cuenta': row['cuenta_id'], 'debe': saldo, 'haber': D})
            else:
                lineas_ape.append({'cuenta': row['cuenta_id'], 'debe': D, 'haber': saldo})

    if not lineas_ape:
        return Response({'error': 'No hay saldos significativos para aperturar'}, status=400)

    desc = f'Asiento de Apertura — Ejercicio {ej_nuevo.anio_inicio}'

    with transaction.atomic():
        a = _crear_asiento(fecha, desc, 'APE', usuario=usuario)
        for l in lineas_ape:
            _linea(a, l['cuenta'], debe=l['debe'], haber=l['haber'], desc='Apertura')

    return Response({
        'ok': True, 'id': a.id,
        'lineas_generadas': len(lineas_ape),
        'ejercicio_anterior': str(ej_anterior),
        'ejercicio_nuevo': str(ej_nuevo),
    })


def _asiento_cierre(fecha, usuario, ejercicio_id):
    """
    ★ A4 fix ★ Cierre filtra solo el ejercicio indicado.
    Refunde cuentas I y E del ejercicio contra Resultado del Ejercicio.
    """
    if not ejercicio_id:
        return Response({'error': 'cierre requiere ejercicio_id'}, status=400)

    try:
        ejercicio = ContabEjercicio.objects.get(pk=ejercicio_id)
    except ContabEjercicio.DoesNotExist:
        return Response({'error': f'Ejercicio {ejercicio_id} no existe'}, status=404)

    config = _config()
    cta_resultado = _cuenta(config, 'RESULTADO_DEL_EJERCICIO') \
                    or _cuenta(config, 'RESULTADO_NO_ASIGNADO', requerida=True)

    qs = (
        ContabAsientoDet.objects
        .filter(
            asiento__anulado=False,
            asiento__estado='M',
            asiento__fecha__gte=ejercicio.fecha_inicio,
            asiento__fecha__lte=ejercicio.fecha_fin,
            cuenta__tipo__in=['I', 'E'],
        )
        .values('cuenta_id', 'cuenta__tipo', 'cuenta__nombre')
        .annotate(suma_debe=Sum('debe'), suma_haber=Sum('haber'))
    )

    if not qs.exists():
        return Response({'error': f'No hay cuentas de resultado para cerrar en {ejercicio}'},
                        status=400)

    resultado_neto = D
    lineas_cie = []

    for row in qs:
        sd = Decimal(str(row['suma_debe']  or 0))
        sh = Decimal(str(row['suma_haber'] or 0))
        if row['cuenta__tipo'] == 'I':
            saldo = sh - sd
            resultado_neto += saldo
            if abs(saldo) > Decimal('0.01'):
                lineas_cie.append({
                    'cuenta': row['cuenta_id'],
                    'debe': saldo, 'haber': D,
                    'desc': f"Cierre — {row['cuenta__nombre']}",
                })
        else:
            saldo = sd - sh
            resultado_neto -= saldo
            if abs(saldo) > Decimal('0.01'):
                lineas_cie.append({
                    'cuenta': row['cuenta_id'],
                    'debe': D, 'haber': saldo,
                    'desc': f"Cierre — {row['cuenta__nombre']}",
                })

    if not lineas_cie:
        return Response({'error': 'No hay saldos significativos para cerrar'}, status=400)

    if abs(resultado_neto) > Decimal('0.01'):
        if resultado_neto > 0:
            lineas_cie.append({'cuenta': cta_resultado, 'debe': D, 'haber': resultado_neto,
                               'desc': 'Resultado del ejercicio (ganancia)'})
        else:
            lineas_cie.append({'cuenta': cta_resultado, 'debe': abs(resultado_neto), 'haber': D,
                               'desc': 'Resultado del ejercicio (pérdida)'})

    desc = f'Asiento de Cierre — {ejercicio} — Refundición de Resultados'

    with transaction.atomic():
        a = _crear_asiento(fecha, desc, 'CIE', usuario=usuario)
        for l in lineas_cie:
            _linea(a, l['cuenta'], debe=l['debe'], haber=l['haber'], desc=l['desc'])

    return Response({
        'ok': True, 'id': a.id,
        'resultado_neto': float(resultado_neto),
        'ejercicio': str(ejercicio),
        'lineas_generadas': len(lineas_cie),
    })


# ═════════════════════════════════════════════════════════════════════════════
# Mayorización / Anulación
# ═════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([ContabAuth])
def MayorizarAsiento(request, asiento_id):
    try:
        a = ContabAsiento.objects.get(id=asiento_id)
    except ContabAsiento.DoesNotExist:
        return Response({'error': 'Asiento no encontrado'}, status=404)
    if a.estado == 'A':
        return Response({'error': 'El asiento está anulado'}, status=400)
    if a.estado == 'M':
        return Response({'error': 'El asiento ya está mayorizado'}, status=400)
    a.estado = 'M'
    a.save(update_fields=['estado'])
    return Response({'ok': True, 'id': a.id, 'estado': 'M'})


@api_view(['POST'])
@permission_classes([ContabAuth])
def AnularAsientoId(request, asiento_id):
    try:
        a = ContabAsiento.objects.get(id=asiento_id)
    except ContabAsiento.DoesNotExist:
        return Response({'error': 'Asiento no encontrado'}, status=404)

    if a.anulado:
        return Response({'error': 'El asiento ya está anulado'}, status=400)

    usuario = get_usuario_actual(request)
    inv = _anular_asiento(a.origen, a.origen_movim or a.id, usuario=usuario)

    if not inv:
        # Anulación directa por id (asientos sin origen_movim)
        with transaction.atomic():
            a.anulado = True
            a.estado  = 'A'
            a.save(update_fields=['anulado', 'estado', 'origen_movim_activo'])
            inv = _crear_asiento(
                timezone.now().date(),
                f"ANULACIÓN de Asiento #{a.id} — {a.descripcion}"[:255],
                'ANU', a.id, usuario,
            )
            inv.asiento_origen = a
            inv.save(update_fields=['asiento_origen'])
            for linea in a.lineas.all():
                ContabAsientoDet.objects.create(
                    asiento=inv, cuenta=linea.cuenta,
                    debe=linea.haber, haber=linea.debe,
                    descripcion=f"Anulación: {linea.descripcion}"[:100],
                )

    return Response({'ok': True, 'id_contraasiento': inv.id if inv else None})


# ═════════════════════════════════════════════════════════════════════════════
# Consulta de Saldos
# ═════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([ContabAuth])
def ConsultaSaldos(request):
    desde   = request.query_params.get('desde')
    hasta   = request.query_params.get('hasta')
    tipos   = request.query_params.get('tipo', '').split(',')
    cuenta  = request.query_params.get('cuenta', '')

    qs = ContabAsientoDet.objects.filter(
        asiento__anulado=False,
        asiento__estado='M',
    )
    if desde:   qs = qs.filter(asiento__fecha__gte=desde)
    if hasta:   qs = qs.filter(asiento__fecha__lte=hasta)
    if cuenta:  qs = qs.filter(cuenta_id=cuenta)

    agg = (qs.values('cuenta_id')
             .annotate(suma_debe=Sum('debe'), suma_haber=Sum('haber'))
             .order_by('cuenta_id'))

    cuentas_filter = ContabPlanCuentas.objects.filter(es_imputable=True)
    if tipos and tipos[0]:
        cuentas_filter = cuentas_filter.filter(tipo__in=tipos)
    cuentas_map = {c.codigo: c for c in cuentas_filter}

    filas = []
    for row in agg:
        cod = row['cuenta_id']
        if cod not in cuentas_map:
            continue
        c  = cuentas_map[cod]
        sd = Decimal(str(row['suma_debe']  or 0))
        sh = Decimal(str(row['suma_haber'] or 0))
        saldo = (sd - sh) if c.saldo_tipo == 'D' else (sh - sd)
        filas.append({
            'codigo':       cod,
            'nombre':       c.nombre,
            'tipo':         c.tipo,
            'saldo_tipo':   c.saldo_tipo,
            'suma_debe':    float(sd),
            'suma_haber':   float(sh),
            'saldo':        float(saldo),
        })

    return Response({'filas': filas, 'total': len(filas)})


# ═════════════════════════════════════════════════════════════════════════════
# Importación
# ═════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([ContabAuth])
def ImportarAsientos(request):
    asientos_in = request.data.get('asientos', [])
    if not asientos_in:
        return Response({'error': 'No se recibieron asientos'}, status=400)

    usuario = get_usuario_actual(request, 'importacion')
    importados = 0
    errores    = []

    for i, asi in enumerate(asientos_in):
        try:
            lineas = asi.get('lineas', [])
            if len(lineas) < 2:
                errores.append(f"Asiento {i}: debe tener al menos 2 líneas")
                continue

            td = sum(Decimal(str(l.get('debe',  0))) for l in lineas)
            th = sum(Decimal(str(l.get('haber', 0))) for l in lineas)
            if abs(td - th) > TOL_AUTOMATICO:
                errores.append(f"Asiento {i}: no cuadra (D={td} H={th})")
                continue

            with transaction.atomic():
                a = _crear_asiento(
                    fecha       = asi['fecha'],
                    descripcion = asi.get('descripcion', 'Asiento importado'),
                    origen      = 'IMP',
                    usuario     = usuario,
                    tipo_pk     = asi.get('tipo_asiento', '001'),
                    serie_pk    = asi.get('serie', 'DIA'),
                    estado      = 'M',
                )
                for l in lineas:
                    _linea(a, l['cuenta'],
                           debe=Decimal(str(l.get('debe',  0))),
                           haber=Decimal(str(l.get('haber', 0))),
                           desc=l.get('descripcion', ''))
            importados += 1
        except Exception as e:
            errores.append(f"Asiento {i}: {str(e)}")

    return Response({
        'ok':         len(errores) == 0,
        'importados': importados,
        'errores':    errores,
        'total':      len(asientos_in),
    })


# ═════════════════════════════════════════════════════════════════════════════
# Sincronización masiva — usa los nuevos generadores
# ═════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([ContabAuth])
def SincronizarAsientos(request):
    """
    Sprint A · Optimizado:
      • Carga config UNA sola vez para toda la sincronización
      • Maneja IntegrityError silenciosamente (idempotencia DB)
    """
    config = _config()
    generados = {'ventas': 0, 'compras': 0, 'recibos': 0, 'errores': []}

    ids_vta = set(ContabAsiento.objects.filter(origen='VTA', anulado=False)
                                       .values_list('origen_movim', flat=True))
    for v in Ventas.objects.filter(~Q(anulado='S')).exclude(movim__in=ids_vta):
        try:
            if _generar_asiento_venta(v, config=config):
                generados['ventas'] += 1
        except Exception as e:
            generados['errores'].append(f"VTA movim={v.movim}: {e}")

    ids_cmp = set(ContabAsiento.objects.filter(origen='CMP', anulado=False)
                                       .values_list('origen_movim', flat=True))
    for c in Compras.objects.filter(~Q(anulado='S')).exclude(movim__in=ids_cmp):
        try:
            if _generar_asiento_compra(c, config=config):
                generados['compras'] += 1
        except Exception as e:
            generados['errores'].append(f"CMP movim={c.movim}: {e}")

    ids_rec = set(ContabAsiento.objects.filter(origen='REC', anulado=False)
                                       .values_list('origen_movim', flat=True))
    for r in Recibos.objects.filter(~Q(anulado='S')).exclude(numero__in=ids_rec):
        try:
            if _generar_asiento_recibo(r, config=config):
                generados['recibos'] += 1
        except Exception as e:
            generados['errores'].append(f"REC nro={r.numero}: {e}")

    return Response({
        'ok': True,
        'generados': generados,
        'total': generados['ventas'] + generados['compras'] + generados['recibos'],
    })


# ═════════════════════════════════════════════════════════════════════════════
# Plan de Cuentas
# ═════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([ContabAuth])
def ListarPlanCuentas(request):
    solo_imputables = request.query_params.get('imputables') == '1'
    tipo_filtro     = request.query_params.get('tipo', '')
    qs = ContabPlanCuentas.objects.filter(activa=True)
    if solo_imputables:
        qs = qs.filter(es_imputable=True)
    if tipo_filtro:
        qs = qs.filter(tipo__in=tipo_filtro.split(','))
    data = [
        {'codigo': c.codigo, 'nombre': c.nombre, 'tipo': c.tipo,
         'nivel': c.nivel, 'padre': c.padre_id,
         'es_imputable': c.es_imputable, 'saldo_tipo': c.saldo_tipo,
         'activa': c.activa, 'codigo_alt': c.codigo_alt,
         'col_impresion': c.col_impresion}
        for c in qs
    ]
    return Response(data)


@api_view(['POST'])
@permission_classes([ContabAuth])
def GuardarCuenta(request):
    d = request.data
    codigo = d.get('codigo', '').strip()
    if not codigo:
        return Response({'ok': False, 'error': 'Código requerido'}, status=400)
    obj, created = ContabPlanCuentas.objects.update_or_create(
        codigo=codigo,
        defaults={
            'nombre':        d.get('nombre', ''),
            'tipo':          d.get('tipo', 'A'),
            'nivel':         int(d.get('nivel', 4)),
            'padre_id':      d.get('padre') or None,
            'es_imputable':  bool(d.get('es_imputable', True)),
            'saldo_tipo':    d.get('saldo_tipo', 'D'),
            'activa':        bool(d.get('activa', True)),
            'observaciones': d.get('observaciones', ''),
            'codigo_alt':    d.get('codigo_alt', ''),
            'col_impresion': int(d.get('col_impresion', 1)),
        },
    )
    return Response({'ok': True, 'creado': created, 'codigo': obj.codigo})


# ═════════════════════════════════════════════════════════════════════════════
# CRUD Asientos
# ═════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([ContabAuth])
def ListarAsientos(request):
    desde  = request.query_params.get('desde')
    hasta  = request.query_params.get('hasta')
    origen = request.query_params.get('origen', '')
    estado = request.query_params.get('estado', '')
    tipo   = request.query_params.get('tipo_asiento', '')

    qs = ContabAsiento.objects.filter(anulado=False)
    if desde:   qs = qs.filter(fecha__gte=desde)
    if hasta:   qs = qs.filter(fecha__lte=hasta)
    if origen:  qs = qs.filter(origen=origen)
    if estado:  qs = qs.filter(estado=estado)
    if tipo:    qs = qs.filter(tipo_asiento_id=tipo)

    data = []
    for a in qs.order_by('fecha', 'id').select_related('tipo_asiento', 'serie', 'ejercicio'):
        lineas = a.lineas.all()
        td = sum(l.debe  for l in lineas)
        th = sum(l.haber for l in lineas)
        data.append({
            'id': a.id, 'fecha': a.fecha, 'descripcion': a.descripcion,
            'origen': a.origen, 'estado': a.estado, 'numero': a.numero,
            'serie': a.serie_id, 'tipo_asiento': a.tipo_asiento_id,
            'ejercicio': a.ejercicio_id,
            'total_debe':  float(td), 'total_haber': float(th),
        })
    return Response(data)


@api_view(['GET'])
@permission_classes([ContabAuth])
def ObtenerAsiento(request, asiento_id):
    try:
        a = ContabAsiento.objects.get(id=asiento_id)
    except ContabAsiento.DoesNotExist:
        return Response({'error': 'No encontrado'}, status=404)
    lineas = [
        {'id': l.id, 'cuenta': l.cuenta_id, 'nombre': l.cuenta.nombre,
         'debe': float(l.debe), 'haber': float(l.haber), 'descripcion': l.descripcion}
        for l in a.lineas.all()
    ]
    return Response({
        'id': a.id, 'fecha': a.fecha, 'descripcion': a.descripcion,
        'origen': a.origen, 'estado': a.estado, 'anulado': a.anulado,
        'numero': a.numero, 'serie': a.serie_id,
        'tipo_asiento': a.tipo_asiento_id, 'ejercicio': a.ejercicio_id,
        'lineas': lineas,
    })


@api_view(['POST'])
@permission_classes([ContabAuth])
def CrearAsientoManual(request):
    d      = request.data
    lineas = d.get('lineas', [])
    if len(lineas) < 2:
        return Response({'ok': False, 'error': 'Se requieren al menos 2 líneas'},
                        status=400)

    td = sum(Decimal(str(l.get('debe',  0))) for l in lineas)
    th = sum(Decimal(str(l.get('haber', 0))) for l in lineas)
    if abs(td - th) > TOL_MANUAL:
        return Response({'ok': False, 'error': f'No cuadra: D={td} H={th}'},
                        status=400)

    usuario = get_usuario_actual(request)

    with transaction.atomic():
        a = _crear_asiento(
            fecha       = d.get('fecha', timezone.now().date()),
            descripcion = d.get('descripcion', 'Asiento manual'),
            origen      = 'AJU',
            usuario     = usuario,
            tipo_pk     = d.get('tipo_asiento', '001'),
            serie_pk    = d.get('serie', 'DIA'),
            estado      = d.get('estado', 'B'),
        )
        for l in lineas:
            _linea(a, l['cuenta'],
                   debe=Decimal(str(l.get('debe', 0))),
                   haber=Decimal(str(l.get('haber', 0))),
                   desc=l.get('descripcion', ''))

    return Response({'ok': True, 'id': a.id})


@api_view(['POST'])
@permission_classes([ContabAuth])
def AnularAsientoManual(request):
    asiento_id = request.data.get('asiento_id')
    try:
        a = ContabAsiento.objects.get(id=asiento_id, origen='AJU')
    except ContabAsiento.DoesNotExist:
        return Response({'ok': False, 'error': 'Asiento no encontrado o no es manual'},
                        status=404)
    inv = _anular_asiento('AJU', a.id, usuario=get_usuario_actual(request))
    return Response({'ok': True, 'id_contraasiento': inv.id if inv else None})


# ═════════════════════════════════════════════════════════════════════════════
# Informes  (sin cambios funcionales en Sprint A; sólo @permission_classes)
# ═════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([ContabAuth])
def InformeLibroDiario(request):
    desde = request.query_params.get('desde')
    hasta = request.query_params.get('hasta')
    qs = ContabAsiento.objects.filter(anulado=False).order_by('fecha', 'id')
    if desde: qs = qs.filter(fecha__gte=desde)
    if hasta: qs = qs.filter(fecha__lte=hasta)

    result = []
    td_total = D
    th_total = D
    for a in qs.prefetch_related('lineas__cuenta'):
        lineas = []
        for l in a.lineas.all():
            lineas.append({
                'cuenta': l.cuenta_id, 'nombre': l.cuenta.nombre,
                'debe': float(l.debe), 'haber': float(l.haber),
                'descripcion': l.descripcion,
            })
            td_total += l.debe
            th_total += l.haber
        result.append({
            'id': a.id, 'fecha': a.fecha, 'descripcion': a.descripcion,
            'origen': a.origen, 'estado': a.estado, 'lineas': lineas,
        })
    return Response({
        'asientos': result,
        'total_debe': float(td_total), 'total_haber': float(th_total),
        'cuadra': abs(td_total - th_total) < TOL_AUTOMATICO,
    })


@api_view(['GET'])
@permission_classes([ContabAuth])
def InformeMayorCuenta(request):
    codigo = request.query_params.get('cuenta')
    desde  = request.query_params.get('desde')
    hasta  = request.query_params.get('hasta')
    if not codigo:
        return Response({'error': 'Parámetro cuenta requerido'}, status=400)
    try:
        cuenta = ContabPlanCuentas.objects.get(codigo=codigo)
    except ContabPlanCuentas.DoesNotExist:
        return Response({'error': 'Cuenta no encontrada'}, status=404)

    qs = ContabAsientoDet.objects.filter(
        cuenta_id=codigo, asiento__anulado=False
    ).select_related('asiento')
    if desde: qs = qs.filter(asiento__fecha__gte=desde)
    if hasta: qs = qs.filter(asiento__fecha__lte=hasta)
    qs = qs.order_by('asiento__fecha', 'asiento__id')

    saldo_acum = D
    movimientos = []
    for l in qs:
        saldo_acum += (l.debe - l.haber) if cuenta.saldo_tipo == 'D' else (l.haber - l.debe)
        movimientos.append({
            'fecha': l.asiento.fecha, 'asiento_id': l.asiento.id,
            'descripcion': l.asiento.descripcion, 'origen': l.asiento.origen,
            'debe': float(l.debe), 'haber': float(l.haber),
            'saldo': float(saldo_acum), 'detalle_linea': l.descripcion,
        })

    return Response({
        'cuenta': codigo, 'nombre': cuenta.nombre,
        'tipo': cuenta.tipo, 'saldo_tipo': cuenta.saldo_tipo,
        'saldo_final': float(saldo_acum), 'movimientos': movimientos,
    })


@api_view(['GET'])
@permission_classes([ContabAuth])
def InformeBalanceSumasYSaldos(request):
    desde = request.query_params.get('desde')
    hasta = request.query_params.get('hasta')
    qs = ContabAsientoDet.objects.filter(asiento__anulado=False)
    if desde: qs = qs.filter(asiento__fecha__gte=desde)
    if hasta: qs = qs.filter(asiento__fecha__lte=hasta)

    agg = qs.values('cuenta_id').annotate(
        suma_debe=Sum('debe'), suma_haber=Sum('haber')
    ).order_by('cuenta_id')

    cuentas_map = {c.codigo: c for c in ContabPlanCuentas.objects.filter(es_imputable=True)}
    filas = []
    gd = gh = gsd = gsc = D
    for row in agg:
        cod = row['cuenta_id']
        if cod not in cuentas_map:
            continue
        c  = cuentas_map[cod]
        sd = Decimal(str(row['suma_debe']  or 0))
        sh = Decimal(str(row['suma_haber'] or 0))
        saldo = sd - sh
        filas.append({
            'codigo': cod, 'nombre': c.nombre, 'tipo': c.tipo,
            'suma_debe': float(sd), 'suma_haber': float(sh),
            'saldo_deudor': float(max(saldo, D)),
            'saldo_acreedor': float(max(-saldo, D)),
        })
        gd += sd; gh += sh
        gsd += max(saldo, D); gsc += max(-saldo, D)

    return Response({
        'filas': filas,
        'totales': {'suma_debe': float(gd), 'suma_haber': float(gh),
                    'saldo_deudor': float(gsd), 'saldo_acreedor': float(gsc)},
        'cuadra': abs(gd - gh) < TOL_AUTOMATICO,
    })


@api_view(['GET'])
@permission_classes([ContabAuth])
def InformeEstadoResultados(request):
    desde = request.query_params.get('desde')
    hasta = request.query_params.get('hasta')
    qs = ContabAsientoDet.objects.filter(asiento__anulado=False)
    if desde: qs = qs.filter(asiento__fecha__gte=desde)
    if hasta: qs = qs.filter(asiento__fecha__lte=hasta)

    agg = qs.values('cuenta_id').annotate(
        suma_debe=Sum('debe'), suma_haber=Sum('haber')
    ).order_by('cuenta_id')

    cuentas_map = {
        c.codigo: c for c in
        ContabPlanCuentas.objects.filter(tipo__in=['I', 'E'], es_imputable=True)
                                 .select_related('padre')
    }
    ingresos_det = {}; egresos_det = {}
    ti = te = D

    for row in agg:
        cod = row['cuenta_id']
        if cod not in cuentas_map:
            continue
        c  = cuentas_map[cod]
        sd = Decimal(str(row['suma_debe']  or 0))
        sh = Decimal(str(row['suma_haber'] or 0))
        grupo = cod[:5]
        if c.tipo == 'I':
            saldo = sh - sd; ti += saldo
            ingresos_det.setdefault(grupo, {'nombre': c.padre.nombre if c.padre else grupo, 'cuentas': []})
            ingresos_det[grupo]['cuentas'].append({'codigo': cod, 'nombre': c.nombre, 'importe': float(saldo)})
        else:
            saldo = sd - sh; te += saldo
            egresos_det.setdefault(grupo, {'nombre': c.padre.nombre if c.padre else grupo, 'cuentas': []})
            egresos_det[grupo]['cuentas'].append({'codigo': cod, 'nombre': c.nombre, 'importe': float(saldo)})

    return Response({
        'ingresos': {'grupos': list(ingresos_det.values()), 'total': float(ti)},
        'egresos':  {'grupos': list(egresos_det.values()),  'total': float(te)},
        'resultado': float(ti - te),
    })


@api_view(['GET'])
@permission_classes([ContabAuth])
def InformeBalanceGeneral(request):
    hasta = request.query_params.get('hasta')
    qs = ContabAsientoDet.objects.filter(asiento__anulado=False)
    if hasta: qs = qs.filter(asiento__fecha__lte=hasta)

    agg = qs.values('cuenta_id').annotate(
        suma_debe=Sum('debe'), suma_haber=Sum('haber')
    )
    cuentas_map = {
        c.codigo: c for c in
        ContabPlanCuentas.objects.filter(tipo__in=['A', 'P', 'PN', 'I', 'E'], es_imputable=True)
                                 .select_related('padre')
    }
    secciones = {'A': {}, 'P': {}, 'PN': {}}
    totales = {'A': D, 'P': D, 'PN': D}
    resultado_periodo = D

    for row in agg:
        cod = row['cuenta_id']
        if cod not in cuentas_map:
            continue
        c  = cuentas_map[cod]
        sd = Decimal(str(row['suma_debe']  or 0))
        sh = Decimal(str(row['suma_haber'] or 0))
        if c.tipo == 'I':
            resultado_periodo += (sh - sd); continue
        if c.tipo == 'E':
            resultado_periodo -= (sd - sh); continue
        saldo = (sd - sh) if c.saldo_tipo == 'D' else (sh - sd)
        t = c.tipo; grupo = cod[:6]
        secciones[t].setdefault(grupo, {'nombre': c.padre.nombre if c.padre else grupo, 'cuentas': []})
        secciones[t][grupo]['cuentas'].append({'codigo': cod, 'nombre': c.nombre, 'saldo': float(saldo)})
        totales[t] += saldo

    totales['PN'] += resultado_periodo
    total_pasivo_pn = totales['P'] + totales['PN']

    return Response({
        'activo':          {'grupos': list(secciones['A'].values()),  'total': float(totales['A'])},
        'pasivo':          {'grupos': list(secciones['P'].values()),  'total': float(totales['P'])},
        'patrimonio_neto': {
            'grupos': list(secciones['PN'].values()),
            'resultado_periodo': float(resultado_periodo),
            'total': float(totales['PN']),
        },
        'total_pasivo_pn': float(total_pasivo_pn),
        'cuadra': abs(totales['A'] - total_pasivo_pn) < TOL_AUTOMATICO,
    })