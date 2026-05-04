import React, { useState } from 'react';

export default function LibroIVAVentas() {
  // Por defecto, ponemos el primer día y el último día del mes actual
  const hoy = new Date();
  const primerDia = new Date(hoy.getFullYear(), hoy.getMonth(), 1).toISOString().split('T')[0];
  const ultimoDia = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 0).toISOString().split('T')[0];

  const [desde, setDesde] = useState(primerDia);
  const [hasta, setHasta] = useState(ultimoDia);
  
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(false);

  const generarInforme = async (e) => {
    if (e) e.preventDefault();
    setCargando(true);
    
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/InformeLibroIVAVentas/?desde=${desde}&hasta=${hasta}`);
      const data = await res.json();
      
      if (data.status === 'success') {
        setDatos(data);
      } else {
        alert("Error al obtener datos: " + data.mensaje);
      }
    } catch (error) {
      alert("Error de conexión con el servidor.");
    }
    setCargando(false);
  };

  const imprimirReporte = () => {
    window.print();
  };

  return (
    <div style={{ background: 'white', padding: '20px', borderRadius: '8px', minHeight: '100%' }}>
      <h2 style={{ borderBottom: '2px solid #ecf0f1', paddingBottom: '10px', color: '#2c3e50', marginTop: 0 }}>
        📘 Libro IVA Ventas
      </h2>

      {/* FILTROS DE BÚSQUEDA */}
      <form onSubmit={generarInforme} style={{ display: 'flex', gap: '15px', alignItems: 'flex-end', background: '#ecf0f1', padding: '15px', borderRadius: '6px', marginBottom: '20px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d' }}>Fecha Desde</label>
          <input type="date" value={desde} onChange={e => setDesde(e.target.value)} style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} required />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d' }}>Fecha Hasta</label>
          <input type="date" value={hasta} onChange={e => setHasta(e.target.value)} style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} required />
        </div>
        <button type="submit" style={{ padding: '9px 20px', background: '#2980b9', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}>
          {cargando ? 'Calculando...' : 'Generar Informe'}
        </button>
        
        {datos && (
          <button type="button" onClick={imprimirReporte} style={{ padding: '9px 20px', background: '#27ae60', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', marginLeft: 'auto' }}>
            🖨️ Imprimir
          </button>
        )}
      </form>

      {/* RESULTADOS */}
      {datos && (
        <>
          {/* TARJETAS DE TOTALES */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '15px', marginBottom: '20px' }}>
            <div style={{ background: '#f8f9fa', padding: '15px', borderRadius: '6px', borderLeft: '4px solid #3498db' }}>
              <div style={{ fontSize: '12px', color: '#7f8c8d', fontWeight: 'bold' }}>TOTAL NETO GRAVADO</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#2c3e50' }}>$ {(datos.totales.suma_neto || 0).toFixed(2)}</div>
            </div>
            <div style={{ background: '#f8f9fa', padding: '15px', borderRadius: '6px', borderLeft: '4px solid #e74c3c' }}>
              <div style={{ fontSize: '12px', color: '#7f8c8d', fontWeight: 'bold' }}>TOTAL IVA (21%)</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#2c3e50' }}>$ {(datos.totales.suma_iva || 0).toFixed(2)}</div>
            </div>
            <div style={{ background: '#f8f9fa', padding: '15px', borderRadius: '6px', borderLeft: '4px solid #f1c40f' }}>
              <div style={{ fontSize: '12px', color: '#7f8c8d', fontWeight: 'bold' }}>TOTAL EXENTO</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#2c3e50' }}>$ {(datos.totales.suma_exento || 0).toFixed(2)}</div>
            </div>
            <div style={{ background: '#e8f8f5', padding: '15px', borderRadius: '6px', borderLeft: '4px solid #27ae60' }}>
              <div style={{ fontSize: '12px', color: '#27ae60', fontWeight: 'bold' }}>TOTAL FACTURADO</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#27ae60' }}>$ {(datos.totales.suma_total || 0).toFixed(2)}</div>
            </div>
          </div>

          {/* GRILLA DE COMPROBANTES */}
          <div style={{ overflowX: 'auto', border: '1px solid #ddd', borderRadius: '6px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ background: '#34495e', color: 'white', textAlign: 'left' }}>
                  <th style={{ padding: '10px' }}>Fecha</th>
                  <th style={{ padding: '10px' }}>Comprobante</th>
                  <th style={{ padding: '10px' }}>Cód. Cliente</th>
                  <th style={{ padding: '10px', textAlign: 'right' }}>Neto</th>
                  <th style={{ padding: '10px', textAlign: 'right' }}>IVA</th>
                  <th style={{ padding: '10px', textAlign: 'right' }}>Total</th>
                </tr>
              </thead>
              <tbody>
                {datos.comprobantes.length === 0 ? (
                  <tr><td colSpan="6" style={{ padding: '20px', textAlign: 'center' }}>No hay comprobantes en esta fecha.</td></tr>
                ) : (
                  datos.comprobantes.map((comp, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '10px' }}>{new Date(comp.fecha_fact).toLocaleDateString()}</td>
                      <td style={{ padding: '10px', fontWeight: 'bold' }}>{comp.cod_comprob} - {comp.comprobante_pto_vta} - {comp.nro_comprob.toString().padStart(8, '0')}</td>
                      <td style={{ padding: '10px' }}>{comp.cod_cli}</td>
                      <td style={{ padding: '10px', textAlign: 'right' }}>$ {parseFloat(comp.neto).toFixed(2)}</td>
                      <td style={{ padding: '10px', textAlign: 'right' }}>$ {parseFloat(comp.iva_1).toFixed(2)}</td>
                      <td style={{ padding: '10px', textAlign: 'right', fontWeight: 'bold', color: '#27ae60' }}>$ {parseFloat(comp.tot_general).toFixed(2)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}