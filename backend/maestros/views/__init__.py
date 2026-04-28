"""
maestros/views/__init__.py  — re-exporta todas las vistas.
"""

# ── Sync / catálogos ──────────────────────────────────────────────────────────
from .sync import (  # noqa
    GetArticulosJSON, GetClientesJSON, GetVendedoresJSON,
    GetPromocionesJSON, GetPromocionesDetJSON, GetKitsJSON,
    GetListasPreciosJSON, GetDescuentosJSON, GetCondIvaJSON,
    GetFormaPagoJSON, GetRubrosJSON, GetSubRubrosJSON, GetParametrosJSON,
)

# ── Autenticación / Usuarios ──────────────────────────────────────────────────
from .auth import (  # noqa
    LoginUsuario, CrearUsuario, ListarUsuarios, BajaUsuario, EditarUsuario,
)

# ── Ventas ────────────────────────────────────────────────────────────────────
from .ventas import (  # noqa
    IngresarComprobanteVentasJSON,
    BuscarComprobanteVenta, AnularComprobanteVenta, UltimosComprobantesVenta,
)

# ── Cotizaciones / Presupuestos ────────────────────────────────────────────────
from .cotizaciones import (  # noqa
    ListarCotizaciones, ObtenerCotizacion,
    GuardarCotizacion, AnularCotizacion, UtilizarCotizacion,
)

# ── Cajas ─────────────────────────────────────────────────────────────────────
from .cajas import (  # noqa
    AbrirCaja, ObtenerEstadoCaja, CerrarCaja,
    RegistrarRetiroCaja, ListarRetirosCaja,
)

# ── Clientes ──────────────────────────────────────────────────────────────────
from .clientes import (  # noqa
    ListarClientes, GuardarCliente,
)

# ── Compras / Proveedores ─────────────────────────────────────────────────────
from .compras import (  # noqa
    ListarProveedores, GuardarProveedor,
    ListarCompras, BuscarComprobanteCompra,
    IngresarComprobanteComprasJSON, AnularComprobanteCompra,
)

# ── CTA CTE Clientes ──────────────────────────────────────────────────────────
from .cta_cte import (  # noqa
    ObtenerDeudaCliente, EmitirRecibo, AnularRecibo,
    ResumenCtaCteCliente, InsertarReciboCtaCte,
)

# ── CTA CTE Proveedores ───────────────────────────────────────────────────────
from .cta_cte_prov import (  # noqa
    ResumenCtaCteProveedores, ObtenerDeudaProveedor,
    RegistrarPagoProveedor, HistorialPagosProveedor,
)

# ── Stock ─────────────────────────────────────────────────────────────────────
from .stock import (  # noqa
    ListarArticulosABM, GuardarArticulo,
    ListarRubros, GuardarRubro, ListarSubRubros, GuardarSubRubro,
    InsertarNuevCausa, ActualizarCausa, ListarCausasEmision,
    RegistrarEntradaStock, RegistrarSalidaStock,
)

# ── Kits / Combos BOM ─────────────────────────────────────────────────────────
from .kits_promos import (  # noqa
    ListarKits, GuardarKit, EliminarKit,
    ListarPromociones, GuardarPromocion, TogglePromocion,
    AgregarArticuloPromo, EliminarArticuloPromo,
)

# ── Factura Electrónica AFIP ──────────────────────────────────────────────────
from .factura_electronica import (  # noqa
    EstadoFE, SolicitarCAEManual, ListarSinCAE,
    ProbarConexionAFIP, GuardarConfigFE,
)

# ── Configuración ─────────────────────────────────────────────────────────────
from .configuracion import (  # noqa
    GestionarParametros, GestionarTipocompCli,
    ListarFormasPago, GuardarFormaPago,
    ActualizarListaPrecio, InsertarNuevaPromo,
)

# ── Informes ──────────────────────────────────────────────────────────────────
from .informes import (  # noqa
    InformeTotalesCondicion, InformeTotalesVendedor,
    InformeLibroIVAVentas, InformeRentabilidadArticulos,
    InformeHistorialCajas, InformeStockActual,
    InformeCtaCteClientes, InformeMovimientosStock, InformeEgresos,
)

# ── Dashboard ─────────────────────────────────────────────────────────────────
from .dashboard import ObtenerDashboard  # noqa

# ── Contabilidad ──────────────────────────────────────────────────────────────
from .contabilidad import (  # noqa
    SincronizarAsientos, ListarPlanCuentas, GuardarCuenta,
    ListarAsientos, ObtenerAsiento, CrearAsientoManual, AnularAsientoManual,
    InformeLibroDiario, InformeMayorCuenta,
    InformeBalanceSumasYSaldos, InformeEstadoResultados, InformeBalanceGeneral,
)