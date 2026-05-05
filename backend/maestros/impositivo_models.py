"""
impositivo_models.py — Módulo Informes Impositivos
Modelos para libros IVA, declaraciones juradas y exportaciones a aplicativos ARCA/AFIP.

Sprint 1 (Mayo 2026):
  - B8: max_length de campos de auditoría aumentado de 20 a 50.
  - Comentarios actualizados (AFIP → ARCA donde aplica, Decreto 953/2024).
  - Sin cambios disruptivos sobre datos existentes (solo amplía columnas).

Instrucciones de integración:
    Al final de backend/maestros/models.py agregar:
        from .impositivo_models import *
"""
from django.db import models
from django.contrib.auth.models import User


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN: Puntos de Registración
# ─────────────────────────────────────────────────────────────────────────────

class ImpPuntoRegistracion(models.Model):
    """
    Punto de registración IVA (equivale a punto de venta en el libro IVA).
    Referenciado desde Libro IVA y exportaciones.
    """
    codigo      = models.CharField(max_length=4, primary_key=True)
    descripcion = models.CharField(max_length=60)
    activo      = models.BooleanField(default=True)

    class Meta:
        db_table = 'imp_puntos_registracion'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} — {self.descripcion}"


# ─────────────────────────────────────────────────────────────────────────────
# LIBRO IVA
# ─────────────────────────────────────────────────────────────────────────────

class ImpLibroIVA(models.Model):
    """
    Cabecera de un Libro IVA generado (Ventas o Compras).
    Cada registro representa una emisión del libro para un período.
    """
    CIRCUITO_CHOICES = [('V', 'Ventas'), ('C', 'Compras')]
    TIPO_CHOICES     = [('P', 'Provisorio'), ('D', 'Definitivo')]

    circuito            = models.CharField(max_length=1, choices=CIRCUITO_CHOICES)
    fecha_desde         = models.DateField()
    fecha_hasta         = models.DateField(null=True, blank=True)
    punto_registracion  = models.ForeignKey(
                              ImpPuntoRegistracion, null=True, blank=True,
                              on_delete=models.SET_NULL,
                              db_column='punto_registracion_id')
    tipo                = models.CharField(max_length=1, choices=TIPO_CHOICES, default='P')
    primer_numero       = models.IntegerField(default=1)
    # Opciones de visualización
    mostrar_cert_ret    = models.BooleanField(default=False)
    mostrar_iibb        = models.BooleanField(default=True)
    mostrar_comp_b_agrup= models.BooleanField(default=False)
    mostrar_anulados_agrup = models.BooleanField(default=False)
    margen_superior     = models.BooleanField(default=False)
    lineas_separadoras  = models.BooleanField(default=True)
    imprime_encabezado  = models.BooleanField(default=False)
    texto_encabezado    = models.TextField(blank=True, default='')
    # Auditoría
    creado_en           = models.DateTimeField(auto_now_add=True)
    creado_por          = models.CharField(max_length=50, blank=True, default='')   # B8: 20 → 50

    class Meta:
        db_table = 'imp_libros_iva'
        ordering = ['-fecha_desde', 'circuito']

    def __str__(self):
        return f"Libro IVA {self.get_circuito_display()} {self.fecha_desde} [{self.get_tipo_display()}]"


# ─────────────────────────────────────────────────────────────────────────────
# DECLARACIONES JURADAS
# ─────────────────────────────────────────────────────────────────────────────

class ImpDeclaracionJurada(models.Model):
    """
    Declaración Jurada Mensual IVA.
    Soporta dos versiones: V1=R.C. 3685 (R.G. 715/99) y V2=IVA Estándar.
    """
    VERSION_CHOICES = [('V1', 'R.C. 3685 (R.G. 715/99)'), ('V2', 'IVA Estándar')]
    EMISION_CHOICES = [
        ('O',  'Original'),
        ('R1', 'Rectificativa N° 1'),
        ('R2', 'Rectificativa N° 2'),
        ('R3', 'Rectificativa N° 3'),
    ]

    periodo         = models.DateField(help_text='Primer día del mes del período')
    version         = models.CharField(max_length=2, choices=VERSION_CHOICES, default='V2')
    tipo_emision    = models.CharField(max_length=2, choices=EMISION_CHOICES, default='O')
    pasado_cg       = models.BooleanField(
                          default=False,
                          help_text='Si fue trasladado a Contabilidad General')
    # Totales calculados al momento de la emisión
    total_debito_fiscal  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_credito_fiscal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    saldo_a_pagar        = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    # Auditoría
    emitido_en      = models.DateTimeField(auto_now_add=True)
    emitido_por     = models.CharField(max_length=50, blank=True, default='')        # B8: 20 → 50

    class Meta:
        db_table = 'imp_declaraciones_juradas'
        ordering = ['-periodo', 'version']
        unique_together = [('periodo', 'version', 'tipo_emision')]

    def __str__(self):
        return f"DDJJ {self.periodo.strftime('%m/%Y')} [{self.get_version_display()} — {self.get_tipo_emision_display()}]"


# ─────────────────────────────────────────────────────────────────────────────
# EXPORTACIONES A APLICATIVOS (ARCA/AFIP y provinciales)
# ─────────────────────────────────────────────────────────────────────────────

APLICATIVO_CHOICES = [
    ('SICORE',   'SICORE — Retenciones/Percepciones ARCA'),
    ('SIFERE',   'SIFERE — IIBB Convenio Multilateral'),
    ('SIACER',   'SIACER — IIBB Entre Ríos'),
    ('EARCIBA',  'e-ARCIBA — IIBB CABA'),
    ('SICOL',    'SICOL — Retenciones ARCA'),
    ('REGELEC',  'Reg. Electrónica ARCA'),
    ('DUPELEC',  'Duplicados Electrónicos CAE/CAEA'),
    ('SIRFT',    'SIRFT — IIBB Santa Fe'),
    ('ARBA',     'ARBA A122R — IIBB Buenos Aires'),
    ('SIJP',     'SIJP — Jubilaciones ARCA'),
    ('SVINCUL',  'Sujetos Vinculados ARCA'),
    ('SIRE',     'SIRE — Retenciones ARCA'),
    ('F8001',    'RG 3668 F8001 — Facturas M'),
    ('SIRCAR',   'SIRCAR — IIBB Córdoba'),
    ('SIPRIB',   'SIPRIB — IIBB Santa Fe DGR'),
    ('ITC',      'ITC — Impuesto Transferencia Combustibles'),
]


class ImpExportacionAplicativo(models.Model):
    """
    Registro de cada exportación a aplicativo ARCA/provincial.
    Guarda los parámetros utilizados y el archivo generado para auditoría legal.
    """
    ESTADO_CHOICES = [
        ('PENDIENTE',   'Pendiente'),
        ('PROCESANDO',  'Procesando'),
        ('COMPLETADO',  'Completado'),
        ('ERROR',       'Error'),
    ]
    CIRCUITO_CHOICES = [('V', 'Ventas'), ('C', 'Compras'), ('A', 'Ambos')]

    aplicativo      = models.CharField(max_length=10, choices=APLICATIVO_CHOICES)
    circuito        = models.CharField(max_length=1, choices=CIRCUITO_CHOICES, default='V')
    fecha_desde     = models.DateField()
    fecha_hasta     = models.DateField()
    estado          = models.CharField(max_length=12, choices=ESTADO_CHOICES, default='PENDIENTE')
    # Parámetros específicos del aplicativo (JSON flexible)
    parametros      = models.JSONField(default=dict, blank=True)
    # Archivo generado (nombre + contenido en base64 o ruta)
    nombre_archivo  = models.CharField(max_length=200, blank=True, default='')
    contenido_b64   = models.TextField(blank=True, default='',
                          help_text='Contenido del archivo en base64 para descarga')
    error_mensaje   = models.TextField(blank=True, default='')
    # Auditoría — requerimiento legal ARCA
    generado_en     = models.DateTimeField(auto_now_add=True)
    generado_por    = models.CharField(max_length=50, blank=True, default='')        # B8: 20 → 50
    cantidad_registros = models.IntegerField(default=0)

    class Meta:
        db_table = 'imp_exportaciones_aplicativos'
        ordering = ['-generado_en']

    def __str__(self):
        return f"{self.aplicativo} {self.fecha_desde}→{self.fecha_hasta} [{self.estado}]"


# ─────────────────────────────────────────────────────────────────────────────
# REGÍMENES ESPECIALES (para selectores en SICORE / SIFERE)
# ─────────────────────────────────────────────────────────────────────────────

class ImpRegimenEspecial(models.Model):
    """
    Catálogo de regímenes especiales para SICORE / SIFERE.
    Cargados manualmente o importados desde ARCA.
    """
    TIPO_CHOICES = [
        ('SICORE', 'SICORE'),
        ('SIFERE', 'SIFERE'),
        ('OTRO',   'Otro'),
    ]

    codigo      = models.CharField(max_length=10, primary_key=True)
    descripcion = models.CharField(max_length=100)
    tipo        = models.CharField(max_length=10, choices=TIPO_CHOICES, default='SICORE')
    activo      = models.BooleanField(default=True)

    class Meta:
        db_table = 'imp_regimenes_especiales'
        ordering = ['tipo', 'codigo']

    def __str__(self):
        return f"[{self.tipo}] {self.codigo} — {self.descripcion}"
    
    # ─────────────────────────────────────────────────────────────────────────────
# DISCRIMINACIÓN DE IVA POR ALÍCUOTA — Sprint 2
# ─────────────────────────────────────────────────────────────────────────────

class ImpIVAAlicuotas(models.Model):
    """
    Discriminación de IVA por alícuota para ventas y compras.

    Fuente única de verdad usada por:
      - Libro IVA con columnas por alícuota (10.5 / 21 / 27 / 5 / 2.5 / 0)
      - Libro IVA Digital RG 4597 (archivo posicional REGINFO_CV_*_ALICUOTAS)
      - DDJJ con discriminación por alícuota

    Cómo se puebla:
      - Comprobantes generados por el sistema → trigger en views/ventas.py y
        views/compras.py que hace SUM(v_iva), SUM(total - v_iva) GROUP BY p_iva
        del detalle e inserta una fila por alícuota presente. (Tarea 2)
      - Importación ARCA → lee columnas "IVA 21%", "Neto Grav. IVA 21%", etc.
        del Excel y persiste lo que tenga valor > 0. (Tarea 3)
      - Datos históricos previos a Sprint 2 → comando de management
        `popular_iva_alicuotas` que recorre la base existente. (Tarea 4)

    Reglas:
      - Una fila por (movim, circuito, alicuota). Si una venta tiene 3 items al
        21% y 2 al 10.5%, son 2 filas (no 5).
      - Operaciones exentas (Ventas.exento) NO se guardan acá — van en su campo
        original. Esta tabla es solo para operaciones GRAVADAS.
      - Notas de crédito/débito heredan el circuito de su factura asociada
        (NCA/NDA → Ventas, NCA/NDA en compras → Compras).
    """
    CIRCUITO_CHOICES = [('V', 'Ventas'), ('C', 'Compras')]

    movim        = models.BigIntegerField()
    circuito     = models.CharField(max_length=1, choices=CIRCUITO_CHOICES)
    alicuota     = models.DecimalField(max_digits=5, decimal_places=2,
                       help_text='Porcentaje: 21.00, 10.50, 27.00, 5.00, 2.50, 0.00')
    neto_gravado = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                       help_text='Base imponible para esta alícuota (sin IVA).')
    iva          = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                       help_text='Importe de IVA correspondiente a esta alícuota.')
    creado_en    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'imp_iva_alicuotas'
        unique_together = [('movim', 'circuito', 'alicuota')]
        indexes = [
            models.Index(fields=['circuito', 'movim'], name='iva_alic_circ_mov_idx'),
            models.Index(fields=['circuito', 'alicuota'], name='iva_alic_circ_ali_idx'),
        ]
        ordering = ['circuito', 'movim', 'alicuota']

    def __str__(self):
        return f"[{self.get_circuito_display()}] movim={self.movim} {self.alicuota}% IVA=${self.iva}"