"""
cta_cte.py — Cuenta corriente de clientes y recibos.

Migrado desde Ven_Recibos.cs (legacy C#).

Flujo del recibo (barButtonItem2_ItemClick):
  1. SELECT cta_cte_cli WHERE saldo > 0 → lista facturas pendientes
  2. INSERT INTO recibos (movim, numero, cliente, fecha, importe, usuario)
  3. Por cada factura seleccionada:
       UPDATE cta_cte_cli SET saldo = saldo - pago  WHERE id = ?
       INSERT INTO cta_cte_cli  (movim, origen='COB', detalle='Cobro FA N°...', saldo=0...)
  4. Por cada medio de pago (EFE, CHE):
       INSERT INTO cheq_tarj_cli (movim, origen='CTA', tipo='EFE'|'CHE'...)
  5. UPDATE tipocomp_cli SET ultnro = ultnro + 1 WHERE cod_compro = 'RC'

Anulación (cmdAnulaRecibo_ItemClick):
  1. UPDATE recibos SET anulado = 'S' WHERE numero = ?
  2. Por cada fila RC en cta_cte_cli:
       UPDATE cta_cte_cli SET saldo = saldo + importeh  (restaura la factura original)
       UPDATE cta_cte_cli SET anulado = 'S'  (borra el movimiento del cobro)
  3. UPDATE cheq_tarj_cli SET anulado = 'S'  WHERE cod_comprob='RC' AND nro_comprob=?
"""

from decimal import Decimal

from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import (
    CtaCteCli, CajasDet, Recibos, CheqTarjCli, TipocompCli, Clientes,
)
from .ventas import _siguiente_movim, _registrar_en_bitacora


# ── Obtener deuda de un cliente ───────────────────────────────────────────────

@api_view(['GET'])
def ObtenerDeudaCliente(request):
    """
    Devuelve las facturas pendientes de cobro de un cliente.
    Replica cmdObtieneDeuda_Click de Ven_Recibos.cs.
    """
    cod_cli = request.query_params.get('cod_cli')
    if not cod_cli:
        return Response({"status": "error", "mensaje": "Falta cod_cli."}, status=400)

    try:
        movimientos = CtaCteCli.objects.filter(
            cod_cli=cod_cli,
            saldo__gt=0,
            anulado='N',
        ).values(
            'id', 'movim', 'origen', 'fecha', 'cod_comprob', 'nro_comprob',
            'detalle', 'imported', 'saldo', 'fec_vto',
        ).order_by('fecha')

        saldo_total = sum(float(m['saldo'] or 0) for m in movimientos)
        lista = list(movimientos)

        # Enriquecer nombre del cliente
        cliente = Clientes.objects.filter(cod_cli=cod_cli).first()
        nom_cliente = cliente.denominacion if cliente else ''

        return Response({
            "status": "success",
            "nom_cliente": nom_cliente,
            "saldo_total": saldo_total,
            "deudas": lista,
        })
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


# ── Emitir recibo ─────────────────────────────────────────────────────────────

@api_view(['POST'])
def EmitirRecibo(request):
    """
    Genera un recibo de cobro.

    Payload:
    {
      "cod_cli": 5,
      "cajero": 1,
      "usuario": "admin",
      "punto_venta": "0001",
      "importe_total": 5000.00,
      // Facturas que se están pagando (con su monto parcial o total)
      "deudas_seleccionadas": [
        { "id": 123, "cod_comprob": "EA", "nro_comprob": 50, "pago": 3000.00 },
        { "id": 124, "cod_comprob": "EA", "nro_comprob": 51, "pago": 2000.00 }
      ],
      // Medios de pago utilizados
      "medios_pago": [
        { "cod_pago": "EFE", "importe": 5000.00, "referencia": "", "numero": 0,
          "cod_pago_det": 0, "cod_cuota": 0, "fec_vto": null, "recargo": 0, "recargo_iva": 0 }
      ]
    }
    """
    data     = request.data
    cod_cli  = int(data.get('cod_cli', 0))
    cajero   = int(data.get('cajero', 1))
    usuario  = str(data.get('usuario', 'admin'))
    pto_vta  = str(data.get('punto_venta', '0001')).zfill(4)
    importe_total  = Decimal(str(data.get('importe_total', 0)))
    deudas_sel     = data.get('deudas_seleccionadas', [])
    medios_pago    = data.get('medios_pago', [])

    if cod_cli == 0:
        return Response({"status": "error", "mensaje": "Falta código de cliente."}, status=400)
    if importe_total <= 0:
        return Response({"status": "error", "mensaje": "El importe debe ser mayor a 0."}, status=400)
    if not deudas_sel:
        return Response({"status": "error", "mensaje": "Debe seleccionar al menos una factura a cobrar."}, status=400)

    try:
        with transaction.atomic():
            # Siguiente número de recibo (tipocomp_cli cod_compro='RC')
            config_rc = (
                TipocompCli.objects
                .select_for_update()
                .filter(cod_compro='RC')
                .first()
            )
            if not config_rc:
                raise ValueError("Configure el tipo de comprobante 'RC' (Recibo) en tipocomp_cli.")

            nro_recibo = config_rc.ultnro + 1
            config_rc.ultnro = nro_recibo
            config_rc.save(update_fields=['ultnro'])

            # movim único
            nuevo_movim = _siguiente_movim()
            _registrar_en_bitacora(nuevo_movim, cajero, pto_vta, usuario)

            # 1. INSERT recibos
            Recibos.objects.create(
                movim      = nuevo_movim,
                numero     = nro_recibo,
                punto_venta= int(pto_vta),
                cliente    = cod_cli,
                fecha      = timezone.now().date(),
                importe    = importe_total,
                usuario    = usuario,
                anulado    = 'N',
                procesado  = 0,
            )

            # 2. Por cada factura seleccionada: descuenta saldo + registra cobro en cta_cte
            for deuda in deudas_sel:
                id_cta   = int(deuda['id'])
                pago     = Decimal(str(deuda['pago']))
                comprob  = str(deuda.get('cod_comprob', ''))
                nro_comp = int(deuda.get('nro_comprob', 0))

                # UPDATE cta_cte_cli saldo = saldo - pago
                CtaCteCli.objects.filter(id=id_cta).update(
                    saldo=__import__('django.db.models', fromlist=['F']).F('saldo') - pago
                )

                # INSERT cta_cte_cli (origen='COB', saldo=0)
                CtaCteCli.objects.create(
                    movim              = nuevo_movim,
                    origen             = 'COB',
                    cod_cli_id         = cod_cli,
                    importeh           = pago,
                    fecha              = timezone.now(),
                    cod_comprob        = 'RC',
                    nro_comprob        = nro_recibo,
                    id_comprob         = config_rc.id_compro,
                    detalle            = f'Cobro {comprob} N° {nro_comp}',
                    saldo              = 0,
                    moneda             = 1,
                    anulado            = 'N',
                    procesado          = 0,
                    cajero             = cajero,
                    comprobante_pto_vta= pto_vta,
                    compro_r           = comprob,
                    nro_compro_r       = nro_comp,
                    usuario            = usuario,
                )

            # 3. Por cada medio de pago: INSERT cheq_tarj_cli (origen='CTA')
            for mp in medios_pago:
                cod_pago = str(mp.get('cod_pago', 'EFE'))
                if cod_pago in ('EFE', 'CHE', 'TAR', 'TCR', 'TRF'):
                    fec_vto = mp.get('fec_vto') or timezone.now()
                    CheqTarjCli.objects.create(
                        movim              = nuevo_movim,
                        origen             = 'CTA',
                        cod_cli            = cod_cli,
                        tipo               = cod_pago,
                        importe            = Decimal(str(mp.get('importe', 0))),
                        fecha_rece         = timezone.now(),
                        fecha_vto          = fec_vto,
                        cod_comprob        = 'RC',
                        nro_comprob        = nro_recibo,
                        id_comprob         = config_rc.id_compro,
                        estado             = 'Cobrado',
                        pendiente          = 'N',
                        usuario            = usuario,
                        cajero             = cajero,
                        cod_entidad        = int(mp.get('cod_pago_det', 0)),
                        observac_1         = str(mp.get('referencia', '')),
                        comprobante_pto_vta= pto_vta,
                        numero             = int(mp.get('numero', 0)),
                        cod_cuota          = int(mp.get('cod_cuota', 0)),
                        recargo            = Decimal(str(mp.get('recargo', 0))),
                        recargo_iva        = Decimal(str(mp.get('recargo_iva', 0))),
                        procesado          = 0,
                    )

                    # Ingreso en arqueo de caja
                    CajasDet.objects.create(
                        nro_caja     = cajero,
                        tipo         = cod_pago,
                        forma        = 'Cobranza CtaCte',
                        nombre       = f'RC N° {nro_recibo}',
                        importe_cajero = Decimal(str(mp.get('importe', 0))),
                        importe_real   = Decimal(str(mp.get('importe', 0))),
                        procesado    = 0,
                    )

        return Response({
            "status":     "success",
            "mensaje":    f"Recibo N° {nro_recibo} generado correctamente.",
            "nro_recibo": nro_recibo,
            "movim":      nuevo_movim,
        }, status=201)

    except ValueError as e:
        return Response({"status": "error", "mensaje": str(e)}, status=400)
    except Exception as e:
        return Response({"status": "error", "mensaje": f"Error interno: {str(e)}"}, status=500)


# ── Anular recibo ─────────────────────────────────────────────────────────────

@api_view(['POST'])
def AnularRecibo(request):
    """
    Anula un recibo por número.
    Replica cmdAnulaRecibo_ItemClick de Ven_Recibos.cs.
    """
    nro_recibo = int(request.data.get('nro_recibo', 0))
    if nro_recibo <= 0:
        return Response({"status": "error", "mensaje": "Ingrese un número de recibo válido."}, status=400)

    try:
        with transaction.atomic():
            recibo = Recibos.objects.select_for_update().filter(numero=nro_recibo).first()
            if not recibo:
                return Response({"status": "error", "mensaje": "Recibo no encontrado."}, status=404)
            if recibo.anulado == 'S':
                return Response({"status": "error", "mensaje": "Este recibo ya fue anulado."}, status=400)

            # Restaurar saldo en las facturas originales y marcar movimientos RC como anulados
            cobros = list(CtaCteCli.objects.select_for_update().filter(
                cod_comprob='RC',
                nro_comprob=nro_recibo,
            ))
            for cobro in cobros:
                # Restaura el saldo en la factura original
                CtaCteCli.objects.filter(
                    cod_comprob=cobro.compro_r,
                    nro_comprob=cobro.nro_compro_r,
                    cod_cli=cobro.cod_cli_id,
                    anulado='N',
                ).update(
                    saldo=__import__('django.db.models', fromlist=['F']).F('saldo') + cobro.importeh
                )

            # Marca todos los movimientos RC de este recibo como anulados
            CtaCteCli.objects.filter(
                cod_comprob='RC',
                nro_comprob=nro_recibo,
            ).update(anulado='S')

            # Marca cheq_tarj_cli
            CheqTarjCli.objects.filter(
                cod_comprob='RC',
                nro_comprob=nro_recibo,
            ).update(anulado='S')

            # Anula el recibo
            recibo.anulado = 'S'
            recibo.save(update_fields=['anulado'])

        return Response({
            "status":  "success",
            "mensaje": f"Recibo N° {nro_recibo} anulado. Saldo restaurado en cta. cte.",
        })
    except Exception as e:
        return Response({"status": "error", "mensaje": f"Error al anular: {str(e)}"}, status=500)


# ── Resumen clásico (ya existía) ──────────────────────────────────────────────

@api_view(['GET'])
def ResumenCtaCteCliente(request):
    """Saldo total y comprobantes adeudados de un cliente."""
    cod_cli = request.query_params.get('cod_cli')
    if not cod_cli:
        return Response({"status": "error", "mensaje": "Debe indicar el código de cliente."}, status=400)

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

        return Response({
            "status": "success",
            "saldo_total": saldo_total,
            "movimientos": list(movimientos),
        })
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['POST'])
def InsertarReciboCtaCte(request):
    """
    Cobro rápido FIFO (sin selección de facturas).
    Redirige al nuevo EmitirRecibo si el cliente tiene deuda detallada.
    Mantiene compatibilidad con el frontend anterior.
    """
    data        = request.data
    cod_cli     = data.get('cod_cli')
    importe_pago= Decimal(str(data.get('importe_pago', 0)))
    cajero      = data.get('cajero', 1)
    nro_caja    = data.get('nro_caja', 1)
    usuario     = data.get('usuario', 'admin')

    if importe_pago <= 0:
        return Response({"status": "error", "mensaje": "El importe debe ser mayor a 0."}, status=400)

    try:
        with transaction.atomic():
            deudas = CtaCteCli.objects.select_for_update().filter(
                cod_cli=cod_cli, saldo__gt=0, anulado='N',
            ).order_by('fecha')

            pago_restante = importe_pago
            deudas_sel = []
            for deuda in deudas:
                if pago_restante <= 0:
                    break
                saldo_actual = Decimal(str(deuda.saldo))
                pago_ahora   = min(pago_restante, saldo_actual)
                deuda.saldo  = saldo_actual - pago_ahora
                deuda.save(update_fields=['saldo'])
                deudas_sel.append({
                    'id':          deuda.id,
                    'cod_comprob': deuda.cod_comprob,
                    'nro_comprob': deuda.nro_comprob,
                    'pago':        pago_ahora,
                })
                pago_restante -= pago_ahora

            # Recibo mínimo
            config_rc = TipocompCli.objects.select_for_update().filter(cod_compro='RC').first()
            nro_recibo = (config_rc.ultnro + 1) if config_rc else 1
            if config_rc:
                config_rc.ultnro = nro_recibo
                config_rc.save(update_fields=['ultnro'])

            nuevo_movim = _siguiente_movim()

            Recibos.objects.create(
                movim=nuevo_movim, numero=nro_recibo,
                punto_venta=1, cliente=cod_cli,
                fecha=timezone.now().date(), importe=importe_pago,
                usuario=usuario, anulado='N', procesado=0,
            )
            CtaCteCli.objects.create(
                movim=nuevo_movim, origen='RE', cod_cli_id=cod_cli,
                fecha=timezone.now(), id_comprob=2, cod_comprob='RC',
                nro_comprob=nro_recibo, detalle='Cobro de Cta. Cte.',
                imported=importe_pago, saldo=0, moneda=1,
                anulado='N', procesado=0, nro_caja=nro_caja, cajero=cajero,
            )
            CajasDet.objects.create(
                nro_caja=nro_caja, tipo='RE', forma='EFE',
                nombre='Cobranza Cta Cte',
                importe_cajero=importe_pago, importe_real=importe_pago, procesado=0,
            )

        return Response({"status": "success", "mensaje": f"Se cobraron ${importe_pago} correctamente."})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)