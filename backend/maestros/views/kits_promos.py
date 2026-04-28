"""
kits_promos.py — ABM de Kits (Combos BOM) y Promociones (N lleva M paga).

Migrado desde:
  DatArticulos_Bom.cs   → kits
  DatArticulos_Promo.cs → promos

Tablas:
  articulos_bom  (cod_padre, cod_hijo, cant_hijo)
  promos         (id, nombre_promo, no_activa, lleva, paga, no_paga_porcentaje,
                  desde, hasta, lunes..domingo)
  promos_det     (cod_promo, cod_art)
"""
from decimal import Decimal
from django.db import connection
from django.db.models import Q, F
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import (
    ArticulosBom, Articulos,
    Promos, PromosDet,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _art_info(cod_art: str) -> dict:
    a = Articulos.objects.filter(cod_art=cod_art).values(
        'cod_art', 'nombre', 'precio_1', 'stock'
    ).first()
    return a or {}


# ════════════════════════════════════════════════════════════════════════════════
# KITS / COMBOS BOM
# ════════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
def ListarKits(request):
    """
    Devuelve todos los artículos padres (es_combo=1 o que tienen hijos en BOM).
    Con sus ítems hijos y totales.
    """
    buscar = request.query_params.get('buscar', '')

    # Artículos que son padres (es_combo=1) o tienen filas en articulos_bom
    qs_padres = Articulos.objects.filter(
        Q(es_combo=1) | Q(cod_art__in=ArticulosBom.objects.values('cod_padre'))
    )
    if buscar:
        qs_padres = qs_padres.filter(
            Q(nombre__icontains=buscar) | Q(cod_art__icontains=buscar)
        )

    result = []
    for art in qs_padres.order_by('nombre')[:200]:
        hijos = list(
            ArticulosBom.objects.filter(cod_padre=art.cod_art).values(
                'id', 'cod_hijo', 'cant_hijo'
            )
        )
        # enriquecer hijos con nombre y precio
        for h in hijos:
            info = _art_info(h['cod_hijo'])
            h['nombre_hijo'] = info.get('nombre', '')
            h['precio_hijo'] = float(info.get('precio_1') or 0)
            h['stock_hijo']  = float(info.get('stock') or 0)
            h['cant_hijo']   = float(h['cant_hijo'])

        result.append({
            'cod_art':  art.cod_art,
            'nombre':   art.nombre,
            'precio_1': float(art.precio_1 or 0),
            'stock':    float(art.stock or 0),
            'es_combo': art.es_combo,
            'hijos':    hijos,
        })

    return Response({'status': 'success', 'data': result})


@api_view(['POST'])
def GuardarKit(request):
    """
    Crea/actualiza el BOM de un artículo padre.

    Payload:
    {
      "cod_padre": "KIT001",
      "hijos": [
        { "cod_hijo": "ART001", "cant_hijo": 2 },
        { "cod_hijo": "ART002", "cant_hijo": 1 }
      ]
    }
    Reemplaza todos los hijos existentes del padre.
    """
    cod_padre = request.data.get('cod_padre', '').strip()
    hijos     = request.data.get('hijos', [])

    if not cod_padre:
        return Response({'status': 'error', 'mensaje': 'cod_padre requerido.'}, status=400)

    padre = Articulos.objects.filter(cod_art=cod_padre).first()
    if not padre:
        return Response({'status': 'error', 'mensaje': f'Artículo {cod_padre} no encontrado.'}, status=404)

    if not hijos:
        return Response({'status': 'error', 'mensaje': 'Debe incluir al menos un hijo.'}, status=400)

    try:
        # Validar hijos
        for h in hijos:
            cod = h.get('cod_hijo', '').strip()
            if not cod:
                return Response({'status': 'error', 'mensaje': 'cod_hijo vacío en un ítem.'}, status=400)
            if cod == cod_padre:
                return Response({'status': 'error', 'mensaje': 'Un artículo no puede ser hijo de sí mismo.'}, status=400)
            cant = float(h.get('cant_hijo', 0))
            if cant <= 0:
                return Response({'status': 'error', 'mensaje': f'Cantidad inválida para {cod}.'}, status=400)

        # Elimina BOM anterior y recrea
        ArticulosBom.objects.filter(cod_padre=cod_padre).delete()
        now = timezone.now()
        for h in hijos:
            ArticulosBom.objects.create(
                cod_padre=cod_padre,
                cod_hijo=h['cod_hijo'].strip(),
                cant_hijo=Decimal(str(h['cant_hijo'])),
                usuario=request.data.get('usuario', 'admin'),
                fecha_mod=now,
            )

        # Marca el padre como combo
        Articulos.objects.filter(cod_art=cod_padre).update(
            es_combo=1,
            existe_en_algun_kit=1,
        )
        # Actualiza hijos: existe_en_algun_kit = 1
        for h in hijos:
            Articulos.objects.filter(cod_art=h['cod_hijo']).update(existe_en_algun_kit=1)

        return Response({
            'status':  'success',
            'mensaje': f'Kit para {cod_padre} guardado con {len(hijos)} componentes.',
        })
    except Exception as e:
        return Response({'status': 'error', 'mensaje': str(e)}, status=500)


@api_view(['POST'])
def EliminarKit(request):
    """Elimina todos los hijos de un kit y desmarca es_combo."""
    cod_padre = request.data.get('cod_padre', '').strip()
    if not cod_padre:
        return Response({'status': 'error', 'mensaje': 'cod_padre requerido.'}, status=400)

    deleted, _ = ArticulosBom.objects.filter(cod_padre=cod_padre).delete()
    Articulos.objects.filter(cod_art=cod_padre).update(es_combo=0)
    return Response({'status': 'success', 'mensaje': f'Kit eliminado ({deleted} componentes).'})


# ════════════════════════════════════════════════════════════════════════════════
# PROMOCIONES  (N lleva, M paga / descuento %)
# ════════════════════════════════════════════════════════════════════════════════

def _promo_to_dict(p: Promos, con_articulos=False) -> dict:
    d = {
        'id':                p.id,
        'nombre_promo':      p.nombre_promo,
        'no_activa':         p.no_activa,
        'lleva':             p.lleva,
        'paga':              p.paga,
        'no_paga_porcentaje': p.no_paga_porcentaje,
        'codigo_erp':        p.codigo_erp,
        'acumulable':        p.acumulable,
        'desde':             str(p.desde) if p.desde else None,
        'hasta':             str(p.hasta) if p.hasta else None,
        'dias': {
            'lunes':   p.lunes,
            'martes':  p.martes,
            'miercoles': p.miercoles,
            'jueves':  p.jueves,
            'viernes': p.viernes,
            'sabado':  p.sabado,
            'domingo': p.domingo,
        },
    }
    if con_articulos:
        arts = list(PromosDet.objects.filter(cod_promo=p.id).values('id', 'cod_art'))
        for a in arts:
            info = _art_info(a['cod_art'])
            a['nombre'] = info.get('nombre', '')
        d['articulos'] = arts
    return d


@api_view(['GET'])
def ListarPromociones(request):
    """
    Devuelve todas las promociones con sus artículos integrantes.
    Parámetros opcionales: solo_activas=1
    """
    solo_activas = request.query_params.get('solo_activas') == '1'
    qs = Promos.objects.all()
    if solo_activas:
        qs = qs.filter(no_activa=0)
    promos = [_promo_to_dict(p, con_articulos=True) for p in qs.order_by('id')]
    return Response({'status': 'success', 'data': promos})


@api_view(['POST'])
def GuardarPromocion(request):
    """
    Crea o actualiza una promoción.

    Payload:
    {
      "id": null,                  // null=nueva, número=editar
      "nombre_promo": "3x2 Gaseosas",
      "lleva": 3,
      "paga": 2,
      "no_paga_porcentaje": 0,     // 0=precio libre, >0=% descuento sobre el que no paga
      "no_activa": 0,
      "acumulable": 0,
      "desde": "2026-01-01",
      "hasta": "2026-12-31",
      "dias": {"lunes":1,"martes":1,"miercoles":1,"jueves":1,"viernes":1,"sabado":1,"domingo":1},
      "articulos": ["ART001","ART002"]
    }
    """
    data      = request.data
    promo_id  = data.get('id')
    articulos = data.get('articulos', [])
    dias      = data.get('dias', {})

    if not data.get('nombre_promo'):
        return Response({'status': 'error', 'mensaje': 'nombre_promo requerido.'}, status=400)

    lleva = int(data.get('lleva', 1))
    paga  = int(data.get('paga', 1))
    if paga >= lleva:
        return Response({'status': 'error', 'mensaje': 'paga debe ser menor que lleva.'}, status=400)

    try:
        if promo_id:
            promo = Promos.objects.filter(id=promo_id).first()
            if not promo:
                return Response({'status': 'error', 'mensaje': 'Promoción no encontrada.'}, status=404)
            accion = 'actualizada'
        else:
            # Obtener próximo ID
            from django.db.models import Max
            max_id = Promos.objects.aggregate(m=Max('id'))['m'] or 0
            promo  = Promos(id=max_id + 1)
            accion = 'creada'

        promo.nombre_promo        = str(data['nombre_promo'])[:50]
        promo.no_activa           = int(data.get('no_activa', 0))
        promo.lleva               = lleva
        promo.paga                = paga
        promo.no_paga_porcentaje  = int(data.get('no_paga_porcentaje', 0))
        promo.acumulable          = int(data.get('acumulable', 0))
        promo.codigo_erp          = str(data.get('codigo_erp', '') or '')[:50]
        promo.desde               = data.get('desde') or None
        promo.hasta               = data.get('hasta') or None
        promo.lunes    = int(dias.get('lunes',    1))
        promo.martes   = int(dias.get('martes',   1))
        promo.miercoles= int(dias.get('miercoles',1))
        promo.jueves   = int(dias.get('jueves',   1))
        promo.viernes  = int(dias.get('viernes',  1))
        promo.sabado   = int(dias.get('sabado',   1))
        promo.domingo  = int(dias.get('domingo',  1))
        promo.save()

        # Reemplazar artículos integrantes
        if articulos is not None:
            PromosDet.objects.filter(cod_promo=promo.id).delete()
            now = timezone.now()
            for cod in articulos:
                cod = str(cod).strip()
                if cod:
                    PromosDet.objects.create(
                        cod_promo=promo.id,
                        cod_art=cod,
                        usuario=data.get('usuario', 'admin'),
                        fecha_mod=now,
                    )
            # Actualiza existe_en_alguna_promo en artículos
            Articulos.objects.filter(cod_art__in=articulos).update(existe_en_alguna_promo=1)

        return Response({
            'status':  'success',
            'mensaje': f'Promoción N° {promo.id} {accion}.',
            'id':      promo.id,
        })
    except Exception as e:
        return Response({'status': 'error', 'mensaje': str(e)}, status=500)


@api_view(['POST'])
def TogglePromocion(request):
    """Activa o desactiva una promoción."""
    promo_id = request.data.get('id')
    try:
        promo = Promos.objects.get(id=promo_id)
        promo.no_activa = 0 if promo.no_activa else 1
        promo.save(update_fields=['no_activa'])
        estado = 'desactivada' if promo.no_activa else 'activada'
        return Response({'status': 'success', 'mensaje': f'Promoción {estado}.', 'no_activa': promo.no_activa})
    except Promos.DoesNotExist:
        return Response({'status': 'error', 'mensaje': 'Promoción no encontrada.'}, status=404)
    except Exception as e:
        return Response({'status': 'error', 'mensaje': str(e)}, status=500)


@api_view(['POST'])
def AgregarArticuloPromo(request):
    """Agrega un artículo a una promoción."""
    promo_id = request.data.get('id')
    cod_art  = request.data.get('cod_art', '').strip()
    if not promo_id or not cod_art:
        return Response({'status': 'error', 'mensaje': 'Faltan id y cod_art.'}, status=400)

    if PromosDet.objects.filter(cod_promo=promo_id, cod_art=cod_art).exists():
        return Response({'status': 'error', 'mensaje': 'El artículo ya integra esta promoción.'}, status=400)

    try:
        det = PromosDet.objects.create(
            cod_promo=promo_id, cod_art=cod_art,
            usuario=request.data.get('usuario', 'admin'), fecha_mod=timezone.now(),
        )
        Articulos.objects.filter(cod_art=cod_art).update(existe_en_alguna_promo=1)
        info = _art_info(cod_art)
        return Response({'status': 'success', 'id': det.id, 'nombre': info.get('nombre', '')})
    except Exception as e:
        return Response({'status': 'error', 'mensaje': str(e)}, status=500)


@api_view(['POST'])
def EliminarArticuloPromo(request):
    """Elimina un artículo de una promoción por id de promos_det."""
    det_id = request.data.get('det_id')
    try:
        PromosDet.objects.filter(id=det_id).delete()
        return Response({'status': 'success', 'mensaje': 'Artículo eliminado de la promoción.'})
    except Exception as e:
        return Response({'status': 'error', 'mensaje': str(e)}, status=500)