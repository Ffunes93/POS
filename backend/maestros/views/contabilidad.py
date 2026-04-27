"""
contabilidad.py
Vistas del módulo de contabilidad.
─ Asientos automáticos desde ventas, compras y recibos
─ Asientos manuales de ajuste
─ 5 informes: Libro Diario, Mayor, Sumas/Saldos, P&L, Balance General
"""
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import (
    Ventas,             # ventas
    Compras,            # compras
    Recibos,            # recibos de cobro
    ContabPlanCuentas,
    ContabAsiento,
    ContabAsientoDet,
)

# ─────────────────────────────────────────────────────────────────────────────
# Cuentas utilizadas para asientos automáticos.
# Modificar los códigos aquí si el plan de cuentas fue personalizado.
# ─────────────────────────────────────────────────────────────────────────────
CA = {
    'caja':         '1.1.01.001',   # Caja
    'banco':        '1.1.01.002',   # Banco - Cta. Corriente
    'deudores':     '1.1.03.001',   # Deudores por Ventas
    'iva_cf':       '1.1.04.001',   # IVA Crédito Fiscal
    'mercerias':    '1.1.05.001',   # Mercaderías
    'proveedores':  '2.1.01.001',   # Proveedores
    'iva_df':       '2.1.02.001',   # IVA Débito Fiscal
    'ventas_21':    '4.1.01.001',   # Ventas Gravadas 21 %
    'ventas_105':   '4.1.01.002',   # Ventas Gravadas 10.5 %
    'ventas_ex':    '4.1.01.003',   # Ventas Exentas
}

D = Decimal('0.00')


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _linea(asiento, codigo_cuenta, debe=D, haber=D, desc=''):
    ContabAsientoDet.objects.create(
        asiento=asiento,
        cuenta_id=codigo_cuenta,
        debe=debe,
        haber=haber,
        descripcion=desc,
    )


def _ya_tiene_asiento(origen, movim_id):
    return ContabAsiento.objects.filter(
        origen=origen, origen_movim=movim_id, anulado=False
    ).exists()


def _generar_asiento_venta(venta):
    """
    Genera asiento contable a partir de un comprobante de venta.
    Soporta comprobantes tipo FA/FB/EA/EB.
    Venta contado → DB Caja / CR Ventas + IVA Débito
    Venta cta cte → DB Deudores / CR Ventas + IVA Débito
    """
    if _ya_tiene_asiento('VTA', venta.movim):
        return None

    neto      = Decimal(str(venta.neto    or 0))
    iva       = Decimal(str(venta.iva_1   or 0))
    iva2      = Decimal('0.00')  # iva_2 no existe en Ventas
    total     = Decimal(str(venta.tot_general or 0))

    if total <= 0:
        return None

    # Detectar alícuota dominante (simple: si iva2 > 0 usamos dos cuentas de ventas)
    # Por defecto asignamos todo a 21%
    cond = str(getattr(venta, 'cond_venta', '') or '')
    cuenta_activo = CA['deudores'] if cond == '2' else CA['caja']

    tipo_comprob = str(getattr(venta, 'cod_comprob', '') or '')
    desc_venta = (
        f"Venta {tipo_comprob} N° {venta.nro_comprob} "
        f"- {getattr(venta, 'nom_cli', '') or venta.cod_cli}"
    )

    with transaction.atomic():
        asiento = ContabAsiento.objects.create(
            fecha        = venta.fecha_fact,
            descripcion  = desc_venta,
            origen       = 'VTA',
            origen_movim = venta.movim,
            usuario      = getattr(venta, 'usuario', '') or '',
        )
        # Débito: Caja o Deudores
        _linea(asiento, cuenta_activo, debe=total, desc='Cobro por ventas')

        # Crédito: Ventas (neto)
        _linea(asiento, CA['ventas_21'], haber=neto, desc='Ventas del período')

        # Crédito: IVA Débito
        iva_total = iva + iva2
        if iva_total > 0:
            _linea(asiento, CA['iva_df'], haber=iva_total, desc='IVA débito fiscal')

        # Ajuste centavos para cuadrar
        suma_haber = neto + iva_total
        if suma_haber != total:
            diff = total - suma_haber
            if diff > 0:
                _linea(asiento, CA['ventas_21'], haber=diff, desc='Diferencia redondeo')
            else:
                _linea(asiento, CA['ventas_21'], debe=abs(diff), desc='Diferencia redondeo')

    return asiento


def _generar_asiento_compra(compra):
    """
    Genera asiento contable a partir de una factura de compra.
    Compra contado (SAC) → DB Mercaderías + IVA CF / CR Caja
    Compra cta cte       → DB Mercaderías + IVA CF / CR Proveedores
    """
    if _ya_tiene_asiento('CMP', compra.movim):
        return None

    neto  = Decimal(str(compra.neto   or 0))
    iva   = Decimal(str(compra.iva_1  or 0))
    iva2  = Decimal('0.00')  # iva_2 no existe en Compras
    total = Decimal(str(compra.tot_general or 0))

    if total <= 0:
        return None

    origen_pago = str(getattr(compra, 'origen', '') or '')
    cuenta_pasivo = CA['caja'] if origen_pago == 'SAC' else CA['proveedores']

    desc = (
        f"Compra {getattr(compra, 'cod_comprob', '')} N° {compra.nro_comprob} "
        f"- {getattr(compra, 'nom_prov', '') or compra.cod_prov}"
    )

    with transaction.atomic():
        asiento = ContabAsiento.objects.create(
            fecha        = compra.fecha_comprob,
            descripcion  = desc,
            origen       = 'CMP',
            origen_movim = compra.movim,
            usuario      = getattr(compra, 'usuario', '') or '',
        )
        # Débito: Mercaderías
        _linea(asiento, CA['mercerias'], debe=neto, desc='Compra de mercaderías')

        # Débito: IVA Crédito Fiscal
        iva_total = iva + iva2
        if iva_total > 0:
            _linea(asiento, CA['iva_cf'], debe=iva_total, desc='IVA crédito fiscal')

        # Crédito: Proveedores o Caja
        _linea(asiento, cuenta_pasivo, haber=total, desc='Obligación de compra')

        # Ajuste centavos
        suma_debe = neto + iva_total
        if suma_debe != total:
            diff = total - suma_debe
            if diff > 0:
                _linea(asiento, CA['mercerias'], debe=diff, desc='Diferencia redondeo')
            else:
                _linea(asiento, CA['mercerias'], haber=abs(diff), desc='Diferencia redondeo')

    return asiento


def _generar_asiento_recibo(recibo):
    """
    Genera asiento para un recibo de cobro de cuenta corriente.
    DB Caja / CR Deudores
    """
    if _ya_tiene_asiento('REC', recibo.numero):
        return None

    importe = Decimal(str(recibo.importe or 0))
    if importe <= 0:
        return None

    cod_cli = getattr(recibo, 'cliente', '')

    with transaction.atomic():
        asiento = ContabAsiento.objects.create(
            fecha        = recibo.fecha,
            descripcion  = f"Recibo N° {recibo.numero} - Cliente {cod_cli}",
            origen       = 'REC',
            origen_movim = recibo.numero,
            usuario      = getattr(recibo, 'usuario', '') or '',
        )
        _linea(asiento, CA['caja'],     debe=importe,   desc='Cobro de cta. cte.')
        _linea(asiento, CA['deudores'], haber=importe,  desc='Cancelación deuda cliente')

    return asiento


def _anular_asiento(origen, origen_movim, usuario='sistema'):
    """
    Genera asiento inverso (contraasiento) cuando se anula una operación.
    """
    original = ContabAsiento.objects.filter(
        origen=origen, origen_movim=origen_movim, anulado=False
    ).first()
    if not original:
        return None

    original.anulado = True
    original.save(update_fields=['anulado'])

    with transaction.atomic():
        inv = ContabAsiento.objects.create(
            fecha        = timezone.now().date(),
            descripcion  = f"ANULACIÓN de Asiento #{original.id} - {original.descripcion}",
            origen       = 'ANU',
            origen_movim = original.id,
            usuario      = usuario,
        )
        for linea in original.lineas.all():
            ContabAsientoDet.objects.create(
                asiento=inv,
                cuenta=linea.cuenta,
                debe=linea.haber,      # invertido
                haber=linea.debe,      # invertido
                descripcion=f"Anulación: {linea.descripcion}",
            )
    return inv


# ─────────────────────────────────────────────────────────────────────────────
# API – Sincronización histórica
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def SincronizarAsientos(request):
    """
    Genera asientos para todas las ventas, compras y recibos que
    todavía no tienen asiento contable. Seguro llamarlo múltiples veces.
    """
    generados = {'ventas': 0, 'compras': 0, 'recibos': 0, 'errores': []}

    # Ventas sin asiento
    ids_con_asiento_vta = set(
        ContabAsiento.objects.filter(origen='VTA')
        .values_list('origen_movim', flat=True)
    )
    ventas = Ventas.objects.filter(anulado__isnull=True).exclude(movim__in=ids_con_asiento_vta)
    for v in ventas:
        try:
            if _generar_asiento_venta(v):
                generados['ventas'] += 1
        except Exception as e:
            generados['errores'].append(f"VTA movim={v.movim}: {e}")

    # Compras sin asiento
    ids_con_asiento_cmp = set(
        ContabAsiento.objects.filter(origen='CMP')
        .values_list('origen_movim', flat=True)
    )
    compras = Compras.objects.filter(anulado__isnull=True).exclude(movim__in=ids_con_asiento_cmp)
    for c in compras:
        try:
            if _generar_asiento_compra(c):
                generados['compras'] += 1
        except Exception as e:
            generados['errores'].append(f"CMP movim={c.movim}: {e}")

    # Recibos sin asiento
    ids_con_asiento_rec = set(
        ContabAsiento.objects.filter(origen='REC')
        .values_list('origen_movim', flat=True)
    )
    recibos = Recibos.objects.filter(anulado__isnull=True).exclude(numero__in=ids_con_asiento_rec)
    for r in recibos:
        try:
            if _generar_asiento_recibo(r):
                generados['recibos'] += 1
        except Exception as e:
            generados["errores"].append(f"REC nro={r.numero}: {e}")

    return Response({
        'ok': True,
        'generados': generados,
        'total': generados['ventas'] + generados['compras'] + generados['recibos'],
    })


# ─────────────────────────────────────────────────────────────────────────────
# API – Plan de cuentas
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def ListarPlanCuentas(request):
    solo_imputables = request.query_params.get('imputables') == '1'
    qs = ContabPlanCuentas.objects.filter(activa=True)
    if solo_imputables:
        qs = qs.filter(es_imputable=True)
    data = [
        {
            'codigo':       c.codigo,
            'nombre':       c.nombre,
            'tipo':         c.tipo,
            'nivel':        c.nivel,
            'padre':        c.padre_id,
            'es_imputable': c.es_imputable,
            'saldo_tipo':   c.saldo_tipo,
            'activa':       c.activa,
        }
        for c in qs
    ]
    return Response(data)


@api_view(['POST'])
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
        },
    )
    return Response({'ok': True, 'creado': created, 'codigo': obj.codigo})


# ─────────────────────────────────────────────────────────────────────────────
# API – Asientos CRUD
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def ListarAsientos(request):
    desde = request.query_params.get('desde')
    hasta = request.query_params.get('hasta')
    origen = request.query_params.get('origen', '')

    qs = ContabAsiento.objects.filter(anulado=False)
    if desde:
        qs = qs.filter(fecha__gte=desde)
    if hasta:
        qs = qs.filter(fecha__lte=hasta)
    if origen:
        qs = qs.filter(origen=origen)

    data = []
    for a in qs.order_by('fecha', 'id'):
        lineas = a.lineas.all()
        total_debe  = sum(l.debe  for l in lineas)
        total_haber = sum(l.haber for l in lineas)
        data.append({
            'id':          a.id,
            'fecha':       a.fecha,
            'descripcion': a.descripcion,
            'origen':      a.origen,
            'total_debe':  float(total_debe),
            'total_haber': float(total_haber),
        })
    return Response(data)


@api_view(['GET'])
def ObtenerAsiento(request, asiento_id):
    try:
        a = ContabAsiento.objects.get(id=asiento_id)
    except ContabAsiento.DoesNotExist:
        return Response({'error': 'No encontrado'}, status=404)
    lineas = [
        {
            'id':          l.id,
            'cuenta':      l.cuenta_id,
            'nombre':      l.cuenta.nombre,
            'debe':        float(l.debe),
            'haber':       float(l.haber),
            'descripcion': l.descripcion,
        }
        for l in a.lineas.all()
    ]
    return Response({
        'id':          a.id,
        'fecha':       a.fecha,
        'descripcion': a.descripcion,
        'origen':      a.origen,
        'anulado':     a.anulado,
        'lineas':      lineas,
    })


@api_view(['POST'])
def CrearAsientoManual(request):
    """Crea un asiento de ajuste manual."""
    d = request.data
    lineas = d.get('lineas', [])

    if len(lineas) < 2:
        return Response({'ok': False, 'error': 'Se requieren al menos 2 líneas'}, status=400)

    total_debe  = sum(Decimal(str(l.get('debe',  0))) for l in lineas)
    total_haber = sum(Decimal(str(l.get('haber', 0))) for l in lineas)

    if abs(total_debe - total_haber) > Decimal('0.01'):
        return Response({
            'ok': False,
            'error': f'El asiento no cuadra: Debe={total_debe} Haber={total_haber}'
        }, status=400)

    with transaction.atomic():
        asiento = ContabAsiento.objects.create(
            fecha       = d.get('fecha', timezone.now().date()),
            descripcion = d.get('descripcion', 'Asiento manual'),
            origen      = 'AJU',
            usuario     = d.get('usuario', ''),
        )
        for l in lineas:
            _linea(
                asiento,
                l['cuenta'],
                debe=Decimal(str(l.get('debe', 0))),
                haber=Decimal(str(l.get('haber', 0))),
                desc=l.get('descripcion', ''),
            )

    return Response({'ok': True, 'id': asiento.id})


@api_view(['POST'])
def AnularAsientoManual(request):
    asiento_id = request.data.get('asiento_id')
    try:
        a = ContabAsiento.objects.get(id=asiento_id, origen='AJU')
    except ContabAsiento.DoesNotExist:
        return Response({'ok': False, 'error': 'Asiento no encontrado o no es manual'}, status=404)

    inv = _anular_asiento('AJU', a.id, usuario=request.data.get('usuario', ''))
    return Response({'ok': True, 'id_contraasiento': inv.id if inv else None})


# ─────────────────────────────────────────────────────────────────────────────
# INFORMES
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def InformeLibroDiario(request):
    """
    Libro Diario: todos los asientos en el período, con sus líneas.
    ?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
    """
    desde = request.query_params.get('desde')
    hasta = request.query_params.get('hasta')

    qs = ContabAsiento.objects.filter(anulado=False).order_by('fecha', 'id')
    if desde:
        qs = qs.filter(fecha__gte=desde)
    if hasta:
        qs = qs.filter(fecha__lte=hasta)

    result = []
    total_debe = D
    total_haber = D

    for a in qs.prefetch_related('lineas__cuenta'):
        lineas = []
        for l in a.lineas.all():
            lineas.append({
                'cuenta':      l.cuenta_id,
                'nombre':      l.cuenta.nombre,
                'debe':        float(l.debe),
                'haber':       float(l.haber),
                'descripcion': l.descripcion,
            })
            total_debe  += l.debe
            total_haber += l.haber

        result.append({
            'id':          a.id,
            'fecha':       a.fecha,
            'descripcion': a.descripcion,
            'origen':      a.origen,
            'lineas':      lineas,
        })

    return Response({
        'asientos':    result,
        'total_debe':  float(total_debe),
        'total_haber': float(total_haber),
        'cuadra':      abs(total_debe - total_haber) < Decimal('0.02'),
    })


@api_view(['GET'])
def InformeMayorCuenta(request):
    """
    Mayor de Cuentas para una cuenta específica.
    ?cuenta=1.1.01.001&desde=...&hasta=...
    """
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

    if desde:
        qs = qs.filter(asiento__fecha__gte=desde)
    if hasta:
        qs = qs.filter(asiento__fecha__lte=hasta)

    qs = qs.order_by('asiento__fecha', 'asiento__id')

    saldo_acumulado = D
    movimientos = []
    for l in qs:
        if cuenta.saldo_tipo == 'D':
            saldo_acumulado += l.debe - l.haber
        else:
            saldo_acumulado += l.haber - l.debe

        movimientos.append({
            'fecha':         l.asiento.fecha,
            'asiento_id':    l.asiento.id,
            'descripcion':   l.asiento.descripcion,
            'origen':        l.asiento.origen,
            'debe':          float(l.debe),
            'haber':         float(l.haber),
            'saldo':         float(saldo_acumulado),
            'detalle_linea': l.descripcion,
        })

    return Response({
        'cuenta':       codigo,
        'nombre':       cuenta.nombre,
        'tipo':         cuenta.tipo,
        'saldo_tipo':   cuenta.saldo_tipo,
        'saldo_final':  float(saldo_acumulado),
        'movimientos':  movimientos,
    })


@api_view(['GET'])
def InformeBalanceSumasYSaldos(request):
    """
    Balance de Sumas y Saldos para el período.
    Verifica que ΣDebe == ΣHaber y ΣSaldo_D == ΣSaldo_C
    """
    desde = request.query_params.get('desde')
    hasta = request.query_params.get('hasta')

    qs = ContabAsientoDet.objects.filter(asiento__anulado=False)
    if desde:
        qs = qs.filter(asiento__fecha__gte=desde)
    if hasta:
        qs = qs.filter(asiento__fecha__lte=hasta)

    # Agregar por cuenta
    agg = (
        qs.values('cuenta_id')
        .annotate(
            suma_debe=Sum('debe'),
            suma_haber=Sum('haber'),
        )
        .order_by('cuenta_id')
    )

    cuentas_map = {
        c.codigo: c
        for c in ContabPlanCuentas.objects.filter(es_imputable=True)
    }

    filas = []
    gran_debe = D
    gran_haber = D
    gran_saldo_d = D
    gran_saldo_c = D

    for row in agg:
        cod = row['cuenta_id']
        if cod not in cuentas_map:
            continue
        cuenta = cuentas_map[cod]
        sd = Decimal(str(row['suma_debe']  or 0))
        sh = Decimal(str(row['suma_haber'] or 0))
        saldo = sd - sh
        saldo_d = max(saldo,   D)
        saldo_c = max(-saldo, D)

        gran_debe   += sd
        gran_haber  += sh
        gran_saldo_d += saldo_d
        gran_saldo_c += saldo_c

        filas.append({
            'codigo':       cod,
            'nombre':       cuenta.nombre,
            'tipo':         cuenta.tipo,
            'suma_debe':    float(sd),
            'suma_haber':   float(sh),
            'saldo_deudor': float(saldo_d),
            'saldo_acreedor': float(saldo_c),
        })

    return Response({
        'filas':        filas,
        'totales': {
            'suma_debe':      float(gran_debe),
            'suma_haber':     float(gran_haber),
            'saldo_deudor':   float(gran_saldo_d),
            'saldo_acreedor': float(gran_saldo_c),
        },
        'cuadra': abs(gran_debe - gran_haber) < Decimal('0.02'),
    })


@api_view(['GET'])
def InformeEstadoResultados(request):
    """
    Estado de Resultados (P&L).
    Ingresos (tipo='I') – Egresos (tipo='E') = Resultado del período
    """
    desde = request.query_params.get('desde')
    hasta = request.query_params.get('hasta')

    qs = ContabAsientoDet.objects.filter(asiento__anulado=False)
    if desde:
        qs = qs.filter(asiento__fecha__gte=desde)
    if hasta:
        qs = qs.filter(asiento__fecha__lte=hasta)

    agg = (
        qs.values('cuenta_id')
        .annotate(suma_debe=Sum('debe'), suma_haber=Sum('haber'))
        .order_by('cuenta_id')
    )

    cuentas_map = {
        c.codigo: c
        for c in ContabPlanCuentas.objects.filter(tipo__in=['I', 'E'], es_imputable=True)
    }

    ingresos_det = {}   # {grupo: {'nombre':..., 'cuentas': []}}
    egresos_det  = {}

    total_ingresos = D
    total_egresos  = D

    for row in agg:
        cod = row['cuenta_id']
        if cod not in cuentas_map:
            continue
        cuenta = cuentas_map[cod]
        sd  = Decimal(str(row['suma_debe']  or 0))
        sh  = Decimal(str(row['suma_haber'] or 0))
        # Ingresos (acreedoras): saldo = haber - debe
        # Egresos (deudoras):    saldo = debe - haber
        if cuenta.tipo == 'I':
            saldo = sh - sd
            total_ingresos += saldo
            grupo = cod[:5]  # nivel 3 (ej: "4.1.01")
            if grupo not in ingresos_det:
                ingresos_det[grupo] = {'nombre': cuenta.padre.nombre if cuenta.padre else grupo, 'cuentas': []}
            ingresos_det[grupo]['cuentas'].append({
                'codigo': cod, 'nombre': cuenta.nombre, 'importe': float(saldo)
            })
        else:
            saldo = sd - sh
            total_egresos += saldo
            grupo = cod[:5]
            if grupo not in egresos_det:
                egresos_det[grupo] = {'nombre': cuenta.padre.nombre if cuenta.padre else grupo, 'cuentas': []}
            egresos_det[grupo]['cuentas'].append({
                'codigo': cod, 'nombre': cuenta.nombre, 'importe': float(saldo)
            })

    resultado = total_ingresos - total_egresos

    return Response({
        'ingresos': {
            'grupos':   list(ingresos_det.values()),
            'total':    float(total_ingresos),
        },
        'egresos': {
            'grupos':   list(egresos_det.values()),
            'total':    float(total_egresos),
        },
        'resultado': float(resultado),
    })


@api_view(['GET'])
def InformeBalanceGeneral(request):
    """
    Balance General (Estado de Situación Patrimonial).
    Activo = Pasivo + Patrimonio Neto (+ Resultado del período)
    """
    hasta = request.query_params.get('hasta')

    qs = ContabAsientoDet.objects.filter(asiento__anulado=False)
    if hasta:
        qs = qs.filter(asiento__fecha__lte=hasta)

    agg = (
        qs.values('cuenta_id')
        .annotate(suma_debe=Sum('debe'), suma_haber=Sum('haber'))
    )

    cuentas_map = {
        c.codigo: c
        for c in ContabPlanCuentas.objects.filter(
            tipo__in=['A', 'P', 'PN', 'I', 'E'], es_imputable=True
        )
    }

    secciones = {'A': {}, 'P': {}, 'PN': {}}
    totales   = {'A': D, 'P': D, 'PN': D}
    resultado_periodo = D

    for row in agg:
        cod = row['cuenta_id']
        if cod not in cuentas_map:
            continue
        cuenta = cuentas_map[cod]
        sd  = Decimal(str(row['suma_debe']  or 0))
        sh  = Decimal(str(row['suma_haber'] or 0))

        if cuenta.tipo == 'I':
            resultado_periodo += (sh - sd)
            continue
        if cuenta.tipo == 'E':
            resultado_periodo -= (sd - sh)
            continue

        # Saldo según naturaleza
        if cuenta.saldo_tipo == 'D':
            saldo = sd - sh   # Activo
        else:
            saldo = sh - sd   # Pasivo / PN

        tipo = cuenta.tipo
        grupo = cod[:6]  # nivel 3

        if grupo not in secciones[tipo]:
            padre_nombre = cuenta.padre.nombre if cuenta.padre else grupo
            secciones[tipo][grupo] = {'nombre': padre_nombre, 'cuentas': []}

        secciones[tipo][grupo]['cuentas'].append({
            'codigo': cod, 'nombre': cuenta.nombre, 'saldo': float(saldo)
        })
        totales[tipo] += saldo

    # El resultado del período se suma al PN
    totales['PN'] += resultado_periodo
    total_pasivo_pn = totales['P'] + totales['PN']

    return Response({
        'activo': {
            'grupos': list(secciones['A'].values()),
            'total':  float(totales['A']),
        },
        'pasivo': {
            'grupos': list(secciones['P'].values()),
            'total':  float(totales['P']),
        },
        'patrimonio_neto': {
            'grupos':             list(secciones['PN'].values()),
            'resultado_periodo':  float(resultado_periodo),
            'total':              float(totales['PN']),
        },
        'total_pasivo_pn': float(total_pasivo_pn),
        'cuadra': abs(totales['A'] - total_pasivo_pn) < Decimal('0.02'),
    })
