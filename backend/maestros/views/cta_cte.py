from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import CtaCteCli, CajasDet


@api_view(['GET'])
def ResumenCtaCteCliente(request):
    """Saldo total y comprobantes adeudados de un cliente."""
    cod_cli = request.query_params.get('cod_cli')

    if not cod_cli:
        return Response(
            {"status": "error", "mensaje": "Debe indicar el código de cliente."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        movimientos = CtaCteCli.objects.filter(
            cod_cli=cod_cli,
            saldo__gt=0,
            anulado='N',
        ).values(
            'movim', 'origen', 'fecha', 'cod_comprob', 'nro_comprob',
            'detalle', 'imported', 'saldo', 'fec_vto',
        ).order_by('fecha')

        saldo_total = sum(float(m['saldo'] or 0) for m in movimientos)

        return Response(
            {"status": "success", "saldo_total": saldo_total, "movimientos": list(movimientos)},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def InsertarReciboCtaCte(request):
    """Registra cobro de deuda en cta. cte. con imputación FIFO."""
    data = request.data
    cod_cli = data.get('cod_cli')
    importe_pago = float(data.get('importe_pago', 0))
    cajero = data.get('cajero', 1)
    nro_caja = data.get('nro_caja', 1)

    if importe_pago <= 0:
        return Response(
            {"status": "error", "mensaje": "El importe debe ser mayor a 0."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with transaction.atomic():
            # Imputa FIFO: del comprobante más viejo al más nuevo
            deudas = CtaCteCli.objects.select_for_update().filter(
                cod_cli=cod_cli,
                saldo__gt=0,
                anulado='N',
            ).order_by('fecha')

            pago_restante = importe_pago
            for deuda in deudas:
                if pago_restante <= 0:
                    break
                saldo_actual = float(deuda.saldo)
                if pago_restante >= saldo_actual:
                    pago_restante -= saldo_actual
                    deuda.saldo = 0
                else:
                    deuda.saldo = saldo_actual - pago_restante
                    pago_restante = 0
                deuda.save(update_fields=['saldo'])

            # Nuevo movimiento de tipo recibo
            ultimo = CtaCteCli.objects.select_for_update().aggregate(Max('movim'))
            nuevo_movim = (ultimo['movim__max'] or 0) + 1

            CtaCteCli.objects.create(
                movim=nuevo_movim,
                origen='RE',
                cod_cli_id=cod_cli,
                fecha=timezone.now(),
                id_comprob=2,
                cod_comprob='RE',
                nro_comprob=nuevo_movim,
                detalle='Cobro de Cta. Cte.',
                imported=importe_pago,
                saldo=0,
                moneda=1,
                anulado='N',
                procesado=0,
                nro_caja=nro_caja,
                cajero=cajero,
            )

            # Ingreso en caja
            CajasDet.objects.create(
                nro_caja=nro_caja,
                tipo='RE',
                forma='EFE',
                nombre='Cobranza Cta Cte',
                importe_cajero=importe_pago,
                importe_real=importe_pago,
                procesado=0,
            )

        return Response(
            {"status": "success", "mensaje": f"Se cobraron ${importe_pago} correctamente."},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
