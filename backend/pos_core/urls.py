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
    # Contabilidad
    SincronizarAsientos, ListarPlanCuentas, GuardarCuenta,
    ListarAsientos, ObtenerAsiento, CrearAsientoManual, AnularAsientoManual,
    InformeLibroDiario, InformeMayorCuenta,
    InformeBalanceSumasYSaldos, InformeEstadoResultados, InformeBalanceGeneral,
    # ── NUEVOS ────────────────────────────────────────────────────────────────
    # Kits / Combos BOM
    ListarKits, GuardarKit, EliminarKit,
    # Promociones
    ListarPromociones, GuardarPromocion, TogglePromocion,
    AgregarArticuloPromo, EliminarArticuloPromo,
    # Factura Electrónica AFIP
    EstadoFE, SolicitarCAEManual, ListarSinCAE,
    ProbarConexionAFIP, GuardarConfigFE,
)
from maestros.views.restaurante import (
    GestionSectores, ObtenerPlano, ActualizarMesa, CrearMesa,
    AbrirMesa, ObtenerPedido,
    AgregarItem, QuitarItem, EnviarCocina,
    PedirCuenta, FacturarMesa, CancelarPedido,
    VistaComanda, MarcarListoItem, MarcarListoPedido,
    HistorialPedidos, ObtenerCartaMenu,
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
    path('api/ListarCotizaciones/',   ListarCotizaciones),
    path('api/ObtenerCotizacion/<int:movim>/', ObtenerCotizacion),
    path('api/GuardarCotizacion/',    GuardarCotizacion),
    path('api/AnularCotizacion/',     AnularCotizacion),
    path('api/UtilizarCotizacion/',   UtilizarCotizacion),

    # ── Cajas ─────────────────────────────────────────────────────────────────
    path('api/AbrirCaja/',           AbrirCaja),
    path('api/CerrarCaja/',          CerrarCaja),
    path('api/EstadoCaja/',          ObtenerEstadoCaja),
    path('api/RegistrarRetiroCaja/', RegistrarRetiroCaja),
    path('api/ListarRetirosCaja/',   ListarRetirosCaja),

    # ── Auth / Usuarios ───────────────────────────────────────────────────────
    path('api/Login/',          LoginUsuario),
    path('api/CrearUsuario/',   CrearUsuario),
    path('api/ListarUsuarios/', ListarUsuarios),
    path('api/BajaUsuario/',    BajaUsuario),
    path('api/EditarUsuario/',  EditarUsuario),

    # ── Clientes ──────────────────────────────────────────────────────────────
    path('api/ListarClientes/', ListarClientes),
    path('api/GuardarCliente/', GuardarCliente),

    # ── Artículos / Rubros ────────────────────────────────────────────────────
    path('api/ListarArticulosABM/', ListarArticulosABM),
    path('api/GuardarArticulo/',    GuardarArticulo),
    path('api/ListarRubros/',       ListarRubros),
    path('api/GuardarRubro/',       GuardarRubro),
    path('api/ListarSubRubros/',    ListarSubRubros),
    path('api/GuardarSubRubro/',    GuardarSubRubro),

    # ── Stock ─────────────────────────────────────────────────────────────────
    path('api/ListarCausasEmision/',   ListarCausasEmision),
    path('api/RegistrarEntradaStock/', RegistrarEntradaStock),
    path('api/RegistrarSalidaStock/',  RegistrarSalidaStock),
    path('api/InsertarNuevCausa/',     InsertarNuevCausa),
    path('api/ActualizarCausa/',       ActualizarCausa),

    # ── Kits / Combos BOM ─────────────────────────────────────────────────────
    path('api/ListarKits/',          ListarKits),
    path('api/GuardarKit/',          GuardarKit),
    path('api/EliminarKit/',         EliminarKit),

    # ── Promociones ───────────────────────────────────────────────────────────
    path('api/ListarPromociones/',       ListarPromociones),
    path('api/GuardarPromocion/',        GuardarPromocion),
    path('api/TogglePromocion/',         TogglePromocion),
    path('api/AgregarArticuloPromo/',    AgregarArticuloPromo),
    path('api/EliminarArticuloPromo/',   EliminarArticuloPromo),

    # ── Proveedores / Formas de pago ──────────────────────────────────────────
    path('api/ListarProveedores/', ListarProveedores),
    path('api/GuardarProveedor/',  GuardarProveedor),
    path('api/ListarFormasPago/',  ListarFormasPago),
    path('api/GuardarFormaPago/',  GuardarFormaPago),

    # ── Compras ───────────────────────────────────────────────────────────────
    path('api/ListarCompras/',                  ListarCompras),
    path('api/IngresarComprobanteComprasJSON/', IngresarComprobanteComprasJSON),
    path('api/BuscarComprobanteCompra/',        BuscarComprobanteCompra),
    path('api/AnularComprobanteCompra/',        AnularComprobanteCompra),

    # ── CTA CTE Clientes ──────────────────────────────────────────────────────
    path('api/ResumenCtaCteCliente/', ResumenCtaCteCliente),
    path('api/InsertarReciboCtaCte/', InsertarReciboCtaCte),
    path('api/ObtenerDeudaCliente/',  ObtenerDeudaCliente),
    path('api/EmitirRecibo/',         EmitirRecibo),
    path('api/AnularRecibo/',         AnularRecibo),

    # ── CTA CTE Proveedores ───────────────────────────────────────────────────
    path('api/ResumenCtaCteProveedores/', ResumenCtaCteProveedores),
    path('api/ObtenerDeudaProveedor/',   ObtenerDeudaProveedor),
    path('api/RegistrarPagoProveedor/',  RegistrarPagoProveedor),
    path('api/HistorialPagosProveedor/', HistorialPagosProveedor),

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
    path('api/GestionarParametros/',  GestionarParametros),
    path('api/GestionarTipocompCli/', GestionarTipocompCli),
    path('api/ActualizarListaPrecio/', ActualizarListaPrecio),
    path('api/InsertarNuevaPromo/',    InsertarNuevaPromo),

    # ── Factura Electrónica AFIP ──────────────────────────────────────────────
    path('api/fe/Estado/',          EstadoFE),
    path('api/fe/ProbarConexion/',  ProbarConexionAFIP),
    path('api/fe/SolicitarCAE/',    SolicitarCAEManual),
    path('api/fe/ListarSinCAE/',    ListarSinCAE),
    path('api/fe/GuardarConfig/',   GuardarConfigFE),

    # ── Contabilidad ──────────────────────────────────────────────────────────
    path('api/contab/Sincronizar/',          SincronizarAsientos),
    path('api/contab/PlanCuentas/',          ListarPlanCuentas),
    path('api/contab/GuardarCuenta/',        GuardarCuenta),
    path('api/contab/Asientos/',             ListarAsientos),
    path('api/contab/Asientos/<int:asiento_id>/', ObtenerAsiento),
    path('api/contab/CrearAsiento/',         CrearAsientoManual),
    path('api/contab/AnularAsiento/',        AnularAsientoManual),
    path('api/contab/LibroDiario/',          InformeLibroDiario),
    path('api/contab/MayorCuenta/',          InformeMayorCuenta),
    path('api/contab/BalanceSumasYSaldos/',  InformeBalanceSumasYSaldos),
    path('api/contab/EstadoResultados/',     InformeEstadoResultados),
    path('api/contab/BalanceGeneral/',       InformeBalanceGeneral),

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

]
