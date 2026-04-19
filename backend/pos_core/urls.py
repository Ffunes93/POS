from django.contrib import admin
from django.urls import path
from maestros.views import (
    GetArticulosJSON, GetClientesJSON, GetVendedoresJSON, 
    GetPromocionesJSON, GetPromocionesDetJSON, GetKitsJSON, 
    GetListasPreciosJSON, GetDescuentosJSON, GetCondIvaJSON, 
    GetFormaPagoJSON, GetRubrosJSON, GetSubRubrosJSON, 
    GetParametrosJSON, IngresarComprobanteVentasJSON, 
    AbrirCaja, CerrarCaja, LoginUsuario # <--- ASEGURATE QUE ESTÉ ACÁ
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
]