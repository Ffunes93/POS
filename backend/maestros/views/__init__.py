"""
maestros/views/__init__.py

Re-exporta todas las vistas desde los módulos separados.
NO contiene implementaciones directas.

Módulos disponibles:
  - auth.py          → Login, usuarios
  - cajas.py         → Apertura, cierre, retiros
  - clientes.py      → ABM clientes
  - compras.py       → Compras, proveedores
  - configuracion.py → Parámetros, tipocomp, formas de pago
  - contabilidad.py  → Módulo contable completo (extendido)
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

# ── Contabilidad (versión extendida) ──────────────────────────────────────────
from .contabilidad import (  # noqa
    # Sincronización
    SincronizarAsientos,
    # Plan de Cuentas
    ListarPlanCuentas, GuardarCuenta,
    # CRUD Asientos
    ListarAsientos, ObtenerAsiento, CrearAsientoManual, AnularAsientoManual,
    # Mayorización y anulación por ID
    MayorizarAsiento, AnularAsientoId,
    # Asientos automáticos e importación
    GenerarAsientoAutomatico, ImportarAsientos,
    # Consulta de saldos
    ConsultaSaldos,
    # Configuración contable (NUEVO)
    GestionTiposAsiento, DetalleTipoAsiento,
    GestionSeries, DetalleSerie,
    GestionEjercicios, DetalleEjercicio,
    GestionModelos, DetalleModelo,
    # Informes
    InformeLibroDiario, InformeMayorCuenta,
    InformeBalanceSumasYSaldos, InformeEstadoResultados, InformeBalanceGeneral,
)

from .impositivo import (  # noqa
    LibrosIVA, EliminarLibroIVA, DatosLibroIVA,
    GenerarIVADigital,
    DeclaracionesJuradas, RectificarDDJJ, MarcarPasadoCG,
    AnalisisOperaciones,
    ListarExportaciones, DescargarExportacion,
    GenerarSICORE, GenerarSIFERE, GenerarExportacionGenerica,
    VentasPorPuntoDeVenta, RankingClientes, RankingProveedores,
    PuntosRegistracion, RegimenesEspeciales,
)

from .bodega import (  # noqa
    BodDashboardView,
    BodVarietalesView, BodInsumosView,
    BodParcelasView, BodMaduracionView,
    BodLaboresCulturalesView, BodTratamientosFitosanitariosView,
    BodContratosUvaView, BodLiquidacionesUvaView,
    BodTicketsBasculaView, BodAsignarTicketLoteView,
    BodRecipientesView,
    BodLotesGranelView, BodMovimientosGranelView,
    BodOperacionesEnologicasView,
    BodOrdenesElaboracionView, BodBalanceMasaView,
    BodAnalisisView,
    BodFichasProductoView, BodNoConformidadesView,
    BodBarricasView, BodAsignacionBarricasView,
    BodOrdenesEmbotelladoView, BodConfirmarEmbotelladoView,
    BodCostosView,
    BodTrazabilidadView,
    BodDeclaracionesINVView, BodGuiasTrasladoView, BodCertificadosAnalisisView,
)