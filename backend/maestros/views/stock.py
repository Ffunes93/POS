"""
stock.py — ABM artículos, rubros, subrubros y movimientos manuales de stock.

Movimientos nuevos migrados desde:
  Stock_Entrada.cs → RegistrarEntradaStock (cod_comprob='IS', stock+)
  Stock_Salida.cs  → RegistrarSalidaStock  (cod_comprob='SS', stock-)
"""

from decimal import Decimal

from django.db import transaction
from django.db.models import Q, F
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import (
    Articulos, ArticulosRubros, ArticulosSubrub, StockCausaemision,
    Compras, ComprasDet, TipocompCli,
)
from .ventas import _siguiente_movim, _registrar_en_bitacora


# ── Artículos ─────────────────────────────────────────────────────────────────

@api_view(['GET'])
def ListarArticulosABM(request):
    busqueda = request.query_params.get('buscar', '')
    articulos = Articulos.objects.all()

    if busqueda:
        articulos = articulos.filter(
            Q(nombre__icontains=busqueda) |
            Q(cod_art__icontains=busqueda) |
            Q(barra__icontains=busqueda)
        )

    data = articulos.values(
        'cod_art', 'nombre', 'precio_1', 'costo_ult', 'iva', 'stock', 'barra', 'rubro',
    )[:100]

    return Response({"status": "success", "data": list(data)})


@api_view(['POST'])
def GuardarArticulo(request):
    data    = request.data
    cod_art = data.get('cod_art')
    is_new  = data.get('is_new', False)

    if not cod_art:
        return Response({"status": "error", "mensaje": "El código de artículo es obligatorio."}, status=400)

    try:
        if is_new:
            if Articulos.objects.filter(cod_art=cod_art).exists():
                return Response({"status": "error", "mensaje": f"El código '{cod_art}' ya existe."}, status=400)
            articulo = Articulos(cod_art=cod_art)
            mensaje  = f"Artículo '{cod_art}' creado exitosamente."
        else:
            articulo = Articulos.objects.filter(cod_art=cod_art).first()
            if not articulo:
                return Response({"status": "error", "mensaje": "Artículo no encontrado."}, status=404)
            mensaje = f"Artículo '{cod_art}' actualizado."

        articulo.nombre    = data.get('nombre', articulo.nombre or '')
        articulo.barra     = data.get('barra', articulo.barra or '')
        articulo.rubro     = data.get('rubro', articulo.rubro or '')
        articulo.precio_1  = float(data.get('precio_1', articulo.precio_1 or 0))
        articulo.costo_ult = float(data.get('costo_ult', articulo.costo_ult or 0))
        articulo.iva       = float(data.get('iva', articulo.iva or 21))
        articulo.save()

        return Response({"status": "success", "mensaje": mensaje})
    except Exception as e:
        return Response({"status": "error", "mensaje": f"Error interno: {str(e)}"}, status=500)


# ── Rubros ────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def ListarRubros(request):
    try:
        rubros = ArticulosRubros.objects.all().values('codigo', 'nombre').order_by('codigo')
        return Response({"status": "success", "data": list(rubros)})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['POST'])
def GuardarRubro(request):
    data    = request.data
    codigo  = data.get('codigo')
    is_new  = data.get('is_new', False)

    if not codigo:
        return Response({"status": "error", "mensaje": "El código es obligatorio."}, status=400)

    try:
        if is_new:
            if ArticulosRubros.objects.filter(codigo=codigo).exists():
                return Response({"status": "error", "mensaje": f"El código '{codigo}' ya existe."}, status=400)
            rubro = ArticulosRubros(codigo=codigo)
        else:
            rubro = ArticulosRubros.objects.filter(codigo=codigo).first()
            if not rubro:
                return Response({"status": "error", "mensaje": "Rubro no encontrado."}, status=404)

        rubro.nombre = data.get('nombre', '').upper()
        rubro.save()
        return Response({"status": "success", "mensaje": "Rubro guardado."})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


# ── Subrubros ─────────────────────────────────────────────────────────────────

@api_view(['GET'])
def ListarSubRubros(request):
    try:
        subrubros = ArticulosSubrub.objects.all().values('codigo', 'nombre').order_by('codigo')
        return Response({"status": "success", "data": list(subrubros)})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['POST'])
def GuardarSubRubro(request):
    data   = request.data
    codigo = data.get('codigo')
    is_new = data.get('is_new', False)

    if not codigo:
        return Response({"status": "error", "mensaje": "El código es obligatorio."}, status=400)

    try:
        if is_new:
            if ArticulosSubrub.objects.filter(codigo=codigo).exists():
                return Response({"status": "error", "mensaje": f"El código '{codigo}' ya existe."}, status=400)
            subrubro = ArticulosSubrub(codigo=codigo)
        else:
            subrubro = ArticulosSubrub.objects.filter(codigo=codigo).first()
            if not subrubro:
                return Response({"status": "error", "mensaje": "Subrubro no encontrado."}, status=404)

        subrubro.nombre = data.get('nombre', '').upper()
        subrubro.save()
        return Response({"status": "success", "mensaje": "Subrubro guardado."})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


# ── Causas de ajuste de stock ─────────────────────────────────────────────────

@api_view(['POST'])
def InsertarNuevCausa(request):
    codigo  = request.data.get('codigo')
    detalle = request.data.get('detalle')
    try:
        if StockCausaemision.objects.filter(codigo=codigo).exists():
            return Response({"status": "error", "mensaje": "El código de causa ya existe."}, status=400)
        StockCausaemision.objects.create(codigo=codigo, detalle=detalle)
        return Response({"status": "success", "mensaje": "Causa guardada."}, status=201)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['POST'])
def ActualizarCausa(request):
    codigo  = request.data.get('codigo')
    detalle = request.data.get('detalle')
    try:
        causa = StockCausaemision.objects.filter(codigo=codigo).first()
        if not causa:
            return Response({"status": "error", "mensaje": "Causa no encontrada."}, status=404)
        causa.detalle = detalle
        causa.save()
        return Response({"status": "success", "mensaje": "Causa actualizada."})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


# ── NUEVO: Entrada manual de stock ────────────────────────────────────────────

@api_view(['POST'])
def RegistrarEntradaStock(request):
    """
    Entrada manual de stock (sin factura de compra).
    Replica Stock_Entrada.cs → barButtonItemSAVE_ItemClick.
    cod_comprob = 'IS'  (Ingreso Stock)

    Payload:
    {
      "cod_prov": 1,          // proveedor origen (requerido en legacy)
      "observac": "Motivo del ingreso",
      "cajero": 1,
      "usuario": "admin",
      "items": [
        { "cod_art": "ART001", "descripcion": "...", "cantidad": 10, "costo": 150.00 }
      ]
    }
    """
    data     = request.data
    cod_prov = int(data.get('cod_prov', 0))
    observac = str(data.get('observac', '')).strip()
    cajero   = int(data.get('cajero', 1))
    usuario  = str(data.get('usuario', 'admin'))
    items    = data.get('items', [])

    if not items:
        return Response({"status": "error", "mensaje": "Debe incluir al menos un artículo."}, status=400)
    if len(observac) < 2:
        return Response({"status": "error", "mensaje": "Ingrese un motivo/observación (mínimo 2 caracteres)."}, status=400)

    try:
        with transaction.atomic():
            # Siguiente número IS
            config_is = (
                TipocompCli.objects
                .select_for_update()
                .filter(cod_compro='IS')
                .first()
            )
            if not config_is:
                raise ValueError("Configure el tipo de comprobante 'IS' (Ingreso Stock) en tipocomp_cli.")

            nro_is = config_is.ultnro + 1
            config_is.ultnro = nro_is
            config_is.save(update_fields=['ultnro'])

            nuevo_movim = _siguiente_movim()
            _registrar_en_bitacora(nuevo_movim, cajero, '0001', usuario)

            # INSERT compras (cabecera) — igual que el legacy usa tabla compras para IS
            compra = Compras.objects.create(
                movim              = nuevo_movim,
                id_comprob         = config_is.id_compro,
                cod_comprob        = 'IS',
                nro_comprob        = nro_is,
                cod_prov           = cod_prov,
                fecha_comprob      = timezone.now().date(),
                fecha_vto          = timezone.now().date(),
                actualiz_stock     = 'S',
                observac           = observac,
                usuario            = usuario,
                fecha_mod          = timezone.now(),
                cajero             = cajero,
                procesado          = 0,
            )

            for item in items:
                cod_art  = str(item['cod_art'])
                cantidad = Decimal(str(item['cantidad']))
                costo    = Decimal(str(item.get('costo', 0)))

                ComprasDet.objects.create(
                    movim       = nuevo_movim,
                    id_comprob  = config_is.id_compro,
                    cod_comprob = 'IS',
                    nro_comprob = nro_is,
                    cod_articulo= cod_art,
                    nom_articulo= str(item.get('descripcion', ''))[:50],
                    cantidad    = cantidad,
                    precio_unit = costo,
                    total       = costo * cantidad,
                    cod_prov    = cod_prov,
                    procesado   = 0,
                )

                # Suma stock y actualiza costo
                Articulos.objects.filter(cod_art=cod_art).update(
                    stock    = F('stock') + cantidad,
                    costo_ult= costo,
                )

        return Response({
            "status":  "success",
            "mensaje": f"Entrada de stock IS N° {nro_is} generada. Stock actualizado.",
            "nro_is":  nro_is,
            "movim":   nuevo_movim,
        }, status=201)

    except ValueError as e:
        return Response({"status": "error", "mensaje": str(e)}, status=400)
    except Exception as e:
        return Response({"status": "error", "mensaje": f"Error interno: {str(e)}"}, status=500)


# ── NUEVO: Salida manual de stock ─────────────────────────────────────────────

@api_view(['POST'])
def RegistrarSalidaStock(request):
    """
    Salida manual de stock.
    Replica Stock_Salida.cs → barButtonItemSAVE_ItemClick.
    cod_comprob = 'SS'  (Salida Stock)

    Payload:
    {
      "observac": "Motivo obligatorio (mín. 2 chars)",
      "causa_emision": "",   // código de stock_causaemision, opcional
      "cajero": 1,
      "usuario": "admin",
      "items": [
        { "cod_art": "ART001", "descripcion": "...", "cantidad": 3 }
      ]
    }
    """
    data          = request.data
    observac      = str(data.get('observac', '')).strip()
    causa_emision = str(data.get('causa_emision', ''))
    cajero        = int(data.get('cajero', 1))
    usuario       = str(data.get('usuario', 'admin'))
    items         = data.get('items', [])

    if not items:
        return Response({"status": "error", "mensaje": "Debe incluir al menos un artículo."}, status=400)
    if len(observac) < 2:
        return Response({"status": "error", "mensaje": "Ingrese un motivo/observación (mínimo 2 caracteres)."}, status=400)

    try:
        with transaction.atomic():
            config_ss = (
                TipocompCli.objects
                .select_for_update()
                .filter(cod_compro='SS')
                .first()
            )
            if not config_ss:
                raise ValueError("Configure el tipo de comprobante 'SS' (Salida Stock) en tipocomp_cli.")

            nro_ss = config_ss.ultnro + 1
            config_ss.ultnro = nro_ss
            config_ss.save(update_fields=['ultnro'])

            nuevo_movim = _siguiente_movim()
            _registrar_en_bitacora(nuevo_movim, cajero, '0001', usuario)

            Compras.objects.create(
                movim          = nuevo_movim,
                id_comprob     = config_ss.id_compro,
                cod_comprob    = 'SS',
                nro_comprob    = nro_ss,
                cod_prov       = 0,
                fecha_comprob  = timezone.now().date(),
                fecha_vto      = timezone.now().date(),
                actualiz_stock = 'S',
                observac       = observac,
                remito_erp     = causa_emision,   # guarda causa de emisión igual que legacy
                usuario        = usuario,
                fecha_mod      = timezone.now(),
                cajero         = cajero,
                procesado      = 0,
            )

            for item in items:
                cod_art  = str(item['cod_art'])
                cantidad = Decimal(str(item['cantidad']))

                ComprasDet.objects.create(
                    movim       = nuevo_movim,
                    id_comprob  = config_ss.id_compro,
                    cod_comprob = 'SS',
                    nro_comprob = nro_ss,
                    cod_articulo= cod_art,
                    nom_articulo= str(item.get('descripcion', ''))[:50],
                    cantidad    = cantidad,
                    precio_unit = 0,
                    total       = 0,
                    cod_prov    = 0,
                    procesado   = 0,
                )

                # Resta stock
                Articulos.objects.filter(cod_art=cod_art).update(
                    stock=F('stock') - cantidad
                )

        return Response({
            "status":  "success",
            "mensaje": f"Salida de stock SS N° {nro_ss} generada. Stock actualizado.",
            "nro_ss":  nro_ss,
            "movim":   nuevo_movim,
        }, status=201)

    except ValueError as e:
        return Response({"status": "error", "mensaje": str(e)}, status=400)
    except Exception as e:
        return Response({"status": "error", "mensaje": f"Error interno: {str(e)}"}, status=500)


@api_view(['GET'])
def ListarCausasEmision(request):
    """Devuelve las causas de emisión para salidas de stock."""
    try:
        causas = StockCausaemision.objects.all().values('codigo', 'detalle').order_by('codigo')
        return Response({"status": "success", "data": list(causas)})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)