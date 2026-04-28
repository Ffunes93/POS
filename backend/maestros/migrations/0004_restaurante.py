"""
0004_restaurante.py
Crea las tablas del módulo de restaurante y siembra datos iniciales
(1 sector "Salón" con 6 mesas de ejemplo).
"""
from django.db import migrations, models
import django.db.models.deletion


def seed_restaurante(apps, schema_editor):
    RestSector = apps.get_model('maestros', 'RestSector')
    RestMesa   = apps.get_model('maestros', 'RestMesa')

    # Sector por defecto
    salon = RestSector.objects.create(
        nombre='Salón',
        color='#2980b9',
        orden=1,
        activo=True,
    )
    terraza = RestSector.objects.create(
        nombre='Terraza',
        color='#27ae60',
        orden=2,
        activo=True,
    )
    barra = RestSector.objects.create(
        nombre='Barra',
        color='#e67e22',
        orden=3,
        activo=True,
    )

    # Mesas de ejemplo en grilla 3×2 para el Salón
    posiciones = [
        ('1', 4, 40,  40),
        ('2', 4, 200, 40),
        ('3', 4, 360, 40),
        ('4', 2, 40,  180),
        ('5', 2, 200, 180),
        ('6', 6, 360, 180),
    ]
    for num, cap, x, y in posiciones:
        RestMesa.objects.create(
            sector=salon, numero=num, capacidad=cap,
            estado='libre', pos_x=x, pos_y=y, activa=True,
        )

    # Mesas terraza
    for i, (x, y) in enumerate([(40, 40), (220, 40), (400, 40)], start=7):
        RestMesa.objects.create(
            sector=terraza, numero=str(i), capacidad=4,
            estado='libre', pos_x=x, pos_y=y, activa=True,
        )

    # Barra (taburetes)
    for i, x in enumerate([40, 140, 240], start=10):
        RestMesa.objects.create(
            sector=barra, numero=f'B{i-9}', capacidad=1,
            estado='libre', pos_x=x, pos_y=40, activa=True,
        )


def reverse_seed(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('maestros', '0003_contabilidad'),
    ]

    operations = [
        # ── RestSector ────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='RestSector',
            fields=[
                ('id',     models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=40)),
                ('color',  models.CharField(default='#3498db', max_length=7)),
                ('orden',  models.SmallIntegerField(default=0)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={'db_table': 'rest_sectores', 'ordering': ['orden', 'nombre']},
        ),

        # ── RestMesa ──────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='RestMesa',
            fields=[
                ('id',        models.AutoField(primary_key=True, serialize=False)),
                ('sector',    models.ForeignKey('RestSector', on_delete=django.db.models.deletion.PROTECT, related_name='mesas')),
                ('numero',    models.CharField(max_length=10)),
                ('capacidad', models.SmallIntegerField(default=4)),
                ('estado',    models.CharField(
                    choices=[('libre','🟢 Libre'),('ocupada','🔴 Ocupada'),
                              ('cuenta_pedida','🟡 Cuenta pedida'),('reservada','🔵 Reservada')],
                    default='libre', max_length=15)),
                ('pos_x',     models.SmallIntegerField(default=0)),
                ('pos_y',     models.SmallIntegerField(default=0)),
                ('activa',    models.BooleanField(default=True)),
                ('fecha_mod', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'rest_mesas', 'ordering': ['sector', 'numero'],
                     'unique_together': {('sector', 'numero')}},
        ),

        # ── RestPedido ────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='RestPedido',
            fields=[
                ('id',             models.AutoField(primary_key=True, serialize=False)),
                ('mesa',           models.ForeignKey('RestMesa', on_delete=django.db.models.deletion.PROTECT, related_name='pedidos')),
                ('estado',         models.CharField(
                    choices=[('abierto','Abierto'),('enviado','Enviado a cocina'),
                              ('listo','Listo para servir'),('cuenta','Cuenta pedida'),
                              ('facturado','Facturado'),('cancelado','Cancelado')],
                    default='abierto', max_length=12)),
                ('mozo_id',        models.IntegerField(default=1)),
                ('mozo_nombre',    models.CharField(blank=True, default='', max_length=60)),
                ('cod_cli',        models.IntegerField(default=1)),
                ('comensales',     models.SmallIntegerField(default=1)),
                ('observac',       models.CharField(blank=True, default='', max_length=200)),
                ('subtotal',       models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total',          models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('movim_venta',    models.BigIntegerField(blank=True, null=True)),
                ('fecha_apertura', models.DateTimeField(auto_now_add=True)),
                ('fecha_mod',      models.DateTimeField(auto_now=True)),
                ('fecha_cierre',   models.DateTimeField(blank=True, null=True)),
                ('usuario',        models.CharField(blank=True, default='', max_length=20)),
            ],
            options={'db_table': 'rest_pedidos', 'ordering': ['-fecha_apertura']},
        ),

        # ── RestPedidoDet ─────────────────────────────────────────────────────
        migrations.CreateModel(
            name='RestPedidoDet',
            fields=[
                ('id',          models.AutoField(primary_key=True, serialize=False)),
                ('pedido',      models.ForeignKey('RestPedido', on_delete=django.db.models.deletion.CASCADE, related_name='items')),
                ('cod_art',     models.CharField(max_length=40)),
                ('nombre_art',  models.CharField(blank=True, default='', max_length=100)),
                ('cantidad',    models.DecimalField(decimal_places=2, default=1, max_digits=7)),
                ('precio_unit', models.DecimalField(decimal_places=2, default=0, max_digits=11)),
                ('subtotal',    models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('p_iva',       models.DecimalField(decimal_places=2, default=21, max_digits=5)),
                ('observac',    models.CharField(blank=True, default='', max_length=200)),
                ('estado_item', models.CharField(
                    choices=[('pendiente','⏳ Pendiente'),('enviado','📤 Enviado'),
                              ('en_preparacion','👨‍🍳 En preparación'),('listo','✅ Listo'),
                              ('entregado','🍽 Entregado'),('cancelado','❌ Cancelado')],
                    default='pendiente', max_length=15)),
                ('nro_comanda', models.IntegerField(blank=True, null=True)),
                ('turno_envio', models.SmallIntegerField(default=1)),
                ('fecha_mod',   models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'rest_pedidos_det', 'ordering': ['id']},
        ),

        # ── RestComanda ───────────────────────────────────────────────────────
        migrations.CreateModel(
            name='RestComanda',
            fields=[
                ('id',          models.AutoField(primary_key=True, serialize=False)),
                ('pedido',      models.ForeignKey('RestPedido', on_delete=django.db.models.deletion.CASCADE, related_name='comandas')),
                ('nro_comanda', models.IntegerField()),
                ('destino',     models.CharField(
                    choices=[('cocina','🍳 Cocina'),('barra','🍺 Barra'),('caja','💵 Caja')],
                    default='cocina', max_length=10)),
                ('turno',       models.SmallIntegerField(default=1)),
                ('impresa',     models.BooleanField(default=False)),
                ('fecha',       models.DateTimeField(auto_now_add=True)),
                ('usuario',     models.CharField(blank=True, default='', max_length=20)),
            ],
            options={'db_table': 'rest_comandas', 'ordering': ['-fecha'],
                     'unique_together': {('pedido', 'nro_comanda', 'destino')}},
        ),

        # ── Índices ───────────────────────────────────────────────────────────
        migrations.AddIndex(
            model_name='restpedido',
            index=models.Index(fields=['mesa', 'estado'], name='rest_ped_mesa_estado_idx'),
        ),
        migrations.AddIndex(
            model_name='restpedidodet',
            index=models.Index(fields=['estado_item'], name='rest_det_estado_idx'),
        ),

        # ── Datos iniciales ───────────────────────────────────────────────────
        migrations.RunPython(seed_restaurante, reverse_seed),
    ]