"""
cotizaciones.py — Circuito de cotizaciones / presupuestos.

Replica la lógica de Ven_Cotiza.cs del legacy:
  - Listar cotizaciones
  - Crear / actualizar cotización
  - Convertir cotización a factura de venta (utilizar)
  - Anular cotización

Tablas involucradas: cotiza, cotiza_det
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Max, Q, F
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import (
    Cotiza, CotizaDet, Articulos, Clientes, TipocompCli,
    Ventas, VentasDet, CheqTarjCli, CtaCteCli, CajasDet,
)
from .ventas import _siguiente_movim, _registrar_en_bitacora


# ── Listar ────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def ListarCotizaciones(request):
    """
    Devuelve cotizaciones activas (no anuladas y no convertidas).
    Soporta filtros por cliente y rango de fechas.
    """
    desde  = request.query_params.get('desde')
    hasta  = request.query_params.get('hasta')
    cod_cli = request.query_params.get('cod_cli')
    solo_pendientes = request.query_params.get('pendientes', '0') == '1'

    try:
        qs = Cotiza.objects.all()

        if cod_cli:
            qs = qs.filter(cod_cli=cod_cli)
        if desde:
            qs = qs.filter(fecha_fact__date__gte=desde)
        if hasta:
            qs = qs.filter(fecha_fact__date__lte=hasta)
        if solo_pendientes:
            # utilizada=0 significa que aún no se convirtió a factura
            qs = qs.filter(anulado__isnull=True, utilizada=0)

        cotizaciones = qs.order_by('-movim').values(
            'movim', 'cod_comprob', 'comprobante_pto_vta', 'nro_comprob',
            'comprobante_letra', 'cod_cli', 'nom_cli',
            'fecha_fact', 'fecha_vto', 'neto', 'iva_1',
            'tot_general', 'anulado', 'utilizada',
            'observac', 'vendedor',
        )[:200]

        # Enriquecer con nombre del cliente
        result = list(cotizaciones)
        cod_clis = {r['cod_cli'] for r in result}
        clientes_dict = {
            c.cod_cli: c.denominacion
            for c in Clientes.objects.filter(cod_cli__in=cod_clis)
        }
        for r in result:
            r['denominacion'] = clientes_dict.get(r['cod_cli'], r.get('nom_cli', ''))

        return Response({"status": "success", "data": result})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['GET'])
def ObtenerCotizacion(request, movim):
    """Devuelve cabecera + ítems de una cotización."""
    try:
        cotiza = Cotiza.objects.filter(movim=movim).first()
        if not cotiza:
            return Response({"status": "error", "mensaje": "Cotización no encontrada."}, status=404)

        items = list(CotizaDet.objects.filter(movim=movim).values(
            'id', 'cod_articulo', 'cantidad', 'precio_unit', 'total',
            'descuento', 'detalle', 'p_iva', 'v_iva',
        ))

        cliente = Clientes.objects.filter(cod_cli=cotiza.cod_cli).first()

        return Response({
            "status": "success",
            "data": {
                "movim":          cotiza.movim,
                "cod_comprob":    cotiza.cod_comprob,
                "nro_comprob":    cotiza.nro_comprob,
                "comprobante_pto_vta": cotiza.comprobante_pto_vta,
                "comprobante_letra":  cotiza.comprobante_letra,
                "cod_cli":        cotiza.cod_cli,
                "nom_cli":        cliente.denominacion if cliente else cotiza.nom_cli,
                "fecha_fact":     cotiza.fecha_fact,
                "fecha_vto":      cotiza.fecha_vto,
                "neto":           float(cotiza.neto  or 0),
                "iva_1":          float(cotiza.iva_1 or 0),
                "tot_general":    float(cotiza.tot_general or 0),
                "descuento":      float(cotiza.descuento or 0),
                "anulado":        cotiza.anulado,
                "utilizada":      cotiza.utilizada,
                "observac":       cotiza.observac,
                "vendedor":       cotiza.vendedor,
                "items":          items,
            },
        })
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


# ── Crear / guardar ───────────────────────────────────────────────────────────

@api_view(['POST'])
def GuardarCotizacion(request):
    """
    Crea o actualiza una cotización.

    Payload:
    {
      "movim": null,          // null = nueva, número = editar
      "cod_cli": 5,
      "nom_cli": "Empresa SA",
      "fecha_fact": "2026-04-26T00:00:00",
      "observac": "",
      "cajero": 1,
      "usuario": "admin",
      "items": [
        {
          "cod_articulo": "ART001",
          "descripcion": "...",
          "cantidad": 2,
          "precio_unit": 1000.00,
          "total": 2000.00,
          "p_iva": 21,
          "v_iva": 347.11,
          "descuento": 0
        }
      ]
    }
    """
    data = request.data
    movim_existente = data.get('movim')

    try:
        with transaction.atomic():
            # Datos del comprobante PR (presupuesto) desde tipocomp_cli
            config = (
                TipocompCli.objects
                .select_for_update()
                .filter(cod_compro='PR')
                .first()
            )
            if not config:
                return Response({
                    "status": "error",
                    "mensaje": "Configure el tipo 'PR' (Presupuesto) en tipocomp_cli.",
                }, status=400)

            items = data.get('items', [])
            if not items:
                return Response({"status": "error", "mensaje": "Agregue al menos un artículo."}, status=400)

            neto_total = sum(
                Decimal(str(i.get('precio_unit', 0))) * Decimal(str(i.get('cantidad', 0)))
                for i in items
            )
            iva_total = sum(Decimal(str(i.get('v_iva', 0))) for i in items)
            tot_general = neto_total + iva_total

            if movim_existente:
                # Edición: actualizar cabecera y reemplazar ítems
                cotiza = Cotiza.objects.filter(movim=movim_existente).first()
                if not cotiza:
                    return Response({"status": "error", "mensaje": "Cotización no encontrada."}, status=404)
                if cotiza.utilizada == 1:
                    return Response({"status": "error", "mensaje": "No se puede editar una cotización ya utilizada."}, status=400)
                if cotiza.anulado == 'S':
                    return Response({"status": "error", "mensaje": "No se puede editar una cotización anulada."}, status=400)

                nuevo_movim = movim_existente
                CotizaDet.objects.filter(movim=nuevo_movim).delete()
            else:
                # Nueva: obtener movim y número
                config.ultnro += 1
                config.save(update_fields=['ultnro'])

                nuevo_movim = _siguiente_movim()
                cajero  = int(data.get('cajero', 1))
                usuario = str(data.get('usuario', 'admin'))
                _registrar_en_bitacora(nuevo_movim, cajero, '0001', usuario)

                # Calcular vencimiento según parámetro limitevalidezcotizaciones
                from ..models import Parametros
                param = Parametros.objects.first()
                dias_validez = getattr(param, 'limitevalidezcotizaciones', 30) or 30
                from datetime import timedelta
                fecha_vto = timezone.now() + timedelta(days=int(dias_validez))

                cotiza = Cotiza(
                    movim              = nuevo_movim,
                    id_comprob         = config.id_compro,
                    cod_comprob        = 'PR',
                    nro_comprob        = config.ultnro,
                    comprobante_pto_vta= '0001',
                    comprobante_letra  = 'X',
                    comprobante_tipo   = 'PR',
                    cod_cli            = int(data.get('cod_cli', 1)),
                    nom_cli            = str(data.get('nom_cli', ''))[:100],
                    fecha_fact         = data.get('fecha_fact', timezone.now()),
                    fecha_vto          = fecha_vto,
                    vendedor           = int(data.get('vendedor', 1)),
                    cajero             = int(data.get('cajero', 1)),
                    nro_caja           = int(data.get('nro_caja', 1)),
                    moneda             = 1,
                    utilizada          = 0,
                    procesado          = 0,
                    usuario            = str(data.get('usuario', 'admin')),
                    fecha_mod          = timezone.now(),
                )

            # Actualizar campos de totales en la cabecera
            cotiza.neto        = neto_total
            cotiza.iva_1       = iva_total
            cotiza.exento      = Decimal('0.00')
            cotiza.total       = tot_general
            cotiza.tot_general = tot_general
            cotiza.descuento   = Decimal('0.00')
            cotiza.observac    = str(data.get('observac', ''))[:50]
            cotiza.fecha_mod   = timezone.now()
            cotiza.save()

            # Guardar ítems
            for item in items:
                precio = Decimal(str(item.get('precio_unit', 0)))
                cant   = Decimal(str(item.get('cantidad', 0)))
                CotizaDet.objects.create(
                    movim               = nuevo_movim,
                    id_comprob          = cotiza.id_comprob,
                    cod_comprob         = 'PR',
                    nro_comprob         = cotiza.nro_comprob,
                    cod_articulo        = item['cod_articulo'],
                    cantidad            = cant,
                    precio_unit         = precio,
                    precio_unit_base    = precio,
                    total               = Decimal(str(item.get('total', precio * cant))),
                    descuento           = Decimal(str(item.get('descuento', 0))),
                    detalle             = str(item.get('descripcion', ''))[:45],
                    p_iva               = Decimal(str(item.get('p_iva', 21))),
                    v_iva               = Decimal(str(item.get('v_iva', 0))),
                    comprobante_pto_vta = cotiza.comprobante_pto_vta,
                    comprobante_tipo    = 'PR',
                    comprobante_letra   = 'X',
                    procesado           = 0,
                )

        return Response({
            "status":    "success",
            "mensaje":   f"Cotización N° {cotiza.nro_comprob} guardada.",
            "movim":     nuevo_movim,
            "nro":       cotiza.nro_comprob,
        }, status=201 if not movim_existente else 200)

    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


# ── Anular ────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def AnularCotizacion(request):
    """Anula una cotización marcándola como anulado='S'."""
    movim = request.data.get('movim')
    try:
        with transaction.atomic():
            cotiza = Cotiza.objects.select_for_update().filter(movim=movim).first()
            if not cotiza:
                return Response({"status": "error", "mensaje": "Cotización no encontrada."}, status=404)
            if cotiza.utilizada == 1:
                return Response({"status": "error", "mensaje": "No se puede anular: ya fue convertida a factura."}, status=400)
            if cotiza.anulado == 'S':
                return Response({"status": "error", "mensaje": "Ya está anulada."}, status=400)

            cotiza.anulado = 'S'
            cotiza.save(update_fields=['anulado'])

        return Response({"status": "success", "mensaje": f"Cotización N° {cotiza.nro_comprob} anulada."})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


# ── Convertir a Factura ────────────────────────────────────────────────────────

@api_view(['POST'])
def UtilizarCotizacion(request):
    """
    Convierte una cotización en un comprobante de venta real.
    Recibe el movim de la cotización + el tipo de comprobante destino.

    Payload:
    {
      "movim": 123,
      "tipo_comprobante": "EA",
      "cajero": 1,
      "nro_caja": 1,
      "usuario": "admin",
      "medio_pago": "EFE"
    }
    """
    movim_cotiza   = request.data.get('movim')
    tipo_comprob   = str(request.data.get('tipo_comprobante', 'EA'))[:2]
    cajero         = int(request.data.get('cajero', 1))
    nro_caja       = int(request.data.get('nro_caja', 1))
    usuario        = str(request.data.get('usuario', 'admin'))
    medio_pago     = str(request.data.get('medio_pago', 'EFE'))

    try:
        with transaction.atomic():
            cotiza = Cotiza.objects.select_for_update().filter(movim=movim_cotiza).first()
            if not cotiza:
                return Response({"status": "error", "mensaje": "Cotización no encontrada."}, status=404)
            if cotiza.utilizada == 1:
                return Response({"status": "error", "mensaje": "Esta cotización ya fue convertida a factura."}, status=400)
            if cotiza.anulado == 'S':
                return Response({"status": "error", "mensaje": "No se puede usar una cotización anulada."}, status=400)

            config_vta = (
                TipocompCli.objects
                .select_for_update()
                .filter(cod_compro=tipo_comprob)
                .first()
            )
            if not config_vta:
                return Response({
                    "status": "error",
                    "mensaje": f"Configure el tipo '{tipo_comprob}' en tipocomp_cli.",
                }, status=400)

            nro_comprob_vta = config_vta.ultnro + 1
            config_vta.ultnro = nro_comprob_vta
            config_vta.save(update_fields=['ultnro'])

            nuevo_movim = _siguiente_movim()
            _registrar_en_bitacora(nuevo_movim, cajero, cotiza.comprobante_pto_vta or '0001', usuario)

            # Crear la venta
            venta = Ventas.objects.create(
                movim               = nuevo_movim,
                id_comprob          = config_vta.id_compro,
                cod_comprob         = tipo_comprob,
                nro_comprob         = nro_comprob_vta,
                cod_cli             = cotiza.cod_cli,
                fecha_fact          = timezone.now().date(),
                fecha_vto           = timezone.now(),
                neto                = cotiza.neto,
                iva_1               = cotiza.iva_1,
                exento              = cotiza.exento or 0,
                total               = cotiza.total,
                tot_general         = cotiza.tot_general,
                descuento           = cotiza.descuento or 0,
                vendedor            = cotiza.vendedor,
                cajero              = cajero,
                nro_caja            = nro_caja,
                moneda              = cotiza.moneda or 1,
                comprobante_pto_vta = cotiza.comprobante_pto_vta or '0001',
                comprobante_tipo    = tipo_comprob,
                comprobante_letra   = cotiza.comprobante_letra or 'X',
                cond_venta          = '1',
                observac            = f"Cotiz. N° {cotiza.nro_comprob}",
                anulado             = 'N',
                procesado           = 0,
                fecha_mod           = timezone.now(),
                usuario             = usuario,
            )

            # Copiar ítems y descontar stock
            for item in CotizaDet.objects.filter(movim=movim_cotiza):
                VentasDet.objects.create(
                    movim               = nuevo_movim,
                    id_comprob          = config_vta.id_compro,
                    cod_comprob         = tipo_comprob,
                    nro_comprob         = nro_comprob_vta,
                    cod_articulo        = item.cod_articulo,
                    cantidad            = item.cantidad,
                    precio_unit         = item.precio_unit,
                    precio_unit_base    = item.precio_unit_base or item.precio_unit,
                    total               = item.total,
                    descuento           = item.descuento or 0,
                    detalle             = item.detalle,
                    p_iva               = item.p_iva,
                    v_iva               = item.v_iva,
                    comprobante_pto_vta = venta.comprobante_pto_vta,
                    comprobante_tipo    = tipo_comprob,
                    comprobante_letra   = venta.comprobante_letra,
                    procesado           = 0,
                )
                Articulos.objects.filter(cod_art=item.cod_articulo).update(
                    stock=F('stock') - item.cantidad
                )

            # Registrar medio de pago
            if medio_pago != 'CTA':
                CheqTarjCli.objects.create(
                    movim               = nuevo_movim,
                    origen              = 'VTA',
                    cod_cli             = cotiza.cod_cli,
                    tipo                = medio_pago,
                    importe             = cotiza.tot_general,
                    fecha_rece          = timezone.now(),
                    cod_comprob         = tipo_comprob,
                    nro_comprob         = nro_comprob_vta,
                    id_comprob          = config_vta.id_compro,
                    estado              = 'Cobrado',
                    pendiente           = 'N',
                    usuario             = usuario,
                    cajero              = cajero,
                    nro_caja            = nro_caja,
                    comprobante_pto_vta = venta.comprobante_pto_vta,
                    comprobante_tipo    = tipo_comprob,
                    comprobante_letra   = venta.comprobante_letra,
                    procesado           = 0,
                )
                CajasDet.objects.create(
                    nro_caja     = nro_caja,
                    tipo         = 'VTA',
                    forma        = medio_pago,
                    nombre       = f"Cotiz→Venta {tipo_comprob} N° {nro_comprob_vta}",
                    importe_cajero = cotiza.tot_general,
                    importe_real   = cotiza.tot_general,
                    procesado    = 0,
                )

            # Marcar cotización como utilizada
            Cotiza.objects.filter(movim=movim_cotiza).update(utilizada=1)

        return Response({
            "status":       "success",
            "mensaje":      f"Cotización convertida a {tipo_comprob} N° {nro_comprob_vta}.",
            "movim_venta":  nuevo_movim,
            "nro_venta":    nro_comprob_vta,
        })

    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)