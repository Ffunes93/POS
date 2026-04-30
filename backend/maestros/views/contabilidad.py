"""
contabilidad.py  (versión extendida)
Vistas del módulo de contabilidad.

Nuevos endpoints vs versión anterior:
  /api/contab/Ejercicios/             GET/POST
  /api/contab/Ejercicios/<id>/        PUT/DELETE
  /api/contab/TiposAsiento/           GET/POST
  /api/contab/TiposAsiento/<pk>/      PUT
  /api/contab/Series/                 GET/POST
  /api/contab/Series/<pk>/            PUT
  /api/contab/Modelos/                GET/POST
  /api/contab/Modelos/<pk>/           GET/PUT/DELETE
  /api/contab/AsientosAutomaticos/    POST (Apertura, Cierre, Ajuste Inflación, etc.)
  /api/contab/ImportarAsientos/       POST (CSV/JSON)
  /api/contab/ConsultaSaldos/         GET
  /api/contab/Asientos/<id>/mayorizar/ POST
  /api/contab/Asientos/<id>/anular/   POST
"""
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework.decorators import api_view
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
)

# ─────────────────────────────────────────────────────────────────────────────
# Mapa de cuentas para asientos automáticos
# ─────────────────────────────────────────────────────────────────────────────
CA = {
    'caja':         '1.1.01.001',
    'banco':        '1.1.01.002',
    'deudores':     '1.1.03.001',
    'iva_cf':       '1.1.04.001',
    'mercerias':    '1.1.05.001',
    'proveedores':  '2.1.01.001',
    'iva_df':       '2.1.02.001',
    'ventas_21':    '4.1.01.001',
    'ventas_105':   '4.1.01.002',
    'ventas_ex':    '4.1.01.003',
    'resultado':    '3.3.01.001',    # Resultados No Asignados
}

D = Decimal('0.00')


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _linea(asiento, codigo_cuenta, debe=D, haber=D, desc=''):
    ContabAsientoDet.objects.create(
        asiento=asiento, cuenta_id=codigo_cuenta,
        debe=debe, haber=haber, descripcion=desc,
    )


def _ya_tiene_asiento(origen, movim_id):
    return ContabAsiento.objects.filter(
        origen=origen, origen_movim=movim_id, anulado=False
    ).exists()


def _get_tipo_real():
    """Devuelve el TipoAsiento 'Real' (001) si existe, sino None."""
    try:
        return ContabTipoAsiento.objects.get(pk='001')
    except ContabTipoAsiento.DoesNotExist:
        return None


def _get_ejercicio_activo():
    """Devuelve el ejercicio abierto más reciente."""
    return ContabEjercicio.objects.filter(estado='A').order_by('-anio_inicio').first()


def _get_serie(codigo='DIA'):
    try:
        return ContabSerieAsiento.objects.get(pk=codigo)
    except ContabSerieAsiento.DoesNotExist:
        return None


def _siguiente_nro_serie(serie):
    """Incrementa y retorna el siguiente número de una serie (con lock)."""
    if not serie:
        return None
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT ultimo_nro FROM contab_serie_asiento WHERE codigo = %s FOR UPDATE",
            [serie.codigo]
        )
        actual = cursor.fetchone()[0]
        nuevo  = actual + 1
        cursor.execute(
            "UPDATE contab_serie_asiento SET ultimo_nro = %s WHERE codigo = %s",
            [nuevo, serie.codigo]
        )
    return nuevo


def _crear_asiento(fecha, descripcion, origen, origen_movim=None,
                   usuario='', tipo_pk='001', serie_pk='DIA', estado='M'):
    ejercicio    = _get_ejercicio_activo()
    tipo_asiento = ContabTipoAsiento.objects.filter(pk=tipo_pk).first()
    serie        = _get_serie(serie_pk)
    numero       = _siguiente_nro_serie(serie) if serie else None

    return ContabAsiento.objects.create(
        fecha        = fecha,
        descripcion  = descripcion,
        origen       = origen,
        origen_movim = origen_movim,
        usuario      = usuario,
        ejercicio    = ejercicio,
        tipo_asiento = tipo_asiento,
        serie        = serie,
        numero       = numero,
        estado       = estado,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Generadores de asientos automáticos (ventas, compras, recibos)
# ─────────────────────────────────────────────────────────────────────────────

def _generar_asiento_venta(venta):
    if _ya_tiene_asiento('VTA', venta.movim):
        return None
    neto  = Decimal(str(venta.neto    or 0))
    iva   = Decimal(str(venta.iva_1   or 0))
    total = Decimal(str(venta.tot_general or 0))
    if total <= 0:
        return None
    cond          = str(getattr(venta, 'cond_venta', '') or '')
    cuenta_activo = CA['deudores'] if cond == '2' else CA['caja']
    desc_venta    = f"Venta {getattr(venta,'cod_comprob','')} N° {venta.nro_comprob}"

    with transaction.atomic():
        a = _crear_asiento(venta.fecha_fact, desc_venta, 'VTA', venta.movim,
                           getattr(venta, 'usuario', '') or '')
        _linea(a, cuenta_activo, debe=total, desc='Cobro por ventas')
        _linea(a, CA['ventas_21'], haber=neto, desc='Ventas del período')
        if iva > 0:
            _linea(a, CA['iva_df'], haber=iva, desc='IVA débito fiscal')
        diff = total - (neto + iva)
        if abs(diff) > Decimal('0.001'):
            if diff > 0:
                _linea(a, CA['ventas_21'], haber=diff, desc='Diferencia redondeo')
            else:
                _linea(a, CA['ventas_21'], debe=abs(diff), desc='Diferencia redondeo')
    return a


def _generar_asiento_compra(compra):
    if _ya_tiene_asiento('CMP', compra.movim):
        return None
    neto  = Decimal(str(compra.neto   or 0))
    iva   = Decimal(str(compra.iva_1  or 0))
    total = Decimal(str(compra.tot_general or 0))
    if total <= 0:
        return None
    cuenta_pasivo = CA['caja'] if getattr(compra, 'observac', '') == 'CONTADO' else CA['proveedores']
    desc          = f"Compra {getattr(compra,'cod_comprob','')} N° {compra.nro_comprob}"

    with transaction.atomic():
        a = _crear_asiento(compra.fecha_comprob, desc, 'CMP', compra.movim,
                           getattr(compra, 'usuario', '') or '')
        _linea(a, CA['mercerias'], debe=neto, desc='Compra de mercaderías')
        if iva > 0:
            _linea(a, CA['iva_cf'], debe=iva, desc='IVA crédito fiscal')
        _linea(a, cuenta_pasivo, haber=total, desc='Obligación de compra')
        diff = total - (neto + iva)
        if abs(diff) > Decimal('0.001'):
            if diff > 0:
                _linea(a, CA['mercerias'], debe=diff, desc='Diferencia redondeo')
            else:
                _linea(a, CA['mercerias'], haber=abs(diff), desc='Diferencia redondeo')
    return a


def _generar_asiento_recibo(recibo):
    if _ya_tiene_asiento('REC', recibo.numero):
        return None
    importe = Decimal(str(recibo.importe or 0))
    if importe <= 0:
        return None
    with transaction.atomic():
        a = _crear_asiento(recibo.fecha,
                           f"Recibo N° {recibo.numero} - Cliente {recibo.cliente}",
                           'REC', recibo.numero,
                           getattr(recibo, 'usuario', '') or '')
        _linea(a, CA['caja'],     debe=importe,  desc='Cobro de cta. cte.')
        _linea(a, CA['deudores'], haber=importe, desc='Cancelación deuda cliente')
    return a


def _anular_asiento(origen, origen_movim, usuario='sistema'):
    original = ContabAsiento.objects.filter(
        origen=origen, origen_movim=origen_movim, anulado=False
    ).first()
    if not original:
        return None
    original.anulado = True
    original.estado  = 'A'
    original.save(update_fields=['anulado', 'estado'])

    with transaction.atomic():
        inv = _crear_asiento(
            timezone.now().date(),
            f"ANULACIÓN de Asiento #{original.id} — {original.descripcion}",
            'ANU', original.id, usuario
        )
        inv.asiento_origen = original
        inv.save(update_fields=['asiento_origen'])
        for linea in original.lineas.all():
            ContabAsientoDet.objects.create(
                asiento=inv, cuenta=linea.cuenta,
                debe=linea.haber, haber=linea.debe,
                descripcion=f"Anulación: {linea.descripcion}",
            )
    return inv


# ─────────────────────────────────────────────────────────────────────────────
# API — Configuración: Tipos de Asiento
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def GestionTiposAsiento(request):
    if request.method == 'GET':
        data = list(ContabTipoAsiento.objects.values(
            'codigo', 'descripcion', 'habilitado', 'excluye_eecc'
        ))
        return Response(data)

    # POST — crear
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


# ─────────────────────────────────────────────────────────────────────────────
# API — Configuración: Series de Numeración
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
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


# ─────────────────────────────────────────────────────────────────────────────
# API — Ejercicios Contables
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
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


# ─────────────────────────────────────────────────────────────────────────────
# API — Modelos de Asientos
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
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

    # POST — crear modelo con sus líneas
    d      = request.data
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
        # Reemplazar líneas
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
def DetalleModelo(request, pk):
    try:
        modelo = ContabModeloAsiento.objects.get(pk=pk)
    except ContabModeloAsiento.DoesNotExist:
        return Response({'error': 'No encontrado'}, status=404)

    if request.method == 'DELETE':
        modelo.delete()
        return Response({'ok': True})

    lineas = [
        {
            'id': l.id, 'orden': l.orden, 'cuenta': l.cuenta_id,
            'nombre': l.cuenta.nombre, 'tipo': l.tipo,
            'importe': float(l.importe), 'descripcion': l.descripcion,
        }
        for l in modelo.lineas.all()
    ]
    return Response({
        'codigo': modelo.codigo, 'descripcion': modelo.descripcion,
        'habilitado': modelo.habilitado, 'tipo_asiento': modelo.tipo_asiento_id,
        'lineas': lineas,
    })


# ─────────────────────────────────────────────────────────────────────────────
# API — Asientos Automáticos (Apertura, Cierre, Ajuste Inflación, etc.)
# ─────────────────────────────────────────────────────────────────────────────

TIPOS_AUTO = {
    'apertura':     ('APE', 'Asiento de Apertura'),
    'cierre':       ('CIE', 'Asiento de Cierre'),
    'inflacion':    ('INF', 'Asiento de Ajuste por Inflación'),
    'dif_cambio':   ('DIF', 'Asiento de Diferencia de Cambio'),
    'refundicion':  ('AJU', 'Refundición de Cuentas de Resultado'),
}


@api_view(['POST'])
def GenerarAsientoAutomatico(request):
    """
    Genera un asiento automático de apertura, cierre u otro tipo.

    Payload:
    {
      "tipo":      "apertura" | "cierre" | "inflacion" | "dif_cambio" | "refundicion",
      "fecha":     "YYYY-MM-DD",
      "ejercicio_id": 1,          // opcional
      "usuario":   "admin",
      "lineas": [                 // para tipos personalizados o sobreescribir
        { "cuenta": "1.1.01.001", "debe": 5000, "haber": 0, "descripcion": "..." },
        ...
      ]
    }
    """
    d    = request.data
    tipo = d.get('tipo', '').lower()

    if tipo not in TIPOS_AUTO:
        return Response({
            'error': f'Tipo inválido. Válidos: {list(TIPOS_AUTO.keys())}'
        }, status=400)

    origen_code, desc_default = TIPOS_AUTO[tipo]
    fecha      = d.get('fecha', timezone.now().date().isoformat())
    usuario    = d.get('usuario', 'sistema')
    lineas_in  = d.get('lineas', [])

    # Cierre: genera asiento de cierre refundiendo resultados
    if tipo == 'cierre' and not lineas_in:
        return _asiento_cierre(fecha, usuario)

    # Apertura: genera el asiento de apertura desde saldos actuales
    if tipo == 'apertura' and not lineas_in:
        return _asiento_apertura(fecha, usuario, d.get('ejercicio_id'))

    # Caso genérico: el usuario provee las líneas
    if not lineas_in:
        return Response({'error': 'Se requieren lineas para este tipo de asiento'}, status=400)

    total_debe  = sum(Decimal(str(l.get('debe', 0)))  for l in lineas_in)
    total_haber = sum(Decimal(str(l.get('haber', 0))) for l in lineas_in)
    if abs(total_debe - total_haber) > Decimal('0.02'):
        return Response({
            'error': f'El asiento no cuadra: Debe={total_debe} Haber={total_haber}'
        }, status=400)

    with transaction.atomic():
        a = _crear_asiento(fecha, desc_default, origen_code, usuario=usuario)
        for l in lineas_in:
            _linea(a, l['cuenta'],
                   debe=Decimal(str(l.get('debe', 0))),
                   haber=Decimal(str(l.get('haber', 0))),
                   desc=l.get('descripcion', ''))

    return Response({'ok': True, 'id': a.id, 'descripcion': desc_default})


def _asiento_apertura(fecha, usuario, ejercicio_id=None):
    """
    Genera el asiento de apertura tomando los saldos acumulados del balance
    al cierre del ejercicio anterior.
    """
    # Toma saldos de todas las cuentas de Activo, Pasivo y PN
    qs = (
        ContabAsientoDet.objects
        .filter(asiento__anulado=False,
                cuenta__tipo__in=['A', 'P', 'PN'])
        .values('cuenta_id', 'cuenta__tipo', 'cuenta__saldo_tipo')
        .annotate(suma_debe=Sum('debe'), suma_haber=Sum('haber'))
    )

    if not qs.exists():
        return Response({'error': 'No hay movimientos anteriores para generar apertura'}, status=400)

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
        return Response({'error': 'No hay saldos para aperturar'}, status=400)

    with transaction.atomic():
        a = _crear_asiento(fecha, 'Asiento de Apertura', 'APE', usuario=usuario)
        for l in lineas_ape:
            _linea(a, l['cuenta'], debe=l['debe'], haber=l['haber'], desc='Apertura')

    return Response({'ok': True, 'id': a.id, 'lineas_generadas': len(lineas_ape)})


def _asiento_cierre(fecha, usuario):
    """
    Genera el asiento de cierre: refunde todas las cuentas de resultado (I y E)
    contra la cuenta de Resultados No Asignados.
    """
    qs = (
        ContabAsientoDet.objects
        .filter(asiento__anulado=False, cuenta__tipo__in=['I', 'E'])
        .values('cuenta_id', 'cuenta__tipo', 'cuenta__nombre')
        .annotate(suma_debe=Sum('debe'), suma_haber=Sum('haber'))
    )

    if not qs.exists():
        return Response({'error': 'No hay cuentas de resultado para cerrar'}, status=400)

    resultado_neto = D
    lineas_cie = []

    for row in qs:
        sd = Decimal(str(row['suma_debe']  or 0))
        sh = Decimal(str(row['suma_haber'] or 0))
        if row['cuenta__tipo'] == 'I':
            saldo_cuenta = sh - sd   # Ingresos: naturaleza acreedora
            resultado_neto += saldo_cuenta
            if abs(saldo_cuenta) > Decimal('0.01'):
                # Para cerrar una cuenta de ingreso: DEBITAMOS
                lineas_cie.append({
                    'cuenta': row['cuenta_id'],
                    'debe': saldo_cuenta, 'haber': D,
                    'desc': f"Cierre — {row['cuenta__nombre']}"
                })
        else:
            saldo_cuenta = sd - sh   # Egresos: naturaleza deudora
            resultado_neto -= saldo_cuenta
            if abs(saldo_cuenta) > Decimal('0.01'):
                # Para cerrar una cuenta de egreso: ACREDITAMOS
                lineas_cie.append({
                    'cuenta': row['cuenta_id'],
                    'debe': D, 'haber': saldo_cuenta,
                    'desc': f"Cierre — {row['cuenta__nombre']}"
                })

    if not lineas_cie:
        return Response({'error': 'No hay cuentas de resultado con saldo para cerrar'}, status=400)

    # La diferencia va a la cuenta de Resultados del período
    if abs(resultado_neto) > Decimal('0.01'):
        if resultado_neto > 0:
            lineas_cie.append({'cuenta': CA['resultado'], 'debe': D, 'haber': resultado_neto, 'desc': 'Resultado del período'})
        else:
            lineas_cie.append({'cuenta': CA['resultado'], 'debe': abs(resultado_neto), 'haber': D, 'desc': 'Resultado del período'})

    with transaction.atomic():
        a = _crear_asiento(fecha, 'Asiento de Cierre — Refundición de Resultados', 'CIE', usuario=usuario)
        for l in lineas_cie:
            _linea(a, l['cuenta'], debe=l['debe'], haber=l['haber'], desc=l['desc'])

    return Response({
        'ok': True, 'id': a.id,
        'resultado_neto': float(resultado_neto),
        'lineas_generadas': len(lineas_cie),
    })


# ─────────────────────────────────────────────────────────────────────────────
# API — Mayorización y Anulación de Asientos
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def MayorizarAsiento(request, asiento_id):
    """Cambia el estado de un asiento a 'Mayorizado'."""
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
def AnularAsientoId(request, asiento_id):
    """Anula un asiento (manual o automático) generando un contraasiento."""
    try:
        a = ContabAsiento.objects.get(id=asiento_id)
    except ContabAsiento.DoesNotExist:
        return Response({'error': 'Asiento no encontrado'}, status=404)

    if a.anulado:
        return Response({'error': 'El asiento ya está anulado'}, status=400)

    inv = _anular_asiento(a.origen, a.origen_movim or a.id,
                          usuario=request.data.get('usuario', ''))
    if not inv:
        # Si no se encontró por origen, anulamos directamente por id
        a.anulado = True
        a.estado  = 'A'
        a.save(update_fields=['anulado', 'estado'])
        with transaction.atomic():
            inv = _crear_asiento(
                timezone.now().date(),
                f"ANULACIÓN de Asiento #{a.id} — {a.descripcion}",
                'ANU', a.id, request.data.get('usuario', '')
            )
            inv.asiento_origen = a
            inv.save(update_fields=['asiento_origen'])
            for linea in a.lineas.all():
                ContabAsientoDet.objects.create(
                    asiento=inv, cuenta=linea.cuenta,
                    debe=linea.haber, haber=linea.debe,
                    descripcion=f"Anulación: {linea.descripcion}",
                )

    return Response({'ok': True, 'id_contraasiento': inv.id if inv else None})


# ─────────────────────────────────────────────────────────────────────────────
# API — Consulta de Saldos
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def ConsultaSaldos(request):
    """
    Devuelve los saldos de todas las cuentas imputables para un período dado.
    Útil para la pantalla 'Consulta de Saldos - Mayores y Asientos' de Onvio.

    Query params:
      ?desde=YYYY-MM-DD&hasta=YYYY-MM-DD&tipo=A,P,PN,I,E (opcional)
      ?cuenta=1.1.01.001 (opcional, filtra una cuenta específica)
    """
    desde   = request.query_params.get('desde')
    hasta   = request.query_params.get('hasta')
    tipos   = request.query_params.get('tipo', '').split(',')
    cuenta  = request.query_params.get('cuenta', '')

    qs = ContabAsientoDet.objects.filter(
        asiento__anulado=False,
        asiento__estado='M',   # solo mayorizados
    )
    if desde:
        qs = qs.filter(asiento__fecha__gte=desde)
    if hasta:
        qs = qs.filter(asiento__fecha__lte=hasta)
    if cuenta:
        qs = qs.filter(cuenta_id=cuenta)

    agg = (
        qs.values('cuenta_id')
        .annotate(suma_debe=Sum('debe'), suma_haber=Sum('haber'))
        .order_by('cuenta_id')
    )

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


# ─────────────────────────────────────────────────────────────────────────────
# API — Importación de Asientos (CSV/JSON)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def ImportarAsientos(request):
    """
    Importa asientos desde JSON.
    Payload:
    {
      "asientos": [
        {
          "fecha": "2024-01-15",
          "descripcion": "Asiento importado",
          "tipo_asiento": "001",
          "serie": "DIA",
          "lineas": [
            {"cuenta": "1.1.01.001", "debe": 1000, "haber": 0, "descripcion": ""},
            {"cuenta": "4.1.01.001", "debe": 0,    "haber": 1000, "descripcion": ""}
          ]
        }
      ]
    }
    """
    asientos_in = request.data.get('asientos', [])
    if not asientos_in:
        return Response({'error': 'No se recibieron asientos'}, status=400)

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
            if abs(td - th) > Decimal('0.02'):
                errores.append(f"Asiento {i} '{asi.get('descripcion','')}': no cuadra (D={td} H={th})")
                continue

            with transaction.atomic():
                a = _crear_asiento(
                    fecha        = asi['fecha'],
                    descripcion  = asi.get('descripcion', 'Asiento importado'),
                    origen       = 'IMP',
                    usuario      = asi.get('usuario', 'importacion'),
                    tipo_pk      = asi.get('tipo_asiento', '001'),
                    serie_pk     = asi.get('serie', 'DIA'),
                    estado       = 'M',
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
        'ok':        len(errores) == 0,
        'importados': importados,
        'errores':   errores,
        'total':     len(asientos_in),
    })


# ─────────────────────────────────────────────────────────────────────────────
# API — Sincronización histórica (sin cambios funcionales, mejorada)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def SincronizarAsientos(request):
    generados = {'ventas': 0, 'compras': 0, 'recibos': 0, 'errores': []}

    ids_vta = set(ContabAsiento.objects.filter(origen='VTA').values_list('origen_movim', flat=True))
    for v in Ventas.objects.filter(anulado='N').exclude(movim__in=ids_vta):
        try:
            if _generar_asiento_venta(v):
                generados['ventas'] += 1
        except Exception as e:
            generados['errores'].append(f"VTA movim={v.movim}: {e}")

    ids_cmp = set(ContabAsiento.objects.filter(origen='CMP').values_list('origen_movim', flat=True))
    for c in Compras.objects.filter(anulado__isnull=True).exclude(movim__in=ids_cmp):
        try:
            if _generar_asiento_compra(c):
                generados['compras'] += 1
        except Exception as e:
            generados['errores'].append(f"CMP movim={c.movim}: {e}")

    ids_rec = set(ContabAsiento.objects.filter(origen='REC').values_list('origen_movim', flat=True))
    for r in Recibos.objects.filter(anulado='N').exclude(numero__in=ids_rec):
        try:
            if _generar_asiento_recibo(r):
                generados['recibos'] += 1
        except Exception as e:
            generados['errores'].append(f"REC nro={r.numero}: {e}")

    return Response({
        'ok': True,
        'generados': generados,
        'total': generados['ventas'] + generados['compras'] + generados['recibos'],
    })


# ─────────────────────────────────────────────────────────────────────────────
# API — Plan de Cuentas
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def ListarPlanCuentas(request):
    solo_imputables = request.query_params.get('imputables') == '1'
    tipo_filtro     = request.query_params.get('tipo', '')
    qs = ContabPlanCuentas.objects.filter(activa=True)
    if solo_imputables:
        qs = qs.filter(es_imputable=True)
    if tipo_filtro:
        qs = qs.filter(tipo__in=tipo_filtro.split(','))
    data = [
        {
            'codigo': c.codigo, 'nombre': c.nombre, 'tipo': c.tipo,
            'nivel': c.nivel, 'padre': c.padre_id,
            'es_imputable': c.es_imputable, 'saldo_tipo': c.saldo_tipo,
            'activa': c.activa, 'codigo_alt': c.codigo_alt,
            'col_impresion': c.col_impresion,
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
            'codigo_alt':    d.get('codigo_alt', ''),
            'col_impresion': int(d.get('col_impresion', 1)),
        },
    )
    return Response({'ok': True, 'creado': created, 'codigo': obj.codigo})


# ─────────────────────────────────────────────────────────────────────────────
# API — CRUD Asientos
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
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
            'id':          a.id,
            'fecha':       a.fecha,
            'descripcion': a.descripcion,
            'origen':      a.origen,
            'estado':      a.estado,
            'numero':      a.numero,
            'serie':       a.serie_id,
            'tipo_asiento': a.tipo_asiento_id,
            'ejercicio':   a.ejercicio_id,
            'total_debe':  float(td),
            'total_haber': float(th),
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
            'id': l.id, 'cuenta': l.cuenta_id, 'nombre': l.cuenta.nombre,
            'debe': float(l.debe), 'haber': float(l.haber), 'descripcion': l.descripcion,
        }
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
def CrearAsientoManual(request):
    d      = request.data
    lineas = d.get('lineas', [])
    if len(lineas) < 2:
        return Response({'ok': False, 'error': 'Se requieren al menos 2 líneas'}, status=400)

    td = sum(Decimal(str(l.get('debe',  0))) for l in lineas)
    th = sum(Decimal(str(l.get('haber', 0))) for l in lineas)
    if abs(td - th) > Decimal('0.01'):
        return Response({'ok': False, 'error': f'El asiento no cuadra: D={td} H={th}'}, status=400)

    with transaction.atomic():
        a = _crear_asiento(
            fecha        = d.get('fecha', timezone.now().date()),
            descripcion  = d.get('descripcion', 'Asiento manual'),
            origen       = 'AJU',
            usuario      = d.get('usuario', ''),
            tipo_pk      = d.get('tipo_asiento', '001'),
            serie_pk     = d.get('serie', 'DIA'),
            estado       = d.get('estado', 'B'),
        )
        for l in lineas:
            _linea(a, l['cuenta'],
                   debe=Decimal(str(l.get('debe', 0))),
                   haber=Decimal(str(l.get('haber', 0))),
                   desc=l.get('descripcion', ''))

    return Response({'ok': True, 'id': a.id})


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
# API — Informes (sin cambios respecto a versión anterior, se mantienen)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
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
        'cuadra': abs(td_total - th_total) < Decimal('0.02'),
    })


@api_view(['GET'])
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
        saldo_acum += l.debe - l.haber if cuenta.saldo_tipo == 'D' else l.haber - l.debe
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
        'cuadra': abs(gd - gh) < Decimal('0.02'),
    })


@api_view(['GET'])
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
        'cuadra': abs(totales['A'] - total_pasivo_pn) < Decimal('0.02'),
    })