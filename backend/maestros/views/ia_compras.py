"""
ia_compras.py — Procesamiento de facturas AFIP con pdfplumber + regex.
Formato probado: facturas digitales AFIP (Monotributo y Responsable Inscripto).
Sin modelos de IA externos — rápido, preciso, sin dependencias pesadas.
"""
import re
import tempfile
import os

from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response


# ── Helpers ───────────────────────────────────────────────────────────────────

def _monto(s: str) -> float:
    """Convierte '369.054,00' o '369054,00' o '369054.00' a float."""
    if not s:
        return 0.0
    s = re.sub(r'[^\d.,]', '', str(s)).strip()
    if ',' in s and '.' in s:
        # Formato AR: punto=miles, coma=decimal → '1.234,56'
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return 0.0


def _fecha(s: str) -> str:
    """Convierte DD/MM/YYYY a YYYY-MM-DD."""
    m = re.search(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', str(s or ''))
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    return ''


def _extraer_texto(pdf_path: str) -> str:
    """Extrae texto de la primera página usando pdfplumber."""
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            return ''
        return pdf.pages[0].extract_text() or ''


# ── Parser principal ──────────────────────────────────────────────────────────

def _parsear(texto: str) -> dict:
    """
    Parsea una factura AFIP a partir del texto extraído por pdfplumber.

    Formato esperado (página 1):
      ORIGINAL / DUPLICADO / TRIPLICADO
      C / A / B / M
      FACTURA / NOTA DE CRÉDITO / NOTA DE DÉBITO
      HD SOLUCIONES GRAFICAS          ← razón social emisor
      COD. 011
      Punto de Venta: 00001 Comp. Nro: 00000346
      Razón Social: FUNES FRANCO GABRIEL Fecha de Emisión: 10/02/2026
      Domicilio Comercial: ... CUIT: 20375173442
      ...
      CUIT: 30716543699 Apellido y Nombre / Razón Social: CROWDFARMING...
      ...
      1 Serigrafía cajas Damia 522,00 unidades 707,00 0,00 0,00 369054,00
      Subtotal: $ 369054,00
      Importe Otros Tributos: $ 0,00
      Importe Total: $ 369054,00
      CAE N°: 86063350554627
      Fecha de Vto. de CAE: 20/02/2026
    """
    lineas = [l.strip() for l in texto.split('\n') if l.strip()]

    d = {
        'tipo_comprob':   '',
        'punto_venta':    '0001',
        'numero':         '',
        'fecha':          '',
        'proveedor_cuit': '',
        'proveedor_razon':'',
        'neto':           0.0,
        'iva_21':         0.0,
        'iva_105':        0.0,
        'percep_iva':     0.0,
        'percep_iibb':    0.0,
        'total':          0.0,
        'cae':            '',
        'cae_vto':        '',
        'condicion_pago': 'CON',
        'items':          [],
        'advertencias':   [],
    }

    # ── Tipo de comprobante ───────────────────────────────────────────────────
    # Formato: "C\nFACTURA" → FC | "A\nFACTURA" → FA | etc.
    tipo_mapa = {
        r'FACTURA': 'F', r'NOTA DE CR[EÉ]DITO': 'NC', r'NOTA DE D[EÉ]BITO': 'ND',
        r'RECIBO': 'R',
    }
    letra_comprob = ''
    tipo_base     = ''
    for i, l in enumerate(lineas):
        if re.match(r'^([ABCM])$', l):
            letra_comprob = l
        for patron, prefijo in tipo_mapa.items():
            if re.search(patron, l, re.I):
                tipo_base = prefijo
                break
        if tipo_base and letra_comprob:
            d['tipo_comprob'] = tipo_base + letra_comprob
            break

    # Fallback: "COD. 011" → FC, "COD. 001" → FA, "COD. 006" → FB
    if not d['tipo_comprob']:
        cod_mapa = {'011': 'FC', '001': 'FA', '006': 'FB', '051': 'FM',
                    '003': 'NCA', '008': 'NCB', '002': 'NDA', '007': 'NDB'}
        for l in lineas:
            m = re.search(r'COD\.\s*(\d{3})', l)
            if m and m.group(1) in cod_mapa:
                d['tipo_comprob'] = cod_mapa[m.group(1)]
                break

    # ── Punto de venta y número ───────────────────────────────────────────────
    # "Punto de Venta: 00001 Comp. Nro: 00000346"
    for l in lineas:
        m = re.search(
            r'Punto\s+de\s+Venta[:\s]+(\d+).*?Comp\.?\s*Nro[:\s]+(\d+)',
            l, re.I
        )
        if m:
            d['punto_venta'] = m.group(1).zfill(4)
            d['numero']      = m.group(2).zfill(8)
            break

    # ── Razón social y CUIT del emisor ────────────────────────────────────────
    # El emisor aparece ANTES de "Punto de Venta:"
    # "Razón Social: FUNES FRANCO GABRIEL Fecha de Emisión: 10/02/2026"
    # "Domicilio Comercial: ... CUIT: 20375173442"
    for l in lineas:
        m = re.search(r'Raz[oó]n\s+Social[:\s]+(.+?)\s+Fecha\s+de\s+Emisi[oó]n', l, re.I)
        if m:
            d['proveedor_razon'] = m.group(1).strip()[:100]
            break
    # Si no lo encontró con ese formato, buscar antes del "Punto de Venta"
    if not d['proveedor_razon']:
        for i, l in enumerate(lineas):
            if re.search(r'Punto\s+de\s+Venta', l, re.I) and i >= 2:
                # La razón social suele estar 2 líneas antes
                candidato = lineas[i-1]
                if not re.search(r'COD\.|^[ABCM]$|FACTURA|ORIGINAL|DUPLICADO', candidato, re.I):
                    d['proveedor_razon'] = candidato[:100]
                break

    # CUIT emisor: "CUIT: 20375173442" (primera aparición)
    for l in lineas:
        m = re.search(r'\bCUIT[:\s]+(\d{11})\b', l)
        if m:
            d['proveedor_cuit'] = m.group(1)
            break
    # También formato con guiones: 20-37517344-2
    if not d['proveedor_cuit']:
        for l in lineas:
            m = re.search(r'\bCUIT[:\s]+(\d{2}-\d{7,8}-\d)\b', l)
            if m:
                d['proveedor_cuit'] = m.group(1).replace('-', '')
                break

    # ── Fecha de emisión ──────────────────────────────────────────────────────
    # "Razón Social: FUNES FRANCO GABRIEL Fecha de Emisión: 10/02/2026"
    for l in lineas:
        m = re.search(r'Fecha\s+de\s+Emisi[oó]n[:\s]+(\d{1,2}/\d{1,2}/\d{4})', l, re.I)
        if m:
            d['fecha'] = _fecha(m.group(1))
            break

    # ── Montos ────────────────────────────────────────────────────────────────
    for l in lineas:
        # Subtotal / Neto gravado
        m = re.search(r'(?:Subtotal|Neto\s+Gravado)[:\s]+\$\s*([\d.,]+)', l, re.I)
        if m and d['neto'] == 0.0:
            d['neto'] = _monto(m.group(1))

        # IVA 21%
        m = re.search(r'I\.?V\.?A\.?\s+21\s*%[:\s]+\$\s*([\d.,]+)', l, re.I)
        if m: d['iva_21'] = _monto(m.group(1))

        # IVA 10.5%
        m = re.search(r'I\.?V\.?A\.?\s+10[,.]?5\s*%[:\s]+\$\s*([\d.,]+)', l, re.I)
        if m: d['iva_105'] = _monto(m.group(1))

        # Percepción IVA
        m = re.search(r'Percep\w*\s+IVA[:\s]+\$\s*([\d.,]+)', l, re.I)
        if m: d['percep_iva'] = _monto(m.group(1))

        # Percepción IIBB
        m = re.search(r'Percep\w*\s+(?:IIBB|Ing\.?\s*Brutos)[:\s]+\$\s*([\d.,]+)', l, re.I)
        if m: d['percep_iibb'] = _monto(m.group(1))

        # Importe Total
        m = re.search(r'Importe\s+Total[:\s]+\$\s*([\d.,]+)', l, re.I)
        if m: d['total'] = _monto(m.group(1))

    # Monotributo: neto = total (sin IVA discriminado)
    if d['neto'] == 0.0 and d['total'] > 0:
        d['neto'] = d['total']
        if d['tipo_comprob'] in ('FC',):
            d['advertencias'].append('Monotributo: neto = total (sin IVA discriminado)')

    # ── CAE ───────────────────────────────────────────────────────────────────
    # "CAE N°: 86063350554627"
    for l in lineas:
        m = re.search(r'CAE\s+N[°º]?[:\s]+(\d{14})', l, re.I)
        if m:
            d['cae'] = m.group(1)
            break

    # "Fecha de Vto. de CAE: 20/02/2026"
    for l in lineas:
        m = re.search(r'Fecha\s+de\s+Vto\.?\s+de\s+CAE[:\s]+(\d{1,2}/\d{1,2}/\d{4})', l, re.I)
        if m:
            d['cae_vto'] = _fecha(m.group(1))
            break

    # ── Condición de pago ─────────────────────────────────────────────────────
    for l in lineas:
        if re.search(r'Contado', l, re.I):
            d['condicion_pago'] = 'CON'
        elif re.search(r'Cuenta\s+Corriente|Cr[eé]dito', l, re.I):
            d['condicion_pago'] = 'CTA'

    # ── Ítems ─────────────────────────────────────────────────────────────────
    # "1 Serigrafía cajas Damia 522,00 unidades 707,00 0,00 0,00 369054,00"
    # Columnas: Código | Descripción | Cantidad | U.Medida | P.Unit | %Bonif | Imp.Bonif | Subtotal
    en_tabla = False
    for l in lineas:
        if re.search(r'Código\s+Producto', l, re.I):
            en_tabla = True
            continue
        if en_tabla and re.search(r'^Subtotal[:\s]', l, re.I):
            break
        if not en_tabla:
            continue

        # Patrón: número | descripción | cantidad | unidad | precio | bonif% | imp.bonif | subtotal
        m = re.match(
            r'^(\d+)\s+'                        # código
            r'(.+?)\s+'                          # descripción
            r'([\d.,]+)\s+'                      # cantidad
            r'\w+\s+'                            # unidad medida
            r'([\d.,]+)\s+'                      # precio unit
            r'[\d.,]+\s+'                        # % bonif
            r'[\d.,]+\s+'                        # imp bonif
            r'([\d.,]+)$',                       # subtotal
            l
        )
        if m:
            d['items'].append({
                'descripcion': m.group(2).strip()[:100],
                'cantidad':    _monto(m.group(3)),
                'precio_unit': _monto(m.group(4)),
                'subtotal':    _monto(m.group(5)),
                'cod_art':     '',
            })

    # ── Confianza ─────────────────────────────────────────────────────────────
    criticos = [d['tipo_comprob'], d['numero'], d['proveedor_cuit'], str(d['total'])]
    vacios   = sum(1 for c in criticos if not c or c in ('0.0', '0'))
    if   vacios == 0: d['confianza'] = 'alta'
    elif vacios == 1:
        d['confianza'] = 'media'
        d['advertencias'].append('Un campo no pudo detectarse — revisá antes de guardar')
    else:
        d['confianza'] = 'baja'
        d['advertencias'].append('Varios campos no detectados — completá manualmente')

    return d


# ── Endpoints ─────────────────────────────────────────────────────────────────

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def ProcesarFacturaPDF(request):
    archivo = request.FILES.get('archivo')
    if not archivo:
        return Response({'status': 'error', 'mensaje': 'No se recibió ningún archivo.'}, status=400)
    if not archivo.name.lower().endswith('.pdf'):
        return Response({'status': 'error', 'mensaje': 'Solo se aceptan archivos PDF.'}, status=400)
    if archivo.size > 20 * 1024 * 1024:
        return Response({'status': 'error', 'mensaje': 'El archivo supera los 20 MB.'}, status=400)

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        for chunk in archivo.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        texto = _extraer_texto(tmp_path)
        if not texto or len(texto.strip()) < 30:
            return Response({
                'status':  'error',
                'mensaje': 'No se pudo extraer texto. El PDF puede ser una imagen escaneada.',
            }, status=422)

        datos = _parsear(texto)
        datos['texto_extraido'] = texto[:2000]
        datos['nombre_archivo'] = archivo.name
        datos['motor']          = 'pdfplumber'

        return Response({
            'status':  'success',
            'datos':   datos,
            'mensaje': f'Factura procesada — confianza: {datos["confianza"]}',
        })

    except Exception as e:
        return Response({
            'status':  'error',
            'mensaje': f'Error al procesar el PDF: {str(e)}',
        }, status=500)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@api_view(['POST'])
def ConfirmarFactura(request):
    d = request.data
    errores = []
    if not d.get('tipo_comprob'):    errores.append('Tipo de comprobante requerido.')
    if not d.get('proveedor_cuit'):  errores.append('CUIT del proveedor requerido.')
    if not d.get('numero'):          errores.append('Número de comprobante requerido.')
    if not d.get('fecha'):           errores.append('Fecha requerida.')
    if float(d.get('total', 0)) <= 0: errores.append('El total debe ser mayor a cero.')
    if errores:
        return Response({'status': 'error', 'mensaje': ' | '.join(errores)}, status=400)

    items = d.get('items', [])
    payload = {
        'Proveedor_Cuit':           d.get('proveedor_cuit', ''),
        'Proveedor_RazonSocial':    d.get('proveedor_razon', ''),
        'Comprobante_Tipo':         d.get('tipo_comprob', ''),
        'Comprobante_PtoVenta':     str(d.get('punto_venta', '0001')).zfill(4),
        'Comprobante_Numero':       str(d.get('numero', '')).zfill(8),
        'Comprobante_Fecha':        d.get('fecha', ''),
        'Comprobante_Neto':         float(d.get('neto', 0)),
        'Comprobante_IVA21':        float(d.get('iva_21', 0)),
        'Comprobante_IVA105':       float(d.get('iva_105', 0)),
        'Comprobante_PercepIVA':    float(d.get('percep_iva', 0)),
        'Comprobante_PercepIIBB':   float(d.get('percep_iibb', 0)),
        'Comprobante_ImporteTotal': float(d.get('total', 0)),
        'Comprobante_CondPago':     d.get('condicion_pago', 'CON'),
        'Comprobante_CAE':          d.get('cae', ''),
        'Comprobante_CAEVto':       d.get('cae_vto', ''),
        'Comprobante_Observac':     f"PDF · {d.get('nombre_archivo', '')}",
        'cajero':                   d.get('cajero', 1),
        'nro_caja':                 d.get('nro_caja', 1),
        'usuario':                  d.get('usuario', 'admin'),
        'Comprobante_Items': [
            {
                'Item_DescripArticulo': it.get('descripcion', ''),
                'Item_CodigoArticulo':  it.get('cod_art', ''),
                'Item_CantidadUM1':     float(it.get('cantidad', 1)),
                'Item_PrecioUnitario':  float(it.get('precio_unit', 0)),
                'Item_ImporteTotal':    float(it.get('subtotal', 0)),
            }
            for it in items
        ],
    }

    from .compras import IngresarComprobanteComprasJSON
    from rest_framework.test import APIRequestFactory
    req  = APIRequestFactory().post('/api/IngresarComprobanteComprasJSON/', payload, format='json')
    resp = IngresarComprobanteComprasJSON(req)

    if resp.status_code in (200, 201):
        return Response({
            'status':  'success',
            'movim':   resp.data.get('movim'),
            'mensaje': f'Factura #{d.get("numero")} guardada correctamente.',
        })
    return Response({
        'status':  'error',
        'mensaje': f'Error al guardar: {resp.data}',
    }, status=400)