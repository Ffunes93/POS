import { useState, useEffect } from 'react';

export default function ModuloInformes() {
  const [submodulo, setSubmodulo] = useState('RANKING_VENTAS');

  // Menú calcado de tu sistema Legacy
  const menuItems = [
    { id: 'COMPROBANTES_DET', label: '📄 Comprobantes (Detallado)' },
    { id: 'COMPROBANTES_RES', label: '📄 Comprobantes (Resumido)' },
    { id: 'RANKING_VENTAS', label: '🏆 Ranking de Ventas' },
    { id: 'TOTALES_CONDICION', label: '💳 Totales x Condición de Venta' },
    { id: 'TOTALES_VENDEDOR', label: '👤 Totales x Vendedor' },
    { id: 'TOTALES_RUBRO', label: '📦 Totales x Rubro' },
    { id: 'COMISIONES', label: '💰 Comisiones x Vendedor' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '80vh', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', overflow: 'hidden' }}>
      
      {/* MENÚ LATERAL */}
      <div style={{ width: '280px', background: '#2c3e50', color: 'white', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '20px', background: '#1a252f', fontWeight: 'bold', fontSize: '16px', color: '#f1c40f', borderBottom: '1px solid #34495e' }}>
          📊 Informes de Ventas
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', padding: '10px 0' }}>
          {menuItems.map(item => (
            <button
              key={item.id}
              onClick={() => setSubmodulo(item.id)}
              style={{
                padding: '15px 20px', textAlign: 'left', background: submodulo === item.id ? '#34495e' : 'transparent',
                color: submodulo === item.id ? '#2ecc71' : '#ecf0f1', border: 'none', borderLeft: submodulo === item.id ? '4px solid #2ecc71' : '4px solid transparent',
                cursor: 'pointer', fontSize: '13px', transition: 'all 0.2s', fontWeight: submodulo === item.id ? 'bold' : 'normal'
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* ÁREA DE TRABAJO (DERECHA) */}
      <div style={{ flex: 1, padding: '30px', background: '#f9f9f9', overflowY: 'auto' }}>
        
        {submodulo === 'RANKING_VENTAS' && <ReporteRankingVentas />}
        {submodulo === 'TOTALES_CONDICION' && <ReporteTotalesCondicion />}
        {submodulo === 'TOTALES_VENDEDOR' && <ReporteTotalesVendedor />}
        
        {/* Placeholders para los que faltan */}
        {!['RANKING_VENTAS', 'TOTALES_CONDICION', 'TOTALES_VENDEDOR'].includes(submodulo) && (
          <div style={{ padding: '60px', textAlign: 'center', color: '#7f8c8d' }}>
            <h2 style={{ fontSize: '40px', margin: '0 0 10px 0' }}>🚧</h2>
            <h3>Reporte en construcción</h3>
            <p>Próximamente conectaremos este informe con las tablas correspondientes.</p>
          </div>
        )}

      </div>
    </div>
  );
}

// ==========================================
// 1. REPORTE: RANKING DE VENTAS (Mantenemos el que ya funcionaba)
// ==========================================
function ReporteRankingVentas() {
  const [datos, setDatos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8001/api/InformeRankingVentas/')
      .then(res => res.json())
      .then(data => { if (data.status === 'success') setDatos(data.data); setLoading(false); })
      .catch(() => { alert("Error cargando reporte."); setLoading(false); });
  }, []);

  return (
    <div>
      <HeaderReporte titulo="🏆 Ranking de Artículos Más Vendidos" />
      {loading ? <p>Cargando...</p> : (
        <TablaReporte 
          columnas={['Puesto', 'Código', 'Descripción', 'Cant. Vendida', 'Total Recaudado ($)']}
          datos={datos.map((item, idx) => [
            `#${idx + 1}`, item.cod_articulo, item.detalle || '-', item.total_vendido, `$ ${parseFloat(item.total_pesos || 0).toFixed(2)}`
          ])}
        />
      )}
    </div>
  );
}

// ==========================================
// 2. REPORTE: TOTALES X CONDICIÓN DE VENTA
// ==========================================
function ReporteTotalesCondicion() {
  const [datos, setDatos] = useState([]);
  const [loading, setLoading] = useState(true);

  // Diccionario para traducir el código legacy a texto legible
  const mapCondicion = { '1': 'Contado Efectivo', '2': 'Cuenta Corriente', '3': 'Tarjeta Débito/Crédito' };

  useEffect(() => {
    fetch('http://localhost:8001/api/InformeTotalesCondicion/')
      .then(res => res.json())
      .then(data => { if (data.status === 'success') setDatos(data.data); setLoading(false); })
      .catch(() => { alert("Error cargando reporte."); setLoading(false); });
  }, []);

  // Calculamos el gran total para el pie de la tabla
  const granTotal = datos.reduce((acc, curr) => acc + parseFloat(curr.total_pesos || 0), 0);

  return (
    <div>
      <HeaderReporte titulo="💳 Totales por Condición de Venta" />
      {loading ? <p>Cargando...</p> : (
        <>
          <TablaReporte 
            columnas={['Código', 'Condición de Venta', 'Cant. Operaciones', 'Monto Total ($)']}
            datos={datos.map(item => [
              item.cond_venta,
              mapCondicion[item.cond_venta] || `Otra (${item.cond_venta})`,
              item.cantidad_operaciones,
              `$ ${parseFloat(item.total_pesos || 0).toFixed(2)}`
            ])}
          />
          <div style={{ textAlign: 'right', marginTop: '20px', fontSize: '20px', color: '#27ae60' }}>
            <b>Total General:</b> $ {granTotal.toFixed(2)}
          </div>
        </>
      )}
    </div>
  );
}

// ==========================================
// 3. REPORTE: TOTALES X VENDEDOR
// ==========================================
function ReporteTotalesVendedor() {
  const [datos, setDatos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8001/api/InformeTotalesVendedor/')
      .then(res => res.json())
      .then(data => { if (data.status === 'success') setDatos(data.data); setLoading(false); })
      .catch(() => { alert("Error cargando reporte."); setLoading(false); });
  }, []);

  const granTotal = datos.reduce((acc, curr) => acc + parseFloat(curr.total_pesos || 0), 0);

  return (
    <div>
      <HeaderReporte titulo="👤 Totales de Venta por Vendedor" />
      {loading ? <p>Cargando...</p> : (
        <>
          <TablaReporte 
            columnas={['ID Vendedor', 'Tickets Emitidos', 'Monto Facturado ($)']}
            datos={datos.map(item => [
              `Vendedor #${item.vendedor}`,
              item.cantidad_operaciones,
              `$ ${parseFloat(item.total_pesos || 0).toFixed(2)}`
            ])}
          />
          <div style={{ textAlign: 'right', marginTop: '20px', fontSize: '20px', color: '#27ae60' }}>
            <b>Total General:</b> $ {granTotal.toFixed(2)}
          </div>
        </>
      )}
    </div>
  );
}

// ==========================================
// COMPONENTES AUXILIARES DE UI PARA REPORTES
// ==========================================
const HeaderReporte = ({ titulo }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '2px solid #ecf0f1', paddingBottom: '10px' }}>
    <h2 style={{ margin: 0, color: '#2c3e50' }}>{titulo}</h2>
    <button onClick={() => window.print()} style={{ padding: '8px 15px', background: '#e74c3c', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
      🖨️ Exportar PDF
    </button>
  </div>
);

const TablaReporte = ({ columnas, datos }) => (
  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px', background: 'white', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
    <thead>
      <tr style={{ background: '#ecf0f1', textAlign: 'left' }}>
        {columnas.map((col, idx) => (
          <th key={idx} style={{ padding: '12px', borderBottom: '2px solid #bdc3c7', textAlign: idx >= columnas.length - 2 ? 'right' : 'left' }}>{col}</th>
        ))}
      </tr>
    </thead>
    <tbody>
      {datos.length === 0 ? (
        <tr><td colSpan={columnas.length} style={{ padding: '20px', textAlign: 'center', color: '#95a5a6' }}>No hay datos para mostrar.</td></tr>
      ) : datos.map((fila, i) => (
        <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
          {fila.map((celda, j) => (
            <td key={j} style={{ padding: '12px', textAlign: j >= fila.length - 2 ? 'right' : 'left', fontWeight: j === fila.length - 1 ? 'bold' : 'normal', color: j === fila.length - 1 ? '#27ae60' : 'inherit' }}>
              {celda}
            </td>
          ))}
        </tr>
      ))}
    </tbody>
  </table>
);