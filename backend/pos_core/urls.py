from django.contrib import admin
from django.urls import path
from maestros.views import (
    GetArticulosJSON, GetClientesJSON, GetVendedoresJSON,
    GetPromocionesJSON, GetPromocionesDetJSON, GetKitsJSON,
    GetListasPreciosJSON, GetDescuentosJSON, GetCondIvaJSON,
    GetFormaPagoJSON, GetRubrosJSON, GetSubRubrosJSON,
    GetParametrosJSON, IngresarComprobanteVentasJSON,
    AbrirCaja, CerrarCaja, LoginUsuario, CrearUsuario, ListarUsuarios, BajaUsuario, EditarUsuario,
    ListarClientes, GuardarCliente,
    ListarArticulosABM, GuardarArticulo,
    ListarProveedores, GuardarProveedor,
    ListarFormasPago, GuardarFormaPago,
    InformeTotalesCondicion, InformeTotalesVendedor,
    ListarRubros, GuardarRubro, ListarSubRubros, GuardarSubRubro,
    ObtenerEstadoCaja,
    ListarCompras, IngresarComprobanteComprasJSON,
    BuscarComprobanteCompra, AnularComprobanteCompra,
    ResumenCtaCteCliente, InsertarReciboCtaCte,
    ObtenerDeudaCliente, EmitirRecibo, AnularRecibo,
    ActualizarListaPrecio, InsertarNuevaPromo,
    InsertarNuevCausa, ActualizarCausa,
    ListarCausasEmision, RegistrarEntradaStock, RegistrarSalidaStock,
    InformeLibroIVAVentas, InformeRentabilidadArticulos, InformeHistorialCajas,
    InformeStockActual, InformeCtaCteClientes, InformeMovimientosStock, InformeEgresos,
    GestionarParametros, GestionarTipocompCli,
    BuscarComprobanteVenta, AnularComprobanteVenta, UltimosComprobantesVenta,
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

    # ── Ventas ────────────────────────────────────────────────────────────────
    path('api/IngresarComprobanteVentasJSON/', IngresarComprobanteVentasJSON, name='IngresarComprobanteVentasJSON'),
    path('api/BuscarComprobanteVenta/',        BuscarComprobanteVenta,        name='BuscarComprobanteVenta'),
    path('api/AnularComprobanteVenta/',        AnularComprobanteVenta,        name='AnularComprobanteVenta'),
    path('api/UltimosComprobantesVenta/',      UltimosComprobantesVenta,      name='UltimosComprobantesVenta'),

    # ── Cajas ─────────────────────────────────────────────────────────────────
    path('api/AbrirCaja/',    AbrirCaja,          name='AbrirCaja'),
    path('api/CerrarCaja/',   CerrarCaja,         name='CerrarCaja'),
    path('api/EstadoCaja/',   ObtenerEstadoCaja,  name='EstadoCaja'),

    # ── Auth / Usuarios ───────────────────────────────────────────────────────
    path('api/Login/',         LoginUsuario,  name='Login'),
    path('api/CrearUsuario/',  CrearUsuario,  name='CrearUsuario'),
    path('api/ListarUsuarios/',ListarUsuarios,name='ListarUsuarios'),
    path('api/BajaUsuario/',   BajaUsuario,   name='BajaUsuario'),
    path('api/EditarUsuario/', EditarUsuario, name='EditarUsuario'),

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

    # ── Proveedores / Formas de Pago ──────────────────────────────────────────
    path('api/ListarProveedores/', ListarProveedores, name='ListarProveedores'),
    path('api/GuardarProveedor/',  GuardarProveedor,  name='GuardarProveedor'),
    path('api/ListarFormasPago/',  ListarFormasPago,  name='ListarFormasPago'),
    path('api/GuardarFormaPago/',  GuardarFormaPago,  name='GuardarFormaPago'),

    # ── Compras ───────────────────────────────────────────────────────────────
    path('api/ListarCompras/',                ListarCompras,                name='ListarCompras'),
    path('api/IngresarComprobanteComprasJSON/', IngresarComprobanteComprasJSON, name='IngresarComprobanteComprasJSON'),
    path('api/BuscarComprobanteCompra/',      BuscarComprobanteCompra,      name='BuscarComprobanteCompra'),
    path('api/AnularComprobanteCompra/',      AnularComprobanteCompra,      name='AnularComprobanteCompra'),

    # ── Cta. Cte. ─────────────────────────────────────────────────────────────
    path('api/ResumenCtaCteCliente/', ResumenCtaCteCliente, name='ResumenCtaCteCliente'),
    path('api/InsertarReciboCtaCte/', InsertarReciboCtaCte, name='InsertarReciboCtaCte'),
    path('api/ObtenerDeudaCliente/',  ObtenerDeudaCliente,  name='ObtenerDeudaCliente'),
    path('api/EmitirRecibo/',         EmitirRecibo,         name='EmitirRecibo'),
    path('api/AnularRecibo/',         AnularRecibo,         name='AnularRecibo'),

    # ── Listas de Precios / Promos ────────────────────────────────────────────
    path('api/ActualizarListaPrecio/', ActualizarListaPrecio, name='ActualizarListaPrecio'),
    path('api/InsertarNuevaPromo/',    InsertarNuevaPromo,    name='InsertarNuevaPromo'),

    # ── Informes ──────────────────────────────────────────────────────────────
    path('api/InformeTotalesCondicion/',      InformeTotalesCondicion,      name='InformeTotalesCondicion'),
    path('api/InformeTotalesVendedor/',       InformeTotalesVendedor,       name='InformeTotalesVendedor'),
    path('api/InformeLibroIVAVentas/',        InformeLibroIVAVentas,        name='InformeLibroIVAVentas'),
    path('api/InformeRentabilidadArticulos/', InformeRentabilidadArticulos, name='InformeRentabilidadArticulos'),
    path('api/InformeHistorialCajas/',        InformeHistorialCajas,        name='InformeHistorialCajas'),
    path('api/InformeStockActual/',           InformeStockActual,           name='InformeStockActual'),
    path('api/InformeCtaCteClientes/',        InformeCtaCteClientes,        name='InformeCtaCteClientes'),
    path('api/InformeMovimientosStock/',      InformeMovimientosStock,      name='InformeMovimientosStock'),
    path('api/InformeEgresos/',               InformeEgresos,               name='InformeEgresos'),

    # ── Parámetros / Gestión ──────────────────────────────────────────────────
    path('api/GestionarParametros/',  GestionarParametros,  name='GestionarParametros'),
    path('api/GestionarTipocompCli/', GestionarTipocompCli, name='GestionarTipocompCli'),

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