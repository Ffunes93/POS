from rest_framework import serializers
from .models import (
    Articulos, Clientes, Usuarios, Promos, PromosDet, ArticulosBom,
    Listasprecios, Descuentos, CondIva, FormaPago, ArticulosRubros,
    ArticulosSubrub, Parametros, TipocompCli,
)


# ── Catálogos / sync ──────────────────────────────────────────────────────────

class ArticuloLegacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Articulos
        fields = '__all__'

class ClienteLegacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Clientes
        fields = '__all__'

class VendedorLegacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuarios
        fields = ['id', 'nombrelogin', 'nombre', 'vendedor', 'no_activo']

class PromoLegacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Promos
        fields = '__all__'

class PromoDetLegacySerializer(serializers.ModelSerializer):
    class Meta:
        model = PromosDet
        fields = '__all__'

class KitLegacySerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticulosBom
        fields = '__all__'

class ListaPrecioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listasprecios
        fields = '__all__'

class DescuentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Descuentos
        fields = '__all__'

class CondIvaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CondIva
        fields = '__all__'

class FormaPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormaPago
        fields = '__all__'

class RubroSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticulosRubros
        fields = '__all__'

class SubRubroSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticulosSubrub
        fields = '__all__'

class ParametrosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parametros
        fields = '__all__'

class TipocompCliSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipocompCli
        fields = '__all__'


# ── Ingreso de comprobante de ventas ──────────────────────────────────────────
# Mapeados 1:1 con los INSERT del legacy (Ven_Factura.cs, genera_comprobante).

class ComprobanteItemSerializer(serializers.Serializer):
    """Mapea con ventas_det. Campos de detVentas (DataTable) del legacy."""
    Item_CodigoArticulo       = serializers.CharField(max_length=40)
    Item_DescripArticulo      = serializers.CharField(max_length=100, required=False,
                                                       allow_blank=True, default='')
    Item_CantidadUM1          = serializers.DecimalField(max_digits=10, decimal_places=3)
    Item_PrecioUnitario       = serializers.DecimalField(max_digits=12, decimal_places=2)
    # precio_unit_base: precio sin recargo de tarjeta
    Item_PrecioUnitarioBase   = serializers.DecimalField(max_digits=12, decimal_places=4,
                                                          required=False, default=0)
    # IVA
    Item_TasaIVAInscrip       = serializers.DecimalField(max_digits=5, decimal_places=2,
                                                          required=False, default=21)
    Item_ImporteIVAInscrip    = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                          required=False, default=0)
    Item_ImporteIVABase       = serializers.DecimalField(max_digits=14, decimal_places=2,
                                                          required=False, default=0)
    # Totales de línea
    Item_ImporteTotal         = serializers.DecimalField(max_digits=12, decimal_places=2)
    Item_Importe              = serializers.DecimalField(max_digits=14, decimal_places=2,
                                                          required=False, default=0)
    # Descuentos por ítem
    Item_ImporteDescComercial = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                          required=False, default=0)
    Item_PorcentajeDescuento  = serializers.DecimalField(max_digits=4, decimal_places=2,
                                                          required=False, default=0)
    Item_DescuentoIVA         = serializers.DecimalField(max_digits=11, decimal_places=2,
                                                          required=False, default=0)
    # Impuesto interno unitario (impuesto_base del legacy)
    Item_ImpuestoUnitario     = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                          required=False, default=0)
    # Costo del ítem
    Item_Costo                = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                          required=False, default=0)
    # Flags: 0=normal, 1=artículo en promoción
    Item_EsPromo              = serializers.IntegerField(required=False, default=0)
    # es_kit(combo): 0=simple, 1=kit → descontar sub-items de articulos_bom
    Item_EsKit                = serializers.IntegerField(required=False, default=0)
    # item_libre: guarda cod_promo cuando es_promo=1
    Item_CodigoPromo          = serializers.CharField(max_length=45, required=False,
                                                       allow_blank=True, default='')


class ComprobanteMedioPagoSerializer(serializers.Serializer):
    """
    Mapea con cheq_tarj_cli (EFE, TAR, CHE, TCR, TRF, MPA, DEV, PWQ, FYD)
    y con cta_cte_cli (CTA).  Campos de detpagos (DataTable) del legacy.
    """
    MedioPago               = serializers.CharField(max_length=10, required=False,
                                                     allow_blank=True, default='EFE')
    MedioPago_Importe       = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                        required=False, default=0)
    MedioPago_CodPagoDet    = serializers.IntegerField(required=False, default=0)
    MedioPago_Referencia    = serializers.CharField(max_length=100, required=False,
                                                     allow_blank=True, default='')
    MedioPago_FechaVencimiento = serializers.DateTimeField(required=False,
                                                            allow_null=True, default=None)
    MedioPago_CantidadCuotas = serializers.IntegerField(required=False, default=0)
    MedioPago_NroCupon      = serializers.CharField(max_length=50, required=False,
                                                     allow_blank=True, default='0')
    MedioPago_NumeroCheque  = serializers.CharField(max_length=50, required=False,
                                                     allow_blank=True, default='0')
    MedioPago_Entidad       = serializers.CharField(max_length=20, required=False,
                                                     allow_blank=True, default='')
    MedioPago_CodigoBanco   = serializers.CharField(max_length=20, required=False,
                                                     allow_blank=True, default='')
    MedioPago_CodigoPago    = serializers.CharField(max_length=20, required=False,
                                                     allow_blank=True, default='')
    MedioPago_Recargo       = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                        required=False, default=0)
    MedioPago_RecargoIVA    = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                        required=False, default=0)
    MedioPago_Recargo10     = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                        required=False, default=0)
    MedioPago_RecargoIVA10  = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                        required=False, default=0)
    MedioPago_Recargo0      = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                        required=False, default=0)
    MedioPago_IdPayway      = serializers.CharField(max_length=100, required=False,
                                                     allow_blank=True, default='')


class ComprobantePromoSerializer(serializers.Serializer):
    """Mapea con ventas_promo."""
    Promo_Codigo     = serializers.CharField(max_length=40)
    Promo_Detalle    = serializers.CharField(max_length=60)
    Promo_Importe    = serializers.DecimalField(max_digits=12, decimal_places=2)
    Promo_IvaImporte = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                 required=False, default=0)
    Promo_CodigoErp  = serializers.CharField(max_length=20, required=False,
                                              allow_blank=True, default='')


class ComprobanteDescuentoSerializer(serializers.Serializer):
    """Mapea con ventas_descuentos."""
    Descu_Codigo     = serializers.CharField(max_length=40)
    Descu_Detalle    = serializers.CharField(max_length=60)
    Descu_Importe    = serializers.DecimalField(max_digits=12, decimal_places=2)
    Descu_IvaImporte = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                 required=False, default=0)
    Descu_Tasa       = serializers.DecimalField(max_digits=5, decimal_places=2,
                                                 required=False, default=0)
    Descu_CodigoErp  = serializers.CharField(max_length=20, required=False,
                                              allow_blank=True, default='')


class ComprobanteRegimenSerializer(serializers.Serializer):
    """Mapea con ventas_regimenes (percepciones IIBB, CABA, BsAs, 5329)."""
    Regimen_Detalle       = serializers.CharField(max_length=255)
    Regimen_Importe       = serializers.DecimalField(max_digits=10, decimal_places=2)
    Regimen_BaseImponible = serializers.DecimalField(max_digits=10, decimal_places=2,
                                                      required=False, default=0)


class IngresoComprobanteSerializer(serializers.Serializer):
    """
    Cabecera completa del comprobante.
    Campos mapeados 1:1 con el INSERT INTO ventas del legacy (línea 160813, Ven_Factura.cs).
    """
    # Identificación
    Comprobante_Tipo         = serializers.CharField(max_length=2)
    Comprobante_Letra        = serializers.CharField(max_length=2)
    Comprobante_PtoVenta     = serializers.CharField(max_length=5)
    Comprobante_Numero       = serializers.CharField(max_length=20)
    Cliente_Codigo           = serializers.CharField(max_length=20)
    Comprobante_FechaEmision      = serializers.DateTimeField()
    Comprobante_FechaVencimiento  = serializers.DateTimeField(required=False,
                                                               allow_null=True, default=None)

    # ── Importes (orden del legacy) ────────────────────────────────────────────
    # neto        = txtSubTotal  = subtotal ANTES de descuentos
    Comprobante_Neto              = serializers.DecimalField(max_digits=11, decimal_places=2,
                                                              required=False, default=0)
    # iva_1       = txtIVA
    Comprobante_IVA               = serializers.DecimalField(max_digits=11, decimal_places=2,
                                                              required=False, default=0)
    # total (base neta impositiva) = neto - descuento + recargos
    # Si no se envía se calcula automáticamente en la vista
    Comprobante_TotalNeto         = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                              required=False, default=None,
                                                              allow_null=True)
    # tot_general = txtTotal = lo que paga el cliente
    Comprobante_ImporteTotal      = serializers.DecimalField(max_digits=12, decimal_places=2)
    Comprobante_Exento            = serializers.DecimalField(max_digits=11, decimal_places=2,
                                                              required=False, default=0)
    # Descuentos cabecera
    Comprobante_Descuento         = serializers.DecimalField(max_digits=11, decimal_places=2,
                                                              required=False, default=0)
    Comprobante_DescuentoIVA      = serializers.DecimalField(max_digits=11, decimal_places=2,
                                                              required=False, default=0)
    Comprobante_DtosPorItems      = serializers.DecimalField(max_digits=11, decimal_places=2,
                                                              required=False, default=0)
    Comprobante_DtosPorItemsIVA   = serializers.DecimalField(max_digits=11, decimal_places=2,
                                                              required=False, default=0)
    # Recargos por medio de pago
    Comprobante_Recargos          = serializers.DecimalField(max_digits=11, decimal_places=2,
                                                              required=False, default=0)
    Comprobante_RecargosIVA       = serializers.DecimalField(max_digits=11, decimal_places=2,
                                                              required=False, default=0)
    # Percepciones
    Comprobante_Percepciones      = serializers.DecimalField(max_digits=11, decimal_places=2,
                                                              required=False, default=0)
    Comprobante_PerceCABA         = serializers.DecimalField(max_digits=11, decimal_places=2,
                                                              required=False, default=0)
    Comprobante_PerceBsAs         = serializers.DecimalField(max_digits=11, decimal_places=2,
                                                              required=False, default=0)
    Comprobante_Perce5329         = serializers.DecimalField(max_digits=11, decimal_places=2,
                                                              required=False, default=0)
    # Impuestos internos
    Comprobante_ImpuestosInternos = serializers.DecimalField(max_digits=11, decimal_places=2,
                                                              required=False, default=0)
    # Costo total
    Comprobante_CostoGeneral      = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                              required=False, default=0)
    Comprobante_CostoCompleto     = serializers.IntegerField(required=False, default=0)

    # Opcionales con defaults
    Comprobante_Moneda     = serializers.CharField(required=False, default='1')
    Vendedor_Codigo        = serializers.IntegerField(required=False, default=1)
    Comprobante_CondVenta  = serializers.CharField(required=False, default='1')
    Comprobante_Observac   = serializers.CharField(max_length=100, required=False,
                                                    allow_blank=True, default='')
    Comprobante_Zeta       = serializers.IntegerField(required=False, default=0)
    Comprobante_Usuario    = serializers.CharField(max_length=20, required=False,
                                                    default='admin', allow_blank=True)
    cajero                 = serializers.IntegerField(required=False, default=1)
    nro_caja               = serializers.IntegerField(required=False, default=1)

    # Cliente varios (cod_cli == 2): datos del comprador anónimo → ventas_extras
    ClienteVarios_Documento = serializers.CharField(max_length=50, required=False,
                                                     allow_blank=True, default='')
    ClienteVarios_Nombre    = serializers.CharField(max_length=100, required=False,
                                                     allow_blank=True, default='')
    ClienteVarios_Domicilio = serializers.CharField(max_length=100, required=False,
                                                     allow_blank=True, default='')

    # Relaciones anidadas
    Comprobante_Items       = ComprobanteItemSerializer(many=True)
    Comprobante_MediosPago  = ComprobanteMedioPagoSerializer(many=True,
                                                               required=False, default=list)
    Comprobante_Promos      = ComprobantePromoSerializer(many=True,
                                                          required=False, default=list)
    Comprobante_Descuentos  = ComprobanteDescuentoSerializer(many=True,
                                                              required=False, default=list)
    Comprobante_Regimenes   = ComprobanteRegimenSerializer(many=True,
                                                            required=False, default=list)


# ── Cajas ─────────────────────────────────────────────────────────────────────

class AbrirCajaSerializer(serializers.Serializer):
    cajero_id           = serializers.IntegerField()
    saldo_ini_billetes  = serializers.DecimalField(max_digits=12, decimal_places=2)
    saldo_ini_cupones   = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                    required=False, default=0)

class CerrarCajaSerializer(serializers.Serializer):
    cajero_id            = serializers.IntegerField()
    saldo_final_billetes = serializers.DecimalField(max_digits=12, decimal_places=2)
    saldo_final_cupones  = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                     required=False, default=0)
    otros_ingresos       = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                     required=False, default=0)
    otros_egresos        = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                     required=False, default=0)
    deja_billetes        = serializers.DecimalField(max_digits=12, decimal_places=2,
                                                     required=False, default=0)


# ── Usuarios ──────────────────────────────────────────────────────────────────

class CrearUsuarioSerializer(serializers.Serializer):
    nombre        = serializers.CharField(max_length=50)
    apellido      = serializers.CharField(max_length=50, required=False,
                                           allow_blank=True, default='')
    nombrelogin   = serializers.CharField(max_length=50)
    password      = serializers.CharField(max_length=50)
    email         = serializers.EmailField(required=False, allow_blank=True, default='')
    nivel_usuario = serializers.IntegerField(default=1)
    cajero        = serializers.IntegerField(default=1)
    vendedor      = serializers.IntegerField(default=1)
    autorizador   = serializers.IntegerField(default=0)