"""
_iva_alicuotas_helper.py — Helper para poblar ImpIVAAlicuotas.

Se usa desde views/ventas.py y views/compras.py al insertar/anular
comprobantes. Centralizado acá para que la lógica viva en un solo lugar.
"""
from decimal import Decimal
from django.db.models import Sum

from ..models import VentasDet, ComprasDet
from ..impositivo_models import ImpIVAAlicuotas


def recalcular_iva_alicuotas(movim: int, circuito: str) -> int:
    """
    Recalcula la discriminación de IVA por alícuota para un comprobante.

    Lee el detalle (ventas_det o compras_det), agrupa por p_iva y persiste
    una fila por alícuota presente en ImpIVAAlicuotas. Idempotente: borra
    las filas previas del mismo (movim, circuito) antes de insertar.

    Args:
        movim:    PK del comprobante en ventas o compras.
        circuito: 'V' o 'C'.

    Returns:
        Cantidad de filas insertadas.

    Notas:
      - Si no hay detalle (caso facturas importadas de ARCA), no inserta nada
        y devuelve 0. La importación ARCA puebla la tabla por su lado leyendo
        las columnas del Excel (Tarea 3).
      - Filas con neto_gravado=0 e iva=0 se descartan (alícuotas vacías no aportan).
      - Se ejecuta DENTRO de la transacción de la venta/compra que lo invoca.
    """
    if circuito not in ('V', 'C'):
        raise ValueError(f"circuito debe ser 'V' o 'C', recibido: {circuito!r}")

    Det = VentasDet if circuito == 'V' else ComprasDet

    # Agrupado por alícuota: total = neto + IVA del item, v_iva = IVA del item.
    # neto_gravado = total - v_iva (lo hacemos en Python para evitar
    # diferencias entre dialectos SQL).
    agregado = (
        Det.objects.filter(movim=movim)
        .values('p_iva')
        .annotate(
            sum_total=Sum('total'),
            sum_iva=Sum('v_iva'),
        )
        .order_by('p_iva')
    )

    # Borra primero (idempotente)
    ImpIVAAlicuotas.objects.filter(movim=movim, circuito=circuito).delete()

    nuevas = []
    for row in agregado:
        alicuota = row['p_iva'] or Decimal('0')
        sum_total = Decimal(str(row['sum_total'] or 0))
        sum_iva   = Decimal(str(row['sum_iva']   or 0))
        neto_gravado = sum_total - sum_iva

        # Saltamos alícuotas sin contenido real
        if sum_iva == 0 and neto_gravado == 0:
            continue

        nuevas.append(ImpIVAAlicuotas(
            movim=movim,
            circuito=circuito,
            alicuota=alicuota,
            neto_gravado=neto_gravado,
            iva=sum_iva,
        ))

    if nuevas:
        ImpIVAAlicuotas.objects.bulk_create(nuevas)
    return len(nuevas)
def persistir_iva_alicuotas_desde_arca(movim: int, circuito: str, fila: dict,
                                        tipo_cambio_pesos: Decimal = None) -> int:
    """
    Persiste filas en ImpIVAAlicuotas leyendo las columnas del Excel ARCA.

    El Excel "Mis Comprobantes Recibidos/Emitidos" tiene 12 columnas relevantes:
       'Neto Grav. IVA 0%',   (sin columna de IVA — siempre 0)
       'IVA 2,5%',  'Neto Grav. IVA 2,5%',
       'IVA 5%',    'Neto Grav. IVA 5%',
       'IVA 10,5%', 'Neto Grav. IVA 10,5%',
       'IVA 21%',   'Neto Grav. IVA 21%',
       'IVA 27%',   'Neto Grav. IVA 27%'.

    Args:
        movim:             PK del comprobante recién creado en ventas/compras.
        circuito:          'V' o 'C'.
        fila:              dict con la fila del Excel (lo que devuelve df.iterrows().to_dict()).
        tipo_cambio_pesos: si el comprobante está en USD, multiplicar por este factor
                           para convertir a pesos (consistente con cómo se guardó la
                           cabecera). None o 1 = no aplica conversión.

    Returns:
        Cantidad de filas persistidas.
    """
    if circuito not in ('V', 'C'):
        raise ValueError(f"circuito debe ser 'V' o 'C', recibido: {circuito!r}")

    factor = Decimal('1') if (tipo_cambio_pesos is None or tipo_cambio_pesos <= 1) \
                          else Decimal(str(tipo_cambio_pesos))

    # Mapeo (alicuota, columna_neto, columna_iva).
    # Para 0%: la columna de IVA no existe (siempre es 0), pero registramos
    # neto_gravado para que aparezca en el libro IVA con su línea de "exento gravado a 0%".
    columnas = [
        (Decimal('0.00'),  'Neto Grav. IVA 0%',    None),
        (Decimal('2.50'),  'Neto Grav. IVA 2,5%',  'IVA 2,5%'),
        (Decimal('5.00'),  'Neto Grav. IVA 5%',    'IVA 5%'),
        (Decimal('10.50'), 'Neto Grav. IVA 10,5%', 'IVA 10,5%'),
        (Decimal('21.00'), 'Neto Grav. IVA 21%',   'IVA 21%'),
        (Decimal('27.00'), 'Neto Grav. IVA 27%',   'IVA 27%'),
    ]

    def _to_dec(v):
        """Convierte cualquier cosa a Decimal, manejando NaN/None."""
        if v is None:
            return Decimal('0')
        s = str(v).strip()
        if not s or s.lower() in ('nan', 'none', ''):
            return Decimal('0')
        try:
            return Decimal(s.replace(',', '.'))
        except Exception:
            return Decimal('0')

    # Borra primero (idempotente) — útil si re-importás el mismo período.
    ImpIVAAlicuotas.objects.filter(movim=movim, circuito=circuito).delete()

    nuevas = []
    for alicuota, col_neto, col_iva in columnas:
        neto = _to_dec(fila.get(col_neto)) * factor
        iva  = _to_dec(fila.get(col_iva)) * factor if col_iva else Decimal('0')
        if neto == 0 and iva == 0:
            continue
        nuevas.append(ImpIVAAlicuotas(
            movim=movim,
            circuito=circuito,
            alicuota=alicuota,
            neto_gravado=neto,
            iva=iva,
        ))

    if nuevas:
        ImpIVAAlicuotas.objects.bulk_create(nuevas)
    return len(nuevas)