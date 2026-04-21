import { useState, useEffect } from 'react';

export default function AperturaCierreCaja({ user, cajaId, onCajaCambiada }) {
  const [loading, setLoading] = useState(true);
  const [estadoCaja, setEstadoCaja] = useState(null); 
  const [errorFetch, setErrorFetch] = useState(false);
  
  // Formularios
  const [fondoInicial, setFondoInicial] = useState('');
  const [totalRetirado, setTotalRetirado] = useState('');
  const [ptoVenta, setPtoVenta] = useState('0001');

  useEffect(() => {
    chequearCaja();
  }, [cajaId]);

  const chequearCaja = async () => {
    // Si sabemos que no hay caja, cortamos camino rápido
    if (!cajaId) {
      setEstadoCaja(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setErrorFetch(false);
    try {
      // Le pasamos explícitamente el cajaId que viene de App.jsx (Ej: 31)
      const res = await fetch(`http://localhost:8001/api/EstadoCaja/?caja_id=${cajaId}`);
      const data = await res.json();
      
      if (res.ok && data.status === 'abierta') {
        setEstadoCaja(data.data);
      } else {
        // Falló o devolvió cerrada a pesar de tener ID
        setErrorFetch(true);
      }
    } catch (error) {
      console.error("Error verificando caja:", error);
      setErrorFetch(true);
    }
    setLoading(false);
  };

  const handleAbrirCaja = async (e) => {
    e.preventDefault();
    if (!fondoInicial || isNaN(fondoInicial)) return alert("Ingrese un monto válido.");

    try {
      const res = await fetch('http://localhost:8001/api/AbrirCaja/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cajero_id: user.id, saldo_inicial: parseFloat(fondoInicial), pto_venta: ptoVenta })
      });
      const data = await res.json();
      
      if (res.ok && data.status === 'success') {
        alert(data.mensaje);
        
        // Magia de React: Le avisamos a la app global el ID de la caja
        // y se actualiza TODO sin parpadear ni recargar la web
        onCajaCambiada(data.caja_id); 
        
      } else {
        alert("El servidor rechazó la apertura:\n" + data.mensaje); 
      }
    } catch (error) {
      alert("Error de conexión al abrir caja.");
    }
  };
  
  const handleCerrarCaja = async (e) => {
    e.preventDefault();
    if (totalRetirado === '') return alert("Ingrese el total retirado.");

    if (!window.confirm("¿Está seguro que desea CERRAR la caja actual?")) return;

    try {
      const res = await fetch('http://localhost:8001/api/CerrarCaja/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nro_caja: estadoCaja.nro_caja, total_retirado: parseFloat(totalRetirado) })
      });
      
      if (res.ok) {
        alert("Caja cerrada y arqueo generado correctamente.");
        onCajaCambiada(null); // Limpia la caja global
      }
    } catch (error) {
      alert("Error al cerrar caja.");
    }
  };

  if (loading) return <div style={{ padding: '40px', textAlign: 'center', fontSize: '18px', color: '#7f8c8d' }}>⚙️ Calculando arqueo de caja...</div>;

  // PANTALLA DE ERROR: La barra dice abierta pero la DB no responde
  if (cajaId && errorFetch) {
    return (
      <div style={{ background: '#e74c3c', color: 'white', padding: '30px', borderRadius: '8px', textAlign: 'center' }}>
        <h2>⚠️ Error de Sincronización</h2>
        <p>El sistema registra que la Caja #{cajaId} está abierta, pero no pudimos cargar los totales (Ingresos/Egresos).</p>
        <p>Por favor revise la consola del backend para verificar si faltan declarar tablas en los modelos.</p>
        <button onClick={chequearCaja} style={{ padding: '10px 20px', background: 'white', color: '#e74c3c', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>Reintentar Conexión</button>
      </div>
    );
  }

  // ==========================================
  // VISTA 1: APERTURA DE CAJA (Si está cerrada)
  // ==========================================
  if (!cajaId || !estadoCaja) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', marginTop: '50px' }}>
        <div style={{ background: 'white', padding: '30px', borderRadius: '8px', boxShadow: '0 4px 15px rgba(0,0,0,0.1)', width: '400px' }}>
          <h2 style={{ marginTop: 0, color: '#2c3e50', textAlign: 'center', borderBottom: '2px solid #ecf0f1', paddingBottom: '10px' }}>
            Apertura de Caja
          </h2>
          <form onSubmit={handleAbrirCaja} style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '20px' }}>
            <div>
              <label style={{ fontWeight: 'bold', fontSize: '14px', color: '#7f8c8d' }}>Punto de Venta:</label>
              <input type="text" value={ptoVenta} onChange={e => setPtoVenta(e.target.value)} style={{ width: '100%', padding: '10px', marginTop: '5px', borderRadius: '4px', border: '1px solid #ccc', boxSizing: 'border-box' }} />
            </div>
            <div>
              <label style={{ fontWeight: 'bold', fontSize: '14px', color: '#7f8c8d' }}>Fondo Fijo Inicial ($):</label>
              <input autoFocus required type="number" step="0.01" value={fondoInicial} onChange={e => setFondoInicial(e.target.value)} placeholder="0.00" style={{ width: '100%', padding: '10px', marginTop: '5px', borderRadius: '4px', border: '2px solid #3498db', fontSize: '18px', textAlign: 'right', boxSizing: 'border-box' }} />
            </div>
            <button type="submit" style={{ padding: '15px', background: '#2ecc71', color: 'white', border: 'none', borderRadius: '4px', fontSize: '16px', fontWeight: 'bold', cursor: 'pointer' }}>
              F12 - ABRIR CAJA
            </button>
          </form>
        </div>
      </div>
    );
  }

  // ==========================================
  // VISTA 2: CIERRE DE CAJA (Idéntica a tu imagen)
  // ==========================================
  return (
    <div style={{ background: '#f0f0f0', padding: '20px', borderRadius: '8px', border: '1px solid #ccc', maxWidth: '800px', margin: '0 auto', fontFamily: 'Arial, sans-serif' }}>
      <h2 style={{ margin: '0 0 20px 0', color: '#000', fontSize: '18px', borderBottom: '1px solid #999', paddingBottom: '5px' }}>
        Cierre de Caja
      </h2>

      <div style={{ display: 'flex', gap: '20px' }}>
        
        {/* LADO IZQUIERDO: Inputs */}
        <div style={{ flex: 1 }}>
          <div style={{ border: '1px solid #b0b0b0', padding: '15px', borderRadius: '4px', background: '#fafafa', height: '100%', boxSizing: 'border-box' }}>
            <form id="formCierre" onSubmit={handleCerrarCaja}>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'inline-block', width: '130px', fontSize: '13px' }}>Punto de Venta:</label>
                <select value={ptoVenta} onChange={e => setPtoVenta(e.target.value)} style={{ padding: '4px', width: '100px', border: '1px solid #999' }}>
                  <option value="0001">0001</option>
                  <option value="0002">0002</option>
                </select>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'inline-block', width: '130px', fontSize: '13px' }}>Fecha Caja:</label>
                <input type="text" readOnly value={estadoCaja.fecha_caja} style={{ padding: '4px', width: '100px', border: '1px solid #999', background: '#e9e9e9' }} />
              </div>

              <div style={{ marginTop: '40px' }}>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 'bold', marginBottom: '5px', color: '#000' }}>Total Retirado</label>
                <input 
                  autoFocus 
                  required 
                  type="number" 
                  step="0.01" 
                  value={totalRetirado} 
                  onChange={e => setTotalRetirado(e.target.value)} 
                  style={{ width: '150px', padding: '8px', border: '1px solid #000', fontSize: '16px', textAlign: 'right' }} 
                />
              </div>
            </form>
          </div>
        </div>

        {/* LADO DERECHO: Resumen (Totales) */}
        <div style={{ flex: 1 }}>
          <div style={{ border: '1px solid #b0b0b0', padding: '15px', borderRadius: '4px', background: '#fafafa' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', fontSize: '13px' }}>
              <span>Caja N°:</span>
              <span style={{ fontWeight: 'bold' }}>{estadoCaja.nro_caja}</span>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', fontSize: '13px', borderBottom: '1px solid #ccc', paddingBottom: '10px' }}>
              <span>Operador Cierre:</span>
              <span style={{ fontWeight: 'bold' }}>{user.id}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', fontSize: '13px' }}>
              <span>Apertura:</span>
              <span>{estadoCaja.apertura.toFixed(2)}</span>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', fontSize: '13px' }}>
              <span>Ingresos:</span>
              <span style={{ color: 'green' }}>{estadoCaja.ingresos.toFixed(2)}</span>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', fontSize: '13px' }}>
              <span>Egresos:</span>
              <span style={{ color: 'red' }}>{estadoCaja.egresos.toFixed(2)}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#e0e0e0', padding: '10px', border: '1px solid #ccc' }}>
              <span style={{ fontWeight: 'bold', fontSize: '14px' }}>Total Efectivo:</span>
              <span style={{ fontWeight: 'bold', fontSize: '18px', color: '#b30000' }}>
                {estadoCaja.total_efectivo.toFixed(2)}
              </span>
            </div>

          </div>
        </div>

      </div>

      {/* BOTONERA INFERIOR */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px', borderTop: '1px solid #999', paddingTop: '15px' }}>
        <button type="submit" form="formCierre" style={{ padding: '8px 20px', background: '#e0e0e0', border: '1px solid #888', cursor: 'pointer', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '5px', fontWeight: 'bold' }}>
          <span style={{ color: 'green', fontSize: '16px' }}>✓</span> Procesar
        </button>
      </div>

    </div>
  );
}