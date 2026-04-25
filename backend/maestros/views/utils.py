import hashlib
import base64
from datetime import datetime


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
