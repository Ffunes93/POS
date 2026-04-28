"""
restaurant_models.py
Modelos para el módulo de restaurante/gastronomía.

Agregar al final de models.py:
    from .restaurant_models import *

Tablas nuevas (4):
    rest_sectores, rest_mesas, rest_pedidos, rest_pedidos_det, rest_comandas

Tablas existentes reutilizadas (sin modificar):
    articulos, articulos_rubros, ventas, ventas_det,
    clientes, usuarios, cajas, tipocomp_cli
"""
from django.db import models


class RestSector(models.Model):
    """
    Zona física del local: Salón, Terraza, Barra, VIP, etc.
    Permite organizar el plano de mesas por área.
    """
    nombre   = models.CharField(max_length=40)
    color    = models.CharField(max_length=7, default='#3498db',
                                help_text='Color hex para el plano visual, ej: #e74c3c')
    orden    = models.SmallIntegerField(default=0, help_text='Orden de aparición en pantalla')
    activo   = models.BooleanField(default=True)

    class Meta:
        db_table = 'rest_sectores'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class RestMesa(models.Model):
    """
    Mesa física del local.
    pos_x / pos_y permiten arrastrarla en el plano visual del frontend.
    """
    ESTADO_CHOICES = [
        ('libre',          '🟢 Libre'),
        ('ocupada',        '🔴 Ocupada'),
        ('cuenta_pedida',  '🟡 Cuenta pedida'),
        ('reservada',      '🔵 Reservada'),
    ]

    sector      = models.ForeignKey(RestSector, on_delete=models.PROTECT,
                                    related_name='mesas')
    numero      = models.CharField(max_length=10,
                                   help_text='Número o nombre visible: "1", "A3", "VIP"')
    capacidad   = models.SmallIntegerField(default=4)
    estado      = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='libre')
    pos_x       = models.SmallIntegerField(default=0,
                                           help_text='Posición X en el plano (px)')
    pos_y       = models.SmallIntegerField(default=0,
                                           help_text='Posición Y en el plano (px)')
    activa      = models.BooleanField(default=True)
    fecha_mod   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rest_mesas'
        ordering = ['sector', 'numero']
        unique_together = [('sector', 'numero')]

    def __str__(self):
        return f'Mesa {self.numero} ({self.sector})'


class RestPedido(models.Model):
    """
    Orden/comanda abierta para una mesa.
    Una mesa puede tener solo UN pedido activo a la vez.
    Al facturar, se guarda el movim de ventas en movim_venta.
    """
    ESTADO_CHOICES = [
        ('abierto',    'Abierto'),
        ('enviado',    'Enviado a cocina'),
        ('listo',      'Listo para servir'),
        ('cuenta',     'Cuenta pedida'),
        ('facturado',  'Facturado'),
        ('cancelado',  'Cancelado'),
    ]

    mesa        = models.ForeignKey(RestMesa, on_delete=models.PROTECT,
                                    related_name='pedidos')
    estado      = models.CharField(max_length=12, choices=ESTADO_CHOICES,
                                   default='abierto')
    # Mozo que atiende (FK lazy a usuarios — managed=False, usamos int)
    mozo_id     = models.IntegerField(default=1,
                                      help_text='ID del mozo (usuarios.id)')
    mozo_nombre = models.CharField(max_length=60, blank=True, default='')
    # Cliente (para facturar con datos reales; por defecto consumidor final = 1)
    cod_cli     = models.IntegerField(default=1)
    # Comensales en la mesa
    comensales  = models.SmallIntegerField(default=1)
    # Observaciones generales de la mesa
    observac    = models.CharField(max_length=200, blank=True, default='')
    # Totales (se recalculan al agregar/quitar ítems)
    subtotal    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total       = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Link a la venta generada al facturar
    movim_venta = models.BigIntegerField(null=True, blank=True,
                                         help_text='ventas.movim una vez facturado')
    # Auditoría
    fecha_apertura  = models.DateTimeField(auto_now_add=True)
    fecha_mod       = models.DateTimeField(auto_now=True)
    fecha_cierre    = models.DateTimeField(null=True, blank=True)
    usuario         = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'rest_pedidos'
        ordering = ['-fecha_apertura']

    def __str__(self):
        return f'Pedido #{self.id} Mesa {self.mesa.numero} [{self.estado}]'


class RestPedidoDet(models.Model):
    """
    Línea de detalle de un pedido.
    estado_item permite rastrear el ciclo de vida en cocina/barra.
    """
    ESTADO_ITEM = [
        ('pendiente',       '⏳ Pendiente'),
        ('enviado',         '📤 Enviado a cocina'),
        ('en_preparacion',  '👨‍🍳 En preparación'),
        ('listo',           '✅ Listo'),
        ('entregado',       '🍽 Entregado'),
        ('cancelado',       '❌ Cancelado'),
    ]

    pedido      = models.ForeignKey(RestPedido, on_delete=models.CASCADE,
                                    related_name='items')
    # Artículo del menú (articulos.cod_art — managed=False)
    cod_art     = models.CharField(max_length=40)
    nombre_art  = models.CharField(max_length=100, blank=True, default='')
    cantidad    = models.DecimalField(max_digits=7, decimal_places=2, default=1)
    precio_unit = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    subtotal    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    p_iva       = models.DecimalField(max_digits=5, decimal_places=2, default=21)
    # Observaciones por ítem: "sin sal", "punto jugoso", etc.
    observac    = models.CharField(max_length=200, blank=True, default='')
    estado_item = models.CharField(max_length=15, choices=ESTADO_ITEM,
                                   default='pendiente')
    # Número de comanda en la que fue enviado este ítem a cocina
    nro_comanda = models.IntegerField(null=True, blank=True)
    # Turno de envío (para reenvíos / pedidos adicionales)
    turno_envio = models.SmallIntegerField(default=1)
    fecha_mod   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rest_pedidos_det'
        ordering = ['id']

    def __str__(self):
        return f'{self.cantidad}x {self.nombre_art} [{self.estado_item}]'


class RestComanda(models.Model):
    """
    Ticket/comanda enviada a cocina o barra.
    Agrupa los ítems pendientes de un pedido en un momento dado.
    Una impresión por cocina/barra.
    """
    DESTINO_CHOICES = [
        ('cocina',  '🍳 Cocina'),
        ('barra',   '🍺 Barra'),
        ('caja',    '💵 Caja'),
    ]

    pedido      = models.ForeignKey(RestPedido, on_delete=models.CASCADE,
                                    related_name='comandas')
    nro_comanda = models.IntegerField(help_text='Número secuencial por pedido')
    destino     = models.CharField(max_length=10, choices=DESTINO_CHOICES,
                                   default='cocina')
    turno       = models.SmallIntegerField(default=1,
                                           help_text='1=primer envío, 2=adicional, etc.')
    impresa     = models.BooleanField(default=False)
    fecha       = models.DateTimeField(auto_now_add=True)
    usuario     = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'rest_comandas'
        ordering = ['-fecha']
        unique_together = [('pedido', 'nro_comanda', 'destino')]

    def __str__(self):
        return f'Comanda #{self.nro_comanda} — {self.pedido}'