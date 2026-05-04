import { useState } from 'react';

const API = `${import.meta.env.VITE_API_URL}/api`;

export default function AnulacionCompraComprobantes() {
  const [busqueda, setBusqueda]       = useState({ tipo: 'F', letra: 'A', pto: '1', nro: '' });
  const [comprobante, setComprobante] = useState(null);
  const [cargando, setCargando]       = useState(false);
  const [msg, setMsg]                 = useState(null);

  const buscar = async (e) => {
    e?.preventDefault();
    if (!busqueda.nro) return setMsg({ tipo: 'error', texto: 'Ingrese un número de comprobante.' });
    setCargando(true); setComprobante(null); setMsg(null);
    try {
      const tipo = busqueda.tipo + busqueda.letra;
      const res = await fetch(
        `${API}/BuscarComprobanteCompra/?tipo=${tipo}&letra=${busqueda.letra}&pto=${busqueda.pto}&nro=${busqueda.nro}`
      );
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setComprobante(data.data);
      } else {
        setMsg({ tipo: 'error', texto: data.mensaje || 'No encontrado.' });
      }
    } catch {
      setMsg({ tipo: 'error', texto: 'Error de conexión.' });
    }
    setCargando(false);
  };

  const anular = async () => {
    if (!comprobante) return;
    if (!window.confirm(
      `⚠️ ¿Confirmar anulación de la compra por $${parseFloat(comprobante.total).toFixed(2)}?\n\nEsta acción revertirá el stock de todos los artículos.`
    )) return;

    setCargando(true);
    try {
      const res = await fetch(`${API}/AnularComprobanteCompra/`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ movim: comprobante.movim }),
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setMsg({ tipo: 'ok', texto: '✅ ' + data.mensaje });
        setComprobante(null);
        setBusqueda({ ...busqueda, nro: '' });
      } else {
        setMsg({ tipo: 'error', texto: data.mensaje });
      }
    } catch {
      setMsg({ tipo: 'error', texto: 'Error de conexión.' });
    }
    setCargando(false);
  };

  const yaAnulado = comprobante?.anulado === 'S';

  return (
    <div style={{ background: '#f6f8fa', padding: '4px', minHeight: '100%' }}>
      <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#24292f', fontWeight: '700' }}>
        🚫 Anulación de Comprobante de Compra
      </h2>

      {msg && (
        <div style={{
          padding: '10px 16px', borderRadius: '6px', marginBottom: '14px', fontSize: '13px', fontWeight: '600',
          background: msg.tipo === 'ok' ? '#dafbe1' : '#ffebe9',
          color:      msg.tipo === 'ok' ? '#116329' : '#a40e26',
          border:     `1px solid ${msg.tipo === 'ok' ? '#56d364' : '#ff818266'}`,
        }}>{msg.texto}</div>
      )}

      {/* Buscador */}
      <form onSubmit={buscar} style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', padding: '18px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: '#57606a', marginBottom: '4px', textTransform: 'uppercase' }}>Tipo</label>
            <select value={busqueda.tipo} onChange={e => setBusqueda({ ...busqueda, tipo: e.target.value })}
              style={{ padding: '9px 10px', border: '1px solid #d0d7de', borderRadius: '5px', fontSize: '14px' }}>
              <option value="F">Factura (F)</option>
              <option value="N">Nota Débito (N)</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: '#57606a', marginBottom: '4px', textTransform: 'uppercase' }}>Letra</label>
            <select value={busqueda.letra} onChange={e => setBusqueda({ ...busqueda, letra: e.target.value })}
              style={{ padding: '9px 10px', border: '1px solid #d0d7de', borderRadius: '5px', fontSize: '14px' }}>
              <option>A</option><option>B</option><option>C</option><option>X</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: '#57606a', marginBottom: '4px', textTransform: 'uppercase' }}>Pto. Venta</label>
            <input type="number" value={busqueda.pto} onChange={e => setBusqueda({ ...busqueda, pto: e.target.value })}
              style={{ width: '70px', padding: '9px 10px', border: '1px solid #d0d7de', borderRadius: '5px', fontSize: '14px' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: '#57606a', marginBottom: '4px', textTransform: 'uppercase' }}>N° Comprobante</label>
            <input autoFocus type="number" value={busqueda.nro} onChange={e => setBusqueda({ ...busqueda, nro: e.target.value })}
              placeholder="ej: 12345"
              style={{ width: '130px', padding: '9px 10px', border: '1px solid #d0d7de', borderRadius: '5px', fontSize: '14px' }} />
          </div>
          <button type="submit" disabled={cargando} style={{
            padding: '9px 20px', background: '#0969da', color: '#fff', border: 'none',
            borderRadius: '5px', cursor: 'pointer', fontWeight: '700',
          }}>
            {cargando ? 'Buscando...' : '🔍 Buscar'}
          </button>
        </div>
      </form>

      {/* Resultado */}
      {comprobante && (
        <div style={{ background: '#fff', border: `1px solid ${yaAnulado ? '#cf222e' : '#d0d7de'}`, borderRadius: '8px', overflow: 'hidden' }}>
          <div style={{
            background: yaAnulado ? '#ffebe9' : '#dafbe1', padding: '14px 18px',
            borderBottom: '1px solid #d0d7de', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{ fontWeight: '700', color: yaAnulado ? '#a40e26' : '#116329' }}>
              {yaAnulado ? '⛔ COMPROBANTE ANULADO' : '✅ Comprobante encontrado'}
            </span>
            <span style={{ fontWeight: '800', fontSize: '16px' }}>
              Total: ${parseFloat(comprobante.total).toFixed(2)}
            </span>
          </div>

          <div style={{ padding: '18px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '16px', marginBottom: '16px', fontSize: '13px' }}>
              <div><span style={{ color: '#57606a' }}>Proveedor: </span><b>{comprobante.nom_proveedor}</b></div>
              <div><span style={{ color: '#57606a' }}>Comprobante: </span><b>{comprobante.cod_comprob} N° {comprobante.nro_comprob}</b></div>
              <div><span style={{ color: '#57606a' }}>Fecha: </span><b>{new Date(comprobante.fecha_comprob).toLocaleDateString()}</b></div>
              <div><span style={{ color: '#57606a' }}>Neto: </span><b>${parseFloat(comprobante.neto || 0).toFixed(2)}</b></div>
            </div>

            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', border: '1px solid #d0d7de', borderRadius: '6px', overflow: 'hidden' }}>
              <thead>
                <tr style={{ background: '#f6f8fa', textAlign: 'left' }}>
                  <th style={{ padding: '9px 12px' }}>Código</th>
                  <th style={{ padding: '9px 12px' }}>Descripción</th>
                  <th style={{ padding: '9px 12px', textAlign: 'right' }}>Cant.</th>
                  <th style={{ padding: '9px 12px', textAlign: 'right' }}>P. Unit.</th>
                  <th style={{ padding: '9px 12px', textAlign: 'right' }}>Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {comprobante.items.map((item, idx) => (
                  <tr key={idx} style={{ borderTop: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '9px 12px', color: '#0969da', fontWeight: '700' }}>{item.cod_articulo}</td>
                    <td style={{ padding: '9px 12px' }}>{item.nom_articulo}</td>
                    <td style={{ padding: '9px 12px', textAlign: 'right' }}>{parseFloat(item.cantidad).toFixed(2)}</td>
                    <td style={{ padding: '9px 12px', textAlign: 'right' }}>${parseFloat(item.precio_unit || 0).toFixed(2)}</td>
                    <td style={{ padding: '9px 12px', textAlign: 'right', fontWeight: '700' }}>${parseFloat(item.total).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {!yaAnulado && (
              <div style={{ marginTop: '20px', textAlign: 'right' }}>
                <button onClick={anular} disabled={cargando} style={{
                  padding: '12px 28px', background: '#cf222e', color: '#fff', border: 'none',
                  borderRadius: '6px', fontSize: '15px', fontWeight: '700', cursor: 'pointer',
                }}>
                  {cargando ? 'Procesando...' : '⚠️ ANULAR COMPROBANTE Y REVERTIR STOCK'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}