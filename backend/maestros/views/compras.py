from django.db import transaction
from django.db.models import Max, Q, F
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import Compras, ComprasDet, Proveedores, Articulos


# ── Proveedores ───────────────────────────────────────────────────────────────

@api_view(['GET'])
def ListarProveedores(request):
    busqueda = request.query_params.get('buscar', '')
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
    proveedor.nomtitular = data.get('nomfantasia', proveedor.nomtitular or '')
    proveedor.nro_cuit = data.get('nro_cuit', proveedor.nro_cuit or '')
    proveedor.domicilio = data.get('domicilio', proveedor.domicilio or '')
    proveedor.telefono = data.get('telefono', proveedor.telefono or '')
    proveedor.mail = data.get('mail', proveedor.mail or '')
    proveedor.cond_iva = int(data.get('cond_iva', proveedor.cond_iva or 1))
    proveedor.estado = int(data.get('estado', proveedor.estado or 0))

    try:
        proveedor.save()
        return Response({"status": "success", "mensaje": mensaje}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"status": "error", "mensaje": f"Error guardando: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ── Compras ───────────────────────────────────────────────────────────────────

@api_view(['GET'])
def ListarCompras(request):
    try:
        compras = Compras.objects.all().order_by('-movim').values(
            'movim', 'cod_prov', 'fecha_comprob', 'nro_comprob',
            'cod_comprob', 'total', 'tot_general', 'anulado',
        )[:100]
        return Response({"status": "success", "data": list(compras)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def IngresarComprobanteComprasJSON(request):
    """
    Registra una factura de compra, actualiza costo_ult y suma stock.
    Campos corregidos respecto al modelo real de Compras.
    """
    data = request.data

    try:
        with transaction.atomic():
            # Autoincremento seguro
            ultimo = Compras.objects.select_for_update().aggregate(Max('movim'))
            nuevo_movim = (ultimo['movim__max'] or 0) + 1

            tipo_comprob = str(data.get('Comprobante_Tipo', 'FC'))[:2]
            nro_comprob = data.get('Comprobante_Numero', 0)
            fecha_emision = data.get('Comprobante_FechaEmision')
            neto = float(data.get('Comprobante_Neto', 0))
            iva_total = float(data.get('Comprobante_IVA', 0))
            importe_total = float(data.get('Comprobante_ImporteTotal', 0))

            compra = Compras.objects.create(
                movim=nuevo_movim,
                id_comprob=1,                  # genérico para compras manuales
                cod_comprob=tipo_comprob,
                nro_comprob=nro_comprob,
                cod_prov=data.get('Proveedor_Codigo'),
                fecha_comprob=fecha_emision,   # campo real del modelo
                fecha_vto=fecha_emision,
                neto=neto,
                iva_1=iva_total,
                total=importe_total,
                tot_general=importe_total,
                observac=data.get('observac', ''),
                usuario=data.get('usuario', 'admin'),
                fecha_mod=timezone.now(),
                procesado=0,
                comprobante_tipo=tipo_comprob,
                comprobante_letra=data.get('Comprobante_Letra', 'A'),
                comprobante_pto_vta=str(data.get('Comprobante_PtoVenta', '0001')).zfill(4),
            )

            for item in data.get('Comprobante_Items', []):
                cod_art = item['Item_CodigoArticulo']
                cantidad = float(item['Item_CantidadUM1'])
                precio_costo = float(item['Item_PrecioUnitario'])
                total_item = float(item['Item_ImporteTotal'])
                p_iva = float(item.get('Item_TasaIVAInscrip', 21))

                ComprasDet.objects.create(
                    movim=nuevo_movim,
                    id_comprob=compra.id_comprob,
                    cod_comprob=compra.cod_comprob,
                    nro_comprob=compra.nro_comprob,
                    cod_articulo=cod_art,
                    nom_articulo=item.get('Item_DescripArticulo', ''),
                    cantidad=cantidad,
                    precio_unit=precio_costo,
                    total=total_item,
                    p_iva=p_iva,
                    v_iva=round(total_item - (total_item / (1 + p_iva / 100)), 2),
                    comprobante_tipo=compra.comprobante_tipo,
                    comprobante_letra=compra.comprobante_letra,
                    comprobante_pto_vta=compra.comprobante_pto_vta,
                    procesado=0,
                )

                # Suma stock y actualiza último costo
                Articulos.objects.filter(cod_art=cod_art).update(
                    stock=F('stock') + cantidad,
                    costo_ult=precio_costo,
                    ult_compra=timezone.now(),
                )

        return Response(
            {
                "status": "success",
                "mensaje": "Compra registrada. Stock y costos actualizados.",
                "movim": nuevo_movim,
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response(
            {"status": "error", "mensaje": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
