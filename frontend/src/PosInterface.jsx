import { useState } from 'react'

export default function PosInterface({ user, cajaId, onCloseShift }) {
  // Valores por defecto para probar la venta
  const [totalSimulado, setTotalSimulado] = useState(1500.00); 
  const [codigoArticulo, setCodigoArticulo] = useState("100"); // Poné un código que sepas que existe

  // --- 1. FUNCIÓN DE VENTA SIMULADA ---
  const cobrarVenta = async () => {
    const payloadVenta = {
      Cliente_Codigo: 1, 
      Comprobante_Tipo: "TK",
      Comprobante_Letra: "X",
      Comprobante_PtoVenta: 1,
      Comprobante_Numero: 1,
      Comprobante_FechaEmision: new Date().toISOString(),
      Comprobante_ImporteTotal: totalSimulado,
      Comprobante_CondVenta: "1", 
      nro_caja: cajaId, // Usa la caja real abierta
      Comprobante_Items: [
        {
          Item_CodigoArticulo: codigoArticulo, // Usa el código del input
          Item_CantidadUM1: 1,
          Item_PrecioUnitario: totalSimulado,
          Item_ImporteTotal: totalSimulado
        }
      ],
      Comprobante_MediosPago: [
        {
          MedioPago: "EFE", 
          MedioPago_Importe: totalSimulado
        }
      ]
    };

    try {
      const res = await fetch('http://localhost:8001/api/IngresarComprobanteVentasJSON/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payloadVenta)
      });
      
      const data = await res.json();
      
      if (res.ok && data.status === 'success') {
        alert(`✅ Venta # ${data.movim} registrada con éxito en la caja ${cajaId}.`);
      } else {
        alert('Django rechazó la venta:\n\n' + JSON.stringify(data, null, 2));
      }
    } catch (error) {
      alert("Error de red: " + error.message);
    }
  };

  // --- 2. FUNCIÓN DE CIERRE DE CAJA ---
  const cerrarCaja = async () => {
    const declaredEfectivo = prompt("ARQUEO Z:\nIngrese el efectivo total contado en caja (Billetes):", "0");
    if (declaredEfectivo === null) return; // Si apretó Cancelar, no hace nada

    const payloadCierre = {
      cajero_id: user.id,
      saldo_final_billetes: parseFloat(declaredEfectivo),
      saldo_final_cupones: 0, 
      otros_ingresos: 0,
      otros_egresos: 0,
      deja_billetes: 0
    };

    try {
      const res = await fetch('http://localhost:8001/api/CerrarCaja/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payloadCierre)
      });
      const data = await res.json();
      
      if (res.ok && data.status === 'success') {
        alert(`🔒 Turno Cerrado Correctamente.\nDiferencia de caja: $ ${data.arqueo.diferencia_efectivo}`);
        onCloseShift(); // Limpia la caja y vuelve a la pantalla de Apertura
      } else {
        alert('Error cerrando caja:\n\n' + JSON.stringify(data, null, 2));
      }
    } catch (error) {
      alert("Error de red: " + error.message);
    }
  };

  // --- 3. INTERFAZ GRÁFICA ---
  return (
    <div style={{ padding: '20px', display: 'flex', gap: '20px' }}>
      
      {/* PANEL IZQUIERDO: VENTAS */}
      <div style={{ flex: 2, background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <h2>🛒 Terminal de Ventas</h2>
        <div style={{ padding: '20px', background: '#ecf0f1', borderRadius: '8px', marginBottom: '20px' }}>
           <p style={{ margin: '0 0 10px 0' }}>Operando en <b>Caja # {cajaId}</b></p>
           
           <div style={{ marginBottom: '15px' }}>
             <label style={{ fontWeight: 'bold' }}>Código Artículo: </label>
             <input 
               type="text" 
               value={codigoArticulo} 
               onChange={(e) => setCodigoArticulo(e.target.value)}
               style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', marginLeft: '10px' }}
             />
           </div>

           <h3 style={{ margin: 0, fontSize: '24px', color: '#2c3e50' }}>Total a Pagar: $ {totalSimulado}</h3>
        </div>
        <button onClick={cobrarVenta} style={{ width: '100%', padding: '15px', background: '#3498db', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '18px', fontWeight: 'bold' }}>
          EFECTUAR COBRO (Efectivo)
        </button>
      </div>

      {/* PANEL DERECHO: OPCIONES DE CAJA */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '15px' }}>
        <div style={{ background: '#fff3cd', padding: '20px', borderRadius: '8px', border: '1px solid #ffeaa7' }}>
          <h3 style={{ marginTop: 0, color: '#d35400' }}>Gestión de Turno</h3>
          <p style={{ fontSize: '14px', color: '#555' }}>
            Al cerrar el turno, el sistema sumará sus ventas al inicio de caja y lo comparará con lo que usted declare en el arqueo.
          </p>
          <button onClick={cerrarCaja} style={{ width: '100%', padding: '15px', background: '#e67e22', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
            CERRAR CAJA (Z)
          </button>
        </div>
      </div>

    </div>
  )
}