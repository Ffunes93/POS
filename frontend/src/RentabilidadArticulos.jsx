import React, { useState } from 'react';

export default function RentabilidadArticulos() {
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
      // 👇 ACÁ ESTÁ LA URL CORRECTA QUE DEFINIMOS EN DJANGO
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/InformeRentabilidadArticulos/?desde=${desde}&hasta=${hasta}`);
      const data = await res.json();
      
      if (data.status === 'success') {
        setDatos(data.data);
      } else {
        alert("Error al obtener datos: " + data.mensaje);
      }
    } catch (error) {
      alert("Error de conexión con el servidor.");
    }
    setCargando(false);
  };

  return (
    <div style={{ background: 'white', padding: '20px', borderRadius: '8px', minHeight: '100%' }}>
      <h2 style={{ borderBottom: '2px solid #ecf0f1', paddingBottom: '10px', color: '#2c3e50', marginTop: 0 }}>
        📈 Consulta de Rentabilidad (Ranking de Ventas)
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
        <button type="submit" style={{ padding: '9px 20px', background: '#e67e22', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}>
          {cargando ? 'Calculando...' : 'Generar Ranking'}
        </button>
      </form>

      {/* RESULTADOS (GRILLA) */}
      {datos && (
        <div style={{ overflowX: 'auto', border: '1px solid #ddd', borderRadius: '6px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ background: '#34495e', color: 'white', textAlign: 'left' }}>
                <th style={{ padding: '10px', width: '50px', textAlign: 'center' }}>Top</th>
                <th style={{ padding: '10px' }}>Código</th>
                <th style={{ padding: '10px' }}>Descripción del Artículo</th>
                <th style={{ padding: '10px', textAlign: 'right' }}>Cant. Vendida</th>
                <th style={{ padding: '10px', textAlign: 'right' }}>Total Facturado</th>
              </tr>
            </thead>
            <tbody>
              {datos.length === 0 ? (
                <tr><td colSpan="5" style={{ padding: '20px', textAlign: 'center' }}>No hay ventas registradas en este período.</td></tr>
              ) : (
                datos.map((item, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '10px', textAlign: 'center', fontWeight: 'bold', color: idx < 3 ? '#e67e22' : '#7f8c8d' }}>
                      #{idx + 1}
                    </td>
                    <td style={{ padding: '10px', fontWeight: 'bold' }}>{item.cod_articulo}</td>
                    <td style={{ padding: '10px' }}>{item.detalle}</td>
                    <td style={{ padding: '10px', textAlign: 'right', fontWeight: 'bold' }}>
                      {parseFloat(item.cantidad_vendida).toFixed(2)}
                    </td>
                    <td style={{ padding: '10px', textAlign: 'right', fontWeight: 'bold', color: '#27ae60' }}>
                      $ {parseFloat(item.total_facturado).toFixed(2)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}