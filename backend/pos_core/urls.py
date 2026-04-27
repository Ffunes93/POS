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
    # Parámetros
    GestionarParametros, GestionarTipocompCli,
    ActualizarListaPrecio, InsertarNuevaPromo,
    # Dashboard
    ObtenerDashboard,
    # Contabilidad
    SincronizarAsientos, ListarPlanCuentas, GuardarCuenta,
    ListarAsientos, ObtenerAsiento, CrearAsientoManual, AnularAsientoManual,
    InformeLibroDiario, InformeMayorCuenta,
    InformeBalanceSumasYSaldos, InformeEstadoResultados, InformeBalanceGeneral,
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

    # ── Contabilidad ──────────────────────────────────────────────────────────
    path('api/contab/Sincronizar/',          SincronizarAsientos,        name='SincronizarAsientos'),
    path('api/contab/PlanCuentas/',          ListarPlanCuentas,          name='ListarPlanCuentas'),
    path('api/contab/GuardarCuenta/',        GuardarCuenta,              name='GuardarCuenta'),
    path('api/contab/Asientos/',             ListarAsientos,             name='ListarAsientos'),
    path('api/contab/Asientos/<int:asiento_id>/', ObtenerAsiento,        name='ObtenerAsiento'),
    path('api/contab/CrearAsiento/',         CrearAsientoManual,         name='CrearAsientoManual'),
    path('api/contab/AnularAsiento/',        AnularAsientoManual,        name='AnularAsientoManual'),
    path('api/contab/LibroDiario/',          InformeLibroDiario,         name='InformeLibroDiario'),
    path('api/contab/MayorCuenta/',          InformeMayorCuenta,         name='InformeMayorCuenta'),
    path('api/contab/BalanceSumasYSaldos/',  InformeBalanceSumasYSaldos, name='InformeBalanceSumasYSaldos'),
    path('api/contab/EstadoResultados/',     InformeEstadoResultados,    name='InformeEstadoResultados'),
    path('api/contab/BalanceGeneral/',       InformeBalanceGeneral,      name='InformeBalanceGeneral'),
]