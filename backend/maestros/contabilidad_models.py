"""
contabilidad_models.py  (versión extendida)
Modelos para el módulo de contabilidad.

Instrucciones de integración:
  Al final de backend/maestros/models.py conservar:
    from .contabilidad_models import *
"""
from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal


# ─────────────────────────────────────────────────────────────────────────────
# TABLAS DE CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────────

class ContabTipoAsiento(models.Model):
    """
    Tipos de asiento (equivale a la tabla 'Tipos de Asiento' de Onvio).
    Valores base: 001=Real, 002=Presupuesto, 003=Impositivos, EXCEECC=Excluido de EECC
    """
    codigo      = models.CharField(max_length=10, primary_key=True)
    descripcion = models.CharField(max_length=60)
    habilitado  = models.BooleanField(default=True)
    excluye_eecc = models.BooleanField(
        default=False,
        help_text='Si True, los asientos de este tipo se excluyen de los Estados Contables'
    )

    class Meta:
        db_table = 'contab_tipo_asiento'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} — {self.descripcion}"


class ContabSerieAsiento(models.Model):
    """
    Series de numeración de asientos.
    Valores base: DIA=Numeración diario, INT=Numeración interna, PRE=Control Presupuestario
    """
    codigo      = models.CharField(max_length=10, primary_key=True)
    descripcion = models.CharField(max_length=60)
    ultimo_nro  = models.IntegerField(default=0)
    habilitada  = models.BooleanField(default=True)

    class Meta:
        db_table = 'contab_serie_asiento'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} — {self.descripcion}"

    def siguiente_numero(self):
        """Devuelve el próximo número y lo incrementa (con SELECT FOR UPDATE)."""
        from django.db import transaction
        with transaction.atomic():
            serie = ContabSerieAsiento.objects.select_for_update().get(pk=self.codigo)
            serie.ultimo_nro += 1
            serie.save(update_fields=['ultimo_nro'])
            return serie.ultimo_nro


class ContabEjercicio(models.Model):
    """
    Ejercicio contable anual.
    Onvio muestra 'Ejercicio: 2022 - 2022' en el pie de página.
    """
    ESTADO_CHOICES = [
        ('A', 'Abierto'),
        ('C', 'Cerrado'),
    ]
    anio_inicio = models.SmallIntegerField()
    anio_fin    = models.SmallIntegerField()
    fecha_inicio = models.DateField()
    fecha_fin    = models.DateField()
    estado      = models.CharField(max_length=1, choices=ESTADO_CHOICES, default='A')
    descripcion = models.CharField(max_length=80, blank=True, default='')
    # Campos de ajuste por inflación
    usa_ajuste_inflacion = models.BooleanField(default=False)

    class Meta:
        db_table = 'contab_ejercicio'
        ordering = ['-anio_inicio']
        unique_together = [('anio_inicio', 'anio_fin')]

    def __str__(self):
        return f"Ejercicio {self.anio_inicio} - {self.anio_fin} [{self.get_estado_display()}]"

    @classmethod
    def get_activo(cls):
        """Devuelve el ejercicio abierto más reciente."""
        return cls.objects.filter(estado='A').order_by('-anio_inicio').first()


# ─────────────────────────────────────────────────────────────────────────────
# PLAN DE CUENTAS  (sin cambios respecto a versión anterior)
# ─────────────────────────────────────────────────────────────────────────────

class ContabPlanCuentas(models.Model):
    TIPO_CHOICES = [
        ('A',  'Activo'),
        ('P',  'Pasivo'),
        ('PN', 'Patrimonio Neto'),
        ('I',  'Ingreso'),
        ('E',  'Egreso'),
    ]
    SALDO_CHOICES = [('D', 'Deudora'), ('C', 'Acreedora')]

    codigo        = models.CharField(max_length=20, primary_key=True)
    nombre        = models.CharField(max_length=100)
    tipo          = models.CharField(max_length=2, choices=TIPO_CHOICES)
    nivel         = models.SmallIntegerField()
    padre         = models.ForeignKey(
                        'self', null=True, blank=True,
                        on_delete=models.SET_NULL,
                        related_name='hijos', db_column='padre_id')
    es_imputable  = models.BooleanField(default=True)
    saldo_tipo    = models.CharField(max_length=1, choices=SALDO_CHOICES, default='D')
    activa        = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=255, blank=True, null=True)
    # Nuevo: código alternativo (como en Onvio)
    codigo_alt    = models.CharField(max_length=20, blank=True, default='')
    # Nuevo: columna de impresión en balance (1 o 2)
    col_impresion = models.SmallIntegerField(default=1)

    class Meta:
        db_table = 'contab_plan_cuentas'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


# ─────────────────────────────────────────────────────────────────────────────
# MODELOS DE ASIENTOS  (plantillas predefinidas)
# ─────────────────────────────────────────────────────────────────────────────

class ContabModeloAsiento(models.Model):
    """Plantilla de asiento predefinido (Modelos de Asientos en Onvio)."""
    codigo       = models.CharField(max_length=20, primary_key=True)
    descripcion  = models.CharField(max_length=100)
    habilitado   = models.BooleanField(default=True)
    tipo_asiento = models.ForeignKey(
                       ContabTipoAsiento, null=True, blank=True,
                       on_delete=models.SET_NULL,
                       db_column='tipo_asiento_id')

    class Meta:
        db_table = 'contab_modelo_asiento'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} — {self.descripcion}"


class ContabModeloAsientoDet(models.Model):
    """Líneas de una plantilla de asiento."""
    TIPO_CHOICES = [('D', 'Debe'), ('H', 'Haber')]

    modelo      = models.ForeignKey(
                      ContabModeloAsiento, on_delete=models.CASCADE,
                      related_name='lineas')
    orden       = models.SmallIntegerField(default=0)
    cuenta      = models.ForeignKey(
                      ContabPlanCuentas, on_delete=models.PROTECT,
                      db_column='cuenta_codigo')
    tipo        = models.CharField(max_length=1, choices=TIPO_CHOICES)
    importe     = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    descripcion = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        db_table = 'contab_modelo_asiento_det'
        ordering = ['orden']


# ─────────────────────────────────────────────────────────────────────────────
# ASIENTOS  (versión extendida)
# ─────────────────────────────────────────────────────────────────────────────

class ContabAsiento(models.Model):
    ORIGEN_CHOICES = [
        ('VTA', 'Venta'),
        ('CMP', 'Compra'),
        ('REC', 'Recibo'),
        ('AJU', 'Ajuste Manual'),
        ('ANU', 'Anulación'),
        ('APE', 'Apertura'),
        ('CIE', 'Cierre'),
        ('INF', 'Ajuste por Inflación'),
        ('DIF', 'Diferencia de Cambio'),
        ('IMP', 'Importación'),
    ]

    ESTADO_CHOICES = [
        ('B', 'Borrador'),
        ('L', 'Listo p/Mayorizar'),
        ('M', 'Mayorizado'),
        ('A', 'Anulado'),
    ]

    id           = models.BigAutoField(primary_key=True)
    ejercicio    = models.ForeignKey(
                       ContabEjercicio, null=True, blank=True,
                       on_delete=models.SET_NULL,
                       db_column='ejercicio_id',
                       related_name='asientos')
    tipo_asiento = models.ForeignKey(
                       ContabTipoAsiento, null=True, blank=True,
                       on_delete=models.PROTECT,
                       db_column='tipo_asiento_id')
    serie        = models.ForeignKey(
                       ContabSerieAsiento, null=True, blank=True,
                       on_delete=models.SET_NULL,
                       db_column='serie_id')
    numero       = models.IntegerField(null=True, blank=True,
                       help_text='Número correlativo dentro de la serie')
    fecha        = models.DateField()
    descripcion  = models.CharField(max_length=255)
    origen       = models.CharField(max_length=5, choices=ORIGEN_CHOICES, default='AJU')
    origen_movim = models.BigIntegerField(null=True, blank=True)
    estado       = models.CharField(max_length=1, choices=ESTADO_CHOICES, default='M')
    usuario      = models.CharField(max_length=20, blank=True, default='')
    fecha_mod    = models.DateTimeField(auto_now=True)
    anulado      = models.BooleanField(default=False)
    # Referencia al asiento original en caso de contraasiento
    asiento_origen = models.ForeignKey(
                         'self', null=True, blank=True,
                         on_delete=models.SET_NULL,
                         related_name='contraasientos')

    class Meta:
        db_table = 'contab_asientos'
        ordering = ['-fecha', '-id']
        indexes = [
            models.Index(fields=['fecha'], name='contab_asi_fecha_idx2'),
            models.Index(fields=['origen', 'origen_movim'], name='contab_asi_origen_idx2'),
            models.Index(fields=['ejercicio', 'estado'], name='contab_asi_ej_estado_idx'),
        ]

    def __str__(self):
        return f"Asiento #{self.id} - {self.fecha} - {self.descripcion}"

    def clean(self):
        if self.lineas.exists():
            total_debe  = sum(l.debe  for l in self.lineas.all())
            total_haber = sum(l.haber for l in self.lineas.all())
            if abs(total_debe - total_haber) > Decimal('0.02'):
                raise ValidationError(
                    f'El asiento no cuadra: Debe={total_debe} Haber={total_haber}'
                )

    @property
    def total_debe(self):
        return sum(l.debe for l in self.lineas.all())

    @property
    def total_haber(self):
        return sum(l.haber for l in self.lineas.all())

    @property
    def cuadra(self):
        return abs(self.total_debe - self.total_haber) <= Decimal('0.02')


class ContabAsientoDet(models.Model):
    id          = models.BigAutoField(primary_key=True)
    asiento     = models.ForeignKey(
                      ContabAsiento, on_delete=models.CASCADE,
                      related_name='lineas')
    cuenta      = models.ForeignKey(
                      ContabPlanCuentas, on_delete=models.PROTECT,
                      db_column='cuenta_codigo')
    debe        = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    haber       = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    descripcion = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        db_table = 'contab_asientos_det'
        indexes = [
            models.Index(fields=['cuenta'], name='contab_det_cuenta_idx2'),
        ]

    def __str__(self):
        return f"{self.cuenta_id} | D:{self.debe} H:{self.haber}"