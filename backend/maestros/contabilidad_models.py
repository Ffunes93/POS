"""
contabilidad_models.py  (versión Sprint A — Mayo 2026)

Cambios vs versión anterior:
  • [Sprint A] Nuevo modelo ContabConfigCuenta — reemplaza el dict hardcodeado CA={...}
  • [Sprint A] ContabAsiento gana campo `origen_movim_activo` + UniqueConstraint
                para idempotencia a nivel DB (compatible con MySQL/Postgres).

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

    def contiene(self, fecha):
        """True si la fecha cae dentro del rango del ejercicio."""
        return self.fecha_inicio <= fecha <= self.fecha_fin


# ─────────────────────────────────────────────────────────────────────────────
# PLAN DE CUENTAS
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
    codigo_alt    = models.CharField(max_length=20, blank=True, default='')
    col_impresion = models.SmallIntegerField(default=1)

    class Meta:
        db_table = 'contab_plan_cuentas'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN CONTABLE PARAMETRIZABLE  ★ Sprint A · A1 ★
# ─────────────────────────────────────────────────────────────────────────────

class ContabConfigCuenta(models.Model):
    """
    Sprint A · Mapeo de conceptos contables canónicos → cuentas concretas.

    Reemplaza el diccionario hardcodeado CA={...} que estaba en views/contabilidad.py
    Permite que cada empresa defina su propio plan sin tocar código.

    Uso en código:
        from maestros.contabilidad_models import ContabConfigCuenta
        cuenta = ContabConfigCuenta.get_cuenta('VENTAS_21')

    Conceptos cubren:
      • Disponibilidades (caja, banco, valores a depositar, cupones)
      • Créditos (deudores, retenciones sufridas)
      • IVA crédito y débito por alícuota (21, 10.5, 27, 5, 2.5, 0)
      • Ventas por alícuota + exentas
      • Pasivos (proveedores, retenciones practicadas, percepciones, imp. internos)
      • PN (RNA, resultado del ejercicio)
      • Resultados varios (diferencia de cambio, redondeo, comisiones, descuentos)
    """

    CONCEPTO_CHOICES = [
        # ── Activo · Disponibilidades ──────────────────────────────────────
        ('CAJA',                            'Caja'),
        ('BANCO_DEFAULT',                   'Banco por defecto'),
        ('VALORES_A_DEPOSITAR',             'Valores a depositar (cheques)'),
        ('CUPONES_A_COBRAR',                'Cupones tarjetas a cobrar'),

        # ── Activo · Créditos ──────────────────────────────────────────────
        ('DEUDORES_CC',                     'Deudores por ventas (Cta Cte)'),
        ('RETENCION_IVA_SUFRIDA',           'Retención IVA sufrida (crédito fiscal)'),
        ('RETENCION_GAN_SUFRIDA',           'Retención Ganancias sufrida'),
        ('RETENCION_IIBB_SUFRIDA',          'Retención IIBB sufrida'),
        ('RETENCION_SUSS_SUFRIDA',          'Retención SUSS sufrida'),

        # ── Activo · IVA Crédito Fiscal por alícuota ───────────────────────
        ('IVA_CF_21',                       'IVA Crédito Fiscal 21%'),
        ('IVA_CF_10_5',                     'IVA Crédito Fiscal 10.5%'),
        ('IVA_CF_27',                       'IVA Crédito Fiscal 27%'),
        ('IVA_CF_5',                        'IVA Crédito Fiscal 5%'),
        ('IVA_CF_2_5',                      'IVA Crédito Fiscal 2.5%'),
        ('IVA_CF_0',                        'IVA Crédito Fiscal 0%'),

        # ── Activo · Bienes de Cambio ──────────────────────────────────────
        ('MERCADERIAS_DEFAULT',             'Mercaderías (cuenta por defecto)'),

        # ── Pasivo · Comerciales ───────────────────────────────────────────
        ('PROVEEDORES',                     'Proveedores'),

        # ── Pasivo · IVA Débito Fiscal por alícuota ────────────────────────
        ('IVA_DF_21',                       'IVA Débito Fiscal 21%'),
        ('IVA_DF_10_5',                     'IVA Débito Fiscal 10.5%'),
        ('IVA_DF_27',                       'IVA Débito Fiscal 27%'),
        ('IVA_DF_5',                        'IVA Débito Fiscal 5%'),
        ('IVA_DF_2_5',                      'IVA Débito Fiscal 2.5%'),
        ('IVA_DF_0',                        'IVA Débito Fiscal 0%'),

        # ── Pasivo · Retenciones practicadas (a depositar a ARCA) ──────────
        ('RETENCION_IVA_PRACTICADA',        'Retención IVA practicada (a depositar)'),
        ('RETENCION_GAN_PRACTICADA',        'Retención Ganancias practicada'),
        ('RETENCION_IIBB_PRACTICADA',       'Retención IIBB practicada'),

        # ── Pasivo · Percepciones a depositar ──────────────────────────────
        ('PERCEPCION_IIBB_CABA_PRACTICADA', 'Percepción IIBB CABA practicada'),
        ('PERCEPCION_IIBB_BSAS_PRACTICADA', 'Percepción IIBB Bs.As. practicada'),
        ('PERCEPCION_5329_PRACTICADA',      'Percepción RG 5329 practicada'),

        # ── Pasivo · Otros ─────────────────────────────────────────────────
        ('IMPUESTOS_INTERNOS',              'Impuestos Internos a pagar'),

        # ── PN ─────────────────────────────────────────────────────────────
        ('RESULTADO_NO_ASIGNADO',           'Resultados No Asignados'),
        ('RESULTADO_DEL_EJERCICIO',         'Resultado del Ejercicio'),

        # ── Resultado · Ingresos por alícuota ──────────────────────────────
        ('VENTAS_21',                       'Ventas Gravadas 21%'),
        ('VENTAS_10_5',                     'Ventas Gravadas 10.5%'),
        ('VENTAS_27',                       'Ventas Gravadas 27%'),
        ('VENTAS_5',                        'Ventas Gravadas 5%'),
        ('VENTAS_2_5',                      'Ventas Gravadas 2.5%'),
        ('VENTAS_0',                        'Ventas Gravadas 0%'),
        ('VENTAS_EXENTAS',                  'Ventas Exentas'),
        ('VENTAS_NO_GRAVADAS',              'Ventas No Gravadas'),

        # ── Resultado · Egresos / Otros ────────────────────────────────────
        ('DIFERENCIA_REDONDEO',             'Diferencia de redondeo'),
        ('DIFERENCIA_CAMBIO_POS',           'Diferencia de Cambio (ganancia)'),
        ('DIFERENCIA_CAMBIO_NEG',           'Diferencia de Cambio (pérdida)'),
        ('COMISIONES_TARJETAS',             'Comisiones de tarjetas'),
        ('DESCUENTOS_OTORGADOS',            'Descuentos otorgados (Egreso)'),
        ('RECARGOS_FINANCIEROS',            'Recargos Financieros (Ingreso)'),
    ]

    concepto = models.CharField(
        max_length=50, choices=CONCEPTO_CHOICES, primary_key=True,
        help_text='Concepto canónico usado por los generadores de asientos'
    )
    cuenta = models.ForeignKey(
        ContabPlanCuentas,
        on_delete=models.PROTECT,
        db_column='cuenta_codigo',
        help_text='Cuenta del plan que se imputará para este concepto'
    )
    descripcion_extra = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Notas internas o de configuración (ej: "Banco Galicia ARS")'
    )
    fecha_mod = models.DateTimeField(auto_now=True)
    usuario   = models.CharField(max_length=50, blank=True, default='')

    class Meta:
        db_table = 'contab_config_cuenta'
        ordering = ['concepto']
        verbose_name = 'Configuración de Cuenta Contable'
        verbose_name_plural = 'Configuración de Cuentas Contables'

    def __str__(self):
        return f"{self.get_concepto_display()} → {self.cuenta_id}"

    # ── Helpers de uso interno ────────────────────────────────────────────
    @classmethod
    def cargar_mapa(cls):
        """
        Devuelve dict {concepto: codigo_cuenta} con toda la config.
        Pensado para cachear por request en los generadores de asientos.
        """
        return {c.concepto: c.cuenta_id for c in cls.objects.all()}

    @classmethod
    def get_cuenta(cls, concepto):
        """
        Devuelve el código de cuenta para el concepto, o None si no está configurado.
        Usar `obtener_cuenta_obligatoria` cuando el concepto sea esencial.
        """
        try:
            return cls.objects.get(pk=concepto).cuenta_id
        except cls.DoesNotExist:
            return None

    @classmethod
    def obtener_cuenta_obligatoria(cls, concepto):
        """
        Igual que get_cuenta pero lanza ValidationError si falta.
        Usar para conceptos sin los cuales no se puede generar el asiento.
        """
        codigo = cls.get_cuenta(concepto)
        if not codigo:
            raise ValidationError(
                f"Configuración contable faltante: el concepto '{concepto}' no "
                f"tiene cuenta asignada. Ir a /api/contab/Config/Cuentas/ "
                f"para definirla."
            )
        return codigo


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
# ASIENTOS  (versión Sprint A — con UniqueConstraint para idempotencia)
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

    # ★ Sprint A · A3 ★ Campo helper para UNIQUE compatible con MySQL.
    # Vale igual que origen_movim cuando NO está anulado, NULL cuando sí.
    # Como NULL no participa de UNIQUE en MySQL/Postgres, esto crea efectivamente
    # un "partial unique index" portable.
    origen_movim_activo = models.BigIntegerField(null=True, blank=True)

    estado       = models.CharField(max_length=1, choices=ESTADO_CHOICES, default='M')
    usuario      = models.CharField(max_length=20, blank=True, default='')
    fecha_mod    = models.DateTimeField(auto_now=True)
    anulado      = models.BooleanField(default=False)
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
        constraints = [
            # ★ Sprint A · A3 ★ Idempotencia a nivel DB.
            # Garantiza que NO existan dos asientos no-anulados con el mismo
            # (origen, origen_movim). Evita race conditions en SincronizarAsientos.
            models.UniqueConstraint(
                fields=['origen', 'origen_movim_activo'],
                name='uq_asiento_origen_movim_activo',
            ),
        ]

    def save(self, *args, **kwargs):
        """
        Sincroniza origen_movim_activo automáticamente.
        Cuando se anula el asiento, libera el slot para regeneración futura.
        """
        self.origen_movim_activo = None if self.anulado else self.origen_movim
        super().save(*args, **kwargs)

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