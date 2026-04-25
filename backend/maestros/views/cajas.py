from django.db import connection
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


@api_view(['POST'])
def AbrirCaja(request):
    """Abre un nuevo turno insertando en 'cajas' y 'cajas_det'."""
    cajero_id = request.data.get('cajero_id')
    fondo_inicial = float(request.data.get('saldo_inicial', 0))

    if cajero_id is None:
        return Response(
            {"status": "error", "mensaje": "cajero_id es requerido."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM cajas WHERE cajero = %s AND estado = 1",
                [cajero_id],
            )
            if cursor.fetchone():
                return Response(
                    {"status": "error", "mensaje": "Este operador ya tiene una caja abierta."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            fecha_actual = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                """
                INSERT INTO cajas (cajero, estado, saldo_ini_billetes, fecha_open)
                VALUES (%s, 1, %s, %s)
                """,
                [cajero_id, fondo_inicial, fecha_actual],
            )
            caja_id = cursor.lastrowid

            if fondo_inicial > 0:
                cursor.execute(
                    """
                    INSERT INTO cajas_det (nro_caja, tipo, forma, nombre, importe_cajero, importe_real)
                    VALUES (%s, 'EFE', 'Efectivo', 'FONDO FIJO', %s, %s)
                    """,
                    [caja_id, fondo_inicial, fondo_inicial],
                )

        return Response(
            {"status": "success", "mensaje": f"Caja N° {caja_id} abierta con éxito.", "caja_id": caja_id},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {"status": "error", "mensaje": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
def ObtenerEstadoCaja(request):
    """Calcula el arqueo real consultando ventas y cajas_retiros."""
    caja_id = request.query_params.get('caja_id')

    if not caja_id:
        return Response({"status": "cerrada"}, status=status.HTTP_200_OK)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, cajero, saldo_ini_billetes, fecha_open, estado FROM cajas WHERE id = %s",
                [caja_id],
            )
            caja_row = cursor.fetchone()

            if not caja_row or caja_row[4] != 1:
                return Response({"status": "cerrada"}, status=status.HTTP_200_OK)

            cajero_id = caja_row[1]
            apertura = float(caja_row[2] or 0)
            fecha_open = caja_row[3]

            # Suma ventas no anuladas (anulado IS NULL o != 'S')
            cursor.execute(
                """
                SELECT COALESCE(SUM(tot_general), 0)
                FROM ventas
                WHERE nro_caja = %s AND (anulado IS NULL OR anulado != 'S')
                """,
                [caja_id],
            )
            ingresos = float(cursor.fetchone()[0])

            cursor.execute(
                "SELECT COALESCE(SUM(retiro), 0) FROM cajas_retiros WHERE cajero = %s AND fecha_open >= %s",
                [cajero_id, fecha_open],
            )
            egresos = float(cursor.fetchone()[0])

        return Response({
            "status": "abierta",
            "data": {
                "nro_caja": caja_id,
                "fecha_caja": fecha_open.strftime("%d/%m/%Y") if fecha_open else "",
                "apertura": apertura,
                "ingresos": ingresos,
                "egresos": egresos,
                "total_efectivo": apertura + ingresos - egresos,
            },
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"status": "error", "mensaje": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
def CerrarCaja(request):
    """Cierra el turno y calcula el arqueo final."""
    nro_caja = request.data.get('nro_caja')
    total_retirado = float(request.data.get('total_retirado', 0))

    if nro_caja is None:
        return Response(
            {"status": "error", "mensaje": "nro_caja es requerido."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT cajero, saldo_ini_billetes, fecha_open FROM cajas WHERE id = %s AND estado = 1",
                [nro_caja],
            )
            row = cursor.fetchone()
            if not row:
                return Response(
                    {"status": "error", "mensaje": "La caja indicada no está abierta o no existe."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            cajero_id, apertura, fecha_open = row[0], float(row[1] or 0), row[2]
            fecha_actual = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

            if total_retirado >= 0:
                cursor.execute(
                    "INSERT INTO cajas_retiros (cajero, fecha_open, retiro) VALUES (%s, %s, %s)",
                    [cajero_id, fecha_actual, total_retirado],
                )

            cursor.execute(
                """
                SELECT COALESCE(SUM(tot_general), 0)
                FROM ventas
                WHERE nro_caja = %s AND (anulado IS NULL OR anulado != 'S')
                """,
                [nro_caja],
            )
            ventas = float(cursor.fetchone()[0])

            cursor.execute(
                "SELECT COALESCE(SUM(retiro), 0) FROM cajas_retiros WHERE cajero = %s AND fecha_open >= %s",
                [cajero_id, fecha_open],
            )
            otros_egresos = float(cursor.fetchone()[0])

            dife_billetes = apertura + ventas - otros_egresos
            con_diferencias = 1 if dife_billetes != 0 else 0

            cursor.execute(
                """
                UPDATE cajas
                SET estado = 2,
                    fecha_close = %s,
                    saldo_final_billetes = %s,
                    ventas = %s,
                    otros_egresos = %s,
                    dife_billetes = %s,
                    con_diferencias = %s,
                    otros_ingresos = 0.00,
                    cta_cte = 0.00,
                    saldo_ini_cupones = 0.00,
                    saldo_final_cupones = 0.00,
                    dife_cupones = 0.00,
                    deja_billetes = 0.00,
                    procesado = 0
                WHERE id = %s
                """,
                [fecha_actual, total_retirado, ventas, otros_egresos, dife_billetes, con_diferencias, nro_caja],
            )

        return Response(
            {"status": "success", "mensaje": "Arqueo procesado y Caja cerrada."},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {"status": "error", "mensaje": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
