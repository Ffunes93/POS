from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import Parametros, TipocompCli, FormaPago, Listasprecios
from ..serializers import ParametrosSerializer, TipocompCliSerializer


# ── Parámetros generales ──────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def GestionarParametros(request):
    parametro = Parametros.objects.first()

    if request.method == 'GET':
        if not parametro:
            return Response(
                {"status": "error", "mensaje": "No hay parámetros configurados."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {"status": "success", "data": ParametrosSerializer(parametro).data},
            status=status.HTTP_200_OK,
        )

    # POST: crea o actualiza
    if parametro:
        serializer = ParametrosSerializer(parametro, data=request.data, partial=True)
    else:
        serializer = ParametrosSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response({"status": "success", "mensaje": "Parámetros guardados."})
    return Response(
        {"status": "error", "errores": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


# ── Tipos de comprobante ──────────────────────────────────────────────────────

@api_view(['GET', 'POST', 'PUT'])
def GestionarTipocompCli(request):
    if request.method == 'GET':
        tipos = TipocompCli.objects.all().order_by('id_compro')
        return Response(
            {"status": "success", "data": TipocompCliSerializer(tipos, many=True).data},
            status=status.HTTP_200_OK,
        )

    if request.method == 'POST':
        serializer = TipocompCliSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "success", "mensaje": "Tipo de comprobante creado."},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"status": "error", "errores": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # PUT: solo permite modificar ultnro por seguridad
    id_compro = request.data.get('id_compro')
    try:
        tipo = TipocompCli.objects.get(id_compro=id_compro)
        if 'ultnro' not in request.data:
            return Response(
                {"status": "error", "mensaje": "No se envió el nuevo número."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tipo.ultnro = request.data['ultnro']
        tipo.save(update_fields=['ultnro'])
        return Response(
            {"status": "success", "mensaje": f"Contador del comprobante {tipo.cod_compro} actualizado."},
        )
    except TipocompCli.DoesNotExist:
        return Response(
            {"status": "error", "mensaje": "Comprobante no encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )


# ── Formas de pago ────────────────────────────────────────────────────────────

@api_view(['GET'])
def ListarFormasPago(request):
    formas = FormaPago.objects.all().values('codigo', 'descripcion', 'activa', 'moneda')
    return Response({"status": "success", "data": list(formas)}, status=status.HTTP_200_OK)


@api_view(['POST'])
def GuardarFormaPago(request):
    data = request.data
    codigo = data.get('codigo')
    is_new = data.get('is_new', False)

    if not codigo:
        return Response(
            {"status": "error", "mensaje": "El código es obligatorio."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        codigo = codigo.upper()[:3]

        if is_new:
            if FormaPago.objects.filter(codigo=codigo).exists():
                return Response(
                    {"status": "error", "mensaje": f"El código '{codigo}' ya existe."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            forma = FormaPago(codigo=codigo)
            mensaje = f"Forma de pago '{codigo}' creada."
        else:
            forma = FormaPago.objects.filter(codigo=codigo).first()
            if not forma:
                return Response(
                    {"status": "error", "mensaje": "Forma de pago no encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            mensaje = f"Forma de pago '{codigo}' actualizada."

        forma.descripcion = data.get('descripcion', forma.descripcion or '')
        forma.activa = int(data.get('activa', getattr(forma, 'activa', 1)))
        forma.moneda = int(data.get('moneda', forma.moneda or 1))
        forma.save()

        return Response({"status": "success", "mensaje": mensaje}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"status": "error", "mensaje": f"Error interno: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ── Listas de precios ─────────────────────────────────────────────────────────

@api_view(['POST'])
def ActualizarListaPrecio(request):
    _nombre = request.data.get('_nombre')
    _lis = request.data.get('_lis')

    if not _nombre or not _lis:
        return Response(
            {"status": "error", "mensaje": "Faltan parámetros (_nombre, _lis)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        lista = Listasprecios.objects.filter(codigo=_lis).first()
        if not lista:
            return Response(
                {"status": "error", "mensaje": "Lista de precios no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        lista.nombrelista = _nombre
        lista.save()
        return Response({"status": "success", "mensaje": "Lista actualizada."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── Promociones ───────────────────────────────────────────────────────────────

@api_view(['POST'])
def InsertarNuevaPromo(request):
    # TODO: implementar cuando se diseñe el módulo de promociones completo
    return Response(
        {"status": "success", "mensaje": "Módulo de promociones pendiente de implementación."},
        status=status.HTTP_200_OK,
    )
