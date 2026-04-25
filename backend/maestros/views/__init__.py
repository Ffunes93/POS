# Re-exporta todas las vistas desde un único punto de entrada.
# urls.py importa desde acá: from maestros.views import X

# ── Sincronización / Catálogos ────────────────────────────────────────────────
from .sync import (
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
)

# ── Autenticación / Usuarios ──────────────────────────────────────────────────
from .auth import (
    LoginUsuario,
    CrearUsuario,
    ListarUsuarios,
    BajaUsuario,
    EditarUsuario,
)

# ── Cajas ─────────────────────────────────────────────────────────────────────
from .cajas import (
    AbrirCaja,
    ObtenerEstadoCaja,
    CerrarCaja,
)

# ── Ventas ────────────────────────────────────────────────────────────────────
from .ventas import (
    IngresarComprobanteVentasJSON,
    UltimosComprobantesVenta,
    BuscarComprobanteVenta,
    AnularComprobanteVenta,
)

# ── Clientes ──────────────────────────────────────────────────────────────────
from .clientes import (
    ListarClientes,
    GuardarCliente,
)

# ── Stock / Artículos / Rubros ────────────────────────────────────────────────
from .stock import (
    ListarArticulosABM,
    GuardarArticulo,
    ListarRubros,
    GuardarRubro,
    ListarSubRubros,
    GuardarSubRubro,
    InsertarNuevCausa,
    ActualizarCausa,
)

# ── Compras / Proveedores ─────────────────────────────────────────────────────
from .compras import (
    ListarProveedores,
    GuardarProveedor,
    ListarCompras,
    IngresarComprobanteComprasJSON,
)

# ── Cuenta Corriente ──────────────────────────────────────────────────────────
from .cta_cte import (
    ResumenCtaCteCliente,
    InsertarReciboCtaCte,
)

# ── Informes ──────────────────────────────────────────────────────────────────
from .informes import (
    InformeTotalesCondicion,
    InformeTotalesVendedor,
    InformeLibroIVAVentas,
    InformeRentabilidadArticulos,
    InformeHistorialCajas,
)

# ── Configuración ─────────────────────────────────────────────────────────────
from .configuracion import (
    GestionarParametros,
    GestionarTipocompCli,
    ListarFormasPago,
    GuardarFormaPago,
    ActualizarListaPrecio,
    InsertarNuevaPromo,
)
