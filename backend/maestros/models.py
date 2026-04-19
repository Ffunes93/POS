from django.db import models



class Articulos(models.Model):
    cod_art = models.CharField(primary_key=True, max_length=40)
    rubro = models.CharField(max_length=4, blank=True, null=True)
    subrubro = models.CharField(max_length=4, blank=True, null=True)
    nombre = models.CharField(max_length=50)
    costo_ult = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    costo_pond = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    stock = models.DecimalField(max_digits=9, decimal_places=3, blank=True, null=True)
    stock_min = models.DecimalField(max_digits=9, decimal_places=3, blank=True, null=True)
    stock_max = models.DecimalField(max_digits=9, decimal_places=3, blank=True, null=True)
    stock_ini = models.DecimalField(max_digits=9, decimal_places=3, blank=True, null=True)
    stock_ini_fec = models.DateTimeField(blank=True, null=True)
    precio_1 = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    precio_2 = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    precio_3 = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    precio_4 = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    precio_5 = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    precio_6 = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    precio_7 = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    precio_8 = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    precio_9 = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    precio_10 = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    precio_11 = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    precio_12 = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    ubicacion = models.CharField(max_length=5, blank=True, null=True)
    iva = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    ult_compra = models.DateTimeField(blank=True, null=True)
    ult_venta = models.DateTimeField(blank=True, null=True)
    unidad = models.CharField(max_length=3, blank=True, null=True)
    estado = models.IntegerField(blank=True, null=True)
    artic_prov = models.CharField(max_length=16, blank=True, null=True)
    artic_obs = models.CharField(max_length=250, blank=True, null=True)
    noactualiza = models.IntegerField(blank=True, null=True)
    modifica_uni = models.IntegerField(blank=True, null=True)
    moneda = models.SmallIntegerField(blank=True, null=True)
    libre = models.SmallIntegerField(blank=True, null=True)
    padre1_hijo2 = models.IntegerField(blank=True, null=True)
    es_combo = models.IntegerField(blank=True, null=True)
    usuario = models.CharField(max_length=20, blank=True, null=True)
    fecha_mod = models.DateTimeField(blank=True, null=True)
    barra = models.CharField(max_length=50, blank=True, null=True)
    impuesto_ng = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    pedido_multiplo = models.IntegerField(blank=True, null=True)
    pedido_estado_inventario = models.IntegerField(blank=True, null=True)
    existe_en_algun_kit = models.IntegerField(blank=True, null=True)
    clase = models.CharField(max_length=3, blank=True, null=True)
    existe_en_alguna_promo = models.IntegerField(blank=True, null=True)
    ultima_actu_precio = models.DateTimeField(blank=True, null=True)
    codigo_proveedor = models.CharField(max_length=20, blank=True, null=True)
    unidad2 = models.CharField(max_length=3, blank=True, null=True)
    factor_conv = models.FloatField(blank=True, null=True)
    p5329 = models.IntegerField(blank=True, null=True)
    iva7 = models.IntegerField(blank=True, null=True)
    piva7 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cant_limi_mayo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    uniporbulto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'articulos'


class ArticulosBom(models.Model):
    id = models.BigAutoField(primary_key=True)
    cod_padre = models.CharField(max_length=40, blank=True, null=True)
    cod_hijo = models.CharField(max_length=40, blank=True, null=True)
    cant_hijo = models.DecimalField(db_column='Cant_hijo', max_digits=10, decimal_places=2)  # Field name made lowercase.
    usuario = models.CharField(max_length=20, blank=True, null=True)
    fecha_mod = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'articulos_bom'


class ArticulosEstadoInventario(models.Model):
    estado = models.IntegerField()
    detalle = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'articulos_estado_inventario'


class ArticulosIvas(models.Model):
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'articulos_ivas'


class ArticulosPrecioHistorico(models.Model):
    id = models.BigAutoField(primary_key=True)
    cod_art = models.CharField(max_length=40)
    precio_anterior_publico = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    precio_nuevo_publico = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    precio_anterior_mayorista = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    precio_nuevo_mayorista = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    ultima_actu_precio = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'articulos_precio_historico'


class ArticulosRubros(models.Model):
    codigo = models.CharField(primary_key=True, max_length=4)
    nombre = models.CharField(max_length=20)
    usuario = models.CharField(max_length=10, blank=True, null=True)
    fecha_hora = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'articulos_rubros'


class ArticulosSubrub(models.Model):
    codigo = models.CharField(primary_key=True, max_length=4)
    nombre = models.CharField(max_length=20)
    usuario = models.CharField(max_length=20, blank=True, null=True)
    fecha_hora = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'articulos_subrub'


class ArticulosUnidades(models.Model):
    unidad = models.CharField(max_length=3, blank=True, null=True)
    detalle = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'articulos_unidades'


class Billetes(models.Model):
    denominacion = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'billetes'


class Bitacora(models.Model):
    movim = models.AutoField(primary_key=True)
    inicio = models.IntegerField(blank=True, null=True)
    fin = models.IntegerField(blank=True, null=True)
    fecha = models.DateTimeField(blank=True, null=True)
    operador = models.SmallIntegerField(blank=True, null=True)
    puesto = models.CharField(max_length=15, blank=True, null=True)
    usuario = models.CharField(max_length=15, blank=True, null=True)
    fiscal_error = models.CharField(max_length=25, blank=True, null=True)
    fiscal_flag = models.FloatField(blank=True, null=True)
    fiscal_terr = models.CharField(max_length=3, blank=True, null=True)
    tipo_evento = models.IntegerField(blank=True, null=True, db_comment='1 - actualizacion , 2 - Envio Data a Centralizador')

    class Meta:
        managed = False
        db_table = 'bitacora'


class Cabcompraproc(models.Model):
    id_unico = models.IntegerField(primary_key=True)
    cod_cli = models.IntegerField()
    nombre_cli = models.CharField(max_length=60)
    cond_iva = models.IntegerField(blank=True, null=True)
    domicilio = models.TextField(blank=True, null=True)
    tipo_doc = models.CharField(max_length=4)
    nro_doc = models.CharField(max_length=13, blank=True, null=True)
    fecha = models.DateTimeField()
    neto = models.DecimalField(max_digits=11, decimal_places=2)
    iva = models.DecimalField(max_digits=11, decimal_places=2)
    exento = models.DecimalField(max_digits=11, decimal_places=2)
    percepcion_caba = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    percepcion_bsas = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    percepcion_ib = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    impuestos_internos = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(max_digits=11, decimal_places=2)
    observac = models.CharField(max_length=100, blank=True, null=True)
    p_estado_posone = models.IntegerField(blank=True, null=True)
    p_fec_estado = models.DateTimeField(blank=True, null=True)
    p_us_estado = models.CharField(max_length=20, blank=True, null=True)
    p_usuario = models.CharField(max_length=20, blank=True, null=True)
    p_fecha_mod = models.DateTimeField()
    p_compr_tipo = models.CharField(max_length=2, blank=True, null=True)
    p_compr_letra = models.CharField(max_length=2, blank=True, null=True)
    p_compr_pto_vta = models.CharField(max_length=4, blank=True, null=True)
    p_compr_numero = models.PositiveBigIntegerField()
    p_cae = models.CharField(max_length=20, blank=True, null=True)
    p_fecha_emision = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cabcompraproc'


class Cajas(models.Model):
    id = models.BigAutoField(primary_key=True)
    cajero = models.IntegerField()
    fecha_open = models.DateTimeField()
    fecha_close = models.DateTimeField(blank=True, null=True)
    saldo_ini_billetes = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    dife_caja_anterior = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    saldo_ini_cupones = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    saldo_final_billetes = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    saldo_final_cupones = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    ventas = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    dife_billetes = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    dife_cupones = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    con_diferencias = models.IntegerField(blank=True, null=True)
    deja_billetes = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    cta_cte = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    otros_ingresos = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    otros_egresos = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    estado = models.IntegerField(db_comment='1 abierta, 2 cerrada')
    procesado = models.IntegerField(blank=True, null=True)
    nro_lote = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cajas'


class CajasDet(models.Model):
    id = models.BigAutoField(primary_key=True)
    nro_caja = models.PositiveIntegerField()
    tipo = models.CharField(max_length=10, blank=True, null=True)
    forma = models.CharField(max_length=50, blank=True, null=True)
    nombre = models.CharField(max_length=50, blank=True, null=True)
    lote_vta = models.CharField(max_length=20, blank=True, null=True)
    importe_cajero = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    importe_real = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)
    nro_lote = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cajas_det'


class CajasRetiros(models.Model):
    id = models.BigAutoField(primary_key=True)
    cajero = models.IntegerField()
    fecha_open = models.DateTimeField()
    retiro = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cajas_retiros'


class CajasRetirosDet(models.Model):
    id = models.BigAutoField(primary_key=True)
    cajero = models.IntegerField()
    fecha_open = models.DateTimeField()
    id_retiro = models.BigIntegerField()
    denominacion = models.IntegerField(blank=True, null=True)
    cantidad = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cajas_retiros_det'


class CheqTarjCli(models.Model):
    id = models.BigAutoField(primary_key=True)
    movim = models.PositiveIntegerField()
    origen = models.CharField(max_length=3)
    cod_cli = models.IntegerField()
    tipo = models.CharField(max_length=3)
    importe = models.DecimalField(max_digits=11, decimal_places=2)
    fecha_rece = models.DateTimeField()
    fecha_vto = models.DateTimeField(blank=True, null=True)
    id_comprob = models.IntegerField(blank=True, null=True)
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.BigIntegerField()
    cod_entidad = models.IntegerField(blank=True, null=True)
    entidad = models.CharField(max_length=20, blank=True, null=True)
    cod_cuota = models.IntegerField(blank=True, null=True)
    titular = models.CharField(max_length=30, blank=True, null=True)
    numero = models.PositiveBigIntegerField(blank=True, null=True)
    observac_1 = models.CharField(max_length=100, blank=True, null=True)
    moneda = models.SmallIntegerField(blank=True, null=True)
    cuota = models.SmallIntegerField(blank=True, null=True)
    estado = models.CharField(max_length=11, blank=True, null=True)
    pendiente = models.CharField(max_length=1, blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)
    nro_lote = models.IntegerField(blank=True, null=True)
    cod_reten = models.BigIntegerField(blank=True, null=True)
    usuario = models.CharField(max_length=20, blank=True, null=True)
    fecha_modificacion = models.DateTimeField(blank=True, null=True)
    cajero = models.IntegerField(blank=True, null=True)
    nro_caja = models.BigIntegerField(blank=True, null=True)
    comprobante_tipo = models.CharField(max_length=2, blank=True, null=True)
    comprobante_letra = models.CharField(max_length=2, blank=True, null=True)
    comprobante_pto_vta = models.CharField(max_length=4, blank=True, null=True)
    anulado = models.CharField(max_length=1, blank=True, null=True)
    recargo = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    recargo_iva = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    codigo_banco = models.CharField(max_length=20, blank=True, null=True)
    codigo_pago = models.CharField(max_length=20, blank=True, null=True)
    recargo10 = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    recargo_iva10 = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    recargo0 = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    idpagos = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cheq_tarj_cli'


class CheqTarjProv(models.Model):
    id = models.BigAutoField(primary_key=True)
    movim = models.PositiveIntegerField()
    origen = models.CharField(max_length=3)
    cod_prov = models.IntegerField()
    tipo = models.CharField(max_length=3)
    importe = models.DecimalField(max_digits=11, decimal_places=2)
    fecha_rece = models.DateTimeField()
    fecha_vto = models.DateTimeField(blank=True, null=True)
    id_comprob = models.IntegerField(blank=True, null=True)
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.BigIntegerField()
    cod_entidad = models.CharField(max_length=10, blank=True, null=True)
    entidad = models.CharField(max_length=20, blank=True, null=True)
    titular = models.CharField(max_length=15, blank=True, null=True)
    numero = models.CharField(max_length=16, blank=True, null=True)
    observac_1 = models.CharField(max_length=100, blank=True, null=True)
    moneda = models.SmallIntegerField(blank=True, null=True)
    estado = models.CharField(max_length=11, blank=True, null=True)
    ban_cuenta = models.BigIntegerField(blank=True, null=True)
    pendiente = models.CharField(max_length=1, blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)
    nro_lote = models.IntegerField(blank=True, null=True)
    usuario = models.CharField(max_length=20, blank=True, null=True)
    fecha_mod = models.DateTimeField(blank=True, null=True)
    cajero = models.IntegerField(blank=True, null=True)
    nro_caja = models.BigIntegerField(blank=True, null=True)
    comprobante_tipo = models.CharField(max_length=2, blank=True, null=True)
    comprobante_letra = models.CharField(max_length=2, blank=True, null=True)
    comprobante_pto_vta = models.CharField(max_length=4, blank=True, null=True)
    anulado = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cheq_tarj_prov'


class Clientes(models.Model):
    cod_cli = models.IntegerField(primary_key=True)
    denominacion = models.CharField(max_length=60)
    contacto = models.CharField(max_length=60, blank=True, null=True)
    domicilio = models.TextField(blank=True, null=True)
    cod_postal = models.BigIntegerField(blank=True, null=True)
    localidad = models.CharField(max_length=40, blank=True, null=True)
    telefono = models.CharField(max_length=40, blank=True, null=True)
    cond_iva = models.IntegerField(blank=True, null=True)
    nro_cuit = models.CharField(max_length=13, blank=True, null=True)
    cond_pago = models.CharField(max_length=3, blank=True, null=True)
    estado_baja = models.IntegerField(blank=True, null=True)
    observac = models.TextField(blank=True, null=True)
    mail = models.CharField(max_length=40, blank=True, null=True)
    fantasia = models.CharField(max_length=60, blank=True, null=True)
    fecha_mod = models.DateTimeField(blank=True, null=True)
    usuario = models.CharField(max_length=20, blank=True, null=True)
    percepcion_iibb = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    credito_cc = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    lista_precio = models.IntegerField(blank=True, null=True)
    codigo_erp_iibb = models.CharField(max_length=20, blank=True, null=True)
    libre1 = models.IntegerField(blank=True, null=True)
    libre2 = models.CharField(max_length=20, blank=True, null=True)
    perce_caba = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    perce_bsas = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    erp_caba = models.CharField(max_length=20, blank=True, null=True)
    erp_bsas = models.CharField(max_length=20, blank=True, null=True)
    p5329 = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clientes'


class Compras(models.Model):
    movim = models.PositiveIntegerField(primary_key=True)
    id_comprob = models.PositiveIntegerField()
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.BigIntegerField()
    cod_prov = models.IntegerField()
    fecha_comprob = models.DateTimeField()
    fecha_recep = models.DateTimeField(blank=True, null=True)
    fecha_vto = models.DateTimeField()
    neto = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    iva_1 = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    iva_2 = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    descuento = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    tot_general = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    actualiz_stock = models.CharField(max_length=1, blank=True, null=True)
    nro_remito = models.BigIntegerField(blank=True, null=True)
    anulado = models.CharField(max_length=1, blank=True, null=True)
    observac = models.TextField()
    moneda = models.SmallIntegerField(blank=True, null=True)
    valordolar = models.DecimalField(max_digits=9, decimal_places=3, blank=True, null=True)
    ret_iibb = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    ret_iva = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    ret_gan = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    mes = models.SmallIntegerField(blank=True, null=True)
    anio = models.SmallIntegerField(blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)
    nro_lote = models.IntegerField(blank=True, null=True)
    destino = models.IntegerField(blank=True, null=True, db_comment='Destino de Transferencia')
    usuario = models.CharField(max_length=20, blank=True, null=True)
    fecha_mod = models.DateTimeField(blank=True, null=True)
    cajero = models.IntegerField(blank=True, null=True)
    estado_pedido = models.IntegerField(blank=True, null=True, db_comment='1-Pendiente, 2-Confirmado')
    nro_caja = models.IntegerField(blank=True, null=True)
    categoria = models.CharField(max_length=4, blank=True, null=True)
    comprobante_tipo = models.CharField(max_length=3, blank=True, null=True)
    comprobante_letra = models.CharField(max_length=2, blank=True, null=True)
    comprobante_pto_vta = models.CharField(max_length=4, blank=True, null=True)
    remito_erp = models.CharField(max_length=50, blank=True, null=True)
    factura_erp = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'compras'


class ComprasCategorias(models.Model):
    codigo = models.CharField(primary_key=True, max_length=4)
    nombre = models.CharField(max_length=20)
    usuario = models.CharField(max_length=10, blank=True, null=True)
    fecha_hora = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'compras_categorias'


class ComprasDet(models.Model):
    id = models.BigAutoField(primary_key=True)
    movim = models.PositiveIntegerField()
    id_comprob = models.IntegerField()
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.BigIntegerField()
    cod_articulo = models.CharField(max_length=40)
    nom_articulo = models.CharField(max_length=50, blank=True, null=True)
    cantidad = models.DecimalField(max_digits=9, decimal_places=3)
    precio_unit = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    descuento = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    cod_prov = models.IntegerField(blank=True, null=True)
    p_iva = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    v_iva = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    stock_fecha = models.DateTimeField(blank=True, null=True)
    stock_detalle = models.CharField(max_length=40, blank=True, null=True)
    pedido_stock = models.DecimalField(max_digits=14, decimal_places=3, blank=True, null=True)
    pedido_stock_pedi = models.DecimalField(max_digits=14, decimal_places=3, blank=True, null=True)
    pedido_stock_minimo = models.DecimalField(max_digits=14, decimal_places=3, blank=True, null=True)
    comprobante_tipo = models.CharField(max_length=3, blank=True, null=True)
    comprobante_letra = models.CharField(max_length=2, blank=True, null=True)
    comprobante_pto_vta = models.CharField(max_length=4, blank=True, null=True)
    nro_lote = models.IntegerField(blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'compras_det'


class CondIva(models.Model):
    tipo = models.CharField(max_length=15)
    codigo = models.IntegerField(primary_key=True)
    tipofac = models.CharField(max_length=1)
    aliciva = models.DecimalField(max_digits=4, decimal_places=2)
    recargoiva = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'cond_iva'


class ControlHorario(models.Model):
    caja_numero = models.BigIntegerField(db_column='Caja_Numero')  # Field name made lowercase.
    cajero = models.CharField(db_column='Cajero', max_length=50, db_collation='latin1_swedish_ci', blank=True, null=True)  # Field name made lowercase.
    fecha_inicio = models.CharField(db_column='Fecha_Inicio', max_length=10, db_collation='utf8mb4_0900_ai_ci', blank=True, null=True)  # Field name made lowercase.
    hora_inicio = models.CharField(db_column='Hora_Inicio', max_length=10, db_collation='utf8mb4_0900_ai_ci', blank=True, null=True)  # Field name made lowercase.
    fecha_fin = models.CharField(db_column='Fecha_Fin', max_length=10, db_collation='utf8mb4_0900_ai_ci', blank=True, null=True)  # Field name made lowercase.
    hora_cierre = models.CharField(db_column='Hora_Cierre', max_length=10, db_collation='utf8mb4_0900_ai_ci', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'control_horario'


class Cotiza(models.Model):
    movim = models.PositiveIntegerField(primary_key=True)
    id_comprob = models.IntegerField()
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.BigIntegerField()
    cod_cli = models.IntegerField()
    nom_cli = models.CharField(max_length=100, blank=True, null=True)
    fecha_fact = models.DateTimeField()
    fecha_vto = models.DateTimeField()
    neto = models.DecimalField(max_digits=11, decimal_places=2)
    iva_1 = models.DecimalField(max_digits=11, decimal_places=2)
    exento = models.DecimalField(max_digits=11, decimal_places=2)
    total = models.DecimalField(max_digits=11, decimal_places=2)
    descuento = models.DecimalField(max_digits=9, decimal_places=2)
    tot_general = models.DecimalField(max_digits=11, decimal_places=2)
    vendedor = models.SmallIntegerField(blank=True, null=True)
    comision = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    anulado = models.CharField(max_length=1, blank=True, null=True)
    observac = models.CharField(max_length=50, blank=True, null=True)
    moneda = models.SmallIntegerField(blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)
    nro_lote = models.IntegerField(blank=True, null=True)
    dolar_dia = models.DecimalField(max_digits=9, decimal_places=3, blank=True, null=True)
    usuario = models.CharField(max_length=20, blank=True, null=True)
    fecha_mod = models.DateTimeField()
    cajero = models.IntegerField()
    nro_caja = models.BigIntegerField(blank=True, null=True)
    comprobante_tipo = models.CharField(max_length=2, blank=True, null=True)
    comprobante_letra = models.CharField(max_length=2, blank=True, null=True)
    comprobante_pto_vta = models.CharField(max_length=4, blank=True, null=True)
    utilizada = models.IntegerField(blank=True, null=True, db_comment='0 no Utilizada, 1-Utilzada')
    percepciones = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cotiza'


class CotizaDet(models.Model):
    id = models.BigAutoField(primary_key=True)
    movim = models.PositiveIntegerField()
    id_comprob = models.IntegerField()
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.BigIntegerField()
    cod_articulo = models.CharField(max_length=40)
    cantidad = models.DecimalField(max_digits=9, decimal_places=3)
    precio_unit = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unit_base = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=9, decimal_places=2)
    lote = models.IntegerField(blank=True, null=True)
    detalle = models.CharField(max_length=45)
    p_iva = models.DecimalField(max_digits=4, decimal_places=2)
    v_iva = models.DecimalField(max_digits=14, decimal_places=2)
    v_iva_base = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    impuesto_unitario = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    subtotal_base = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    total_base = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    combo = models.IntegerField(blank=True, null=True)
    item_libre = models.CharField(max_length=45, blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)
    nro_lote = models.IntegerField(blank=True, null=True)
    es_promo = models.IntegerField(blank=True, null=True)
    comprobante_tipo = models.CharField(max_length=2, blank=True, null=True)
    comprobante_letra = models.CharField(max_length=2, blank=True, null=True)
    comprobante_pto_vta = models.CharField(max_length=4, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cotiza_det'


class CtaCteCli(models.Model):
    id = models.BigAutoField(primary_key=True)
    movim = models.IntegerField()
    origen = models.CharField(max_length=3)
    cod_cli = models.ForeignKey(Clientes, models.DO_NOTHING, db_column='cod_cli')
    fecha = models.DateTimeField()
    fecha_oper = models.DateTimeField(blank=True, null=True)
    id_comprob = models.IntegerField()
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.BigIntegerField()
    detalle = models.CharField(max_length=50)
    imported = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    importeh = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    moneda = models.SmallIntegerField(blank=True, null=True)
    anulado = models.CharField(max_length=1, blank=True, null=True)
    cuota = models.SmallIntegerField(blank=True, null=True)
    cobrado = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    parcial = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    fec_vto = models.DateTimeField(blank=True, null=True)
    saldo = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    compro_r = models.CharField(max_length=2, blank=True, null=True)
    nro_compro_r = models.BigIntegerField(blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)
    nro_lote = models.IntegerField(blank=True, null=True)
    fec_mod = models.DateTimeField(blank=True, null=True)
    usuario = models.CharField(max_length=20, blank=True, null=True)
    cajero = models.IntegerField(blank=True, null=True)
    nro_caja = models.IntegerField(blank=True, null=True)
    comprobante_tipo = models.CharField(max_length=2, blank=True, null=True)
    comprobante_letra = models.CharField(max_length=2, blank=True, null=True)
    comprobante_pto_vta = models.CharField(max_length=4, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cta_cte_cli'


class CtaCteProv(models.Model):
    id = models.BigAutoField(primary_key=True)
    movim = models.IntegerField()
    origen = models.CharField(max_length=3)
    cod_prov = models.IntegerField()
    fecha = models.DateTimeField()
    fecha_oper = models.DateTimeField()
    id_comprob = models.IntegerField()
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.BigIntegerField()
    detalle = models.CharField(max_length=50)
    imported = models.DecimalField(max_digits=11, decimal_places=2)
    importeh = models.DecimalField(max_digits=11, decimal_places=2)
    moneda = models.SmallIntegerField()
    anulado = models.CharField(max_length=1)
    cuota = models.SmallIntegerField()
    cobrado = models.BigIntegerField()
    parcial = models.DecimalField(max_digits=9, decimal_places=2)
    fec_mod = models.DateTimeField()
    cobrado_tmp = models.BigIntegerField()
    parcial_tmp = models.DecimalField(max_digits=9, decimal_places=2)
    saldo = models.DecimalField(max_digits=11, decimal_places=2)
    compro_r = models.CharField(max_length=2)
    nro_compro_r = models.BigIntegerField()
    procesado = models.IntegerField(blank=True, null=True)
    nro_lote = models.IntegerField()
    usuario = models.CharField(max_length=20, blank=True, null=True)
    fecha_mod = models.DateTimeField(blank=True, null=True)
    comprobante_letra = models.CharField(max_length=2, blank=True, null=True)
    comprobante_tipo = models.CharField(max_length=2, blank=True, null=True)
    comprobante_pto_vta = models.CharField(max_length=4, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cta_cte_prov'


class CtaDevoluciones(models.Model):
    id = models.BigAutoField(primary_key=True)
    movim = models.IntegerField()
    origen = models.CharField(max_length=3)
    cod_cli = models.IntegerField()
    fecha = models.DateTimeField()
    id_comprob = models.IntegerField()
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.BigIntegerField()
    detalle = models.CharField(max_length=50)
    detalle_utilizada = models.CharField(max_length=50, blank=True, null=True)
    imported = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    importeh = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    anulado = models.CharField(max_length=1, blank=True, null=True)
    utilizado = models.IntegerField(blank=True, null=True)
    procesado = models.IntegerField()
    nro_lote = models.IntegerField(blank=True, null=True)
    fec_mod = models.DateTimeField()
    usuario = models.CharField(max_length=20, blank=True, null=True)
    cajero = models.IntegerField(blank=True, null=True)
    nro_caja = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cta_devoluciones'


class Descuentos(models.Model):
    descuento_nom = models.CharField(max_length=25)
    porcentaje = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    aplicamayorista = models.IntegerField(db_column='aplicaMayorista', blank=True, null=True)  # Field name made lowercase.
    activo = models.IntegerField(db_column='Activo', blank=True, null=True)  # Field name made lowercase.
    cod_erp = models.CharField(db_column='cod_ERP', max_length=20, blank=True, null=True)  # Field name made lowercase.
    tipo_erp = models.CharField(db_column='tipo_ERP', max_length=20, blank=True, null=True)  # Field name made lowercase.
    conceptoerp = models.CharField(db_column='conceptoERP', max_length=20, blank=True, null=True)  # Field name made lowercase.
    digitostarjeta = models.IntegerField(db_column='digitosTarjeta', blank=True, null=True)  # Field name made lowercase.
    lunes = models.IntegerField(blank=True, null=True)
    martes = models.IntegerField(blank=True, null=True)
    miercoles = models.IntegerField(blank=True, null=True)
    jueves = models.IntegerField(blank=True, null=True)
    viernes = models.IntegerField(blank=True, null=True)
    sabado = models.IntegerField(blank=True, null=True)
    domingo = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'descuentos'


class Detcompraproc(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_unico = models.IntegerField()
    cod_articulo = models.CharField(max_length=40)
    nom_articulo = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=9, decimal_places=3)
    precio_unit = models.DecimalField(max_digits=11, decimal_places=2)
    p_iva = models.DecimalField(max_digits=4, decimal_places=2)
    total_item = models.DecimalField(max_digits=11, decimal_places=2)
    precio_unit_base = models.DecimalField(max_digits=12, decimal_places=4)
    p5329 = models.DecimalField(max_digits=11, decimal_places=2)
    impuesto_unitario = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'detcompraproc'


class FeLog(models.Model):
    fecha = models.DateTimeField(blank=True, null=True)
    log = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fe_log'


class FeMail(models.Model):
    server = models.CharField(max_length=100, blank=True, null=True)
    usuario = models.CharField(max_length=100, blank=True, null=True)
    clave = models.CharField(max_length=100, blank=True, null=True)
    usassl = models.IntegerField(db_column='usaSSL', blank=True, null=True)  # Field name made lowercase.
    puerto = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fe_mail'


class FeParam(models.Model):
    id_fnc = models.CharField(max_length=20, blank=True, null=True)
    url_autentica = models.CharField(max_length=250, blank=True, null=True)
    url_homologa = models.CharField(max_length=255, blank=True, null=True)
    url_produccion = models.CharField(max_length=255, blank=True, null=True)
    servicio = models.CharField(max_length=20, blank=True, null=True)
    ruta_certificado = models.CharField(max_length=255, blank=True, null=True)
    estado_homologa = models.IntegerField(blank=True, null=True)
    clavecertificado = models.CharField(db_column='claveCertificado', max_length=255, blank=True, null=True)  # Field name made lowercase.
    estado_produccion = models.IntegerField(blank=True, null=True)
    razonsocial = models.CharField(db_column='RazonSocial', max_length=200, blank=True, null=True)  # Field name made lowercase.
    domicilio = models.CharField(db_column='Domicilio', max_length=200, blank=True, null=True)  # Field name made lowercase.
    condicioniva = models.CharField(db_column='CondicionIVA', max_length=100, blank=True, null=True)  # Field name made lowercase.
    iibb = models.CharField(db_column='IIBB', max_length=50, blank=True, null=True)  # Field name made lowercase.
    inicioactividades = models.CharField(db_column='InicioActividades', max_length=10, blank=True, null=True)  # Field name made lowercase.
    usa_persistente = models.IntegerField(blank=True, null=True)
    copias = models.IntegerField(blank=True, null=True)
    dias = models.IntegerField(blank=True, null=True)
    cbu = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fe_param'


class FeTas(models.Model):
    fecha = models.DateTimeField(blank=True, null=True)
    ticketacceso = models.TextField(db_column='ticketAcceso', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'fe_tas'


class FeTipocompCli(models.Model):
    id_compro = models.IntegerField(primary_key=True)
    cod_compro = models.CharField(max_length=2)
    nom_compro = models.CharField(max_length=20)
    ultnro = models.BigIntegerField()
    copias = models.SmallIntegerField()
    ultdia = models.DateTimeField()
    punto_venta = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'fe_tipocomp_cli'
        unique_together = (('cod_compro', 'punto_venta'),)


class FormaPago(models.Model):
    id = models.SmallAutoField(primary_key=True)
    codigo = models.CharField(max_length=3)
    descripcion = models.CharField(max_length=20)
    activa = models.IntegerField()
    moneda = models.SmallIntegerField()
    usar_en_cta_cte = models.IntegerField()
    usar_en_arqueo = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'forma_pago'


class FormaPagoCopy(models.Model):
    id = models.SmallAutoField(primary_key=True)
    codigo = models.CharField(max_length=3)
    descripcion = models.CharField(max_length=20)
    activa = models.IntegerField()
    moneda = models.SmallIntegerField()
    usar_en_cta_cte = models.IntegerField()
    usar_en_arqueo = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'forma_pago_copy'


class FormaPagoCuotas(models.Model):
    id = models.BigAutoField(primary_key=True)
    forma_pago_det_padre = models.IntegerField(blank=True, null=True)
    detalle = models.CharField(max_length=100, blank=True, null=True)
    cuotas = models.IntegerField(blank=True, null=True)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    no_activo = models.IntegerField(blank=True, null=True)
    codigo_erp = models.CharField(max_length=20, blank=True, null=True)
    codigo_banco = models.CharField(max_length=20, blank=True, null=True)
    codigo_pago = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'forma_pago_cuotas'


class FormaPagoCuotasCopy(models.Model):
    id = models.BigAutoField(primary_key=True)
    forma_pago_det_padre = models.IntegerField(blank=True, null=True)
    detalle = models.CharField(max_length=100, blank=True, null=True)
    cuotas = models.IntegerField(blank=True, null=True)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    no_activo = models.IntegerField(blank=True, null=True)
    codigo_erp = models.CharField(max_length=20, blank=True, null=True)
    codigo_banco = models.CharField(max_length=20, blank=True, null=True)
    codigo_pago = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'forma_pago_cuotas_copy'


class FormaPagoDet(models.Model):
    nombre = models.CharField(db_column='Nombre', max_length=100)  # Field name made lowercase.
    debito = models.IntegerField(blank=True, null=True)
    credito = models.IntegerField(blank=True, null=True)
    banco = models.IntegerField(blank=True, null=True)
    no_activa = models.IntegerField(blank=True, null=True)
    cod_erp = models.CharField(max_length=10, blank=True, null=True)
    libre1 = models.CharField(max_length=20, blank=True, null=True)
    tranfe = models.IntegerField(blank=True, null=True)
    nrocuentabancaria = models.CharField(db_column='nroCuentaBancaria', max_length=50, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'forma_pago_det'


class FormaPagoDetCopy(models.Model):
    nombre = models.CharField(db_column='Nombre', max_length=100)  # Field name made lowercase.
    debito = models.IntegerField(blank=True, null=True)
    credito = models.IntegerField(blank=True, null=True)
    banco = models.IntegerField(blank=True, null=True)
    no_activa = models.IntegerField(blank=True, null=True)
    cod_erp = models.CharField(max_length=10, blank=True, null=True)
    libre1 = models.CharField(max_length=20, blank=True, null=True)
    tranfe = models.IntegerField(blank=True, null=True)
    nrocuentabancaria = models.CharField(db_column='nroCuentaBancaria', max_length=50, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'forma_pago_det_copy'


class FormaPagoPromos(models.Model):
    id_erp = models.IntegerField()
    codigo_erp = models.CharField(max_length=50)
    banco_cod = models.CharField(max_length=50)
    concepto_erp = models.CharField(max_length=50)
    banco_suc = models.CharField(max_length=50)
    promo_nombre = models.CharField(max_length=50)
    noactiva = models.IntegerField()
    descuento = models.DecimalField(max_digits=20, decimal_places=6)
    acumulable = models.IntegerField()
    dias = models.CharField(max_length=50)
    desde = models.DateTimeField()
    hasta = models.DateTimeField()
    debito = models.IntegerField()
    credito = models.IntegerField()
    cuotas = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'forma_pago_promos'


class FormaPagoPromosArtis(models.Model):
    id_det = models.PositiveIntegerField()
    cod_art = models.CharField(max_length=50)
    noactivoa = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'forma_pago_promos_artis'


class Listasprecios(models.Model):
    codigo = models.IntegerField(blank=True, null=True)
    nombrelista = models.CharField(db_column='NombreLista', max_length=20)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'listasprecios'


class Logs(models.Model):
    fecha = models.DateTimeField(blank=True, null=True)
    detalle = models.CharField(max_length=255, blank=True, null=True)
    comprobante_pto_vta = models.CharField(max_length=5, blank=True, null=True)
    cod_comprob = models.CharField(max_length=2, blank=True, null=True)
    nro_comprob = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'logs'


class LogsItems(models.Model):
    id = models.BigAutoField(primary_key=True)
    cajero = models.IntegerField()
    fecha = models.DateTimeField()
    cantidad = models.DecimalField(max_digits=9, decimal_places=3)
    cod_articulo = models.CharField(max_length=40)
    precio_unit = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.PositiveBigIntegerField()
    comprobante_pto_vta = models.CharField(max_length=4, blank=True, null=True)
    usuario = models.CharField(max_length=20, blank=True, null=True)
    obs = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'logs_items'


class Mensajes(models.Model):
    fecha = models.DateTimeField()
    mensaje = models.CharField(max_length=255, blank=True, null=True)
    origen = models.CharField(max_length=30, blank=True, null=True)
    leido = models.IntegerField()
    sucursal_origen = models.IntegerField()
    envia_a_todos = models.IntegerField(blank=True, null=True)
    enviado = models.IntegerField(blank=True, null=True)
    nro_lote = models.IntegerField(blank=True, null=True)
    id_sucursal_global = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mensajes'


class MenuNivel(models.Model):
    menu = models.CharField(max_length=25)
    nivel = models.IntegerField()
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    no_visible = models.IntegerField(blank=True, null=True)
    nombre_menu = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'menu_nivel'


class ParamPagos(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    nombre = models.CharField(max_length=50, blank=True, null=True)
    mail = models.CharField(max_length=50, blank=True, null=True)
    secret = models.CharField(max_length=100, blank=True, null=True)
    external_id = models.CharField(max_length=50, blank=True, null=True)
    terminal_id = models.CharField(max_length=50, blank=True, null=True)
    pide_mail = models.IntegerField(blank=True, null=True)
    pide_telefono = models.IntegerField(blank=True, null=True)
    en_produccion = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'param_pagos'


class Parametros(models.Model):
    puntoventa = models.IntegerField(db_column='puntoVenta', primary_key=True)  # Field name made lowercase.
    nombreempresa = models.CharField(db_column='NombreEmpresa', max_length=30, db_collation='latin1_swedish_ci')  # Field name made lowercase.
    nombresucursal = models.CharField(db_column='NombreSucursal', max_length=30, db_collation='latin1_swedish_ci', blank=True, null=True)  # Field name made lowercase.
    cond_iva = models.IntegerField(db_column='Cond_iva')  # Field name made lowercase.
    tipo_impresora = models.IntegerField(blank=True, null=True, db_comment='1 - Fiscal Hasar')
    modelo_impresora = models.IntegerField(db_column='Modelo_impresora', blank=True, null=True)  # Field name made lowercase.
    puerto_impresora = models.IntegerField(blank=True, null=True)
    ip_impresora = models.CharField(max_length=20, db_collation='latin1_swedish_ci', blank=True, null=True)
    usa_consfinal = models.IntegerField(blank=True, null=True)
    usa_cod_barra = models.IntegerField(blank=True, null=True)
    nro_lote = models.IntegerField(blank=True, null=True)
    fecha_cierre_zeta = models.DateTimeField(blank=True, null=True)
    fecha_actualiz_central = models.DateTimeField(blank=True, null=True)
    fecha_envio_data = models.DateTimeField(blank=True, null=True)
    cajero_activo = models.IntegerField(blank=True, null=True)
    fec_cajin = models.DateTimeField(blank=True, null=True)
    promo_mayorista = models.IntegerField(blank=True, null=True)
    promo_limite = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    paso_imagen = models.CharField(max_length=100, db_collation='latin1_swedish_ci')
    paso_documentos = models.CharField(max_length=100, db_collation='latin1_swedish_ci', blank=True, null=True)
    habilitapresupuesto = models.IntegerField(db_column='habilitaPresupuesto', blank=True, null=True)  # Field name made lowercase.
    pasologobig = models.CharField(db_column='pasoLogoBig', max_length=150, db_collation='latin1_swedish_ci')  # Field name made lowercase.
    pasologopeque = models.CharField(db_column='pasoLogoPeque', max_length=150, db_collation='latin1_swedish_ci')  # Field name made lowercase.
    barra_longitud = models.SmallIntegerField(blank=True, null=True)
    barra_inicio_desde = models.SmallIntegerField(blank=True, null=True)
    barra_inicio_hasta = models.SmallIntegerField(blank=True, null=True)
    barra_codigo_desde = models.SmallIntegerField(blank=True, null=True)
    barra_codigo_hasta = models.SmallIntegerField(blank=True, null=True)
    barra_ipc_desde = models.SmallIntegerField(blank=True, null=True)
    barra_ipc_hasta = models.SmallIntegerField(blank=True, null=True)
    barra_ipc = models.CharField(max_length=1, db_collation='latin1_swedish_ci', blank=True, null=True)
    punto_de_venta_fiscal = models.CharField(max_length=4, db_collation='latin1_swedish_ci', blank=True, null=True)
    limtepidedatosclientevarios = models.DecimalField(db_column='limtePideDatosClienteVarios', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    usapreciomayoristacomodescuento = models.IntegerField(db_column='usaPrecioMayoristaComoDescuento', blank=True, null=True)  # Field name made lowercase.
    limitevalidezcotizaciones = models.IntegerField(db_column='limiteValidezCotizaciones', blank=True, null=True)  # Field name made lowercase.
    canalventa = models.CharField(db_column='CanalVenta', max_length=50, db_collation='latin1_swedish_ci', blank=True, null=True)  # Field name made lowercase.
    canalventagrupo = models.CharField(db_column='CanalVentaGrupo', max_length=50, db_collation='latin1_swedish_ci', blank=True, null=True)  # Field name made lowercase.
    punto_de_venta_manual = models.CharField(max_length=4, db_collation='latin1_swedish_ci', blank=True, null=True)
    webservicebejerman = models.CharField(db_column='webServiceBejerman', max_length=200, db_collation='latin1_swedish_ci', blank=True, null=True)  # Field name made lowercase.
    webservicesync = models.CharField(db_column='webServiceSync', max_length=200, db_collation='latin1_swedish_ci', blank=True, null=True)  # Field name made lowercase.
    webservicelicencias = models.CharField(db_column='webServiceLicencias', max_length=200, blank=True, null=True)  # Field name made lowercase.
    imprime_rollo1_continuo2 = models.IntegerField(blank=True, null=True)
    pedidos_codigonp = models.CharField(db_column='pedidos_codigoNP', max_length=10, db_collation='latin1_swedish_ci', blank=True, null=True)  # Field name made lowercase.
    pedidos_codigocliente = models.IntegerField(db_column='pedidos_codigoCliente', blank=True, null=True)  # Field name made lowercase.
    no_usa_percepcion = models.IntegerField(blank=True, null=True)
    no_traer_clientes = models.IntegerField(blank=True, null=True)
    libre1 = models.IntegerField(blank=True, null=True)
    libre2 = models.IntegerField(blank=True, null=True)
    libre3 = models.CharField(max_length=30, db_collation='latin1_swedish_ci', blank=True, null=True)
    libre4 = models.CharField(max_length=30, db_collation='latin1_swedish_ci', blank=True, null=True)
    clave = models.CharField(max_length=50, db_collation='latin1_swedish_ci', blank=True, null=True)
    mailfran = models.CharField(max_length=50, blank=True, null=True)
    actuhora = models.CharField(max_length=10, blank=True, null=True)
    libre5 = models.CharField(max_length=30, blank=True, null=True)
    libre6 = models.IntegerField(blank=True, null=True)
    libre7 = models.IntegerField(blank=True, null=True)
    libre8 = models.IntegerField(blank=True, null=True)
    libre9 = models.IntegerField(blank=True, null=True)
    libre10 = models.IntegerField(blank=True, null=True)
    libre11 = models.IntegerField(blank=True, null=True)
    libre12 = models.IntegerField(blank=True, null=True)
    libre13 = models.IntegerField(blank=True, null=True)
    libre14 = models.IntegerField(blank=True, null=True)
    libre15 = models.IntegerField(blank=True, null=True)
    libre16 = models.IntegerField(blank=True, null=True)
    compro_inter = models.CharField(max_length=20, blank=True, null=True)
    clavefec = models.TextField(blank=True, null=True)
    libre17 = models.IntegerField(blank=True, null=True)
    mercadopago = models.IntegerField(blank=True, null=True)
    libre18 = models.IntegerField(blank=True, null=True)
    libre19 = models.IntegerField(blank=True, null=True)
    datosadicionales = models.IntegerField(blank=True, null=True)
    noesperacierrecaja = models.IntegerField(db_column='noEsperaCierreCaja', blank=True, null=True)  # Field name made lowercase.
    vendedorcentralizado = models.IntegerField(db_column='VendedorCentralizado', blank=True, null=True)  # Field name made lowercase.
    tipocodigobarra = models.IntegerField(db_column='tipoCodigoBarra', blank=True, null=True)  # Field name made lowercase.
    modulofe = models.TextField(db_column='moduloFE', blank=True, null=True)  # Field name made lowercase.
    barra_pesable = models.SmallIntegerField(blank=True, null=True)
    multicajeros = models.IntegerField(blank=True, null=True)
    monotributo = models.IntegerField(blank=True, null=True)
    presu_en_ticket = models.IntegerField(blank=True, null=True)
    limite5329 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    porce5329 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    params = models.JSONField(blank=True, null=True)
    nompresu = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'parametros'


class ParametrosErp(models.Model):
    cab_empresa = models.CharField(max_length=10, blank=True, null=True)
    cab_provincia = models.CharField(max_length=3, blank=True, null=True)
    cab_tipocambio = models.CharField(max_length=3, blank=True, null=True)
    cab_listaprecioa = models.CharField(db_column='cab_listaPrecioA', max_length=3, blank=True, null=True)  # Field name made lowercase.
    cab_listapreb = models.CharField(db_column='cab_listaPreB', max_length=3, blank=True, null=True)  # Field name made lowercase.
    item_iibb = models.CharField(db_column='item_IIBB', max_length=3, blank=True, null=True)  # Field name made lowercase.
    med_tipocambio = models.CharField(db_column='med_TipoCambio', max_length=3, blank=True, null=True)  # Field name made lowercase.
    med_cajaorigen = models.CharField(db_column='med_cajaOrigen', max_length=3, blank=True, null=True)  # Field name made lowercase.
    cod_cliente1 = models.CharField(max_length=6, blank=True, null=True)
    cod_cliente2 = models.CharField(max_length=6, blank=True, null=True)
    item_caba = models.CharField(max_length=4, blank=True, null=True)
    item_bsas = models.CharField(max_length=4, blank=True, null=True)
    cod_bco_tarjeta = models.CharField(max_length=3, blank=True, null=True)
    cod_flex_cheque = models.CharField(max_length=3, blank=True, null=True)
    cod_ingresostock = models.CharField(db_column='cod_IngresoStock', max_length=3, blank=True, null=True)  # Field name made lowercase.
    cod_salidastock = models.CharField(db_column='cod_SalidaStock', max_length=3, blank=True, null=True)  # Field name made lowercase.
    cod_tranfestock = models.CharField(db_column='cod_TranfeStock', max_length=3, blank=True, null=True)  # Field name made lowercase.
    cod_ajupositivo = models.CharField(db_column='cod_AjuPositivo', max_length=3, blank=True, null=True)  # Field name made lowercase.
    cod_ajunegativo = models.CharField(db_column='cod_AjuNegativo', max_length=3, blank=True, null=True)  # Field name made lowercase.
    cod_pedidos = models.CharField(db_column='cod_Pedidos', max_length=3, blank=True, null=True)  # Field name made lowercase.
    cod_causainve = models.CharField(db_column='cod_CausaInve', max_length=3, blank=True, null=True)  # Field name made lowercase.
    cod_causafrac = models.CharField(db_column='cod_CausaFrac', max_length=3, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'parametros_erp'


class PedidosDet(models.Model):
    id = models.BigAutoField(primary_key=True)
    movim = models.PositiveIntegerField()
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.BigIntegerField()
    cod_articulo = models.CharField(max_length=40)
    nom_articulo = models.CharField(max_length=50, blank=True, null=True)
    cantidad_pedida = models.DecimalField(max_digits=10, decimal_places=3)
    cantidad_ingresada = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    precio_unit = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    descuento = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    cod_prov = models.IntegerField(blank=True, null=True)
    p_iva = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    v_iva = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    stock_fecha = models.DateTimeField(blank=True, null=True)
    stock_detalle = models.CharField(max_length=40, blank=True, null=True)
    pedido_stock = models.IntegerField(blank=True, null=True)
    pedido_stock_pedi = models.IntegerField(blank=True, null=True)
    pedido_stock_minimo = models.IntegerField(blank=True, null=True)
    comprobante_tipo = models.CharField(max_length=3, blank=True, null=True)
    comprobante_letra = models.CharField(max_length=2, blank=True, null=True)
    comprobante_sucursal = models.CharField(max_length=4, blank=True, null=True)
    nro_lote = models.IntegerField(blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)
    factura_erp = models.CharField(max_length=50, blank=True, null=True)
    remito_erp = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pedidos_det'


class Promos(models.Model):
    id = models.BigIntegerField(primary_key=True)
    nombre_promo = models.CharField(max_length=50)
    no_activa = models.IntegerField(blank=True, null=True)
    lleva = models.IntegerField(blank=True, null=True)
    paga = models.IntegerField(blank=True, null=True)
    no_paga_porcentaje = models.IntegerField(blank=True, null=True)
    codigo_erp = models.CharField(max_length=50, blank=True, null=True)
    tasa_erp = models.CharField(max_length=10, blank=True, null=True)
    codvta_erp = models.CharField(max_length=10, blank=True, null=True)
    iva_erp = models.CharField(max_length=10, blank=True, null=True)
    acumulable = models.IntegerField(blank=True, null=True)
    desde = models.DateField(blank=True, null=True)
    hasta = models.DateField(blank=True, null=True)
    lunes = models.IntegerField(blank=True, null=True)
    martes = models.IntegerField(blank=True, null=True)
    miercoles = models.IntegerField(blank=True, null=True)
    jueves = models.IntegerField(blank=True, null=True)
    viernes = models.IntegerField(blank=True, null=True)
    sabado = models.IntegerField(blank=True, null=True)
    domingo = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'promos'


class PromosDet(models.Model):
    id = models.BigAutoField(primary_key=True)
    cod_promo = models.BigIntegerField()
    cod_art = models.CharField(max_length=40)
    usuario = models.CharField(max_length=20, blank=True, null=True)
    fecha_mod = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'promos_det'


class Proveedores(models.Model):
    cod_prov = models.IntegerField(primary_key=True)
    nomfantasia = models.CharField(max_length=60)
    nomtitular = models.CharField(max_length=60, blank=True, null=True)
    contacto = models.CharField(max_length=60, blank=True, null=True)
    domicilio = models.CharField(max_length=40, blank=True, null=True)
    cod_postal = models.BigIntegerField(blank=True, null=True)
    localidad = models.CharField(max_length=40, blank=True, null=True)
    telefono = models.CharField(max_length=40, blank=True, null=True)
    cond_iva = models.IntegerField(blank=True, null=True)
    nro_cuit = models.CharField(max_length=13, blank=True, null=True)
    cond_pago = models.CharField(max_length=3, blank=True, null=True)
    estado = models.SmallIntegerField(blank=True, null=True)
    observac = models.TextField(blank=True, null=True)
    fax = models.CharField(max_length=15, blank=True, null=True)
    mail = models.CharField(max_length=40, blank=True, null=True)
    usuario = models.CharField(max_length=20, blank=True, null=True)
    fecha_mod = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'proveedores'


class Recibos(models.Model):
    id = models.BigAutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    movim = models.BigIntegerField()
    numero = models.BigIntegerField()
    punto_venta = models.IntegerField()
    fecha = models.DateTimeField()
    importe = models.DecimalField(max_digits=9, decimal_places=2)
    cliente = models.IntegerField()
    cotiza_uss = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True)
    reten_iva = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    reten_iibb = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    reten_ganan = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    reten_suss = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    usuario = models.CharField(max_length=20, blank=True, null=True)
    fecha_mod = models.DateTimeField(blank=True, null=True)
    anulado = models.CharField(max_length=1, blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recibos'


class RecibosRet(models.Model):
    id = models.BigAutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    movim = models.BigIntegerField()
    numero = models.BigIntegerField()
    punto_venta = models.IntegerField()
    fecha = models.DateTimeField()
    base = models.DecimalField(max_digits=12, decimal_places=2)
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    usuario = models.CharField(max_length=20, blank=True, null=True)
    res_cod = models.CharField(max_length=20, blank=True, null=True)
    res_art = models.CharField(max_length=20, blank=True, null=True)
    fecha_mod = models.DateTimeField(blank=True, null=True)
    anulado = models.CharField(max_length=1, blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)
    reten_iva = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    numero_retencion = models.IntegerField(blank=True, null=True)
    ptovta_retencion = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recibos_ret'


class Retenciones(models.Model):
    res_cod = models.CharField(max_length=20, blank=True, null=True)
    res_art = models.CharField(max_length=20, blank=True, null=True)
    res_desc = models.CharField(max_length=50, blank=True, null=True)
    tipo = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'retenciones'


class StockCausaemision(models.Model):
    codigo = models.CharField(max_length=4)
    detalle = models.CharField(max_length=15)

    class Meta:
        managed = False
        db_table = 'stock_causaemision'


class Sucursales(models.Model):
    id = models.BigAutoField(primary_key=True)
    cod_sucursal = models.IntegerField(unique=True)
    nom_sucursal = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sucursales'


class Temporal(models.Model):
    codigo = models.CharField(max_length=40, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'temporal'


class TipocompCli(models.Model):
    id_compro = models.IntegerField(primary_key=True)
    cod_compro = models.CharField(unique=True, max_length=2)
    nom_compro = models.CharField(max_length=20)
    ultnro = models.BigIntegerField()
    copias = models.SmallIntegerField()
    ultdia = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'tipocomp_cli'


class TipocompProv(models.Model):
    id_compro = models.IntegerField(primary_key=True)
    cod_compro = models.CharField(unique=True, max_length=2)
    nom_compro = models.CharField(max_length=20)
    abrev = models.CharField(max_length=6)
    ultnro = models.IntegerField()
    copias = models.SmallIntegerField()
    ultdia = models.DateTimeField()
    rubro = models.CharField(max_length=1)

    class Meta:
        managed = False
        db_table = 'tipocomp_prov'


class Usuarios(models.Model):
    id = models.PositiveIntegerField(db_column='ID', primary_key=True)  # Field name made lowercase.
    nombrelogin = models.CharField(db_column='NombreLogin', max_length=50)  # Field name made lowercase.
    password = models.CharField(db_column='Password', max_length=50)  # Field name made lowercase.
    nombre = models.CharField(db_column='Nombre', max_length=50, blank=True, null=True)  # Field name made lowercase.
    apellido = models.CharField(db_column='Apellido', max_length=50, blank=True, null=True)  # Field name made lowercase.
    email = models.CharField(max_length=50)
    nivel_usuario = models.IntegerField(db_column='Nivel_usuario', blank=True, null=True)  # Field name made lowercase.
    no_activo = models.IntegerField(blank=True, null=True)
    interfaz = models.CharField(max_length=30, blank=True, null=True)
    fecha_mod = models.DateTimeField(blank=True, null=True)
    usuario = models.CharField(max_length=20, blank=True, null=True)
    cajero = models.IntegerField(blank=True, null=True)
    vendedor = models.IntegerField(blank=True, null=True)
    autorizador = models.IntegerField(blank=True, null=True)
    cambia_lista_precio = models.IntegerField(blank=True, null=True)
    cajero_activo = models.IntegerField(blank=True, null=True)
    fec_cajin = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'usuarios'


class UsuariosNiveles(models.Model):
    nivel = models.IntegerField()
    detalle = models.CharField(db_column='Detalle', max_length=20)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'usuarios_niveles'


class Ventas(models.Model):
    movim = models.IntegerField(primary_key=True)
    id_comprob = models.IntegerField()
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.PositiveBigIntegerField()
    cod_cli = models.IntegerField()
    fecha_fact = models.DateTimeField()
    fecha_vto = models.DateTimeField()
    neto = models.DecimalField(max_digits=11, decimal_places=2)
    iva_1 = models.DecimalField(max_digits=11, decimal_places=2)
    exento = models.DecimalField(max_digits=11, decimal_places=2)
    total = models.DecimalField(max_digits=11, decimal_places=2)
    descuento = models.DecimalField(max_digits=11, decimal_places=2)
    descuento_iva = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    dtos_por_items = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    dtos_por_items_iva = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    percepciones = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    impuestos_internos = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    recargos = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    recargos_iva = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    tot_general = models.DecimalField(max_digits=11, decimal_places=2)
    costo_general = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    costo_completo = models.IntegerField(blank=True, null=True)
    vendedor = models.SmallIntegerField(blank=True, null=True)
    comision = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    anulado = models.CharField(max_length=1, blank=True, null=True)
    observac = models.CharField(max_length=100, blank=True, null=True)
    moneda = models.SmallIntegerField(blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)
    nro_lote = models.IntegerField(blank=True, null=True)
    dolar_dia = models.DecimalField(max_digits=9, decimal_places=3, blank=True, null=True)
    usuario = models.CharField(max_length=20, blank=True, null=True)
    fecha_mod = models.DateTimeField()
    cajero = models.IntegerField()
    nro_caja = models.BigIntegerField(blank=True, null=True)
    comprobante_tipo = models.CharField(max_length=2, blank=True, null=True)
    comprobante_letra = models.CharField(max_length=2, blank=True, null=True)
    comprobante_pto_vta = models.CharField(max_length=4, blank=True, null=True)
    cond_venta = models.CharField(max_length=1, blank=True, null=True, db_comment='1 Contado, 2 Cta Cte')
    zeta = models.PositiveIntegerField(blank=True, null=True)
    cae = models.CharField(max_length=20, blank=True, null=True)
    perce_caba = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    perce_bsas = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    perce_5329 = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    mail_venta = models.CharField(max_length=100, blank=True, null=True)
    referencia_venta = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ventas'
        unique_together = (('cod_comprob', 'nro_comprob', 'comprobante_pto_vta'),)


class VentasAdicionales(models.Model):
    movim = models.IntegerField(primary_key=True)
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.PositiveBigIntegerField()
    usuario = models.CharField(max_length=20, blank=True, null=True)
    fecha_mod = models.DateTimeField()
    comprobante_tipo = models.CharField(max_length=2, blank=True, null=True)
    comprobante_letra = models.CharField(max_length=2, blank=True, null=True)
    comprobante_pto_vta = models.CharField(max_length=4, blank=True, null=True)
    fe_autoriza = models.JSONField(blank=True, null=True)
    fe_items = models.JSONField(blank=True, null=True)
    fe_promos = models.JSONField(blank=True, null=True)
    fe_descuentos = models.JSONField(blank=True, null=True)
    fe_reporte = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ventas_adicionales'


class VentasDescuentos(models.Model):
    id = models.BigAutoField(primary_key=True)
    movim = models.PositiveBigIntegerField(blank=True, null=True)
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.PositiveBigIntegerField()
    id_comprob = models.IntegerField(blank=True, null=True)
    cod_descu = models.CharField(max_length=40, blank=True, null=True)
    detalle = models.CharField(max_length=60, blank=True, null=True)
    importe = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    iva_importe = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    comprobante_tipo = models.CharField(max_length=2, blank=True, null=True)
    comprobante_letra = models.CharField(max_length=2, blank=True, null=True)
    comprobante_pto_vta = models.CharField(max_length=4, blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)
    nro_lote = models.IntegerField(blank=True, null=True)
    cod_erp = models.CharField(max_length=20, blank=True, null=True)
    tasa = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ventas_descuentos'


class VentasDet(models.Model):
    id = models.BigAutoField(primary_key=True)
    movim = models.PositiveIntegerField()
    id_comprob = models.IntegerField()
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.PositiveBigIntegerField()
    cod_articulo = models.CharField(max_length=40)
    cantidad = models.DecimalField(max_digits=9, decimal_places=3)
    precio_unit = models.DecimalField(max_digits=11, decimal_places=2)
    precio_unit_base = models.DecimalField(max_digits=12, decimal_places=4)
    total = models.DecimalField(max_digits=11, decimal_places=2)
    descuento = models.DecimalField(max_digits=11, decimal_places=2)
    descuento_iva = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    p_descuento = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    lote = models.IntegerField(blank=True, null=True)
    detalle = models.CharField(max_length=60)
    p_iva = models.DecimalField(max_digits=4, decimal_places=2)
    v_iva = models.DecimalField(max_digits=14, decimal_places=2)
    v_iva_base = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    impuesto_unitario = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    combo = models.IntegerField(blank=True, null=True)
    item_libre = models.CharField(max_length=45, blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)
    nro_lote = models.IntegerField(blank=True, null=True)
    es_promo = models.IntegerField(blank=True, null=True)
    es_kit = models.IntegerField(blank=True, null=True)
    comprobante_tipo = models.CharField(max_length=2, blank=True, null=True)
    comprobante_letra = models.CharField(max_length=2, blank=True, null=True)
    comprobante_pto_vta = models.CharField(max_length=4, blank=True, null=True)
    costo = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ventas_det'


class VentasDetalladas(models.Model):
    fecha = models.DateTimeField(db_column='Fecha')  # Field name made lowercase.
    nro_zeta = models.PositiveIntegerField(db_column='Nro_Zeta', blank=True, null=True)  # Field name made lowercase.
    comprobante = models.TextField(db_column='Comprobante', blank=True, null=True)  # Field name made lowercase.
    cliente = models.CharField(db_column='Cliente', max_length=60, blank=True, null=True)  # Field name made lowercase.
    cuit = models.CharField(db_column='Cuit', max_length=13, blank=True, null=True)  # Field name made lowercase.
    art_cod = models.CharField(db_column='Art_Cod', max_length=40, blank=True, null=True)  # Field name made lowercase.
    articulo = models.CharField(db_column='Articulo', max_length=50, blank=True, null=True)  # Field name made lowercase.
    cantidad = models.DecimalField(db_column='Cantidad', max_digits=7, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    precio_neto = models.DecimalField(db_column='Precio_Neto', max_digits=11, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    iva = models.DecimalField(db_column='IVA', max_digits=14, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    impuesto_interno = models.DecimalField(db_column='Impuesto_Interno', max_digits=12, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    precio_final = models.DecimalField(db_column='Precio_Final', max_digits=16, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    total_neto = models.DecimalField(db_column='Total_Neto', max_digits=17, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    total_iva = models.DecimalField(db_column='Total_IVA', max_digits=21, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    total_impuesto_interno = models.DecimalField(db_column='Total_Impuesto_Interno', max_digits=19, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    venta_total_sin_desc = models.DecimalField(db_column='Venta_Total_Sin_Desc', max_digits=22, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    descuento = models.DecimalField(db_column='DESCUENTO', max_digits=28, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    descuento_iva = models.DecimalField(db_column='DESCUENTO_IVA', max_digits=32, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    percepcion_real = models.DecimalField(db_column='PERCEPCION_REAL', max_digits=40, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    neto_final = models.DecimalField(db_column='NETO_FINAL', max_digits=29, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    imp_int_final = models.DecimalField(db_column='IMP_INT_FINAL', max_digits=19, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    iva_final = models.DecimalField(db_column='IVA_FINAL', max_digits=33, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    total_final = models.DecimalField(db_column='TOTAL_FINAL', max_digits=41, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    costo_unitario = models.DecimalField(db_column='COSTO_UNITARIO', max_digits=16, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    costo_total = models.DecimalField(db_column='COSTO_TOTAL', max_digits=12, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    forma_pago = models.CharField(db_column='Forma_Pago', max_length=20, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ventas_detalladas'


class VentasExtras(models.Model):
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.BigIntegerField()
    comprobante_pto_vta = models.CharField(max_length=4)
    cliente_documento = models.CharField(max_length=50, blank=True, null=True)
    cliente_nombre = models.CharField(max_length=100, blank=True, null=True)
    obs = models.CharField(max_length=50, blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ventas_extras'


class VentasPromo(models.Model):
    id = models.BigAutoField(primary_key=True)
    movim = models.PositiveBigIntegerField(blank=True, null=True)
    cod_comprob = models.CharField(max_length=2, blank=True, null=True)
    nro_comprob = models.PositiveBigIntegerField(blank=True, null=True)
    id_comprob = models.IntegerField(blank=True, null=True)
    cod_promo = models.CharField(max_length=40, blank=True, null=True)
    detalle = models.CharField(max_length=60, blank=True, null=True)
    importe = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    iva_importe = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    comprobante_tipo = models.CharField(max_length=2, blank=True, null=True)
    comprobante_letra = models.CharField(max_length=2, blank=True, null=True)
    comprobante_pto_vta = models.CharField(max_length=4, blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)
    nro_lote = models.IntegerField(blank=True, null=True)
    codigo_erp = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ventas_promo'


class VentasRegimenes(models.Model):
    id = models.BigAutoField(primary_key=True)
    movim = models.PositiveBigIntegerField(blank=True, null=True)
    cod_comprob = models.CharField(max_length=2)
    nro_comprob = models.PositiveBigIntegerField()
    id_comprob = models.IntegerField(blank=True, null=True)
    regimen = models.CharField(max_length=255, blank=True, null=True)
    importe = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    base_imponible = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    comprobante_tipo = models.CharField(max_length=2, blank=True, null=True)
    comprobante_letra = models.CharField(max_length=2, blank=True, null=True)
    comprobante_pto_vta = models.CharField(max_length=4, blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)
    nro_lote = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ventas_regimenes'


class Zetas(models.Model):
    pv = models.IntegerField(db_column='PV')  # Field name made lowercase.
    numerozeta = models.IntegerField(db_column='NumeroZeta')  # Field name made lowercase.
    fecha = models.DateTimeField(blank=True, null=True)
    iva = models.DecimalField(db_column='Iva', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    gravado = models.DecimalField(db_column='Gravado', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    nogravado = models.DecimalField(db_column='NoGravado', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    impuestosinternos = models.DecimalField(db_column='ImpuestosInternos', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    total = models.DecimalField(db_column='Total', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    emitidos = models.IntegerField(blank=True, null=True)
    cancelados = models.IntegerField(blank=True, null=True)
    ultimo_fa = models.BigIntegerField(blank=True, null=True)
    ultimo_fb = models.BigIntegerField(blank=True, null=True)
    ultima_nca = models.BigIntegerField(blank=True, null=True)
    ultima_ncb = models.BigIntegerField(blank=True, null=True)
    sis_emitidos = models.IntegerField(blank=True, null=True)
    sis_total = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    sis_fa_desde = models.BigIntegerField(blank=True, null=True)
    sis_fa_hasta = models.BigIntegerField(blank=True, null=True)
    sis_fb_desde = models.BigIntegerField(blank=True, null=True)
    sis_fb_hasta = models.BigIntegerField(blank=True, null=True)
    sis_nca_desde = models.BigIntegerField(blank=True, null=True)
    sis_nca_hasta = models.BigIntegerField(blank=True, null=True)
    sis_ncb_desde = models.BigIntegerField(blank=True, null=True)
    sis_ncb_hasta = models.BigIntegerField(blank=True, null=True)
    procesado = models.IntegerField(blank=True, null=True)
    fecha_procesado = models.DateTimeField(blank=True, null=True)
    nro_lote = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'zetas'
