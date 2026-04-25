from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import Articulos, ArticulosRubros, ArticulosSubrub, StockCausaemision


# ── Artículos ────────────────────────────────────────────────────────────────

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

    return Response({"status": "success", "data": list(data)}, status=status.HTTP_200_OK)


@api_view(['POST'])
def GuardarArticulo(request):
    data = request.data
    cod_art = data.get('cod_art')
    is_new = data.get('is_new', False)

    if not cod_art:
        return Response(
            {"status": "error", "mensaje": "El código de artículo es obligatorio."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        if is_new:
            if Articulos.objects.filter(cod_art=cod_art).exists():
                return Response(
                    {"status": "error", "mensaje": f"El código '{cod_art}' ya existe."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            articulo = Articulos(cod_art=cod_art)
            mensaje = f"Artículo '{cod_art}' creado exitosamente."
        else:
            articulo = Articulos.objects.filter(cod_art=cod_art).first()
            if not articulo:
                return Response(
                    {"status": "error", "mensaje": "Artículo no encontrado."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            mensaje = f"Artículo '{cod_art}' actualizado."

        articulo.nombre = data.get('nombre', articulo.nombre or '')
        articulo.barra = data.get('barra', articulo.barra or '')
        articulo.rubro = data.get('rubro', articulo.rubro or '')
        articulo.precio_1 = float(data.get('precio_1', articulo.precio_1 or 0))
        articulo.costo_ult = float(data.get('costo_ult', articulo.costo_ult or 0))
        articulo.iva = float(data.get('iva', articulo.iva or 21))
        articulo.save()

        return Response({"status": "success", "mensaje": mensaje}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"status": "error", "mensaje": f"Error interno: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ── Rubros ───────────────────────────────────────────────────────────────────

@api_view(['GET'])
def ListarRubros(request):
    try:
        rubros = ArticulosRubros.objects.all().values('codigo', 'nombre').order_by('codigo')
        return Response({"status": "success", "data": list(rubros)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def GuardarRubro(request):
    data = request.data
    codigo = data.get('codigo')
    is_new = data.get('is_new', False)

    if not codigo:
        return Response(
            {"status": "error", "mensaje": "El código es obligatorio."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        if is_new:
            if ArticulosRubros.objects.filter(codigo=codigo).exists():
                return Response(
                    {"status": "error", "mensaje": f"El código '{codigo}' ya existe."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            rubro = ArticulosRubros(codigo=codigo)
        else:
            rubro = ArticulosRubros.objects.filter(codigo=codigo).first()
            if not rubro:
                return Response(
                    {"status": "error", "mensaje": "Rubro no encontrado."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        rubro.nombre = data.get('nombre', '').upper()
        rubro.save()
        return Response({"status": "success", "mensaje": "Rubro guardado."}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── Subrubros ────────────────────────────────────────────────────────────────

@api_view(['GET'])
def ListarSubRubros(request):
    try:
        subrubros = ArticulosSubrub.objects.all().values('codigo', 'nombre').order_by('codigo')
        return Response({"status": "success", "data": list(subrubros)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def GuardarSubRubro(request):
    data = request.data
    codigo = data.get('codigo')
    is_new = data.get('is_new', False)

    if not codigo:
        return Response(
            {"status": "error", "mensaje": "El código es obligatorio."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        if is_new:
            if ArticulosSubrub.objects.filter(codigo=codigo).exists():
                return Response(
                    {"status": "error", "mensaje": f"El código '{codigo}' ya existe."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subrubro = ArticulosSubrub(codigo=codigo)
        else:
            subrubro = ArticulosSubrub.objects.filter(codigo=codigo).first()
            if not subrubro:
                return Response(
                    {"status": "error", "mensaje": "Subrubro no encontrado."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        subrubro.nombre = data.get('nombre', '').upper()
        subrubro.save()
        return Response({"status": "success", "mensaje": "Subrubro guardado."}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── Causas de ajuste de stock ────────────────────────────────────────────────

@api_view(['POST'])
def InsertarNuevCausa(request):
    codigo = request.data.get('codigo')
    detalle = request.data.get('detalle')

    try:
        if StockCausaemision.objects.filter(codigo=codigo).exists():
            return Response(
                {"status": "error", "mensaje": "El código de causa ya existe."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        StockCausaemision.objects.create(codigo=codigo, detalle=detalle)
        return Response(
            {"status": "success", "mensaje": "Causa guardada."},
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def ActualizarCausa(request):
    codigo = request.data.get('codigo')
    detalle = request.data.get('detalle')

    try:
        causa = StockCausaemision.objects.filter(codigo=codigo).first()
        if not causa:
            return Response(
                {"status": "error", "mensaje": "Causa no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        causa.detalle = detalle
        causa.save()
        return Response({"status": "success", "mensaje": "Causa actualizada."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
