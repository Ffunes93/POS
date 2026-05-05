"""
Migration: Sprint A · Configuración contable + Idempotencia DB
Fecha: 2026-05-05

Cambios:
  1. Crea tabla `contab_config_cuenta` (modelo ContabConfigCuenta).
  2. Agrega campo `origen_movim_activo` a `contab_asientos`.
  3. Detecta y desduplica asientos con (origen, origen_movim) repetidos
     (mantiene el más reciente, anula los demás).
  4. Backfill de `origen_movim_activo` desde `origen_movim` para asientos
     no anulados.
  5. Agrega UniqueConstraint sobre (origen, origen_movim_activo).

⚠️  IMPORTANTE: ajustar `dependencies` con la última migración real del
    módulo `maestros` antes de aplicar.
"""
from django.db import migrations, models
import django.db.models.deletion


# ─────────────────────────────────────────────────────────────────────────────
# OPERACIONES DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

def deduplicar_asientos(apps, schema_editor):
    """
    Si la BD ya tiene duplicados (origen, origen_movim) no anulados, los detecta
    y anula todos excepto el más reciente para que el UNIQUE no falle.
    """
    ContabAsiento = apps.get_model('maestros', 'ContabAsiento')
    from django.db.models import Count

    duplicados = (
        ContabAsiento.objects
        .filter(anulado=False, origen_movim__isnull=False)
        .values('origen', 'origen_movim')
        .annotate(n=Count('id'))
        .filter(n__gt=1)
    )

    total_anulados = 0
    for dup in duplicados:
        asientos = list(
            ContabAsiento.objects.filter(
                origen=dup['origen'],
                origen_movim=dup['origen_movim'],
                anulado=False,
            ).order_by('-id')
        )
        # Mantener el más reciente, anular el resto
        for asi in asientos[1:]:
            asi.anulado = True
            asi.estado = 'A'
            asi.save(update_fields=['anulado', 'estado'])
            total_anulados += 1

    if total_anulados:
        print(f"  ⚠ Sprint A: {total_anulados} asientos duplicados fueron "
              f"anulados automáticamente para satisfacer UNIQUE.")


def backfill_origen_movim_activo(apps, schema_editor):
    """
    Para asientos NO anulados con origen_movim seteado, copia el valor a
    origen_movim_activo. Para anulados deja NULL (esto libera el slot).
    """
    ContabAsiento = apps.get_model('maestros', 'ContabAsiento')

    # Asientos no anulados → origen_movim_activo = origen_movim
    actualizados = (
        ContabAsiento.objects
        .filter(anulado=False)
        .update(origen_movim_activo=models.F('origen_movim'))
    )
    print(f"  ✓ Sprint A: backfill completado en {actualizados} asientos.")


def reverse_noop(apps, schema_editor):
    """No hace nada — el reverse de los datos es destructivo y no auto-recuperable."""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# CHOICES (replicados acá para que la migración sea reproducible standalone)
# ─────────────────────────────────────────────────────────────────────────────

CONCEPTO_CHOICES = [
    ('CAJA', 'Caja'),
    ('BANCO_DEFAULT', 'Banco por defecto'),
    ('VALORES_A_DEPOSITAR', 'Valores a depositar (cheques)'),
    ('CUPONES_A_COBRAR', 'Cupones tarjetas a cobrar'),
    ('DEUDORES_CC', 'Deudores por ventas (Cta Cte)'),
    ('RETENCION_IVA_SUFRIDA', 'Retención IVA sufrida (crédito fiscal)'),
    ('RETENCION_GAN_SUFRIDA', 'Retención Ganancias sufrida'),
    ('RETENCION_IIBB_SUFRIDA', 'Retención IIBB sufrida'),
    ('RETENCION_SUSS_SUFRIDA', 'Retención SUSS sufrida'),
    ('IVA_CF_21', 'IVA Crédito Fiscal 21%'),
    ('IVA_CF_10_5', 'IVA Crédito Fiscal 10.5%'),
    ('IVA_CF_27', 'IVA Crédito Fiscal 27%'),
    ('IVA_CF_5', 'IVA Crédito Fiscal 5%'),
    ('IVA_CF_2_5', 'IVA Crédito Fiscal 2.5%'),
    ('IVA_CF_0', 'IVA Crédito Fiscal 0%'),
    ('MERCADERIAS_DEFAULT', 'Mercaderías (cuenta por defecto)'),
    ('PROVEEDORES', 'Proveedores'),
    ('IVA_DF_21', 'IVA Débito Fiscal 21%'),
    ('IVA_DF_10_5', 'IVA Débito Fiscal 10.5%'),
    ('IVA_DF_27', 'IVA Débito Fiscal 27%'),
    ('IVA_DF_5', 'IVA Débito Fiscal 5%'),
    ('IVA_DF_2_5', 'IVA Débito Fiscal 2.5%'),
    ('IVA_DF_0', 'IVA Débito Fiscal 0%'),
    ('RETENCION_IVA_PRACTICADA', 'Retención IVA practicada (a depositar)'),
    ('RETENCION_GAN_PRACTICADA', 'Retención Ganancias practicada'),
    ('RETENCION_IIBB_PRACTICADA', 'Retención IIBB practicada'),
    ('PERCEPCION_IIBB_CABA_PRACTICADA', 'Percepción IIBB CABA practicada'),
    ('PERCEPCION_IIBB_BSAS_PRACTICADA', 'Percepción IIBB Bs.As. practicada'),
    ('PERCEPCION_5329_PRACTICADA', 'Percepción RG 5329 practicada'),
    ('IMPUESTOS_INTERNOS', 'Impuestos Internos a pagar'),
    ('RESULTADO_NO_ASIGNADO', 'Resultados No Asignados'),
    ('RESULTADO_DEL_EJERCICIO', 'Resultado del Ejercicio'),
    ('VENTAS_21', 'Ventas Gravadas 21%'),
    ('VENTAS_10_5', 'Ventas Gravadas 10.5%'),
    ('VENTAS_27', 'Ventas Gravadas 27%'),
    ('VENTAS_5', 'Ventas Gravadas 5%'),
    ('VENTAS_2_5', 'Ventas Gravadas 2.5%'),
    ('VENTAS_0', 'Ventas Gravadas 0%'),
    ('VENTAS_EXENTAS', 'Ventas Exentas'),
    ('VENTAS_NO_GRAVADAS', 'Ventas No Gravadas'),
    ('DIFERENCIA_REDONDEO', 'Diferencia de redondeo'),
    ('DIFERENCIA_CAMBIO_POS', 'Diferencia de Cambio (ganancia)'),
    ('DIFERENCIA_CAMBIO_NEG', 'Diferencia de Cambio (pérdida)'),
    ('COMISIONES_TARJETAS', 'Comisiones de tarjetas'),
    ('DESCUENTOS_OTORGADOS', 'Descuentos otorgados (Egreso)'),
    ('RECARGOS_FINANCIEROS', 'Recargos Financieros (Ingreso)'),
]


class Migration(migrations.Migration):

    dependencies = [
        # ⚠️  AJUSTAR: poner acá el nombre de la última migración aplicada.
        # Ejemplo: ('maestros', '0010_alter_imp_iva_alicuotas'),
        ('maestros', '0011_sprint2_iva_alicuotas'),
    ]

    operations = [
        # ─── 1. Crear tabla ContabConfigCuenta ──────────────────────────────
        migrations.CreateModel(
            name='ContabConfigCuenta',
            fields=[
                ('concepto', models.CharField(
                    choices=CONCEPTO_CHOICES,
                    help_text='Concepto canónico usado por los generadores de asientos',
                    max_length=50,
                    primary_key=True,
                    serialize=False
                )),
                ('descripcion_extra', models.CharField(
                    blank=True, default='', max_length=200,
                    help_text='Notas internas o de configuración (ej: "Banco Galicia ARS")'
                )),
                ('fecha_mod', models.DateTimeField(auto_now=True)),
                ('usuario', models.CharField(blank=True, default='', max_length=50)),
                ('cuenta', models.ForeignKey(
                    db_column='cuenta_codigo',
                    on_delete=django.db.models.deletion.PROTECT,
                    to='maestros.contabplancuentas',
                    help_text='Cuenta del plan que se imputará para este concepto'
                )),
            ],
            options={
                'verbose_name': 'Configuración de Cuenta Contable',
                'verbose_name_plural': 'Configuración de Cuentas Contables',
                'db_table': 'contab_config_cuenta',
                'ordering': ['concepto'],
            },
        ),

        # ─── 2. Agregar campo origen_movim_activo ───────────────────────────
        migrations.AddField(
            model_name='contabasiento',
            name='origen_movim_activo',
            field=models.BigIntegerField(blank=True, null=True),
        ),

        # ─── 3. Desduplicar asientos existentes ─────────────────────────────
        migrations.RunPython(deduplicar_asientos, reverse_noop),

        # ─── 4. Backfill de origen_movim_activo ─────────────────────────────
        migrations.RunPython(backfill_origen_movim_activo, reverse_noop),

        # ─── 5. UniqueConstraint final ──────────────────────────────────────
        migrations.AddConstraint(
            model_name='contabasiento',
            constraint=models.UniqueConstraint(
                fields=('origen', 'origen_movim_activo'),
                name='uq_asiento_origen_movim_activo',
            ),
        ),
    ]