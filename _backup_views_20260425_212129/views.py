import hashlib
import base64
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField, Max
from django.db import connection
from django.db.models import Q
from django.utils.dateparse import parse_datetime, parse_date
from django.utils import timezone
from .serializers import *
from .models import (
    ArticulosRubros, ArticulosSubrub, Cajas, CajasRetiros, 
    Ventas, VentasDet, CheqTarjCli, TipocompCli, CtaCteCli, 
    CajasDet, Compras, ComprasDet, FeTipocompCli, Parametros,Proveedores
)


# Importamos todos los modelos y serializers juntos


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


@api_view(['GET', 'POST'])
def GestionarParametros(request):
    # Buscamos el primer registro de parámetros (suele ser la sucursal actual)
    parametro = Parametros.objects.first()

    if request.method == 'GET':
        if not parametro:
            return Response({"status": "error", "mensaje": "No hay parámetros configurados aún."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ParametrosSerializer(parametro)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        if parametro:
            # Actualiza el existente
            serializer = ParametrosSerializer(parametro, data=request.data, partial=True)
        else:
            # Crea uno nuevo si la tabla estaba vacía
            serializer = ParametrosSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "mensaje": "Parámetros guardados con éxito."})
        return Response({"status": "error", "errores": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


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
            ultima = Ventas.objects.select_for_update().aggregate(Max('movim'))
            nuevo_movim = (ultima['movim__max'] or 0) + 1
            
            condicion_venta = data.get('Comprobante_CondVenta', '1')
            cliente_codigo = int(data['Cliente_Codigo'])
            importe_total = data['Comprobante_ImporteTotal']
            
            # =================================================================
            # 1.5 LÓGICA LEGACY REAL: Obtener ID y NRO desde tipocomp_cli
            # =================================================================
            tipo_comprob = data['Comprobante_Tipo'][:2]
            pto_vta = data['Comprobante_PtoVenta']
            
            config_comprobante = TipocompCli.objects.filter(cod_compro=tipo_comprob).first()
            
            if not config_comprobante:
                raise Exception(f"El comprobante {tipo_comprob} no está configurado en la tabla tipocomp_cli.")
                
            id_comprob_real = config_comprobante.id_compro
            nro_comprob_final = config_comprobante.ultnro + 1
            
            config_comprobante.ultnro = nro_comprob_final
            config_comprobante.save()
            # =================================================================

            # 2. Guardar CABECERA (ventas)
            venta = Ventas.objects.create(
                movim=nuevo_movim,
                id_comprob=id_comprob_real,      
                cod_comprob=tipo_comprob,
                nro_comprob=nro_comprob_final,   
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
            
            # 3. Guardar DETALLES y descontar STOCK
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
                
                Articulos.objects.filter(cod_art=cod_art).update(stock=F('stock') - cantidad_vendida)

            # 4. REGLA DE NEGOCIO: CUENTA CORRIENTE (cta_cte_cli) 
            if condicion_venta == '2':
                CtaCteCli.objects.create(
                    movim=nuevo_movim,
                    origen='VTA',
                    cod_cli_id=cliente_codigo, 
                    fecha=timezone.now(),
                    id_comprob=venta.id_comprob,
                    cod_comprob=venta.cod_comprob,
                    nro_comprob=venta.nro_comprob,
                    detalle="Venta Cta. Cte.",
                    imported=importe_total,
                    saldo=importe_total, 
                    fec_vto=venta.fecha_vto,
                    moneda=1,
                    anulado='N',
                    procesado=0,
                    nro_caja=venta.nro_caja,
                    comprobante_tipo=venta.comprobante_tipo,
                    comprobante_letra=venta.comprobante_letra,
                    comprobante_pto_vta=venta.comprobante_pto_vta
                )
                
            # 5. REGLA DE NEGOCIO: MEDIOS DE PAGO Y CAJAS
            medios_pago = data.get('Comprobante_MediosPago', [])
            
            for mp in medios_pago:
                codigo_pago = str(mp.get('MedioPago', 'EFE')) 
                importe_pago = mp.get('MedioPago_Importe', 0)
                
                # 1. Registro general en Caja (para que el cierre de caja sume el total de ingresos)
                CajasDet.objects.create(
                    nro_caja=venta.nro_caja,
                    tipo='VTA',
                    forma=codigo_pago,
                    nombre=f"Cobro Venta {venta.cod_comprob} N° {venta.nro_comprob}",
                    importe_cajero=importe_pago,
                    importe_real=importe_pago,
                    procesado=0
                )

                # 2. Guardar en Cheques y Tarjetas (EXCLUYENDO Efectivo y Cta. Cte.)
                if codigo_pago not in ['EFE', '1', 'CTA', '2']: 
                    
                    # Intentamos sacar el número de cupón, si está vacío le ponemos un 0
                    nro_cupon = mp.get('MedioPago_NroCupon') or mp.get('MedioPago_NumeroCheque')
                    if not nro_cupon:
                        nro_cupon = 0

                    CheqTarjCli.objects.create(
                        movim=venta.movim,
                        origen='VTA',
                        cod_cli=venta.cod_cli,
                        tipo=codigo_pago,  
                        importe=importe_pago,
                        fecha_rece=venta.fecha_fact,
                        fecha_vto=mp.get('MedioPago_FechaVencimiento', venta.fecha_fact),
                        id_comprob=venta.id_comprob,
                        cod_comprob=venta.cod_comprob,
                        nro_comprob=venta.nro_comprob,
                        entidad=mp.get('MedioPago_CodigoBanco', ''),
                        numero=nro_cupon,
                        moneda=mp.get('MedioPago_Moneda', 1),
                        cuota=mp.get('MedioPago_CantidadCuotas', 1),
                        estado='PENDIENTE',
                        procesado=0,
                        nro_caja=venta.nro_caja,
                        cajero=venta.cajero,
                        comprobante_tipo=venta.comprobante_tipo,
                        comprobante_letra=venta.comprobante_letra,
                        comprobante_pto_vta=venta.comprobante_pto_vta
                    )
            # ... acá arriba termina el guardado de base de datos (CheqTarjCli, etc.) ...

        # =================================================================
        # 6. GUARDAR RESPALDO DEL JSON EN DISCO (ESPEJO EXACTO DE LA BD)
        # =================================================================
        try:
            import os
            import json
            from django.core.serializers.json import DjangoJSONEncoder
            
            # 1. Recuperamos los registros exactos de la BD usando .values()
            # Esto extrae TODAS las columnas definidas en el models.py automáticamente
            cabecera_dict = list(Ventas.objects.filter(movim=nuevo_movim).values())[0]
            detalles_lista = list(VentasDet.objects.filter(movim=nuevo_movim).values())
            pagos_lista = list(CheqTarjCli.objects.filter(movim=nuevo_movim).values())
            
            # 2. Armamos el objeto maestro juntando las 3 tablas
            json_a_guardar = cabecera_dict
            json_a_guardar['VentasDet'] = detalles_lista
            json_a_guardar['CheqTarjCli'] = pagos_lista
            
            # 3. Armamos el nombre concatenado
            tipo_arch = venta.cod_comprob
            letra_arch = venta.comprobante_letra
            pto_arch = str(venta.comprobante_pto_vta).zfill(4)
            nro_arch = str(venta.nro_comprob).zfill(8)
            
            nombre_archivo = f"{tipo_arch}{letra_arch}{pto_arch}{nro_arch}.json"
            ruta_carpeta = "/documentos_json"
            
            os.makedirs(ruta_carpeta, exist_ok=True)
            ruta_completa = os.path.join(ruta_carpeta, nombre_archivo)
            
            # 4. Escribimos el archivo físicamente
            with open(ruta_completa, 'w', encoding='utf-8') as archivo:
                json.dump(json_a_guardar, archivo, indent=4, ensure_ascii=False, cls=DjangoJSONEncoder)
                
        except Exception as error_archivo:
            print(f"⚠️ Venta exitosa, pero no se pudo guardar el archivo JSON: {error_archivo}")
        # =================================================================

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
    



@api_view(['GET', 'POST', 'PUT']) # Sacamos el DELETE de los métodos permitidos
def GestionarTipocompCli(request):
    if request.method == 'GET':
        tipos = TipocompCli.objects.all().order_by('id_compro')
        serializer = TipocompCliSerializer(tipos, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        # Para crear un nuevo comprobante (Alta permitida)
        serializer = TipocompCliSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "mensaje": "Tipo de comprobante creado con éxito."}, status=status.HTTP_201_CREATED)
        return Response({"status": "error", "errores": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        # REGLA DE NEGOCIO: Solo se permite actualizar el último número
        id_compro = request.data.get('id_compro')
        try:
            tipo = TipocompCli.objects.get(id_compro=id_compro)
            
            if 'ultnro' in request.data:
                tipo.ultnro = request.data['ultnro']
                # Usamos update_fields para asegurarnos que NINGÚN otro campo se modifique
                tipo.save(update_fields=['ultnro']) 
                return Response({"status": "success", "mensaje": f"Se actualizó el contador del comprobante {tipo.cod_compro} a {tipo.ultnro}."})
            else:
                return Response({"status": "error", "mensaje": "No se envió el nuevo número."}, status=status.HTTP_400_BAD_REQUEST)
                
        except TipocompCli.DoesNotExist:
            return Response({"status": "error", "mensaje": "Comprobante no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        
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
#     MÓDULO DE INFORMES Y ESTADÍSTICAS
# ==========================================
@api_view(['GET'])
def InformeTotalesCondicion(request):
    """Agrupa las ventas por Condición de Venta (Contado, Cta Cte, etc.)"""
    try:
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
    
@api_view(['GET'])
def InformeLibroIVAVentas(request):
    """Genera el Libro IVA Ventas para una fecha determinada o rango de fechas"""
    fecha_desde = request.query_params.get('desde')
    fecha_hasta = request.query_params.get('hasta')
    
    try:
        query = Ventas.objects.all()
        
        if fecha_desde and fecha_hasta:
            query = query.filter(fecha_fact__range=[fecha_desde, fecha_hasta])
            
        # Obtenemos el detalle comprobante por comprobante
        comprobantes = query.values(
            'fecha_fact', 'cod_comprob', 'comprobante_pto_vta', 'nro_comprob',
            'cod_cli', 'tot_general', 'neto', 'iva_1', 'exento'
        ).order_by('fecha_fact', 'nro_comprob')
        
        # Obtenemos los totales del mes/rango
        totales = query.aggregate(
            suma_neto=Sum('neto'),
            suma_iva=Sum('iva_1'),
            suma_exento=Sum('exento'),
            suma_total=Sum('tot_general')
        )
        
        return Response({
            "status": "success",
            "totales": totales,
            "comprobantes": list(comprobantes)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def InformeRentabilidadArticulos(request):
    """Muestra cuáles son los artículos más vendidos y la ganancia (Rentabilidad)"""
    fecha_desde = request.query_params.get('desde')
    fecha_hasta = request.query_params.get('hasta')
    
    try:
        # Filtramos los detalles de venta por fecha (usando la cabecera)
        query = VentasDet.objects.all()
        
        # En tu modelo, el costo lo sacamos del precio_unit_base o lo cruzamos con Articulos
        # Acá hacemos la suma total de Cantidades y Dinero por Artículo
        ranking = query.values('cod_articulo', 'detalle').annotate(
            cantidad_vendida=Sum('cantidad'),
            total_facturado=Sum('total')
        ).order_by('-cantidad_vendida')[:100] # Top 100 más vendidos
        
        return Response({"status": "success", "data": list(ranking)}, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def InformeHistorialCajas(request):
    """Trae el historial de cajas cerradas con sus diferencias de arqueo"""
    try:
        # Traemos solo las cajas cerradas (estado = 2)
        cajas_cerradas = Cajas.objects.filter(estado=2).values(
            'id', 'cajero', 'fecha_open', 'fecha_close', 
            'saldo_ini_billetes', 'ventas', 'otros_egresos', 
            'saldo_final_billetes', 'dife_billetes'
        ).order_by('-id')[:50] # Últimas 50 cajas
        
        return Response({"status": "success", "data": list(cajas_cerradas)}, status=status.HTTP_200_OK)
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
    
# ==========================================
#     MÓDULO DE ANULACIÓN DE COMPROBANTES
# ==========================================

@api_view(['GET'])
def UltimosComprobantesVenta(request):
    """Trae los últimos 50 comprobantes emitidos para facilitar la anulación"""
    try:
        # Buscamos las últimas 50 ventas ordenadas por fecha/movimiento descendente
        ultimas_ventas = Ventas.objects.all().order_by('-movim')[:50]
        
        data = []
        for v in ultimas_ventas:
            data.append({
                "movim": v.movim,
                "tipo": v.cod_comprob,
                "letra": v.comprobante_letra or '',
                "pto_vta": v.comprobante_pto_vta,
                "nro": v.nro_comprob,
                "fecha": v.fecha_fact,
                "total": v.tot_general,
            })
            
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def BuscarComprobanteVenta(request):
    """Busca una venta específica por Tipo, Punto de Venta y Número"""
    tipo = request.query_params.get('tipo', 'TK')
    pto = request.query_params.get('pto', '1') # Ej: 1 o 0001
    nro = request.query_params.get('nro')

    try:
        # Acomodamos el padding del punto de venta por si lo guardaron como "0001" o "1"
        venta = Ventas.objects.filter(cod_comprob=tipo, nro_comprob=nro).filter(
            comprobante_pto_vta__endswith=str(pto).zfill(4)[-1:] # Flexibilidad en la búsqueda
        ).first()

        if not venta:
            return Response({"status": "error", "mensaje": "Comprobante no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # Buscamos los artículos de esta venta
        detalles = VentasDet.objects.filter(movim=venta.movim).values(
            'cod_articulo', 'detalle', 'cantidad', 'precio_unit', 'total'
        )
        
        data = {
            "movim": venta.movim,
            "fecha": venta.fecha_fact,
            "cliente": venta.cod_cli,
            "total": venta.tot_general,
            "procesado": venta.procesado, # Si es -1, ya está anulado
            "items": list(detalles)
        }
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def AnularComprobanteVenta(request):
    """Realiza la reversión contable emitiendo una NOTA DE CRÉDITO (NC)"""
    movim_original = request.data.get('movim')
    
    try:
        with transaction.atomic():
            # 1. Buscar la venta original
            venta_orig = Ventas.objects.filter(movim=movim_original).first()
            if not venta_orig:
                return Response({"status": "error", "mensaje": "No se encontró el movimiento original."}, status=status.HTTP_404_NOT_FOUND)
            
            # Verificamos que no esté ya anulado (para no emitir dos NC para la misma venta)
            if venta_orig.procesado == -1:
                return Response({"status": "error", "mensaje": "Este comprobante ya posee una anulación/NC."}, status=status.HTTP_400_BAD_REQUEST)

            # 2. Buscar configuración del tipo de comprobante "NC" (Nota de Crédito)
            # 2. Mapeo exacto de Comprobantes a sus respectivas Notas de Crédito
            mapa_anulaciones = {
                'EA': 'KA', 'EB': 'KB', 'EC': 'KC',  # Electrónicas
                'FA': 'CA', 'FB': 'CB', 'FC': 'CC',  # Manuales
                'MA': 'NA', 'MB': 'NB',              # MiPyme
                'PR': 'DV',                          # Presupuesto a Devolución (777)
                'TK': 'NC'                           # Por si queda algún ticket viejo
            }
            
            cod_nc = mapa_anulaciones.get(venta_orig.cod_comprob)
            
            if not cod_nc:
                return Response({"status": "error", "mensaje": f"El comprobante original ({venta_orig.cod_comprob}) no tiene un código de anulación asignado en el sistema."}, status=status.HTTP_400_BAD_REQUEST)

            config_nc = TipocompCli.objects.filter(cod_compro=cod_nc).first()

            if not config_nc:
                return Response({"status": "error", "mensaje": f"Falta configurar el comprobante '{cod_nc}' en la tabla TipocompCli."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Si el sistema legacy los separa por letra (Ej: NCA), buscamos ese:
            if not config_nc:
                config_nc = TipocompCli.objects.filter(cod_compro=f"NC{venta_orig.comprobante_letra}").first()

            if not config_nc:
                return Response({"status": "error", "mensaje": f"No se encontró la configuración del comprobante Nota de Crédito en la tabla TipocompCli."}, status=status.HTTP_400_BAD_REQUEST)

            # 3. Preparar el nuevo ID y Número correlativo para la Nota de Crédito
            max_movim = Ventas.objects.aggregate(Max('movim'))['movim__max']
            nuevo_movim = (max_movim or 0) + 1
            
            nro_comprob_nc = config_nc.ultnro + 1
            config_nc.ultnro = nro_comprob_nc
            config_nc.save()

            # 4. CREAR LA CABECERA DE LA NOTA DE CRÉDITO
            nc = Ventas.objects.create(
                movim=nuevo_movim,
                id_comprob=config_nc.id_compro,
                cod_comprob=config_nc.cod_compro,
                nro_comprob=nro_comprob_nc,
                cod_cli=venta_orig.cod_cli,
                fecha_fact=timezone.now(),
                fecha_vto=timezone.now(),
                neto=venta_orig.neto,
                iva_1=venta_orig.iva_1,
                exento=venta_orig.exento,
                total=venta_orig.total,
                tot_general=venta_orig.tot_general,
                descuento=venta_orig.descuento,
                vendedor=venta_orig.vendedor,
                moneda=venta_orig.moneda,
                cajero=venta_orig.cajero,
                nro_caja=venta_orig.nro_caja,
                comprobante_tipo=config_nc.cod_compro,
                comprobante_letra=venta_orig.comprobante_letra,
                comprobante_pto_vta=venta_orig.comprobante_pto_vta,
                cond_venta=venta_orig.cond_venta,
                procesado=0, 
                observac=f"Anula Comp. {venta_orig.cod_comprob} N° {venta_orig.nro_comprob}",
                fecha_mod=timezone.now()
            )

            # 5. CREAR LOS DETALLES DE LA NC Y RESTAURAR STOCK
            detalles_orig = VentasDet.objects.filter(movim=movim_original)
            for item in detalles_orig:
                VentasDet.objects.create(
                    movim=nuevo_movim,
                    id_comprob=nc.id_comprob,
                    cod_comprob=nc.cod_comprob,
                    nro_comprob=nc.nro_comprob,
                    cod_articulo=item.cod_articulo,
                    cantidad=item.cantidad, 
                    precio_unit=item.precio_unit,
                    precio_unit_base=item.precio_unit_base,
                    total=item.total,
                    descuento=item.descuento,
                    detalle=item.detalle,
                    p_iva=item.p_iva,
                    v_iva=item.v_iva,
                    comprobante_tipo=nc.comprobante_tipo,
                    comprobante_letra=nc.comprobante_letra,
                    comprobante_pto_vta=nc.comprobante_pto_vta,
                    procesado=0
                )
                
                # Restauramos stock a las estanterías (Sumando)
                Articulos.objects.filter(cod_art=item.cod_articulo).update(stock=F('stock') + item.cantidad)

            # 6. ASENTAR DEVOLUCIÓN DE DINERO (Caja, Cta Cte y Tarjetas)
            
            if venta_orig.cond_venta == '2':
                # Si fue Cta Cte, limpiamos la deuda
                CtaCteCli.objects.create(
                    movim=nuevo_movim, origen='N/C', cod_cli_id=venta_orig.cod_cli,
                    fecha=timezone.now(), id_comprob=nc.id_comprob, cod_comprob=nc.cod_comprob,
                    nro_comprob=nc.nro_comprob, detalle=f"S/Nota de Credito N° {nc.nro_comprob}",
                    imported=-nc.total, saldo=0, fec_vto=timezone.now(), moneda=1, anulado='N',
                    procesado=0, nro_caja=nc.nro_caja, comprobante_tipo=nc.comprobante_tipo,
                    comprobante_letra=nc.comprobante_letra, comprobante_pto_vta=nc.comprobante_pto_vta
                )
            else:
                # Si fue al contado o tarjeta, revertimos en CajaDet
                CajasDet.objects.create(
                    nro_caja=nc.nro_caja, tipo='N/C', forma='EFE',
                    nombre=f"NC N° {nc.nro_comprob} (Devolución)",
                    importe_cajero=-nc.total, importe_real=-nc.total, procesado=0
                )
                
                # 👇 LÓGICA NUEVA: REVERSAR TARJETAS/CHEQUES EN CHEQ_TARJ_CLI
                pagos_orig = CheqTarjCli.objects.filter(movim=movim_original)
                for pago in pagos_orig:
                    CheqTarjCli.objects.create(
                        movim=nuevo_movim,  # Lo atamos a la N/C
                        origen='N/C',
                        cod_cli=pago.cod_cli,
                        tipo=pago.tipo,
                        importe=-pago.importe, # ⚠️ Importe NEGATIVO para cancelar el cupón
                        fecha_rece=timezone.now(),
                        fecha_vto=pago.fecha_vto,
                        id_comprob=nc.id_comprob,
                        cod_comprob=nc.cod_comprob,
                        nro_comprob=nc.nro_comprob,
                        cod_entidad=pago.cod_entidad,
                        entidad=pago.entidad,
                        numero=pago.numero,
                        moneda=pago.moneda,
                        cuota=pago.cuota,
                        estado='ANULADO', # Marcamos el reverso como anulado/devuelto
                        procesado=0,
                        nro_caja=nc.nro_caja,
                        cajero=nc.cajero,
                        comprobante_tipo=nc.comprobante_tipo,
                        comprobante_letra=nc.comprobante_letra,
                        comprobante_pto_vta=nc.comprobante_pto_vta
                    )

            # 7. Marcar la factura original como procesada/anulada para que no la vuelvan a tocar
            Ventas.objects.filter(movim=movim_original).update(procesado=-1)

            return Response({
                "status": "success", 
                "mensaje": f"Se emitió la {nc.comprobante_tipo} ({nc.cod_comprob}) N° {nc.nro_comprob} correctamente. El dinero y el stock han sido revertidos."
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({"status": "error", "mensaje": f"Error al emitir NC: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)