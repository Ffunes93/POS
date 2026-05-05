"""
maestros/views/contabilidad_config.py — Sprint A · A1

Endpoints para gestionar la tabla ContabConfigCuenta (mapeo concepto → cuenta).

Endpoints expuestos:
  GET    /api/contab/Config/Cuentas/                     → lista completa
  POST   /api/contab/Config/Cuentas/                     → crear/actualizar uno
  GET    /api/contab/Config/Cuentas/<concepto>/          → detalle
  PUT    /api/contab/Config/Cuentas/<concepto>/          → actualizar
  DELETE /api/contab/Config/Cuentas/<concepto>/          → eliminar
  GET    /api/contab/Config/ConceptosDisponibles/        → lista catálogo
  GET    /api/contab/Config/Estado/                      → diagnóstico (qué falta)
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from ..models import ContabConfigCuenta, ContabPlanCuentas
from ..permissions import ContabAuth, get_usuario_actual


@api_view(['GET', 'POST'])
@permission_classes([ContabAuth])
def ListarOCrearConfigCuentas(request):
    """
    GET  → devuelve toda la config con detalle de la cuenta asociada
    POST → upsert: crea o actualiza la entrada para el concepto enviado
    """
    if request.method == 'GET':
        items = (ContabConfigCuenta.objects
                 .select_related('cuenta')
                 .all())
        data = [
            {
                'concepto':           c.concepto,
                'concepto_label':     c.get_concepto_display(),
                'cuenta_codigo':      c.cuenta_id,
                'cuenta_nombre':      c.cuenta.nombre,
                'cuenta_tipo':        c.cuenta.tipo,
                'cuenta_es_imputable': c.cuenta.es_imputable,
                'descripcion_extra':  c.descripcion_extra,
                'fecha_mod':          c.fecha_mod,
                'usuario':            c.usuario,
            }
            for c in items
        ]
        return Response({'ok': True, 'data': data, 'total': len(data)})

    # POST — upsert
    d = request.data
    concepto = (d.get('concepto') or '').strip().upper()
    cuenta_codigo = (d.get('cuenta_codigo') or d.get('cuenta') or '').strip()

    if not concepto:
        return Response({'ok': False, 'error': 'concepto requerido'}, status=400)
    if not cuenta_codigo:
        return Response({'ok': False, 'error': 'cuenta_codigo requerido'}, status=400)

    # Validar que el concepto sea uno del catálogo
    conceptos_validos = {c[0] for c in ContabConfigCuenta.CONCEPTO_CHOICES}
    if concepto not in conceptos_validos:
        return Response({
            'ok': False,
            'error': f"Concepto '{concepto}' no está en el catálogo. "
                     f"GET /api/contab/Config/ConceptosDisponibles/ para ver válidos."
        }, status=400)

    # Validar que la cuenta exista, esté activa y sea imputable
    try:
        cuenta = ContabPlanCuentas.objects.get(codigo=cuenta_codigo)
    except ContabPlanCuentas.DoesNotExist:
        return Response({'ok': False, 'error': f"Cuenta '{cuenta_codigo}' no existe"},
                        status=400)

    if not cuenta.activa:
        return Response({'ok': False,
                         'error': f"Cuenta '{cuenta_codigo}' está inactiva"}, status=400)

    if not cuenta.es_imputable:
        return Response({'ok': False,
                         'error': f"Cuenta '{cuenta_codigo}' no es imputable. "
                                  "Asigne una cuenta de último nivel."}, status=400)

    obj, created = ContabConfigCuenta.objects.update_or_create(
        concepto=concepto,
        defaults={
            'cuenta':            cuenta,
            'descripcion_extra': d.get('descripcion_extra', ''),
            'usuario':           get_usuario_actual(request)[:50],
        }
    )

    return Response({
        'ok': True,
        'creado': created,
        'concepto': obj.concepto,
        'cuenta_codigo': obj.cuenta_id,
    })


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([ContabAuth])
def DetalleConfigCuenta(request, concepto):
    concepto = concepto.upper()
    try:
        obj = ContabConfigCuenta.objects.select_related('cuenta').get(pk=concepto)
    except ContabConfigCuenta.DoesNotExist:
        return Response({'ok': False, 'error': 'No encontrado'}, status=404)

    if request.method == 'GET':
        return Response({
            'concepto':           obj.concepto,
            'concepto_label':     obj.get_concepto_display(),
            'cuenta_codigo':      obj.cuenta_id,
            'cuenta_nombre':      obj.cuenta.nombre,
            'cuenta_tipo':        obj.cuenta.tipo,
            'descripcion_extra':  obj.descripcion_extra,
            'fecha_mod':          obj.fecha_mod,
            'usuario':            obj.usuario,
        })

    if request.method == 'DELETE':
        obj.delete()
        return Response({'ok': True})

    # PUT
    d = request.data
    if 'cuenta_codigo' in d or 'cuenta' in d:
        codigo = (d.get('cuenta_codigo') or d.get('cuenta') or '').strip()
        try:
            nueva = ContabPlanCuentas.objects.get(codigo=codigo)
        except ContabPlanCuentas.DoesNotExist:
            return Response({'ok': False,
                             'error': f"Cuenta '{codigo}' no existe"}, status=400)
        if not nueva.activa or not nueva.es_imputable:
            return Response({'ok': False,
                             'error': f"Cuenta '{codigo}' debe ser activa e imputable"},
                            status=400)
        obj.cuenta = nueva

    if 'descripcion_extra' in d:
        obj.descripcion_extra = d.get('descripcion_extra', '')

    obj.usuario = get_usuario_actual(request)[:50]
    obj.save()
    return Response({'ok': True, 'concepto': obj.concepto, 'cuenta_codigo': obj.cuenta_id})


@api_view(['GET'])
@permission_classes([ContabAuth])
def ConceptosDisponibles(request):
    """
    Devuelve el catálogo completo de conceptos canónicos, agrupados por familia.
    Útil para que el frontend arme un wizard de configuración inicial.
    """
    grupos = {
        'Disponibilidades':    [],
        'Créditos':            [],
        'IVA Crédito Fiscal':  [],
        'Bienes de Cambio':    [],
        'Pasivos comerciales': [],
        'IVA Débito Fiscal':   [],
        'Retenciones a depositar': [],
        'Percepciones a depositar': [],
        'Otros pasivos':       [],
        'Patrimonio Neto':     [],
        'Ingresos':            [],
        'Resultados varios':   [],
    }

    mapeo = {
        'CAJA': 'Disponibilidades', 'BANCO_DEFAULT': 'Disponibilidades',
        'VALORES_A_DEPOSITAR': 'Disponibilidades', 'CUPONES_A_COBRAR': 'Disponibilidades',

        'DEUDORES_CC': 'Créditos',
        'RETENCION_IVA_SUFRIDA': 'Créditos', 'RETENCION_GAN_SUFRIDA': 'Créditos',
        'RETENCION_IIBB_SUFRIDA': 'Créditos', 'RETENCION_SUSS_SUFRIDA': 'Créditos',

        'IVA_CF_21': 'IVA Crédito Fiscal', 'IVA_CF_10_5': 'IVA Crédito Fiscal',
        'IVA_CF_27': 'IVA Crédito Fiscal', 'IVA_CF_5': 'IVA Crédito Fiscal',
        'IVA_CF_2_5': 'IVA Crédito Fiscal', 'IVA_CF_0': 'IVA Crédito Fiscal',

        'MERCADERIAS_DEFAULT': 'Bienes de Cambio',

        'PROVEEDORES': 'Pasivos comerciales',

        'IVA_DF_21': 'IVA Débito Fiscal', 'IVA_DF_10_5': 'IVA Débito Fiscal',
        'IVA_DF_27': 'IVA Débito Fiscal', 'IVA_DF_5': 'IVA Débito Fiscal',
        'IVA_DF_2_5': 'IVA Débito Fiscal', 'IVA_DF_0': 'IVA Débito Fiscal',

        'RETENCION_IVA_PRACTICADA':  'Retenciones a depositar',
        'RETENCION_GAN_PRACTICADA':  'Retenciones a depositar',
        'RETENCION_IIBB_PRACTICADA': 'Retenciones a depositar',

        'PERCEPCION_IIBB_CABA_PRACTICADA': 'Percepciones a depositar',
        'PERCEPCION_IIBB_BSAS_PRACTICADA': 'Percepciones a depositar',
        'PERCEPCION_5329_PRACTICADA':      'Percepciones a depositar',

        'IMPUESTOS_INTERNOS': 'Otros pasivos',

        'RESULTADO_NO_ASIGNADO':    'Patrimonio Neto',
        'RESULTADO_DEL_EJERCICIO':  'Patrimonio Neto',

        'VENTAS_21': 'Ingresos', 'VENTAS_10_5': 'Ingresos', 'VENTAS_27': 'Ingresos',
        'VENTAS_5': 'Ingresos', 'VENTAS_2_5': 'Ingresos', 'VENTAS_0': 'Ingresos',
        'VENTAS_EXENTAS': 'Ingresos', 'VENTAS_NO_GRAVADAS': 'Ingresos',

        'DIFERENCIA_REDONDEO': 'Resultados varios',
        'DIFERENCIA_CAMBIO_POS': 'Resultados varios',
        'DIFERENCIA_CAMBIO_NEG': 'Resultados varios',
        'COMISIONES_TARJETAS': 'Resultados varios',
        'DESCUENTOS_OTORGADOS': 'Resultados varios',
        'RECARGOS_FINANCIEROS': 'Resultados varios',
    }

    configurados = set(ContabConfigCuenta.objects.values_list('concepto', flat=True))

    for codigo, label in ContabConfigCuenta.CONCEPTO_CHOICES:
        familia = mapeo.get(codigo, 'Otros')
        if familia not in grupos:
            grupos[familia] = []
        grupos[familia].append({
            'concepto':    codigo,
            'label':       label,
            'configurado': codigo in configurados,
        })

    return Response({'ok': True, 'grupos': grupos})


@api_view(['GET'])
@permission_classes([ContabAuth])
def EstadoConfig(request):
    """
    Diagnóstico: indica qué conceptos faltan y cuáles son críticos para la
    operación contable básica. El frontend puede usarlo para mostrar un
    "completá tu configuración" en el dashboard.
    """
    todos = {c[0] for c in ContabConfigCuenta.CONCEPTO_CHOICES}
    configurados = set(ContabConfigCuenta.objects.values_list('concepto', flat=True))
    faltantes = todos - configurados

    # Conceptos sin los cuales la operación básica no funciona
    criticos = {
        'CAJA', 'DEUDORES_CC', 'PROVEEDORES',
        'VENTAS_21', 'IVA_DF_21',
        'MERCADERIAS_DEFAULT', 'IVA_CF_21',
    }
    faltantes_criticos = sorted(criticos & faltantes)

    # Recomendados (sin estos algunos casos no se imputan bien, pero opera)
    recomendados = {
        'BANCO_DEFAULT', 'VALORES_A_DEPOSITAR',
        'VENTAS_10_5', 'VENTAS_EXENTAS',
        'IVA_DF_10_5', 'IVA_CF_10_5',
        'PERCEPCION_IIBB_CABA_PRACTICADA',
        'PERCEPCION_IIBB_BSAS_PRACTICADA',
        'RESULTADO_NO_ASIGNADO', 'DIFERENCIA_REDONDEO',
    }
    faltantes_recomendados = sorted(recomendados & faltantes)

    return Response({
        'ok': True,
        'total_conceptos':       len(todos),
        'configurados':          len(configurados),
        'faltantes':             len(faltantes),
        'faltantes_criticos':    faltantes_criticos,
        'faltantes_recomendados': faltantes_recomendados,
        'porcentaje_completado': round(100 * len(configurados) / len(todos), 1),
        'puede_operar':          len(faltantes_criticos) == 0,
    })