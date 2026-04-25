import { useState, useEffect } from 'react';
import * as XLSX from 'xlsx';

export default function ModuloInformes() {
  const [submodulo, setSubmodulo] = useState('RANKING_VENTAS');

  const menuItems = [
    { id: 'RANKING_VENTAS', label: '🏆 Ranking de Ventas' },
    { id: 'TOTALES_CONDICION', label: '💳 Totales x Condición de Venta' },
    { id: 'TOTALES_VENDEDOR', label: '👤 Totales x Vendedor' },
    { id: 'COMPROBANTES_DET', label: '📄 Comprobantes (Detallado)' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '80vh', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', overflow: 'hidden' }}>
      
      {/* MENÚ LATERAL (Sin filtros) */}
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

      {/* ÁREA DE TRABAJO */}
      <div style={{ flex: 1, padding: '30px', background: '#f9f9f9', overflowY: 'auto' }}>
        {/* Cada componente maneja su propio estado ahora */}
        {submodulo === 'RANKING_VENTAS' && <ReporteRankingVentas />}
        {submodulo === 'TOTALES_CONDICION' && <ReporteTotalesCondicion />}
        {submodulo === 'TOTALES_VENDEDOR' && <ReporteTotalesVendedor />}
        
        {!['RANKING_VENTAS', 'TOTALES_CONDICION', 'TOTALES_VENDEDOR'].includes(submodulo) && (
          <div style={{ padding: '60px', textAlign: 'center', color: '#7f8c8d' }}>
            <h2 style={{ fontSize: '40px', margin: '0 0 10px 0' }}>🚧</h2>
            <h3>Reporte en construcción</h3>
          </div>
        )}
      </div>
    </div>
  );
}

// ==========================================
// UTILIDADES COMPARTIDAS
// ==========================================
const exportarExcel = (jsonDatos, nombreArchivo) => {
  const worksheet = XLSX.utils.json_to_sheet(jsonDatos);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Datos");
  XLSX.writeFile(workbook, `${nombreArchivo}.xlsx`);
};

// Nuevo Componente Reutilizable para Fechas
const SelectorFechas = ({ filtros, setFiltros }) => {
  const handleChange = (e) => setFiltros({ ...filtros, [e.target.name]: e.target.value });
  
  return (
    <div style={{ display: 'flex', gap: '15px', marginBottom: '20px', background: '#ecf0f1', padding: '15px', borderRadius: '6px', alignItems: 'center' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <label style={{ fontWeight: 'bold', fontSize: '14px', color: '#2c3e50' }}>Desde:</label>
        <input type="date" name="desde" value={filtros.desde} onChange={handleChange} style={{ padding: '6px', borderRadius: '4px', border: '1px solid #bdc3c7' }} />
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <label style={{ fontWeight: 'bold', fontSize: '14px', color: '#2c3e50' }}>Hasta:</label>
        <input type="date" name="hasta" value={filtros.hasta} onChange={handleChange} style={{ padding: '6px', borderRadius: '4px', border: '1px solid #bdc3c7' }} />
      </div>
    </div>
  );
};

const HeaderReporte = ({ titulo, onExcel }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px', borderBottom: '2px solid #ecf0f1', paddingBottom: '10px' }}>
    <h2 style={{ margin: 0, color: '#2c3e50', fontSize: '20px' }}>{titulo}</h2>
    <div style={{ display: 'flex', gap: '10px' }}>
      <button onClick={onExcel} style={{ padding: '8px 15px', background: '#27ae60', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
        Excel 📊
      </button>
      <button onClick={() => window.print()} style={{ padding: '8px 15px', background: '#e74c3c', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
        PDF 🖨️
      </button>
    </div>
  </div>
);

// ==========================================
// 1. REPORTE: RANKING DE VENTAS (Con filtro propio)
// ==========================================
function ReporteRankingVentas() {
  const hoy = new Date().toISOString().split('T')[0];
  const [filtros, setFiltros] = useState({ desde: hoy, hasta: hoy });
  const [datos, setDatos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`http://localhost:8001/api/InformeRentabilidadArticulos/?desde=${filtros.desde}&hasta=${filtros.hasta}`)
      .then(res => res.json())
      .then(data => { if (data.status === 'success') setDatos(data.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [filtros]);

  const handleExport = () => {
    const paraExcel = datos.map((item, idx) => ({
      Ranking: idx + 1,
      Codigo: item.cod_articulo,
      Descripcion: item.detalle,
      Cantidad: item.cantidad_vendida,
      Total: item.total_facturado
    }));
    exportarExcel(paraExcel, `Ranking_Ventas_${filtros.desde}_${filtros.hasta}`);
  };

  return (
    <div>
      <HeaderReporte titulo="🏆 Ranking de Artículos Más Vendidos" onExcel={handleExport} />
      <SelectorFechas filtros={filtros} setFiltros={setFiltros} />
      
      {loading ? <p>Cargando datos...</p> : (
        <TablaReporte 
          columnas={['Puesto', 'Código', 'Descripción', 'Cant. Vendida', 'Total ($)']}
          datos={datos.map((item, idx) => [
            `#${idx + 1}`, item.cod_articulo, item.detalle, item.cantidad_vendida, `$ ${parseFloat(item.total_facturado || 0).toFixed(2)}`
          ])}
        />
      )}
    </div>
  );
}

// ==========================================
// 2. REPORTE: TOTALES X CONDICIÓN DE VENTA (Con filtro propio)
// ==========================================
function ReporteTotalesCondicion() {
  const hoy = new Date().toISOString().split('T')[0];
  const [filtros, setFiltros] = useState({ desde: hoy, hasta: hoy });
  const [datos, setDatos] = useState([]);
  const [loading, setLoading] = useState(true);

  const mapCondicion = { '1': 'Contado Efectivo', '2': 'Cuenta Corriente', '3': 'Tarjeta Débito/Crédito' };

  useEffect(() => {
    setLoading(true);
    fetch(`http://localhost:8001/api/InformeTotalesCondicion/?desde=${filtros.desde}&hasta=${filtros.hasta}`)
      .then(res => res.json())
      .then(data => { if (data.status === 'success') setDatos(data.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [filtros]);

  const handleExport = () => {
    const paraExcel = datos.map(item => ({
      Codigo: item.cond_venta,
      Condicion: mapCondicion[item.cond_venta] || `Otra (${item.cond_venta})`,
      Operaciones: item.cantidad_operaciones,
      Total: item.total_pesos
    }));
    exportarExcel(paraExcel, `Totales_Condicion_${filtros.desde}_${filtros.hasta}`);
  };

  const granTotal = datos.reduce((acc, curr) => acc + parseFloat(curr.total_pesos || 0), 0);

  return (
    <div>
      <HeaderReporte titulo="💳 Totales por Condición de Venta" onExcel={handleExport} />
      <SelectorFechas filtros={filtros} setFiltros={setFiltros} />

      {loading ? <p>Cargando datos...</p> : (
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
// 3. REPORTE: TOTALES X VENDEDOR (Con filtro propio)
// ==========================================
function ReporteTotalesVendedor() {
  const hoy = new Date().toISOString().split('T')[0];
  const [filtros, setFiltros] = useState({ desde: hoy, hasta: hoy });
  const [datos, setDatos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`http://localhost:8001/api/InformeTotalesVendedor/?desde=${filtros.desde}&hasta=${filtros.hasta}`)
      .then(res => res.json())
      .then(data => { if (data.status === 'success') setDatos(data.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [filtros]);

  const handleExport = () => {
    const paraExcel = datos.map(item => ({
      Vendedor: `Vendedor #${item.vendedor}`,
      Operaciones: item.cantidad_operaciones,
      Total: item.total_pesos
    }));
    exportarExcel(paraExcel, `Totales_Vendedor_${filtros.desde}_${filtros.hasta}`);
  };

  const granTotal = datos.reduce((acc, curr) => acc + parseFloat(curr.total_pesos || 0), 0);

  return (
    <div>
      <HeaderReporte titulo="👤 Totales de Venta por Vendedor" onExcel={handleExport} />
      <SelectorFechas filtros={filtros} setFiltros={setFiltros} />

      {loading ? <p>Cargando datos...</p> : (
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
// COMPONENTE DE TABLA
// ==========================================
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
        <tr><td colSpan={columnas.length} style={{ padding: '20px', textAlign: 'center', color: '#95a5a6' }}>No hay datos para mostrar en estas fechas.</td></tr>
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