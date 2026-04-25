"""
ventas.py — Circuito de facturación migrado desde Ven_Factura.cs (legacy C#).

Correcciones respecto a la versión anterior:
  1. movim  ← MAX(ventas, bitacora) + 1 con INSERT explícito en bitacora.
             El legacy usa bitacora AUTO_INCREMENT, pero esa tabla se TRUNCA
             periódicamente (líneas 88862 y 88977 del legacy), lo que resetea
             el contador y genera conflictos de PK con ventas.
             La nueva implementación calcula el movim como MAX de ambas tablas,
             serializado por el SELECT FOR UPDATE de TipocompCli.
  2. ventas: campos completos — zeta, exento, percepciones, recargos, descuento_iva,
             recargos_iva, impuestos_internos, dtos_por_items/iva, costo_general/completo,
             perce_caba, perce_bsas, perce_5329
  3. ventas: fecha_fact = DATE ONLY  (DateTime.Now.Date del legacy)
             ventas: neto = subtotal bruto, total = base neta impositiva, tot_general = total cliente
  4. ventas_det: campos completos — es_promo, impuesto_unitario, v_iva_base,
                 p_descuento, es_kit, descuento_iva, costo, item_libre
  5. Stock kits: es_kit==1 → descuenta sub-items de articulos_bom, NO el artículo padre
  6. cheq_tarj_cli: EFE también va a esta tabla (bug crítico corregido)
  7. cta_cte_cli: detalle = "Vta Cte Cte"  (cadena exacta del legacy)
  8. Tablas adicionales: ventas_promo, ventas_descuentos, ventas_regimenes, ventas_extras
"""

import json
import os
from decimal import Decimal

from django.db import transaction, connection
from django.db.models import F
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import (
    Ventas, VentasDet, VentasPromo, VentasDescuentos, VentasRegimenes, VentasExtras,
    TipocompCli, Articulos, ArticulosBom,
    CtaCteCli, CajasDet, CheqTarjCli,
)
from ..serializers import IngresoComprobanteSerializer

# Medios de pago que van a cheq_tarj_cli (EFE incluido — igual que el legacy)
_TIPOS_CHEQ = frozenset({'EFE', 'TAR', 'CHE', 'TCR', 'TRF', 'MPA', 'DEV', 'PWQ', 'FYD'})

# Mapa de anulaciones comprobante → nota de crédito
MAPA_ANULACIONES = {
    'EA': 'KA', 'EB': 'KB', 'EC': 'KC',
    'FA': 'CA', 'FB': 'CB', 'FC': 'CC',
    'MA': 'NA', 'MB': 'NB',
    'PR': 'DV',
    'TK': 'NC',
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _registrar_en_bitacora(nuevo_movim: int, cajero: int,
                            pto_venta: str, usuario: str) -> None:
    """
    Inserta en bitacora el registro de auditoría con el movim ya calculado.

    Por qué NO usamos bitacora AUTO_INCREMENT para generar el movim:
      El legacy hace TRUNCATE sobre bitacora en sus rutinas de mantenimiento
      (Ven_Factura.cs líneas 88862 y 88977), lo que resetea el AUTO_INCREMENT
      a 1. Si ventas ya tiene movim hasta N, el próximo INSERT en bitacora
      devolvería 1 y rompería la PK de ventas con Duplicate entry.

    La serialización de movim se logra mediante el SELECT FOR UPDATE sobre
    TipocompCli que se hace ANTES de llamar a esta función: todas las
    transacciones de facturación se serializan ahí, garantizando que
    MAX(ventas.movim) sea estable durante el cálculo.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT IGNORE INTO bitacora
                (movim, inicio, fin, fecha, operador, puesto, usuario, tipo_evento)
            VALUES
                (%s, 1, 1, NOW(), %s, %s, %s, 1)
            """,
            [
                nuevo_movim,
                cajero,
                (pto_venta or '')[:15],    # max_length=15 en el modelo
                (usuario or 'admin')[:15],  # max_length=15 en el modelo
            ],
        )


def _siguiente_movim() -> int:
    """
    Devuelve MAX(ventas.movim, bitacora.movim) + 1.
    Debe llamarse DENTRO de una transacción con SELECT FOR UPDATE activo
    sobre TipocompCli para que el valor sea seguro entre hilos.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT GREATEST(
                COALESCE((SELECT MAX(movim) FROM ventas),   0),
                COALESCE((SELECT MAX(movim) FROM bitacora), 0)
            ) + 1
        """)
        return int(cursor.fetchone()[0])


def _guardar_json_respaldo(venta, payload: dict) -> None:
    """Copia JSON en disco. No es crítico: falla silenciosamente."""
    try:
        nombre = (
            f"{venta.cod_comprob}"
            f"{venta.comprobante_letra or 'X'}"
            f"{str(venta.comprobante_pto_vta).zfill(4)}"
            f"{str(venta.nro_comprob).zfill(8)}.json"
        )
        carpeta = "/documentos_json"
        os.makedirs(carpeta, exist_ok=True)
        with open(os.path.join(carpeta, nombre), 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=4, ensure_ascii=False, cls=DjangoJSONEncoder)
    except Exception as e:
        print(f"⚠️  JSON backup failed: {e}")


# ── Ingreso de comprobante ────────────────────────────────────────────────────

@api_view(['POST'])
def IngresarComprobanteVentasJSON(request):
    serializer = IngresoComprobanteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"status": "error", "mensaje": "JSON inválido", "errores": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = serializer.validated_data

    try:
        with transaction.atomic():

            # ── Parámetros base ───────────────────────────────────────────────
            tipo_comprob    = data['Comprobante_Tipo'][:2]
            letra_comprob   = data['Comprobante_Letra']
            pto_vta         = str(data['Comprobante_PtoVenta']).zfill(4)
            cliente_codigo  = int(data['Cliente_Codigo'])
            condicion_venta = data.get('Comprobante_CondVenta', '1')
            cajero          = int(data.get('cajero', 1))
            nro_caja        = int(data.get('nro_caja', 1))
            vendedor        = int(data.get('Vendedor_Codigo', 1))
            usuario         = data.get('Comprobante_Usuario', 'admin')
            zeta            = int(data.get('Comprobante_Zeta', 0))

            # 1. SELECT FOR UPDATE sobre TipocompCli — serializa TODAS las
            #    transacciones de facturación. El movim se calcula DESPUÉS
            #    de adquirir este lock para que MAX(ventas.movim) sea estable.
            config = (
                TipocompCli.objects
                .select_for_update()
                .filter(cod_compro=tipo_comprob)
                .first()
            )
            if not config:
                raise ValueError(
                    f"Comprobante '{tipo_comprob}' no configurado en tipocomp_cli."
                )
            nro_comprob = config.ultnro + 1
            config.ultnro = nro_comprob
            config.save(update_fields=['ultnro'])

            # 2. movim: GREATEST(MAX(ventas), MAX(bitacora)) + 1
            #    Seguro porque el lock de TipocompCli serializa concurrentes.
            #    Insertamos en bitacora con valor explícito (no AUTO_INCREMENT)
            #    ya que el legacy trunca esa tabla y resetea el contador.
            nuevo_movim = _siguiente_movim()
            _registrar_en_bitacora(nuevo_movim, cajero, pto_vta, usuario)

            # 3. Importes de cabecera
            # neto        = txtSubTotal  — subtotal bruto ANTES de descuentos
            # total       = neto - descuento + recargos  — base neta impositiva
            # tot_general = txtTotal     — lo que paga el cliente
            neto        = Decimal(str(data.get('Comprobante_Neto', 0)))
            iva_1       = Decimal(str(data.get('Comprobante_IVA', 0)))
            exento      = Decimal(str(data.get('Comprobante_Exento', 0)))
            descuento   = Decimal(str(data.get('Comprobante_Descuento', 0)))
            descu_iva   = Decimal(str(data.get('Comprobante_DescuentoIVA', 0)))
            dtos_items  = Decimal(str(data.get('Comprobante_DtosPorItems', 0)))
            dtos_i_iva  = Decimal(str(data.get('Comprobante_DtosPorItemsIVA', 0)))
            recargos    = Decimal(str(data.get('Comprobante_Recargos', 0)))
            rec_iva     = Decimal(str(data.get('Comprobante_RecargosIVA', 0)))
            percepciones= Decimal(str(data.get('Comprobante_Percepciones', 0)))
            perce_caba  = Decimal(str(data.get('Comprobante_PerceCABA', 0)))
            perce_bsas  = Decimal(str(data.get('Comprobante_PerceBsAs', 0)))
            perce_5329  = Decimal(str(data.get('Comprobante_Perce5329', 0)))
            imp_int     = Decimal(str(data.get('Comprobante_ImpuestosInternos', 0)))
            costo_gen   = Decimal(str(data.get('Comprobante_CostoGeneral', 0)))
            costo_comp  = int(data.get('Comprobante_CostoCompleto', 0))
            tot_general = Decimal(str(data['Comprobante_ImporteTotal']))

            total_neto_raw = data.get('Comprobante_TotalNeto')
            total_neto = (
                Decimal(str(total_neto_raw))
                if total_neto_raw is not None
                else neto - descuento + recargos
            )

            # 4. INSERT INTO ventas (campos exactos del legacy)
            venta = Ventas.objects.create(
                movim=nuevo_movim,
                id_comprob=config.id_compro,
                cod_comprob=tipo_comprob,
                nro_comprob=nro_comprob,
                cod_cli=cliente_codigo,
                fecha_fact=timezone.now().date(),   # DATE ONLY — igual que DateTime.Now.Date
                fecha_vto=timezone.now(),            # DATETIME  — igual que DateTime.Now
                neto=neto,
                iva_1=iva_1,
                total=total_neto,
                descuento=descuento,
                descuento_iva=descu_iva,
                dtos_por_items=dtos_items,
                dtos_por_items_iva=dtos_i_iva,
                recargos=recargos,
                recargos_iva=rec_iva,
                exento=exento,
                percepciones=percepciones,
                perce_caba=perce_caba,
                perce_bsas=perce_bsas,
                perce_5329=perce_5329,
                impuestos_internos=imp_int,
                tot_general=tot_general,
                costo_general=costo_gen,
                costo_completo=costo_comp,
                observac=data.get('Comprobante_Observac', ''),
                usuario=usuario,
                cajero=cajero,
                nro_caja=nro_caja,
                comprobante_pto_vta=pto_vta,
                comprobante_tipo=tipo_comprob,    # agregado para FE
                comprobante_letra=letra_comprob,  # agregado para FE
                cond_venta=condicion_venta,
                vendedor=vendedor,
                moneda=int(data.get('Comprobante_Moneda', 1)),
                zeta=zeta,
                anulado='N',
                procesado=0,
                fecha_mod=timezone.now(),
            )

            # 5. INSERT INTO ventas_det + stock
            for item in data['Comprobante_Items']:
                cod_art  = item['Item_CodigoArticulo']
                cantidad = item['Item_CantidadUM1']
                es_kit   = int(item.get('Item_EsKit', 0))

                VentasDet.objects.create(
                    movim=nuevo_movim,
                    id_comprob=config.id_compro,
                    cod_comprob=tipo_comprob,
                    nro_comprob=nro_comprob,
                    cod_articulo=cod_art,
                    cantidad=cantidad,
                    precio_unit=item['Item_PrecioUnitario'],
                    precio_unit_base=item.get('Item_PrecioUnitarioBase',
                                              item['Item_PrecioUnitario']),
                    descuento=item.get('Item_ImporteDescComercial', 0),
                    descuento_iva=item.get('Item_DescuentoIVA', 0),
                    p_descuento=item.get('Item_PorcentajeDescuento', 0),
                    total=item['Item_ImporteTotal'],
                    p_iva=item.get('Item_TasaIVAInscrip', 21),
                    v_iva=item.get('Item_ImporteIVAInscrip', 0),
                    v_iva_base=item.get('Item_ImporteIVABase', 0),
                    impuesto_unitario=item.get('Item_ImpuestoUnitario', 0),
                    costo=item.get('Item_Costo', 0),
                    detalle=item.get('Item_DescripArticulo', ''),
                    es_promo=int(item.get('Item_EsPromo', 0)),
                    es_kit=es_kit,
                    item_libre=item.get('Item_CodigoPromo', ''),
                    comprobante_pto_vta=pto_vta,
                    comprobante_tipo=tipo_comprob,
                    comprobante_letra=letra_comprob,
                    procesado=0,
                )

                # Stock: combo=0 → descuenta artículo; combo=1 → descuenta BOM
                if es_kit == 0:
                    Articulos.objects.filter(cod_art=cod_art).update(
                        stock=F('stock') - cantidad
                    )
                else:
                    for bom in ArticulosBom.objects.filter(cod_padre=cod_art):
                        Articulos.objects.filter(cod_art=bom.cod_hijo).update(
                            stock=F('stock') - (cantidad * bom.cant_hijo)
                        )

            # 6. Medios de pago
            for mp in data.get('Comprobante_MediosPago', []):
                cod_pago   = str(mp.get('MedioPago', 'EFE'))
                importe_mp = mp.get('MedioPago_Importe', 0)
                fec_vto_mp = mp.get('MedioPago_FechaVencimiento') or timezone.now()
                referencia = mp.get('MedioPago_Referencia', '')

                if cod_pago in _TIPOS_CHEQ:
                    nro_raw = (mp.get('MedioPago_NroCupon') or
                               mp.get('MedioPago_NumeroCheque') or '0')
                    try:
                        nro_cupon = int(nro_raw)
                    except (ValueError, TypeError):
                        nro_cupon = 0

                    CheqTarjCli.objects.create(
                        movim=nuevo_movim,
                        origen='VTA',
                        cod_cli=cliente_codigo,
                        tipo=cod_pago,
                        importe=importe_mp,
                        fecha_rece=timezone.now(),
                        cod_comprob=tipo_comprob,
                        nro_comprob=nro_comprob,
                        id_comprob=config.id_compro,
                        estado='Cobrado',
                        pendiente='N',
                        usuario=usuario,
                        cajero=cajero,
                        cod_entidad=mp.get('MedioPago_CodPagoDet', 0),
                        observac_1=referencia,
                        comprobante_pto_vta=pto_vta,
                        fecha_vto=fec_vto_mp,
                        recargo=mp.get('MedioPago_Recargo', 0),
                        recargo_iva=mp.get('MedioPago_RecargoIVA', 0),
                        cod_cuota=mp.get('MedioPago_CantidadCuotas', 0),
                        numero=nro_cupon,
                        entidad=mp.get('MedioPago_Entidad', ''),
                        codigo_banco=mp.get('MedioPago_CodigoBanco', ''),
                        codigo_pago=mp.get('MedioPago_CodigoPago', ''),
                        recargo10=mp.get('MedioPago_Recargo10', 0),
                        recargo_iva10=mp.get('MedioPago_RecargoIVA10', 0),
                        recargo0=mp.get('MedioPago_Recargo0', 0),
                        idpagos=mp.get('MedioPago_IdPayway', ''),
                        nro_caja=nro_caja,
                        comprobante_tipo=tipo_comprob,
                        comprobante_letra=letra_comprob,
                        procesado=0,
                    )

                elif cod_pago == 'CTA' and tipo_comprob != 'PR':
                    CtaCteCli.objects.create(
                        movim=nuevo_movim,
                        origen='VTA',
                        cod_cli_id=cliente_codigo,
                        imported=importe_mp,
                        fecha=timezone.now(),
                        cod_comprob=tipo_comprob,
                        nro_comprob=nro_comprob,
                        id_comprob=config.id_compro,
                        detalle='Vta Cte Cte',   # cadena EXACTA del legacy
                        fec_vto=timezone.now(),
                        saldo=importe_mp,
                        usuario=usuario,
                        cajero=cajero,
                        comprobante_pto_vta=pto_vta,
                        comprobante_tipo=tipo_comprob,
                        comprobante_letra=letra_comprob,
                        procesado=0,
                    )

            # 7. Promociones aplicadas → ventas_promo
            for promo in data.get('Comprobante_Promos', []):
                VentasPromo.objects.create(
                    movim=nuevo_movim,
                    cod_comprob=tipo_comprob,
                    nro_comprob=nro_comprob,
                    id_comprob=config.id_compro,
                    detalle=promo['Promo_Detalle'],
                    comprobante_pto_vta=pto_vta,
                    importe=promo['Promo_Importe'],
                    iva_importe=promo.get('Promo_IvaImporte', 0),
                    cod_promo=promo['Promo_Codigo'],
                    codigo_erp=promo.get('Promo_CodigoErp', ''),
                    comprobante_tipo=tipo_comprob,
                    comprobante_letra=letra_comprob,
                    procesado=0,
                )

            # 8. Descuentos globales → ventas_descuentos
            for descu in data.get('Comprobante_Descuentos', []):
                tasa = Decimal(str(descu.get('Descu_Tasa', 0)))
                if tasa == 0:
                    tasa = Decimal('99')   # legacy convierte 0→99
                VentasDescuentos.objects.create(
                    movim=nuevo_movim,
                    cod_comprob=tipo_comprob,
                    nro_comprob=nro_comprob,
                    id_comprob=config.id_compro,
                    detalle=descu['Descu_Detalle'],
                    comprobante_pto_vta=pto_vta,
                    importe=descu['Descu_Importe'],
                    iva_importe=descu.get('Descu_IvaImporte', 0),
                    cod_descu=descu['Descu_Codigo'],
                    tasa=tasa,
                    cod_erp=descu.get('Descu_CodigoErp', ''),
                    comprobante_tipo=tipo_comprob,
                    comprobante_letra=letra_comprob,
                    procesado=0,
                )

            # 9. Regímenes / percepciones → ventas_regimenes
            for reg in data.get('Comprobante_Regimenes', []):
                VentasRegimenes.objects.create(
                    movim=nuevo_movim,
                    cod_comprob=tipo_comprob,
                    nro_comprob=nro_comprob,
                    id_comprob=config.id_compro,
                    regimen=reg['Regimen_Detalle'],
                    comprobante_pto_vta=pto_vta,
                    importe=reg['Regimen_Importe'],
                    base_imponible=reg.get('Regimen_BaseImponible', 0),
                    comprobante_tipo=tipo_comprob,
                    comprobante_letra=letra_comprob,
                    procesado=0,
                )

            # 10. ventas_extras (cliente == 2: comprador anónimo con documento)
            if cliente_codigo == 2:
                doc = data.get('ClienteVarios_Documento', '')
                if doc:
                    try:
                        VentasExtras.objects.create(
                            cod_comprob=tipo_comprob,
                            nro_comprob=nro_comprob,
                            comprobante_pto_vta=pto_vta,
                            cliente_documento=doc,
                            cliente_nombre=data.get('ClienteVarios_Nombre', ''),
                            obs=(data.get('ClienteVarios_Domicilio', '') or '')[:50],
                            procesado=0,
                        )
                    except Exception:
                        pass  # no crítico (igual que el try/catch vacío del legacy)

        # Fuera del atomic: backup no crítico
        _guardar_json_respaldo(venta, request.data)

        return Response({
            "status": "success",
            "mensaje": "Comprobante ingresado correctamente.",
            "movim": nuevo_movim,
            "nro_comprob": nro_comprob,
            "tipo": tipo_comprob,
            "pto_vta": pto_vta,
        }, status=status.HTTP_201_CREATED)

    except ValueError as e:
        return Response({"status": "error", "mensaje": str(e)},
                        status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"status": "error", "mensaje": f"Error interno: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── Búsqueda y anulación ──────────────────────────────────────────────────────

@api_view(['GET'])
def UltimosComprobantesVenta(request):
    try:
        ventas = Ventas.objects.all().order_by('-movim')[:50]
        data = [
            {
                "movim":     v.movim,
                "tipo":      v.cod_comprob,
                "letra":     v.comprobante_letra or '',
                "pto_vta":   v.comprobante_pto_vta,
                "nro":       v.nro_comprob,
                "fecha":     v.fecha_fact,
                "total":     v.tot_general,
                "procesado": v.procesado,
            }
            for v in ventas
        ]
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def BuscarComprobanteVenta(request):
    tipo = request.query_params.get('tipo', 'EA')
    pto  = request.query_params.get('pto', '1')
    nro  = request.query_params.get('nro')

    if not nro:
        return Response({"status": "error", "mensaje": "Falta el parámetro nro."},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        venta = Ventas.objects.filter(
            cod_comprob=tipo,
            nro_comprob=nro,
            comprobante_pto_vta=str(pto).zfill(4),
        ).first()

        if not venta:
            return Response({"status": "error", "mensaje": "Comprobante no encontrado."},
                            status=status.HTTP_404_NOT_FOUND)

        detalles = VentasDet.objects.filter(movim=venta.movim).values(
            'cod_articulo', 'detalle', 'cantidad', 'precio_unit', 'total', 'costo'
        )
        return Response({
            "status": "success",
            "data": {
                "movim":     venta.movim,
                "fecha":     venta.fecha_fact,
                "cliente":   venta.cod_cli,
                "total":     venta.tot_general,
                "procesado": venta.procesado,
                "items":     list(detalles),
            },
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def AnularComprobanteVenta(request):
    movim_original = request.data.get('movim')

    try:
        with transaction.atomic():
            venta_orig = Ventas.objects.filter(movim=movim_original).first()
            if not venta_orig:
                return Response({"status": "error", "mensaje": "Movimiento no encontrado."},
                                status=status.HTTP_404_NOT_FOUND)

            if venta_orig.procesado == -1:
                return Response({"status": "error",
                                  "mensaje": "Este comprobante ya fue anulado."},
                                status=status.HTTP_400_BAD_REQUEST)

            cod_nc = MAPA_ANULACIONES.get(venta_orig.cod_comprob)
            if not cod_nc:
                return Response(
                    {"status": "error",
                     "mensaje": f"Sin N/C configurada para '{venta_orig.cod_comprob}'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            config_nc = (
                TipocompCli.objects
                .select_for_update()
                .filter(cod_compro=cod_nc)
                .first()
            )
            if not config_nc:
                return Response(
                    {"status": "error",
                     "mensaje": f"Configurar '{cod_nc}' en tipocomp_cli primero."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cajero  = venta_orig.cajero or 1
            usuario = venta_orig.usuario or 'admin'
            pto_vta = venta_orig.comprobante_pto_vta or '0001'

            nro_comprob_nc = config_nc.ultnro + 1
            config_nc.ultnro = nro_comprob_nc
            config_nc.save(update_fields=['ultnro'])

            nuevo_movim = _siguiente_movim()
            _registrar_en_bitacora(nuevo_movim, cajero, pto_vta, usuario)

            nc = Ventas.objects.create(
                movim=nuevo_movim,
                id_comprob=config_nc.id_compro,
                cod_comprob=config_nc.cod_compro,
                nro_comprob=nro_comprob_nc,
                cod_cli=venta_orig.cod_cli,
                fecha_fact=timezone.now().date(),
                fecha_vto=timezone.now(),
                neto=venta_orig.neto,
                iva_1=venta_orig.iva_1,
                total=venta_orig.total,
                descuento=venta_orig.descuento,
                descuento_iva=venta_orig.descuento_iva or 0,
                dtos_por_items=venta_orig.dtos_por_items or 0,
                dtos_por_items_iva=venta_orig.dtos_por_items_iva or 0,
                recargos=venta_orig.recargos or 0,
                recargos_iva=venta_orig.recargos_iva or 0,
                exento=venta_orig.exento,
                percepciones=venta_orig.percepciones or 0,
                perce_caba=venta_orig.perce_caba or 0,
                perce_bsas=venta_orig.perce_bsas or 0,
                perce_5329=venta_orig.perce_5329 or 0,
                impuestos_internos=venta_orig.impuestos_internos or 0,
                tot_general=venta_orig.tot_general,
                costo_general=venta_orig.costo_general or 0,
                costo_completo=venta_orig.costo_completo or 0,
                vendedor=venta_orig.vendedor,
                moneda=venta_orig.moneda,
                cajero=cajero,
                nro_caja=venta_orig.nro_caja,
                comprobante_pto_vta=pto_vta,
                comprobante_tipo=config_nc.cod_compro,
                comprobante_letra=venta_orig.comprobante_letra,
                cond_venta=venta_orig.cond_venta,
                zeta=0,
                anulado='N',
                procesado=0,
                observac=f"Anula {venta_orig.cod_comprob} N° {venta_orig.nro_comprob}",
                usuario=usuario,
                fecha_mod=timezone.now(),
            )

            for item in VentasDet.objects.filter(movim=movim_original):
                VentasDet.objects.create(
                    movim=nuevo_movim,
                    id_comprob=nc.id_comprob,
                    cod_comprob=nc.cod_comprob,
                    nro_comprob=nc.nro_comprob,
                    cod_articulo=item.cod_articulo,
                    cantidad=item.cantidad,
                    precio_unit=item.precio_unit,
                    precio_unit_base=item.precio_unit_base,
                    descuento=item.descuento,
                    descuento_iva=item.descuento_iva or 0,
                    p_descuento=item.p_descuento or 0,
                    total=item.total,
                    p_iva=item.p_iva,
                    v_iva=item.v_iva,
                    v_iva_base=item.v_iva_base or 0,
                    impuesto_unitario=item.impuesto_unitario or 0,
                    costo=item.costo or 0,
                    detalle=item.detalle,
                    es_promo=item.es_promo or 0,
                    es_kit=item.es_kit or 0,
                    item_libre=item.item_libre or '',
                    comprobante_pto_vta=pto_vta,
                    comprobante_tipo=nc.comprobante_tipo,
                    comprobante_letra=nc.comprobante_letra,
                    procesado=0,
                )
                es_kit = item.es_kit or 0
                if es_kit == 0:
                    Articulos.objects.filter(cod_art=item.cod_articulo).update(
                        stock=F('stock') + item.cantidad
                    )
                else:
                    for bom in ArticulosBom.objects.filter(cod_padre=item.cod_articulo):
                        Articulos.objects.filter(cod_art=bom.cod_hijo).update(
                            stock=F('stock') + (item.cantidad * bom.cant_hijo)
                        )

            if venta_orig.cond_venta == '2':
                CtaCteCli.objects.create(
                    movim=nuevo_movim, origen='N/C', cod_cli_id=venta_orig.cod_cli,
                    imported=-nc.total, fecha=timezone.now(),
                    cod_comprob=nc.cod_comprob, nro_comprob=nc.nro_comprob,
                    id_comprob=nc.id_comprob,
                    detalle=f"N/C N° {nc.nro_comprob}",
                    fec_vto=timezone.now(), saldo=0,
                    usuario=usuario, cajero=cajero,
                    comprobante_pto_vta=pto_vta,
                    comprobante_tipo=nc.comprobante_tipo,
                    comprobante_letra=nc.comprobante_letra,
                    procesado=0,
                )
            else:
                CajasDet.objects.create(
                    nro_caja=nc.nro_caja or 1, tipo='N/C', forma='EFE',
                    nombre=f"NC N° {nc.nro_comprob} (Dev.)",
                    importe_cajero=-nc.tot_general,
                    importe_real=-nc.tot_general,
                    procesado=0,
                )
                for pago in CheqTarjCli.objects.filter(movim=movim_original):
                    CheqTarjCli.objects.create(
                        movim=nuevo_movim, origen='N/C',
                        cod_cli=pago.cod_cli, tipo=pago.tipo,
                        importe=-pago.importe,
                        fecha_rece=timezone.now(), fecha_vto=pago.fecha_vto,
                        id_comprob=nc.id_comprob, cod_comprob=nc.cod_comprob,
                        nro_comprob=nc.nro_comprob,
                        cod_entidad=pago.cod_entidad, entidad=pago.entidad,
                        numero=pago.numero, moneda=pago.moneda, cuota=pago.cuota,
                        estado='ANULADO', pendiente='N',
                        usuario=usuario, cajero=cajero,
                        nro_caja=nc.nro_caja or 1,
                        comprobante_tipo=nc.comprobante_tipo,
                        comprobante_letra=nc.comprobante_letra,
                        comprobante_pto_vta=pto_vta,
                        procesado=0,
                    )

            Ventas.objects.filter(movim=movim_original).update(procesado=-1, anulado='S')

        return Response({
            "status": "success",
            "mensaje": (
                f"Emitida {nc.comprobante_tipo} N° {nc.nro_comprob}. "
                "Stock y caja revertidos."
            ),
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status": "error", "mensaje": f"Error al emitir N/C: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)