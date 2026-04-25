from django.db.models import Sum, Count
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import Ventas, VentasDet, Cajas


@api_view(['GET'])
def InformeTotalesCondicion(request):
    """Ventas agrupadas por condición de venta (Contado, Cta. Cte., etc.)."""
    try:
        reporte = (
            Ventas.objects
            .values('cond_venta')
            .annotate(cantidad_operaciones=Count('movim'), total_pesos=Sum('total'))
            .order_by('-total_pesos')
        )
        return Response({"status": "success", "data": list(reporte)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def InformeTotalesVendedor(request):
    """Ventas agrupadas por vendedor."""
    try:
        reporte = (
            Ventas.objects
            .values('vendedor')
            .annotate(cantidad_operaciones=Count('movim'), total_pesos=Sum('total'))
            .order_by('-total_pesos')
        )
        return Response({"status": "success", "data": list(reporte)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def InformeLibroIVAVentas(request):
    """Libro IVA Ventas para un rango de fechas."""
    fecha_desde = request.query_params.get('desde')
    fecha_hasta = request.query_params.get('hasta')

    try:
        query = Ventas.objects.all()
        if fecha_desde and fecha_hasta:
            query = query.filter(fecha_fact__range=[fecha_desde, fecha_hasta])

        comprobantes = query.values(
            'fecha_fact', 'cod_comprob', 'comprobante_pto_vta', 'nro_comprob',
            'cod_cli', 'tot_general', 'neto', 'iva_1', 'exento',
        ).order_by('fecha_fact', 'nro_comprob')

        totales = query.aggregate(
            suma_neto=Sum('neto'),
            suma_iva=Sum('iva_1'),
            suma_exento=Sum('exento'),
            suma_total=Sum('tot_general'),
        )

        return Response(
            {"status": "success", "totales": totales, "comprobantes": list(comprobantes)},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def InformeRentabilidadArticulos(request):
    """Top 100 artículos más vendidos por cantidad."""
    try:
        ranking = (
            VentasDet.objects
            .values('cod_articulo', 'detalle')
            .annotate(cantidad_vendida=Sum('cantidad'), total_facturado=Sum('total'))
            .order_by('-cantidad_vendida')[:100]
        )
        return Response({"status": "success", "data": list(ranking)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def InformeHistorialCajas(request):
    """Historial de las últimas 50 cajas cerradas con sus diferencias de arqueo."""
    try:
        cajas_cerradas = (
            Cajas.objects
            .filter(estado=2)
            .values(
                'id', 'cajero', 'fecha_open', 'fecha_close',
                'saldo_ini_billetes', 'ventas', 'otros_egresos',
                'saldo_final_billetes', 'dife_billetes',
            )
            .order_by('-id')[:50]
        )
        return Response({"status": "success", "data": list(cajas_cerradas)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
