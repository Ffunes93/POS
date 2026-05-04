"""
restaurante.py — API completa del módulo de restaurante.

Endpoints agrupados:
  /api/rest/sectores/          GET, POST
  /api/rest/mesas/             GET — plano completo con estado actual
  /api/rest/mesa/<id>/         PATCH — editar posición/capacidad
  /api/rest/abrir_mesa/        POST — abre mesa y crea pedido
  /api/rest/pedido/<id>/       GET — detalle completo del pedido activo
  /api/rest/agregar_item/      POST — agrega ítem al pedido
  /api/rest/quitar_item/       POST — elimina / reduce cantidad
  /api/rest/enviar_cocina/     POST — envía ítems pendientes como comanda
  /api/rest/pedir_cuenta/      POST — cambia estado mesa a cuenta_pedida
  /api/rest/facturar_mesa/     POST — genera venta y cierra mesa
  /api/rest/cancelar_pedido/   POST — cancela el pedido activo
  /api/rest/comandas/          GET — vista cocina (ítems pendientes)
  /api/rest/marcar_listo/      POST — cocina marca ítem como listo
  /api/rest/historial/         GET — pedidos del día
"""
from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import Articulos, Clientes
from ..restaurant_models import (
    RestSector, RestMesa, RestPedido, RestPedidoDet, RestComanda, 
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pedido_to_dict(p: RestPedido) -> dict:
    items = []
    for it in p.items.exclude(estado_item='cancelado'):
        items.append({
            'id':          it.id,
            'cod_art':     it.cod_art,
            'nombre_art':  it.nombre_art,
            'cantidad':    float(it.cantidad),
            'precio_unit': float(it.precio_unit),
            'subtotal':    float(it.subtotal),
            'p_iva':       float(it.p_iva),
            'observac':    it.observac,
            'estado_item': it.estado_item,
            'nro_comanda': it.nro_comanda,
        })
    return {
        'id':            p.id,
        'mesa_id':       p.mesa_id,
        'mesa_numero':   p.mesa.numero,
        'mesa_sector':   p.mesa.sector.nombre,
        'estado':        p.estado,
        'mozo_id':       p.mozo_id,
        'mozo_nombre':   p.mozo_nombre,
        'cod_cli':       p.cod_cli,
        'comensales':    p.comensales,
        'observac':      p.observac,
        'subtotal':      float(p.subtotal),
        'total':         float(p.total),
        'fecha_apertura': p.fecha_apertura.strftime('%d/%m/%Y %H:%M'),
        'items':         items,
        'pendientes_cocina': sum(1 for i in items if i['estado_item'] == 'pendiente'),
    }


def _recalcular_totales(pedido: RestPedido):
    items = pedido.items.exclude(estado_item='cancelado')
    sub   = sum(i.subtotal for i in items)
    pedido.subtotal = sub
    pedido.total    = sub
    pedido.save(update_fields=['subtotal', 'total'])


# ── Sectores ──────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def GestionSectores(request):
    if request.method == 'GET':
        data = [
            {'id': s.id, 'nombre': s.nombre, 'color': s.color,
             'orden': s.orden, 'activo': s.activo,
             'cant_mesas': s.mesas.filter(activa=True).count()}
            for s in RestSector.objects.filter(activo=True)
        ]
        return Response({'status': 'success', 'data': data})

    d = request.data
    sector_id = d.get('id')
    if sector_id:
        sector = RestSector.objects.filter(id=sector_id).first()
        if not sector:
            return Response({'status': 'error', 'mensaje': 'Sector no encontrado.'}, status=404)
    else:
        sector = RestSector()

    sector.nombre = str(d.get('nombre', '')).strip()
    sector.color  = str(d.get('color', '#3498db'))
    sector.orden  = int(d.get('orden', 0))
    sector.activo = bool(d.get('activo', True))
    sector.save()
    return Response({'status': 'success', 'id': sector.id, 'mensaje': 'Sector guardado.'})


# ── Plano de mesas ────────────────────────────────────────────────────────────

@api_view(['GET'])
def ObtenerPlano(request):
    """
    Devuelve todos los sectores con sus mesas y el pedido activo de cada una.
    Es el endpoint principal del plano visual.
    """
    sector_id = request.query_params.get('sector_id')
    qs = RestSector.objects.filter(activo=True)
    if sector_id:
        qs = qs.filter(id=sector_id)

    sectores = []
    for sec in qs:
        mesas = []
        for m in sec.mesas.filter(activa=True):
            # Pedido activo (no facturado/cancelado)
            pedido_activo = RestPedido.objects.filter(
                mesa=m,
                estado__in=['abierto', 'enviado', 'listo', 'cuenta'],
            ).order_by('-fecha_apertura').first()

            mesas.append({
                'id':       m.id,
                'numero':   m.numero,
                'capacidad':m.capacidad,
                'estado':   m.estado,
                'pos_x':    m.pos_x,
                'pos_y':    m.pos_y,
                'pedido_id':      pedido_activo.id if pedido_activo else None,
                'pedido_total':   float(pedido_activo.total) if pedido_activo else 0,
                'pedido_items':   pedido_activo.items.exclude(estado_item='cancelado').count()
                                  if pedido_activo else 0,
                'mozo_nombre':    pedido_activo.mozo_nombre if pedido_activo else '',
                'minutos_abierto': int(
                    (timezone.now() - pedido_activo.fecha_apertura).total_seconds() / 60
                ) if pedido_activo else 0,
            })
        sectores.append({
            'id':     sec.id,
            'nombre': sec.nombre,
            'color':  sec.color,
            'mesas':  mesas,
        })
    return Response({'status': 'success', 'data': sectores})


@api_view(['PATCH'])
def ActualizarMesa(request, mesa_id):
    """Actualiza posición, capacidad o nombre de una mesa (drag & drop del plano)."""
    try:
        mesa = RestMesa.objects.get(id=mesa_id)
    except RestMesa.DoesNotExist:
        return Response({'status': 'error', 'mensaje': 'Mesa no encontrada.'}, status=404)

    d = request.data
    if 'pos_x'    in d: mesa.pos_x    = int(d['pos_x'])
    if 'pos_y'    in d: mesa.pos_y    = int(d['pos_y'])
    if 'capacidad'in d: mesa.capacidad= int(d['capacidad'])
    if 'numero'   in d: mesa.numero   = str(d['numero'])
    if 'activa'   in d: mesa.activa   = bool(d['activa'])
    mesa.save()
    return Response({'status': 'success', 'mensaje': 'Mesa actualizada.'})


@api_view(['POST'])
def CrearMesa(request):
    """Crea una nueva mesa en un sector."""
    d = request.data
    sector = RestSector.objects.filter(id=d.get('sector_id')).first()
    if not sector:
        return Response({'status': 'error', 'mensaje': 'Sector inválido.'}, status=400)

    mesa = RestMesa.objects.create(
        sector   = sector,
        numero   = str(d.get('numero', '')).strip(),
        capacidad= int(d.get('capacidad', 4)),
        pos_x    = int(d.get('pos_x', 0)),
        pos_y    = int(d.get('pos_y', 0)),
        estado   = 'libre',
        activa   = True,
    )
    return Response({'status': 'success', 'id': mesa.id, 'mensaje': f'Mesa {mesa.numero} creada.'})


# ── Pedidos ───────────────────────────────────────────────────────────────────

@api_view(['POST'])
def AbrirMesa(request):
    """
    Abre una mesa y crea el pedido.
    Si ya tiene un pedido activo, lo devuelve.

    Payload: { "mesa_id": 1, "mozo_id": 2, "mozo_nombre": "Juan", "comensales": 4 }
    """
    d        = request.data
    mesa_id  = d.get('mesa_id')
    mozo_id  = int(d.get('mozo_id', 1))
    comensales = int(d.get('comensales', 1))

    try:
        mesa = RestMesa.objects.get(id=mesa_id, activa=True)
    except RestMesa.DoesNotExist:
        return Response({'status': 'error', 'mensaje': 'Mesa no encontrada.'}, status=404)

    # Verificar pedido activo existente
    pedido_activo = RestPedido.objects.filter(
        mesa=mesa, estado__in=['abierto', 'enviado', 'listo', 'cuenta']
    ).first()

    if pedido_activo:
        return Response({
            'status':   'success',
            'pedido_id': pedido_activo.id,
            'nuevo':     False,
            'mensaje':  'Mesa ya abierta, continuando pedido existente.',
        })

    with transaction.atomic():
        pedido = RestPedido.objects.create(
            mesa        = mesa,
            mozo_id     = mozo_id,
            mozo_nombre = str(d.get('mozo_nombre', ''))[:60],
            comensales  = comensales,
            cod_cli     = int(d.get('cod_cli', 1)),
            observac    = str(d.get('observac', '')),
            usuario     = str(d.get('usuario', 'admin')),
        )
        mesa.estado = 'ocupada'
        mesa.save(update_fields=['estado'])

    return Response({
        'status':    'success',
        'pedido_id': pedido.id,
        'nuevo':     True,
        'mensaje':   f'Mesa {mesa.numero} abierta.',
    })


@api_view(['GET'])
def ObtenerPedido(request, pedido_id):
    """Detalle completo del pedido con todos sus ítems."""
    try:
        pedido = RestPedido.objects.select_related('mesa__sector').get(id=pedido_id)
    except RestPedido.DoesNotExist:
        return Response({'status': 'error', 'mensaje': 'Pedido no encontrado.'}, status=404)
    return Response({'status': 'success', 'data': _pedido_to_dict(pedido)})


@api_view(['POST'])
def AgregarItem(request):
    """
    Agrega un ítem al pedido.
    Si el mismo artículo sin observación ya existe como 'pendiente', suma cantidad.

    Payload: {
      "pedido_id": 1,
      "cod_art": "BIFE001",
      "cantidad": 1,
      "observac": "sin sal"
    }
    """
    d          = request.data
    pedido_id  = d.get('pedido_id')
    cod_art    = str(d.get('cod_art', '')).strip()
    cantidad   = Decimal(str(d.get('cantidad', 1)))
    observac   = str(d.get('observac', '')).strip()

    try:
        pedido = RestPedido.objects.get(id=pedido_id)
    except RestPedido.DoesNotExist:
        return Response({'status': 'error', 'mensaje': 'Pedido no encontrado.'}, status=404)

    if pedido.estado in ('facturado', 'cancelado'):
        return Response({'status': 'error', 'mensaje': 'El pedido ya está cerrado.'}, status=400)

    # Buscar artículo
    art = Articulos.objects.filter(cod_art=cod_art).first()
    if not art:
        return Response({'status': 'error', 'mensaje': f'Artículo {cod_art} no encontrado.'}, status=404)

    precio = Decimal(str(art.precio_1 or 0))
    p_iva  = Decimal(str(art.iva or 21))

    with transaction.atomic():
        # ¿Existe el mismo ítem pendiente sin obs? → sumar cantidad
        item_existente = pedido.items.filter(
            cod_art=cod_art,
            estado_item='pendiente',
            observac=observac,
        ).first() if not observac else None

        if item_existente:
            item_existente.cantidad += cantidad
            item_existente.subtotal  = item_existente.cantidad * precio
            item_existente.save()
            item = item_existente
        else:
            item = RestPedidoDet.objects.create(
                pedido     = pedido,
                cod_art    = cod_art,
                nombre_art = art.nombre[:100],
                cantidad   = cantidad,
                precio_unit= precio,
                subtotal   = cantidad * precio,
                p_iva      = p_iva,
                observac   = observac,
            )

        _recalcular_totales(pedido)
        if pedido.estado == 'abierto':
            pass  # permanece en abierto hasta enviar_cocina

    return Response({
        'status':   'success',
        'item_id':  item.id,
        'subtotal': float(pedido.total),
        'mensaje':  f'{art.nombre} agregado.',
    })


@api_view(['POST'])
def QuitarItem(request):
    """
    Quita o reduce un ítem del pedido.
    Solo permite cancelar ítems en estado 'pendiente'.

    Payload: { "item_id": 5, "cantidad": 1 }  — 0 o null = eliminar todo
    """
    item_id  = request.data.get('item_id')
    cantidad = request.data.get('cantidad')  # None = eliminar todo

    try:
        item = RestPedidoDet.objects.select_related('pedido').get(id=item_id)
    except RestPedidoDet.DoesNotExist:
        return Response({'status': 'error', 'mensaje': 'Ítem no encontrado.'}, status=404)

    if item.estado_item not in ('pendiente',):
        return Response({'status': 'error',
                          'mensaje': f'No se puede quitar un ítem en estado {item.estado_item}.'}, status=400)

    with transaction.atomic():
        if cantidad is None or Decimal(str(cantidad)) >= item.cantidad:
            item.estado_item = 'cancelado'
            item.save(update_fields=['estado_item'])
        else:
            nueva = item.cantidad - Decimal(str(cantidad))
            item.cantidad = nueva
            item.subtotal = nueva * item.precio_unit
            item.save()

        _recalcular_totales(item.pedido)

    return Response({'status': 'success', 'mensaje': 'Ítem actualizado.', 'total': float(item.pedido.total)})


@api_view(['POST'])
def EnviarCocina(request):
    """
    Envía todos los ítems 'pendiente' a cocina/barra.
    Crea una RestComanda y cambia el estado de los ítems a 'enviado'.

    Payload: { "pedido_id": 1, "usuario": "mozo1" }
    """
    pedido_id = request.data.get('pedido_id')
    usuario   = str(request.data.get('usuario', 'mozo'))

    try:
        pedido = RestPedido.objects.get(id=pedido_id)
    except RestPedido.DoesNotExist:
        return Response({'status': 'error', 'mensaje': 'Pedido no encontrado.'}, status=404)

    pendientes = pedido.items.filter(estado_item='pendiente')
    if not pendientes.exists():
        return Response({'status': 'error', 'mensaje': 'No hay ítems pendientes para enviar.'}, status=400)

    with transaction.atomic():
        # Número de comanda: cantidad de comandas previas + 1
        nro = pedido.comandas.count() + 1
        turno = (pedido.comandas.aggregate(
            t=__import__('django.db.models', fromlist=['Max']).Max('turno'))['t'] or 0) + 1

        # Comanda de cocina
        comanda = RestComanda.objects.create(
            pedido=pedido, nro_comanda=nro, destino='cocina',
            turno=turno, usuario=usuario,
        )

        # Actualizar ítems
        pendientes.update(estado_item='enviado', nro_comanda=nro, turno_envio=turno)

        # Estado del pedido
        pedido.estado = 'enviado'
        pedido.save(update_fields=['estado'])

    return Response({
        'status':      'success',
        'nro_comanda': nro,
        'cant_items':  pendientes.count(),
        'mensaje':     f'Comanda #{nro} enviada a cocina.',
    })


@api_view(['POST'])
def PedirCuenta(request):
    """Marca la mesa como 'cuenta pedida'."""
    pedido_id = request.data.get('pedido_id')
    try:
        pedido = RestPedido.objects.select_related('mesa').get(id=pedido_id)
    except RestPedido.DoesNotExist:
        return Response({'status': 'error', 'mensaje': 'Pedido no encontrado.'}, status=404)

    pedido.estado = 'cuenta'
    pedido.save(update_fields=['estado'])
    pedido.mesa.estado = 'cuenta_pedida'
    pedido.mesa.save(update_fields=['estado'])

    return Response({
        'status':  'success',
        'mensaje': f'Cuenta pedida para Mesa {pedido.mesa.numero}. Total: ${float(pedido.total):.2f}',
        'total':   float(pedido.total),
    })


@api_view(['POST'])
def FacturarMesa(request):
    """
    Genera la venta completa usando el endpoint existente de ventas y cierra la mesa.

    Payload: {
      "pedido_id": 1,
      "tipo_comprob": "EB",
      "cajero": 1,
      "nro_caja": 1,
      "usuario": "admin",
      "medio_pago": "EFE",   // o lista de medios
      "cod_cli": 1
    }

    Internamente llama a la lógica de IngresarComprobanteVentasJSON reutilizando
    el código ya existente sin duplicarlo.
    """
    d = request.data
    pedido_id   = d.get('pedido_id')
    tipo_comprob= str(d.get('tipo_comprob', 'EB'))
    cajero      = int(d.get('cajero', 1))
    nro_caja    = int(d.get('nro_caja', 1))
    usuario     = str(d.get('usuario', 'admin'))
    medio_pago  = str(d.get('medio_pago', 'EFE'))
    cod_cli     = int(d.get('cod_cli', 1))
    pto_vta     = str(d.get('pto_venta', '0001')).zfill(4)

    try:
        pedido = RestPedido.objects.select_related('mesa').get(id=pedido_id)
    except RestPedido.DoesNotExist:
        return Response({'status': 'error', 'mensaje': 'Pedido no encontrado.'}, status=404)

    if pedido.estado == 'facturado':
        return Response({'status': 'error', 'mensaje': 'Este pedido ya fue facturado.'}, status=400)

    items_activos = pedido.items.exclude(estado_item__in=['cancelado'])
    if not items_activos.exists():
        return Response({'status': 'error', 'mensaje': 'El pedido no tiene ítems.'}, status=400)

    # Construir payload para el sistema de ventas existente
    comprobante_items = []
    for it in items_activos:
        total_item = float(it.subtotal)
        tasa_iva   = float(it.p_iva)
        neto_item  = round(total_item / (1 + tasa_iva / 100), 2)
        iva_item   = round(total_item - neto_item, 2)
        comprobante_items.append({
            'Item_CodigoArticulo':    it.cod_art,
            'Item_DescripArticulo':   it.nombre_art,
            'Item_CantidadUM1':       float(it.cantidad),
            'Item_PrecioUnitario':    float(it.precio_unit),
            'Item_ImporteTotal':      total_item,
            'Item_TasaIVAInscrip':    tasa_iva,
            'Item_ImporteIVAInscrip': iva_item,
        })

    total_general = float(pedido.total)
    neto_total    = round(sum(i['Item_ImporteTotal'] / (1 + i['Item_TasaIVAInscrip'] / 100)
                              for i in comprobante_items), 2)
    iva_total     = round(total_general - neto_total, 2)

    payload_venta = {
        'Cliente_Codigo':          cod_cli,
        'Comprobante_Tipo':        tipo_comprob,
        'Comprobante_Letra':       'B' if tipo_comprob.endswith('B') else 'A',
        'Comprobante_PtoVenta':    pto_vta,
        'Comprobante_Numero':      0,
        'Comprobante_FechaEmision': timezone.now().isoformat(),
        'Comprobante_Neto':        neto_total,
        'Comprobante_IVA':         iva_total,
        'Comprobante_ImporteTotal': total_general,
        'Comprobante_CondVenta':   '1',
        'cajero':                  cajero,
        'nro_caja':                nro_caja,
        'Vendedor_Codigo':         pedido.mozo_id,
        'Comprobante_Usuario':     usuario,
        'Comprobante_Observac':    f'Mesa {pedido.mesa.numero} — {pedido.comensales} comensal(es)',
        'Comprobante_Items':       comprobante_items,
        'Comprobante_MediosPago':  [
            {'MedioPago': medio_pago, 'MedioPago_Importe': total_general}
        ],
    }

    # Llamar a la lógica de ventas directamente (import local para evitar circular)
    from .ventas import IngresarComprobanteVentasJSON
    from rest_framework.test import APIRequestFactory
    factory = APIRequestFactory()
    req_venta = factory.post('/api/IngresarComprobanteVentasJSON/', payload_venta, format='json')
    resp_venta = IngresarComprobanteVentasJSON(req_venta)

    if resp_venta.status_code not in (200, 201):
        return Response({
            'status':  'error',
            'mensaje': f'Error generando venta: {resp_venta.data}',
        }, status=400)

    movim_generado = resp_venta.data.get('movim')

    # Cerrar pedido y mesa
    with transaction.atomic():
        pedido.estado       = 'facturado'
        pedido.movim_venta  = movim_generado
        pedido.fecha_cierre = timezone.now()
        pedido.save(update_fields=['estado', 'movim_venta', 'fecha_cierre'])

        pedido.items.filter(estado_item__in=['listo', 'entregado', 'enviado', 'en_preparacion', 'pendiente'])\
                    .update(estado_item='entregado')

        pedido.mesa.estado = 'libre'
        pedido.mesa.save(update_fields=['estado'])

    return Response({
        'status':  'success',
        'movim':   movim_generado,
        'nro_comprob': resp_venta.data.get('nro_comprob'),
        'mensaje': f'Mesa {pedido.mesa.numero} facturada. Venta #{movim_generado}',
    })


@api_view(['POST'])
def CancelarPedido(request):
    """Cancela el pedido activo y libera la mesa."""
    pedido_id = request.data.get('pedido_id')
    motivo    = str(request.data.get('motivo', ''))

    try:
        pedido = RestPedido.objects.select_related('mesa').get(id=pedido_id)
    except RestPedido.DoesNotExist:
        return Response({'status': 'error', 'mensaje': 'Pedido no encontrado.'}, status=404)

    if pedido.estado == 'facturado':
        return Response({'status': 'error', 'mensaje': 'No se puede cancelar un pedido facturado.'}, status=400)

    with transaction.atomic():
        pedido.estado    = 'cancelado'
        pedido.observac  = (pedido.observac + f' | CANCELADO: {motivo}').strip()
        pedido.fecha_cierre = timezone.now()
        pedido.save()

        pedido.items.all().update(estado_item='cancelado')
        pedido.mesa.estado = 'libre'
        pedido.mesa.save(update_fields=['estado'])

    return Response({'status': 'success', 'mensaje': f'Pedido #{pedido_id} cancelado.'})


# ── Vista Cocina ──────────────────────────────────────────────────────────────

@api_view(['GET'])
def VistaComanda(request):
    """
    Vista para la pantalla de cocina/barra.
    Devuelve los ítems en estado 'enviado' y 'en_preparacion' agrupados por pedido.
    """
    destino = request.query_params.get('destino', 'cocina')  # cocina | barra

    items = RestPedidoDet.objects.filter(
        estado_item__in=['enviado', 'en_preparacion'],
        pedido__estado__in=['enviado', 'listo', 'cuenta'],
    ).select_related('pedido__mesa__sector').order_by('fecha_mod')

    # Agrupar por pedido
    grupos = {}
    for it in items:
        pid = it.pedido_id
        if pid not in grupos:
            grupos[pid] = {
                'pedido_id':    pid,
                'mesa_numero':  it.pedido.mesa.numero,
                'mesa_sector':  it.pedido.mesa.sector.nombre,
                'mozo':         it.pedido.mozo_nombre,
                'minutos':      int((timezone.now() - it.pedido.fecha_apertura).total_seconds() / 60),
                'items':        [],
            }
        grupos[pid]['items'].append({
            'id':          it.id,
            'cod_art':     it.cod_art,
            'nombre_art':  it.nombre_art,
            'cantidad':    float(it.cantidad),
            'observac':    it.observac,
            'estado_item': it.estado_item,
            'nro_comanda': it.nro_comanda,
            'minutos_item': int((timezone.now() - it.fecha_mod).total_seconds() / 60),
        })

    return Response({
        'status': 'success',
        'data':   list(grupos.values()),
        'total':  sum(len(g['items']) for g in grupos.values()),
    })


@api_view(['POST'])
def MarcarListoItem(request):
    """
    Cocina marca un ítem como listo (o en_preparacion).
    Payload: { "item_id": 5, "estado": "listo" }
    """
    item_id = request.data.get('item_id')
    estado  = request.data.get('estado', 'listo')

    if estado not in ('en_preparacion', 'listo', 'entregado'):
        return Response({'status': 'error', 'mensaje': 'Estado inválido.'}, status=400)

    updated = RestPedidoDet.objects.filter(id=item_id).update(estado_item=estado)
    if not updated:
        return Response({'status': 'error', 'mensaje': 'Ítem no encontrado.'}, status=404)

    # Si todos los ítems del pedido están listos → cambiar estado pedido
    item = RestPedidoDet.objects.select_related('pedido').get(id=item_id)
    pedido = item.pedido
    hay_pendientes = pedido.items.filter(
        estado_item__in=['enviado', 'en_preparacion', 'pendiente']
    ).exists()
    if not hay_pendientes and pedido.estado in ('enviado',):
        pedido.estado = 'listo'
        pedido.save(update_fields=['estado'])

    return Response({'status': 'success', 'mensaje': f'Ítem marcado como {estado}.'})


@api_view(['POST'])
def MarcarListoPedido(request):
    """Cocina marca todos los ítems de un pedido como listos."""
    pedido_id = request.data.get('pedido_id')
    RestPedidoDet.objects.filter(
        pedido_id=pedido_id,
        estado_item__in=['enviado', 'en_preparacion'],
    ).update(estado_item='listo')

    RestPedido.objects.filter(id=pedido_id).update(estado='listo')
    return Response({'status': 'success', 'mensaje': 'Pedido marcado como listo.'})


# ── Historial ─────────────────────────────────────────────────────────────────

@api_view(['GET'])
def HistorialPedidos(request):
    """
    Historial del día (o rango) con resumen de ventas del restaurante.
    """
    desde = request.query_params.get('desde')
    hasta = request.query_params.get('hasta')

    qs = RestPedido.objects.select_related('mesa__sector').order_by('-fecha_apertura')
    if desde:
        qs = qs.filter(fecha_apertura__date__gte=desde)
    if hasta:
        qs = qs.filter(fecha_apertura__date__lte=hasta)

    data = [{
        'id':            p.id,
        'mesa':          p.mesa.numero,
        'sector':        p.mesa.sector.nombre,
        'estado':        p.estado,
        'comensales':    p.comensales,
        'mozo':          p.mozo_nombre,
        'total':         float(p.total),
        'movim_venta':   p.movim_venta,
        'fecha_apertura':p.fecha_apertura.strftime('%d/%m %H:%M'),
        'fecha_cierre':  p.fecha_cierre.strftime('%d/%m %H:%M') if p.fecha_cierre else '',
    } for p in qs[:100]]

    total_facturado = sum(p['total'] for p in data if p['estado'] == 'facturado')
    return Response({
        'status': 'success',
        'data':   data,
        'resumen': {
            'total_pedidos':    len(data),
            'facturados':       sum(1 for p in data if p['estado'] == 'facturado'),
            'total_facturado':  total_facturado,
        },
    })


# ── ABM mesas (config) ────────────────────────────────────────────────────────

@api_view(['GET'])
def ObtenerCartaMenu(request):
    """
    Devuelve los artículos activos organizados por rubro,
    pensados para armar la carta del restaurante.
    """
    from ..models import ArticulosRubros

    rubros = ArticulosRubros.objects.all().order_by('nombre')
    carta  = []
    for r in rubros:
        arts = list(
            Articulos.objects.filter(
                rubro=r.codigo,
            ).exclude(estado=1).values(
                'cod_art', 'nombre', 'precio_1', 'iva', 'artic_obs', 'stock'
            )[:200]
        )
        if arts:
            carta.append({
                'rubro_cod':  r.codigo,
                'rubro_nom':  r.nombre,
                'articulos':  arts,
            })

    # Artículos sin rubro
    sin_rubro = list(
        Articulos.objects.filter(rubro__isnull=True).exclude(estado=1)\
        .values('cod_art', 'nombre', 'precio_1', 'iva', 'artic_obs')[:100]
    )
    if sin_rubro:
        carta.append({'rubro_cod': '', 'rubro_nom': 'Sin categoría', 'articulos': sin_rubro})

    return Response({'status': 'success', 'data': carta})