import { useState, useRef } from 'react';

const API = 'http://localhost:8001/api';
const s = { // inline styles helpers
  card:  { background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', padding: '18px', marginBottom: '14px' },
  label: { display: 'block', fontSize: '11px', fontWeight: '700', color: '#57606a', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '.4px' },
  input: { width: '100%', padding: '9px 10px', border: '1px solid #d0d7de', borderRadius: '5px', fontSize: '14px', boxSizing: 'border-box' },
  btn:   (col) => ({ padding: '9px 18px', background: col, color: '#fff', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: '700', fontSize: '13px' }),
};

function Msg({ msg }) {
  if (!msg) return null;
  return (
    <div style={{ padding: '10px 16px', borderRadius: '6px', marginBottom: '14px', fontSize: '13px', fontWeight: '600',
      background: msg.tipo === 'ok' ? '#dafbe1' : '#ffebe9',
      color:      msg.tipo === 'ok' ? '#116329' : '#a40e26',
      border:     `1px solid ${msg.tipo === 'ok' ? '#56d364' : '#ff818266'}`,
    }}>{msg.texto}</div>
  );
}

// ── Emisión de recibo ─────────────────────────────────────────────────────────
function EmisionRecibo() {
  const [clienteText, setClienteText]       = useState('');
  const [clienteSel,  setClienteSel]        = useState(null);
  const [suggestions, setSuggestions]       = useState([]);
  const [deudas,       setDeudas]           = useState([]);
  const [pagosGrid,    setPagosGrid]        = useState([]); // montos que se van a cobrar por factura
  const [medioPago,    setMedioPago]        = useState('EFE');
  const [nroCupon,     setNroCupon]         = useState('');
  const [cargando,     setCargando]         = useState(false);
  const [msg,          setMsg]              = useState(null);
  const [nombreCliente, setNombreCliente]   = useState('');
  const ref = useRef(null);

  // Autocomplete clientes
  const buscarClientes = async (v) => {
    setClienteText(v);
    if (v.length < 2) { setSuggestions([]); return; }
    const r = await fetch(`${API}/ListarClientes/?buscar=${encodeURIComponent(v)}`);
    const d = await r.json();
    if (d.status === 'success') setSuggestions(d.data.slice(0, 8));
  };

  const seleccionarCliente = (c) => {
    setClienteSel(c);
    setClienteText(c.denominacion);
    setSuggestions([]);
    setNombreCliente(c.denominacion);
    cargarDeuda(c.cod_cli);
  };

  const cargarDeuda = async (codCli) => {
    setCargando(true); setDeudas([]); setPagosGrid([]); setMsg(null);
    const r = await fetch(`${API}/ObtenerDeudaCliente/?cod_cli=${codCli}`);
    const d = await r.json();
    if (d.status === 'success') {
      setDeudas(d.deudas);
      // Inicializa el monto a pagar con el saldo total de cada factura
      setPagosGrid(d.deudas.map(f => ({ id: f.id, checked: false, pago: parseFloat(f.saldo || 0) })));
      setNombreCliente(d.nom_cliente);
    }
    setCargando(false);
  };

  const toggleDeuda = (id) => {
    setPagosGrid(prev => prev.map(p => p.id === id ? { ...p, checked: !p.checked } : p));
  };

  const cambiarPago = (id, val) => {
    setPagosGrid(prev => prev.map(p => p.id === id ? { ...p, pago: parseFloat(val) || 0 } : p));
  };

  const totalSeleccionado = pagosGrid.filter(p => p.checked).reduce((s, p) => s + p.pago, 0);

  const emitir = async () => {
    if (!clienteSel) return setMsg({ tipo: 'error', texto: 'Seleccione un cliente.' });
    const sel = pagosGrid.filter(p => p.checked);
    if (sel.length === 0) return setMsg({ tipo: 'error', texto: 'Seleccione al menos una factura a cobrar.' });
    if (totalSeleccionado <= 0) return setMsg({ tipo: 'error', texto: 'El importe total debe ser mayor a 0.' });

    setCargando(true); setMsg(null);
    const payload = {
      cod_cli:       clienteSel.cod_cli,
      cajero:        1,
      usuario:       'admin',
      punto_venta:   '0001',
      importe_total: parseFloat(totalSeleccionado.toFixed(2)),
      deudas_seleccionadas: sel.map(p => {
        const deuda = deudas.find(d => d.id === p.id);
        return { id: p.id, cod_comprob: deuda?.cod_comprob, nro_comprob: deuda?.nro_comprob, pago: p.pago };
      }),
      medios_pago: [{
        cod_pago: medioPago,
        importe:  parseFloat(totalSeleccionado.toFixed(2)),
        referencia: nroCupon,
        numero:   nroCupon ? parseInt(nroCupon) : 0,
      }],
    };

    const r  = await fetch(`${API}/EmitirRecibo/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const d  = await r.json();
    if (r.ok && d.status === 'success') {
      setMsg({ tipo: 'ok', texto: `✅ Recibo N° ${d.nro_recibo} emitido por $${totalSeleccionado.toFixed(2)}` });
      setClienteSel(null); setClienteText(''); setDeudas([]); setPagosGrid([]); setNroCupon('');
    } else {
      setMsg({ tipo: 'error', texto: d.mensaje || 'Error al emitir.' });
    }
    setCargando(false);
  };

  return (
    <div>
      <h3 style={{ marginTop: 0, color: '#24292f' }}>📄 Emisión de Recibo</h3>
      <Msg msg={msg} />

      {/* Buscador cliente */}
      <div style={s.card}>
        <label style={s.label}>Cliente</label>
        <div ref={ref} style={{ position: 'relative' }}>
          <input style={s.input} value={clienteText} onChange={e => buscarClientes(e.target.value)}
            placeholder="Buscar por nombre o CUIT..." />
          {suggestions.length > 0 && (
            <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100,
              background: '#fff', border: '1px solid #d0d7de', borderRadius: '5px',
              boxShadow: '0 8px 24px rgba(0,0,0,.1)', maxHeight: '200px', overflowY: 'auto' }}>
              {suggestions.map((c, i) => (
                <div key={i} onClick={() => seleccionarCliente(c)}
                  style={{ padding: '10px 14px', cursor: 'pointer', fontSize: '13px', borderBottom: '1px solid #f0f0f0' }}
                  onMouseOver={e => e.currentTarget.style.background = '#f6f8fa'}
                  onMouseOut={e  => e.currentTarget.style.background = ''}>
                  <b>{c.denominacion}</b> — {c.nro_cuit}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Deuda */}
      {deudas.length > 0 && (
        <div style={s.card}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#57606a', textTransform: 'uppercase', marginBottom: '12px' }}>
            Facturas pendientes de {nombreCliente}
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ background: '#f6f8fa', borderBottom: '1px solid #d0d7de', textAlign: 'left' }}>
                <th style={{ padding: '8px 10px', width: '40px' }}>Paga</th>
                <th style={{ padding: '8px 10px' }}>Fecha</th>
                <th style={{ padding: '8px 10px' }}>Comprobante</th>
                <th style={{ padding: '8px 10px', textAlign: 'right' }}>Saldo</th>
                <th style={{ padding: '8px 10px', textAlign: 'right' }}>Paga ahora</th>
              </tr>
            </thead>
            <tbody>
              {deudas.map((d, i) => {
                const pg = pagosGrid.find(p => p.id === d.id);
                return (
                  <tr key={d.id} style={{ borderBottom: '1px solid #f0f0f0', background: pg?.checked ? '#f0fff4' : '#fff' }}>
                    <td style={{ padding: '8px 10px', textAlign: 'center' }}>
                      <input type="checkbox" checked={pg?.checked || false} onChange={() => toggleDeuda(d.id)} />
                    </td>
                    <td style={{ padding: '8px 10px' }}>{new Date(d.fecha).toLocaleDateString()}</td>
                    <td style={{ padding: '8px 10px', fontWeight: '700', color: '#0969da' }}>
                      {d.cod_comprob} N° {d.nro_comprob}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'right' }}>${parseFloat(d.saldo).toFixed(2)}</td>
                    <td style={{ padding: '8px 10px', textAlign: 'right' }}>
                      <input type="number" step="0.01" value={pg?.pago || 0}
                        onChange={e => cambiarPago(d.id, e.target.value)}
                        disabled={!pg?.checked}
                        style={{ width: '90px', padding: '4px 8px', border: '1px solid #d0d7de', borderRadius: '4px', textAlign: 'right' }} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Medio de pago + botón */}
      {deudas.length > 0 && (
        <div style={{ ...s.card, display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ flex: 1 }}>
            <label style={s.label}>Medio de Pago</label>
            <select value={medioPago} onChange={e => setMedioPago(e.target.value)} style={s.input}>
              <option value="EFE">💵 Efectivo</option>
              <option value="TAR">💳 Tarjeta</option>
              <option value="CHE">🏦 Cheque</option>
              <option value="TRF">🔁 Transferencia</option>
            </select>
          </div>
          {medioPago !== 'EFE' && (
            <div style={{ flex: 1 }}>
              <label style={s.label}>N° Cupón / Referencia</label>
              <input type="text" value={nroCupon} onChange={e => setNroCupon(e.target.value)} style={s.input} />
            </div>
          )}
          <div style={{ textAlign: 'right', minWidth: '200px' }}>
            <div style={{ fontSize: '20px', fontWeight: '800', color: '#1a7f37', marginBottom: '8px' }}>
              Total: ${totalSeleccionado.toFixed(2)}
            </div>
            <button onClick={emitir} disabled={cargando || totalSeleccionado <= 0} style={s.btn('#2da44e')}>
              {cargando ? 'Emitiendo...' : '✅ Emitir Recibo'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Anulación de recibo ───────────────────────────────────────────────────────
function AnulacionRecibo() {
  const [nroRecibo, setNroRecibo] = useState('');
  const [cargando,  setCargando]  = useState(false);
  const [msg,       setMsg]       = useState(null);

  const anular = async () => {
    if (!nroRecibo) return setMsg({ tipo: 'error', texto: 'Ingrese el número de recibo.' });
    if (!window.confirm(`¿Confirma la anulación del Recibo N° ${nroRecibo}?\nEsta acción restaurará el saldo en las facturas originales.`)) return;
    setCargando(true); setMsg(null);
    const r = await fetch(`${API}/AnularRecibo/`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nro_recibo: parseInt(nroRecibo) }),
    });
    const d = await r.json();
    setMsg({ tipo: r.ok && d.status === 'success' ? 'ok' : 'error', texto: d.mensaje });
    if (r.ok && d.status === 'success') setNroRecibo('');
    setCargando(false);
  };

  return (
    <div>
      <h3 style={{ marginTop: 0, color: '#24292f' }}>🚫 Anulación de Recibo</h3>
      <Msg msg={msg} />
      <div style={{ ...s.card, display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
        <div style={{ flex: 1 }}>
          <label style={s.label}>Número de Recibo</label>
          <input autoFocus type="number" value={nroRecibo} onChange={e => setNroRecibo(e.target.value)}
            placeholder="ej: 15" style={s.input} />
        </div>
        <button onClick={anular} disabled={cargando} style={s.btn('#cf222e')}>
          {cargando ? 'Procesando...' : '⚠️ Anular Recibo'}
        </button>
      </div>
      <div style={{ background: '#fff8c5', border: '1px solid #f0c000', borderRadius: '6px', padding: '12px 16px', fontSize: '13px', color: '#735c0f' }}>
        ⚠️ Al anular un recibo se restaura el saldo pendiente en todas las facturas que se habían cobrado con ese recibo.
      </div>
    </div>
  );
}

// ── Módulo principal ──────────────────────────────────────────────────────────
export default function GestionRecibos() {
  const [sub, setSub] = useState('EMISION');

  return (
    <div style={{ background: '#f6f8fa', minHeight: '100%', padding: '4px' }}>
      <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#24292f', fontWeight: '700' }}>
        🧾 Recibos de Cobro
      </h2>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        {[['EMISION', '📄 Emitir Recibo'], ['ANULACION', '🚫 Anular Recibo']].map(([id, label]) => (
          <button key={id} onClick={() => setSub(id)} style={{
            padding: '8px 16px', borderRadius: '5px', cursor: 'pointer', fontWeight: '700', fontSize: '13px',
            background: sub === id ? '#0969da' : '#fff',
            color:      sub === id ? '#fff' : '#57606a',
            border:     `1px solid ${sub === id ? '#0969da' : '#d0d7de'}`,
          }}>{label}</button>
        ))}
      </div>
      {sub === 'EMISION'   && <EmisionRecibo />}
      {sub === 'ANULACION' && <AnulacionRecibo />}
    </div>
  );
}