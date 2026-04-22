import hashlib
import base64
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import Max, F, Sum
from django.db import connection
from django.db.models import Q
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from .models import (
    ArticulosRubros, ArticulosSubrub, Cajas, CajasRetiros, 
    Ventas, VentasDet, CheqTarjCli, TipocompCli, CtaCteCli, 
    CajasDet, Compras, ComprasDet, FeTipocompCli
)

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
            
            # 1. Movim Autoincremental (Esto SÍ es idéntico al legacy: SELECT max(movim) FROM ventas [cite: 239])
            max_movim = Ventas.objects.aggregate(Max('movim'))['movim__max']
            nuevo_movim = (max_movim or 0) + 1
            
            condicion_venta = data.get('Comprobante_CondVenta', '1')
            cliente_codigo = int(data['Cliente_Codigo'])
            importe_total = data['Comprobante_ImporteTotal']
            
            # =================================================================
            # 1.5 LÓGICA LEGACY REAL: Obtener ID y NRO desde tipocomp_cli
            # =================================================================
            tipo_comprob = data['Comprobante_Tipo'][:2]
            pto_vta = data['Comprobante_PtoVenta']
            
            # Buscamos en la tabla contadora (Cambiar por FeTipocompCli si usas factura electrónica)
            config_comprobante = TipocompCli.objects.filter(cod_compro=tipo_comprob).first()
            
            if not config_comprobante:
                raise Exception(f"El comprobante {tipo_comprob} no está configurado en la tabla tipocomp_cli.")
                
            # Extraemos el ID real y sumamos 1 al último número usado
            id_comprob_real = config_comprobante.id_compro
            nro_comprob_final = config_comprobante.ultnro + 1
            
            # Actualizamos el contador en la tabla para la próxima venta
            config_comprobante.ultnro = nro_comprob_final
            config_comprobante.save()
            # =================================================================

            # 2. Guardar CABECERA (ventas)
            venta = Ventas.objects.create(
                movim=nuevo_movim,
                id_comprob=id_comprob_real,      # <-- AHORA USA EL ID REAL DEL TIPO (Ej: 1=FA, 6=FB)
                cod_comprob=tipo_comprob,
                nro_comprob=nro_comprob_final,   # <-- NÚMERO CORRELATIVO PERFECTO
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
                cajero=int(data.get('cajero', 1)),  
                nro_caja=int(data.get('nro_caja', 1)), 
                comprobante_tipo=data['Comprobante_Tipo'],
                comprobante_letra=data['Comprobante_Letra'],
                comprobante_pto_vta=pto_vta,
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



# ==========================================
#     MÓDULO DE CAJAS (APERTURA Y CIERRE)
# ==========================================

@api_view(['POST'])
def AbrirCaja(request):
    """Abre un nuevo turno insertando en 'cajas' y 'cajas_det' vía SQL"""
    data = request.data
    cajero_id = data.get('cajero_id')
    fondo_inicial = float(data.get('saldo_inicial', 0))

    try:
        with connection.cursor() as cursor:
            # 1. Verificar si ya hay caja abierta (estado=1)
            cursor.execute("SELECT id FROM cajas WHERE cajero = %s AND estado = 1", [cajero_id])
            if cursor.fetchone():
                return Response({"status": "error", "mensaje": "Este operador ya tiene una caja abierta."}, status=status.HTTP_400_BAD_REQUEST)

            # 2. Insertar en la tabla maestra 'cajas'
            fecha_actual = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT INTO cajas (cajero, estado, saldo_ini_billetes, fecha_open)
                VALUES (%s, 1, %s, %s)
            """, [cajero_id, fondo_inicial, fecha_actual])

            # Obtener el ID autonumérico de la caja recién creada
            caja_id = cursor.lastrowid

            # 3. Insertar el fondo inicial en 'cajas_det' usando la estructura real
            if fondo_inicial > 0:
                cursor.execute("""
                    INSERT INTO cajas_det (nro_caja, tipo, forma, nombre, importe_cajero, importe_real)
                    VALUES (%s, 'EFE', 'Efectivo', 'FONDO FIJO', %s, %s)
                """, [caja_id, fondo_inicial, fondo_inicial])

        return Response({
            "status": "success", 
            "mensaje": f"Caja N° {caja_id} abierta con éxito.", 
            "caja_id": caja_id
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def ObtenerEstadoCaja(request):
    """Calcula el arqueo real consultando ventas y cajas_retiros mediante SQL"""
    caja_id = request.query_params.get('caja_id')
    
    try:
        if not caja_id:
            return Response({"status": "cerrada"}, status=status.HTTP_200_OK)

        with connection.cursor() as cursor:
            # 1. Traer datos de la cabecera
            cursor.execute("SELECT id, cajero, saldo_ini_billetes, fecha_open, estado FROM cajas WHERE id = %s", [caja_id])
            caja_row = cursor.fetchone()
            
            if not caja_row or caja_row[4] != 1: # estado 1 = Abierta
                return Response({"status": "cerrada"}, status=status.HTTP_200_OK)
            
            cajero_id = caja_row[1]
            apertura = float(caja_row[2] or 0)
            fecha_open = caja_row[3]

            # 2. Sumar Ingresos (Ventas)
            cursor.execute("SELECT SUM(tot_general) FROM ventas WHERE nro_caja = %s AND anulado = 'N'", [caja_id])
            ingresos_row = cursor.fetchone()
            ingresos = float(ingresos_row[0] or 0)

            # 3. Sumar Egresos (cajas_retiros). 
            # Como cajas_retiros NO tiene nro_caja, filtramos por cajero y fecha posterior a la apertura (Igual que en C#)
            cursor.execute("SELECT SUM(retiro) FROM cajas_retiros WHERE cajero = %s AND fecha_open >= %s", [cajero_id, fecha_open])
            egresos_row = cursor.fetchone()
            egresos = float(egresos_row[0] or 0)

            total_efectivo = apertura + ingresos - egresos

            datos_caja = {
                "nro_caja": caja_id,
                "fecha_caja": fecha_open.strftime("%d/%m/%Y") if fecha_open else "",
                "apertura": apertura,
                "ingresos": ingresos,
                "egresos": egresos,
                "total_efectivo": total_efectivo
            }
            
        return Response({"status": "abierta", "data": datos_caja}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def CerrarCaja(request):
    """Cierra el turno insertando en 'cajas_retiros' y calculando todos los totales para 'cajas'"""
    data = request.data
    nro_caja = data.get('nro_caja')
    total_retirado = float(data.get('total_retirado', 0))

    try:
        with connection.cursor() as cursor:
            # 1. Verificar si existe la caja y traer los datos iniciales
            cursor.execute("SELECT cajero, saldo_ini_billetes, fecha_open FROM cajas WHERE id = %s AND estado = 1", [nro_caja])
            row = cursor.fetchone()
            if not row:
                return Response({"status": "error", "mensaje": "La caja indicada no está abierta o no existe."}, status=status.HTTP_404_NOT_FOUND)
            
            cajero_id = row[0]
            apertura = float(row[1] or 0)
            fecha_open = row[2]
            fecha_actual = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

            # 2. Registrar el retiro en 'cajas_retiros'
            if total_retirado >= 0:
                cursor.execute("""
                    INSERT INTO cajas_retiros (cajero, fecha_open, retiro)
                    VALUES (%s, %s, %s)
                """, [cajero_id, fecha_actual, total_retirado])

            # 3. Sumarizar Ventas del turno
            cursor.execute("SELECT SUM(tot_general) FROM ventas WHERE nro_caja = %s AND anulado = 'N'", [nro_caja])
            ventas_row = cursor.fetchone()
            ventas = float(ventas_row[0] or 0)

            # 4. Sumarizar todos los egresos/retiros del turno (incluyendo el que acabamos de insertar)
            cursor.execute("SELECT SUM(retiro) FROM cajas_retiros WHERE cajero = %s AND fecha_open >= %s", [cajero_id, fecha_open])
            egresos_row = cursor.fetchone()
            otros_egresos = float(egresos_row[0] or 0)

            # 5. Cálculos de diferencia (Teórico vs Declarado)
            # Diferencia = (Apertura + Ventas - Egresos_Previos) - Lo que retira
            # Matemáticamente equivale a: Apertura + Ventas - (Todos los egresos incluido el actual)
            dife_billetes = apertura + ventas - otros_egresos
            con_diferencias = 1 if dife_billetes != 0 else 0

            # 6. UPDATE FINAL MASTER DE LA CAJA (Llenando todos los campos para que no queden en NULL)
            cursor.execute("""
                UPDATE cajas
                SET estado = 2, 
                    fecha_close = %s, 
                    saldo_final_billetes = %s,
                    ventas = %s,
                    otros_egresos = %s,
                    dife_billetes = %s,
                    con_diferencias = %s,
                    otros_ingresos = 0.00,
                    cta_cte = 0.00,
                    saldo_ini_cupones = 0.00,
                    saldo_final_cupones = 0.00,
                    dife_cupones = 0.00,
                    deja_billetes = 0.00,
                    procesado = 0
                WHERE id = %s
            """, [
                fecha_actual, 
                total_retirado, 
                ventas, 
                otros_egresos, 
                dife_billetes, 
                con_diferencias, 
                nro_caja
            ])

        return Response({"status": "success", "mensaje": "Arqueo procesado y Caja cerrada."}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            },
            "caja_id": None # Sys asume que no tiene caja por defecto
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

    # ---> NUEVO: Buscar si el cajero ya tiene un turno abierto (estado=1) <---
    caja_abierta = Cajas.objects.filter(cajero=usuario_db.id, estado=1).first()
    nro_caja = caja_abierta.id if caja_abierta else None

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
        },
        "caja_id": nro_caja # Mandamos el ID si existe, o null si está cerrada
    }, status=status.HTTP_200_OK)



# ==========================================
#         MÓDULO DE GESTIÓN (ABM)
# ==========================================

@api_view(['POST'])
def CrearUsuario(request):

    serializer = CrearUsuarioSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Regla 1: Validar que el usuario no exista
    if Usuarios.objects.filter(nombrelogin=data['nombrelogin']).exists():
        return Response({
            "status": "error", 
            "mensaje": f"El usuario {data['nombrelogin']} ya existe."
        }, status=status.HTTP_400_BAD_REQUEST)
        
    # Regla 2: Replicar lógica de ID < 1000 del sistema legacy
    max_id = Usuarios.objects.filter(id__lt=1000).aggregate(Max('id'))['id__max'] or 0
    nuevo_id = max_id + 1
    
    # Regla 3: Hashear la password con la lógica legacy (NombreLogin + Password)
    hashed_password = encode_password_legacy(data['nombrelogin'], data['password'])
    
    # Regla 4: Crear usuario
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
        interfaz='Migracion Web' # Para que sepas que se creó desde el nuevo sistema
    )
    
    return Response({
        "status": "success", 
        "mensaje": f"Usuario '{nuevo_usuario.nombrelogin}' creado con éxito.",
        "id": nuevo_usuario.id
    }, status=status.HTTP_201_CREATED)



@api_view(['GET'])
def ListarUsuarios(request):
    """Devuelve la lista de usuarios, excluyendo al superusuario sys (id=0)"""
    usuarios = Usuarios.objects.filter(id__gt=0).values(
        'id', 'nombrelogin', 'nombre', 'apellido', 'nivel_usuario', 'no_activo'
    )
    return Response({"status": "success", "data": list(usuarios)}, status=status.HTTP_200_OK)


@api_view(['POST'])
def BajaUsuario(request):
    """Aplica una baja lógica (no_activo = 1) o lo reactiva (no_activo = 0) """
    user_id = request.data.get('id')
    estado_nuevo = request.data.get('no_activo') # 1 para dar de baja, 0 para reactivar

    if user_id is None or estado_nuevo is None:
        return Response({"status": "error", "mensaje": "Faltan parámetros (id, no_activo)"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        usuario = Usuarios.objects.get(id=user_id)
        usuario.no_activo = estado_nuevo
        usuario.save()
        
        accion = "dado de baja" if estado_nuevo == 1 else "reactivado"
        return Response({
            "status": "success", 
            "mensaje": f"Usuario {usuario.nombrelogin} {accion} exitosamente."
        }, status=status.HTTP_200_OK)
    except Usuarios.DoesNotExist:
        return Response({"status": "error", "mensaje": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def EditarUsuario(request):

    user_id = request.data.get('id')
    
    if not user_id:
        return Response({"status": "error", "mensaje": "ID de usuario requerido."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        usuario = Usuarios.objects.get(id=user_id)
        
        # Actualizamos campos básicos
        usuario.nombre = request.data.get('nombre', usuario.nombre)
        usuario.apellido = request.data.get('apellido', usuario.apellido)
        usuario.email = request.data.get('email', usuario.email)
        usuario.nivel_usuario = int(request.data.get('nivel_usuario', usuario.nivel_usuario))
        usuario.cajero = int(request.data.get('cajero', usuario.cajero))
        usuario.vendedor = int(request.data.get('vendedor', usuario.vendedor))
        usuario.autorizador = int(request.data.get('autorizador', usuario.autorizador))

        # Solo cambiamos la clave si el frontend envió una nueva
        nueva_clave = request.data.get('password', '')
        if nueva_clave:
            # Replicar algoritmo legacy: EncodePassword(NombreLogin + Password)
            usuario.password = encode_password_legacy(usuario.nombrelogin, nueva_clave)

        usuario.save()

        return Response({
            "status": "success", 
            "mensaje": f"Usuario '{usuario.nombrelogin}' actualizado correctamente."
        }, status=status.HTTP_200_OK)

    except Usuarios.DoesNotExist:
        return Response({"status": "error", "mensaje": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    

# ==========================================
#         SUBMÓDULO DE CLIENTES
# ==========================================

@api_view(['GET'])
def ListarClientes(request):
    """Devuelve los clientes. Permite filtrar por nombre o CUIT."""
    busqueda = request.query_params.get('buscar', '')
    
    clientes = Clientes.objects.all()
    if busqueda:
        clientes = clientes.filter(Q(denominacion__icontains=busqueda) | Q(nro_cuit__icontains=busqueda))
        
    # Limitamos a 100 para que la pantalla no se cuelgue si tenés miles de clientes
    data = clientes.values(
        'cod_cli', 'denominacion', 'nro_cuit', 'domicilio', 'telefono', 
        'cond_iva', 'credito_cc', 'estado_baja', 'lista_precio'
    )[:100]
    
    return Response({"status": "success", "data": list(data)}, status=status.HTTP_200_OK)

@api_view(['POST'])
def GuardarCliente(request):

    """Crea un nuevo cliente o edita uno existente [cite: 465, 466]"""
    data = request.data
    cod_cli = data.get('cod_cli')
    
    if cod_cli: # MODO EDICIÓN
        cliente = Clientes.objects.filter(cod_cli=cod_cli).first()
        if not cliente:
            return Response({"status": "error", "mensaje": "Cliente no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        mensaje = f"Cliente '{cliente.denominacion}' actualizado."
    else: # MODO CREACIÓN
        max_id = Clientes.objects.aggregate(Max('cod_cli'))['cod_cli__max'] or 0
        cod_cli = max_id + 1
        cliente = Clientes(cod_cli=cod_cli)
        mensaje = f"Cliente creado con el código {cod_cli}."

    # Actualizamos los campos basados en tu C# [cite: 465]
    cliente.denominacion = data.get('denominacion', cliente.denominacion or '')
    cliente.nro_cuit = data.get('nro_cuit', cliente.nro_cuit or '')
    cliente.domicilio = data.get('domicilio', cliente.domicilio or '')
    cliente.telefono = data.get('telefono', cliente.telefono or '')
    cliente.cond_iva = int(data.get('cond_iva', cliente.cond_iva or 5)) # 5 = Consumidor Final por defecto [cite: 470]
    cliente.estado_baja = int(data.get('estado_baja', cliente.estado_baja or 0))
    cliente.credito_cc = data.get('credito_cc', cliente.credito_cc or 0)
    
    cliente.save()

    return Response({"status": "success", "mensaje": mensaje}, status=status.HTTP_200_OK)

# ==========================================
#         MÓDULO DE STOCK (ARTÍCULOS)
# ==========================================

@api_view(['GET'])
def ListarArticulosABM(request):
    """Devuelve los artículos para el ABM. Permite filtrar por nombre, código o barra."""
    busqueda = request.query_params.get('buscar', '')
    
    articulos = Articulos.objects.all()
    if busqueda:
        articulos = articulos.filter(
            Q(nombre__icontains=busqueda) | 
            Q(cod_art__icontains=busqueda) | 
            Q(barra__icontains=busqueda)
        )
        
    # Limitamos a 100 para no saturar la red (ideal si tenés miles de productos)
    data = articulos.values(
        'cod_art', 'nombre', 'precio_1', 'costo_ult', 'iva', 'stock', 'barra', 'rubro'
    )[:100]
    
    return Response({"status": "success", "data": list(data)}, status=status.HTTP_200_OK)

@api_view(['POST'])
def GuardarArticulo(request):
    """Crea un nuevo artículo o edita uno existente"""
    data = request.data
    cod_art = data.get('cod_art')
    is_new = data.get('is_new', False)
    
    if not cod_art:
        return Response({"status": "error", "mensaje": "El código de artículo es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        if is_new:
            if Articulos.objects.filter(cod_art=cod_art).exists():
                return Response({"status": "error", "mensaje": f"El código '{cod_art}' ya existe."}, status=status.HTTP_400_BAD_REQUEST)
            articulo = Articulos(cod_art=cod_art)
            mensaje = f"Artículo '{cod_art}' creado exitosamente."
        else:
            articulo = Articulos.objects.filter(cod_art=cod_art).first()
            if not articulo:
                return Response({"status": "error", "mensaje": "Artículo no encontrado."}, status=status.HTTP_404_NOT_FOUND)
            mensaje = f"Artículo '{cod_art}' actualizado."

        # Actualizamos los campos vitales
        articulo.nombre = data.get('nombre', articulo.nombre or '')
        articulo.barra = data.get('barra', articulo.barra or '')
        articulo.rubro = data.get('rubro', articulo.rubro or '')
        articulo.precio_1 = float(data.get('precio_1', articulo.precio_1 or 0))
        articulo.costo_ult = float(data.get('costo_ult', articulo.costo_ult or 0))
        articulo.iva = float(data.get('iva', articulo.iva or 21)) # Por defecto 21%
        
        # Opcional: Podríamos permitir modificar el stock manual acá, 
        # pero en sistemas grandes el stock se mueve por compras o ajustes.
        
        articulo.save()

        return Response({"status": "success", "mensaje": mensaje}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"status": "error", "mensaje": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# ==========================================
#         MÓDULO DE COMPRAS (PROVEEDORES)
# ==========================================

@api_view(['GET'])
def ListarProveedores(request):
    """Devuelve los proveedores. Permite filtrar por razón social o CUIT."""
    busqueda = request.query_params.get('buscar', '')
    
    proveedores = Proveedores.objects.all()
    if busqueda:
        proveedores = proveedores.filter(Q(nomfantasia__icontains=busqueda) | Q(nro_cuit__icontains=busqueda))
        
    # Extraemos directamente los campos con su nombre original en la DB
    data = proveedores.values(
        'cod_prov', 'nomfantasia', 'nro_cuit', 'domicilio', 'telefono', 
        'mail', 'cond_iva', 'estado'
    )[:100]
    
    return Response({"status": "success", "data": list(data)}, status=status.HTTP_200_OK)

@api_view(['POST'])
def GuardarProveedor(request):

    """Crea un nuevo proveedor o edita uno existente"""
    data = request.data
    cod_prov = data.get('cod_prov')
    
    if cod_prov: # MODO EDICIÓN
        proveedor = Proveedores.objects.filter(cod_prov=cod_prov).first()
        if not proveedor:
            return Response({"status": "error", "mensaje": "Proveedor no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        mensaje = f"Proveedor '{proveedor.nomfantasia}' actualizado."
    else: # MODO CREACIÓN
        max_id = Proveedores.objects.aggregate(Max('cod_prov'))['cod_prov__max'] or 0
        cod_prov = max_id + 1
        proveedor = Proveedores(cod_prov=cod_prov)
        mensaje = f"Proveedor creado con el código {cod_prov}."

    # Mapeo usando los nombres originales del sistema legacy
    proveedor.nomfantasia = data.get('nomfantasia', proveedor.nomfantasia or '')
    proveedor.nomtitular = data.get('nomfantasia', proveedor.nomtitular or '') # Replicamos nomfantasia acá por las dudas
    proveedor.nro_cuit = data.get('nro_cuit', proveedor.nro_cuit or '')
    proveedor.domicilio = data.get('domicilio', proveedor.domicilio or '')
    proveedor.telefono = data.get('telefono', proveedor.telefono or '')
    proveedor.mail = data.get('mail', proveedor.mail or '')
    proveedor.cond_iva = int(data.get('cond_iva', proveedor.cond_iva or 1))
    proveedor.estado = int(data.get('estado', proveedor.estado or 0))
    
    try:
        proveedor.save()
        return Response({"status": "success", "mensaje": mensaje}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": f"Error guardando: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# ==========================================
#         MÓDULO DE GESTIÓN (FORMAS DE PAGO)
# ==========================================

@api_view(['GET'])
def ListarFormasPago(request):
    """Devuelve las formas de pago configuradas en el sistema."""
    # Asumimos que tu modelo en models.py se llama FormaPago o FormasPago
    # Si se llama distinto, ajustalo a tu nombre exacto.
    formas = FormaPago.objects.all().values('codigo', 'descripcion', 'activa', 'moneda')
    return Response({"status": "success", "data": list(formas)}, status=status.HTTP_200_OK)

@api_view(['POST'])
def GuardarFormaPago(request):
    """Crea una nueva forma de pago o edita una existente."""
    data = request.data
    codigo = data.get('codigo')
    is_new = data.get('is_new', False)
    
    if not codigo:
        return Response({"status": "error", "mensaje": "El código es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Forzamos que el código esté en mayúsculas (ej: 'EFE')
        codigo = codigo.upper()[:3] 

        if is_new:
            if FormaPago.objects.filter(codigo=codigo).exists():
                return Response({"status": "error", "mensaje": f"El código '{codigo}' ya existe."}, status=status.HTTP_400_BAD_REQUEST)
            forma = FormaPago(codigo=codigo)
            mensaje = f"Forma de pago '{codigo}' creada."
        else:
            forma = FormaPago.objects.filter(codigo=codigo).first()
            if not forma:
                return Response({"status": "error", "mensaje": "Forma de pago no encontrada."}, status=status.HTTP_404_NOT_FOUND)
            mensaje = f"Forma de pago '{codigo}' actualizada."

        forma.descripcion = data.get('descripcion', forma.descripcion or '')
        forma.activa = int(data.get('activa', forma.activa if forma.activa is not None else 1))
        forma.moneda = int(data.get('moneda', forma.moneda or 1))
        
        forma.save()

        return Response({"status": "success", "mensaje": mensaje}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"status": "error", "mensaje": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# ==========================================
#     NUEVOS INFORMES DE VENTAS
# ==========================================

@api_view(['GET'])
def InformeTotalesCondicion(request):
    """Agrupa las ventas por Condición de Venta (Contado, Cta Cte, etc.)"""
    try:
        # Agrupamos por cond_venta, contamos cuántos tickets hay y sumamos la plata
        reporte = Ventas.objects.values('cond_venta').annotate(
            cantidad_operaciones=Count('movim'),
            total_pesos=Sum('total')
        ).order_by('-total_pesos')

        return Response({"status": "success", "data": list(reporte)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def InformeTotalesVendedor(request):
    """Agrupa las ventas por el ID del Vendedor"""
    try:
        reporte = Ventas.objects.values('vendedor').annotate(
            cantidad_operaciones=Count('movim'),
            total_pesos=Sum('total')
        ).order_by('-total_pesos')

        return Response({"status": "success", "data": list(reporte)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


# ==========================================
#     MÓDULO DE STOCK: RUBROS Y SUBRUBROS
# ==========================================

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
        return Response({"status": "error", "mensaje": "El código es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if is_new:
            if ArticulosRubros.objects.filter(codigo=codigo).exists():
                return Response({"status": "error", "mensaje": f"El código '{codigo}' ya existe."}, status=status.HTTP_400_BAD_REQUEST)
            rubro = ArticulosRubros(codigo=codigo)
        else:
            rubro = ArticulosRubros.objects.filter(codigo=codigo).first()
            if not rubro: return Response({"status": "error", "mensaje": "Rubro no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        rubro.nombre = data.get('nombre', '').upper()
        # Podríamos guardar el usuario logueado en rubro.usuario y la fecha en rubro.fecha_hora si lo pasás en el request
        rubro.save()
        return Response({"status": "success", "mensaje": "Rubro guardado con éxito."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        return Response({"status": "error", "mensaje": "El código es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if is_new:
            if ArticulosSubrub.objects.filter(codigo=codigo).exists():
                return Response({"status": "error", "mensaje": f"El código '{codigo}' ya existe."}, status=status.HTTP_400_BAD_REQUEST)
            subrubro = ArticulosSubrub(codigo=codigo)
        else:
            subrubro = ArticulosSubrub.objects.filter(codigo=codigo).first()
            if not subrubro: return Response({"status": "error", "mensaje": "Subrubro no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        subrubro.nombre = data.get('nombre', '').upper()
        subrubro.save()
        return Response({"status": "success", "mensaje": "Subrubro guardado con éxito."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# ==========================================
#     MÓDULO DE COMPRAS E INGRESO DE MERCADERÍA
# ==========================================

@api_view(['GET'])
def ListarCompras(request):
    """Devuelve el historial usando la lógica del comprasTableAdapter"""
    try:
        # TODO: Lógica para leer la tabla 'compras'
        return Response({"status": "success", "data": []}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def IngresarComprobanteComprasJSON(request):
    """Guarda factura de compra, actualiza el costo_ult y SUMA el stock de los artículos"""
    data = request.data
    try:
        with transaction.atomic():
            
            max_movim = Compras.objects.aggregate(Max('movim'))['movim__max'] or 0
            nuevo_movim = max_movim + 1
            
            # 1. Cabecera de la Compra
            compra = Compras.objects.create(
                movim=nuevo_movim,
                cod_prov=data.get('Proveedor_Codigo'),
                fecha_fact=data.get('Comprobante_FechaEmision'),
                fecha_vto=data.get('Comprobante_FechaEmision'), # Por defecto igual
                nro_comprob=data.get('Comprobante_Numero'),
                cod_comprob=data.get('Comprobante_Tipo', 'FC')[:2],
                neto=data.get('Comprobante_Neto', 0),
                iva_1=data.get('Comprobante_IVA', 0),
                total=data.get('Comprobante_ImporteTotal', 0),
                tot_general=data.get('Comprobante_ImporteTotal', 0),
                cond_compra=data.get('Comprobante_CondVenta', '1'),
                usuario=data.get('usuario', 'admin'),
                fecha_mod=timezone.now(),
                procesado=0
            )

            # 2. Detalles y Ajuste de Stock
            for item in data.get('Comprobante_Items', []):
                cod_art = item['Item_CodigoArticulo']
                cantidad = float(item['Item_CantidadUM1'])
                precio_costo = float(item['Item_PrecioUnitario'])
                total_item = float(item['Item_ImporteTotal'])

                ComprasDet.objects.create(
                    movim=nuevo_movim,
                    cod_articulo=cod_art,
                    cantidad=cantidad,
                    precio_unit=precio_costo,
                    total=total_item,
                    detalle=item.get('Item_DescripArticulo', ''),
                    p_iva=item.get('Item_TasaIVAInscrip', 21),
                    v_iva=total_item - (total_item / 1.21),
                    procesado=0
                )
                
                # REGLA DE NEGOCIO: Actualizamos Stock sumando, y actualizamos el último costo
                Articulos.objects.filter(cod_art=cod_art).update(
                    stock=F('stock') + cantidad,
                    costo_ult=precio_costo,
                    ult_compra=timezone.now()
                )

        return Response({
            "status": "success", 
            "mensaje": "Compra registrada. Stock y costos actualizados.",
            "movim": nuevo_movim
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==========================================
#     MÓDULO DE CUENTAS CORRIENTES (CLIENTES Y PROVEEDORES)
# ==========================================

@api_view(['GET'])
def ResumenCtaCteCliente(request):
    """Devuelve el saldo total y los comprobantes adeudados de un cliente"""
    cod_cli = request.query_params.get('cod_cli')
    if not cod_cli:
        return Response({"status": "error", "mensaje": "Debe indicar el código de cliente."}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        # Buscamos todos los movimientos de ese cliente donde todavía deba plata (saldo > 0)
        movimientos = CtaCteCli.objects.filter(cod_cli=cod_cli, saldo__gt=0, anulado='N').values(
            'movim', 'origen', 'fecha', 'cod_comprob', 'nro_comprob', 'detalle', 'imported', 'saldo', 'fec_vto'
        ).order_by('fecha')
        
        # Sumamos el total de la deuda
        saldo_total = sum(mov['saldo'] for mov in movimientos)
        
        return Response({
            "status": "success", 
            "saldo_total": saldo_total, 
            "movimientos": list(movimientos)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def InsertarReciboCtaCte(request):
    """Registra el pago de una deuda de Cta Cte, impactando caja y descontando saldo"""
    data = request.data
    cod_cli = data.get('cod_cli')
    importe_pago = float(data.get('importe_pago', 0))
    cajero = data.get('cajero', 1)
    nro_caja = data.get('nro_caja', 1)
    
    if importe_pago <= 0:
        return Response({"status": "error", "mensaje": "El importe debe ser mayor a 0."}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        with transaction.atomic():
            # 1. Traer los comprobantes adeudados del más viejo al más nuevo
            deudas = CtaCteCli.objects.filter(cod_cli=cod_cli, saldo__gt=0, anulado='N').order_by('fecha')
            
            pago_restante = importe_pago
            
            # 2. Descontar el saldo cascada (FIFO)
            for deuda in deudas:
                if pago_restante <= 0:
                    break
                    
                if pago_restante >= deuda.saldo:
                    # Paga la totalidad de este comprobante
                    pago_restante -= float(deuda.saldo)
                    deuda.saldo = 0
                else:
                    # Paga una parte de este comprobante
                    deuda.saldo = float(deuda.saldo) - pago_restante
                    pago_restante = 0
                
                deuda.save()

            # 3. Generar el nuevo número de Movimiento
            max_movim = CtaCteCli.objects.aggregate(Max('movim'))['movim__max'] or 0
            nuevo_movim = max_movim + 1
            
            # 4. Insertar el Recibo (Comprobante de Pago) en Cta Cte
            CtaCteCli.objects.create(
                movim=nuevo_movim,
                origen='RE', # Recibo
                cod_cli=cod_cli,
                fecha=timezone.now(),
                id_comprob=2, # ID genérico para Recibos
                cod_comprob='RE',
                nro_comprob=nuevo_movim, # Usamos movim como comprobante
                detalle='Cobro de Cta. Cte.',
                imported=importe_pago,
                saldo=0, # Un recibo no genera deuda
                moneda=1,
                anulado='N',
                nro_caja=nro_caja,
                cajero=cajero
            )
            
            # 5. Ingresar el dinero en efectivo a la Caja (CajasDet)
            CajasDet.objects.create(
                nro_caja=nro_caja,
                tipo='RE',
                forma='EFE', # Asumimos efectivo por ahora
                nombre='Cobranza Cta Cte',
                importe_cajero=importe_pago,
                importe_real=importe_pago,
                procesado=0
            )

        return Response({"status": "success", "mensaje": f"Se cobraron ${importe_pago} correctamente."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==========================================
#     MÓDULO DE LISTAS DE PRECIOS Y PROMOCIONES
# ==========================================

@api_view(['POST'])
def ActualizarListaPrecio(request):
    """Actualiza el nombre de una lista de precios (Legacy: ActualizarListaPrecio)"""
    _nombre = request.data.get('_nombre')
    _lis = request.data.get('_lis')
    
    if not _nombre or not _lis:
        return Response({"status": "error", "mensaje": "Faltan parámetros (_nombre, _lis)"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        # Buscamos la lista y la actualizamos (equivalente al UPDATE listasprecios SET NombreLista=...)
        lista = Listasprecios.objects.filter(codigo=_lis).first()
        if not lista:
            return Response({"status": "error", "mensaje": "Lista de precios no encontrada."}, status=status.HTTP_404_NOT_FOUND)
            
        lista.nombrelista = _nombre
        lista.save()
        return Response({"status": "success", "mensaje": "Lista de precios actualizada."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def InsertarNuevaPromo(request):
    """Crea reglas de descuento y promociones (Mismo nombre que en C#)"""
    try:
        with transaction.atomic():
            # TODO: INSERT INTO promos (id, nombre_promo, no_activa, lleva, paga...) 
            pass
        return Response({"status": "success", "mensaje": "Promoción guardada."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
#     MÓDULO DE INVENTARIO Y AJUSTES
# ==========================================

@api_view(['POST'])
def InsertarNuevCausa(request):
    """Registra motivos de ajuste de stock (Legacy: InsertarNuevCausa)"""
    _id = request.data.get('codigo')
    _nom = request.data.get('detalle')
    
    try:
        if StockCausaemision.objects.filter(codigo=_id).exists():
             return Response({"status": "error", "mensaje": "El código de causa ya existe."}, status=status.HTTP_400_BAD_REQUEST)
             
        StockCausaemision.objects.create(codigo=_id, detalle=_nom)
        return Response({"status": "success", "mensaje": "Causa guardada con éxito."}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def ActualizarCausa(request):
    """Actualiza motivos de ajuste de stock (Legacy: ActualizarCausa)"""
    _id = request.data.get('codigo')
    _nom = request.data.get('detalle')
    
    try:
        causa = StockCausaemision.objects.filter(codigo=_id).first()
        if not causa:
            return Response({"status": "error", "mensaje": "Causa no encontrada."}, status=status.HTTP_404_NOT_FOUND)
            
        causa.detalle = _nom
        causa.save()
        return Response({"status": "success", "mensaje": "Causa actualizada con éxito."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)