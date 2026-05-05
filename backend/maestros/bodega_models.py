"""
bodega_models.py — Módulo Bodega / Vitivinícola
Modelos para la gestión integral de bodegas: viñedo, recepción,
elaboración, depósitos, barricas, laboratorio y embotellado.

Instrucciones de integración:
    Al final de backend/maestros/models.py agregar:
        from .bodega_models import *
"""
from django.db import models
from decimal import Decimal


# ─────────────────────────────────────────────────────────────────────────────
# TABLAS DE CONFIGURACIÓN / CATÁLOGOS
# ─────────────────────────────────────────────────────────────────────────────

class BodVarietal(models.Model):
    """Catálogo de varietales de uva."""
    codigo      = models.CharField(max_length=10, primary_key=True)
    nombre      = models.CharField(max_length=60)
    color       = models.CharField(max_length=1, choices=[('T', 'Tinto'), ('B', 'Blanco'), ('R', 'Rosado')], default='T')
    activo      = models.BooleanField(default=True)

    class Meta:
        db_table = 'bod_varietal'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"


class BodInsumoEnologico(models.Model):
    """
    Catálogo de insumos enológicos (SO2, levaduras, enzimas, clarificantes, etc.).
    Se vincula con articulos.cod_art para el control de stock.
    """
    TIPO_CHOICES = [
        ('SO2',  'Dióxido de azufre'),
        ('LEV',  'Levadura'),
        ('NUT',  'Nutriente'),
        ('ENZ',  'Enzima'),
        ('CLA',  'Clarificante'),
        ('ACI',  'Acidificante'),
        ('TAN',  'Tanino'),
        ('OTR',  'Otro'),
    ]
    cod_art      = models.CharField(max_length=40, help_text='FK a articulos.cod_art')
    nombre       = models.CharField(max_length=80)
    tipo         = models.CharField(max_length=5, choices=TIPO_CHOICES, default='OTR')
    unidad       = models.CharField(max_length=10, default='kg')
    dosis_max_gl = models.DecimalField(
        max_digits=8, decimal_places=4, null=True, blank=True,
        help_text='Dosis máxima legal en g/L según OIV/INV'
    )
    activo       = models.BooleanField(default=True)

    class Meta:
        db_table = 'bod_insumo_enologico'
        ordering = ['tipo', 'nombre']

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.nombre}"


# ─────────────────────────────────────────────────────────────────────────────
# VIÑEDO
# ─────────────────────────────────────────────────────────────────────────────

class BodParcela(models.Model):
    """Parcela o cuartel de viñedo propio o de terceros."""
    TIPO_CHOICES = [('P', 'Propia'), ('T', 'Terceros')]

    nombre       = models.CharField(max_length=80)
    tipo         = models.CharField(max_length=1, choices=TIPO_CHOICES, default='P')
    varietal     = models.ForeignKey(
                       BodVarietal, on_delete=models.PROTECT,
                       db_column='varietal_codigo', to_field='codigo')
    superficie_ha = models.DecimalField(max_digits=8, decimal_places=4)
    anio_plantacion = models.SmallIntegerField(null=True, blank=True)
    portainjerto = models.CharField(max_length=40, blank=True, default='')
    # Ubicación
    finca        = models.CharField(max_length=80, blank=True, default='')
    zona         = models.CharField(max_length=60, blank=True, default='',
                       help_text='Zona / Denominación de Origen (ej: Luján de Cuyo, Valle de Uco)')
    latitud      = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitud     = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    altitud_msnm = models.SmallIntegerField(null=True, blank=True)
    # Proveedor viñatero (si tipo=T)
    cod_prov     = models.IntegerField(null=True, blank=True,
                       help_text='FK a proveedores.cod_prov si es uva de terceros')
    activa       = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'bod_parcela'
        ordering = ['finca', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.varietal_id}) — {self.superficie_ha} ha"


class BodMaduracion(models.Model):
    """Registro periódico de maduración (Brix, pH, acidez) por parcela y campaña."""
    parcela      = models.ForeignKey(BodParcela, on_delete=models.CASCADE,
                                     related_name='maduraciones')
    campaña      = models.SmallIntegerField(help_text='Año de cosecha')
    fecha        = models.DateField()
    brix         = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ph           = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    acidez_total = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                       help_text='g/L de ácido tartárico')
    estado_sanitario = models.CharField(max_length=20, blank=True, default='',
                           help_text='Óptimo / Bueno / Regular / Malo')
    observaciones = models.CharField(max_length=200, blank=True, default='')
    usuario      = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'bod_maduracion'
        ordering = ['parcela', '-fecha']

    def __str__(self):
        return f"{self.parcela} {self.fecha} — {self.brix}°Bx"


# ─────────────────────────────────────────────────────────────────────────────
# RECEPCIÓN Y VENDIMIA
# ─────────────────────────────────────────────────────────────────────────────

class BodTicketBascula(models.Model):
    """
    Ticket de pesaje en recepción de uva.
    Integrable con báscula electrónica.
    """
    ESTADO_CHOICES = [
        ('PE', 'Pendiente de destino'),
        ('AS', 'Asignado a lote'),
        ('LI', 'Liquidado'),
    ]

    numero       = models.AutoField(primary_key=True)
    campaña      = models.SmallIntegerField(help_text='Año de cosecha')
    fecha        = models.DateTimeField()
    parcela      = models.ForeignKey(BodParcela, on_delete=models.PROTECT,
                                     related_name='tickets', null=True, blank=True)
    varietal     = models.ForeignKey(BodVarietal, on_delete=models.PROTECT,
                                     db_column='varietal_codigo', to_field='codigo')
    # Datos de pesaje
    patente_camion = models.CharField(max_length=15, blank=True, default='')
    peso_bruto   = models.DecimalField(max_digits=8, decimal_places=0,
                       help_text='kg')
    tara         = models.DecimalField(max_digits=8, decimal_places=0, default=0,
                       help_text='kg')
    peso_neto    = models.DecimalField(max_digits=8, decimal_places=0,
                       help_text='kg — calculado automáticamente')
    # Análisis de recepción
    brix_entrada  = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ph_entrada    = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    acidez_entrada = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    estado_sanitario = models.CharField(max_length=20, blank=True, default='')
    # Proveedor (si uva de terceros)
    cod_prov     = models.IntegerField(null=True, blank=True,
                       help_text='FK a proveedores.cod_prov')
    nombre_prov  = models.CharField(max_length=60, blank=True, default='')
    # Precio pactado
    precio_kg    = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    # Estado y destino
    estado       = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='PE')
    lote_destino = models.ForeignKey(
                       'BodLoteGranel', on_delete=models.SET_NULL,
                       null=True, blank=True, related_name='tickets_origen')
    observaciones = models.CharField(max_length=200, blank=True, default='')
    usuario      = models.CharField(max_length=20, blank=True, default='')
    fecha_mod    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bod_ticket_bascula'
        ordering = ['-fecha']

    def save(self, *args, **kwargs):
        self.peso_neto = self.peso_bruto - self.tara
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ticket #{self.numero} — {self.varietal_id} {self.peso_neto} kg"


# ─────────────────────────────────────────────────────────────────────────────
# DEPÓSITOS / RECIPIENTES
# ─────────────────────────────────────────────────────────────────────────────

class BodRecipiente(models.Model):
    """
    Recipiente de bodega: tanque de acero, pileta de cemento, barrica, etc.
    Representa la unidad física de almacenamiento de granel.
    """
    TIPO_CHOICES = [
        ('TA', 'Tanque de acero inoxidable'),
        ('PC', 'Pileta de cemento'),
        ('TR', 'Tanque de roble'),
        ('BA', 'Barrica'),
        ('TI', 'Tinaja / Ánfora'),
        ('OT', 'Otro'),
    ]
    ESTADO_CHOICES = [
        ('LI', 'Libre'),
        ('OC', 'Ocupado'),
        ('LA', 'En limpieza'),
        ('MN', 'En mantenimiento'),
        ('BA', 'Baja'),
    ]

    codigo       = models.CharField(max_length=20, unique=True)
    nombre       = models.CharField(max_length=60)
    tipo         = models.CharField(max_length=2, choices=TIPO_CHOICES, default='TA')
    capacidad_litros = models.DecimalField(max_digits=10, decimal_places=2)
    sector       = models.CharField(max_length=40, blank=True, default='',
                       help_text='Nave, sector o ubicación física')
    fila         = models.SmallIntegerField(null=True, blank=True)
    posicion     = models.SmallIntegerField(null=True, blank=True)
    estado       = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='LI')
    activo       = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        db_table = 'bod_recipiente'
        ordering = ['sector', 'codigo']

    def __str__(self):
        return f"{self.codigo} — {self.nombre} ({self.capacidad_litros} L)"


# ─────────────────────────────────────────────────────────────────────────────
# LOTES DE ELABORACIÓN (GRANEL)
# ─────────────────────────────────────────────────────────────────────────────

class BodLoteGranel(models.Model):
    """
    Lote de elaboración / partida de vino a granel.
    Unidad central de trazabilidad del módulo.
    """
    TIPO_VINO_CHOICES = [
        ('TI', 'Tinto'),
        ('BL', 'Blanco'),
        ('RO', 'Rosado'),
        ('ES', 'Espumante'),
        ('DU', 'Dulce natural'),
        ('OT', 'Otro'),
    ]
    ESTADO_CHOICES = [
        ('EB', 'En elaboración'),
        ('CR', 'En crianza'),
        ('LI', 'Listo para embotellar'),
        ('EM', 'Embotellado total'),
        ('EP', 'Embotellado parcial'),
        ('VE', 'Vendido a granel'),
        ('AN', 'Anulado'),
    ]

    codigo       = models.CharField(max_length=20, unique=True,
                       help_text='Ej: 2024-MAL-001')
    campaña      = models.SmallIntegerField(help_text='Año de cosecha/elaboración')
    varietal_ppal = models.ForeignKey(
                       BodVarietal, on_delete=models.PROTECT,
                       db_column='varietal_ppal', to_field='codigo',
                       related_name='lotes_principales')
    tipo_vino    = models.CharField(max_length=2, choices=TIPO_VINO_CHOICES, default='TI')
    descripcion  = models.CharField(max_length=120, blank=True, default='')
    fecha_inicio = models.DateField()
    estado       = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='EB')
    # Volúmenes
    litros_iniciales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    litros_actuales  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Recipiente actual (principal)
    recipiente   = models.ForeignKey(
                       BodRecipiente, on_delete=models.SET_NULL,
                       null=True, blank=True, related_name='lotes')
    # Parámetros enológicos objetivo
    grado_alcohol_obj = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    acidez_total_obj  = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    azucar_residual_obj = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    # Auditoría
    usuario      = models.CharField(max_length=20, blank=True, default='')
    fecha_mod    = models.DateTimeField(auto_now=True)
    observaciones = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'bod_lote_granel'
        ordering = ['-campaña', 'codigo']

    def __str__(self):
        return f"{self.codigo} — {self.varietal_ppal_id} {self.campaña} [{self.get_estado_display()}]"

    @property
    def merma_total(self):
        return self.litros_iniciales - self.litros_actuales


class BodComposicionLote(models.Model):
    """
    Composición varietal de un lote (para coupages y mezclas).
    Un lote puede componerse de varios sub-lotes fuente.
    """
    lote_destino = models.ForeignKey(BodLoteGranel, on_delete=models.CASCADE,
                                     related_name='composicion')
    lote_origen  = models.ForeignKey(BodLoteGranel, on_delete=models.PROTECT,
                                     related_name='usos', null=True, blank=True)
    varietal     = models.ForeignKey(BodVarietal, on_delete=models.PROTECT,
                                     db_column='varietal_codigo', to_field='codigo')
    litros       = models.DecimalField(max_digits=12, decimal_places=2)
    porcentaje   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    campaña_origen = models.SmallIntegerField(null=True, blank=True)
    fecha_mezcla = models.DateField()
    observaciones = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        db_table = 'bod_composicion_lote'
        ordering = ['-litros']


# ─────────────────────────────────────────────────────────────────────────────
# MOVIMIENTOS DE GRANEL (LIBRO DE BODEGA)
# ─────────────────────────────────────────────────────────────────────────────

class BodMovimientoGranel(models.Model):
    """
    Movimiento de vino entre recipientes o hacia/desde exterior.
    Base del libro de bodega automático (INV).
    """
    TIPO_CHOICES = [
        ('IN', 'Ingreso'),
        ('EG', 'Egreso'),
        ('TR', 'Trasvase entre recipientes'),
        ('ME', 'Merma declarada'),
        ('CL', 'Limpieza / lavado'),
        ('CO', 'Coupage / Mezcla'),
        ('VE', 'Venta a granel'),
    ]

    lote         = models.ForeignKey(BodLoteGranel, on_delete=models.CASCADE,
                                     related_name='movimientos')
    tipo         = models.CharField(max_length=2, choices=TIPO_CHOICES)
    fecha        = models.DateTimeField()
    litros       = models.DecimalField(max_digits=12, decimal_places=2)
    recipiente_origen = models.ForeignKey(
                            BodRecipiente, on_delete=models.SET_NULL,
                            null=True, blank=True, related_name='movim_salidas')
    recipiente_destino = models.ForeignKey(
                            BodRecipiente, on_delete=models.SET_NULL,
                            null=True, blank=True, related_name='movim_entradas')
    temperatura  = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                       help_text='°C al momento del trasvase')
    descripcion  = models.CharField(max_length=200, blank=True, default='')
    usuario      = models.CharField(max_length=20, blank=True, default='')
    fecha_mod    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bod_movimiento_granel'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} {self.lote.codigo} {self.litros} L — {self.fecha}"


# ─────────────────────────────────────────────────────────────────────────────
# ELABORACIÓN — OPERACIONES ENOLÓGICAS
# ─────────────────────────────────────────────────────────────────────────────

class BodOperacionEnologica(models.Model):
    """
    Operación enológica aplicada a un lote: adición de insumos,
    clarificación, filtración, correcciones, etc.
    """
    TIPO_CHOICES = [
        ('AIC', 'Adición de insumo/corrector'),
        ('CLA', 'Clarificación'),
        ('FIL', 'Filtración'),
        ('SOL', 'Sulfitado'),
        ('FER', 'Registro de fermentación'),
        ('COR', 'Corrección enológica'),
        ('OTR', 'Otra práctica'),
    ]

    lote         = models.ForeignKey(BodLoteGranel, on_delete=models.CASCADE,
                                     related_name='operaciones')
    tipo         = models.CharField(max_length=3, choices=TIPO_CHOICES)
    fecha        = models.DateTimeField()
    descripcion  = models.CharField(max_length=150)
    # Si es adición de insumo
    insumo       = models.ForeignKey(
                       BodInsumoEnologico, on_delete=models.SET_NULL,
                       null=True, blank=True, related_name='operaciones')
    cantidad_insumo = models.DecimalField(max_digits=10, decimal_places=4,
                          null=True, blank=True)
    unidad_insumo = models.CharField(max_length=10, blank=True, default='')
    lote_insumo_prov = models.CharField(max_length=40, blank=True, default='',
                           help_text='N° de lote del proveedor del insumo')
    # Si es fermentación: parámetros del día
    temperatura  = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    densidad     = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    grado_real   = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    # Resultado
    resultado    = models.CharField(max_length=200, blank=True, default='')
    usuario      = models.CharField(max_length=20, blank=True, default='')
    fecha_mod    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bod_operacion_enologica'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.lote.codigo} {self.fecha}"


# ─────────────────────────────────────────────────────────────────────────────
# ANÁLISIS DE LABORATORIO
# ─────────────────────────────────────────────────────────────────────────────

class BodAnalisis(models.Model):
    """
    Análisis enológico de un lote de granel.
    Todos los parámetros son opcionales para permitir análisis parciales.
    """
    ORIGEN_CHOICES = [
        ('INT', 'Laboratorio interno'),
        ('EXT', 'Laboratorio externo'),
        ('INV', 'INV — Instituto Nac. Vitivinicultura'),
    ]

    lote          = models.ForeignKey(BodLoteGranel, on_delete=models.CASCADE,
                                      related_name='analisis')
    fecha         = models.DateField()
    origen        = models.CharField(max_length=3, choices=ORIGEN_CHOICES, default='INT')
    laboratorio   = models.CharField(max_length=80, blank=True, default='')
    # Parámetros principales
    grado_alcohol = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                        help_text='% v/v')
    acidez_total  = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                        help_text='g/L ác. tartárico')
    acidez_volatil = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                         help_text='g/L ác. acético')
    ph            = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    azucar_residual = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                          help_text='g/L')
    so2_libre     = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                        help_text='mg/L')
    so2_total     = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                        help_text='mg/L')
    turbidez_ntu  = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    color_absorbancia = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    # Aprobación
    aprobado      = models.BooleanField(null=True, blank=True,
                        help_text='True=Aprobado, False=Rechazado, None=Pendiente evaluación')
    observaciones = models.TextField(blank=True, default='')
    usuario       = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'bod_analisis'
        ordering = ['-fecha']

    def __str__(self):
        return f"Análisis {self.lote.codigo} — {self.fecha}"


# ─────────────────────────────────────────────────────────────────────────────
# CRIANZA — BARRICAS
# ─────────────────────────────────────────────────────────────────────────────

class BodBarrica(models.Model):
    """Inventario de barricas con historial de uso."""
    MADERA_CHOICES = [
        ('FRA', 'Roble francés'),
        ('AME', 'Roble americano'),
        ('HUN', 'Roble húngaro'),
        ('OTR', 'Otro'),
    ]
    TOSTADO_CHOICES = [
        ('L',  'Ligero'),
        ('M',  'Medio'),
        ('MO', 'Medio plus'),
        ('F',  'Fuerte'),
    ]
    ESTADO_CHOICES = [
        ('LI', 'Libre'),
        ('OC', 'Ocupada'),
        ('LA', 'En limpieza'),
        ('BA', 'Baja enológica'),
    ]

    numero        = models.CharField(max_length=20, unique=True,
                        help_text='Número de identificación de la barrica')
    capacidad_litros = models.DecimalField(max_digits=7, decimal_places=2, default=225)
    madera        = models.CharField(max_length=3, choices=MADERA_CHOICES, default='FRA')
    tostado       = models.CharField(max_length=2, choices=TOSTADO_CHOICES, default='M')
    tonelero      = models.CharField(max_length=60, blank=True, default='')
    anio_compra   = models.SmallIntegerField(null=True, blank=True)
    cantidad_usos = models.SmallIntegerField(default=0,
                        help_text='Número de veces que fue usada')
    estado        = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='LI')
    sector        = models.CharField(max_length=40, blank=True, default='')
    fila          = models.SmallIntegerField(null=True, blank=True)
    posicion      = models.SmallIntegerField(null=True, blank=True)
    # Costo de amortización
    costo_compra  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vida_util_usos = models.SmallIntegerField(default=4,
                         help_text='Número de usos enológicos hasta baja')
    activa        = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        db_table = 'bod_barrica'
        ordering = ['sector', 'numero']

    def __str__(self):
        return f"Barrica #{self.numero} — {self.get_madera_display()} {self.capacidad_litros}L"

    @property
    def porcentaje_vida_util(self):
        if self.vida_util_usos:
            return round((self.cantidad_usos / self.vida_util_usos) * 100, 1)
        return 0


class BodAsignacionBarrica(models.Model):
    """Asignación de un lote de granel a una barrica para crianza."""
    ESTADO_CHOICES = [
        ('OC', 'Ocupada — en crianza'),
        ('VA', 'Vaciada'),
    ]

    barrica      = models.ForeignKey(BodBarrica, on_delete=models.PROTECT,
                                     related_name='asignaciones')
    lote         = models.ForeignKey(BodLoteGranel, on_delete=models.PROTECT,
                                     related_name='asignaciones_barrica')
    fecha_entrada = models.DateField()
    fecha_salida  = models.DateField(null=True, blank=True)
    litros_entrada = models.DecimalField(max_digits=8, decimal_places=2)
    litros_salida  = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    estado        = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='OC')
    # Rellenos registrados (topping)
    litros_relleno = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    # Merma por evaporación calculada
    merma_litros  = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    observaciones = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        db_table = 'bod_asignacion_barrica'
        ordering = ['-fecha_entrada']

    def __str__(self):
        return f"Barrica {self.barrica.numero} ← {self.lote.codigo} [{self.estado}]"


# ─────────────────────────────────────────────────────────────────────────────
# EMBOTELLADO
# ─────────────────────────────────────────────────────────────────────────────

class BodOrdenEmbotellado(models.Model):
    """
    Orden de embotellado: planificación y registro de una corrida de embotellado.
    Al confirmar, se descuenta stock de granel y se genera PT en artículos del ERP.
    """
    FORMATO_CHOICES = [
        ('375',  '375 ml'),
        ('750',  '750 ml'),
        ('1500', '1.5 L — Magnum'),
        ('3000', '3 L — Jeroboam'),
        ('BIB',  'Bag in Box'),
        ('OTR',  'Otro'),
    ]
    ESTADO_CHOICES = [
        ('PL', 'Planificada'),
        ('EN', 'En proceso'),
        ('CO', 'Completada'),
        ('AN', 'Anulada'),
    ]

    numero       = models.AutoField(primary_key=True)
    lote         = models.ForeignKey(BodLoteGranel, on_delete=models.PROTECT,
                                     related_name='ordenes_embotellado')
    fecha_plan   = models.DateField()
    fecha_real   = models.DateField(null=True, blank=True)
    formato      = models.CharField(max_length=5, choices=FORMATO_CHOICES, default='750')
    formato_desc = models.CharField(max_length=40, blank=True, default='')
    # Cantidades planificadas vs reales
    botellas_plan    = models.IntegerField()
    botellas_real    = models.IntegerField(null=True, blank=True)
    botellas_merma   = models.IntegerField(default=0)
    litros_consumidos = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # Materiales de embotellado (se integran con stock de artículos)
    cod_botella  = models.CharField(max_length=40, blank=True, default='',
                       help_text='cod_art del artículo botella en el ERP')
    cod_corcho   = models.CharField(max_length=40, blank=True, default='')
    cod_etiqueta = models.CharField(max_length=40, blank=True, default='')
    cod_capsula  = models.CharField(max_length=40, blank=True, default='')
    cod_caja     = models.CharField(max_length=40, blank=True, default='')
    # Artículo de PT generado en el ERP
    cod_art_pt   = models.CharField(max_length=40, blank=True, default='',
                       help_text='cod_art del producto terminado en articulos')
    # RNOE (Registro Nacional de Origen y Especie)
    nro_rnoe     = models.CharField(max_length=30, blank=True, default='')
    estado       = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='PL')
    observaciones = models.CharField(max_length=200, blank=True, default='')
    usuario      = models.CharField(max_length=20, blank=True, default='')
    fecha_mod    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bod_orden_embotellado'
        ordering = ['-fecha_plan']

    def __str__(self):
        return f"OE #{self.numero} — {self.lote.codigo} {self.botellas_plan} bot. [{self.get_estado_display()}]"

    @property
    def litros_planificados(self):
        factor = {
            '375': 0.375, '750': 0.750,
            '1500': 1.5, '3000': 3.0,
        }
        return round(self.botellas_plan * factor.get(self.formato, 0.750), 2)


# ─────────────────────────────────────────────────────────────────────────────
# VIÑEDO — LABORES, TRATAMIENTOS Y CONTRATOS (faltantes)
# ─────────────────────────────────────────────────────────────────────────────

class BodLaborCultural(models.Model):
    """Registro de labores culturales por parcela y campaña."""
    TIPO_CHOICES = [
        ('POD', 'Poda'),
        ('DES', 'Desbrote'),
        ('VEV', 'Vendimia en verde'),
        ('COS', 'Cosecha'),
        ('RIE', 'Riego'),
        ('FER', 'Fertilización'),
        ('LAB', 'Laboreo de suelo'),
        ('ATA', 'Atado / Levante'),
        ('OTR', 'Otra'),
    ]

    parcela      = models.ForeignKey(BodParcela, on_delete=models.CASCADE,
                                     related_name='labores')
    campaña      = models.SmallIntegerField()
    tipo         = models.CharField(max_length=3, choices=TIPO_CHOICES)
    fecha_inicio = models.DateField()
    fecha_fin    = models.DateField(null=True, blank=True)
    descripcion  = models.CharField(max_length=200, blank=True, default='')
    # Recursos
    jornales     = models.DecimalField(max_digits=8, decimal_places=2, default=0,
                       help_text='Cantidad de jornales utilizados')
    costo_jornal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_maquinaria = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_insumos    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_total      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    responsable  = models.CharField(max_length=60, blank=True, default='')
    usuario      = models.CharField(max_length=20, blank=True, default='')
    fecha_mod    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bod_labor_cultural'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.parcela.nombre} {self.campaña}"


class BodTratamientoFitosanitario(models.Model):
    """Tratamientos fitosanitarios aplicados por parcela."""

    parcela      = models.ForeignKey(BodParcela, on_delete=models.CASCADE,
                                     related_name='tratamientos')
    campaña      = models.SmallIntegerField()
    fecha        = models.DateField()
    producto     = models.CharField(max_length=80)
    principio_activo = models.CharField(max_length=80, blank=True, default='')
    dosis_aplicada = models.DecimalField(max_digits=8, decimal_places=4,
                         help_text='Dosis en cc o g por planta/ha según unidad')
    unidad       = models.CharField(max_length=10, default='cc/ha')
    volumen_caldo = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
                        help_text='Litros de caldo total aplicado')
    dias_carencia = models.SmallIntegerField(default=0,
                        help_text='Días de carencia del producto')
    fecha_fin_carencia = models.DateField(null=True, blank=True)
    objetivo     = models.CharField(max_length=120, blank=True, default='',
                       help_text='Plaga/enfermedad objetivo')
    operario     = models.CharField(max_length=60, blank=True, default='')
    lote_producto = models.CharField(max_length=40, blank=True, default='')
    costo        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usuario      = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'bod_tratamiento_fitosanitario'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.producto} — {self.parcela.nombre} {self.fecha}"

    def save(self, *args, **kwargs):
        if self.fecha and self.dias_carencia:
            from datetime import timedelta
            self.fecha_fin_carencia = self.fecha + timedelta(days=self.dias_carencia)
        super().save(*args, **kwargs)


class BodContratoUva(models.Model):
    """Contrato de compra de uva con viñatero externo."""
    TIPO_PRECIO_CHOICES = [
        ('FI', 'Precio fijo'),
        ('GR', 'Por grado brix'),
        ('ME', 'Precio de mercado'),
        ('AC', 'A confirmar'),
    ]

    cod_prov     = models.IntegerField(help_text='FK a proveedores.cod_prov')
    nombre_prov  = models.CharField(max_length=80)
    campaña      = models.SmallIntegerField()
    varietal     = models.ForeignKey(BodVarietal, on_delete=models.PROTECT,
                                     db_column='varietal_codigo', to_field='codigo')
    parcela      = models.ForeignKey(BodParcela, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='contratos')
    kg_estimados = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    tipo_precio  = models.CharField(max_length=2, choices=TIPO_PRECIO_CHOICES, default='FI')
    precio_base_kg = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    anticipo     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    condiciones  = models.TextField(blank=True, default='')
    activo       = models.BooleanField(default=True)
    usuario      = models.CharField(max_length=20, blank=True, default='')
    fecha_mod    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bod_contrato_uva'
        ordering = ['-campaña', 'nombre_prov']

    def __str__(self):
        return f"{self.nombre_prov} — {self.varietal_id} {self.campaña}"


class BodLiquidacionUva(models.Model):
    """Liquidación de pago al viñatero por uva recibida."""
    ESTADO_CHOICES = [
        ('BO', 'Borrador'),
        ('EM', 'Emitida'),
        ('PA', 'Pagada'),
    ]

    contrato     = models.ForeignKey(BodContratoUva, on_delete=models.PROTECT,
                                     related_name='liquidaciones', null=True, blank=True)
    cod_prov     = models.IntegerField()
    nombre_prov  = models.CharField(max_length=80)
    campaña      = models.SmallIntegerField()
    fecha        = models.DateField()
    kg_liquidados = models.DecimalField(max_digits=10, decimal_places=0)
    precio_kg    = models.DecimalField(max_digits=8, decimal_places=4)
    importe_bruto = models.DecimalField(max_digits=14, decimal_places=2)
    descuentos   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    anticipo_aplicado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    importe_neto = models.DecimalField(max_digits=14, decimal_places=2)
    estado       = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='BO')
    # Referencia a CTA CTE proveedor del ERP
    movim_cta_cte = models.BigIntegerField(null=True, blank=True,
                        help_text='FK a cta_cte_prov.movim una vez contabilizada')
    observaciones = models.TextField(blank=True, default='')
    usuario      = models.CharField(max_length=20, blank=True, default='')
    fecha_mod    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bod_liquidacion_uva'
        ordering = ['-fecha']

    def __str__(self):
        return f"Liq. {self.nombre_prov} {self.campaña} — ${self.importe_neto}"


# ─────────────────────────────────────────────────────────────────────────────
# ELABORACIÓN — BALANCE DE MASA Y ORDEN DE ELABORACIÓN (faltantes)
# ─────────────────────────────────────────────────────────────────────────────

class BodOrdenElaboracion(models.Model):
    """
    Orden de trabajo interna para el enólogo / cellarman.
    Detalla instrucciones, parámetros objetivo y operaciones a realizar.
    """
    ESTADO_CHOICES = [
        ('PE', 'Pendiente'),
        ('EN', 'En proceso'),
        ('CO', 'Completada'),
        ('AN', 'Anulada'),
    ]

    numero       = models.AutoField(primary_key=True)
    lote         = models.ForeignKey(BodLoteGranel, on_delete=models.CASCADE,
                                     related_name='ordenes_elaboracion')
    fecha_emision = models.DateField()
    fecha_ejecucion = models.DateField(null=True, blank=True)
    proceso      = models.CharField(max_length=120,
                       help_text='Descripción del proceso: Fermentación maloláctica, Trasiego N°2, etc.')
    instrucciones = models.TextField(blank=True, default='')
    parametros_objetivo = models.JSONField(default=dict, blank=True,
                              help_text='{"temperatura": 18, "densidad_objetivo": 1.020, ...}')
    responsable  = models.CharField(max_length=60, blank=True, default='')
    estado       = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='PE')
    resultado    = models.TextField(blank=True, default='')
    usuario      = models.CharField(max_length=20, blank=True, default='')
    fecha_mod    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bod_orden_elaboracion'
        ordering = ['-fecha_emision']

    def __str__(self):
        return f"OE #{self.numero} — {self.lote.codigo} [{self.estado}]"


class BodBalanceMasa(models.Model):
    """
    Balance de masa por lote: cuadre entre kg de uva → litros de vino.
    Se genera al cierre de la vinificación primaria.
    """
    lote          = models.OneToOneField(BodLoteGranel, on_delete=models.CASCADE,
                                         related_name='balance_masa')
    campaña       = models.SmallIntegerField()
    # Entradas
    kg_uva_total  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    kg_uva_propia = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    kg_uva_comprada = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Salidas de masa sólida
    kg_escobajo   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    kg_orujo      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    kg_borras     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Litros obtenidos
    litros_mosto_flor   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    litros_prensa       = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    litros_totales      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Mermas de proceso
    litros_merma_proceso = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Calculados
    rendimiento_lkg     = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True,
                              help_text='Litros / kg de uva')
    porcentaje_extraccion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fecha_cierre = models.DateField()
    observaciones = models.TextField(blank=True, default='')
    usuario      = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'bod_balance_masa'

    def save(self, *args, **kwargs):
        if self.kg_uva_total and self.kg_uva_total > 0:
            self.rendimiento_lkg = round(
                float(self.litros_totales) / float(self.kg_uva_total), 3)
            self.porcentaje_extraccion = round(
                float(self.litros_totales) / float(self.kg_uva_total) * 100, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Balance {self.lote.codigo} — {self.rendimiento_lkg} L/kg"


# ─────────────────────────────────────────────────────────────────────────────
# CALIDAD — FICHAS, NO CONFORMIDADES, AUDITORÍAS (faltantes)
# ─────────────────────────────────────────────────────────────────────────────

class BodFichaProducto(models.Model):
    """Ficha técnica de un producto/vino con perfil sensorial y parámetros objetivo."""

    codigo       = models.CharField(max_length=20, unique=True)
    nombre       = models.CharField(max_length=100)
    varietal     = models.ForeignKey(BodVarietal, on_delete=models.PROTECT,
                                     db_column='varietal_codigo', to_field='codigo',
                                     null=True, blank=True)
    tipo_vino    = models.CharField(max_length=2, default='TI')
    descripcion  = models.TextField(blank=True, default='')
    # Parámetros analíticos objetivo (rangos min/max)
    alcohol_min  = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    alcohol_max  = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    acidez_total_min = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    acidez_total_max = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ph_min       = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    ph_max       = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    azucar_max   = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    so2_libre_max = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    so2_total_max = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    # Perfil sensorial
    perfil_sensorial = models.TextField(blank=True, default='',
                           help_text='Descripción del perfil organoléptico objetivo')
    proceso_elaboracion = models.TextField(blank=True, default='')
    activa       = models.BooleanField(default=True)
    usuario      = models.CharField(max_length=20, blank=True, default='')
    fecha_mod    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bod_ficha_producto'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"


class BodNoConformidad(models.Model):
    """No conformidades del sistema de calidad."""
    GRAVEDAD_CHOICES = [
        ('L', 'Leve'),
        ('M', 'Moderada'),
        ('G', 'Grave'),
        ('C', 'Crítica'),
    ]
    ESTADO_CHOICES = [
        ('AB', 'Abierta'),
        ('EN', 'En tratamiento'),
        ('CE', 'Cerrada'),
        ('RE', 'Reincidente'),
    ]

    numero       = models.AutoField(primary_key=True)
    fecha        = models.DateField()
    descripcion  = models.TextField()
    origen       = models.CharField(max_length=100,
                       help_text='Dónde se detectó: Recepción, Elaboración, Laboratorio...')
    lote         = models.ForeignKey(BodLoteGranel, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='no_conformidades')
    gravedad     = models.CharField(max_length=1, choices=GRAVEDAD_CHOICES, default='L')
    responsable  = models.CharField(max_length=60, blank=True, default='')
    accion_correctiva = models.TextField(blank=True, default='')
    fecha_cierre = models.DateField(null=True, blank=True)
    estado       = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='AB')
    usuario      = models.CharField(max_length=20, blank=True, default='')
    fecha_mod    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bod_no_conformidad'
        ordering = ['-fecha']

    def __str__(self):
        return f"NC #{self.numero} [{self.get_gravedad_display()}] — {self.fecha}"


# ─────────────────────────────────────────────────────────────────────────────
# COSTOS DE PRODUCCIÓN (módulo completo faltante)
# ─────────────────────────────────────────────────────────────────────────────

class BodCostoLote(models.Model):
    """
    Acumulación de costos por lote de elaboración.
    Se alimenta desde viñedo, elaboración, crianza y embotellado.
    """
    lote         = models.OneToOneField(BodLoteGranel, on_delete=models.CASCADE,
                                         related_name='costos')
    # Costos de materia prima
    costo_uva_propia    = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    costo_uva_comprada  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    # Costos de proceso
    costo_insumos_enologicos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    costo_mano_obra_bodega   = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    costo_energia            = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    costo_crianza_barricas   = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    costo_amortizacion_barrica = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    costo_gastos_indirectos  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    # Totales calculados
    costo_total_granel  = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                              help_text='Costo total hasta producto a granel')
    costo_por_litro     = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    # Embotellado
    costo_materiales_emb = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                               help_text='Botellas, corchos, etiquetas, cápsulas, cajas')
    costo_mano_obra_emb  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    costo_total_pt       = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                               help_text='Costo total producto terminado')
    costo_por_botella    = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    # Auditoría
    fecha_calculo = models.DateTimeField(auto_now=True)
    usuario       = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'bod_costo_lote'

    def recalcular(self):
        self.costo_total_granel = sum([
            self.costo_uva_propia, self.costo_uva_comprada,
            self.costo_insumos_enologicos, self.costo_mano_obra_bodega,
            self.costo_energia, self.costo_crianza_barricas,
            self.costo_amortizacion_barrica, self.costo_gastos_indirectos,
        ])
        litros = float(self.lote.litros_actuales or 1)
        self.costo_por_litro = round(float(self.costo_total_granel) / litros, 4)
        self.costo_total_pt = self.costo_total_granel + self.costo_materiales_emb + self.costo_mano_obra_emb
        return self

    def __str__(self):
        return f"Costo {self.lote.codigo} — ${self.costo_total_pt}"


class BodCostoDetalle(models.Model):
    """Línea de costo individual imputada a un lote."""
    CATEGORIA_CHOICES = [
        ('UVA',  'Materia prima — uva'),
        ('INS',  'Insumo enológico'),
        ('MO',   'Mano de obra'),
        ('ENE',  'Energía'),
        ('BAR',  'Amortización barrica'),
        ('MAT',  'Material de embotellado'),
        ('GI',   'Gasto indirecto'),
        ('OTR',  'Otro'),
    ]

    costo_lote   = models.ForeignKey(BodCostoLote, on_delete=models.CASCADE,
                                     related_name='detalles')
    fecha        = models.DateField()
    categoria    = models.CharField(max_length=3, choices=CATEGORIA_CHOICES)
    descripcion  = models.CharField(max_length=150)
    cantidad     = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    unidad       = models.CharField(max_length=15, blank=True, default='')
    precio_unit  = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    importe      = models.DecimalField(max_digits=14, decimal_places=2)
    usuario      = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'bod_costo_detalle'
        ordering = ['-fecha']

    def save(self, *args, **kwargs):
        self.importe = round(float(self.cantidad) * float(self.precio_unit), 2)
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# FISCAL / LEGAL — INV (módulo completo faltante)
# ─────────────────────────────────────────────────────────────────────────────

class BodDeclaracionINV(models.Model):
    """
    Declaraciones ante el INV (Instituto Nacional de Vitivinicultura).
    Cubre declaración de cosecha, producción mensual y existencias.
    """
    TIPO_CHOICES = [
        ('COS', 'Declaración de cosecha'),
        ('PRO', 'Declaración de producción'),
        ('EXI', 'Declaración de existencias'),
        ('ELA', 'Declaración de elaboración'),
    ]
    ESTADO_CHOICES = [
        ('BO', 'Borrador'),
        ('PR', 'Presentada'),
        ('AC', 'Aceptada'),
        ('OB', 'Con observaciones'),
    ]

    tipo         = models.CharField(max_length=3, choices=TIPO_CHOICES)
    periodo      = models.DateField(help_text='Primer día del período declarado')
    campaña      = models.SmallIntegerField(null=True, blank=True)
    estado       = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='BO')
    # Totales del período
    kg_uva_declarados   = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    litros_declarados   = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    litros_existencias  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    # Presentación
    fecha_presentacion  = models.DateField(null=True, blank=True)
    nro_expediente_inv  = models.CharField(max_length=40, blank=True, default='')
    observaciones       = models.TextField(blank=True, default='')
    # Datos calculados (JSON con detalle por varietal)
    detalle_varietal    = models.JSONField(default=list, blank=True)
    usuario      = models.CharField(max_length=20, blank=True, default='')
    fecha_mod    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bod_declaracion_inv'
        ordering = ['-periodo', 'tipo']

    def __str__(self):
        return f"{self.get_tipo_display()} {self.periodo.strftime('%m/%Y')} [{self.get_estado_display()}]"


class BodGuiaTraslado(models.Model):
    """
    Guía de traslado de vinos entre establecimientos.
    Documento habilitante exigido por el INV (Art. 36 Ley 14.878).
    """
    TIPO_CHOICES = [
        ('GR', 'Granel'),
        ('PT', 'Producto terminado'),
        ('AM', 'Ambos'),
    ]
    ESTADO_CHOICES = [
        ('EM', 'Emitida'),
        ('US', 'Utilizada'),
        ('AN', 'Anulada'),
        ('VE', 'Vencida'),
    ]

    numero       = models.AutoField(primary_key=True)
    fecha        = models.DateField()
    tipo         = models.CharField(max_length=2, choices=TIPO_CHOICES, default='PT')
    # Origen
    establecimiento_origen = models.CharField(max_length=120, default='')
    domicilio_origen       = models.CharField(max_length=200, blank=True, default='')
    rnoe_origen            = models.CharField(max_length=30, blank=True, default='')
    # Destino
    establecimiento_destino = models.CharField(max_length=120)
    domicilio_destino       = models.CharField(max_length=200, blank=True, default='')
    # Mercadería
    lote         = models.ForeignKey(BodLoteGranel, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='guias_traslado')
    descripcion_mercaderia = models.TextField()
    litros_o_unidades      = models.DecimalField(max_digits=12, decimal_places=2)
    varietal               = models.ForeignKey(
                                 BodVarietal, on_delete=models.SET_NULL,
                                 null=True, blank=True,
                                 db_column='varietal_codigo', to_field='codigo')
    campaña                = models.SmallIntegerField(null=True, blank=True)
    grado_alcohol          = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    # Transporte
    transportista          = models.CharField(max_length=80, blank=True, default='')
    patente_vehiculo       = models.CharField(max_length=15, blank=True, default='')
    # Vinculación con remito del ERP
    movim_remito           = models.BigIntegerField(null=True, blank=True,
                                 help_text='FK a ventas.movim del remito de despacho')
    estado         = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='EM')
    observaciones  = models.TextField(blank=True, default='')
    usuario        = models.CharField(max_length=20, blank=True, default='')
    fecha_mod      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bod_guia_traslado'
        ordering = ['-fecha']

    def __str__(self):
        return f"Guía #{self.numero} → {self.establecimiento_destino} {self.fecha}"


class BodCertificadoAnalisis(models.Model):
    """
    Certificado de análisis enológico para acompañar traslados.
    Requerido por el INV para acreditar aptitud del vino.
    """
    numero       = models.AutoField(primary_key=True)
    lote         = models.ForeignKey(BodLoteGranel, on_delete=models.PROTECT,
                                     related_name='certificados_analisis')
    analisis     = models.ForeignKey(BodAnalisis, on_delete=models.PROTECT,
                                     related_name='certificados', null=True, blank=True)
    guia_traslado = models.ForeignKey(BodGuiaTraslado, on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='certificados')
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField(null=True, blank=True)
    laboratorio   = models.CharField(max_length=80, blank=True, default='INV')
    # Valores certificados
    grado_alcohol = models.DecimalField(max_digits=4, decimal_places=2)
    acidez_total  = models.DecimalField(max_digits=5, decimal_places=2)
    acidez_volatil = models.DecimalField(max_digits=5, decimal_places=2)
    so2_total     = models.DecimalField(max_digits=6, decimal_places=2)
    azucar_residual = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    apto_consumo  = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True, default='')
    usuario       = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'bod_certificado_analisis'
        ordering = ['-fecha_emision']

    def __str__(self):
        return f"Cert. #{self.numero} — {self.lote.codigo} {self.fecha_emision}"


# ═════════════════════════════════════════════════════════════════════════════
# FASE 1 — PROCESO FERMENTATIVO, CATA Y SO₂
# ═════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# FERMENTACIÓN ALCOHÓLICA — PLANILLA DIARIA
# ─────────────────────────────────────────────────────────────────────────────

class BodFermentacionDiaria(models.Model):
    """
    Lectura diaria (o dos veces/día) durante la fermentación alcohólica.
    Permite trazar la curva de densidad, temperatura y alcohol en curso.
    El campo `turno` diferencia la lectura de mañana vs tarde.
    """
    TURNO_CHOICES = [
        ('M', 'Mañana'),
        ('T', 'Tarde'),
        ('N', 'Noche'),
    ]
    SOMBRERO_CHOICES = [
        ('AL', 'Alto — compacto'),
        ('ME', 'Medio — semi-hundido'),
        ('BA', 'Bajo — hundido'),
        ('SN', 'Sin sombrero (blanco/rosado)'),
    ]

    lote             = models.ForeignKey(
                           'BodLoteGranel', on_delete=models.CASCADE,
                           related_name='fermentacion_diaria')
    fecha            = models.DateField()
    turno            = models.CharField(max_length=1, choices=TURNO_CHOICES, default='M')
    # Parámetros principales
    temperatura_c    = models.DecimalField(max_digits=5, decimal_places=2,
                           help_text='Temperatura del mosto en °C')
    densidad         = models.DecimalField(max_digits=7, decimal_places=3,
                           help_text='Densidad en g/L — ej: 1082.5 al inicio, 990 al final')
    brix             = models.DecimalField(max_digits=5, decimal_places=2,
                           null=True, blank=True)
    # Alcohol probable calculado automáticamente
    alcohol_probable = models.DecimalField(max_digits=5, decimal_places=2,
                           null=True, blank=True,
                           help_text='% v/v calculado por fórmula densimétrica')
    # Sombrero (cap) — solo tintos
    estado_sombrero  = models.CharField(max_length=2, choices=SOMBRERO_CHOICES,
                           blank=True, default='SN')
    # Gases / visual
    co2_activo       = models.BooleanField(default=True,
                           help_text='¿Se observa desprendimiento activo de CO₂?')
    color_mosto      = models.CharField(max_length=60, blank=True, default='',
                           help_text='Observación visual del color')
    # Anomalías
    fermentacion_trabada = models.BooleanField(default=False,
                               help_text='True si delta densidad < 1 g/L en últimas 24h')
    observaciones    = models.CharField(max_length=250, blank=True, default='')
    usuario          = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table  = 'bod_fermentacion_diaria'
        ordering  = ['lote', '-fecha', 'turno']
        unique_together = [('lote', 'fecha', 'turno')]

    def save(self, *args, **kwargs):
        """Calcula alcohol probable desde densidad usando fórmula densimétrica estándar."""
        if self.densidad:
            # PA (% v/v) ≈ (1000 - densidad_actual) / 7.4
            # Válido para fermentaciones secas (< 2 g/L azúcar residual)
            d = float(self.densidad)
            if d < 1000:
                self.alcohol_probable = round((1000 - d) / 7.4, 2)
            else:
                self.alcohol_probable = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.lote.codigo} {self.fecha} {self.get_turno_display()} — {self.densidad} g/L"


# ─────────────────────────────────────────────────────────────────────────────
# REMONTAJES Y DÉLESTAGES
# ─────────────────────────────────────────────────────────────────────────────

class BodRemontaje(models.Model):
    """
    Registro de operaciones mecánicas de extracción durante maceración:
    remontaje (pump-over), délestage (rack & return) y bazuqueo (pigeage).
    """
    TIPO_CHOICES = [
        ('REM', 'Remontaje (pump-over)'),
        ('DEL', 'Délestage (rack & return)'),
        ('BAZ', 'Bazuqueo (pigeage)'),
        ('OTR', 'Otra operación mecánica'),
    ]
    OBJETIVO_CHOICES = [
        ('EXT', 'Extracción de color y taninos'),
        ('AIR', 'Aireación del mosto'),
        ('SOL', 'Disolución de SO₂ / levaduras'),
        ('ENF', 'Enfriamiento'),
        ('HOM', 'Homogeneización de temperatura'),
        ('OTR', 'Otro'),
    ]

    lote             = models.ForeignKey(
                           'BodLoteGranel', on_delete=models.CASCADE,
                           related_name='remontajes')
    fecha            = models.DateTimeField()
    tipo             = models.CharField(max_length=3, choices=TIPO_CHOICES, default='REM')
    objetivo         = models.CharField(max_length=3, choices=OBJETIVO_CHOICES, default='EXT')
    # Parámetros operativos
    volumen_bombeado_l   = models.DecimalField(max_digits=8, decimal_places=2,
                               null=True, blank=True,
                               help_text='Litros bombeados (remontaje/délestage)')
    duracion_min         = models.SmallIntegerField(null=True, blank=True)
    caudal_lh            = models.DecimalField(max_digits=8, decimal_places=2,
                               null=True, blank=True,
                               help_text='Caudal de bomba en L/h')
    temperatura_mosto_c  = models.DecimalField(max_digits=5, decimal_places=2,
                               null=True, blank=True)
    # Para délestage: tiempo de escurrido y reinundación
    tiempo_escurrido_min = models.SmallIntegerField(null=True, blank=True,
                               help_text='Minutos que estuvo el orujo escurriendo (délestage)')
    # Resultado observado
    cambio_color         = models.CharField(max_length=100, blank=True, default='',
                               help_text='Ej: intensificación notable del color rojo')
    observaciones        = models.CharField(max_length=250, blank=True, default='')
    usuario              = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'bod_remontaje'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.lote.codigo} {self.fecha}"


# ─────────────────────────────────────────────────────────────────────────────
# FERMENTACIÓN MALOLÁCTICA (FML)
# ─────────────────────────────────────────────────────────────────────────────

class BodFML(models.Model):
    """
    Seguimiento de la fermentación maloláctica por lote.
    Un lote tiene un único registro de FML (o no la realiza).
    """
    TIPO_CHOICES = [
        ('INO', 'Inoculada con bacteria seleccionada'),
        ('ESP', 'Espontánea (flora nativa)'),
        ('NO',  'No se realiza FML'),
    ]
    ESTADO_CHOICES = [
        ('PE', 'Pendiente de inicio'),
        ('EN', 'En curso'),
        ('CO', 'Completada'),
        ('DE', 'Detenida / problema'),
        ('NA', 'No aplica'),
    ]

    lote             = models.OneToOneField(
                           'BodLoteGranel', on_delete=models.CASCADE,
                           related_name='fml')
    tipo             = models.CharField(max_length=3, choices=TIPO_CHOICES, default='INO')
    estado           = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='PE')
    # Inoculación
    fecha_inoculacion = models.DateField(null=True, blank=True)
    cepa_bacteria    = models.CharField(max_length=60, blank=True, default='',
                           help_text='Ej: Oenococcus oeni VP41, Enoferm Alpha')
    dosis_ghl        = models.DecimalField(max_digits=6, decimal_places=3,
                           null=True, blank=True,
                           help_text='Dosis en g/hL')
    temperatura_inicio_c = models.DecimalField(max_digits=4, decimal_places=1,
                               null=True, blank=True,
                               help_text='Temperatura del vino al inocular (mín recomendado: 18°C)')
    ph_al_inicio     = models.DecimalField(max_digits=4, decimal_places=2,
                           null=True, blank=True)
    so2_libre_al_inicio = models.DecimalField(max_digits=5, decimal_places=1,
                              null=True, blank=True,
                              help_text='mg/L — no debe superar 15 mg/L para no inhibir bacteria')
    # Completado
    fecha_completada = models.DateField(null=True, blank=True)
    dias_duracion    = models.SmallIntegerField(null=True, blank=True)
    # Acidez total post-FML (la FML reduce ~1-3 g/L de acidez total)
    acidez_total_post = models.DecimalField(max_digits=5, decimal_places=2,
                            null=True, blank=True,
                            help_text='g/L acidez total una vez completada la FML')
    observaciones    = models.TextField(blank=True, default='')
    usuario          = models.CharField(max_length=20, blank=True, default='')
    fecha_mod        = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bod_fml'

    def save(self, *args, **kwargs):
        if self.fecha_inoculacion and self.fecha_completada:
            self.dias_duracion = (self.fecha_completada - self.fecha_inoculacion).days
        super().save(*args, **kwargs)

    def __str__(self):
        return f"FML {self.lote.codigo} — {self.get_estado_display()}"


class BodCromatografia(models.Model):
    """
    Resultado de cromatografía de papel para control de FML.
    Método visual (mancha de ácido málico presente o ausente).
    """
    RESULTADO_CHOICES = [
        ('MA', 'Ácido málico presente — FML incompleta'),
        ('AU', 'Ácido málico ausente — FML completa'),
        ('TR', 'Traza de málico — finalizando'),
        ('ND', 'No determinado'),
    ]

    fml              = models.ForeignKey(BodFML, on_delete=models.CASCADE,
                                         related_name='cromatografias')
    fecha            = models.DateField()
    resultado        = models.CharField(max_length=2, choices=RESULTADO_CHOICES)
    temperatura_vino = models.DecimalField(max_digits=4, decimal_places=1,
                           null=True, blank=True)
    acidez_volatil   = models.DecimalField(max_digits=4, decimal_places=2,
                           null=True, blank=True,
                           help_text='g/L AV — control de desvíos durante la FML')
    observaciones    = models.CharField(max_length=200, blank=True, default='')
    usuario          = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'bod_cromatografia'
        ordering = ['-fecha']

    def __str__(self):
        return f"Croma {self.fml.lote.codigo} {self.fecha} — {self.get_resultado_display()}"


# ─────────────────────────────────────────────────────────────────────────────
# CATA TÉCNICA
# ─────────────────────────────────────────────────────────────────────────────

class BodCataTecnica(models.Model):
    """
    Evaluación sensorial técnica de un lote de granel.
    Registra color, nariz, boca, defectos detectados, puntaje y conclusión.
    """
    CONTEXTO_CHOICES = [
        ('RU', 'Control de rutina'),
        ('AE', 'Aprobación embotellado'),
        ('CO', 'Comparativa de lotes'),
        ('BL', 'Evaluación previa a blend'),
        ('DE', 'Control de defecto detectado'),
        ('EX', 'Evaluación para exportación'),
    ]
    CONCLUSION_CHOICES = [
        ('AP', 'Apto — continúa proceso normal'),
        ('RC', 'Requiere corrección enológica'),
        ('RE', 'Rechazado — no apto para embotellado'),
        ('PE', 'Pendiente nueva evaluación'),
    ]
    INTENSIDAD_CHOICES = [
        (1, 'Baja'),
        (2, 'Media-baja'),
        (3, 'Media'),
        (4, 'Media-alta'),
        (5, 'Alta'),
    ]

    lote             = models.ForeignKey(
                           'BodLoteGranel', on_delete=models.CASCADE,
                           related_name='catas')
    fecha            = models.DateField()
    contexto         = models.CharField(max_length=2, choices=CONTEXTO_CHOICES, default='RU')
    catadores        = models.CharField(max_length=200,
                           help_text='Nombres separados por coma')
    temperatura_servicio = models.DecimalField(max_digits=4, decimal_places=1,
                               null=True, blank=True,
                               help_text='°C a la que se sirvió la muestra')
    # ── Vista / Color ─────────────────────────────────────────────────────────
    color_intensidad = models.SmallIntegerField(choices=INTENSIDAD_CHOICES, null=True, blank=True)
    color_tonalidad  = models.CharField(max_length=60, blank=True, default='',
                           help_text='Ej: rojo rubí con ribetes violáceos, amarillo verdoso')
    color_limpidez   = models.CharField(max_length=30, blank=True, default='',
                           help_text='Brillante / Limpio / Ligeramente turbio / Turbio')
    # ── Nariz ─────────────────────────────────────────────────────────────────
    nariz_intensidad = models.SmallIntegerField(choices=INTENSIDAD_CHOICES, null=True, blank=True)
    nariz_calidad    = models.CharField(max_length=30, blank=True, default='',
                           help_text='Limpio / Con defecto leve / Con defecto marcado')
    nariz_descriptores = models.CharField(max_length=300, blank=True, default='',
                             help_text='Ej: frutos rojos frescos, especias, vainilla, tierra')
    # ── Boca ──────────────────────────────────────────────────────────────────
    boca_ataque      = models.CharField(max_length=30, blank=True, default='',
                           help_text='Fresco / Suave / Punzante / Áspero')
    boca_acidez      = models.SmallIntegerField(choices=INTENSIDAD_CHOICES, null=True, blank=True)
    boca_taninos     = models.CharField(max_length=60, blank=True, default='',
                           help_text='Sedosos / Firmes / Astringentes / Rugosos / Secos')
    boca_cuerpo      = models.CharField(max_length=30, blank=True, default='',
                           help_text='Ligero / Medio / Amplio / Voluminoso')
    boca_final_s     = models.SmallIntegerField(null=True, blank=True,
                           help_text='Persistencia en segundos (caudalía)')
    boca_balance     = models.CharField(max_length=30, blank=True, default='',
                           help_text='Equilibrado / Desequilibrado / En evolución')
    # ── Defectos ──────────────────────────────────────────────────────────────
    defecto_brett    = models.BooleanField(default=False,
                           help_text='Brettanomyces (cuero, sudor, establo)')
    defecto_reduccion = models.BooleanField(default=False,
                            help_text='Reducción (azufre, hule quemado, cebolla)')
    defecto_va_alta  = models.BooleanField(default=False,
                           help_text='Acidez volátil marcada (vinagre, acetato de etilo)')
    defecto_oxidacion = models.BooleanField(default=False,
                            help_text='Oxidación (manzana pasada, nuez, ranciedad)')
    defecto_turbidez = models.BooleanField(default=False)
    defecto_otro     = models.CharField(max_length=100, blank=True, default='')
    # ── Evaluación global ─────────────────────────────────────────────────────
    puntaje          = models.SmallIntegerField(null=True, blank=True,
                           help_text='Escala 0-100 (Parker/Wine Spectator)')
    conclusion       = models.CharField(max_length=2, choices=CONCLUSION_CHOICES, default='AP')
    accion_recomendada = models.TextField(blank=True, default='',
                             help_text='Corrección enológica recomendada si aplica')
    observaciones    = models.TextField(blank=True, default='')
    usuario          = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'bod_cata_tecnica'
        ordering = ['-fecha']

    @property
    def tiene_defectos(self):
        return any([self.defecto_brett, self.defecto_reduccion,
                    self.defecto_va_alta, self.defecto_oxidacion,
                    self.defecto_turbidez, bool(self.defecto_otro)])

    def __str__(self):
        return f"Cata {self.lote.codigo} {self.fecha} [{self.get_conclusion_display()}]"


# ─────────────────────────────────────────────────────────────────────────────
# GESTIÓN ACTIVA DE SO₂ LIBRE
# ─────────────────────────────────────────────────────────────────────────────

class BodGestionSO2(models.Model):
    """
    Registro de medición y adición de SO₂ por lote.
    Calcula automáticamente la dosis necesaria para alcanzar el SO₂ molecular
    objetivo (0.5–0.8 mg/L) en función del pH actual del vino.

    Fórmula:
        SO₂ molecular (mg/L) = SO₂ libre / (1 + 10^(pH − 1.81))
        SO₂ libre necesario   = objetivo_molecular × (1 + 10^(pH − 1.81))
        Déficit               = libre_necesario − libre_medido
        Gramos SO₂ puro       = déficit × litros_lote / 1000
        Gramos metabisulfito K = g_SO₂_puro / 0.57
    """
    PRODUCTO_CHOICES = [
        ('MBK', 'Metabisulfito de potasio (K₂S₂O₅)'),
        ('SO2', 'SO₂ gaseoso'),
        ('SOL', 'Solución sulfurosa (6%)'),
        ('OTR', 'Otro'),
    ]

    lote                   = models.ForeignKey(
                                 'BodLoteGranel', on_delete=models.CASCADE,
                                 related_name='gestiones_so2')
    fecha                  = models.DateTimeField()
    # Medición actual
    so2_libre_medido       = models.DecimalField(max_digits=6, decimal_places=2,
                                 help_text='mg/L SO₂ libre medido (Ripper o Aeration-Oxidation)')
    ph_actual              = models.DecimalField(max_digits=4, decimal_places=2)
    temperatura_bodega_c   = models.DecimalField(max_digits=4, decimal_places=1,
                                 null=True, blank=True,
                                 help_text='°C de la bodega (afecta la velocidad de caída de SO₂)')
    # Target
    so2_molecular_objetivo = models.DecimalField(max_digits=4, decimal_places=2, default=0.5,
                                 help_text='mg/L SO₂ molecular objetivo (0.5 vinos tintos, 0.8 blancos/dulces)')
    # Calculados automáticamente
    so2_molecular_actual   = models.DecimalField(max_digits=5, decimal_places=3,
                                 null=True, blank=True,
                                 help_text='mg/L SO₂ molecular real calculado')
    so2_libre_necesario    = models.DecimalField(max_digits=6, decimal_places=2,
                                 null=True, blank=True,
                                 help_text='mg/L SO₂ libre necesario para alcanzar objetivo')
    deficit_so2            = models.DecimalField(max_digits=6, decimal_places=2,
                                 null=True, blank=True,
                                 help_text='mg/L déficit a corregir')
    # Dosis calculada para el lote completo
    gramos_so2_puro        = models.DecimalField(max_digits=8, decimal_places=2,
                                 null=True, blank=True)
    gramos_metabisulfito   = models.DecimalField(max_digits=8, decimal_places=2,
                                 null=True, blank=True,
                                 help_text='Gramos de metabisulfito de potasio a agregar')
    # Adición real efectuada
    adicion_realizada      = models.BooleanField(default=False)
    producto_usado         = models.CharField(max_length=3, choices=PRODUCTO_CHOICES,
                                 blank=True, default='MBK')
    gramos_agregados_real  = models.DecimalField(max_digits=8, decimal_places=2,
                                 null=True, blank=True)
    metodo_medicion        = models.CharField(max_length=30, blank=True, default='Ripper',
                                 help_text='Método de medición: Ripper, Aeration-Oxidation, etc.')
    # Próxima medición recomendada
    proxima_medicion       = models.DateField(null=True, blank=True,
                                 help_text='Fecha estimada para próxima medición')
    observaciones          = models.CharField(max_length=250, blank=True, default='')
    usuario                = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'bod_gestion_so2'
        ordering = ['-fecha']

    def calcular(self):
        """Ejecuta los cálculos de SO₂ y los guarda en los campos calculados."""
        import math
        libre   = float(self.so2_libre_medido)
        ph      = float(self.ph_actual)
        obj_mol = float(self.so2_molecular_objetivo)

        factor = 1 + 10 ** (ph - 1.81)
        self.so2_molecular_actual  = round(libre / factor, 3)
        self.so2_libre_necesario   = round(obj_mol * factor, 2)
        deficit = max(0, self.so2_libre_necesario - libre)
        self.deficit_so2 = round(deficit, 2)

        # Volumen del lote para calcular gramos totales
        litros = float(self.lote.litros_actuales or 1000)
        g_so2  = deficit * litros / 1000
        self.gramos_so2_puro      = round(g_so2, 2)
        self.gramos_metabisulfito = round(g_so2 / 0.57, 1)
        return self

    def save(self, *args, **kwargs):
        self.calcular()
        super().save(*args, **kwargs)

    def __str__(self):
        return (f"SO₂ {self.lote.codigo} {self.fecha} — "
                f"libre: {self.so2_libre_medido} mg/L | "
                f"molecular: {self.so2_molecular_actual} mg/L")