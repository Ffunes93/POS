import { useState, useEffect } from 'react';
import * as XLSX from 'xlsx';

const API = `${import.meta.env.VITE_API_URL}/api`;

export default function HistorialCompras() {
  const hoy        = new Date().toISOString().split('T')[0];
  const primerDia  = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0];

  const [desde,    setDesde]    = useState(primerDia);
  const [hasta,    setHasta]    = useState(hoy);
  const [compras,  setCompras]  = useState([]);
  const [loading,  setLoading]  = useState(false);
  const [selMovim, setSelMovim] = useState(null);
  const [detalle,  setDetalle]  = useState(null);

  const fetchCompras = async () => {
    setLoading(true);
    try {
      const res  = await fetch(`${API}/ListarCompras/?desde=${desde}&hasta=${hasta}`);
      const data = await res.json();
      if (data.status === 'success') setCompras(data.data);
    } catch {}
    setLoading(false);
  };

  useEffect(() => { fetchCompras(); }, []);

  const verDetalle = async (movim) => {
    if (selMovim === movim) { setSelMovim(null); setDetalle(null); return; }
    setSelMovim(movim);
    try {
      // Buscamos la compra por movim usando el endpoint de búsqueda
      const compra = compras.find(c => c.movim === movim);
      if (!compra) return;
      // Extraemos pto_vta y nro_comprob del comprobante legacy
      const nro_comprob = compra.nro_comprob;
      // nro_comprob legacy = pto_vta*100000000 + nro_factura
      const pto_vta = String(Math.floor(nro_comprob / 100_000_000)).padStart(4, '0');
      const nro_fac = nro_comprob % 100_000_000;
      const tipo    = compra.cod_comprob;
      const letra   = compra.comprobante_letra || 'A';
      const res = await fetch(`${API}/BuscarComprobanteCompra/?tipo=${tipo}&letra=${letra}&pto=${parseInt(pto_vta)}&nro=${nro_fac}`);
      const data = await res.json();
      if (data.status === 'success') setDetalle(data.data);
    } catch {}
  };

  const exportarExcel = () => {
    const rows = compras.map(c => ({
      'Movim':       c.movim,
      'Fecha':       new Date(c.fecha_comprob).toLocaleDateString(),
      'Tipo':        c.cod_comprob,
      'Nro':         c.nro_comprob,
      'Proveedor':   c.nom_proveedor,
      'Neto':        c.neto,
      'IVA':         c.iva_1,
      'Total':       c.tot_general,
      'Anulado':     c.anulado === 'S' ? 'SÍ' : 'No',
    }));
    const ws = XLSX.utils.json_to_sheet(rows);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Compras');
    XLSX.writeFile(wb, `Compras_${desde}_${hasta}.xlsx`);
  };

  const totalNeto = compras.filter(c => c.anulado !== 'S').reduce((s,c) => s + parseFloat(c.neto || 0), 0);
  const totalGral = compras.filter(c => c.anulado !== 'S').reduce((s,c) => s + parseFloat(c.tot_general || 0), 0);

  return (
    <div style={{ background: '#f6f8fa', padding: '4px', minHeight: '100%' }}>
      <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#24292f', fontWeight: '700' }}>
        📋 Historial de Compras
      </h2>

      {/* Filtros */}
      <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', padding: '14px 18px', marginBottom: '14px', display: 'flex', gap: '14px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
        <div>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: '#57606a', marginBottom: '4px', textTransform: 'uppercase' }}>Desde</label>
          <input type="date" value={desde} onChange={e => setDesde(e.target.value)}
            style={{ padding: '8px 10px', border: '1px solid #d0d7de', borderRadius: '5px', fontSize: '13px' }} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: '#57606a', marginBottom: '4px', textTransform: 'uppercase' }}>Hasta</label>
          <input type="date" value={hasta} onChange={e => setHasta(e.target.value)}
            style={{ padding: '8px 10px', border: '1px solid #d0d7de', borderRadius: '5px', fontSize: '13px' }} />
        </div>
        <button onClick={fetchCompras} disabled={loading} style={{
          padding: '8px 18px', background: '#0969da', color: '#fff', border: 'none',
          borderRadius: '5px', cursor: 'pointer', fontWeight: '700', fontSize: '13px',
        }}>
          {loading ? 'Cargando...' : '🔍 Filtrar'}
        </button>
        <button onClick={exportarExcel} style={{
          padding: '8px 14px', background: '#2da44e', color: '#fff', border: 'none',
          borderRadius: '5px', cursor: 'pointer', fontWeight: '700', fontSize: '13px', marginLeft: 'auto',
        }}>📊 Excel</button>
      </div>

      {/* Totales */}
      {compras.length > 0 && (
        <div style={{ display: 'flex', gap: '14px', marginBottom: '14px' }}>
          {[
            { label: 'Compras vigentes', val: compras.filter(c => c.anulado !== 'S').length, color: '#0969da' },
            { label: 'Total Neto',       val: `$${totalNeto.toFixed(2)}`,                    color: '#1a7f37' },
            { label: 'Total General',    val: `$${totalGral.toFixed(2)}`,                    color: '#8250df' },
            { label: 'Anuladas',         val: compras.filter(c => c.anulado === 'S').length, color: '#cf222e' },
          ].map(t => (
            <div key={t.label} style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '6px', padding: '12px 18px', flex: 1 }}>
              <div style={{ fontSize: '11px', color: '#57606a', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '.4px' }}>{t.label}</div>
              <div style={{ fontSize: '20px', fontWeight: '800', color: t.color, marginTop: '4px' }}>{t.val}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tabla */}
      <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: '#f6f8fa', borderBottom: '2px solid #d0d7de', textAlign: 'left' }}>
              <th style={{ padding: '10px 12px' }}>Fecha</th>
              <th style={{ padding: '10px 12px' }}>Comprobante</th>
              <th style={{ padding: '10px 12px' }}>Proveedor</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>Neto</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>IVA</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>Total</th>
              <th style={{ padding: '10px 12px', textAlign: 'center' }}>Estado</th>
              <th style={{ padding: '10px 12px', textAlign: 'center' }}>Detalle</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={8} style={{ padding: '28px', textAlign: 'center', color: '#57606a' }}>Cargando...</td></tr>
            )}
            {!loading && compras.length === 0 && (
              <tr><td colSpan={8} style={{ padding: '28px', textAlign: 'center', color: '#8c959f' }}>No hay compras en el período seleccionado.</td></tr>
            )}
            {compras.map(c => (
              <>
                <tr key={c.movim}
                  style={{ borderBottom: '1px solid #f0f0f0', background: c.anulado === 'S' ? '#fff8f8' : selMovim === c.movim ? '#f6f8fa' : '#fff' }}>
                  <td style={{ padding: '10px 12px', color: '#57606a' }}>{new Date(c.fecha_comprob).toLocaleDateString()}</td>
                  <td style={{ padding: '10px 12px', fontWeight: '700', color: '#0969da' }}>
                    {c.cod_comprob} {c.comprobante_letra || ''} — {String(c.nro_comprob).padStart(8, '0')}
                  </td>
                  <td style={{ padding: '10px 12px' }}>{c.nom_proveedor}</td>
                  <td style={{ padding: '10px 12px', textAlign: 'right' }}>${parseFloat(c.neto || 0).toFixed(2)}</td>
                  <td style={{ padding: '10px 12px', textAlign: 'right' }}>${parseFloat(c.iva_1 || 0).toFixed(2)}</td>
                  <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: '700' }}>${parseFloat(c.tot_general || 0).toFixed(2)}</td>
                  <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                    {c.anulado === 'S'
                      ? <span style={{ background: '#ffebe9', color: '#cf222e', padding: '2px 8px', borderRadius: '10px', fontSize: '11px', fontWeight: '700' }}>ANULADO</span>
                      : <span style={{ background: '#dafbe1', color: '#116329', padding: '2px 8px', borderRadius: '10px', fontSize: '11px', fontWeight: '700' }}>VIGENTE</span>
                    }
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                    <button onClick={() => verDetalle(c.movim)} style={{
                      background: 'none', border: '1px solid #d0d7de', borderRadius: '4px',
                      padding: '3px 8px', cursor: 'pointer', fontSize: '12px', color: '#0969da',
                    }}>
                      {selMovim === c.movim ? '▲ Ocultar' : '▼ Ver'}
                    </button>
                  </td>
                </tr>
                {/* Fila expandida de detalle */}
                {selMovim === c.movim && detalle && (
                  <tr key={`det-${c.movim}`}>
                    <td colSpan={8} style={{ padding: '0', background: '#f6f8fa' }}>
                      <div style={{ padding: '14px 24px' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                          <thead>
                            <tr style={{ textAlign: 'left', color: '#57606a', borderBottom: '1px solid #d0d7de' }}>
                              <th style={{ padding: '6px 10px' }}>Artículo</th>
                              <th style={{ padding: '6px 10px' }}>Descripción</th>
                              <th style={{ padding: '6px 10px', textAlign: 'right' }}>Cant.</th>
                              <th style={{ padding: '6px 10px', textAlign: 'right' }}>P. Unit.</th>
                              <th style={{ padding: '6px 10px', textAlign: 'right' }}>Total</th>
                            </tr>
                          </thead>
                          <tbody>
                            {detalle.items.map((it, idx) => (
                              <tr key={idx} style={{ borderBottom: '1px solid #f0f0f0' }}>
                                <td style={{ padding: '6px 10px', fontWeight: '700', color: '#0969da' }}>{it.cod_articulo}</td>
                                <td style={{ padding: '6px 10px' }}>{it.nom_articulo}</td>
                                <td style={{ padding: '6px 10px', textAlign: 'right' }}>{parseFloat(it.cantidad).toFixed(2)}</td>
                                <td style={{ padding: '6px 10px', textAlign: 'right' }}>${parseFloat(it.precio_unit || 0).toFixed(2)}</td>
                                <td style={{ padding: '6px 10px', textAlign: 'right', fontWeight: '700' }}>${parseFloat(it.total).toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}