"""
maestros/views/__init__.py

Este archivo solo re-exporta las vistas desde los módulos separados.
NO debe contener implementaciones directas — usar los archivos específicos.

Módulos disponibles:
  - auth.py          → Login, usuarios
  - cajas.py         → Apertura, cierre, retiros
  - clientes.py      → ABM clientes
  - compras.py       → Compras, proveedores
  - configuracion.py → Parámetros, tipocomp, formas de pago
  - contabilidad.py  → Módulo contable completo
  - cotizaciones.py  → Presupuestos / cotizaciones
  - cta_cte.py       → CTA CTE clientes, recibos
  - cta_cte_prov.py  → CTA CTE proveedores, pagos
  - dashboard.py     → KPIs del panel de control
  - informes.py      → Todos los informes
  - stock.py         → ABM artículos, rubros, movimientos
  - ventas.py        → Facturación, anulaciones
  - sync.py          → Endpoints de sincronización de catálogos
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