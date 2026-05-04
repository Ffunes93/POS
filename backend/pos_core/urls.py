from django.contrib import admin
from django.urls import path
from maestros.views import (
    # Sync
    GetArticulosJSON, GetClientesJSON, GetVendedoresJSON,
    GetPromocionesJSON, GetPromocionesDetJSON, GetKitsJSON,
    GetListasPreciosJSON, GetDescuentosJSON, GetCondIvaJSON,
    GetFormaPagoJSON, GetRubrosJSON, GetSubRubrosJSON, GetParametrosJSON,
    # Ventas
    IngresarComprobanteVentasJSON,
    BuscarComprobanteVenta, AnularComprobanteVenta, UltimosComprobantesVenta,
    # Cotizaciones
    ListarCotizaciones, ObtenerCotizacion,
    GuardarCotizacion, AnularCotizacion, UtilizarCotizacion,
    # Cajas
    AbrirCaja, CerrarCaja, ObtenerEstadoCaja,
    RegistrarRetiroCaja, ListarRetirosCaja,
    # Auth
    LoginUsuario, CrearUsuario, ListarUsuarios, BajaUsuario, EditarUsuario,
    # Clientes
    ListarClientes, GuardarCliente,
    # Stock
    ListarArticulosABM, GuardarArticulo,
    ListarRubros, GuardarRubro, ListarSubRubros, GuardarSubRubro,
    ListarCausasEmision, RegistrarEntradaStock, RegistrarSalidaStock,
    InsertarNuevCausa, ActualizarCausa,
    # Proveedores / Compras
    ListarProveedores, GuardarProveedor,
    ListarCompras, IngresarComprobanteComprasJSON,
    BuscarComprobanteCompra, AnularComprobanteCompra,
    # Formas de pago
    ListarFormasPago, GuardarFormaPago,
    # CTA CTE Clientes
    ResumenCtaCteCliente, InsertarReciboCtaCte,
    ObtenerDeudaCliente, EmitirRecibo, AnularRecibo,
    # CTA CTE Proveedores
    ResumenCtaCteProveedores, ObtenerDeudaProveedor,
    RegistrarPagoProveedor, HistorialPagosProveedor,
    # Informes
    InformeTotalesCondicion, InformeTotalesVendedor,
    InformeLibroIVAVentas, InformeRentabilidadArticulos,
    InformeHistorialCajas, InformeStockActual,
    InformeCtaCteClientes, InformeMovimientosStock, InformeEgresos,
    # Parámetros / Gestión
    GestionarParametros, GestionarTipocompCli,
    ActualizarListaPrecio, InsertarNuevaPromo,
    # Dashboard
    ObtenerDashboard,
    # Contabilidad — Sincronización y plan de cuentas
    SincronizarAsientos, ListarPlanCuentas, GuardarCuenta,
    # Contabilidad — CRUD Asientos
    ListarAsientos, ObtenerAsiento, CrearAsientoManual, AnularAsientoManual,
    MayorizarAsiento, AnularAsientoId,
    # Contabilidad — Operaciones automáticas
    GenerarAsientoAutomatico, ImportarAsientos,
    # Contabilidad — Consultas
    ConsultaSaldos,
    # Contabilidad — Configuración (NUEVO)
    GestionTiposAsiento, DetalleTipoAsiento,
    GestionSeries, DetalleSerie,
    GestionEjercicios, DetalleEjercicio,
    GestionModelos, DetalleModelo,
    # Contabilidad — Informes
    InformeLibroDiario, InformeMayorCuenta,
    InformeBalanceSumasYSaldos, InformeEstadoResultados, InformeBalanceGeneral,
    # Informes Impositivos
    LibrosIVA, EliminarLibroIVA, DatosLibroIVA,
    GenerarIVADigital, DeclaracionesJuradas, RectificarDDJJ, MarcarPasadoCG,
    AnalisisOperaciones, ListarExportaciones, DescargarExportacion,
    GenerarSICORE, GenerarSIFERE, GenerarExportacionGenerica,
    VentasPorPuntoDeVenta, RankingClientes, RankingProveedores,
    PuntosRegistracion, RegimenesEspeciales,)
from maestros.views.kits_promos import (
    # Kits / Combos BOM
    ListarKits, GuardarKit, EliminarKit,
    # Promociones
    ListarPromociones, GuardarPromocion, TogglePromocion,
    AgregarArticuloPromo, EliminarArticuloPromo,)
from maestros.views.factura_electronica import (
    # Factura Electrónica AFIP
    EstadoFE, SolicitarCAEManual, ListarSinCAE,
    ProbarConexionAFIP, GuardarConfigFE,)
    # Restaurante
from maestros.views.restaurante import (
    GestionSectores, ObtenerPlano, ActualizarMesa, CrearMesa,
    AbrirMesa, ObtenerPedido,
    AgregarItem, QuitarItem, EnviarCocina,
    PedirCuenta, FacturarMesa, CancelarPedido,
    VistaComanda, MarcarListoItem, MarcarListoPedido,
    HistorialPedidos, ObtenerCartaMenu,
)
from maestros.views.ia_compras import (
    ProcesarFacturaPDF, 
    ConfirmarFactura
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Sincronización de Catálogos ───────────────────────────────────────────
    path('api/getArticulosJSON/',      GetArticulosJSON.as_view()),
    path('api/getClientesJSON/',       GetClientesJSON.as_view()),
    path('api/getVendedoresJSON/',     GetVendedoresJSON.as_view()),
    path('api/getPromocionesJSON/',    GetPromocionesJSON.as_view()),
    path('api/getPromocionesDetJSON/', GetPromocionesDetJSON.as_view()),
    path('api/getKitsJSON/',           GetKitsJSON.as_view()),
    path('api/getListaPreciosJSON/',   GetListasPreciosJSON.as_view()),
    path('api/getDescuentosJSON/',     GetDescuentosJSON.as_view()),
    path('api/getCondIvaJSON/',        GetCondIvaJSON.as_view()),
    path('api/getFormaPagoJSON/',      GetFormaPagoJSON.as_view()),
    path('api/getRubrosJSON/',         GetRubrosJSON.as_view()),
    path('api/getSubRubrosJSON/',      GetSubRubrosJSON.as_view()),
    path('api/getParametrosJSON/',     GetParametrosJSON.as_view()),

    # ── Dashboard ─────────────────────────────────────────────────────────────
    path('api/Dashboard/', ObtenerDashboard, name='Dashboard'),

    # ── Ventas ────────────────────────────────────────────────────────────────
    path('api/IngresarComprobanteVentasJSON/', IngresarComprobanteVentasJSON),
    path('api/BuscarComprobanteVenta/',        BuscarComprobanteVenta),
    path('api/AnularComprobanteVenta/',        AnularComprobanteVenta),
    path('api/UltimosComprobantesVenta/',      UltimosComprobantesVenta),

    # ── Cotizaciones / Presupuestos ───────────────────────────────────────────
    path('api/ListarCotizaciones/',   ListarCotizaciones,   name='ListarCotizaciones'),
    path('api/ObtenerCotizacion/<int:movim>/', ObtenerCotizacion, name='ObtenerCotizacion'),
    path('api/GuardarCotizacion/',    GuardarCotizacion,    name='GuardarCotizacion'),
    path('api/AnularCotizacion/',     AnularCotizacion,     name='AnularCotizacion'),
    path('api/UtilizarCotizacion/',   UtilizarCotizacion,   name='UtilizarCotizacion'),

    # ── Cajas ─────────────────────────────────────────────────────────────────
    path('api/AbrirCaja/',           AbrirCaja,           name='AbrirCaja'),
    path('api/CerrarCaja/',          CerrarCaja,          name='CerrarCaja'),
    path('api/EstadoCaja/',          ObtenerEstadoCaja,   name='EstadoCaja'),
    path('api/RegistrarRetiroCaja/', RegistrarRetiroCaja, name='RegistrarRetiroCaja'),
    path('api/ListarRetirosCaja/',   ListarRetirosCaja,   name='ListarRetirosCaja'),

    # ── Auth / Usuarios ───────────────────────────────────────────────────────
    path('api/Login/',          LoginUsuario,   name='Login'),
    path('api/CrearUsuario/',   CrearUsuario,   name='CrearUsuario'),
    path('api/ListarUsuarios/', ListarUsuarios, name='ListarUsuarios'),
    path('api/BajaUsuario/',    BajaUsuario,    name='BajaUsuario'),
    path('api/EditarUsuario/',  EditarUsuario,  name='EditarUsuario'),

    # ── Clientes ──────────────────────────────────────────────────────────────
    path('api/ListarClientes/', ListarClientes, name='ListarClientes'),
    path('api/GuardarCliente/', GuardarCliente, name='GuardarCliente'),

    # ── Artículos / Rubros ────────────────────────────────────────────────────
    path('api/ListarArticulosABM/', ListarArticulosABM, name='ListarArticulosABM'),
    path('api/GuardarArticulo/',    GuardarArticulo,    name='GuardarArticulo'),
    path('api/ListarRubros/',       ListarRubros,       name='ListarRubros'),
    path('api/GuardarRubro/',       GuardarRubro,       name='GuardarRubro'),
    path('api/ListarSubRubros/',    ListarSubRubros,    name='ListarSubRubros'),
    path('api/GuardarSubRubro/',    GuardarSubRubro,    name='GuardarSubRubro'),

    # ── Stock ─────────────────────────────────────────────────────────────────
    path('api/ListarCausasEmision/',   ListarCausasEmision,   name='ListarCausasEmision'),
    path('api/RegistrarEntradaStock/', RegistrarEntradaStock, name='RegistrarEntradaStock'),
    path('api/RegistrarSalidaStock/',  RegistrarSalidaStock,  name='RegistrarSalidaStock'),
    path('api/InsertarNuevCausa/',     InsertarNuevCausa,     name='InsertarNuevCausa'),
    path('api/ActualizarCausa/',       ActualizarCausa,       name='ActualizarCausa'),

    # ── Kits / Combos BOM ─────────────────────────────────────────────────────
    path('api/ListarKits/',          ListarKits),
    path('api/GuardarKit/',          GuardarKit),
    path('api/EliminarKit/',         EliminarKit),

    # ── Promociones ───────────────────────────────────────────────────────────
    path('api/ListarPromociones/',       ListarPromociones,),
    path('api/GuardarPromocion/',        GuardarPromocion),
    path('api/TogglePromocion/',         TogglePromocion),
    path('api/AgregarArticuloPromo/',    AgregarArticuloPromo),
    path('api/EliminarArticuloPromo/',   EliminarArticuloPromo),

    # ── Proveedores / Formas de pago ──────────────────────────────────────────
    path('api/ListarProveedores/', ListarProveedores, name='ListarProveedores'),
    path('api/GuardarProveedor/',  GuardarProveedor,  name='GuardarProveedor'),
    path('api/ListarFormasPago/',  ListarFormasPago,  name='ListarFormasPago'),
    path('api/GuardarFormaPago/',  GuardarFormaPago,  name='GuardarFormaPago'),

    # ── Compras ───────────────────────────────────────────────────────────────
    path('api/ListarCompras/',                  ListarCompras,                name='ListarCompras'),
    path('api/IngresarComprobanteComprasJSON/', IngresarComprobanteComprasJSON, name='IngresarComprobanteComprasJSON'),
    path('api/BuscarComprobanteCompra/',        BuscarComprobanteCompra,      name='BuscarComprobanteCompra'),
    path('api/AnularComprobanteCompra/',        AnularComprobanteCompra,      name='AnularComprobanteCompra'),

    # ── IA Compras / Asistente AFIP ───────────────────────────────────────────
    path('api/ProcesarFacturaPDF/',             ProcesarFacturaPDF,           name='ProcesarFacturaPDF'),
    path('api/ConfirmarFactura/',               ConfirmarFactura,             name='ConfirmarFactura'),

    # ── CTA CTE Clientes ──────────────────────────────────────────────────────
    path('api/ResumenCtaCteCliente/', ResumenCtaCteCliente, name='ResumenCtaCteCliente'),
    path('api/InsertarReciboCtaCte/', InsertarReciboCtaCte, name='InsertarReciboCtaCte'),
    path('api/ObtenerDeudaCliente/',  ObtenerDeudaCliente,  name='ObtenerDeudaCliente'),
    path('api/EmitirRecibo/',         EmitirRecibo,         name='EmitirRecibo'),
    path('api/AnularRecibo/',         AnularRecibo,         name='AnularRecibo'),

    # ── CTA CTE Proveedores ───────────────────────────────────────────────────
    path('api/ResumenCtaCteProveedores/', ResumenCtaCteProveedores, name='ResumenCtaCteProveedores'),
    path('api/ObtenerDeudaProveedor/',   ObtenerDeudaProveedor,   name='ObtenerDeudaProveedor'),
    path('api/RegistrarPagoProveedor/',  RegistrarPagoProveedor,  name='RegistrarPagoProveedor'),
    path('api/HistorialPagosProveedor/', HistorialPagosProveedor, name='HistorialPagosProveedor'),

    # ── Informes ──────────────────────────────────────────────────────────────
    path('api/InformeTotalesCondicion/',      InformeTotalesCondicion),
    path('api/InformeTotalesVendedor/',       InformeTotalesVendedor),
    path('api/InformeLibroIVAVentas/',        InformeLibroIVAVentas),
    path('api/InformeRentabilidadArticulos/', InformeRentabilidadArticulos),
    path('api/InformeHistorialCajas/',        InformeHistorialCajas),
    path('api/InformeStockActual/',           InformeStockActual),
    path('api/InformeCtaCteClientes/',        InformeCtaCteClientes),
    path('api/InformeMovimientosStock/',      InformeMovimientosStock),
    path('api/InformeEgresos/',               InformeEgresos),

    # ── Parámetros / Gestión ──────────────────────────────────────────────────
    path('api/GestionarParametros/',  GestionarParametros,  name='GestionarParametros'),
    path('api/GestionarTipocompCli/', GestionarTipocompCli, name='GestionarTipocompCli'),
    path('api/ActualizarListaPrecio/', ActualizarListaPrecio, name='ActualizarListaPrecio'),
    path('api/InsertarNuevaPromo/',    InsertarNuevaPromo,    name='InsertarNuevaPromo'),

    # ── Factura Electrónica AFIP ──────────────────────────────────────────────
    path('api/fe/Estado/',          EstadoFE),
    path('api/fe/ProbarConexion/',  ProbarConexionAFIP),
    path('api/fe/SolicitarCAE/',    SolicitarCAEManual),
    path('api/fe/ListarSinCAE/',    ListarSinCAE),
    path('api/fe/GuardarConfig/',   GuardarConfigFE),

     # ── Restaurante / Gastronomía ─────────────────────────────────────────────
    path('api/rest/sectores/',               GestionSectores),
    path('api/rest/plano/',                  ObtenerPlano),
    path('api/rest/mesa/<int:mesa_id>/',     ActualizarMesa),
    path('api/rest/mesa/crear/',             CrearMesa),
    path('api/rest/abrir_mesa/',             AbrirMesa),
    path('api/rest/pedido/<int:pedido_id>/', ObtenerPedido),
    path('api/rest/agregar_item/',           AgregarItem),
    path('api/rest/quitar_item/',            QuitarItem),
    path('api/rest/enviar_cocina/',          EnviarCocina),
    path('api/rest/pedir_cuenta/',           PedirCuenta),
    path('api/rest/facturar_mesa/',          FacturarMesa),
    path('api/rest/cancelar_pedido/',        CancelarPedido),
    path('api/rest/comandas/',               VistaComanda),
    path('api/rest/marcar_listo/',           MarcarListoItem),
    path('api/rest/marcar_listo_pedido/',    MarcarListoPedido),
    path('api/rest/historial/',              HistorialPedidos),
    path('api/rest/carta_menu/',             ObtenerCartaMenu),

    # ── Contabilidad — Configuración ──────────────────────────────────────────
    path('api/contab/Ejercicios/',            GestionEjercicios,        name='GestionEjercicios'),
    path('api/contab/Ejercicios/<int:pk>/',   DetalleEjercicio,         name='DetalleEjercicio'),
    path('api/contab/TiposAsiento/',          GestionTiposAsiento,      name='GestionTiposAsiento'),
    path('api/contab/TiposAsiento/<str:pk>/', DetalleTipoAsiento,       name='DetalleTipoAsiento'),
    path('api/contab/Series/',                GestionSeries,            name='GestionSeries'),
    path('api/contab/Series/<str:pk>/',       DetalleSerie,             name='DetalleSerie'),
    path('api/contab/Modelos/',               GestionModelos,           name='GestionModelos'),
    path('api/contab/Modelos/<str:pk>/',      DetalleModelo,            name='DetalleModelo'),

    # ── Contabilidad — Plan de Cuentas ────────────────────────────────────────
    path('api/contab/PlanCuentas/',           ListarPlanCuentas,        name='ListarPlanCuentas'),
    path('api/contab/GuardarCuenta/',         GuardarCuenta,            name='GuardarCuenta'),

    # ── Contabilidad — Asientos ───────────────────────────────────────────────
    path('api/contab/Sincronizar/',           SincronizarAsientos,      name='SincronizarAsientos'),
    path('api/contab/Asientos/',              ListarAsientos,           name='ListarAsientos'),
    path('api/contab/Asientos/<int:asiento_id>/',            ObtenerAsiento,   name='ObtenerAsiento'),
    path('api/contab/Asientos/<int:asiento_id>/mayorizar/',  MayorizarAsiento, name='MayorizarAsiento'),
    path('api/contab/Asientos/<int:asiento_id>/anular/',     AnularAsientoId,  name='AnularAsientoId'),
    path('api/contab/CrearAsiento/',          CrearAsientoManual,       name='CrearAsientoManual'),
    path('api/contab/AnularAsiento/',         AnularAsientoManual,      name='AnularAsientoManual'),

    # ── Contabilidad — Operaciones automáticas ────────────────────────────────
    path('api/contab/AsientosAutomaticos/',   GenerarAsientoAutomatico, name='GenerarAsientoAutomatico'),
    path('api/contab/ImportarAsientos/',      ImportarAsientos,         name='ImportarAsientos'),

    # ── Contabilidad — Consultas ──────────────────────────────────────────────
    path('api/contab/ConsultaSaldos/',        ConsultaSaldos,           name='ConsultaSaldos'),

    # ── Contabilidad — Informes ───────────────────────────────────────────────
    path('api/contab/LibroDiario/',           InformeLibroDiario,         name='InformeLibroDiario'),
    path('api/contab/MayorCuenta/',           InformeMayorCuenta,         name='InformeMayorCuenta'),
    path('api/contab/BalanceSumasYSaldos/',   InformeBalanceSumasYSaldos, name='InformeBalanceSumasYSaldos'),
    path('api/contab/EstadoResultados/',      InformeEstadoResultados,    name='InformeEstadoResultados'),
    path('api/contab/BalanceGeneral/',        InformeBalanceGeneral,      name='InformeBalanceGeneral'),

    # Informes Impositivos:
    path('api/impositivo/libros-iva/',                LibrosIVA),
    path('api/impositivo/libros-iva/<int:libro_id>/', EliminarLibroIVA),
    path('api/impositivo/libros-iva/<int:libro_id>/datos/', DatosLibroIVA),
    path('api/impositivo/iva-digital/',               GenerarIVADigital),
    path('api/impositivo/ddjj/',                      DeclaracionesJuradas),
    path('api/impositivo/ddjj/<int:ddjj_id>/rectificar/', RectificarDDJJ),
    path('api/impositivo/ddjj/<int:ddjj_id>/pasar-cg/',   MarcarPasadoCG),
    path('api/impositivo/analisis-operaciones/',      AnalisisOperaciones),
    path('api/impositivo/exportaciones/',             ListarExportaciones),
    path('api/impositivo/exportaciones/<int:expo_id>/descargar/', DescargarExportacion),
    path('api/impositivo/exportaciones/sicore/',      GenerarSICORE),
    path('api/impositivo/exportaciones/sifere/',      GenerarSIFERE),
    path('api/impositivo/exportaciones/<str:aplicativo_slug>/', GenerarExportacionGenerica),
    path('api/impositivo/monotributistas/ventas-pdv/',        VentasPorPuntoDeVenta),
    path('api/impositivo/monotributistas/ranking-clientes/',  RankingClientes),
    path('api/impositivo/monotributistas/ranking-proveedores/', RankingProveedores),
    path('api/impositivo/puntos-registracion/',       PuntosRegistracion),
    path('api/impositivo/regimenes/',                 RegimenesEspeciales),
    
]