"""
cta_cte_prov.py — Cuenta corriente de proveedores y pagos.

Replica la lógica de Com_CtaCte.cs y Com_Pago.cs del legacy.
Tablas: cta_cte_prov, cheq_tarj_prov
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import CtaCteProv, CheqTarjProv, Proveedores


# ── Resumen de deuda por proveedor ────────────────────────────────────────────

@api_view(['GET'])
def ResumenCtaCteProveedores(request):
    """
    Devuelve el resumen de deuda por proveedor.
    Soporta filtro por proveedor específico.
    """
    cod_prov = request.query_params.get('cod_prov')

    try:
        qs = CtaCteProv.objects.filter(saldo__gt=0, anulado='N')
        if cod_prov:
            qs = qs.filter(cod_prov=cod_prov)

        resumen = (
            qs.values('cod_prov')
            .annotate(
                total_deuda   = Sum('saldo'),
                cant_facturas = Count('id'),
            )
            .order_by('-total_deuda')[:200]
        )

        result = list(resumen)

        # Enriquecer con nombre del proveedor
        prov_ids = [r['cod_prov'] for r in result]
        provs_dict = {
            p.cod_prov: p.nomfantasia
            for p in Proveedores.objects.filter(cod_prov__in=prov_ids)
        }
        for r in result:
            r['nomfantasia'] = provs_dict.get(r['cod_prov'], '')

        total_cartera = sum(float(r['total_deuda'] or 0) for r in result)

        # Detalle si se pidió un proveedor específico
        detalle = []
        if cod_prov:
            detalle = list(
                qs.values(
                    'id', 'movim', 'fecha', 'cod_comprob', 'nro_comprob',
                    'detalle', 'imported', 'saldo', 'fecha_oper',
                ).order_by('fecha')
            )

        return Response({
            "status":        "success",
            "total_cartera": total_cartera,
            "proveedores":   result,
            "detalle":       detalle,
        })
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['GET'])
def ObtenerDeudaProveedor(request):
    """Devuelve las facturas pendientes de pago de un proveedor."""
    cod_prov = request.query_params.get('cod_prov')
    if not cod_prov:
        return Response({"status": "error", "mensaje": "Falta cod_prov."}, status=400)

    try:
        facturas = list(
            CtaCteProv.objects.filter(
                cod_prov=cod_prov,
                saldo__gt=0,
                anulado='N',
            ).values(
                'id', 'movim', 'origen', 'fecha', 'cod_comprob', 'nro_comprob',
                'detalle', 'imported', 'saldo',
            ).order_by('fecha')
        )

        proveedor = Proveedores.objects.filter(cod_prov=cod_prov).first()
        saldo_total = sum(float(f['saldo'] or 0) for f in facturas)

        return Response({
            "status":      "success",
            "nom_proveedor": proveedor.nomfantasia if proveedor else '',
            "saldo_total":  saldo_total,
            "deudas":       facturas,
        })
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


# ── Registrar pago ────────────────────────────────────────────────────────────

@api_view(['POST'])
def RegistrarPagoProveedor(request):
    """
    Registra el pago de facturas de un proveedor.

    Payload:
    {
      "cod_prov": 5,
      "cajero": 1,
      "usuario": "admin",
      "importe_total": 5000.00,
      "deudas_seleccionadas": [
        { "id": 10, "cod_comprob": "FA", "nro_comprob": 12345, "pago": 3000.00 },
        { "id": 11, "cod_comprob": "FA", "nro_comprob": 12346, "pago": 2000.00 }
      ],
      "medios_pago": [
        {
          "tipo": "EFE",      // EFE | CHE | TRF
          "importe": 5000.00,
          "referencia": ""
        }
      ]
    }
    """
    data          = request.data
    cod_prov      = int(data.get('cod_prov', 0))
    cajero        = int(data.get('cajero', 1))
    usuario       = str(data.get('usuario', 'admin'))
    importe_total = Decimal(str(data.get('importe_total', 0)))
    deudas_sel    = data.get('deudas_seleccionadas', [])
    medios_pago   = data.get('medios_pago', [])

    if cod_prov == 0:
        return Response({"status": "error", "mensaje": "Falta código de proveedor."}, status=400)
    if importe_total <= 0:
        return Response({"status": "error", "mensaje": "El importe debe ser mayor a 0."}, status=400)
    if not deudas_sel:
        return Response({"status": "error", "mensaje": "Seleccione al menos una factura."}, status=400)

    try:
        with transaction.atomic():
            # Calcular nuevo movim (usamos Max de la tabla cta_cte_prov)
            max_movim = CtaCteProv.objects.aggregate(
                m=__import__('django.db.models', fromlist=['Max']).Max('movim')
            )['m'] or 0
            nuevo_movim = max_movim + 1

            # 1. Descontar saldo de cada factura seleccionada
            for deuda in deudas_sel:
                id_cta  = int(deuda['id'])
                pago    = Decimal(str(deuda['pago']))
                comprob = str(deuda.get('cod_comprob', ''))
                nro     = int(deuda.get('nro_comprob', 0))

                row = CtaCteProv.objects.select_for_update().filter(id=id_cta).first()
                if not row:
                    continue

                saldo_actual = Decimal(str(row.saldo))
                nuevo_saldo  = max(saldo_actual - pago, Decimal('0.00'))
                row.saldo    = nuevo_saldo
                row.save(update_fields=['saldo'])

                # Insertar movimiento de cobro (saldo = 0)
                CtaCteProv.objects.create(
                    movim           = nuevo_movim,
                    origen          = 'PAG',
                    cod_prov        = cod_prov,
                    fecha           = timezone.now(),
                    fecha_oper      = timezone.now(),
                    cod_comprob     = 'PA',
                    nro_comprob     = nuevo_movim,
                    id_comprob      = 0,
                    detalle         = f'Pago {comprob} N° {nro}',
                    imported        = pago,
                    importeh        = pago,
                    saldo           = Decimal('0.00'),
                    cobrado         = 0,
                    cobrado_tmp     = 0,
                    parcial         = Decimal('0.00'),
                    parcial_tmp     = Decimal('0.00'),
                    fec_mod         = timezone.now(),
                    fecha_mod       = timezone.now(),
                    moneda          = 1,
                    anulado         = 'N',
                    cuota           = 0,
                    nro_lote        = 0,
                    usuario         = usuario,
                    comprobante_tipo    = 'PA',
                    comprobante_letra   = '',
                    comprobante_pto_vta = '0001',
                    compro_r        = comprob,
                    nro_compro_r    = nro,
                )

            # 2. Registrar medios de pago en cheq_tarj_prov
            for mp in medios_pago:
                tipo_pago = str(mp.get('tipo', 'EFE'))
                importe_mp = Decimal(str(mp.get('importe', 0)))
                referencia = str(mp.get('referencia', ''))

                CheqTarjProv.objects.create(
                    movim               = nuevo_movim,
                    origen              = 'PAG',
                    cod_prov            = cod_prov,
                    tipo                = tipo_pago,
                    importe             = importe_mp,
                    fecha_rece          = timezone.now(),
                    fecha_vto           = timezone.now(),
                    cod_comprob         = 'PA',
                    nro_comprob         = nuevo_movim,
                    id_comprob          = 0,
                    observac_1          = referencia,
                    moneda              = 1,
                    estado              = 'Pagado',
                    pendiente           = 'N',
                    usuario             = usuario,
                    cajero              = cajero,
                    comprobante_tipo    = 'PA',
                    comprobante_letra   = '',
                    comprobante_pto_vta = '0001',
                    anulado             = 'N',
                )

        proveedor = Proveedores.objects.filter(cod_prov=cod_prov).first()
        nom = proveedor.nomfantasia if proveedor else f'#{cod_prov}'

        return Response({
            "status":    "success",
            "mensaje":   f"Pago de ${float(importe_total):.2f} a {nom} registrado correctamente.",
            "movim":     nuevo_movim,
        }, status=201)

    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


# ── Historial de pagos ────────────────────────────────────────────────────────

@api_view(['GET'])
def HistorialPagosProveedor(request):
    """
    Devuelve el historial completo de movimientos de un proveedor en CTA CTE.
    """
    cod_prov = request.query_params.get('cod_prov')
    desde    = request.query_params.get('desde')
    hasta    = request.query_params.get('hasta')

    if not cod_prov:
        return Response({"status": "error", "mensaje": "Falta cod_prov."}, status=400)

    try:
        qs = CtaCteProv.objects.filter(cod_prov=cod_prov)
        if desde:
            qs = qs.filter(fecha__date__gte=desde)
        if hasta:
            qs = qs.filter(fecha__date__lte=hasta)

        movimientos = list(
            qs.values(
                'id', 'movim', 'origen', 'fecha', 'cod_comprob', 'nro_comprob',
                'detalle', 'imported', 'saldo', 'anulado',
            ).order_by('-fecha')[:200]
        )

        proveedor = Proveedores.objects.filter(cod_prov=cod_prov).first()

        return Response({
            "status":        "success",
            "nom_proveedor": proveedor.nomfantasia if proveedor else '',
            "movimientos":   movimientos,
        })
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)