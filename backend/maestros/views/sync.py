from rest_framework.views import APIView
from rest_framework.response import Response

from ..models import (
    Articulos, Clientes, Usuarios, Promos, PromosDet,
    ArticulosBom, Listasprecios, Descuentos, CondIva,
    FormaPago, ArticulosRubros, ArticulosSubrub, Parametros, TipocompCli,
)
from ..serializers import (
    ArticuloLegacySerializer, ClienteLegacySerializer, VendedorLegacySerializer,
    PromoLegacySerializer, PromoDetLegacySerializer, KitLegacySerializer,
    ListaPrecioSerializer, DescuentoSerializer, CondIvaSerializer,
    FormaPagoSerializer, RubroSerializer, SubRubroSerializer,
    ParametrosSerializer, TipocompCliSerializer,
)
from .utils import filtrar_por_fecha


class GetArticulosJSON(APIView):
    def get(self, request):
        qs = Articulos.objects.all()
        cod = request.query_params.get('CodigoGenerico', '')
        if cod:
            qs = qs.filter(cod_art__icontains=cod)
        qs = filtrar_por_fecha(qs, 'fecha_mod', request.query_params.get('FechaModificacion', ''))
        return Response(ArticuloLegacySerializer(qs, many=True).data)


class GetClientesJSON(APIView):
    def get(self, request):
        qs = Clientes.objects.all()
        cod = request.query_params.get('CodigoCliente', '')
        if cod:
            qs = qs.filter(cod_cli=cod)
        qs = filtrar_por_fecha(qs, 'fecha_mod', request.query_params.get('FechaModificacion', ''))
        return Response(ClienteLegacySerializer(qs, many=True).data)


class GetVendedoresJSON(APIView):
    def get(self, request):
        qs = Usuarios.objects.filter(vendedor=1, no_activo=0)
        return Response(VendedorLegacySerializer(qs, many=True).data)


class GetPromocionesJSON(APIView):
    def get(self, request):
        return Response(PromoLegacySerializer(Promos.objects.all(), many=True).data)


class GetPromocionesDetJSON(APIView):
    def get(self, request):
        return Response(PromoDetLegacySerializer(PromosDet.objects.all(), many=True).data)


class GetKitsJSON(APIView):
    def get(self, request):
        return Response(KitLegacySerializer(ArticulosBom.objects.all(), many=True).data)


class GetListasPreciosJSON(APIView):
    def get(self, request):
        return Response(ListaPrecioSerializer(Listasprecios.objects.all(), many=True).data)


class GetDescuentosJSON(APIView):
    def get(self, request):
        return Response(DescuentoSerializer(Descuentos.objects.all(), many=True).data)


class GetCondIvaJSON(APIView):
    def get(self, request):
        return Response(CondIvaSerializer(CondIva.objects.all(), many=True).data)


class GetFormaPagoJSON(APIView):
    def get(self, request):
        return Response(FormaPagoSerializer(FormaPago.objects.all(), many=True).data)


class GetRubrosJSON(APIView):
    def get(self, request):
        return Response(RubroSerializer(ArticulosRubros.objects.all(), many=True).data)


class GetSubRubrosJSON(APIView):
    def get(self, request):
        return Response(SubRubroSerializer(ArticulosSubrub.objects.all(), many=True).data)


class GetParametrosJSON(APIView):
    def get(self, request):
        return Response(ParametrosSerializer(Parametros.objects.all(), many=True).data)
