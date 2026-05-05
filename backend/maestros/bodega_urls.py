"""
bodega_urls.py — URLs del módulo Bodega.
Incluir en pos_core/urls.py:
    path('api/bodega/', include('maestros.bodega_urls')),
"""
from django.urls import path
from maestros.views.bodega import (
    # Dashboard
    BodDashboardView,
    # Fase 1 — Proceso fermentativo, cata, SO₂
    BodFermentacionDiariaView, BodCurvaFermentacionView,
    BodRemontajesView,
    BodFMLView,
    BodCatasTecnicasView,
    BodGestionSO2View, BodCalculadoraSO2View,
    # Catálogos
    BodVarietalesView, BodInsumosView,
    # Viñedo
    BodParcelasView, BodMaduracionView,
    BodLaboresCulturalesView, BodTratamientosFitosanitariosView,
    BodContratosUvaView, BodLiquidacionesUvaView,
    # Recepción
    BodTicketsBasculaView, BodAsignarTicketLoteView,
    # Depósitos
    BodRecipientesView,
    # Lotes y movimientos
    BodLotesGranelView, BodMovimientosGranelView,
    # Elaboración
    BodOperacionesEnologicasView,
    BodOrdenesElaboracionView, BodBalanceMasaView,
    # Laboratorio
    BodAnalisisView,
    # Calidad
    BodFichasProductoView, BodNoConformidadesView,
    # Barricas
    BodBarricasView, BodAsignacionBarricasView,
    # Embotellado
    BodOrdenesEmbotelladoView, BodConfirmarEmbotelladoView,
    # Costos
    BodCostosView,
    # Trazabilidad
    BodTrazabilidadView,
    # Fiscal / INV
    BodDeclaracionesINVView, BodGuiasTrasladoView, BodCertificadosAnalisisView,
    # NUEVO: Libro de bodega INV
    BodLibroBodegaView,
)

urlpatterns = [
    # Dashboard
    path('dashboard/',                      BodDashboardView.as_view()),

    # Catálogos
    path('varietales/',                     BodVarietalesView.as_view()),
    path('insumos/',                        BodInsumosView.as_view()),

    # Viñedo
    path('parcelas/',                       BodParcelasView.as_view()),
    path('maduracion/',                     BodMaduracionView.as_view()),
    path('labores/',                        BodLaboresCulturalesView.as_view()),
    path('tratamientos/',                   BodTratamientosFitosanitariosView.as_view()),
    path('contratos-uva/',                  BodContratosUvaView.as_view()),
    path('liquidaciones-uva/',              BodLiquidacionesUvaView.as_view()),

    # Recepción
    path('tickets-bascula/',                BodTicketsBasculaView.as_view()),
    path('tickets-bascula/asignar/',        BodAsignarTicketLoteView.as_view()),

    # Depósitos
    path('recipientes/',                    BodRecipientesView.as_view()),

    # Lotes y movimientos
    path('lotes/',                          BodLotesGranelView.as_view()),
    path('movimientos/',                    BodMovimientosGranelView.as_view()),

    # Elaboración
    path('operaciones/',                    BodOperacionesEnologicasView.as_view()),
    path('ordenes-elaboracion/',            BodOrdenesElaboracionView.as_view()),
    path('balance-masa/',                   BodBalanceMasaView.as_view()),

    # Laboratorio
    path('analisis/',                       BodAnalisisView.as_view()),

    # Calidad
    path('fichas-producto/',                BodFichasProductoView.as_view()),
    path('no-conformidades/',               BodNoConformidadesView.as_view()),

    # Barricas
    path('barricas/',                       BodBarricasView.as_view()),
    path('barricas/asignaciones/',          BodAsignacionBarricasView.as_view()),

    # Embotellado
    path('embotellado/',                    BodOrdenesEmbotelladoView.as_view()),
    path('embotellado/confirmar/',          BodConfirmarEmbotelladoView.as_view()),

    # Costos
    path('costos/',                         BodCostosView.as_view()),

    # Trazabilidad
    path('trazabilidad/',                   BodTrazabilidadView.as_view()),

    # Fiscal / INV
    path('declaraciones-inv/',              BodDeclaracionesINVView.as_view()),
    path('guias-traslado/',                 BodGuiasTrasladoView.as_view()),
    path('certificados-analisis/',          BodCertificadosAnalisisView.as_view()),
    # NUEVO — libro de bodega consolidado
    path('libro-bodega/',                   BodLibroBodegaView.as_view()),

    # Fase 1 — Fermentación
    path('fermentacion/',                   BodFermentacionDiariaView.as_view()),
    path('fermentacion/curva/',             BodCurvaFermentacionView.as_view()),
    path('remontajes/',                     BodRemontajesView.as_view()),
    path('fml/',                            BodFMLView.as_view()),

    # Fase 1 — Cata
    path('catas/',                          BodCatasTecnicasView.as_view()),

    # Fase 1 — SO₂
    path('so2/',                            BodGestionSO2View.as_view()),
    path('so2/calculadora/',                BodCalculadoraSO2View.as_view()),
]