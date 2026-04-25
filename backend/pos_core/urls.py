from django.contrib import admin
from django.urls import path

from maestros.views import (
    # ── Sincronización / Catálogos ────────────────────────────────────────
    GetArticulosJSON,
    GetClientesJSON,
    GetVendedoresJSON,
    GetPromocionesJSON,
    GetPromocionesDetJSON,
    GetKitsJSON,
    GetListasPreciosJSON,
    GetDescuentosJSON,
    GetCondIvaJSON,
    GetFormaPagoJSON,
    GetRubrosJSON,
    GetSubRubrosJSON,
    GetParametrosJSON,
    # ── Auth / Usuarios ───────────────────────────────────────────────────
    LoginUsuario,
    CrearUsuario,
    ListarUsuarios,
    BajaUsuario,
    EditarUsuario,
    # ── Cajas ─────────────────────────────────────────────────────────────
    AbrirCaja,
    ObtenerEstadoCaja,
    CerrarCaja,
    # ── Ventas ────────────────────────────────────────────────────────────
    IngresarComprobanteVentasJSON,
    UltimosComprobantesVenta,
    BuscarComprobanteVenta,
    AnularComprobanteVenta,
    # ── Clientes ──────────────────────────────────────────────────────────
    ListarClientes,
    GuardarCliente,
    # ── Stock ─────────────────────────────────────────────────────────────
    ListarArticulosABM,
    GuardarArticulo,
    ListarRubros,
    GuardarRubro,
    ListarSubRubros,
    GuardarSubRubro,
    InsertarNuevCausa,
    ActualizarCausa,
    # ── Compras / Proveedores ─────────────────────────────────────────────
    ListarProveedores,
    GuardarProveedor,
    ListarCompras,
    IngresarComprobanteComprasJSON,
    # ── Cuenta Corriente ──────────────────────────────────────────────────
    ResumenCtaCteCliente,
    InsertarReciboCtaCte,
    # ── Informes ──────────────────────────────────────────────────────────
    InformeTotalesCondicion,
    InformeTotalesVendedor,
    InformeLibroIVAVentas,
    InformeRentabilidadArticulos,
    InformeHistorialCajas,
    # ── Configuración ─────────────────────────────────────────────────────
    GestionarParametros,
    GestionarTipocompCli,
    ListarFormasPago,
    GuardarFormaPago,
    ActualizarListaPrecio,
    InsertarNuevaPromo,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Sincronización de catálogos (GET, usado por el frontend al iniciar) ──
    path('api/getArticulosJSON/',    GetArticulosJSON.as_view()),
    path('api/getClientesJSON/',     GetClientesJSON.as_view()),
    path('api/getVendedoresJSON/',   GetVendedoresJSON.as_view()),
    path('api/getPromocionesJSON/',  GetPromocionesJSON.as_view()),
    path('api/getPromocionesDetJSON/', GetPromocionesDetJSON.as_view()),
    path('api/getKitsJSON/',         GetKitsJSON.as_view()),
    path('api/getListaPreciosJSON/', GetListasPreciosJSON.as_view()),
    path('api/getDescuentosJSON/',   GetDescuentosJSON.as_view()),
    path('api/getCondIvaJSON/',      GetCondIvaJSON.as_view()),
    path('api/getFormaPagoJSON/',    GetFormaPagoJSON.as_view()),
    path('api/getRubrosJSON/',       GetRubrosJSON.as_view()),
    path('api/getSubRubrosJSON/',    GetSubRubrosJSON.as_view()),
    path('api/getParametrosJSON/',   GetParametrosJSON.as_view()),

    # ── Auth ─────────────────────────────────────────────────────────────────
    path('api/Login/',          LoginUsuario),
    path('api/CrearUsuario/',   CrearUsuario),
    path('api/ListarUsuarios/', ListarUsuarios),
    path('api/BajaUsuario/',    BajaUsuario),
    path('api/EditarUsuario/',  EditarUsuario),

    # ── Cajas ─────────────────────────────────────────────────────────────────
    path('api/AbrirCaja/',   AbrirCaja),
    path('api/CerrarCaja/',  CerrarCaja),
    path('api/EstadoCaja/',  ObtenerEstadoCaja),

    # ── Ventas ────────────────────────────────────────────────────────────────
    path('api/IngresarComprobanteVentasJSON/', IngresarComprobanteVentasJSON),
    path('api/UltimosComprobantesVenta/',      UltimosComprobantesVenta),
    path('api/BuscarComprobanteVenta/',        BuscarComprobanteVenta),
    path('api/AnularComprobanteVenta/',        AnularComprobanteVenta),

    # ── Clientes ──────────────────────────────────────────────────────────────
    path('api/ListarClientes/',  ListarClientes),
    path('api/GuardarCliente/',  GuardarCliente),

    # ── Stock ─────────────────────────────────────────────────────────────────
    path('api/ListarArticulosABM/', ListarArticulosABM),
    path('api/GuardarArticulo/',    GuardarArticulo),
    path('api/ListarRubros/',       ListarRubros),
    path('api/GuardarRubro/',       GuardarRubro),
    path('api/ListarSubRubros/',    ListarSubRubros),
    path('api/GuardarSubRubro/',    GuardarSubRubro),
    path('api/InsertarNuevCausa/',  InsertarNuevCausa),
    path('api/ActualizarCausa/',    ActualizarCausa),

    # ── Compras / Proveedores ─────────────────────────────────────────────────
    path('api/ListarProveedores/',             ListarProveedores),
    path('api/GuardarProveedor/',              GuardarProveedor),
    path('api/ListarCompras/',                 ListarCompras),
    path('api/IngresarComprobanteComprasJSON/', IngresarComprobanteComprasJSON),

    # ── Cuenta Corriente ──────────────────────────────────────────────────────
    path('api/ResumenCtaCteCliente/',  ResumenCtaCteCliente),
    path('api/InsertarReciboCtaCte/',  InsertarReciboCtaCte),

    # ── Informes ──────────────────────────────────────────────────────────────
    path('api/InformeTotalesCondicion/',    InformeTotalesCondicion),
    path('api/InformeTotalesVendedor/',     InformeTotalesVendedor),
    path('api/InformeLibroIVAVentas/',      InformeLibroIVAVentas),
    path('api/InformeRentabilidadArticulos/', InformeRentabilidadArticulos),
    path('api/InformeHistorialCajas/',      InformeHistorialCajas),

    # ── Configuración ─────────────────────────────────────────────────────────
    path('api/GestionarParametros/',  GestionarParametros),
    path('api/GestionarTipocompCli/', GestionarTipocompCli),
    path('api/ListarFormasPago/',     ListarFormasPago),
    path('api/GuardarFormaPago/',     GuardarFormaPago),
    path('api/ActualizarListaPrecio/', ActualizarListaPrecio),
    path('api/InsertarNuevaPromo/',   InsertarNuevaPromo),
]
