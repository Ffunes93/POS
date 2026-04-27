// ModuloInformes.jsx — igual que el original pero con Historial de Cajas en el menú
// (solo se agrega la entrada 'HISTORIAL_CAJAS' y su componente ReporteHistorialCajas)

import { useState, useEffect } from 'react';
import * as XLSX from 'xlsx';

const API = 'http://localhost:8001/api';

const exportarExcel = (rows, nombre) => {
  const ws = XLSX.utils.json_to_sheet(rows);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Datos');
  XLSX.writeFile(wb, `${nombre}.xlsx`);
};

const SelectorFechas = ({ filtros, setFiltros }) => (
  <div style={{ display: 'flex', gap: '14px', marginBottom: '20px', background: '#ecf0f1', padding: '14px', borderRadius: '6px', alignItems: 'center', flexWrap: 'wrap' }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <label style={{ fontWeight: 'bold', fontSize: '13px' }}>Desde:</label>
      <input type="date" value={filtros.desde} onChange={e => setFiltros({ ...filtros, desde: e.target.value })}
        style={{ padding: '6px', borderRadius: '4px', border: '1px solid #bdc3c7', fontSize: '13px' }} />
    </div>
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <label style={{ fontWeight: 'bold', fontSize: '13px' }}>Hasta:</label>
      <input type="date" value={filtros.hasta} onChange={e => setFiltros({ ...filtros, hasta: e.target.value })}
        style={{ padding: '6px', borderRadius: '4px', border: '1px solid #bdc3c7', fontSize: '13px' }} />
    </div>
  </div>
);

const TablaReporte = ({ columnas, datos, alignRight = [] }) => (
  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', background: 'white', boxShadow: '0 1px 3px rgba(0,0,0,.1)' }}>
    <thead>
      <tr style={{ background: '#ecf0f1', textAlign: 'left' }}>
        {columnas.map((c, i) => (
          <th key={i} style={{ padding: '10px 12px', borderBottom: '2px solid #bdc3c7', textAlign: alignRight.includes(i) ? 'right' : 'left' }}>{c}</th>
        ))}
      </tr>
    </thead>
    <tbody>
      {datos.length === 0 ? (
        <tr><td colSpan={columnas.length} style={{ padding: '20px', textAlign: 'center', color: '#95a5a6' }}>Sin datos.</td></tr>
      ) : datos.map((fila, i) => (
        <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
          {fila.map((celda, j) => (
            <td key={j} style={{ padding: '10px 12px', textAlign: alignRight.includes(j) ? 'right' : 'left' }}>{celda}</td>
          ))}
        </tr>
      ))}
    </tbody>
  </table>
);

const HeaderReporte = ({ titulo, onExcel }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', borderBottom: '2px solid #ecf0f1', paddingBottom: '10px' }}>
    <h2 style={{ margin: 0, fontSize: '18px', color: '#2c3e50' }}>{titulo}</h2>
    <div style={{ display: 'flex', gap: '8px' }}>
      <button onClick={onExcel} style={{ padding: '7px 14px', background: '#27ae60', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' }}>📊 Excel</button>
      <button onClick={() => window.print()} style={{ padding: '7px 14px', background: '#e74c3c', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' }}>🖨️ PDF</button>
    </div>
  </div>
);

// ── Historial de Cajas (nuevo) ────────────────────────────────────────────────
function ReporteHistorialCajas() {
  const hoy    = new Date().toISOString().split('T')[0];
  const primer = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0];
  const [filtros, setFiltros] = useState({ desde: primer, hasta: hoy });
  const [datos,   setDatos]   = useState([]);
  const [loading, setLoading] = useState(false);

  const cargar = async () => {
    setLoading(true);
    const r = await fetch(`${API}/InformeHistorialCajas/?desde=${filtros.desde}&hasta=${filtros.hasta}`);
    const d = await r.json();
    if (d.status === 'success') setDatos(d.data);
    setLoading(false);
  };

  useEffect(() => { cargar(); }, [filtros]);

  const totalVentas = datos.reduce((s, c) => s + parseFloat(c.ventas || 0), 0);

  return (
    <div>
      <HeaderReporte titulo="🏧 Historial de Cajas" onExcel={() => exportarExcel(datos.map(c => ({
        'N° Caja': c.id, Cajero: c.cajero,
        'Fecha Apertura': new Date(c.fecha_open).toLocaleString(),
        'Fecha Cierre': c.fecha_close ? new Date(c.fecha_close).toLocaleString() : '',
        'Fondo Ini.': c.saldo_ini_billetes, Ventas: c.ventas,
        Egresos: c.otros_egresos, 'Final Decl.': c.saldo_final_billetes,
        Diferencia: c.dife_billetes,
      })), `HistorialCajas_${filtros.desde}`)} />
      <SelectorFechas filtros={filtros} setFiltros={setFiltros} />

      {datos.length > 0 && (
        <div style={{ display: 'flex', gap: '12px', marginBottom: '14px' }}>
          {[
            { label: 'Turnos cerrados', val: datos.length, color: '#0969da' },
            { label: 'Total ventas', val: `$${totalVentas.toFixed(2)}`, color: '#1a7f37' },
            { label: 'Con diferencias', val: datos.filter(c => c.con_diferencias).length, color: '#cf222e' },
          ].map(t => (
            <div key={t.label} style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '6px', padding: '10px 16px', flex: 1 }}>
              <div style={{ fontSize: '11px', color: '#57606a', fontWeight: '700', textTransform: 'uppercase' }}>{t.label}</div>
              <div style={{ fontSize: '20px', fontWeight: '800', color: t.color }}>{t.val}</div>
            </div>
          ))}
        </div>
      )}

      {loading ? <p>Cargando...</p> : (
        <TablaReporte
          columnas={['N° Caja', 'Cajero', 'Apertura', 'Cierre', 'Fondo Ini.', 'Ventas', 'Egresos', 'Final Decl.', 'Diferencia']}
          alignRight={[4, 5, 6, 7, 8]}
          datos={datos.map(c => [
            c.id, c.cajero,
            new Date(c.fecha_open).toLocaleString(),
            c.fecha_close ? new Date(c.fecha_close).toLocaleString() : '—',
            `$${parseFloat(c.saldo_ini_billetes || 0).toFixed(2)}`,
            `$${parseFloat(c.ventas || 0).toFixed(2)}`,
            `$${parseFloat(c.otros_egresos || 0).toFixed(2)}`,
            `$${parseFloat(c.saldo_final_billetes || 0).toFixed(2)}`,
            <span style={{ color: parseFloat(c.dife_billetes || 0) !== 0 ? '#cf222e' : '#1a7f37', fontWeight: '700' }}>
              ${parseFloat(c.dife_billetes || 0).toFixed(2)}
            </span>,
          ])}
        />
      )}
    </div>
  );
}

// ── Los demás reportes (idénticos al original) ────────────────────────────────
function ReporteRankingVentas() {
  const hoy = new Date().toISOString().split('T')[0];
  const [filtros, setFiltros] = useState({ desde: hoy, hasta: hoy });
  const [datos, setDatos] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    setLoading(true);
    fetch(`${API}/InformeRentabilidadArticulos/?desde=${filtros.desde}&hasta=${filtros.hasta}`)
      .then(r => r.json()).then(d => { if (d.status === 'success') setDatos(d.data); setLoading(false); });
  }, [filtros]);
  return (
    <div>
      <HeaderReporte titulo="🏆 Ranking de Artículos Más Vendidos" onExcel={() => exportarExcel(datos.map((i, idx) => ({ Ranking: idx+1, Codigo: i.cod_articulo, Descripcion: i.detalle, Cantidad: i.cantidad_vendida, Total: i.total_facturado })), `Ranking_${filtros.desde}`)} />
      <SelectorFechas filtros={filtros} setFiltros={setFiltros} />
      {loading ? <p>Cargando...</p> : <TablaReporte columnas={['#', 'Código', 'Descripción', 'Cant.', 'Total ($)']} datos={datos.map((i, idx) => [`#${idx+1}`, i.cod_articulo, i.detalle, i.cantidad_vendida, `$${parseFloat(i.total_facturado||0).toFixed(2)}`])} alignRight={[3, 4]} />}
    </div>
  );
}
function ReporteTotalesCondicion() {
  const hoy = new Date().toISOString().split('T')[0];
  const [filtros, setFiltros] = useState({ desde: hoy, hasta: hoy });
  const [datos, setDatos] = useState([]);
  const [loading, setLoading] = useState(true);
  const mapCond = { '1': 'Contado', '2': 'Cta. Corriente' };
  useEffect(() => { setLoading(true); fetch(`${API}/InformeTotalesCondicion/?desde=${filtros.desde}&hasta=${filtros.hasta}`).then(r => r.json()).then(d => { if (d.status === 'success') setDatos(d.data); setLoading(false); }); }, [filtros]);
  return (
    <div>
      <HeaderReporte titulo="💳 Totales por Condición de Venta" onExcel={() => exportarExcel(datos.map(i => ({ Cond: i.cond_venta, Descripcion: mapCond[i.cond_venta]||i.cond_venta, Operaciones: i.cantidad_operaciones, Total: i.total_pesos })), 'TotalesCondicion')} />
      <SelectorFechas filtros={filtros} setFiltros={setFiltros} />
      {loading ? <p>Cargando...</p> : <TablaReporte columnas={['Código', 'Condición', 'Operaciones', 'Total ($)']} alignRight={[2, 3]} datos={datos.map(i => [i.cond_venta, mapCond[i.cond_venta]||i.cond_venta, i.cantidad_operaciones, `$${parseFloat(i.total_pesos||0).toFixed(2)}`])} />}
    </div>
  );
}
function ReporteTotalesVendedor() {
  const hoy = new Date().toISOString().split('T')[0];
  const [filtros, setFiltros] = useState({ desde: hoy, hasta: hoy });
  const [datos, setDatos] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => { setLoading(true); fetch(`${API}/InformeTotalesVendedor/?desde=${filtros.desde}&hasta=${filtros.hasta}`).then(r => r.json()).then(d => { if (d.status === 'success') setDatos(d.data); setLoading(false); }); }, [filtros]);
  return (
    <div>
      <HeaderReporte titulo="👤 Totales por Vendedor" onExcel={() => exportarExcel(datos.map(i => ({ Vendedor: `#${i.vendedor}`, Operaciones: i.cantidad_operaciones, Total: i.total_pesos })), 'TotalesVendedor')} />
      <SelectorFechas filtros={filtros} setFiltros={setFiltros} />
      {loading ? <p>Cargando...</p> : <TablaReporte columnas={['Vendedor', 'Operaciones', 'Total ($)']} alignRight={[1, 2]} datos={datos.map(i => [`Vendedor #${i.vendedor}`, i.cantidad_operaciones, `$${parseFloat(i.total_pesos||0).toFixed(2)}`])} />}
    </div>
  );
}
function ReporteStockActual() {
  const [datos, setDatos] = useState(null); const [loading, setLoading] = useState(false); const [buscar, setBuscar] = useState(''); const [criticos, setCriticos] = useState(false);
  const cargar = async () => { setLoading(true); const r = await fetch(`${API}/InformeStockActual/?buscar=${buscar}${criticos ? '&solo_criticos=1' : ''}`); const d = await r.json(); if (d.status === 'success') setDatos(d); setLoading(false); };
  useEffect(() => { cargar(); }, []);
  return (
    <div>
      <HeaderReporte titulo="📦 Stock Actual" onExcel={() => datos && exportarExcel(datos.data.map(a => ({ Codigo: a.cod_art, Nombre: a.nombre, Stock: a.stock, StockMin: a.stock_min, Costo: a.costo_ult, Precio: a.precio_1 })), 'StockActual')} />
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', alignItems: 'center', background: '#ecf0f1', padding: '14px', borderRadius: '6px' }}>
        <input type="text" placeholder="Buscar..." value={buscar} onChange={e => setBuscar(e.target.value)} style={{ padding: '7px 10px', borderRadius: '4px', border: '1px solid #ccc', flex: 1 }} />
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '13px' }}><input type="checkbox" checked={criticos} onChange={e => setCriticos(e.target.checked)} />Solo críticos</label>
        <button onClick={cargar} style={{ padding: '7px 16px', background: '#0969da', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: '700' }}>{loading ? '...' : '🔍'}</button>
      </div>
      {datos && <TablaReporte columnas={['Código', 'Nombre', 'Stock', 'Mín.', 'Costo', 'Precio']} alignRight={[2, 3, 4, 5]} datos={datos.data.map(a => [a.cod_art, a.nombre, parseFloat(a.stock||0).toFixed(2), parseFloat(a.stock_min||0).toFixed(2), `$${parseFloat(a.costo_ult||0).toFixed(2)}`, `$${parseFloat(a.precio_1||0).toFixed(2)}`])} />}
    </div>
  );
}
function ReporteCtaCte() {
  const [datos, setDatos] = useState(null); const [loading, setLoading] = useState(true);
  useEffect(() => { fetch(`${API}/InformeCtaCteClientes/`).then(r => r.json()).then(d => { if (d.status === 'success') setDatos(d); setLoading(false); }); }, []);
  return (
    <div>
      <HeaderReporte titulo="💳 Cartera de Clientes (Cta. Cte.)" onExcel={() => datos && exportarExcel(datos.clientes.map(c => ({ Codigo: c.cod_cli_id, Nombre: c.denominacion, Facturas: c.cant_facturas, Deuda: c.total_deuda })), 'CartaClientes')} />
      {loading ? <p>Cargando...</p> : datos && <>
        <div style={{ background: '#fff3cd', border: '1px solid #f0c000', borderRadius: '6px', padding: '12px 18px', marginBottom: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: '700', color: '#735c0f' }}>💰 Total en cartera:</span>
          <span style={{ fontSize: '22px', fontWeight: '800', color: '#cf222e' }}>${parseFloat(datos.total_cartera||0).toFixed(2)}</span>
        </div>
        <TablaReporte columnas={['Cód.', 'Cliente', 'Facturas pend.', 'Total deuda ($)']} alignRight={[2, 3]} datos={datos.clientes.map(c => [c.cod_cli_id, c.denominacion, c.cant_facturas, `$${parseFloat(c.total_deuda||0).toFixed(2)}`])} />
      </>}
    </div>
  );
}
function ReporteEgresos() {
  const hoy = new Date().toISOString().split('T')[0];
  const primer = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0];
  const [filtros, setFiltros] = useState({ desde: primer, hasta: hoy }); const [datos, setDatos] = useState(null); const [loading, setLoading] = useState(false);
  const cargar = async () => { setLoading(true); const r = await fetch(`${API}/InformeEgresos/?desde=${filtros.desde}&hasta=${filtros.hasta}`); const d = await r.json(); if (d.status === 'success') setDatos(d); setLoading(false); };
  useEffect(() => { cargar(); }, [filtros]);
  return (
    <div>
      <HeaderReporte titulo="📥 Libro de Compras / Egresos" onExcel={() => datos && exportarExcel(datos.comprobantes.map(c => ({ Fecha: new Date(c.fecha_comprob).toLocaleDateString(), Comprobante: `${c.cod_comprob} ${c.nro_comprob}`, Proveedor: c.nom_proveedor, Neto: c.neto, IVA: c.iva_1, Total: c.tot_general })), 'LibroCompras')} />
      <SelectorFechas filtros={filtros} setFiltros={setFiltros} />
      {loading ? <p>Cargando...</p> : datos && <TablaReporte columnas={['Fecha', 'Comprobante', 'Proveedor', 'Neto', 'IVA', 'Total']} alignRight={[3, 4, 5]} datos={datos.comprobantes.map(c => [new Date(c.fecha_comprob).toLocaleDateString(), `${c.cod_comprob}${c.comprobante_letra||''} ${c.nro_comprob}`, c.nom_proveedor, `$${parseFloat(c.neto||0).toFixed(2)}`, `$${parseFloat(c.iva_1||0).toFixed(2)}`, `$${parseFloat(c.tot_general||0).toFixed(2)}`])} />}
    </div>
  );
}

// ── Módulo principal ──────────────────────────────────────────────────────────
export default function ModuloInformes() {
  const [submodulo, setSubmodulo] = useState('RANKING_VENTAS');

  const menuItems = [
    { id: 'RANKING_VENTAS',    label: '🏆 Ranking de Ventas' },
    { id: 'TOTALES_CONDICION', label: '💳 Totales x Condición' },
    { id: 'TOTALES_VENDEDOR',  label: '👤 Totales x Vendedor' },
    { id: 'STOCK_ACTUAL',      label: '📦 Stock Actual' },
    { id: 'CTA_CTE',           label: '💳 Cartera Cta. Cte.' },
    { id: 'EGRESOS',           label: '📥 Libro de Compras' },
    { id: 'HISTORIAL_CAJAS',   label: '🏧 Historial de Cajas' },  // ← NUEVO
  ];

  return (
    <div style={{ display: 'flex', minHeight: '80vh', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', overflow: 'hidden' }}>
      <div style={{ width: '240px', background: '#2c3e50', color: 'white', flexShrink: 0 }}>
        <div style={{ padding: '18px 20px', background: '#1a252f', fontWeight: '700', fontSize: '15px', color: '#f1c40f', borderBottom: '1px solid rgba(255,255,255,.1)' }}>
          📊 Informes
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', padding: '8px 0' }}>
          {menuItems.map(item => (
            <button key={item.id} onClick={() => setSubmodulo(item.id)} style={{
              padding: '13px 20px', textAlign: 'left', background: submodulo === item.id ? '#34495e' : 'transparent',
              color: submodulo === item.id ? '#2ecc71' : '#ecf0f1', border: 'none',
              borderLeft: submodulo === item.id ? '4px solid #2ecc71' : '4px solid transparent',
              cursor: 'pointer', fontSize: '13px', fontWeight: submodulo === item.id ? '700' : '400',
            }}>{item.label}</button>
          ))}
        </div>
      </div>
      <div style={{ flex: 1, padding: '24px', background: '#f9f9f9', overflowY: 'auto' }}>
        {submodulo === 'RANKING_VENTAS'    && <ReporteRankingVentas />}
        {submodulo === 'TOTALES_CONDICION' && <ReporteTotalesCondicion />}
        {submodulo === 'TOTALES_VENDEDOR'  && <ReporteTotalesVendedor />}
        {submodulo === 'STOCK_ACTUAL'      && <ReporteStockActual />}
        {submodulo === 'CTA_CTE'           && <ReporteCtaCte />}
        {submodulo === 'EGRESOS'           && <ReporteEgresos />}
        {submodulo === 'HISTORIAL_CAJAS'   && <ReporteHistorialCajas />}
      </div>
    </div>
  );
}