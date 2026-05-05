"""
maestros/permissions.py — Sprint A · A5

Auth condicional para el módulo de contabilidad.
Activación: agregar a settings.py:

    CONTAB_REQUIRE_AUTH = True

Mientras el flag esté en False (default), el comportamiento se mantiene
abierto (compatibilidad hacia atrás con el sistema actual sin login).

Cuando se active, todas las vistas marcadas con ContabAuth requerirán
un usuario autenticado vía SessionAuthentication o TokenAuthentication.
"""
from rest_framework.permissions import BasePermission
from django.conf import settings


class ContabAuth(BasePermission):
    """
    Auth opt-in para módulo contabilidad.

    Si settings.CONTAB_REQUIRE_AUTH = True, exige usuario autenticado.
    Si no está seteado o es False, permite anónimo (modo legacy).
    """
    message = 'Autenticación requerida para operaciones contables.'

    def has_permission(self, request, view):
        if not getattr(settings, 'CONTAB_REQUIRE_AUTH', False):
            return True
        return bool(request.user and request.user.is_authenticated)


def get_usuario_actual(request, payload_fallback='sistema'):
    """
    Obtiene el username de forma segura.

    Prioridad:
      1. request.user.username si está autenticado
      2. payload['usuario'] si vino en el body (modo legacy)
      3. payload_fallback (default 'sistema')

    Cuando CONTAB_REQUIRE_AUTH=True, NUNCA cae al payload (más seguro).
    """
    if hasattr(request, 'user') and request.user and request.user.is_authenticated:
        return (request.user.username or 'unknown')[:20]

    if getattr(settings, 'CONTAB_REQUIRE_AUTH', False):
        # En modo estricto, si no hay user autenticado, usar 'anon' explícito.
        # No aceptamos payload['usuario'] para evitar suplantación.
        return 'anon'

    # Modo legacy: aceptar payload
    payload = getattr(request, 'data', {}) or {}
    return str(payload.get('usuario') or payload_fallback)[:20]