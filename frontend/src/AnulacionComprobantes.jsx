import React, { useState, useEffect } from 'react';

export default function AnulacionComprobantes() {
  const [busqueda, setBusqueda] = useState({ tipo: 'EA', pto: '1', nro: '' });
  const [comprobante, setComprobante] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [tiposDisponibles, setTiposDisponibles] = useState([]);

  // Estados para los últimos 50 comprobantes
  const [ultimos, setUltimos] = useState([]);
  const [modalUltimos, setModalUltimos] = useState(false);

  useEffect(() => {
    const cargarTipos = async () => {
      try {
        const res = await fetch('http://localhost:8001/api/GestionarTipocompCli/');
        const data = await res.json();
        
        if (data.status === 'success') {
          const permitidos = ['EA', 'EB', 'EC', 'FA', 'FB', 'FC', 'PR', 'TK', 'MA', 'MB'];
          const filtrados = data.data.filter(t => permitidos.includes(t.cod_compro));
          setTiposDisponibles(filtrados);
          if (filtrados.length > 0) {
            const defaultComp = filtrados.find(t => t.cod_compro === 'EA') || filtrados[0];
            setBusqueda(prev => ({ ...prev, tipo: defaultComp.cod_compro }));
          }
        }
      } catch (error) {
        console.error("Error al cargar comprobantes:", error);
      }
    };
    cargarTipos();
  }, []);

  const buscarComprobante = async (e) => {
    if (e) e.preventDefault();
    if (!busqueda.nro) return alert("Ingrese un número de comprobante.");
    
    setCargando(true);
    setComprobante(null);

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
      `⚠️ ATENCIÓN: ¿Está seguro que desea anular este comprobante por $${comprobante.total.toFixed(2)}?\n\nEsta acción devolverá los artículos al stock, revertirá los cobros y emitirá una NOTA DE CRÉDITO.`
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
        setComprobante(null);
        setBusqueda({ ...busqueda, nro: '' });
      } else {
        alert("Error al anular:\n" + data.mensaje);
      }
    } catch (error) {
      alert("Error de red al procesar la anulación.");
    }
    setCargando(false);
  };

  const buscarUltimos50 = async () => {
    setCargando(true);
    try {
      const res = await fetch('http://localhost:8001/api/UltimosComprobantesVenta/');
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setUltimos(data.data);
        setModalUltimos(true);
      } else {
        alert("Error al obtener últimos comprobantes.");
      }
    } catch (error) {
      alert("Error de red al consultar historial.");
    }
    setCargando(false);
  };

  // 👇 ACÁ ESTÁ LA MAGIA NUEVA: Busca automáticamente al hacer clic en la lista
  const seleccionarHistorial = async (comp) => {
    if (comp.procesado === -1) return alert("Ese comprobante ya está anulado.");
    
    const ptoLimpio = parseInt(comp.pto_vta, 10).toString();
    
    // Actualizamos los inputs visuales
    setBusqueda({ tipo: comp.tipo, pto: ptoLimpio, nro: comp.nro.toString() });
    setModalUltimos(false);
    
    // Disparamos la búsqueda de inmediato
    setCargando(true);
    setComprobante(null);

    try {
      const res = await fetch(`http://localhost:8001/api/BuscarComprobanteVenta/?tipo=${comp.tipo}&pto=${ptoLimpio}&nro=${comp.nro}`);
      const data = await res.json();

      if (res.ok && data.status === 'success') {
        setComprobante(data.data);
      } else {
        alert(data.mensaje || "Comprobante no encontrado.");
      }
    } catch (error) {
      alert("Error de red al auto-buscar el comprobante.");
    }
    setCargando(false);
  };

  return (
    <div style={{ background: 'white', padding: '20px', borderRadius: '8px', minHeight: '80vh', border: '1px solid #ddd', position: 'relative' }}>
      <h2 style={{ borderBottom: '2px solid #ecf0f1', paddingBottom: '10px', color: '#e74c3c', marginTop: 0 }}>
        🚫 Anulación de Comprobantes
      </h2>

      {/* PANEL DE BÚSQUEDA */}
      <form onSubmit={buscarComprobante} style={{ display: 'flex', gap: '15px', alignItems: 'flex-end', background: '#f8f9fa', padding: '20px', borderRadius: '6px', marginBottom: '20px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d' }}>Tipo Original</label>
          <select 
            value={busqueda.tipo} 
            onChange={e => setBusqueda({...busqueda, tipo: e.target.value})} 
            style={{ padding: '10px', borderRadius: '4px', border: '1px solid #ccc', fontSize: '14px', minWidth: '150px' }}
          >
            {tiposDisponibles.map(tipo => (
              <option key={tipo.id_compro} value={tipo.cod_compro}>
                {tipo.cod_compro} - {tipo.nom_compro}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d' }}>Pto. Venta</label>
          <input type="number" value={busqueda.pto} onChange={e => setBusqueda({...busqueda, pto: e.target.value})} style={{ padding: '10px', borderRadius: '4px', border: '1px solid #ccc', width: '80px', textAlign: 'center' }} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d' }}>N° Comprobante</label>
          <input type="number" placeholder="Ej: 15" value={busqueda.nro} onChange={e => setBusqueda({...busqueda, nro: e.target.value})} style={{ padding: '10px', borderRadius: '4px', border: '1px solid #ccc', width: '120px', textAlign: 'center' }} autoFocus />
        </div>
        <button type="submit" disabled={cargando} style={{ padding: '11px 25px', background: '#34495e', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}>
          {cargando ? 'Buscando...' : '🔍 Buscar'}
        </button>
        
        <button type="button" onClick={buscarUltimos50} disabled={cargando} style={{ padding: '11px 25px', background: '#3498db', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', marginLeft: 'auto' }}>
          📋 Ver Últimos 50
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

            {/* 👇 ACÁ ESTÁ EL BOTÓN ROJO DE ANULACIÓN */}
            {comprobante.procesado !== -1 && (
              <div style={{ marginTop: '30px', textAlign: 'right', borderTop: '1px solid #ddd', paddingTop: '20px' }}>
                <button onClick={confirmarAnulacion} disabled={cargando} style={{ padding: '15px 30px', background: '#c0392b', color: 'white', border: 'none', borderRadius: '6px', fontSize: '16px', fontWeight: 'bold', cursor: 'pointer', boxShadow: '0 4px 6px rgba(192,57,43,0.3)' }}>
                  {cargando ? 'Procesando...' : '⚠️ ANULAR COMPROBANTE Y EMITIR N/C'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODAL FLOTANTE CON LOS ÚLTIMOS 50 COMPROBANTES */}
      {modalUltimos && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.7)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 9999 }}>
          <div style={{ background: 'white', width: '800px', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 10px 25px rgba(0,0,0,0.5)', display: 'flex', flexDirection: 'column', maxHeight: '80vh' }}>
            
            <div style={{ background: '#34495e', color: 'white', padding: '15px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0 }}>📋 Últimos 50 Comprobantes Emitidos</h3>
              <button onClick={() => setModalUltimos(false)} style={{ background: 'transparent', color: 'white', border: 'none', fontSize: '20px', cursor: 'pointer' }}>✖</button>
            </div>

            <div style={{ padding: '10px', background: '#fff3cd', color: '#856404', fontSize: '13px', textAlign: 'center', borderBottom: '1px solid #ffeeba' }}>
              ℹ️ Haga clic en cualquier registro válido para seleccionarlo y buscarlo automáticamente.
            </div>

            <div style={{ overflowY: 'auto', flex: 1 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ background: '#ecf0f1', textAlign: 'left', position: 'sticky', top: 0, boxShadow: '0 2px 2px -1px rgba(0,0,0,0.1)' }}>
                    <th style={{ padding: '12px' }}>Fecha</th>
                    <th style={{ padding: '12px' }}>Tipo</th>
                    <th style={{ padding: '12px' }}>Pto. Vta</th>
                    <th style={{ padding: '12px', textAlign: 'right' }}>Número</th>
                    <th style={{ padding: '12px', textAlign: 'right' }}>Total</th>
                    <th style={{ padding: '12px', textAlign: 'center' }}>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {ultimos.map(comp => (
                    <tr 
                      key={comp.movim} 
                      onClick={() => seleccionarHistorial(comp)}
                      style={{ 
                        borderBottom: '1px solid #eee', 
                        cursor: comp.procesado === -1 ? 'not-allowed' : 'pointer',
                        background: comp.procesado === -1 ? '#f9f9f9' : 'white',
                        opacity: comp.procesado === -1 ? 0.6 : 1
                      }}
                      onMouseOver={(e) => { if (comp.procesado !== -1) e.currentTarget.style.backgroundColor = '#f1f8ff' }}
                      onMouseOut={(e) => { if (comp.procesado !== -1) e.currentTarget.style.backgroundColor = 'white' }}
                    >
                      <td style={{ padding: '12px' }}>{new Date(comp.fecha).toLocaleString()}</td>
                      <td style={{ padding: '12px', fontWeight: 'bold', color: '#2980b9' }}>{comp.tipo} {comp.letra}</td>
                      <td style={{ padding: '12px' }}>{comp.pto_vta}</td>
                      <td style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold' }}>{comp.nro}</td>
                      <td style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold', color: '#27ae60' }}>${parseFloat(comp.total).toFixed(2)}</td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        {comp.procesado === -1 
                          ? <span style={{ background: '#e74c3c', color: 'white', padding: '3px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 'bold' }}>ANULADO</span> 
                          : <span style={{ background: '#2ecc71', color: 'white', padding: '3px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 'bold' }}>VIGENTE</span>
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
          </div>
        </div>
      )}

    </div>
  );
}