from django.contrib import admin
from django.urls import path
from maestros.views import (
    GetArticulosJSON, GetClientesJSON, GetVendedoresJSON, 
    GetPromocionesJSON, GetPromocionesDetJSON, GetKitsJSON, 
    GetListasPreciosJSON, GetDescuentosJSON, GetCondIvaJSON, 
    GetFormaPagoJSON, GetRubrosJSON, GetSubRubrosJSON, 
    GetParametrosJSON, IngresarComprobanteVentasJSON, 
    AbrirCaja, CerrarCaja, LoginUsuario, CrearUsuario, ListarUsuarios, BajaUsuario, EditarUsuario, ListarClientes,
    GuardarCliente,ListarArticulosABM, GuardarArticulo, ListarProveedores, GuardarProveedor,
    ListarFormasPago, GuardarFormaPago, InformeTotalesCondicion, InformeTotalesVendedor, ListarRubros,
    GuardarRubro, ListarSubRubros, GuardarSubRubro, ObtenerEstadoCaja, ListarCompras, IngresarComprobanteComprasJSON,
    ResumenCtaCteCliente, InsertarReciboCtaCte, ActualizarListaPrecio, InsertarNuevaPromo, InsertarNuevCausa, 
    ActualizarCausa, InformeLibroIVAVentas, InformeRentabilidadArticulos, InformeHistorialCajas, GestionarParametros,
    BuscarComprobanteVenta, AnularComprobanteVenta, GestionarTipocompCli
      # <--- ASEGURATE QUE ESTÉ ACÁ
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Sincronización de Catálogos y Maestros
    path('api/getArticulosJSON/', GetArticulosJSON.as_view()),
    path('api/getClientesJSON/', GetClientesJSON.as_view()),
    path('api/getVendedoresJSON/', GetVendedoresJSON.as_view()),
    path('api/getPromocionesJSON/', GetPromocionesJSON.as_view()),
    path('api/getPromocionesDetJSON/', GetPromocionesDetJSON.as_view()),
    path('api/getKitsJSON/', GetKitsJSON.as_view()),
    path('api/getListaPreciosJSON/', GetListasPreciosJSON.as_view()),
    path('api/getDescuentosJSON/', GetDescuentosJSON.as_view()),
    path('api/getCondIvaJSON/', GetCondIvaJSON.as_view()),
    path('api/getFormaPagoJSON/', GetFormaPagoJSON.as_view()),
    path('api/getRubrosJSON/', GetRubrosJSON.as_view()),
    path('api/getSubRubrosJSON/', GetSubRubrosJSON.as_view()),
    path('api/getParametrosJSON/', GetParametrosJSON.as_view()),
    
    # ACÁ LE SACAMOS EL "views." DEL PRINCIPIO Y CORREGIMOS EL NOMBRE
    path('api/IngresarComprobanteVentasJSON/', IngresarComprobanteVentasJSON, name='IngresarComprobanteVentasJSON'),
    path('api/AbrirCaja/', AbrirCaja, name='AbrirCaja'),
    path('api/CerrarCaja/', CerrarCaja, name='CerrarCaja'),
    path('api/Login/', LoginUsuario, name='Login'),
    path('api/CrearUsuario/', CrearUsuario, name='CrearUsuario'),
    path('api/ListarUsuarios/', ListarUsuarios, name='ListarUsuarios'),
    path('api/BajaUsuario/', BajaUsuario, name='BajaUsuario'),
    path('api/EditarUsuario/', EditarUsuario, name='EditarUsuario'),
    path('api/ListarClientes/', ListarClientes, name='ListarClientes'),
    path('api/GuardarCliente/', GuardarCliente, name='GuardarCliente'),
    path('api/ListarArticulosABM/', ListarArticulosABM, name='ListarArticulosABM'),
    path('api/GuardarArticulo/', GuardarArticulo, name='GuardarArticulo'),
    path('api/ListarProveedores/', ListarProveedores, name='ListarProveedores'),
    path('api/GuardarProveedor/', GuardarProveedor, name='GuardarProveedor'),
    path('api/ListarFormasPago/', ListarFormasPago, name='ListarFormasPago'),
    path('api/GuardarFormaPago/', GuardarFormaPago, name='GuardarFormaPago'),
    path('api/InformeTotalesCondicion/', InformeTotalesCondicion, name='InformeTotalesCondicion'),
    path('api/InformeTotalesVendedor/', InformeTotalesVendedor, name='InformeTotalesVendedor'),
    path('api/ListarRubros/', ListarRubros, name='ListarRubros'),
    path('api/GuardarRubro/', GuardarRubro, name='GuardarRubro'),
    path('api/ListarSubRubros/', ListarSubRubros, name='ListarSubRubros'),
    path('api/GuardarSubRubro/', GuardarSubRubro, name='GuardarSubRubro'),
    path('api/EstadoCaja/', ObtenerEstadoCaja, name='EstadoCaja'),
    # MÓDULO DE COMPRAS
    path('api/ListarCompras/', ListarCompras, name='ListarCompras'),
    path('api/IngresarComprobanteComprasJSON/', IngresarComprobanteComprasJSON, name='IngresarComprobanteComprasJSON'),

    # MÓDULO DE CUENTAS CORRIENTES
    path('api/ResumenCtaCteCliente/', ResumenCtaCteCliente, name='ResumenCtaCteCliente'),
    path('api/InsertarReciboCtaCte/', InsertarReciboCtaCte, name='InsertarReciboCtaCte'),

    # MÓDULO DE LISTAS DE PRECIOS Y PROMOS (Nombres Legacy)
    path('api/ActualizarListaPrecio/', ActualizarListaPrecio, name='ActualizarListaPrecio'),
    path('api/InsertarNuevaPromo/', InsertarNuevaPromo, name='InsertarNuevaPromo'),

    # MÓDULO DE INVENTARIO (Nombres Legacy)
    path('api/InsertarNuevCausa/', InsertarNuevCausa, name='InsertarNuevCausa'),
    path('api/ActualizarCausa/', ActualizarCausa, name='ActualizarCausa'),

    # MÓDULO DE INFORMES
    path('api/InformeLibroIVAVentas/', InformeLibroIVAVentas, name='InformeLibroIVAVentas'),
    path('api/InformeRentabilidadArticulos/', InformeRentabilidadArticulos, name='InformeRentabilidadArticulos'),
    path('api/InformeHistorialCajas/', InformeHistorialCajas, name='InformeHistorialCajas'),

     # MÓDULO DE PARAMETROS
    path('api/GestionarParametros/', GestionarParametros, name='GestionarParametros'),

    # MÓDULO DE ANULACIONES
    path('api/BuscarComprobanteVenta/', BuscarComprobanteVenta, name='BuscarComprobanteVenta'),
    path('api/AnularComprobanteVenta/', AnularComprobanteVenta, name='AnularComprobanteVenta'),

    # MÓDULO DE GESTION
    path('api/GestionarTipocompCli/', GestionarTipocompCli, name='GestionarTipocompCli'),
]