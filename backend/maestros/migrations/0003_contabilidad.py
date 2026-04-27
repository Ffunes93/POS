"""
0003_contabilidad.py
Crea las tablas de contabilidad y siembra el plan de cuentas
estándar para comercio minorista argentino.
"""
from django.db import migrations, models
import django.db.models.deletion


PLAN = [
    # (codigo, nombre, tipo, nivel, padre, imputable, saldo_tipo)
    # tipo: A=Activo  P=Pasivo  PN=PatrimonioNeto  I=Ingreso  E=Egreso
    # saldo_tipo: D=Deudora  C=Acreedora
    # ── ACTIVO ────────────────────────────────────────────────────────────────
    ('1',           'ACTIVO',                    'A',  1, None,        False, 'D'),
    ('1.1',         'Activo Corriente',           'A',  2, '1',         False, 'D'),
    ('1.1.01',      'Caja y Bancos',              'A',  3, '1.1',       False, 'D'),
    ('1.1.01.001',  'Caja',                       'A',  4, '1.1.01',    True,  'D'),
    ('1.1.01.002',  'Banco - Cta. Corriente',     'A',  4, '1.1.01',    True,  'D'),
    ('1.1.01.003',  'Fondo Fijo',                 'A',  4, '1.1.01',    True,  'D'),
    ('1.1.02',      'Inversiones Temporarias',    'A',  3, '1.1',       False, 'D'),
    ('1.1.02.001',  'Plazos Fijos',               'A',  4, '1.1.02',    True,  'D'),
    ('1.1.03',      'Créditos por Ventas',        'A',  3, '1.1',       False, 'D'),
    ('1.1.03.001',  'Deudores por Ventas',        'A',  4, '1.1.03',    True,  'D'),
    ('1.1.03.002',  'Documentos a Cobrar',        'A',  4, '1.1.03',    True,  'D'),
    ('1.1.04',      'Otros Créditos',             'A',  3, '1.1',       False, 'D'),
    ('1.1.04.001',  'IVA Crédito Fiscal',         'A',  4, '1.1.04',    True,  'D'),
    ('1.1.04.002',  'Otros Créditos Fiscales',    'A',  4, '1.1.04',    True,  'D'),
    ('1.1.04.003',  'Anticipos a Proveedores',    'A',  4, '1.1.04',    True,  'D'),
    ('1.1.05',      'Bienes de Cambio',           'A',  3, '1.1',       False, 'D'),
    ('1.1.05.001',  'Mercaderías',                'A',  4, '1.1.05',    True,  'D'),
    ('1.2',         'Activo No Corriente',        'A',  2, '1',         False, 'D'),
    ('1.2.01',      'Bienes de Uso',              'A',  3, '1.2',       False, 'D'),
    ('1.2.01.001',  'Rodados',                    'A',  4, '1.2.01',    True,  'D'),
    ('1.2.01.002',  'Muebles y Útiles',           'A',  4, '1.2.01',    True,  'D'),
    ('1.2.01.003',  'Equipos Informáticos',       'A',  4, '1.2.01',    True,  'D'),
    ('1.2.01.004',  'Instalaciones',              'A',  4, '1.2.01',    True,  'D'),
    # ── PASIVO ────────────────────────────────────────────────────────────────
    ('2',           'PASIVO',                     'P',  1, None,        False, 'C'),
    ('2.1',         'Pasivo Corriente',           'P',  2, '2',         False, 'C'),
    ('2.1.01',      'Deudas Comerciales',         'P',  3, '2.1',       False, 'C'),
    ('2.1.01.001',  'Proveedores',                'P',  4, '2.1.01',    True,  'C'),
    ('2.1.01.002',  'Documentos a Pagar',         'P',  4, '2.1.01',    True,  'C'),
    ('2.1.02',      'Deudas Fiscales',            'P',  3, '2.1',       False, 'C'),
    ('2.1.02.001',  'IVA Débito Fiscal',          'P',  4, '2.1.02',    True,  'C'),
    ('2.1.02.002',  'IIBB a Pagar',               'P',  4, '2.1.02',    True,  'C'),
    ('2.1.02.003',  'Retenciones a Pagar',        'P',  4, '2.1.02',    True,  'C'),
    ('2.1.03',      'Deudas Laborales',           'P',  3, '2.1',       False, 'C'),
    ('2.1.03.001',  'Sueldos a Pagar',            'P',  4, '2.1.03',    True,  'C'),
    ('2.1.03.002',  'Cargas Sociales a Pagar',    'P',  4, '2.1.03',    True,  'C'),
    ('2.1.04',      'Otras Deudas',               'P',  3, '2.1',       False, 'C'),
    ('2.1.04.001',  'Anticipos de Clientes',      'P',  4, '2.1.04',    True,  'C'),
    ('2.2',         'Pasivo No Corriente',        'P',  2, '2',         False, 'C'),
    ('2.2.01',      'Préstamos a Largo Plazo',    'P',  3, '2.2',       False, 'C'),
    ('2.2.01.001',  'Préstamos Bancarios L/P',    'P',  4, '2.2.01',    True,  'C'),
    # ── PATRIMONIO NETO ───────────────────────────────────────────────────────
    ('3',           'PATRIMONIO NETO',            'PN', 1, None,        False, 'C'),
    ('3.1',         'Capital',                    'PN', 2, '3',         False, 'C'),
    ('3.1.01',      'Capital Social',             'PN', 3, '3.1',       False, 'C'),
    ('3.1.01.001',  'Capital Suscripto',          'PN', 4, '3.1.01',    True,  'C'),
    ('3.2',         'Reservas',                   'PN', 2, '3',         False, 'C'),
    ('3.2.01',      'Reserva Legal',              'PN', 3, '3.2',       False, 'C'),
    ('3.2.01.001',  'Reserva Legal',              'PN', 4, '3.2.01',    True,  'C'),
    ('3.3',         'Resultados',                 'PN', 2, '3',         False, 'C'),
    ('3.3.01',      'Resultados Acumulados',      'PN', 3, '3.3',       False, 'C'),
    ('3.3.01.001',  'Resultados No Asignados',    'PN', 4, '3.3.01',    True,  'C'),
    # ── INGRESOS ──────────────────────────────────────────────────────────────
    ('4',           'INGRESOS',                   'I',  1, None,        False, 'C'),
    ('4.1',         'Ventas',                     'I',  2, '4',         False, 'C'),
    ('4.1.01',      'Ventas de Mercaderías',      'I',  3, '4.1',       False, 'C'),
    ('4.1.01.001',  'Ventas Gravadas 21%',        'I',  4, '4.1.01',    True,  'C'),
    ('4.1.01.002',  'Ventas Gravadas 10.5%',      'I',  4, '4.1.01',    True,  'C'),
    ('4.1.01.003',  'Ventas Exentas',             'I',  4, '4.1.01',    True,  'C'),
    ('4.1.02',      'Descuentos s/ Ventas',       'I',  3, '4.1',       False, 'C'),
    ('4.1.02.001',  'Descuentos Otorgados',       'I',  4, '4.1.02',    True,  'C'),
    ('4.2',         'Otros Ingresos',             'I',  2, '4',         False, 'C'),
    ('4.2.01',      'Ingresos Financieros',       'I',  3, '4.2',       False, 'C'),
    ('4.2.01.001',  'Intereses Ganados',          'I',  4, '4.2.01',    True,  'C'),
    ('4.2.01.002',  'Diferencias de Cambio',      'I',  4, '4.2.01',    True,  'C'),
    # ── EGRESOS ───────────────────────────────────────────────────────────────
    ('5',           'EGRESOS',                    'E',  1, None,        False, 'D'),
    ('5.1',         'Costo de Ventas',            'E',  2, '5',         False, 'D'),
    ('5.1.01',      'Costo de Mercaderías',       'E',  3, '5.1',       False, 'D'),
    ('5.1.01.001',  'CMV - Mercaderías',          'E',  4, '5.1.01',    True,  'D'),
    ('5.2',         'Gastos de Comercialización', 'E',  2, '5',         False, 'D'),
    ('5.2.01',      'Gastos de Venta',            'E',  3, '5.2',       False, 'D'),
    ('5.2.01.001',  'Comisiones sobre Ventas',    'E',  4, '5.2.01',    True,  'D'),
    ('5.2.01.002',  'Publicidad y Propaganda',    'E',  4, '5.2.01',    True,  'D'),
    ('5.3',         'Gastos de Administración',   'E',  2, '5',         False, 'D'),
    ('5.3.01',      'Gastos Generales',           'E',  3, '5.3',       False, 'D'),
    ('5.3.01.001',  'Sueldos y Jornales',         'E',  4, '5.3.01',    True,  'D'),
    ('5.3.01.002',  'Cargas Sociales',            'E',  4, '5.3.01',    True,  'D'),
    ('5.3.01.003',  'Alquileres',                 'E',  4, '5.3.01',    True,  'D'),
    ('5.3.01.004',  'Servicios Públicos',         'E',  4, '5.3.01',    True,  'D'),
    ('5.3.01.005',  'Gastos de Mantenimiento',    'E',  4, '5.3.01',    True,  'D'),
    ('5.3.01.006',  'Librería y Útiles de Of.',   'E',  4, '5.3.01',    True,  'D'),
    ('5.3.01.007',  'Gastos Varios',              'E',  4, '5.3.01',    True,  'D'),
    ('5.4',         'Gastos Financieros',         'E',  2, '5',         False, 'D'),
    ('5.4.01',      'Gastos Financieros',         'E',  3, '5.4',       False, 'D'),
    ('5.4.01.001',  'Intereses Pagados',          'E',  4, '5.4.01',    True,  'D'),
    ('5.4.01.002',  'Gastos Bancarios',           'E',  4, '5.4.01',    True,  'D'),
    ('5.4.01.003',  'Dif. de Cambio Negativa',    'E',  4, '5.4.01',    True,  'D'),
]


def seed_plan_cuentas(apps, schema_editor):
    ContabPlanCuentas = apps.get_model('maestros', 'ContabPlanCuentas')
    for codigo, nombre, tipo, nivel, padre, imputable, saldo_tipo in PLAN:
        ContabPlanCuentas.objects.get_or_create(
            codigo=codigo,
            defaults=dict(
                nombre=nombre, tipo=tipo, nivel=nivel,
                padre_id=padre, es_imputable=imputable,
                saldo_tipo=saldo_tipo, activa=True,
            ),
        )


def reverse_seed(apps, schema_editor):
    pass  # non-destructive rollback


class Migration(migrations.Migration):

    dependencies = [
        ('maestros', '0002_alter_articulos_options'),
    ]

    operations = [
        # ── Plan de cuentas ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='ContabPlanCuentas',
            fields=[
                ('codigo',      models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('nombre',      models.CharField(max_length=100)),
                ('tipo',        models.CharField(max_length=2,
                                choices=[('A','Activo'),('P','Pasivo'),('PN','Patrimonio Neto'),
                                         ('I','Ingreso'),('E','Egreso')])),
                ('nivel',       models.SmallIntegerField()),
                ('padre',       models.ForeignKey('self', null=True, blank=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                related_name='hijos', db_column='padre_id')),
                ('es_imputable',models.BooleanField(default=True)),
                ('saldo_tipo',  models.CharField(max_length=1,
                                choices=[('D','Deudora'),('C','Acreedora')], default='D')),
                ('activa',      models.BooleanField(default=True)),
                ('observaciones', models.CharField(max_length=255, blank=True, null=True)),
            ],
            options={'db_table': 'contab_plan_cuentas', 'ordering': ['codigo']},
        ),

        # ── Cabecera de asiento ───────────────────────────────────────────────
        migrations.CreateModel(
            name='ContabAsiento',
            fields=[
                ('id',           models.BigAutoField(primary_key=True, serialize=False)),
                ('fecha',        models.DateField()),
                ('descripcion',  models.CharField(max_length=255)),
                ('origen',       models.CharField(max_length=5,
                                 choices=[('VTA','Venta'),('CMP','Compra'),
                                          ('REC','Recibo'),('AJU','Ajuste Manual'),
                                          ('ANU','Anulación')],
                                 default='AJU')),
                ('origen_movim', models.BigIntegerField(null=True, blank=True,
                                 help_text='movim o id de la transacción origen')),
                ('usuario',      models.CharField(max_length=20, blank=True, default='')),
                ('fecha_mod',    models.DateTimeField(auto_now=True)),
                ('anulado',      models.BooleanField(default=False)),
            ],
            options={'db_table': 'contab_asientos', 'ordering': ['-fecha', '-id']},
        ),

        # ── Líneas del asiento ────────────────────────────────────────────────
        migrations.CreateModel(
            name='ContabAsientoDet',
            fields=[
                ('id',          models.BigAutoField(primary_key=True, serialize=False)),
                ('asiento',     models.ForeignKey('ContabAsiento', on_delete=django.db.models.deletion.CASCADE,
                                related_name='lineas')),
                ('cuenta',      models.ForeignKey('ContabPlanCuentas', on_delete=django.db.models.deletion.PROTECT,
                                db_column='cuenta_codigo')),
                ('debe',        models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('haber',       models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('descripcion', models.CharField(max_length=100, blank=True, default='')),
            ],
            options={'db_table': 'contab_asientos_det'},
        ),

        # ── Índices ───────────────────────────────────────────────────────────
        migrations.AddIndex(
            model_name='contabasiento',
            index=models.Index(fields=['fecha'], name='contab_asi_fecha_idx'),
        ),
        migrations.AddIndex(
            model_name='contabasiento',
            index=models.Index(fields=['origen', 'origen_movim'], name='contab_asi_origen_idx'),
        ),
        migrations.AddIndex(
            model_name='contabasientodet',
            index=models.Index(fields=['cuenta'], name='contab_det_cuenta_idx'),
        ),

        # ── Seed plan de cuentas ──────────────────────────────────────────────
        migrations.RunPython(seed_plan_cuentas, reverse_seed),
    ]
