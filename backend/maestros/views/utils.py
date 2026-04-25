import hashlib
import base64
from datetime import datetime, time


def encode_password_legacy(username: str, password: str) -> str:
    """
    Replica exacta de Helper.EncodePassword(usuario + password)
    usado en el sistema legacy C#.
    UnicodeEncoding en C# es UTF-16 Little Endian + SHA1 + Base64.
    """
    original_string = username + password
    bytes_string = original_string.encode('utf-16le')
    sha1_hash = hashlib.sha1(bytes_string).digest()
    return base64.b64encode(sha1_hash).decode('utf-8')


def filtrar_por_fecha(queryset, campo_fecha: str, fecha_str: str):
    """Filtra un queryset por fecha en formato DD/MM/YYYY."""
    if fecha_str:
        try:
            fecha_dt = datetime.strptime(fecha_str, '%d/%m/%Y')
            return queryset.filter(**{f"{campo_fecha}__gte": fecha_dt})
        except ValueError:
            pass
    return queryset


def aplicar_rango_fechas(request, queryset, campo_fecha):
    """
    Utility para aplicar filtros de fecha 'desde' y 'hasta' de forma uniforme.
    Soporta formatos YYYY-MM-DD.
    """
    fecha_desde = request.query_params.get('desde')
    fecha_hasta = request.query_params.get('hasta')

    if fecha_desde:
        try:
            # Convertimos a inicio del día (00:00:00)
            d = datetime.strptime(fecha_desde, '%Y-%m-%d')
            queryset = queryset.filter(**{f"{campo_fecha}__gte": d})
        except ValueError:
            pass

    if fecha_hasta:
        try:
            # Convertimos a fin del día (23:59:59) para incluir todo el día final
            h = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            h_final = datetime.combine(h.date(), time.max)
            queryset = queryset.filter(**{f"{campo_fecha}__lte": h_final})
        except ValueError:
            pass

    return queryset

