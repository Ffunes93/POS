"""
cajas.py — Apertura, cierre y retiros de caja.
Retiro migrado desde Ven_Retiros.cs (legacy C#):
  INSERT cajas_retiros + cajas_retiros_det
"""

from django.db import connection
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


@api_view(['POST'])
def AbrirCaja(request):
    cajero_id    = request.data.get('cajero_id')
    fondo_inicial = float(request.data.get('saldo_inicial', 0))

    if cajero_id is None:
        return Response({"status": "error", "mensaje": "cajero_id es requerido."}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM cajas WHERE cajero = %s AND estado = 1", [cajero_id])
            if cursor.fetchone():
                return Response({"status": "error", "mensaje": "Este operador ya tiene una caja abierta."}, status=400)

            fecha_actual = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                "INSERT INTO cajas (cajero, estado, saldo_ini_billetes, fecha_open) VALUES (%s, 1, %s, %s)",
                [cajero_id, fondo_inicial, fecha_actual],
            )
            caja_id = cursor.lastrowid

            if fondo_inicial > 0:
                cursor.execute(
                    "INSERT INTO cajas_det (nro_caja, tipo, forma, nombre, importe_cajero, importe_real) "
                    "VALUES (%s, 'EFE', 'Efectivo', 'FONDO FIJO', %s, %s)",
                    [caja_id, fondo_inicial, fondo_inicial],
                )

        return Response({"status": "success", "mensaje": f"Caja N° {caja_id} abierta con éxito.", "caja_id": caja_id})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['GET'])
def ObtenerEstadoCaja(request):
    caja_id = request.query_params.get('caja_id')
    if not caja_id:
        return Response({"status": "cerrada"})

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, cajero, saldo_ini_billetes, fecha_open, estado FROM cajas WHERE id = %s",
                [caja_id],
            )
            caja_row = cursor.fetchone()
            if not caja_row or caja_row[4] != 1:
                return Response({"status": "cerrada"})

            cajero_id = caja_row[1]
            apertura  = float(caja_row[2] or 0)
            fecha_open = caja_row[3]

            cursor.execute(
                "SELECT COALESCE(SUM(tot_general), 0) FROM ventas "
                "WHERE nro_caja = %s AND (anulado IS NULL OR anulado != 'S')",
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
                "nro_caja":      caja_id,
                "fecha_caja":    fecha_open.strftime("%d/%m/%Y") if fecha_open else "",
                "apertura":      apertura,
                "ingresos":      ingresos,
                "egresos":       egresos,
                "total_efectivo": apertura + ingresos - egresos,
            },
        })
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['POST'])
def CerrarCaja(request):
    nro_caja       = request.data.get('nro_caja')
    total_retirado = float(request.data.get('total_retirado', 0))

    if nro_caja is None:
        return Response({"status": "error", "mensaje": "nro_caja es requerido."}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT cajero, saldo_ini_billetes, fecha_open FROM cajas WHERE id = %s AND estado = 1",
                [nro_caja],
            )
            row = cursor.fetchone()
            if not row:
                return Response({"status": "error", "mensaje": "La caja indicada no está abierta o no existe."}, status=404)

            cajero_id, apertura, fecha_open = row[0], float(row[1] or 0), row[2]
            fecha_actual = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

            if total_retirado >= 0:
                cursor.execute(
                    "INSERT INTO cajas_retiros (cajero, fecha_open, retiro) VALUES (%s, %s, %s)",
                    [cajero_id, fecha_actual, total_retirado],
                )

            cursor.execute(
                "SELECT COALESCE(SUM(tot_general), 0) FROM ventas "
                "WHERE nro_caja = %s AND (anulado IS NULL OR anulado != 'S')",
                [nro_caja],
            )
            ventas = float(cursor.fetchone()[0])

            cursor.execute(
                "SELECT COALESCE(SUM(retiro), 0) FROM cajas_retiros WHERE cajero = %s AND fecha_open >= %s",
                [cajero_id, fecha_open],
            )
            otros_egresos = float(cursor.fetchone()[0])

            dife_billetes  = apertura + ventas - otros_egresos
            con_diferencias = 1 if dife_billetes != 0 else 0

            cursor.execute(
                """
                UPDATE cajas
                SET estado = 2, fecha_close = %s, saldo_final_billetes = %s,
                    ventas = %s, otros_egresos = %s, dife_billetes = %s,
                    con_diferencias = %s, otros_ingresos = 0.00, cta_cte = 0.00,
                    saldo_ini_cupones = 0.00, saldo_final_cupones = 0.00,
                    dife_cupones = 0.00, deja_billetes = 0.00, procesado = 0
                WHERE id = %s
                """,
                [fecha_actual, total_retirado, ventas, otros_egresos, dife_billetes, con_diferencias, nro_caja],
            )

        return Response({"status": "success", "mensaje": "Arqueo procesado y Caja cerrada."})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


# ── NUEVO: Retiro de caja ─────────────────────────────────────────────────────

@api_view(['POST'])
def RegistrarRetiroCaja(request):
    """
    Registra un retiro de caja durante el turno.
    Replica Ven_Retiros.cs → RealizaRetiro():
      INSERT INTO cajas_retiros (cajero, fecha_open, retiro)
      INSERT INTO cajas_retiros_det (cajero, fecha_open, id_retiro, denominacion, cantidad) -- opcional

    Payload:
    {
      "cajero_id": 1,
      "importe": 5000.00,
      "motivo": "Depósito banco",
      // Opcional: detalle de billetes
      "billetes": [
        { "denominacion": 1000, "cantidad": 3 },
        { "denominacion": 500,  "cantidad": 4 }
      ]
    }
    """
    cajero_id = request.data.get('cajero_id')
    importe   = float(request.data.get('importe', 0))
    motivo    = str(request.data.get('motivo', 'Retiro de caja'))
    billetes  = request.data.get('billetes', [])

    if not cajero_id:
        return Response({"status": "error", "mensaje": "cajero_id es requerido."}, status=400)
    if importe <= 0:
        return Response({"status": "error", "mensaje": "El importe debe ser mayor a 0."}, status=400)

    try:
        with connection.cursor() as cursor:
            # Verifica que tenga caja abierta
            cursor.execute("SELECT id FROM cajas WHERE cajero = %s AND estado = 1", [cajero_id])
            if not cursor.fetchone():
                return Response({"status": "error", "mensaje": "No hay caja abierta para este cajero."}, status=400)

            fecha_actual = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute(
                "INSERT INTO cajas_retiros (cajero, fecha_open, retiro) VALUES (%s, %s, %s)",
                [cajero_id, fecha_actual, importe],
            )
            id_retiro = cursor.lastrowid

            # Detalle de billetes (opcional)
            for billete in billetes:
                den = int(billete.get('denominacion', 0))
                cant = int(billete.get('cantidad', 0))
                if cant > 0 and den > 0:
                    cursor.execute(
                        "INSERT INTO cajas_retiros_det (cajero, fecha_open, id_retiro, denominacion, cantidad) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        [cajero_id, fecha_actual, id_retiro, den, cant],
                    )

        return Response({
            "status":    "success",
            "mensaje":   f"Retiro de ${importe:.2f} registrado correctamente.",
            "id_retiro": id_retiro,
            "importe":   importe,
        })
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)


@api_view(['GET'])
def ListarRetirosCaja(request):
    """Lista los retiros del turno actual de un cajero."""
    cajero_id = request.query_params.get('cajero_id')
    if not cajero_id:
        return Response({"status": "error", "mensaje": "Falta cajero_id."}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, fecha_open, retiro FROM cajas_retiros "
                "WHERE cajero = %s ORDER BY fecha_open DESC LIMIT 50",
                [cajero_id],
            )
            rows = cursor.fetchall()
            data = [
                {"id": r[0], "fecha": r[1].strftime("%d/%m/%Y %H:%M") if r[1] else "", "importe": float(r[2] or 0)}
                for r in rows
            ]
            total = sum(r['importe'] for r in data)

        return Response({"status": "success", "data": data, "total": total})
    except Exception as e:
        return Response({"status": "error", "mensaje": str(e)}, status=500)