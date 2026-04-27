"""
informes.py — Informes de ventas, compras, stock y cuenta corriente.
"""

from django.db.models import (
    Sum, Count, F, ExpressionWrapper, DecimalField,
    Subquery, OuterRef, Q,
)
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import Ventas, VentasDet, Cajas, Articulos, Compras, ComprasDet, CtaCteCli, Clientes
from .utils import aplicar_rango_fechas


# ── Ventas ────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def InformeTotalesCondicion(request):
    try:
        qs = aplicar_rango_fechas(request, Ventas.objects.all(), 'fecha_fact')
        reporte = (
            qs.values('cond_venta')
            .annotate(cantidad_operaciones=Count('movim'), total_pesos=Sum('total'))
            .order_by('-total_pesos')
        )
        return Response({"status": "success", "data": list(reporte)})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['GET'])
def InformeTotalesVendedor(request):
    try:
        qs = aplicar_rango_fechas(request, Ventas.objects.all(), 'fecha_fact')
        reporte = (
            qs.values('vendedor')
            .annotate(cantidad_operaciones=Count('movim'), total_pesos=Sum('total'))
            .order_by('-total_pesos')
        )
        return Response({"status": "success", "data": list(reporte)})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['GET'])
def InformeLibroIVAVentas(request):
    try:
        qs = aplicar_rango_fechas(request, Ventas.objects.all(), 'fecha_fact')
        comprobantes = qs.values(
            'fecha_fact', 'cod_comprob', 'comprobante_pto_vta', 'nro_comprob',
            'cod_cli', 'tot_general', 'neto', 'iva_1', 'exento',
        ).order_by('fecha_fact', 'nro_comprob')
        totales = qs.aggregate(
            suma_neto=Sum('neto'), suma_iva=Sum('iva_1'),
            suma_exento=Sum('exento'), suma_total=Sum('tot_general'),
        )
        return Response({"status": "success", "totales": totales, "comprobantes": list(comprobantes)})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['GET'])
def InformeRentabilidadArticulos(request):
    try:
        ventas_filtradas = aplicar_rango_fechas(request, Ventas.objects.all(), 'fecha_fact')
        movims_validos   = ventas_filtradas.values_list('movim', flat=True)
        ranking = (
            VentasDet.objects.filter(movim__in=movims_validos)
            .values('cod_articulo', 'detalle')
            .annotate(cantidad_vendida=Sum('cantidad'), total_facturado=Sum('total'))
            .order_by('-cantidad_vendida')[:100]
        )
        return Response({"status": "success", "data": list(ranking)})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['GET'])
def InformeHistorialCajas(request):
    try:
        qs = aplicar_rango_fechas(request, Cajas.objects.filter(estado=2), 'fecha_open')
        cajas_cerradas = qs.values(
            'id', 'cajero', 'fecha_open', 'fecha_close',
            'saldo_ini_billetes', 'ventas', 'otros_egresos',
            'saldo_final_billetes', 'dife_billetes',
        ).order_by('-id')[:50]
        return Response({"status": "success", "data": list(cajas_cerradas)})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


# ── Nuevos informes ───────────────────────────────────────────────────────────

@api_view(['GET'])
def InformeStockActual(request):
    """
    Stock actual de todos los artículos.
    Incluye: bajo mínimo, sin stock, con stock.
    Soporta filtro opcional por rubro y búsqueda.
    """
    try:
        qs = Articulos.objects.all()

        buscar = request.query_params.get('buscar', '')
        if buscar:
            qs = qs.filter(Q(nombre__icontains=buscar) | Q(cod_art__icontains=buscar))

        rubro = request.query_params.get('rubro', '')
        if rubro:
            qs = qs.filter(rubro=rubro)

        solo_criticos = request.query_params.get('solo_criticos', '')
        if solo_criticos == '1':
            qs = qs.filter(stock__lte=F('stock_min'))

        data = qs.values(
            'cod_art', 'nombre', 'rubro', 'stock', 'stock_min', 'stock_max',
            'costo_ult', 'precio_1', 'ult_compra', 'ult_venta', 'unidad',
        ).order_by('nombre')[:500]

        result    = list(data)
        total_art = len(result)
        sin_stock = sum(1 for a in result if (a['stock'] or 0) <= 0)
        criticos  = sum(1 for a in result if (a['stock'] or 0) <= (a['stock_min'] or 0) and (a['stock_min'] or 0) > 0)

        return Response({
            "status":    "success",
            "resumen":   {"total": total_art, "sin_stock": sin_stock, "criticos": criticos},
            "data":      result,
        })
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['GET'])
def InformeCtaCteClientes(request):
    """
    Saldo de cuenta corriente por cliente.
    Agrupa las facturas pendientes y muestra el total adeudado por cliente.
    """
    try:
        qs = CtaCteCli.objects.filter(saldo__gt=0, anulado='N')

        cod_cli = request.query_params.get('cod_cli', '')
        if cod_cli:
            qs = qs.filter(cod_cli=cod_cli)

        # Resumen por cliente
        resumen = (
            qs.values('cod_cli')
            .annotate(
                total_deuda    = Sum('saldo'),
                cant_facturas  = Count('id'),
            )
            .order_by('-total_deuda')[:200]
        )

        result = list(resumen)

        # Enriquecer con nombre del cliente
        cod_clis = [r['cod_cli'] for r in result]
        clientes_dict = {
            c.cod_cli: c.denominacion
            for c in Clientes.objects.filter(cod_cli__in=cod_clis)
        }
        for r in result:
            r['cod_cli_id']   = r.pop('cod_cli')  # evitar confusión con FK
            r['denominacion'] = clientes_dict.get(r['cod_cli_id'], '')

        total_cartera = sum(float(r['total_deuda'] or 0) for r in result)

        # Si pidieron detalle de un cliente específico
        detalle = []
        if cod_cli:
            detalle = list(
                qs.values(
                    'id', 'movim', 'fecha', 'cod_comprob', 'nro_comprob',
                    'detalle', 'imported', 'saldo', 'fec_vto',
                ).order_by('fecha')
            )

        return Response({
            "status":         "success",
            "total_cartera":  total_cartera,
            "clientes":       result,
            "detalle":        detalle,
        })
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['GET'])
def InformeMovimientosStock(request):
    """
    Historial de movimientos de stock: entradas (IS), salidas (SS), compras (FA/FB/FC).
    Filtra por período y/o tipo.
    """
    try:
        qs = Compras.objects.filter(
            cod_comprob__in=['IS', 'SS', 'FA', 'FB', 'FC', 'FX']
        ).exclude(anulado='S')

        qs = aplicar_rango_fechas(request, qs, 'fecha_comprob')

        tipo = request.query_params.get('tipo', '')
        if tipo:
            qs = qs.filter(cod_comprob=tipo)

        movimientos = qs.values(
            'movim', 'cod_comprob', 'nro_comprob', 'cod_prov',
            'fecha_comprob', 'observac', 'neto', 'usuario',
        ).order_by('-movim')[:200]

        result = list(movimientos)

        # Enriquecer con detalle de artículos (top 5 por movim)
        movim_ids = [m['movim'] for m in result]
        det_qs = (
            ComprasDet.objects
            .filter(movim__in=movim_ids)
            .values('movim', 'cod_articulo', 'nom_articulo', 'cantidad')
        )
        det_map: dict = {}
        for d in det_qs:
            det_map.setdefault(d['movim'], []).append(d)

        for m in result:
            m['items'] = det_map.get(m['movim'], [])

        return Response({"status": "success", "data": result})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['GET'])
def InformeEgresos(request):
    """
    Libro de egresos / compras.
    Filtra solo compras reales (FA/FB/FC/FX) por período.
    Totales: neto, IVA, retenciones, total general.
    """
    try:
        qs = Compras.objects.filter(
            cod_comprob__in=['FA', 'FB', 'FC', 'FX']
        ).exclude(anulado='S')

        qs = aplicar_rango_fechas(request, qs, 'fecha_comprob')

        comprobantes = qs.values(
            'movim', 'cod_comprob', 'comprobante_letra', 'comprobante_pto_vta',
            'nro_comprob', 'cod_prov', 'fecha_comprob',
            'neto', 'iva_1', 'total', 'tot_general',
            'ret_iva', 'ret_gan', 'ret_iibb', 'observac',
        ).order_by('fecha_comprob')

        totales = qs.aggregate(
            suma_neto    = Sum('neto'),
            suma_iva     = Sum('iva_1'),
            suma_total   = Sum('tot_general'),
            suma_ret_iva = Sum('ret_iva'),
            suma_ret_gan = Sum('ret_gan'),
            suma_ret_iibb= Sum('ret_iibb'),
        )

        result = list(comprobantes)

        # Enriquecer con nombre de proveedor
        from ..models import Proveedores
        prov_ids = {r['cod_prov'] for r in result}
        provs    = {p.cod_prov: p.nomfantasia for p in Proveedores.objects.filter(cod_prov__in=prov_ids)}
        for r in result:
            r['nom_proveedor'] = provs.get(r['cod_prov'], '')

        return Response({
            "status":        "success",
            "totales":       totales,
            "comprobantes":  result,
        })
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)