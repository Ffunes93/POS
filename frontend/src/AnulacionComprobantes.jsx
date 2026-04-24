import React, { useState } from 'react';

export default function AnulacionComprobantes() {
  const [busqueda, setBusqueda] = useState({ tipo: 'TK', pto: '1', nro: '' });
  const [comprobante, setComprobante] = useState(null);
  const [cargando, setCargando] = useState(false);

  const buscarComprobante = async (e) => {
    e.preventDefault();
    if (!busqueda.nro) return alert("Ingrese un número de comprobante.");
    
    setCargando(true);
    setComprobante(null); // Limpiamos búsqueda anterior

    try {
      const res = await fetch(`http://localhost:8001/api/BuscarComprobanteVenta/?tipo=${busqueda.tipo}&pto=${busqueda.pto}&nro=${busqueda.nro}`);
      const data = await res.json();

      if (res.ok && data.status === 'success') {
        setComprobante(data.data);
      } else {
        alert(data.mensaje || "Comprobante no encontrado.");
      }
    } catch (error) {
      alert("Error de red al buscar el comprobante.");
    }
    setCargando(false);
  };

  const confirmarAnulacion = async () => {
    if (!comprobante) return;
    if (comprobante.procesado === -1) return alert("Este comprobante ya fue anulado previamente.");

    const confirmar = window.confirm(
      `⚠️ ATENCIÓN: ¿Está seguro que desea anular este comprobante por $${comprobante.total.toFixed(2)}?\n\nEsta acción devolverá los artículos al stock y eliminará la venta de la caja del día.`
    );

    if (!confirmar) return;
    setCargando(true);

    try {
      const res = await fetch('http://localhost:8001/api/AnularComprobanteVenta/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ movim: comprobante.movim })
      });
      const data = await res.json();

      if (res.ok && data.status === 'success') {
        alert("✅ " + data.mensaje);
        setComprobante(null); // Limpiamos pantalla
        setBusqueda({ ...busqueda, nro: '' });
      } else {
        alert("Error al anular:\n" + data.mensaje);
      }
    } catch (error) {
      alert("Error de red al procesar la anulación.");
    }
    setCargando(false);
  };

  return (
    <div style={{ background: 'white', padding: '20px', borderRadius: '8px', minHeight: '80vh', border: '1px solid #ddd' }}>
      <h2 style={{ borderBottom: '2px solid #ecf0f1', paddingBottom: '10px', color: '#e74c3c', marginTop: 0 }}>
        🚫 Anulación de Comprobantes
      </h2>

      {/* PANEL DE BÚSQUEDA */}
      <form onSubmit={buscarComprobante} style={{ display: 'flex', gap: '15px', alignItems: 'flex-end', background: '#f8f9fa', padding: '20px', borderRadius: '6px', marginBottom: '20px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d' }}>Tipo</label>
          <select value={busqueda.tipo} onChange={e => setBusqueda({...busqueda, tipo: e.target.value})} style={{ padding: '10px', borderRadius: '4px', border: '1px solid #ccc' }}>
            <option value="TK">TICKET (TK)</option>
            <option value="FA">FACTURA (FA)</option>
            <option value="PR">PRESUPUESTO (PR)</option>
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d' }}>Pto. Venta</label>
          <input type="number" value={busqueda.pto} onChange={e => setBusqueda({...busqueda, pto: e.target.value})} style={{ padding: '10px', borderRadius: '4px', border: '1px solid #ccc', width: '80px', textAlign: 'center' }} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d' }}>N° Comprobante</label>
          <input type="number" placeholder="Ej: 15" value={busqueda.nro} onChange={e => setBusqueda({...busqueda, nro: e.target.value})} style={{ padding: '10px', borderRadius: '4px', border: '1px solid #ccc', width: '150px', textAlign: 'center' }} autoFocus />
        </div>
        <button type="submit" disabled={cargando} style={{ padding: '11px 25px', background: '#34495e', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}>
          {cargando ? 'Buscando...' : '🔍 Buscar'}
        </button>
      </form>

      {/* DETALLE DEL COMPROBANTE ENCONTRADO */}
      {comprobante && (
        <div style={{ border: '1px solid #ddd', borderRadius: '6px', overflow: 'hidden' }}>
          <div style={{ background: comprobante.procesado === -1 ? '#e74c3c' : '#2ecc71', color: 'white', padding: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0 }}>
              {comprobante.procesado === -1 ? '⚠️ COMPROBANTE YA ANULADO' : '✅ COMPROBANTE VÁLIDO ENCONTRADO'}
            </h3>
            <span style={{ fontSize: '18px', fontWeight: 'bold' }}>Total: ${comprobante.total.toFixed(2)}</span>
          </div>
          
          <div style={{ padding: '20px' }}>
            <p><strong>Fecha:</strong> {new Date(comprobante.fecha).toLocaleString()}</p>
            <p><strong>Cód. Cliente:</strong> {comprobante.cliente}</p>
            
            <table style={{ width: '100%', marginTop: '15px', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ background: '#ecf0f1', textAlign: 'left' }}>
                  <th style={{ padding: '8px' }}>Código</th>
                  <th style={{ padding: '8px' }}>Descripción</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>Cant.</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {comprobante.items.map((item, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '8px' }}>{item.cod_articulo}</td>
                    <td style={{ padding: '8px' }}>{item.detalle}</td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>{parseFloat(item.cantidad).toFixed(2)}</td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>${parseFloat(item.total).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* BOTÓN DE ANULACIÓN DEFINITIVA */}
            {comprobante.procesado !== -1 && (
              <div style={{ marginTop: '30px', textAlign: 'right', borderTop: '1px solid #ddd', paddingTop: '20px' }}>
                <button onClick={confirmarAnulacion} disabled={cargando} style={{ padding: '15px 30px', background: '#c0392b', color: 'white', border: 'none', borderRadius: '6px', fontSize: '16px', fontWeight: 'bold', cursor: 'pointer', boxShadow: '0 4px 6px rgba(192,57,43,0.3)' }}>
                  {cargando ? 'Procesando...' : '⚠️ ANULAR COMPROBANTE Y DEVOLVER STOCK'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}