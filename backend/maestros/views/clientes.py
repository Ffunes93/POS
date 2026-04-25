from django.db.models import Max, Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import Clientes


@api_view(['GET'])
def ListarClientes(request):
    busqueda = request.query_params.get('buscar', '')
    clientes = Clientes.objects.all()

    if busqueda:
        clientes = clientes.filter(
            Q(denominacion__icontains=busqueda) | Q(nro_cuit__icontains=busqueda)
        )

    data = clientes.values(
        'cod_cli', 'denominacion', 'nro_cuit', 'domicilio', 'telefono',
        'cond_iva', 'credito_cc', 'estado_baja', 'lista_precio',
    )[:100]

    return Response({"status": "success", "data": list(data)}, status=status.HTTP_200_OK)


@api_view(['POST'])
def GuardarCliente(request):
    data = request.data
    cod_cli = data.get('cod_cli')

    if cod_cli:
        cliente = Clientes.objects.filter(cod_cli=cod_cli).first()
        if not cliente:
            return Response(
                {"status": "error", "mensaje": "Cliente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        mensaje = f"Cliente '{cliente.denominacion}' actualizado."
    else:
        max_id = Clientes.objects.aggregate(Max('cod_cli'))['cod_cli__max'] or 0
        cod_cli = max_id + 1
        cliente = Clientes(cod_cli=cod_cli)
        mensaje = f"Cliente creado con el código {cod_cli}."

    cliente.denominacion = data.get('denominacion', cliente.denominacion or '')
    cliente.nro_cuit = data.get('nro_cuit', cliente.nro_cuit or '')
    cliente.domicilio = data.get('domicilio', cliente.domicilio or '')
    cliente.telefono = data.get('telefono', cliente.telefono or '')
    cliente.cond_iva = int(data.get('cond_iva', cliente.cond_iva or 5))
    cliente.estado_baja = int(data.get('estado_baja', cliente.estado_baja or 0))
    cliente.credito_cc = data.get('credito_cc', cliente.credito_cc or 0)
    cliente.save()

    return Response({"status": "success", "mensaje": mensaje}, status=status.HTTP_200_OK)
