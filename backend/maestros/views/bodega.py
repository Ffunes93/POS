"""
views/bodega.py — Vistas del módulo Bodega / Vitivinícola
MEJORAS APLICADAS:
  1. _validar_vs_ficha: compara análisis vs ficha técnica (alertas_ficha)
  2. BodAnalisisView.post: retorna alertas_ficha
  3. BodOperacionesEnologicasView.post: auto-imputa costo insumo a BodCostoLote
  4. BodNoConformidadesView.post: acción cambiar_estado
  5. BodLibroBodegaView: libro de bodega INV por varietal
"""
from django.db import transaction
from django.db.models import Sum, Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..bodega_models import (
    BodVarietal, BodInsumoEnologico,
    BodParcela, BodMaduracion,
    BodTicketBascula,
    BodRecipiente,
    BodLoteGranel, BodComposicionLote, BodMovimientoGranel,
    BodOperacionEnologica,
    BodAnalisis,
    BodBarrica, BodAsignacionBarrica,
    BodOrdenEmbotellado,
)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _ok(data=None, msg='OK'):
    return Response({'ok': True, 'msg': msg, 'data': data or {}})

def _err(msg, code=400):
    return Response({'ok': False, 'msg': msg}, status=code)

def _varietal_dict(v):
    return {'codigo': v.codigo, 'nombre': v.nombre, 'color': v.color}

def _parcela_dict(p):
    return {
        'id': p.pk, 'nombre': p.nombre, 'tipo': p.tipo,
        'varietal': p.varietal_id, 'varietal_nombre': p.varietal.nombre,
        'superficie_ha': float(p.superficie_ha),
        'anio_plantacion': p.anio_plantacion,
        'finca': p.finca, 'zona': p.zona, 'cod_prov': p.cod_prov,
    }

def _recipiente_dict(r):
    return {
        'id': r.pk, 'codigo': r.codigo, 'nombre': r.nombre,
        'tipo': r.tipo, 'tipo_display': r.get_tipo_display(),
        'capacidad_litros': float(r.capacidad_litros),
        'sector': r.sector, 'fila': r.fila, 'posicion': r.posicion,
        'estado': r.estado, 'estado_display': r.get_estado_display(),
    }

def _lote_dict(l):
    return {
        'id': l.pk, 'codigo': l.codigo, 'campana': l.campaña,
        'varietal': l.varietal_ppal_id, 'varietal_nombre': l.varietal_ppal.nombre,
        'tipo_vino': l.tipo_vino, 'tipo_vino_display': l.get_tipo_vino_display(),
        'descripcion': l.descripcion,
        'fecha_inicio': l.fecha_inicio.isoformat(),
        'estado': l.estado, 'estado_display': l.get_estado_display(),
        'litros_iniciales': float(l.litros_iniciales),
        'litros_actuales': float(l.litros_actuales),
        'merma_total': float(l.merma_total),
        'recipiente_id': l.recipiente_id,
        'recipiente_codigo': l.recipiente.codigo if l.recipiente else None,
        'grado_alcohol_obj': float(l.grado_alcohol_obj) if l.grado_alcohol_obj else None,
    }

def _ticket_dict(t):
    return {
        'id': t.numero, 'campana': t.campaña, 'fecha': t.fecha.isoformat(),
        'parcela_id': t.parcela_id,
        'parcela_nombre': t.parcela.nombre if t.parcela else '',
        'varietal': t.varietal_id, 'varietal_nombre': t.varietal.nombre,
        'patente_camion': t.patente_camion,
        'peso_bruto': float(t.peso_bruto), 'tara': float(t.tara),
        'peso_neto': float(t.peso_neto),
        'brix_entrada': float(t.brix_entrada) if t.brix_entrada else None,
        'ph_entrada': float(t.ph_entrada) if t.ph_entrada else None,
        'estado': t.estado, 'estado_display': t.get_estado_display(),
        'cod_prov': t.cod_prov, 'nombre_prov': t.nombre_prov,
        'precio_kg': float(t.precio_kg) if t.precio_kg else None,
        'lote_destino_id': t.lote_destino_id,
        'lote_destino_codigo': t.lote_destino.codigo if t.lote_destino else None,
    }

def _analisis_dict(a):
    return {
        'id': a.pk, 'lote_id': a.lote_id, 'lote_codigo': a.lote.codigo,
        'fecha': a.fecha.isoformat(), 'origen': a.origen, 'laboratorio': a.laboratorio,
        'grado_alcohol': float(a.grado_alcohol) if a.grado_alcohol else None,
        'acidez_total': float(a.acidez_total) if a.acidez_total else None,
        'acidez_volatil': float(a.acidez_volatil) if a.acidez_volatil else None,
        'ph': float(a.ph) if a.ph else None,
        'azucar_residual': float(a.azucar_residual) if a.azucar_residual else None,
        'so2_libre': float(a.so2_libre) if a.so2_libre else None,
        'so2_total': float(a.so2_total) if a.so2_total else None,
        'turbidez_ntu': float(a.turbidez_ntu) if a.turbidez_ntu else None,
        'aprobado': a.aprobado, 'observaciones': a.observaciones,
    }

def _barrica_dict(b):
    return {
        'id': b.pk, 'numero': b.numero,
        'capacidad_litros': float(b.capacidad_litros),
        'madera': b.madera, 'madera_display': b.get_madera_display(),
        'tostado': b.tostado, 'tostado_display': b.get_tostado_display(),
        'tonelero': b.tonelero, 'anio_compra': b.anio_compra,
        'cantidad_usos': b.cantidad_usos, 'vida_util_usos': b.vida_util_usos,
        'porcentaje_vida_util': b.porcentaje_vida_util,
        'estado': b.estado, 'estado_display': b.get_estado_display(),
        'sector': b.sector, 'fila': b.fila, 'posicion': b.posicion,
    }

def _orden_emb_dict(o):
    return {
        'id': o.numero, 'lote_id': o.lote_id, 'lote_codigo': o.lote.codigo,
        'fecha_plan': o.fecha_plan.isoformat(),
        'fecha_real': o.fecha_real.isoformat() if o.fecha_real else None,
        'formato': o.formato, 'formato_display': o.get_formato_display(),
        'botellas_plan': o.botellas_plan, 'botellas_real': o.botellas_real,
        'botellas_merma': o.botellas_merma,
        'litros_planificados': o.litros_planificados,
        'litros_consumidos': float(o.litros_consumidos) if o.litros_consumidos else None,
        'cod_art_pt': o.cod_art_pt, 'nro_rnoe': o.nro_rnoe,
        'estado': o.estado, 'estado_display': o.get_estado_display(),
        'observaciones': o.observaciones,
    }


# =============================================================================
# MEJORA 1: Validador de analisis vs ficha tecnica
# =============================================================================

def _validar_vs_ficha(analisis, lote):
    """
    Compara los valores del analisis contra los rangos de la ficha tecnica
    activa para el varietal + tipo_vino del lote.
    Retorna lista de alertas con: param, etiqueta, valor, limite, tipo, unidad.
    """
    from ..bodega_models import BodFichaProducto
    try:
        ficha = BodFichaProducto.objects.filter(
            varietal_id=lote.varietal_ppal_id,
            tipo_vino=lote.tipo_vino,
            activa=True,
        ).first()
    except Exception:
        return []
    if not ficha:
        return []
    CHECKS = [
        ('grado_alcohol',   'Grado alcoholico',   ficha.alcohol_min,      ficha.alcohol_max,      '% v/v'),
        ('acidez_total',    'Acidez total',        ficha.acidez_total_min, ficha.acidez_total_max, 'g/L'),
        ('ph',              'pH',                  ficha.ph_min,           ficha.ph_max,           None),
        ('azucar_residual', 'Azucar residual',     None,                   ficha.azucar_max,       'g/L'),
        ('so2_libre',       'SO2 libre',           None,                   ficha.so2_libre_max,    'mg/L'),
        ('so2_total',       'SO2 total',           None,                   ficha.so2_total_max,    'mg/L'),
    ]
    alertas = []
    for campo, etiqueta, min_v, max_v, unidad in CHECKS:
        val = getattr(analisis, campo, None)
        if val is None:
            continue
        val = float(val)
        if min_v and val < float(min_v):
            alertas.append({'param': campo, 'etiqueta': etiqueta, 'valor': val, 'limite': float(min_v), 'tipo': 'bajo', 'unidad': unidad})
        elif max_v and val > float(max_v):
            alertas.append({'param': campo, 'etiqueta': etiqueta, 'valor': val, 'limite': float(max_v), 'tipo': 'alto', 'unidad': unidad})
    return alertas



# =============================================================================
# VARIETALES
# =============================================================================
class BodVarietalesView(APIView):
    def get(self, request):
        qs = BodVarietal.objects.filter(activo=True)
        return _ok([_varietal_dict(v) for v in qs])
    def post(self, request):
        d = request.data
        try:
            v, _ = BodVarietal.objects.update_or_create(
                codigo=d['codigo'],
                defaults={'nombre': d['nombre'], 'color': d.get('color','T'), 'activo': True}
            )
            return _ok(_varietal_dict(v), 'Varietal guardado')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# PARCELAS
# =============================================================================
class BodParcelasView(APIView):
    def get(self, request):
        qs = BodParcela.objects.select_related('varietal').filter(activa=True)
        return _ok([_parcela_dict(p) for p in qs])
    def post(self, request):
        d = request.data
        try:
            varietal = BodVarietal.objects.get(codigo=d['varietal'])
        except BodVarietal.DoesNotExist:
            return _err('Varietal no encontrado')
        try:
            defaults = {
                'nombre': d['nombre'], 'tipo': d.get('tipo','P'), 'varietal': varietal,
                'superficie_ha': d['superficie_ha'], 'anio_plantacion': d.get('anio_plantacion'),
                'portainjerto': d.get('portainjerto',''), 'finca': d.get('finca',''),
                'zona': d.get('zona',''), 'latitud': d.get('latitud'), 'longitud': d.get('longitud'),
                'altitud_msnm': d.get('altitud_msnm'), 'cod_prov': d.get('cod_prov'),
                'observaciones': d.get('observaciones',''),
            }
            if d.get('id'):
                BodParcela.objects.filter(pk=d['id']).update(**defaults)
                parcela = BodParcela.objects.select_related('varietal').get(pk=d['id'])
            else:
                parcela = BodParcela.objects.create(**defaults)
            return _ok(_parcela_dict(parcela), 'Parcela guardada')
        except Exception as e:
            return _err(str(e))

class BodMaduracionView(APIView):
    def get(self, request):
        qs = BodMaduracion.objects.select_related('parcela__varietal')
        if request.query_params.get('parcela_id'):
            qs = qs.filter(parcela_id=request.query_params['parcela_id'])
        if request.query_params.get('campaña'):
            qs = qs.filter(campaña=request.query_params['campaña'])
        data = [{'id':m.pk,'parcela_id':m.parcela_id,'parcela_nombre':m.parcela.nombre,
                 'varietal':m.parcela.varietal_id,'campaña':m.campaña,'fecha':m.fecha.isoformat(),
                 'brix':float(m.brix) if m.brix else None,'ph':float(m.ph) if m.ph else None,
                 'acidez_total':float(m.acidez_total) if m.acidez_total else None,
                 'estado_sanitario':m.estado_sanitario} for m in qs[:200]]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            m = BodMaduracion.objects.create(
                parcela_id=d['parcela_id'], campaña=d['campaña'], fecha=d['fecha'],
                brix=d.get('brix'), ph=d.get('ph'), acidez_total=d.get('acidez_total'),
                estado_sanitario=d.get('estado_sanitario',''), observaciones=d.get('observaciones',''),
                usuario=d.get('usuario',''))
            return _ok({'id':m.pk}, 'Maduracion registrada')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# TICKETS DE BASCULA
# =============================================================================
class BodTicketsBasculaView(APIView):
    def get(self, request):
        qs = BodTicketBascula.objects.select_related('parcela','varietal','lote_destino')
        if request.query_params.get('campaña'):
            qs = qs.filter(campaña=request.query_params['campaña'])
        if request.query_params.get('estado'):
            qs = qs.filter(estado=request.query_params['estado'])
        return _ok([_ticket_dict(t) for t in qs[:500]])
    def post(self, request):
        d = request.data
        try:
            varietal = BodVarietal.objects.get(codigo=d['varietal'])
        except BodVarietal.DoesNotExist:
            return _err('Varietal no encontrado')
        try:
            t = BodTicketBascula.objects.create(
                campaña=d['campaña'], fecha=d['fecha'], parcela_id=d.get('parcela_id'),
                varietal=varietal, patente_camion=d.get('patente_camion',''),
                peso_bruto=d['peso_bruto'], tara=d.get('tara',0),
                brix_entrada=d.get('brix_entrada'), ph_entrada=d.get('ph_entrada'),
                acidez_entrada=d.get('acidez_entrada'), estado_sanitario=d.get('estado_sanitario',''),
                cod_prov=d.get('cod_prov'), nombre_prov=d.get('nombre_prov',''),
                precio_kg=d.get('precio_kg'), observaciones=d.get('observaciones',''),
                usuario=d.get('usuario',''))
            return _ok(_ticket_dict(t), f'Ticket #{t.numero} — {t.peso_neto} kg')
        except Exception as e:
            return _err(str(e))

class BodAsignarTicketLoteView(APIView):
    def post(self, request):
        d = request.data
        try:
            with transaction.atomic():
                ticket = BodTicketBascula.objects.select_for_update().get(pk=d['ticket_id'])
                lote   = BodLoteGranel.objects.select_for_update().get(pk=d['lote_id'])
                if ticket.estado == 'LI':
                    return _err('El ticket ya fue liquidado')
                litros = float(ticket.peso_neto) * 0.70
                ticket.lote_destino = lote; ticket.estado = 'AS'; ticket.save()
                lote.litros_actuales = (lote.litros_actuales or 0) + litros
                lote.save(update_fields=['litros_actuales'])
                return _ok({'litros_sumados': round(litros,2)}, f'Ticket asignado a {lote.codigo}')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# RECIPIENTES
# =============================================================================
class BodRecipientesView(APIView):
    def get(self, request):
        qs = BodRecipiente.objects.filter(activo=True)
        if request.query_params.get('sector'):
            qs = qs.filter(sector=request.query_params['sector'])
        return _ok([_recipiente_dict(r) for r in qs])
    def post(self, request):
        d = request.data
        try:
            defaults = {
                'nombre': d['nombre'], 'tipo': d.get('tipo','TA'),
                'capacidad_litros': d['capacidad_litros'], 'sector': d.get('sector',''),
                'fila': d.get('fila'), 'posicion': d.get('posicion'),
                'estado': d.get('estado','LI'), 'observaciones': d.get('observaciones',''),
            }
            if d.get('id'):
                BodRecipiente.objects.filter(pk=d['id']).update(**defaults)
                r = BodRecipiente.objects.get(pk=d['id'])
            else:
                defaults['codigo'] = d['codigo']
                r = BodRecipiente.objects.create(**defaults)
            return _ok(_recipiente_dict(r), 'Recipiente guardado')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# LOTES DE GRANEL
# =============================================================================
class BodLotesGranelView(APIView):
    def get(self, request):
        qs = BodLoteGranel.objects.select_related('varietal_ppal','recipiente')
        if request.query_params.get('campaña'):
            qs = qs.filter(campaña=request.query_params['campaña'])
        if request.query_params.get('estado'):
            qs = qs.filter(estado=request.query_params['estado'])
        return _ok([_lote_dict(l) for l in qs])
    def post(self, request):
        d = request.data
        try:
            varietal = BodVarietal.objects.get(codigo=d['varietal'])
        except BodVarietal.DoesNotExist:
            return _err('Varietal no encontrado')
        try:
            defaults = {
                'campaña': d['campaña'], 'varietal_ppal': varietal,
                'tipo_vino': d.get('tipo_vino','TI'), 'descripcion': d.get('descripcion',''),
                'fecha_inicio': d['fecha_inicio'], 'estado': d.get('estado','EB'),
                'litros_iniciales': d.get('litros_iniciales',0),
                'litros_actuales': d.get('litros_actuales', d.get('litros_iniciales',0)),
                'recipiente_id': d.get('recipiente_id'),
                'grado_alcohol_obj': d.get('grado_alcohol_obj'),
                'usuario': d.get('usuario',''), 'observaciones': d.get('observaciones',''),
            }
            if d.get('id'):
                BodLoteGranel.objects.filter(pk=d['id']).update(**defaults)
                lote = BodLoteGranel.objects.select_related('varietal_ppal','recipiente').get(pk=d['id'])
            else:
                defaults['codigo'] = d['codigo']
                lote = BodLoteGranel.objects.create(**defaults)
            return _ok(_lote_dict(lote), 'Lote guardado')
        except Exception as e:
            return _err(str(e))

class BodMovimientosGranelView(APIView):
    def get(self, request):
        lote_id = request.query_params.get('lote_id')
        if not lote_id:
            return _err('Se requiere lote_id')
        qs = BodMovimientoGranel.objects.filter(lote_id=lote_id).select_related('recipiente_origen','recipiente_destino')
        data = [{'id':m.pk,'tipo':m.tipo,'tipo_display':m.get_tipo_display(),
                 'fecha':m.fecha.isoformat(),'litros':float(m.litros),
                 'recipiente_origen':m.recipiente_origen.codigo if m.recipiente_origen else None,
                 'recipiente_destino':m.recipiente_destino.codigo if m.recipiente_destino else None,
                 'descripcion':m.descripcion,'usuario':m.usuario} for m in qs[:200]]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            with transaction.atomic():
                lote = BodLoteGranel.objects.select_for_update().get(pk=d['lote_id'])
                m = BodMovimientoGranel.objects.create(
                    lote=lote, tipo=d['tipo'], fecha=d['fecha'], litros=d['litros'],
                    recipiente_origen_id=d.get('recipiente_origen_id'),
                    recipiente_destino_id=d.get('recipiente_destino_id'),
                    temperatura=d.get('temperatura'), descripcion=d.get('descripcion',''),
                    usuario=d.get('usuario',''))
                if d['tipo'] in ('IN','TR'):
                    lote.litros_actuales = (lote.litros_actuales or 0) + float(d['litros'])
                elif d['tipo'] in ('EG','ME','VE'):
                    lote.litros_actuales = max(0,(lote.litros_actuales or 0) - float(d['litros']))
                lote.save(update_fields=['litros_actuales'])
                if m.recipiente_destino:
                    BodRecipiente.objects.filter(pk=m.recipiente_destino_id).update(estado='OC')
                    lote.recipiente_id = m.recipiente_destino_id
                    lote.save(update_fields=['recipiente_id'])
                return _ok({'id':m.pk}, 'Movimiento registrado')
        except BodLoteGranel.DoesNotExist:
            return _err('Lote no encontrado')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# MEJORA 2: Operaciones enologicas con auto-imputacion de costos
# =============================================================================
class BodOperacionesEnologicasView(APIView):
    def get(self, request):
        qs = BodOperacionEnologica.objects.select_related('insumo')
        if request.query_params.get('lote_id'):
            qs = qs.filter(lote_id=request.query_params['lote_id'])
        data = [{'id':op.pk,'lote_id':op.lote_id,
                 'tipo':op.tipo,'tipo_display':op.get_tipo_display(),
                 'fecha':op.fecha.isoformat(),'descripcion':op.descripcion,
                 'insumo_id':op.insumo_id,
                 'insumo_nombre':op.insumo.nombre if op.insumo else None,
                 'cantidad_insumo':float(op.cantidad_insumo) if op.cantidad_insumo else None,
                 'unidad_insumo':op.unidad_insumo,'lote_insumo_prov':op.lote_insumo_prov,
                 'temperatura':float(op.temperatura) if op.temperatura else None,
                 'densidad':float(op.densidad) if op.densidad else None,
                 'grado_real':float(op.grado_real) if op.grado_real else None,
                 'resultado':op.resultado,'usuario':op.usuario} for op in qs[:200]]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            op = BodOperacionEnologica.objects.create(
                lote_id=d['lote_id'], tipo=d['tipo'], fecha=d['fecha'],
                descripcion=d.get('descripcion',''), insumo_id=d.get('insumo_id'),
                cantidad_insumo=d.get('cantidad_insumo'), unidad_insumo=d.get('unidad_insumo',''),
                lote_insumo_prov=d.get('lote_insumo_prov',''),
                temperatura=d.get('temperatura'), densidad=d.get('densidad'),
                grado_real=d.get('grado_real'), resultado=d.get('resultado',''),
                usuario=d.get('usuario',''))
            # Auto-imputar costo de insumo (no-blocking)
            costo_imputado = 0.0
            if op.insumo_id and op.cantidad_insumo:
                try:
                    from ..bodega_models import BodCostoLote, BodCostoDetalle
                    from ..models import Articulos
                    from datetime import date as _date
                    art = Articulos.objects.filter(cod_art=op.insumo.cod_art).first()
                    precio = float(art.costo_ult or art.costo_pond or 0) if art else 0
                    if precio > 0:
                        cl, _ = BodCostoLote.objects.get_or_create(lote_id=op.lote_id)
                        fecha_det = op.fecha.date() if hasattr(op.fecha,'date') else _date.today()
                        BodCostoDetalle.objects.create(
                            costo_lote=cl, fecha=fecha_det, categoria='INS',
                            descripcion=f'{op.insumo.nombre} — {op.get_tipo_display()}',
                            cantidad=op.cantidad_insumo, unidad=op.unidad_insumo or op.insumo.unidad,
                            precio_unit=precio, usuario=op.usuario or '')
                        cl.costo_insumos_enologicos = float(cl.costo_insumos_enologicos) + precio*float(op.cantidad_insumo)
                        cl.recalcular(); cl.save()
                        costo_imputado = round(precio * float(op.cantidad_insumo), 2)
                except Exception:
                    pass
            extra = f' — costo ${costo_imputado:,.2f} imputado' if costo_imputado else ''
            return _ok({'id':op.pk,'costo_imputado':costo_imputado}, f'Operacion registrada{extra}')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# MEJORA 3: Analisis con validacion vs ficha tecnica
# =============================================================================
class BodAnalisisView(APIView):
    def get(self, request):
        qs = BodAnalisis.objects.select_related('lote')
        if request.query_params.get('lote_id'):
            qs = qs.filter(lote_id=request.query_params['lote_id'])
        return _ok([_analisis_dict(a) for a in qs[:200]])
    def post(self, request):
        d = request.data
        try:
            campos = dict(
                fecha=d.get('fecha'), origen=d.get('origen','INT'), laboratorio=d.get('laboratorio',''),
                grado_alcohol=d.get('grado_alcohol'), acidez_total=d.get('acidez_total'),
                acidez_volatil=d.get('acidez_volatil'), ph=d.get('ph'),
                azucar_residual=d.get('azucar_residual'), so2_libre=d.get('so2_libre'),
                so2_total=d.get('so2_total'), turbidez_ntu=d.get('turbidez_ntu'),
                aprobado=d.get('aprobado'), observaciones=d.get('observaciones',''))
            if d.get('id'):
                BodAnalisis.objects.filter(pk=d['id']).update(**campos)
                a = BodAnalisis.objects.select_related('lote').get(pk=d['id'])
            else:
                campos['lote_id'] = d['lote_id']
                campos['usuario'] = d.get('usuario','')
                a = BodAnalisis.objects.create(**campos)
            # Validar vs ficha tecnica
            alertas_ficha = _validar_vs_ficha(a, a.lote)
            data = _analisis_dict(a)
            data['alertas_ficha'] = alertas_ficha
            sufijo = f' — \u26a0\ufe0f {len(alertas_ficha)} parametro(s) fuera de spec' if alertas_ficha else ''
            return _ok(data, f'Analisis guardado{sufijo}')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# BARRICAS
# =============================================================================
class BodBarricasView(APIView):
    def get(self, request):
        qs = BodBarrica.objects.filter(activa=True)
        if request.query_params.get('estado'):
            qs = qs.filter(estado=request.query_params['estado'])
        return _ok([_barrica_dict(b) for b in qs])
    def post(self, request):
        d = request.data
        try:
            defaults = {
                'capacidad_litros':d.get('capacidad_litros',225),'madera':d.get('madera','FRA'),
                'tostado':d.get('tostado','M'),'tonelero':d.get('tonelero',''),
                'anio_compra':d.get('anio_compra'),'vida_util_usos':d.get('vida_util_usos',4),
                'costo_compra':d.get('costo_compra'),'estado':d.get('estado','LI'),
                'sector':d.get('sector',''),'fila':d.get('fila'),'posicion':d.get('posicion'),
                'observaciones':d.get('observaciones',''),
            }
            if d.get('id'):
                BodBarrica.objects.filter(pk=d['id']).update(**defaults)
                b = BodBarrica.objects.get(pk=d['id'])
            else:
                defaults['numero'] = d['numero']
                b = BodBarrica.objects.create(**defaults)
            return _ok(_barrica_dict(b), 'Barrica guardada')
        except Exception as e:
            return _err(str(e))

class BodAsignacionBarricasView(APIView):
    def get(self, request):
        qs = BodAsignacionBarrica.objects.select_related('barrica','lote')
        if request.query_params.get('barrica_id'):
            qs = qs.filter(barrica_id=request.query_params['barrica_id'])
        if request.query_params.get('lote_id'):
            qs = qs.filter(lote_id=request.query_params['lote_id'])
        data = [{'id':a.pk,'barrica_id':a.barrica_id,'barrica_numero':a.barrica.numero,
                 'lote_id':a.lote_id,'lote_codigo':a.lote.codigo,
                 'fecha_entrada':a.fecha_entrada.isoformat(),
                 'fecha_salida':a.fecha_salida.isoformat() if a.fecha_salida else None,
                 'litros_entrada':float(a.litros_entrada),
                 'litros_salida':float(a.litros_salida) if a.litros_salida else None,
                 'litros_relleno':float(a.litros_relleno),
                 'estado':a.estado,'estado_display':a.get_estado_display()} for a in qs[:200]]
        return _ok(data)
    def post(self, request):
        d = request.data
        accion = d.get('accion','asignar')
        try:
            with transaction.atomic():
                if accion == 'asignar':
                    barrica = BodBarrica.objects.select_for_update().get(pk=d['barrica_id'])
                    if barrica.estado == 'OC':
                        return _err(f'Barrica #{barrica.numero} ya esta ocupada')
                    a = BodAsignacionBarrica.objects.create(
                        barrica=barrica, lote_id=d['lote_id'],
                        fecha_entrada=d['fecha_entrada'], litros_entrada=d['litros_entrada'], estado='OC')
                    barrica.estado='OC'; barrica.cantidad_usos+=1
                    barrica.save(update_fields=['estado','cantidad_usos'])
                    return _ok({'id':a.pk}, f'Barrica asignada a lote')
                elif accion == 'vaciar':
                    a = BodAsignacionBarrica.objects.select_for_update().get(pk=d['asignacion_id'])
                    a.fecha_salida=d['fecha_salida']; a.litros_salida=d.get('litros_salida'); a.estado='VA'; a.save()
                    BodBarrica.objects.filter(pk=a.barrica_id).update(estado='LI')
                    return _ok({}, 'Barrica vaciada')
                elif accion == 'relleno':
                    a = BodAsignacionBarrica.objects.select_for_update().get(pk=d['asignacion_id'])
                    a.litros_relleno = (a.litros_relleno or 0) + float(d['litros'])
                    a.save(update_fields=['litros_relleno'])
                    return _ok({}, f'Relleno registrado')
                return _err('Accion desconocida')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# ORDENES DE EMBOTELLADO
# =============================================================================
class BodOrdenesEmbotelladoView(APIView):
    def get(self, request):
        qs = BodOrdenEmbotellado.objects.select_related('lote')
        if request.query_params.get('lote_id'):
            qs = qs.filter(lote_id=request.query_params['lote_id'])
        if request.query_params.get('estado'):
            qs = qs.filter(estado=request.query_params['estado'])
        return _ok([_orden_emb_dict(o) for o in qs])
    def post(self, request):
        d = request.data
        try:
            defaults = dict(
                lote_id=d['lote_id'], fecha_plan=d['fecha_plan'], formato=d.get('formato','750'),
                formato_desc=d.get('formato_desc',''), botellas_plan=d['botellas_plan'],
                cod_botella=d.get('cod_botella',''), cod_corcho=d.get('cod_corcho',''),
                cod_etiqueta=d.get('cod_etiqueta',''), cod_capsula=d.get('cod_capsula',''),
                cod_caja=d.get('cod_caja',''), cod_art_pt=d.get('cod_art_pt',''),
                nro_rnoe=d.get('nro_rnoe',''), estado=d.get('estado','PL'),
                observaciones=d.get('observaciones',''), usuario=d.get('usuario',''))
            if d.get('id'):
                BodOrdenEmbotellado.objects.filter(pk=d['id']).update(**defaults)
                o = BodOrdenEmbotellado.objects.select_related('lote').get(pk=d['id'])
            else:
                o = BodOrdenEmbotellado.objects.create(**defaults)
            return _ok(_orden_emb_dict(o), f'Orden #{o.numero} guardada')
        except Exception as e:
            return _err(str(e))

class BodConfirmarEmbotelladoView(APIView):
    def post(self, request):
        d = request.data
        try:
            with transaction.atomic():
                orden = BodOrdenEmbotellado.objects.select_for_update().get(pk=d['orden_id'])
                if orden.estado == 'CO': return _err('La orden ya fue completada')
                if orden.estado == 'AN': return _err('La orden esta anulada')
                factor = {'375':0.375,'750':0.750,'1500':1.5,'3000':3.0}
                litros = round(float(d['botellas_real']) * factor.get(orden.formato,0.750), 2)
                lote = BodLoteGranel.objects.select_for_update().get(pk=orden.lote_id)
                if litros > float(lote.litros_actuales):
                    return _err(f'Litros insuficientes: necesitas {litros} L, disponible {lote.litros_actuales} L')
                lote.litros_actuales = max(0, float(lote.litros_actuales) - litros)
                lote.estado = 'EM' if lote.litros_actuales < 1 else 'EP'
                lote.save(update_fields=['litros_actuales','estado'])
                orden.botellas_real=d['botellas_real']; orden.botellas_merma=d.get('botellas_merma',0)
                orden.litros_consumidos=litros; orden.fecha_real=d.get('fecha_real'); orden.estado='CO'; orden.save()
                return _ok({'litros_consumidos':litros,'litros_restantes':float(lote.litros_actuales)},
                           f'Embotellado confirmado — {d["botellas_real"]} botellas')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# DASHBOARD
# =============================================================================
class BodDashboardView(APIView):
    def get(self, request):
        campaña = request.query_params.get('campaña')
        lotes_qs = BodLoteGranel.objects.all()
        tickets_qs = BodTicketBascula.objects.all()
        if campaña:
            lotes_qs = lotes_qs.filter(campaña=campaña)
            tickets_qs = tickets_qs.filter(campaña=campaña)
        return _ok({
            'kg_uva_recibidos': float(tickets_qs.aggregate(t=Sum('peso_neto'))['t'] or 0),
            'litros_en_stock': float(lotes_qs.aggregate(t=Sum('litros_actuales'))['t'] or 0),
            'lotes_por_estado': list(lotes_qs.values('estado').annotate(cant=Count('id'))),
            'recipientes': {
                'libres': BodRecipiente.objects.filter(estado='LI',activo=True).count(),
                'ocupados': BodRecipiente.objects.filter(estado='OC',activo=True).count()},
            'barricas': {
                'libres': BodBarrica.objects.filter(estado='LI',activa=True).count(),
                'ocupadas': BodBarrica.objects.filter(estado='OC',activa=True).count()},
            'ordenes_embotellado_pendientes': BodOrdenEmbotellado.objects.filter(estado='PL').count(),
            'tickets_bascula_pendientes': BodTicketBascula.objects.filter(estado='PE').count(),
        })

# =============================================================================
# INSUMOS
# =============================================================================
class BodInsumosView(APIView):
    def get(self, request):
        qs = BodInsumoEnologico.objects.filter(activo=True)
        data = [{'id':i.pk,'cod_art':i.cod_art,'nombre':i.nombre,
                 'tipo':i.tipo,'tipo_display':i.get_tipo_display(),'unidad':i.unidad,
                 'dosis_max_gl':float(i.dosis_max_gl) if i.dosis_max_gl else None} for i in qs]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            defaults = {'nombre':d['nombre'],'tipo':d.get('tipo','OTR'),
                        'unidad':d.get('unidad','kg'),'dosis_max_gl':d.get('dosis_max_gl'),'activo':True}
            if d.get('id'):
                BodInsumoEnologico.objects.filter(pk=d['id']).update(**defaults)
                i = BodInsumoEnologico.objects.get(pk=d['id'])
            else:
                defaults['cod_art'] = d['cod_art']
                i = BodInsumoEnologico.objects.create(**defaults)
            return _ok({'id':i.pk}, 'Insumo guardado')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# SEGUNDO BLOQUE DE IMPORTS (vino, elaboracion, calidad, costos, trazabilidad)
# =============================================================================
from ..bodega_models import (
    BodLaborCultural, BodTratamientoFitosanitario,
    BodContratoUva, BodLiquidacionUva,
    BodOrdenElaboracion, BodBalanceMasa,
    BodFichaProducto, BodNoConformidad,
    BodCostoLote, BodCostoDetalle,
    BodDeclaracionINV, BodGuiaTraslado, BodCertificadoAnalisis,
)

# =============================================================================
# VINEDO — LABORES
# =============================================================================
class BodLaboresCulturalesView(APIView):
    def get(self, request):
        qs = BodLaborCultural.objects.select_related('parcela')
        if request.query_params.get('parcela_id'):
            qs = qs.filter(parcela_id=request.query_params['parcela_id'])
        if request.query_params.get('campaña'):
            qs = qs.filter(campaña=request.query_params['campaña'])
        data = [{'id':l.pk,'parcela_id':l.parcela_id,'parcela_nombre':l.parcela.nombre,
                 'campaña':l.campaña,'tipo':l.tipo,'tipo_display':l.get_tipo_display(),
                 'fecha_inicio':l.fecha_inicio.isoformat(),
                 'fecha_fin':l.fecha_fin.isoformat() if l.fecha_fin else None,
                 'descripcion':l.descripcion,'jornales':float(l.jornales),
                 'costo_jornal':float(l.costo_jornal),'costo_maquinaria':float(l.costo_maquinaria),
                 'costo_insumos':float(l.costo_insumos),'costo_total':float(l.costo_total),
                 'responsable':l.responsable} for l in qs[:500]]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            costo_total = (float(d.get('costo_jornal',0))*float(d.get('jornales',0))
                          + float(d.get('costo_maquinaria',0)) + float(d.get('costo_insumos',0)))
            defaults = dict(
                parcela_id=d['parcela_id'], campaña=d['campaña'], tipo=d['tipo'],
                fecha_inicio=d['fecha_inicio'], fecha_fin=d.get('fecha_fin'),
                descripcion=d.get('descripcion',''), jornales=d.get('jornales',0),
                costo_jornal=d.get('costo_jornal',0), costo_maquinaria=d.get('costo_maquinaria',0),
                costo_insumos=d.get('costo_insumos',0), costo_total=costo_total,
                responsable=d.get('responsable',''), usuario=d.get('usuario',''))
            if d.get('id'):
                BodLaborCultural.objects.filter(pk=d['id']).update(**defaults)
                obj = BodLaborCultural.objects.select_related('parcela').get(pk=d['id'])
            else:
                obj = BodLaborCultural.objects.create(**defaults)
            return _ok({'id':obj.pk,'costo_total':float(obj.costo_total)}, 'Labor registrada')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# VINEDO — TRATAMIENTOS FITOSANITARIOS
# =============================================================================
class BodTratamientosFitosanitariosView(APIView):
    def get(self, request):
        qs = BodTratamientoFitosanitario.objects.select_related('parcela')
        if request.query_params.get('parcela_id'):
            qs = qs.filter(parcela_id=request.query_params['parcela_id'])
        if request.query_params.get('campaña'):
            qs = qs.filter(campaña=request.query_params['campaña'])
        data = [{'id':t.pk,'parcela_id':t.parcela_id,'parcela_nombre':t.parcela.nombre,
                 'campaña':t.campaña,'fecha':t.fecha.isoformat(),'producto':t.producto,
                 'principio_activo':t.principio_activo,'dosis_aplicada':float(t.dosis_aplicada),
                 'unidad':t.unidad,'dias_carencia':t.dias_carencia,
                 'fecha_fin_carencia':t.fecha_fin_carencia.isoformat() if t.fecha_fin_carencia else None,
                 'objetivo':t.objetivo,'operario':t.operario,'costo':float(t.costo)} for t in qs[:500]]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            defaults = dict(
                parcela_id=d['parcela_id'], campaña=d['campaña'], fecha=d['fecha'],
                producto=d['producto'], principio_activo=d.get('principio_activo',''),
                dosis_aplicada=d['dosis_aplicada'], unidad=d.get('unidad','cc/ha'),
                volumen_caldo=d.get('volumen_caldo'), dias_carencia=d.get('dias_carencia',0),
                objetivo=d.get('objetivo',''), operario=d.get('operario',''),
                lote_producto=d.get('lote_producto',''), costo=d.get('costo',0),
                usuario=d.get('usuario',''))
            if d.get('id'):
                BodTratamientoFitosanitario.objects.filter(pk=d['id']).update(**defaults)
                obj = BodTratamientoFitosanitario.objects.get(pk=d['id'])
            else:
                obj = BodTratamientoFitosanitario.objects.create(**defaults)
            return _ok({'id':obj.pk}, 'Tratamiento registrado')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# VINEDO — CONTRATOS Y LIQUIDACIONES DE UVA
# =============================================================================
class BodContratosUvaView(APIView):
    def get(self, request):
        qs = BodContratoUva.objects.select_related('varietal').filter(activo=True)
        if request.query_params.get('campaña'):
            qs = qs.filter(campaña=request.query_params['campaña'])
        data = [{'id':c.pk,'cod_prov':c.cod_prov,'nombre_prov':c.nombre_prov,
                 'campaña':c.campaña,'varietal':c.varietal_id,'varietal_nombre':c.varietal.nombre,
                 'kg_estimados':float(c.kg_estimados) if c.kg_estimados else None,
                 'tipo_precio':c.tipo_precio,'tipo_precio_display':c.get_tipo_precio_display(),
                 'precio_base_kg':float(c.precio_base_kg) if c.precio_base_kg else None,
                 'anticipo':float(c.anticipo),'condiciones':c.condiciones} for c in qs]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            varietal = BodVarietal.objects.get(codigo=d['varietal'])
            defaults = dict(
                cod_prov=d['cod_prov'], nombre_prov=d['nombre_prov'], campaña=d['campaña'],
                varietal=varietal, parcela_id=d.get('parcela_id'),
                kg_estimados=d.get('kg_estimados'), tipo_precio=d.get('tipo_precio','FI'),
                precio_base_kg=d.get('precio_base_kg'), anticipo=d.get('anticipo',0),
                condiciones=d.get('condiciones',''), usuario=d.get('usuario',''))
            if d.get('id'):
                BodContratoUva.objects.filter(pk=d['id']).update(**defaults)
                obj = BodContratoUva.objects.select_related('varietal').get(pk=d['id'])
            else:
                obj = BodContratoUva.objects.create(**defaults)
            return _ok({'id':obj.pk}, 'Contrato guardado')
        except BodVarietal.DoesNotExist:
            return _err('Varietal no encontrado')
        except Exception as e:
            return _err(str(e))

class BodLiquidacionesUvaView(APIView):
    def get(self, request):
        qs = BodLiquidacionUva.objects.all()
        if request.query_params.get('cod_prov'):
            qs = qs.filter(cod_prov=request.query_params['cod_prov'])
        if request.query_params.get('campaña'):
            qs = qs.filter(campaña=request.query_params['campaña'])
        data = [{'id':l.pk,'cod_prov':l.cod_prov,'nombre_prov':l.nombre_prov,
                 'campaña':l.campaña,'fecha':l.fecha.isoformat(),
                 'kg_liquidados':float(l.kg_liquidados),'precio_kg':float(l.precio_kg),
                 'importe_bruto':float(l.importe_bruto),'descuentos':float(l.descuentos),
                 'anticipo_aplicado':float(l.anticipo_aplicado),'importe_neto':float(l.importe_neto),
                 'estado':l.estado,'estado_display':l.get_estado_display()} for l in qs]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            importe_bruto = float(d['kg_liquidados'])*float(d['precio_kg'])
            importe_neto  = importe_bruto - float(d.get('descuentos',0)) - float(d.get('anticipo_aplicado',0))
            obj = BodLiquidacionUva.objects.create(
                contrato_id=d.get('contrato_id'), cod_prov=d['cod_prov'], nombre_prov=d['nombre_prov'],
                campaña=d['campaña'], fecha=d['fecha'], kg_liquidados=d['kg_liquidados'],
                precio_kg=d['precio_kg'], importe_bruto=importe_bruto,
                descuentos=d.get('descuentos',0), anticipo_aplicado=d.get('anticipo_aplicado',0),
                importe_neto=importe_neto, observaciones=d.get('observaciones',''),
                usuario=d.get('usuario',''))
            return _ok({'id':obj.pk,'importe_neto':float(obj.importe_neto)},
                       f'Liquidacion por ${importe_neto:,.2f}')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# ELABORACION
# =============================================================================
class BodOrdenesElaboracionView(APIView):
    def get(self, request):
        qs = BodOrdenElaboracion.objects.select_related('lote')
        if request.query_params.get('lote_id'):
            qs = qs.filter(lote_id=request.query_params['lote_id'])
        data = [{'id':o.numero,'lote_id':o.lote_id,'lote_codigo':o.lote.codigo,
                 'fecha_emision':o.fecha_emision.isoformat(),
                 'fecha_ejecucion':o.fecha_ejecucion.isoformat() if o.fecha_ejecucion else None,
                 'proceso':o.proceso,'instrucciones':o.instrucciones,
                 'responsable':o.responsable,'estado':o.estado,'estado_display':o.get_estado_display(),
                 'resultado':o.resultado} for o in qs[:200]]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            defaults = dict(
                lote_id=d['lote_id'], fecha_emision=d['fecha_emision'],
                fecha_ejecucion=d.get('fecha_ejecucion'), proceso=d['proceso'],
                instrucciones=d.get('instrucciones',''), parametros_objetivo=d.get('parametros_objetivo',{}),
                responsable=d.get('responsable',''), estado=d.get('estado','PE'),
                resultado=d.get('resultado',''), usuario=d.get('usuario',''))
            if d.get('id'):
                BodOrdenElaboracion.objects.filter(pk=d['id']).update(**defaults)
                obj = BodOrdenElaboracion.objects.select_related('lote').get(pk=d['id'])
            else:
                obj = BodOrdenElaboracion.objects.create(**defaults)
            return _ok({'id':obj.numero}, 'Orden de elaboracion guardada')
        except Exception as e:
            return _err(str(e))

class BodBalanceMasaView(APIView):
    def get(self, request):
        lote_id = request.query_params.get('lote_id')
        if not lote_id:
            return _err('Se requiere lote_id')
        try:
            b = BodBalanceMasa.objects.select_related('lote').get(lote_id=lote_id)
            return _ok({'id':b.pk,'lote_id':b.lote_id,'lote_codigo':b.lote.codigo,
                        'campaña':b.campaña,'kg_uva_total':float(b.kg_uva_total),
                        'kg_uva_propia':float(b.kg_uva_propia),'kg_uva_comprada':float(b.kg_uva_comprada),
                        'kg_escobajo':float(b.kg_escobajo),'kg_orujo':float(b.kg_orujo),'kg_borras':float(b.kg_borras),
                        'litros_mosto_flor':float(b.litros_mosto_flor),'litros_prensa':float(b.litros_prensa),
                        'litros_totales':float(b.litros_totales),'litros_merma_proceso':float(b.litros_merma_proceso),
                        'rendimiento_lkg':float(b.rendimiento_lkg) if b.rendimiento_lkg else None,
                        'porcentaje_extraccion':float(b.porcentaje_extraccion) if b.porcentaje_extraccion else None,
                        'fecha_cierre':b.fecha_cierre.isoformat()})
        except BodBalanceMasa.DoesNotExist:
            return _ok(None)
    def post(self, request):
        d = request.data
        try:
            b, _ = BodBalanceMasa.objects.update_or_create(
                lote_id=d['lote_id'],
                defaults=dict(campaña=d['campaña'],kg_uva_total=d['kg_uva_total'],
                              kg_uva_propia=d.get('kg_uva_propia',0),kg_uva_comprada=d.get('kg_uva_comprada',0),
                              kg_escobajo=d.get('kg_escobajo',0),kg_orujo=d.get('kg_orujo',0),
                              kg_borras=d.get('kg_borras',0),litros_mosto_flor=d.get('litros_mosto_flor',0),
                              litros_prensa=d.get('litros_prensa',0),litros_totales=d['litros_totales'],
                              litros_merma_proceso=d.get('litros_merma_proceso',0),
                              fecha_cierre=d['fecha_cierre'],observaciones=d.get('observaciones',''),
                              usuario=d.get('usuario','')))
            return _ok({'id':b.pk,'rendimiento_lkg':float(b.rendimiento_lkg) if b.rendimiento_lkg else None},
                       f'Balance guardado')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# CALIDAD — FICHAS DE PRODUCTO
# =============================================================================
class BodFichasProductoView(APIView):
    def get(self, request):
        qs = BodFichaProducto.objects.filter(activa=True).select_related('varietal')
        data = [{'id':f.pk,'codigo':f.codigo,'nombre':f.nombre,'varietal':f.varietal_id,
                 'tipo_vino':f.tipo_vino,
                 'alcohol_min':float(f.alcohol_min) if f.alcohol_min else None,
                 'alcohol_max':float(f.alcohol_max) if f.alcohol_max else None,
                 'ph_min':float(f.ph_min) if f.ph_min else None,
                 'ph_max':float(f.ph_max) if f.ph_max else None,
                 'acidez_total_min':float(f.acidez_total_min) if f.acidez_total_min else None,
                 'acidez_total_max':float(f.acidez_total_max) if f.acidez_total_max else None,
                 'so2_libre_max':float(f.so2_libre_max) if f.so2_libre_max else None,
                 'so2_total_max':float(f.so2_total_max) if f.so2_total_max else None,
                 'azucar_max':float(f.azucar_max) if f.azucar_max else None,
                 'perfil_sensorial':f.perfil_sensorial,
                 'proceso_elaboracion':f.proceso_elaboracion} for f in qs]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            defaults = dict(
                nombre=d['nombre'],varietal_id=d.get('varietal'),tipo_vino=d.get('tipo_vino','TI'),
                descripcion=d.get('descripcion',''),
                alcohol_min=d.get('alcohol_min'),alcohol_max=d.get('alcohol_max'),
                acidez_total_min=d.get('acidez_total_min'),acidez_total_max=d.get('acidez_total_max'),
                ph_min=d.get('ph_min'),ph_max=d.get('ph_max'),azucar_max=d.get('azucar_max'),
                so2_libre_max=d.get('so2_libre_max'),so2_total_max=d.get('so2_total_max'),
                perfil_sensorial=d.get('perfil_sensorial',''),
                proceso_elaboracion=d.get('proceso_elaboracion',''),
                usuario=d.get('usuario',''))
            if d.get('id'):
                BodFichaProducto.objects.filter(pk=d['id']).update(**defaults)
                obj = BodFichaProducto.objects.get(pk=d['id'])
            else:
                defaults['codigo'] = d['codigo']
                obj = BodFichaProducto.objects.create(**defaults)
            return _ok({'id':obj.pk}, 'Ficha guardada')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# MEJORA 4: No conformidades con cambio de estado rapido
# =============================================================================
class BodNoConformidadesView(APIView):
    def get(self, request):
        qs = BodNoConformidad.objects.all()
        if request.query_params.get('estado'):
            qs = qs.filter(estado=request.query_params['estado'])
        data = [{'id':nc.numero,'fecha':nc.fecha.isoformat(),'descripcion':nc.descripcion,
                 'origen':nc.origen,'lote_id':nc.lote_id,
                 'lote_codigo':nc.lote.codigo if nc.lote else None,
                 'gravedad':nc.gravedad,'gravedad_display':nc.get_gravedad_display(),
                 'responsable':nc.responsable,'accion_correctiva':nc.accion_correctiva,
                 'fecha_cierre':nc.fecha_cierre.isoformat() if nc.fecha_cierre else None,
                 'estado':nc.estado,'estado_display':nc.get_estado_display()} for nc in qs[:200]]
        return _ok(data)
    def post(self, request):
        d = request.data
        # Accion rapida de cambio de estado
        if d.get('accion') == 'cambiar_estado':
            try:
                from datetime import date as _date
                nc = BodNoConformidad.objects.get(pk=d['id'])
                nc.estado = d['estado']
                if d['estado'] == 'CE' and not nc.fecha_cierre:
                    nc.fecha_cierre = d.get('fecha_cierre') or _date.today().isoformat()
                if d.get('accion_correctiva'):
                    nc.accion_correctiva = d['accion_correctiva']
                nc.usuario = d.get('usuario','')
                nc.save()
                return _ok({'id':nc.numero,'estado':nc.estado,
                            'estado_display':nc.get_estado_display(),
                            'fecha_cierre':nc.fecha_cierre.isoformat() if nc.fecha_cierre else None},
                           f'NC #{nc.numero} → {nc.get_estado_display()}')
            except BodNoConformidad.DoesNotExist:
                return _err('NC no encontrada')
            except Exception as e:
                return _err(str(e))
        try:
            defaults = dict(
                fecha=d['fecha'],descripcion=d['descripcion'],origen=d.get('origen',''),
                lote_id=d.get('lote_id'),gravedad=d.get('gravedad','L'),
                responsable=d.get('responsable',''),accion_correctiva=d.get('accion_correctiva',''),
                fecha_cierre=d.get('fecha_cierre'),estado=d.get('estado','AB'),
                usuario=d.get('usuario',''))
            if d.get('id'):
                BodNoConformidad.objects.filter(pk=d['id']).update(**defaults)
                obj = BodNoConformidad.objects.get(pk=d['id'])
            else:
                obj = BodNoConformidad.objects.create(**defaults)
            return _ok({'id':obj.numero}, f'NC #{obj.numero} guardada')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# COSTOS
# =============================================================================
class BodCostosView(APIView):
    def get(self, request):
        lote_id = request.query_params.get('lote_id')
        if not lote_id:
            data = [{'lote_id':c.lote_id,'lote_codigo':c.lote.codigo,
                     'costo_uva_propia':float(c.costo_uva_propia),'costo_uva_comprada':float(c.costo_uva_comprada),
                     'costo_insumos_enologicos':float(c.costo_insumos_enologicos),
                     'costo_mano_obra_bodega':float(c.costo_mano_obra_bodega),
                     'costo_total_granel':float(c.costo_total_granel),
                     'costo_por_litro':float(c.costo_por_litro) if c.costo_por_litro else None,
                     'costo_materiales_emb':float(c.costo_materiales_emb),
                     'costo_total_pt':float(c.costo_total_pt),
                     'costo_por_botella':float(c.costo_por_botella) if c.costo_por_botella else None,
                     'fecha_calculo':c.fecha_calculo.isoformat()}
                    for c in BodCostoLote.objects.select_related('lote').all()]
            return _ok(data)
        try:
            c = BodCostoLote.objects.select_related('lote').get(lote_id=lote_id)
            detalles = [{'id':det.pk,'fecha':det.fecha.isoformat(),'categoria':det.categoria,
                         'categoria_display':det.get_categoria_display(),'descripcion':det.descripcion,
                         'cantidad':float(det.cantidad),'unidad':det.unidad,
                         'precio_unit':float(det.precio_unit),'importe':float(det.importe)}
                        for det in c.detalles.all()]
            cl = {'lote_id':c.lote_id,'lote_codigo':c.lote.codigo,
                  'costo_uva_propia':float(c.costo_uva_propia),'costo_uva_comprada':float(c.costo_uva_comprada),
                  'costo_insumos_enologicos':float(c.costo_insumos_enologicos),
                  'costo_mano_obra_bodega':float(c.costo_mano_obra_bodega),
                  'costo_energia':float(c.costo_energia),'costo_crianza_barricas':float(c.costo_crianza_barricas),
                  'costo_amortizacion_barrica':float(c.costo_amortizacion_barrica),
                  'costo_gastos_indirectos':float(c.costo_gastos_indirectos),
                  'costo_total_granel':float(c.costo_total_granel),
                  'costo_por_litro':float(c.costo_por_litro) if c.costo_por_litro else None,
                  'costo_materiales_emb':float(c.costo_materiales_emb),
                  'costo_mano_obra_emb':float(c.costo_mano_obra_emb),
                  'costo_total_pt':float(c.costo_total_pt),
                  'costo_por_botella':float(c.costo_por_botella) if c.costo_por_botella else None}
            return _ok({'costo_lote':cl,'detalles':detalles})
        except BodCostoLote.DoesNotExist:
            return _ok({'costo_lote':None,'detalles':[]})
    def post(self, request):
        d = request.data
        accion = d.get('accion','actualizar_cabecera')
        try:
            with transaction.atomic():
                if accion == 'actualizar_cabecera':
                    c, _ = BodCostoLote.objects.get_or_create(lote_id=d['lote_id'])
                    for campo in ['costo_uva_propia','costo_uva_comprada','costo_insumos_enologicos',
                                  'costo_mano_obra_bodega','costo_energia','costo_crianza_barricas',
                                  'costo_amortizacion_barrica','costo_gastos_indirectos',
                                  'costo_materiales_emb','costo_mano_obra_emb']:
                        if campo in d:
                            setattr(c, campo, d[campo])
                    c.recalcular(); c.usuario=d.get('usuario',''); c.save()
                    return _ok({'costo_total_granel':float(c.costo_total_granel),
                                'costo_por_litro':float(c.costo_por_litro) if c.costo_por_litro else None,
                                'costo_total_pt':float(c.costo_total_pt),
                                'costo_por_botella':float(c.costo_por_botella) if c.costo_por_botella else None},
                               'Costos recalculados')
                elif accion == 'agregar_detalle':
                    c, _ = BodCostoLote.objects.get_or_create(lote_id=d['lote_id'])
                    det = BodCostoDetalle.objects.create(
                        costo_lote=c, fecha=d['fecha'], categoria=d['categoria'],
                        descripcion=d['descripcion'], cantidad=d.get('cantidad',1),
                        unidad=d.get('unidad',''), precio_unit=d.get('precio_unit',0),
                        usuario=d.get('usuario',''))
                    mapa = {'UVA':'costo_uva_comprada','INS':'costo_insumos_enologicos',
                            'MO':'costo_mano_obra_bodega','ENE':'costo_energia',
                            'BAR':'costo_amortizacion_barrica','MAT':'costo_materiales_emb'}
                    if det.categoria in mapa:
                        campo = mapa[det.categoria]
                        setattr(c, campo, float(getattr(c,campo)) + float(det.importe))
                        c.recalcular(); c.save()
                    return _ok({'id':det.pk,'importe':float(det.importe)}, 'Detalle agregado')
                return _err('Accion desconocida')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# TRAZABILIDAD
# =============================================================================
class BodTrazabilidadView(APIView):
    def get(self, request):
        lote_id = request.query_params.get('lote_id')
        direccion = request.query_params.get('direccion','atras')
        if not lote_id:
            return _err('Se requiere lote_id')
        try:
            lote = BodLoteGranel.objects.select_related('varietal_ppal').get(pk=lote_id)
        except BodLoteGranel.DoesNotExist:
            return _err('Lote no encontrado')
        if direccion == 'atras':
            composicion = [{'lote_origen_id':c.lote_origen_id,
                            'lote_origen_codigo':c.lote_origen.codigo if c.lote_origen else None,
                            'varietal':c.varietal_id,'litros':float(c.litros),
                            'porcentaje':float(c.porcentaje) if c.porcentaje else None,
                            'campaña_origen':c.campaña_origen}
                           for c in BodComposicionLote.objects.filter(lote_destino=lote).select_related('lote_origen','varietal')]
            tickets = [{'ticket_id':t.numero,'fecha':t.fecha.isoformat(),
                        'parcela':t.parcela.nombre if t.parcela else None,
                        'varietal':t.varietal_id,'kg_neto':float(t.peso_neto),
                        'cod_prov':t.cod_prov,'nombre_prov':t.nombre_prov,
                        'brix':float(t.brix_entrada) if t.brix_entrada else None}
                       for t in BodTicketBascula.objects.filter(lote_destino=lote).select_related('parcela','varietal')]
            insumos = [{'operacion_id':op.pk,'fecha':op.fecha.isoformat(),
                        'insumo':op.insumo.nombre if op.insumo else None,
                        'lote_proveedor':op.lote_insumo_prov,
                        'cantidad':float(op.cantidad_insumo) if op.cantidad_insumo else None,
                        'unidad':op.unidad_insumo}
                       for op in BodOperacionEnologica.objects.filter(lote=lote,insumo__isnull=False).select_related('insumo')]
            return _ok({'lote':_lote_dict(lote),'composicion_varietal':composicion,
                        'tickets_uva':tickets,'insumos_utilizados':insumos})
        else:
            usos = [{'lote_destino_id':c.lote_destino_id,'lote_destino_codigo':c.lote_destino.codigo,
                     'litros':float(c.litros),'porcentaje':float(c.porcentaje) if c.porcentaje else None}
                    for c in BodComposicionLote.objects.filter(lote_origen=lote).select_related('lote_destino')]
            ordenes = [{'orden_id':o.numero,'formato':o.formato,
                        'botellas':o.botellas_real or o.botellas_plan,
                        'cod_art_pt':o.cod_art_pt,'nro_rnoe':o.nro_rnoe,'estado':o.estado,
                        'fecha':o.fecha_real.isoformat() if o.fecha_real else o.fecha_plan.isoformat()}
                       for o in BodOrdenEmbotellado.objects.filter(lote=lote)]
            guias = [{'guia_id':g.numero,'fecha':g.fecha.isoformat(),
                      'destino':g.establecimiento_destino,
                      'litros_o_unidades':float(g.litros_o_unidades),'estado':g.estado}
                     for g in BodGuiaTraslado.objects.filter(lote=lote)]
            return _ok({'lote':_lote_dict(lote),'usado_en_lotes':usos,
                        'ordenes_embotellado':ordenes,'guias_traslado':guias})

# =============================================================================
# FISCAL / INV
# =============================================================================
class BodDeclaracionesINVView(APIView):
    def get(self, request):
        qs = BodDeclaracionINV.objects.all()
        if request.query_params.get('tipo'):
            qs = qs.filter(tipo=request.query_params['tipo'])
        data = [{'id':dec.pk,'tipo':dec.tipo,'tipo_display':dec.get_tipo_display(),
                 'periodo':dec.periodo.isoformat(),'campaña':dec.campaña,
                 'estado':dec.estado,'estado_display':dec.get_estado_display(),
                 'kg_uva_declarados':float(dec.kg_uva_declarados),
                 'litros_declarados':float(dec.litros_declarados),
                 'litros_existencias':float(dec.litros_existencias),
                 'fecha_presentacion':dec.fecha_presentacion.isoformat() if dec.fecha_presentacion else None,
                 'nro_expediente_inv':dec.nro_expediente_inv} for dec in qs]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            if d.get('auto_calcular') and d.get('campaña'):
                campaña = d['campaña']
                lotes = BodLoteGranel.objects.filter(campaña=campaña)
                litros_existencias = sum(float(l.litros_actuales) for l in lotes if l.estado not in ['EM','VE','AN'])
                kg_uva = float(BodTicketBascula.objects.filter(campaña=campaña).aggregate(t=Sum('peso_neto'))['t'] or 0)
                litros_declarados = sum(float(l.litros_iniciales) for l in lotes)
            else:
                litros_existencias = d.get('litros_existencias',0)
                kg_uva = d.get('kg_uva_declarados',0)
                litros_declarados = d.get('litros_declarados',0)
            obj = BodDeclaracionINV.objects.create(
                tipo=d['tipo'],periodo=d['periodo'],campaña=d.get('campaña'),
                estado=d.get('estado','BO'),kg_uva_declarados=kg_uva,
                litros_declarados=litros_declarados,litros_existencias=litros_existencias,
                fecha_presentacion=d.get('fecha_presentacion'),
                nro_expediente_inv=d.get('nro_expediente_inv',''),
                observaciones=d.get('observaciones',''),usuario=d.get('usuario',''))
            return _ok({'id':obj.pk}, f'{obj.get_tipo_display()} creada')
        except Exception as e:
            return _err(str(e))

class BodGuiasTrasladoView(APIView):
    def get(self, request):
        qs = BodGuiaTraslado.objects.select_related('lote','varietal')
        if request.query_params.get('lote_id'):
            qs = qs.filter(lote_id=request.query_params['lote_id'])
        if request.query_params.get('estado'):
            qs = qs.filter(estado=request.query_params['estado'])
        data = [{'id':g.numero,'fecha':g.fecha.isoformat(),'tipo':g.tipo,'tipo_display':g.get_tipo_display(),
                 'establecimiento_destino':g.establecimiento_destino,'domicilio_destino':g.domicilio_destino,
                 'lote_id':g.lote_id,'lote_codigo':g.lote.codigo if g.lote else None,
                 'descripcion_mercaderia':g.descripcion_mercaderia,
                 'litros_o_unidades':float(g.litros_o_unidades),'varietal':g.varietal_id,
                 'campaña':g.campaña,'grado_alcohol':float(g.grado_alcohol) if g.grado_alcohol else None,
                 'transportista':g.transportista,'patente_vehiculo':g.patente_vehiculo,
                 'estado':g.estado,'estado_display':g.get_estado_display()} for g in qs[:200]]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            defaults = dict(
                fecha=d['fecha'],tipo=d.get('tipo','PT'),
                establecimiento_origen=d.get('establecimiento_origen',''),
                domicilio_origen=d.get('domicilio_origen',''),rnoe_origen=d.get('rnoe_origen',''),
                establecimiento_destino=d['establecimiento_destino'],
                domicilio_destino=d.get('domicilio_destino',''),lote_id=d.get('lote_id'),
                descripcion_mercaderia=d['descripcion_mercaderia'],
                litros_o_unidades=d['litros_o_unidades'],varietal_id=d.get('varietal'),
                campaña=d.get('campaña'),grado_alcohol=d.get('grado_alcohol'),
                transportista=d.get('transportista',''),patente_vehiculo=d.get('patente_vehiculo',''),
                movim_remito=d.get('movim_remito'),estado=d.get('estado','EM'),
                observaciones=d.get('observaciones',''),usuario=d.get('usuario',''))
            if d.get('id'):
                BodGuiaTraslado.objects.filter(pk=d['id']).update(**defaults)
                obj = BodGuiaTraslado.objects.get(pk=d['id'])
            else:
                obj = BodGuiaTraslado.objects.create(**defaults)
            return _ok({'id':obj.numero}, f'Guia #{obj.numero} guardada')
        except Exception as e:
            return _err(str(e))

class BodCertificadosAnalisisView(APIView):
    def get(self, request):
        qs = BodCertificadoAnalisis.objects.select_related('lote','analisis','guia_traslado')
        if request.query_params.get('lote_id'):
            qs = qs.filter(lote_id=request.query_params['lote_id'])
        data = [{'id':c.numero,'lote_id':c.lote_id,'lote_codigo':c.lote.codigo,
                 'fecha_emision':c.fecha_emision.isoformat(),
                 'fecha_vencimiento':c.fecha_vencimiento.isoformat() if c.fecha_vencimiento else None,
                 'laboratorio':c.laboratorio,'grado_alcohol':float(c.grado_alcohol),
                 'acidez_total':float(c.acidez_total),'acidez_volatil':float(c.acidez_volatil),
                 'so2_total':float(c.so2_total),'azucar_residual':float(c.azucar_residual),
                 'apto_consumo':c.apto_consumo,'guia_id':c.guia_traslado_id} for c in qs[:200]]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            obj = BodCertificadoAnalisis.objects.create(
                lote_id=d['lote_id'],analisis_id=d.get('analisis_id'),
                guia_traslado_id=d.get('guia_traslado_id'),
                fecha_emision=d['fecha_emision'],fecha_vencimiento=d.get('fecha_vencimiento'),
                laboratorio=d.get('laboratorio','INV'),grado_alcohol=d['grado_alcohol'],
                acidez_total=d['acidez_total'],acidez_volatil=d['acidez_volatil'],
                so2_total=d['so2_total'],azucar_residual=d.get('azucar_residual',0),
                apto_consumo=d.get('apto_consumo',True),observaciones=d.get('observaciones',''),
                usuario=d.get('usuario',''))
            return _ok({'id':obj.numero}, f'Certificado #{obj.numero} emitido')
        except Exception as e:
            return _err(str(e))

# =============================================================================
# MEJORA 5: Libro de bodega INV por varietal
# =============================================================================
class BodLibroBodegaView(APIView):
    """
    Libro de bodega formato INV: consolida movimientos de granel
    agrupados por varietal y periodo. Parametros GET:
    campaña, varietal, fecha_desde, fecha_hasta
    """
    def get(self, request):
        campaña = request.query_params.get('campaña')
        varietal = request.query_params.get('varietal')
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        qs = BodMovimientoGranel.objects.select_related(
            'lote','lote__varietal_ppal','recipiente_origen','recipiente_destino'
        ).order_by('lote__varietal_ppal__nombre','fecha')
        if campaña: qs = qs.filter(lote__campaña=campaña)
        if varietal: qs = qs.filter(lote__varietal_ppal__codigo=varietal)
        if fecha_desde: qs = qs.filter(fecha__date__gte=fecha_desde)
        if fecha_hasta: qs = qs.filter(fecha__date__lte=fecha_hasta)
        from collections import defaultdict
        from decimal import Decimal
        por_varietal = defaultdict(list)
        totales = defaultdict(lambda: {'ingresos':Decimal(0),'egresos':Decimal(0),'movimientos':0})
        TIPOS_EGRESO = {'EG','ME','VE','CO'}
        for m in qs:
            var_key = m.lote.varietal_ppal_id
            var_nom = m.lote.varietal_ppal.nombre
            es_egreso = m.tipo in TIPOS_EGRESO
            por_varietal[var_key].append({
                'fecha': m.fecha.isoformat(), 'tipo': m.tipo,
                'tipo_display': m.get_tipo_display(),
                'lote': m.lote.codigo, 'campaña': m.lote.campaña,
                'litros': float(m.litros), 'es_egreso': es_egreso,
                'recipiente_origen': m.recipiente_origen.codigo if m.recipiente_origen else None,
                'recipiente_destino': m.recipiente_destino.codigo if m.recipiente_destino else None,
                'descripcion': m.descripcion, 'usuario': m.usuario,
                'varietal': var_key, 'varietal_nombre': var_nom,
            })
            if es_egreso: totales[var_key]['egresos'] += m.litros
            else: totales[var_key]['ingresos'] += m.litros
            totales[var_key]['movimientos'] += 1
            totales[var_key]['varietal_nombre'] = var_nom
        # Existencias actuales por varietal
        ex_qs = (BodLoteGranel.objects.filter(estado__in=['EB','CR','LI','EP'])
                 .values('varietal_ppal__codigo','varietal_ppal__nombre')
                 .annotate(litros=Sum('litros_actuales')))
        if campaña: ex_qs = ex_qs.filter(campaña=campaña)
        existencias = {e['varietal_ppal__codigo']:
                       {'litros':float(e['litros'] or 0),'varietal_nombre':e['varietal_ppal__nombre']}
                       for e in ex_qs}
        return _ok({
            'movimientos_por_varietal': {
                k: {'varietal_nombre': totales[k].get('varietal_nombre',k),
                    'total_ingresos': float(totales[k]['ingresos']),
                    'total_egresos': float(totales[k]['egresos']),
                    'saldo_movimientos': float(totales[k]['ingresos']-totales[k]['egresos']),
                    'cant_movimientos': totales[k]['movimientos'],
                    'detalle': por_varietal[k]}
                for k in por_varietal},
            'existencias_actuales': existencias,
            'filtros_aplicados': {'campaña':campaña,'varietal':varietal,
                                  'fecha_desde':fecha_desde,'fecha_hasta':fecha_hasta},
        })

# =============================================================================
# FASE 1 — PROCESO FERMENTATIVO, CATA Y SO2
# =============================================================================
from ..bodega_models import (
    BodFermentacionDiaria, BodRemontaje,
    BodFML, BodCromatografia,
    BodCataTecnica, BodGestionSO2,
)

class BodFermentacionDiariaView(APIView):
    def get(self, request):
        lote_id = request.query_params.get('lote_id')
        if not lote_id: return _err('Se requiere lote_id')
        qs = BodFermentacionDiaria.objects.filter(lote_id=lote_id).order_by('fecha','turno')
        data = [{'id':f.pk,'fecha':f.fecha.isoformat(),'turno':f.turno,
                 'turno_display':f.get_turno_display(),
                 'temperatura_c':float(f.temperatura_c),'densidad':float(f.densidad),
                 'brix':float(f.brix) if f.brix else None,
                 'alcohol_probable':float(f.alcohol_probable) if f.alcohol_probable else None,
                 'estado_sombrero':f.estado_sombrero,'co2_activo':f.co2_activo,
                 'fermentacion_trabada':f.fermentacion_trabada,
                 'color_mosto':f.color_mosto,'observaciones':f.observaciones} for f in qs]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            ultima = BodFermentacionDiaria.objects.filter(lote_id=d['lote_id']).order_by('-fecha','-turno').first()
            trabada = False
            if ultima and float(ultima.densidad) > 995:
                trabada = (float(ultima.densidad) - float(d['densidad'])) < 1.0
            obj, _ = BodFermentacionDiaria.objects.update_or_create(
                lote_id=d['lote_id'], fecha=d['fecha'], turno=d.get('turno','M'),
                defaults={'temperatura_c':d['temperatura_c'],'densidad':d['densidad'],
                          'brix':d.get('brix'),'estado_sombrero':d.get('estado_sombrero','SN'),
                          'co2_activo':d.get('co2_activo',True),'color_mosto':d.get('color_mosto',''),
                          'fermentacion_trabada':trabada,'observaciones':d.get('observaciones',''),
                          'usuario':d.get('usuario','')})
            alerta = 'FERMENTACION TRABADA' if trabada else ''
            return _ok({'id':obj.pk,'alcohol_probable':float(obj.alcohol_probable) if obj.alcohol_probable else 0,
                        'fermentacion_trabada':trabada,'alerta':alerta},
                       f'Lectura guardada{" — " + alerta if alerta else ""}')
        except Exception as e:
            return _err(str(e))

class BodCurvaFermentacionView(APIView):
    def get(self, request):
        lote_id = request.query_params.get('lote_id')
        if not lote_id: return _err('Se requiere lote_id')
        qs = BodFermentacionDiaria.objects.filter(lote_id=lote_id).order_by('fecha','turno')
        curva = [{'fecha':f.fecha.isoformat(),'turno':f.turno,
                  'label':f"{f.fecha.strftime('%d/%m')} {f.get_turno_display()[0]}",
                  'densidad':float(f.densidad),'temperatura_c':float(f.temperatura_c),
                  'alcohol_probable':float(f.alcohol_probable) if f.alcohol_probable else 0,
                  'fermentacion_trabada':f.fermentacion_trabada} for f in qs]
        return _ok(curva)

class BodRemontajesView(APIView):
    def get(self, request):
        qs = BodRemontaje.objects.select_related('lote').all()
        if request.query_params.get('lote_id'):
            qs = qs.filter(lote_id=request.query_params['lote_id'])
        data = [{'id':r.pk,'lote_id':r.lote_id,'lote_codigo':r.lote.codigo,
                 'fecha':r.fecha.isoformat(),'tipo':r.tipo,'tipo_display':r.get_tipo_display(),
                 'objetivo':r.objetivo,'objetivo_display':r.get_objetivo_display(),
                 'volumen_bombeado_l':float(r.volumen_bombeado_l) if r.volumen_bombeado_l else None,
                 'duracion_min':r.duracion_min,'temperatura_mosto_c':float(r.temperatura_mosto_c) if r.temperatura_mosto_c else None,
                 'observaciones':r.observaciones} for r in qs[:500]]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            obj = BodRemontaje.objects.create(
                lote_id=d['lote_id'], fecha=d['fecha'], tipo=d.get('tipo','REM'),
                objetivo=d.get('objetivo','EXT'), volumen_bombeado_l=d.get('volumen_bombeado_l'),
                duracion_min=d.get('duracion_min'), caudal_lh=d.get('caudal_lh'),
                temperatura_mosto_c=d.get('temperatura_mosto_c'),
                tiempo_escurrido_min=d.get('tiempo_escurrido_min'),
                cambio_color=d.get('cambio_color',''), observaciones=d.get('observaciones',''),
                usuario=d.get('usuario',''))
            return _ok({'id':obj.pk}, f'{obj.get_tipo_display()} registrado')
        except Exception as e:
            return _err(str(e))

class BodFMLView(APIView):
    def get(self, request):
        lote_id = request.query_params.get('lote_id')
        if lote_id:
            try:
                fml = BodFML.objects.prefetch_related('cromatografias').get(lote_id=lote_id)
                cromas = [{'id':c.pk,'fecha':c.fecha.isoformat(),'resultado':c.resultado,
                           'resultado_display':c.get_resultado_display(),
                           'temperatura_vino':float(c.temperatura_vino) if c.temperatura_vino else None,
                           'acidez_volatil':float(c.acidez_volatil) if c.acidez_volatil else None,
                           'observaciones':c.observaciones} for c in fml.cromatografias.order_by('fecha')]
                return _ok({'id':fml.pk,'lote_id':fml.lote_id,'tipo':fml.tipo,'estado':fml.estado,
                            'estado_display':fml.get_estado_display(),
                            'fecha_inoculacion':fml.fecha_inoculacion.isoformat() if fml.fecha_inoculacion else None,
                            'cepa_bacteria':fml.cepa_bacteria,
                            'dosis_ghl':float(fml.dosis_ghl) if fml.dosis_ghl else None,
                            'fecha_completada':fml.fecha_completada.isoformat() if fml.fecha_completada else None,
                            'dias_duracion':fml.dias_duracion,
                            'observaciones':fml.observaciones,'cromatografias':cromas})
            except BodFML.DoesNotExist:
                return _ok(None)
        qs = BodFML.objects.select_related('lote').all()
        return _ok([{'id':f.pk,'lote_id':f.lote_id,'lote_codigo':f.lote.codigo,'estado':f.estado,
                     'estado_display':f.get_estado_display(),'tipo':f.tipo,
                     'fecha_inoculacion':f.fecha_inoculacion.isoformat() if f.fecha_inoculacion else None,
                     'dias_duracion':f.dias_duracion} for f in qs])
    def post(self, request):
        d = request.data
        accion = d.get('accion','guardar_fml')
        try:
            if accion == 'guardar_fml':
                fml, _ = BodFML.objects.update_or_create(lote_id=d['lote_id'], defaults={
                    'tipo':d.get('tipo','INO'),'estado':d.get('estado','PE'),
                    'fecha_inoculacion':d.get('fecha_inoculacion'),'cepa_bacteria':d.get('cepa_bacteria',''),
                    'dosis_ghl':d.get('dosis_ghl'),'temperatura_inicio_c':d.get('temperatura_inicio_c'),
                    'ph_al_inicio':d.get('ph_al_inicio'),'so2_libre_al_inicio':d.get('so2_libre_al_inicio'),
                    'fecha_completada':d.get('fecha_completada'),'acidez_total_post':d.get('acidez_total_post'),
                    'observaciones':d.get('observaciones',''),'usuario':d.get('usuario','')})
                alerta = ''
                if fml.so2_libre_al_inicio and float(fml.so2_libre_al_inicio) > 15:
                    alerta = f'SO2 libre alto puede inhibir bacteria malolactica'
                return _ok({'id':fml.pk,'alerta':alerta}, 'FML guardada')
            elif accion == 'agregar_croma':
                fml = BodFML.objects.get(lote_id=d['lote_id'])
                croma = BodCromatografia.objects.create(
                    fml=fml, fecha=d['fecha'], resultado=d['resultado'],
                    temperatura_vino=d.get('temperatura_vino'),acidez_volatil=d.get('acidez_volatil'),
                    observaciones=d.get('observaciones',''),usuario=d.get('usuario',''))
                if croma.resultado == 'AU' and fml.estado != 'CO':
                    fml.estado='CO'; fml.fecha_completada=croma.fecha; fml.save()
                return _ok({'id':croma.pk,'fml_completada':croma.resultado=='AU'},
                           f'Cromatografia — {croma.get_resultado_display()}')
            return _err('Accion desconocida')
        except BodFML.DoesNotExist:
            return _err('FML no encontrada. Primero inicializa el seguimiento.')
        except Exception as e:
            return _err(str(e))

class BodCatasTecnicasView(APIView):
    def get(self, request):
        qs = BodCataTecnica.objects.select_related('lote')
        if request.query_params.get('lote_id'):
            qs = qs.filter(lote_id=request.query_params['lote_id'])
        data = [{'id':c.pk,'lote_id':c.lote_id,'lote_codigo':c.lote.codigo,
                 'fecha':c.fecha.isoformat(),'contexto':c.contexto,'contexto_display':c.get_contexto_display(),
                 'catadores':c.catadores,'color_intensidad':c.color_intensidad,
                 'nariz_intensidad':c.nariz_intensidad,'nariz_descriptores':c.nariz_descriptores,
                 'boca_acidez':c.boca_acidez,'boca_taninos':c.boca_taninos,
                 'boca_final_s':c.boca_final_s,'defecto_brett':c.defecto_brett,
                 'defecto_va_alta':c.defecto_va_alta,'defecto_oxidacion':c.defecto_oxidacion,
                 'tiene_defectos':c.tiene_defectos,'puntaje':c.puntaje,
                 'conclusion':c.conclusion,'conclusion_display':c.get_conclusion_display(),
                 'accion_recomendada':c.accion_recomendada} for c in qs[:200]]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            defaults = dict(
                fecha=d['fecha'],contexto=d.get('contexto','RU'),catadores=d.get('catadores',''),
                temperatura_servicio=d.get('temperatura_servicio'),
                color_intensidad=d.get('color_intensidad'),color_tonalidad=d.get('color_tonalidad',''),
                color_limpidez=d.get('color_limpidez',''),nariz_intensidad=d.get('nariz_intensidad'),
                nariz_calidad=d.get('nariz_calidad',''),nariz_descriptores=d.get('nariz_descriptores',''),
                boca_ataque=d.get('boca_ataque',''),boca_acidez=d.get('boca_acidez'),
                boca_taninos=d.get('boca_taninos',''),boca_cuerpo=d.get('boca_cuerpo',''),
                boca_final_s=d.get('boca_final_s'),boca_balance=d.get('boca_balance',''),
                defecto_brett=d.get('defecto_brett',False),defecto_reduccion=d.get('defecto_reduccion',False),
                defecto_va_alta=d.get('defecto_va_alta',False),defecto_oxidacion=d.get('defecto_oxidacion',False),
                defecto_turbidez=d.get('defecto_turbidez',False),defecto_otro=d.get('defecto_otro',''),
                puntaje=d.get('puntaje'),conclusion=d.get('conclusion','AP'),
                accion_recomendada=d.get('accion_recomendada',''),
                observaciones=d.get('observaciones',''),usuario=d.get('usuario',''))
            if d.get('id'):
                BodCataTecnica.objects.filter(pk=d['id']).update(**defaults)
                obj = BodCataTecnica.objects.select_related('lote').get(pk=d['id'])
            else:
                defaults['lote_id'] = d['lote_id']
                obj = BodCataTecnica.objects.create(**defaults)
            return _ok({'id':obj.pk,'conclusion':obj.conclusion,'tiene_defectos':obj.tiene_defectos},
                       f'Cata guardada — {obj.get_conclusion_display()}')
        except Exception as e:
            return _err(str(e))

class BodGestionSO2View(APIView):
    def get(self, request):
        qs = BodGestionSO2.objects.select_related('lote')
        if request.query_params.get('lote_id'):
            qs = qs.filter(lote_id=request.query_params['lote_id'])
        data = [{'id':g.pk,'lote_id':g.lote_id,'lote_codigo':g.lote.codigo,
                 'fecha':g.fecha.isoformat(),'so2_libre_medido':float(g.so2_libre_medido),
                 'ph_actual':float(g.ph_actual),
                 'temperatura_bodega_c':float(g.temperatura_bodega_c) if g.temperatura_bodega_c else None,
                 'so2_molecular_objetivo':float(g.so2_molecular_objetivo),
                 'so2_molecular_actual':float(g.so2_molecular_actual) if g.so2_molecular_actual else None,
                 'so2_libre_necesario':float(g.so2_libre_necesario) if g.so2_libre_necesario else None,
                 'deficit_so2':float(g.deficit_so2) if g.deficit_so2 else None,
                 'gramos_metabisulfito':float(g.gramos_metabisulfito) if g.gramos_metabisulfito else None,
                 'adicion_realizada':g.adicion_realizada,
                 'proxima_medicion':g.proxima_medicion.isoformat() if g.proxima_medicion else None,
                 'alerta':('CRITICO' if g.so2_molecular_actual and float(g.so2_molecular_actual)<0.2
                           else 'BAJO' if g.so2_molecular_actual and float(g.so2_molecular_actual)<float(g.so2_molecular_objetivo)
                           else 'OK')} for g in qs[:200]]
        return _ok(data)
    def post(self, request):
        d = request.data
        try:
            from datetime import date, timedelta
            temp = float(d.get('temperatura_bodega_c',15))
            dias_prox = 7 if temp > 20 else 14 if temp > 14 else 21
            proxima = date.today() + timedelta(days=dias_prox)
            obj = BodGestionSO2(
                lote_id=d['lote_id'],fecha=d['fecha'],so2_libre_medido=d['so2_libre_medido'],
                ph_actual=d['ph_actual'],temperatura_bodega_c=d.get('temperatura_bodega_c'),
                so2_molecular_objetivo=d.get('so2_molecular_objetivo',0.5),
                adicion_realizada=d.get('adicion_realizada',False),
                producto_usado=d.get('producto_usado','MBK'),
                gramos_agregados_real=d.get('gramos_agregados_real'),
                metodo_medicion=d.get('metodo_medicion','Ripper'),
                proxima_medicion=d.get('proxima_medicion',proxima),
                observaciones=d.get('observaciones',''),usuario=d.get('usuario',''))
            obj.save()
            alerta = ('SO2 CRITICO' if obj.so2_molecular_actual and float(obj.so2_molecular_actual)<0.2
                      else 'SO2 bajo del objetivo' if obj.deficit_so2 and float(obj.deficit_so2)>0
                      else 'SO2 en rango')
            return _ok({'id':obj.pk,
                        'so2_molecular_actual':float(obj.so2_molecular_actual) if obj.so2_molecular_actual else 0,
                        'deficit_so2':float(obj.deficit_so2) if obj.deficit_so2 else 0,
                        'gramos_metabisulfito':float(obj.gramos_metabisulfito) if obj.gramos_metabisulfito else 0,
                        'proxima_medicion':obj.proxima_medicion.isoformat() if obj.proxima_medicion else None,
                        'alerta':alerta}, alerta)
        except Exception as e:
            return _err(str(e))

class BodCalculadoraSO2View(APIView):
    def get(self, request):
        try:
            libre = float(request.query_params.get('libre',0))
            ph = float(request.query_params.get('ph',3.5))
            obj_mol = float(request.query_params.get('objetivo_molecular',0.5))
            litros = float(request.query_params.get('litros',1000))
            factor = 1 + 10**(ph - 1.81)
            molecular_actual = round(libre / factor, 3)
            libre_necesario = round(obj_mol * factor, 2)
            deficit = round(max(0, libre_necesario - libre), 2)
            g_so2 = deficit * litros / 1000
            return _ok({'so2_molecular_actual':molecular_actual,'so2_libre_necesario':libre_necesario,
                        'deficit_so2':deficit,'gramos_so2_puro':round(g_so2,2),
                        'gramos_metabisulfito_k':round(g_so2/0.57,1),
                        'estado':'CRITICO' if molecular_actual<0.2 else 'BAJO' if molecular_actual<obj_mol else 'OK'})
        except Exception as e:
            return _err(str(e))