from rest_framework import serializers
from .models import (
    Articulos, Clientes, Usuarios, Promos, PromosDet, ArticulosBom, 
    Listasprecios, Descuentos, CondIva, FormaPago, ArticulosRubros, 
    ArticulosSubrub, Parametros, TipocompCli
)

class ArticuloLegacySerializer(serializers.ModelSerializer):
    class Meta: model = Articulos; fields = '__all__'

class ClienteLegacySerializer(serializers.ModelSerializer):
    class Meta: model = Clientes; fields = '__all__'

class VendedorLegacySerializer(serializers.ModelSerializer):
    class Meta: model = Usuarios; fields = ['id', 'nombrelogin', 'nombre', 'vendedor', 'no_activo']

class PromoLegacySerializer(serializers.ModelSerializer):
    class Meta: model = Promos; fields = '__all__'

class PromoDetLegacySerializer(serializers.ModelSerializer):
    class Meta: model = PromosDet; fields = '__all__'

class KitLegacySerializer(serializers.ModelSerializer):
    class Meta: model = ArticulosBom; fields = '__all__'

class ListaPrecioSerializer(serializers.ModelSerializer):
    class Meta: model = Listasprecios; fields = '__all__'

class DescuentoSerializer(serializers.ModelSerializer):
    class Meta: model = Descuentos; fields = '__all__'

class CondIvaSerializer(serializers.ModelSerializer):
    class Meta: model = CondIva; fields = '__all__'

class FormaPagoSerializer(serializers.ModelSerializer):
    class Meta: model = FormaPago; fields = '__all__'

class RubroSerializer(serializers.ModelSerializer):
    class Meta: model = ArticulosRubros; fields = '__all__'

class SubRubroSerializer(serializers.ModelSerializer):
    class Meta: model = ArticulosSubrub; fields = '__all__'

class ParametrosSerializer(serializers.ModelSerializer):
    class Meta: model = Parametros; fields = '__all__'


class ComprobanteItemSerializer(serializers.Serializer):
    Item_CodigoArticulo = serializers.CharField(max_length=40)
    Item_DescripArticulo = serializers.CharField(max_length=100, required=False, allow_blank=True)
    Item_CantidadUM1 = serializers.DecimalField(max_digits=10, decimal_places=3)
    Item_PrecioUnitario = serializers.DecimalField(max_digits=12, decimal_places=2)
    Item_TasaIVAInscrip = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=0)
    Item_ImporteIVAInscrip = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    Item_ImporteTotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    Item_ImporteDescComercial = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    Item_Importe = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, default=0)

class ComprobanteMedioPagoSerializer(serializers.Serializer):
    MedioPago = serializers.CharField(max_length=10, required=False, allow_blank=True)
    MedioPago_Importe = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    # Podés agregar más campos de la tarjeta/cheque si los necesitás validar

class IngresoComprobanteSerializer(serializers.Serializer):
    # Cabecera
    Comprobante_Tipo = serializers.CharField(max_length=2)
    Comprobante_Letra = serializers.CharField(max_length=2)
    Comprobante_PtoVenta = serializers.CharField(max_length=5)
    Comprobante_Numero = serializers.CharField(max_length=20)
    Cliente_Codigo = serializers.CharField(max_length=20)
    Comprobante_FechaEmision = serializers.DateTimeField()
    Comprobante_FechaVencimiento = serializers.DateTimeField(required=False)
    Comprobante_ImporteTotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Opcionales con valores por defecto
    Comprobante_Moneda = serializers.CharField(required=False, default="1")
    Vendedor_Codigo = serializers.CharField(required=False, default="1")
    Comprobante_CondVenta = serializers.CharField(required=False, default="1")
    
    # Relaciones anidadas
    Comprobante_Items = ComprobanteItemSerializer(many=True)
    Comprobante_MediosPago = ComprobanteMedioPagoSerializer(many=True, required=False)

class AbrirCajaSerializer(serializers.Serializer):
    cajero_id = serializers.IntegerField()
    saldo_ini_billetes = serializers.DecimalField(max_digits=12, decimal_places=2)
    saldo_ini_cupones = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)

class CerrarCajaSerializer(serializers.Serializer):
    cajero_id = serializers.IntegerField()
    saldo_final_billetes = serializers.DecimalField(max_digits=12, decimal_places=2)
    saldo_final_cupones = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    otros_ingresos = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    otros_egresos = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    deja_billetes = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)

class CrearUsuarioSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=50)
    apellido = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    nombrelogin = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=50)
    email = serializers.EmailField(required=False, allow_blank=True, default='')
    nivel_usuario = serializers.IntegerField(default=1)
    cajero = serializers.IntegerField(default=1) # 1 = Es cajero
    vendedor = serializers.IntegerField(default=1) # 1 = Es vendedor
    autorizador = serializers.IntegerField(default=0)

class ParametrosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parametros
        fields = '__all__'

class TipocompCliSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipocompCli
        fields = '__all__'