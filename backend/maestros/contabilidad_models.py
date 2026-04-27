"""
contabilidad_models.py
Modelos para el módulo de contabilidad.
Agregar al final de models.py:  from .contabilidad_models import *
"""
from django.db import models


class ContabPlanCuentas(models.Model):
    TIPO_CHOICES = [
        ('A',  'Activo'),
        ('P',  'Pasivo'),
        ('PN', 'Patrimonio Neto'),
        ('I',  'Ingreso'),
        ('E',  'Egreso'),
    ]
    SALDO_CHOICES = [('D', 'Deudora'), ('C', 'Acreedora')]

    codigo       = models.CharField(max_length=20, primary_key=True)
    nombre       = models.CharField(max_length=100)
    tipo         = models.CharField(max_length=2, choices=TIPO_CHOICES)
    nivel        = models.SmallIntegerField()
    padre        = models.ForeignKey(
                       'self', null=True, blank=True,
                       on_delete=models.SET_NULL,
                       related_name='hijos', db_column='padre_id')
    es_imputable = models.BooleanField(default=True)
    saldo_tipo   = models.CharField(max_length=1, choices=SALDO_CHOICES, default='D')
    activa       = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'contab_plan_cuentas'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class ContabAsiento(models.Model):
    ORIGEN_CHOICES = [
        ('VTA', 'Venta'),
        ('CMP', 'Compra'),
        ('REC', 'Recibo'),
        ('AJU', 'Ajuste Manual'),
        ('ANU', 'Anulación'),
    ]

    id           = models.BigAutoField(primary_key=True)
    fecha        = models.DateField()
    descripcion  = models.CharField(max_length=255)
    origen       = models.CharField(max_length=5, choices=ORIGEN_CHOICES, default='AJU')
    origen_movim = models.BigIntegerField(null=True, blank=True)
    usuario      = models.CharField(max_length=20, blank=True, default='')
    fecha_mod    = models.DateTimeField(auto_now=True)
    anulado      = models.BooleanField(default=False)

    class Meta:
        db_table = 'contab_asientos'
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f"Asiento #{self.id} - {self.fecha} - {self.descripcion}"


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

    def __str__(self):
        return f"{self.cuenta_id} | D:{self.debe} H:{self.haber}"
