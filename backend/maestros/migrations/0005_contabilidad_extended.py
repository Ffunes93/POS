"""
0005_contabilidad_extended.py
Extiende el módulo de contabilidad con:
  - ContabTipoAsiento
  - ContabSerieAsiento
  - ContabEjercicio
  - ContabModeloAsiento + ContabModeloAsientoDet
  - Campos nuevos en ContabAsiento (ejercicio, tipo_asiento, serie, numero, estado)
  - Siembra de datos base (tipos, series y ejercicio actual)
"""
from django.db import migrations, models
import django.db.models.deletion
from datetime import date


# ── Datos semilla ─────────────────────────────────────────────────────────────

TIPOS_ASIENTO = [
    # (codigo, descripcion, excluye_eecc)
    ('001',     'Real',                              False),
    ('002',     'Presupuesto',                       False),
    ('003',     'Impositivos',                       False),
    ('EXCEECC', 'Excluido de los Estados Contables', True),
]

SERIES_ASIENTO = [
    # (codigo, descripcion)
    ('DIA', 'Numeración diario'),
    ('INT', 'Numeración interna'),
    ('PRE', 'Numeración asientos Control Presupuestario'),
]

ANO_ACTUAL = date.today().year


def seed_config(apps, schema_editor):
    TipoAsiento  = apps.get_model('maestros', 'ContabTipoAsiento')
    SerieAsiento = apps.get_model('maestros', 'ContabSerieAsiento')
    Ejercicio    = apps.get_model('maestros', 'ContabEjercicio')

    for codigo, desc, excluye in TIPOS_ASIENTO:
        TipoAsiento.objects.get_or_create(
            codigo=codigo,
            defaults=dict(descripcion=desc, habilitado=True, excluye_eecc=excluye),
        )

    for codigo, desc in SERIES_ASIENTO:
        SerieAsiento.objects.get_or_create(
            codigo=codigo,
            defaults=dict(descripcion=desc, ultimo_nro=0, habilitada=True),
        )

    # Crea ejercicio del año actual si no existe ninguno
    if not Ejercicio.objects.exists():
        Ejercicio.objects.create(
            anio_inicio  = ANO_ACTUAL,
            anio_fin     = ANO_ACTUAL,
            fecha_inicio = date(ANO_ACTUAL, 1, 1),
            fecha_fin    = date(ANO_ACTUAL, 12, 31),
            estado       = 'A',
            descripcion  = f'Ejercicio {ANO_ACTUAL}',
        )


def reverse_seed(apps, schema_editor):
    pass   # non-destructive


class Migration(migrations.Migration):

    # ── IMPORTANTE: depende de 0003_contabilidad Y de 0004_restaurante ────────
    dependencies = [
        ('maestros', '0003_contabilidad'),
        ('maestros', '0004_restaurante'),
    ]

    operations = [

        # ── ContabTipoAsiento ─────────────────────────────────────────────────
        migrations.CreateModel(
            name='ContabTipoAsiento',
            fields=[
                ('codigo',       models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('descripcion',  models.CharField(max_length=60)),
                ('habilitado',   models.BooleanField(default=True)),
                ('excluye_eecc', models.BooleanField(default=False,
                    help_text='Si True, los asientos de este tipo se excluyen de los Estados Contables')),
            ],
            options={'db_table': 'contab_tipo_asiento', 'ordering': ['codigo']},
        ),

        # ── ContabSerieAsiento ────────────────────────────────────────────────
        migrations.CreateModel(
            name='ContabSerieAsiento',
            fields=[
                ('codigo',      models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('descripcion', models.CharField(max_length=60)),
                ('ultimo_nro',  models.IntegerField(default=0)),
                ('habilitada',  models.BooleanField(default=True)),
            ],
            options={'db_table': 'contab_serie_asiento', 'ordering': ['codigo']},
        ),

        # ── ContabEjercicio ───────────────────────────────────────────────────
        migrations.CreateModel(
            name='ContabEjercicio',
            fields=[
                ('id',           models.BigAutoField(primary_key=True, serialize=False)),
                ('anio_inicio',  models.SmallIntegerField()),
                ('anio_fin',     models.SmallIntegerField()),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin',    models.DateField()),
                ('estado',       models.CharField(max_length=1,
                                 choices=[('A', 'Abierto'), ('C', 'Cerrado')],
                                 default='A')),
                ('descripcion',  models.CharField(max_length=80, blank=True, default='')),
                ('usa_ajuste_inflacion', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'contab_ejercicio',
                'ordering': ['-anio_inicio'],
            },
        ),
        migrations.AddConstraint(
            model_name='contabejercicio',
            constraint=models.UniqueConstraint(
                fields=['anio_inicio', 'anio_fin'],
                name='uq_ejercicio_anio'
            ),
        ),

        # ── ContabModeloAsiento ───────────────────────────────────────────────
        migrations.CreateModel(
            name='ContabModeloAsiento',
            fields=[
                ('codigo',       models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('descripcion',  models.CharField(max_length=100)),
                ('habilitado',   models.BooleanField(default=True)),
                ('tipo_asiento', models.ForeignKey('ContabTipoAsiento', null=True, blank=True,
                                 on_delete=django.db.models.deletion.SET_NULL,
                                 db_column='tipo_asiento_id')),
            ],
            options={'db_table': 'contab_modelo_asiento', 'ordering': ['codigo']},
        ),

        # ── ContabModeloAsientoDet ────────────────────────────────────────────
        migrations.CreateModel(
            name='ContabModeloAsientoDet',
            fields=[
                ('id',          models.BigAutoField(primary_key=True, serialize=False)),
                ('modelo',      models.ForeignKey('ContabModeloAsiento',
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name='lineas')),
                ('orden',       models.SmallIntegerField(default=0)),
                ('cuenta',      models.ForeignKey('ContabPlanCuentas',
                                on_delete=django.db.models.deletion.PROTECT,
                                db_column='cuenta_codigo')),
                ('tipo',        models.CharField(max_length=1,
                                choices=[('D', 'Debe'), ('H', 'Haber')])),
                ('importe',     models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('descripcion', models.CharField(max_length=100, blank=True, default='')),
            ],
            options={'db_table': 'contab_modelo_asiento_det', 'ordering': ['orden']},
        ),

        # ── Nuevos campos en ContabAsiento ────────────────────────────────────
        migrations.AddField(
            model_name='contabasiento',
            name='ejercicio',
            field=models.ForeignKey('ContabEjercicio', null=True, blank=True,
                                    on_delete=django.db.models.deletion.SET_NULL,
                                    db_column='ejercicio_id',
                                    related_name='asientos'),
        ),
        migrations.AddField(
            model_name='contabasiento',
            name='tipo_asiento',
            field=models.ForeignKey('ContabTipoAsiento', null=True, blank=True,
                                    on_delete=django.db.models.deletion.PROTECT,
                                    db_column='tipo_asiento_id'),
        ),
        migrations.AddField(
            model_name='contabasiento',
            name='serie',
            field=models.ForeignKey('ContabSerieAsiento', null=True, blank=True,
                                    on_delete=django.db.models.deletion.SET_NULL,
                                    db_column='serie_id'),
        ),
        migrations.AddField(
            model_name='contabasiento',
            name='numero',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='contabasiento',
            name='estado',
            field=models.CharField(max_length=1,
                choices=[('B', 'Borrador'), ('L', 'Listo p/Mayorizar'),
                         ('M', 'Mayorizado'), ('A', 'Anulado')],
                default='M'),
        ),
        migrations.AddField(
            model_name='contabasiento',
            name='asiento_origen',
            field=models.ForeignKey('ContabAsiento', null=True, blank=True,
                                    on_delete=django.db.models.deletion.SET_NULL,
                                    related_name='contraasientos'),
        ),

        # ── Nuevos campos en ContabPlanCuentas ────────────────────────────────
        migrations.AddField(
            model_name='contabplancuentas',
            name='codigo_alt',
            field=models.CharField(max_length=20, blank=True, default=''),
        ),
        migrations.AddField(
            model_name='contabplancuentas',
            name='col_impresion',
            field=models.SmallIntegerField(default=1),
        ),

        # ── Índice nuevo en ContabAsiento ─────────────────────────────────────
        migrations.AddIndex(
            model_name='contabasiento',
            index=models.Index(fields=['ejercicio', 'estado'], name='contab_asi_ej_estado_idx'),
        ),

        # ── Siembra de datos base ─────────────────────────────────────────────
        migrations.RunPython(seed_config, reverse_seed),
    ]