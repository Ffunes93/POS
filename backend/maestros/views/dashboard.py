"""
dashboard.py — Endpoint de KPIs para el panel de control principal.
GET /api/Dashboard/
"""
from decimal import Decimal
from datetime import date, timedelta

from django.db.models import Sum, Count, Q
from django.db import connection
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import (
    Ventas, VentasDet, Compras, CtaCteCli, Articulos,
    Cajas, CheqTarjCli,
)


@api_view(['GET'])
def ObtenerDashboard(request):
    """
    Devuelve los KPIs principales para el panel de inicio.
    Incluye: ventas del día, del mes, stock crítico, deuda cartera, cajas abiertas.
    """
    hoy       = date.today()
    ini_mes   = hoy.replace(day=1)
    ayer      = hoy - timedelta(days=1)

    try:
        # ── Ventas del día ────────────────────────────────────────────────────
        ventas_hoy_qs = Ventas.objects.filter(
            fecha_fact__date=hoy, anulado='N'
        )
        ventas_hoy = ventas_hoy_qs.aggregate(
            total=Sum('tot_general'), cantidad=Count('movim')
        )

        # ── Ventas del mes ────────────────────────────────────────────────────
        ventas_mes_qs = Ventas.objects.filter(
            fecha_fact__date__gte=ini_mes, anulado='N'
        )
        ventas_mes = ventas_mes_qs.aggregate(
            total=Sum('tot_general'), cantidad=Count('movim')
        )

        # ── Ventas de ayer (para comparar) ────────────────────────────────────
        ventas_ayer = Ventas.objects.filter(
            fecha_fact__date=ayer, anulado='N'
        ).aggregate(total=Sum('tot_general'))

        # ── Compras del mes ───────────────────────────────────────────────────
        compras_mes = Compras.objects.filter(
            fecha_comprob__date__gte=ini_mes,
            anulado__isnull=True,
            cod_comprob__in=['FA', 'FB', 'FC', 'FX'],
        ).aggregate(total=Sum('tot_general'), cantidad=Count('movim'))

        # ── Artículos con stock crítico (≤ stock_min) ─────────────────────────
        criticos = Articulos.objects.filter(
            stock__lte=0
        ).count()
        # Comparación entre campos requiere SQL raw
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM articulos WHERE stock <= stock_min AND stock_min > 0"
            )
            bajo_minimo = cursor.fetchone()[0]

        # ── Cartera CTA CTE clientes ───────────────────────────────────────────
        cartera = CtaCteCli.objects.filter(
            saldo__gt=0, anulado='N'
        ).aggregate(
            total_deuda=Sum('saldo'),
            cant_clientes=Count('cod_cli', distinct=True),
        )

        # ── Cajas abiertas ────────────────────────────────────────────────────
        cajas_abiertas = Cajas.objects.filter(estado=1).count()

        # ── Últimas 5 ventas del día ──────────────────────────────────────────
        ultimas_ventas = list(
            ventas_hoy_qs.order_by('-movim').values(
                'movim', 'cod_comprob', 'comprobante_pto_vta',
                'nro_comprob', 'fecha_fact', 'tot_general',
                'cod_cli', 'comprobante_letra',
            )[:5]
        )

        # ── Top 5 artículos vendidos hoy ─────────────────────────────────────
        movims_hoy = list(ventas_hoy_qs.values_list('movim', flat=True))
        top_articulos = list(
            VentasDet.objects.filter(movim__in=movims_hoy)
            .values('cod_articulo', 'detalle')
            .annotate(
                cant_vendida=Sum('cantidad'),
                total_venta=Sum('total'),
            )
            .order_by('-cant_vendida')[:5]
        )

        # ── Comparativo día anterior ──────────────────────────────────────────
        total_hoy  = float(ventas_hoy['total']  or 0)
        total_ayer = float(ventas_ayer['total']  or 0)
        variacion_pct = (
            round(((total_hoy - total_ayer) / total_ayer * 100), 1)
            if total_ayer > 0 else 0
        )

        return Response({
            "status": "success",
            "fecha_hoy": hoy.isoformat(),
            "ventas_hoy": {
                "total":      total_hoy,
                "cantidad":   ventas_hoy['cantidad'] or 0,
                "variacion_vs_ayer": variacion_pct,
                "total_ayer": total_ayer,
            },
            "ventas_mes": {
                "total":    float(ventas_mes['total']    or 0),
                "cantidad": ventas_mes['cantidad'] or 0,
            },
            "compras_mes": {
                "total":    float(compras_mes['total']    or 0),
                "cantidad": compras_mes['cantidad'] or 0,
            },
            "stock": {
                "sin_stock":   criticos,
                "bajo_minimo": bajo_minimo,
            },
            "cartera": {
                "total_deuda":   float(cartera['total_deuda']   or 0),
                "cant_clientes": cartera['cant_clientes'] or 0,
            },
            "cajas_abiertas": cajas_abiertas,
            "ultimas_ventas":  ultimas_ventas,
            "top_articulos":   top_articulos,
        })

    except Exception as e:
        return Response(
            {"status": "error", "mensaje": str(e)},
            status=500,
        )