"""
compras.py — Circuito de compras migrado desde Compras.cs y Com_Anula.cs (legacy C#).

Flujo del legacy (barButtonItemSAVE_ItemClick, Compras.cs):
  1. INSERT INTO compras   (cabecera con movim=bitacora, campos completos)
  2. INSERT INTO compras_det + UPDATE articulos (stock + costo_ult)  por cada ítem
  3. Si condición == 'CONTADO' → INSERT INTO cheq_tarj_prov (origen='SAC', tipo='EFE')
  4. Si condición == 'CTA.CTE.' → INSERT INTO cta_cte_prov  (origen='CMP', saldo=total)

Anulación (Com_Anula.cs):
  1. UPDATE compras SET anulado='S'
  2. Por cada ítem en compras_det → UPDATE articulos stock=stock-cantidad (revierte)
"""

from decimal import Decimal

from django.db import transaction, connection
from django.db.models import Max, F
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import (
    Compras, ComprasDet, Proveedores, Articulos,
    CheqTarjProv, CtaCteProv,
)
from .ventas import _siguiente_movim, _registrar_en_bitacora


# ── Helpers ───────────────────────────────────────────────────────────────────

def _verificar_existe_egreso(tipo_comprob: str, nro_comprob: int, cod_prov: int) -> bool:
    """Replica PuntoVentaClases.VerificarExisteEgreso del legacy."""
    return Compras.objects.filter(
        cod_comprob=tipo_comprob,
        nro_comprob=nro_comprob,
        cod_prov=cod_prov,
        anulado__isnull=True,
    ).exists()


# ── Proveedores ───────────────────────────────────────────────────────────────

@api_view(['GET'])
def ListarProveedores(request):
    busqueda = request.query_params.get('buscar', '')
    from django.db.models import Q
    proveedores = Proveedores.objects.all()

    if busqueda:
        proveedores = proveedores.filter(
            Q(nomfantasia__icontains=busqueda) | Q(nro_cuit__icontains=busqueda)
        )

    data = proveedores.values(
        'cod_prov', 'nomfantasia', 'nro_cuit', 'domicilio', 'telefono',
        'mail', 'cond_iva', 'estado',
    )[:100]

    return Response({"status": "success", "data": list(data)}, status=status.HTTP_200_OK)


@api_view(['POST'])
def GuardarProveedor(request):
    from django.db.models import Max
    data = request.data
    cod_prov = data.get('cod_prov')

    if cod_prov:
        proveedor = Proveedores.objects.filter(cod_prov=cod_prov).first()
        if not proveedor:
            return Response(
                {"status": "error", "mensaje": "Proveedor no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        mensaje = f"Proveedor '{proveedor.nomfantasia}' actualizado."
    else:
        max_id = Proveedores.objects.aggregate(Max('cod_prov'))['cod_prov__max'] or 0
        cod_prov = max_id + 1
        proveedor = Proveedores(cod_prov=cod_prov)
        mensaje = f"Proveedor creado con el código {cod_prov}."

    proveedor.nomfantasia = data.get('nomfantasia', proveedor.nomfantasia or '')
    proveedor.nomtitular  = data.get('nomfantasia', proveedor.nomtitular or '')
    proveedor.nro_cuit    = data.get('nro_cuit', proveedor.nro_cuit or '')
    proveedor.domicilio   = data.get('domicilio', proveedor.domicilio or '')
    proveedor.telefono    = data.get('telefono', proveedor.telefono or '')
    proveedor.mail        = data.get('mail', proveedor.mail or '')
    proveedor.cond_iva    = int(data.get('cond_iva', proveedor.cond_iva or 1))
    proveedor.estado      = int(data.get('estado', proveedor.estado or 0))

    try:
        proveedor.save()
        return Response({"status": "success", "mensaje": mensaje}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": "error", "mensaje": f"Error guardando: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ── Compras — Listado ─────────────────────────────────────────────────────────

@api_view(['GET'])
def ListarCompras(request):
    """
    Devuelve las últimas 100 compras con datos del proveedor (JOIN manual).
    Soporta filtro por proveedor y rango de fechas.
    """
    try:
        from .utils import aplicar_rango_fechas
        qs = Compras.objects.all()
        qs = aplicar_rango_fechas(request, qs, 'fecha_comprob')

        cod_prov = request.query_params.get('cod_prov')
        if cod_prov:
            qs = qs.filter(cod_prov=cod_prov)

        compras = qs.order_by('-movim').values(
            'movim', 'cod_prov', 'fecha_comprob', 'nro_comprob',
            'cod_comprob', 'comprobante_letra', 'comprobante_pto_vta',
            'neto', 'iva_1', 'total', 'tot_general', 'anulado',
            'observac', 'ret_iva', 'ret_gan', 'ret_iibb',
        )[:100]

        # Enriquecer con nombre del proveedor
        result = list(compras)
        prov_ids = {c['cod_prov'] for c in result}
        provs = {p.cod_prov: p.nomfantasia for p in Proveedores.objects.filter(cod_prov__in=prov_ids)}
        for c in result:
            c['nom_proveedor'] = provs.get(c['cod_prov'], '')

        return Response({"status": "success", "data": result}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def BuscarComprobanteCompra(request):
    """Devuelve cabecera + detalle de una compra para previsualizar o anular."""
    tipo  = request.query_params.get('tipo', 'FA')
    letra = request.query_params.get('letra', 'A')
    pto   = request.query_params.get('pto', '1')
    nro   = request.query_params.get('nro')

    if not nro:
        return Response({"status": "error", "mensaje": "Falta parámetro nro."}, status=400)

    try:
        # nro_comprob legacy = pto_vta * 100000000 + nro_factura
        pto_int = int(pto)
        nro_int = int(nro)
        nro_comprob_legacy = pto_int * 100_000_000 + nro_int
        tipo_comprob = tipo  # p.ej. "FA", "FB"

        compra = Compras.objects.filter(
            cod_comprob=tipo_comprob,
            nro_comprob=nro_comprob_legacy,
        ).first()

        if not compra:
            # Intentar búsqueda por comprobante_pto_vta (modo nuevo)
            compra = Compras.objects.filter(
                cod_comprob=tipo_comprob,
                nro_comprob=nro_int,
                comprobante_pto_vta=str(pto_int).zfill(4),
            ).first()

        if not compra:
            return Response({"status": "error", "mensaje": "Comprobante no encontrado."}, status=404)

        detalles = ComprasDet.objects.filter(movim=compra.movim).values(
            'cod_articulo', 'nom_articulo', 'cantidad', 'precio_unit', 'total', 'p_iva'
        )

        prov = Proveedores.objects.filter(cod_prov=compra.cod_prov).first()

        return Response({
            "status": "success",
            "data": {
                "movim":        compra.movim,
                "cod_prov":     compra.cod_prov,
                "nom_proveedor": prov.nomfantasia if prov else '',
                "fecha_comprob": compra.fecha_comprob,
                "nro_comprob":  compra.nro_comprob,
                "cod_comprob":  compra.cod_comprob,
                "neto":         compra.neto,
                "iva_1":        compra.iva_1,
                "total":        compra.tot_general,
                "anulado":      compra.anulado,
                "items":        list(detalles),
            },
        })
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


# ── Ingreso de comprobante de compras ─────────────────────────────────────────

@api_view(['POST'])
def IngresarComprobanteComprasJSON(request):
    """
    Registra una factura de compra completa.

    Payload esperado (mapeado 1:1 con Compras.cs legacy):
    {
      "Proveedor_Codigo": 5,
      "Comprobante_Tipo": "FA",        // "FA" | "FB" | "FC" | "FX" | "NDA" etc.
      "Comprobante_Letra": "A",
      "Comprobante_PtoVenta": "0001",
      "Comprobante_Numero": 12345,      // número de factura (sin pto venta)
      "Comprobante_FechaEmision": "2026-04-26T00:00:00",
      "Comprobante_Neto": 1000.00,
      "Comprobante_IVA": 210.00,
      "Comprobante_ImporteTotal": 1210.00,
      "Comprobante_Ret_IVA": 0,
      "Comprobante_Ret_Ganancias": 0,
      "Comprobante_Ret_IIBB": 0,
      "Comprobante_CondCompra": "CONTADO",   // "CONTADO" | "CTA.CTE."
      "Comprobante_Categoria": "",
      "cajero": 1,
      "usuario": "admin",
      "Comprobante_Items": [
        {
          "Item_CodigoArticulo": "ART001",
          "Item_DescripArticulo": "Descripción",
          "Item_CantidadUM1": 5,
          "Item_PrecioUnitario": 200.00,
          "Item_TasaIVAInscrip": 21,
          "Item_ImporteTotal": 1000.00
        }
      ]
    }
    """
    data = request.data

    try:
        with transaction.atomic():
            # ── Parámetros base ───────────────────────────────────────────
            cod_prov        = int(data.get('Proveedor_Codigo', 0))
            tipo_comprob    = str(data.get('Comprobante_Tipo', 'FA'))[:2]
            letra_comprob   = str(data.get('Comprobante_Letra', 'A'))
            pto_vta_str     = str(data.get('Comprobante_PtoVenta', '0001')).zfill(4)
            nro_factura     = int(data.get('Comprobante_Numero', 0))
            fecha_emision   = data.get('Comprobante_FechaEmision')
            neto            = Decimal(str(data.get('Comprobante_Neto', 0)))
            iva_total       = Decimal(str(data.get('Comprobante_IVA', 0)))
            importe_total   = Decimal(str(data.get('Comprobante_ImporteTotal', 0)))
            ret_iva         = Decimal(str(data.get('Comprobante_Ret_IVA', 0)))
            ret_gan         = Decimal(str(data.get('Comprobante_Ret_Ganancias', 0)))
            ret_iibb        = Decimal(str(data.get('Comprobante_Ret_IIBB', 0)))
            cond_compra     = str(data.get('Comprobante_CondCompra', 'CONTADO'))
            categoria       = str(data.get('Comprobante_Categoria', ''))[:4]
            cajero          = int(data.get('cajero', 1))
            usuario         = str(data.get('usuario', 'admin'))

            if cod_prov == 0:
                raise ValueError("Debe indicar el código de proveedor.")
            if nro_factura == 0:
                raise ValueError("Debe indicar el número de comprobante.")

            # nro_comprob legacy = pto_vta * 100000000 + nro_factura
            pto_vta_int     = int(pto_vta_str)
            nro_comprob_legacy = pto_vta_int * 100_000_000 + nro_factura

            # Verifica duplicado (igual que VerificarExisteEgreso del legacy)
            if _verificar_existe_egreso(tipo_comprob, nro_comprob_legacy, cod_prov):
                raise ValueError(
                    f"El comprobante {tipo_comprob} {pto_vta_str}-{nro_factura:08d} "
                    f"ya fue registrado para este proveedor."
                )

            # movim = MAX(ventas, bitacora) + 1  (igual que ventas.py)
            nuevo_movim = _siguiente_movim()
            _registrar_en_bitacora(nuevo_movim, cajero, pto_vta_str, usuario)

            # ── INSERT INTO compras ───────────────────────────────────────
            compra = Compras.objects.create(
                movim              = nuevo_movim,
                id_comprob         = 0,
                cod_comprob        = tipo_comprob,
                nro_comprob        = nro_comprob_legacy,
                cod_prov           = cod_prov,
                fecha_comprob      = fecha_emision,
                fecha_vto          = fecha_emision,
                neto               = neto,
                iva_1              = iva_total,
                total              = importe_total,
                tot_general        = importe_total,
                actualiz_stock     = 'S',
                observac           = cond_compra,   # igual que el legacy: str1 (condición)
                usuario            = usuario,
                fecha_mod          = timezone.now(),
                cajero             = cajero,
                categoria          = categoria or None,
                comprobante_tipo   = tipo_comprob,
                comprobante_letra  = letra_comprob,
                comprobante_pto_vta= pto_vta_str,
                ret_iva            = ret_iva,
                ret_gan            = ret_gan,
                ret_iibb           = ret_iibb,
                procesado          = 0,
            )

            # ── INSERT INTO compras_det + UPDATE articulos ────────────────
            for item in data.get('Comprobante_Items', []):
                cod_art     = str(item['Item_CodigoArticulo'])
                cantidad    = Decimal(str(item['Item_CantidadUM1']))
                precio_unit = Decimal(str(item['Item_PrecioUnitario']))
                total_item  = Decimal(str(item.get('Item_ImporteTotal', precio_unit * cantidad)))
                p_iva       = Decimal(str(item.get('Item_TasaIVAInscrip', 21)))
                v_iva       = round(total_item - (total_item / (1 + p_iva / 100)), 2)

                ComprasDet.objects.create(
                    movim              = nuevo_movim,
                    id_comprob         = compra.id_comprob,
                    cod_comprob        = compra.cod_comprob,
                    nro_comprob        = compra.nro_comprob,
                    cod_articulo       = cod_art,
                    nom_articulo       = str(item.get('Item_DescripArticulo', ''))[:50],
                    cantidad           = cantidad,
                    precio_unit        = precio_unit,
                    total              = total_item,
                    cod_prov           = cod_prov,
                    p_iva              = p_iva,
                    v_iva              = v_iva,
                    comprobante_tipo   = compra.comprobante_tipo,
                    comprobante_letra  = compra.comprobante_letra,
                    comprobante_pto_vta= compra.comprobante_pto_vta,
                    procesado          = 0,
                )

                # Suma stock y actualiza último costo (igual que legacy)
                Articulos.objects.filter(cod_art=cod_art).update(
                    stock     = F('stock') + cantidad,
                    costo_ult = precio_unit,
                    ult_compra= timezone.now(),
                )

            # ── Medio de pago: CONTADO → cheq_tarj_prov (origen='SAC') ───
            if cond_compra == 'CONTADO':
                CheqTarjProv.objects.create(
                    movim              = nuevo_movim,
                    origen             = 'SAC',
                    cod_prov           = cod_prov,
                    tipo               = 'EFE',
                    importe            = importe_total,
                    fecha_rece         = timezone.now(),
                    fecha_vto          = timezone.now(),
                    cod_comprob        = tipo_comprob,
                    nro_comprob        = nro_comprob_legacy,
                    id_comprob         = 0,
                    estado             = 'Cobrado',
                    pendiente          = 'N',
                    observac_1         = cond_compra,
                    usuario            = usuario,
                    cajero             = cajero,
                    comprobante_tipo   = tipo_comprob,
                    comprobante_letra  = letra_comprob,
                    comprobante_pto_vta= pto_vta_str,
                )

            # ── Medio de pago: CTA.CTE. → cta_cte_prov (origen='CMP') ────
            elif cond_compra == 'CTA.CTE.':
                CtaCteProv.objects.create(
                    movim          = nuevo_movim,
                    origen         = 'CMP',
                    cod_prov       = cod_prov,
                    imported       = importe_total,
                    importeh       = importe_total,
                    fecha          = fecha_emision,
                    fecha_oper     = timezone.now(),
                    cod_comprob    = tipo_comprob,
                    nro_comprob    = nro_comprob_legacy,
                    id_comprob     = 0,
                    detalle        = f'Compra {tipo_comprob} N° {nro_factura}',
                    fec_mod        = timezone.now(),
                    saldo          = importe_total,
                    cobrado        = 0,
                    cobrado_tmp    = 0,
                    parcial        = 0,
                    parcial_tmp    = 0,
                    moneda         = 1,
                    anulado        = 'N',
                    cuota          = 0,
                    nro_lote       = 0,
                    usuario        = usuario,
                    comprobante_tipo   = tipo_comprob,
                    comprobante_letra  = letra_comprob,
                    comprobante_pto_vta= pto_vta_str,
                    compro_r       = '',
                    nro_compro_r   = 0,
                )

        return Response({
            "status":    "success",
            "mensaje":   "Compra registrada. Stock y costos actualizados.",
            "movim":     nuevo_movim,
            "nro_comprob": nro_comprob_legacy,
        }, status=status.HTTP_201_CREATED)

    except ValueError as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {"status": "error", "mensaje": f"Error interno: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ── Anulación de comprobante de compras ───────────────────────────────────────

@api_view(['POST'])
def AnularComprobanteCompra(request):
    """
    Anula una compra:
      1. UPDATE compras SET anulado='S'
      2. Revierte stock por cada ítem (stock = stock - cantidad)
      3. Si había CTA.CTE., revierte el saldo en cta_cte_prov

    Replica Com_Anula.cs del legacy.
    """
    movim_original = request.data.get('movim')

    try:
        with transaction.atomic():
            compra = Compras.objects.select_for_update().filter(movim=movim_original).first()
            if not compra:
                return Response({"status": "error", "mensaje": "Movimiento no encontrado."}, status=404)

            if compra.anulado == 'S':
                return Response({"status": "error", "mensaje": "Este comprobante ya fue anulado."}, status=400)

            # Revertir stock por cada item (Com_Anula.cs usa stock=stock-cantidad)
            for item in ComprasDet.objects.filter(movim=movim_original):
                Articulos.objects.filter(cod_art=item.cod_articulo).update(
                    stock=F('stock') - item.cantidad
                )

            # Marcar como anulado
            compra.anulado   = 'S'
            compra.procesado = -1
            compra.save(update_fields=['anulado', 'procesado'])

            # Si era cuenta corriente, anulamos el saldo en cta_cte_prov
            if compra.observac == 'CTA.CTE.':
                CtaCteProv.objects.filter(
                    movim=movim_original,
                    origen='CMP',
                ).update(anulado='S', saldo=0)

        return Response({
            "status":  "success",
            "mensaje": (
                f"Compra {compra.cod_comprob} N° {compra.nro_comprob} anulada. "
                "Stock revertido."
            ),
        })

    except Exception as e:
        return Response(
            {"status": "error", "mensaje": f"Error al anular: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )