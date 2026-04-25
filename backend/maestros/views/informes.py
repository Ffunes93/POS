from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField, Subquery, OuterRef
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import Ventas, VentasDet, Cajas, Articulos
from .utils import aplicar_rango_fechas

@api_view(['GET'])
def InformeTotalesCondicion(request):
    """Ventas agrupadas por condición de venta con filtro de fecha."""
    try:
        queryset = Ventas.objects.all()
        # Aplicamos el filtro uniforme usando la utilidad
        queryset = aplicar_rango_fechas(request, queryset, 'fecha_fact')
        
        reporte = (
            queryset.values('cond_venta')
            .annotate(cantidad_operaciones=Count('movim'), total_pesos=Sum('total'))
            .order_by('-total_pesos')
        )
        return Response({"status": "success", "data": list(reporte)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def InformeTotalesVendedor(request):
    """Ventas agrupadas por vendedor con filtro de fecha."""
    try:
        queryset = Ventas.objects.all()
        queryset = aplicar_rango_fechas(request, queryset, 'fecha_fact')
        
        reporte = (
            queryset.values('vendedor')
            .annotate(cantidad_operaciones=Count('movim'), total_pesos=Sum('total'))
            .order_by('-total_pesos')
        )
        return Response({"status": "success", "data": list(reporte)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def InformeLibroIVAVentas(request):
    """Libro IVA Ventas estandarizado con la utilidad de fechas."""
    try:
        queryset = Ventas.objects.all()
        queryset = aplicar_rango_fechas(request, queryset, 'fecha_fact')

        comprobantes = queryset.values(
            'fecha_fact', 'cod_comprob', 'comprobante_pto_vta', 'nro_comprob',
            'cod_cli', 'tot_general', 'neto', 'iva_1', 'exento',
        ).order_by('fecha_fact', 'nro_comprob')

        totales = queryset.aggregate(
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
    """Top 100 artículos con filtro de fecha aplicado a la cabecera de la venta."""
    try:
        # 1. Filtramos primero la tabla cabecera (Ventas)
        ventas_filtradas = Ventas.objects.all()
        ventas_filtradas = aplicar_rango_fechas(request, ventas_filtradas, 'fecha_fact')
        
        # 2. Extraemos solo los IDs (movim) de esas ventas
        movims_validos = ventas_filtradas.values_list('movim', flat=True)

        # 3. Filtramos los detalles usando movim__in
        queryset = VentasDet.objects.filter(movim__in=movims_validos)
        
        ranking = (
            queryset.values('cod_articulo', 'detalle')
            .annotate(cantidad_vendida=Sum('cantidad'), total_facturado=Sum('total'))
            .order_by('-cantidad_vendida')[:100]
        )
        return Response({"status": "success", "data": list(ranking)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def InformeHistorialCajas(request):
    """Historial de cajas cerradas con filtro por fecha de apertura."""
    try:
        queryset = Cajas.objects.filter(estado=2)
        queryset = aplicar_rango_fechas(request, queryset, 'fecha_open')
        
        cajas_cerradas = (
            queryset.values(
                'id', 'cajero', 'fecha_open', 'fecha_close',
                'saldo_ini_billetes', 'ventas', 'otros_egresos',
                'saldo_final_billetes', 'dife_billetes',
            )
            .order_by('-id')[:50]
        )
        return Response({"status": "success", "data": list(cajas_cerradas)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def InformeMargenUtilidad(request):
    """Rentabilidad real con filtro de fechas."""
    try:
        ventas_filtradas = Ventas.objects.all()
        ventas_filtradas = aplicar_rango_fechas(request, ventas_filtradas, 'fecha_fact')
        movims_validos = ventas_filtradas.values_list('movim', flat=True)

        queryset = VentasDet.objects.filter(movim__in=movims_validos)
        
        reporte = (
            queryset.annotate(
                utilidad=ExpressionWrapper(
                    F('total') - (F('cantidad') * F('costo')), 
                    output_field=DecimalField()
                )
            )
            .values('cod_articulo', 'detalle')
            .annotate(
                total_vendido=Sum('total'),
                ganancia_neta=Sum('utilidad')
            )
            .order_by('-ganancia_neta')[:50]
        )
        return Response({"status": "success", "data": list(reporte)})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['GET'])
def InformeVentasPorRubro(request):
    """Agrupación por rubro usando subconsultas y filtro de fechas."""
    try:
        ventas_filtradas = Ventas.objects.all()
        ventas_filtradas = aplicar_rango_fechas(request, ventas_filtradas, 'fecha_fact')
        movims_validos = ventas_filtradas.values_list('movim', flat=True)

        queryset = VentasDet.objects.filter(movim__in=movims_validos)
        
        # Como cod_articulo es un CharField, usamos Subquery para buscar el rubro en la tabla Articulos
        rubro_sq = Articulos.objects.filter(cod_art=OuterRef('cod_articulo')).values('rubro')[:1]
        
        reporte = (
            queryset.annotate(rubro=Subquery(rubro_sq))
            .values('rubro')
            .annotate(total_rubro=Sum('total'))
            .order_by('-total_rubro')
        )
        return Response({"status": "success", "data": list(reporte)})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)
    
    
@api_view(['GET'])
def InformeReposicionCritica(request):
    """
    Artículos con stock bajo. 
    Nota: No se aplica filtro de fecha aquí por ser un estado de inventario actual.
    """
    try:
        criticos = (
            Articulos.objects
            .filter(stock__lte=F('stock_min'))
            .values('cod_art', 'nombre', 'stock', 'stock_min', 'codigo_proveedor')
            .order_by('stock')
        )
        return Response({"status": "success", "data": list(criticos)})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)