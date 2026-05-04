import { useState, useEffect } from 'react';

const API = `${import.meta.env.VITE_API_URL}/api`;
const fmt = n => parseFloat(n || 0).toFixed(2);
const s = {
  input: { width: '100%', padding: '9px 10px', border: '1px solid #d0d7de', borderRadius: '5px', fontSize: '14px', boxSizing: 'border-box' },
  label: { display: 'block', fontSize: '11px', fontWeight: '700', color: '#57606a', marginBottom: '4px', textTransform: 'uppercase' },
  btn:   (col, sec) => ({ padding: '9px 18px', background: sec ? '#fff' : col, color: sec ? col : '#fff', border: `1px solid ${col}`, borderRadius: '5px', cursor: 'pointer', fontWeight: '700', fontSize: '13px' }),
};

function Msg({ msg }) {
  if (!msg) return null;
  return (
    <div style={{ padding: '10px 16px', borderRadius: '6px', marginBottom: '14px', fontSize: '13px', fontWeight: '600',
      background: msg.tipo === 'ok' ? '#dafbe1' : '#ffebe9',
      color:      msg.tipo === 'ok' ? '#116329' : '#a40e26',
      border:     `1px solid ${msg.tipo === 'ok' ? '#56d364' : '#ff818266'}` }}>{msg.texto}</div>
  );
}

// ── Panel Resumen ─────────────────────────────────────────────────────────────
function ResumenDeuda({ onSeleccionarProv }) {
  const [proveedores, setProveedores] = useState([]);
  const [totalCartera, setTotal]      = useState(0);
  const [loading,      setLoading]    = useState(true);
  const [buscar,       setBuscar]     = useState('');

  const cargar = async () => {
    setLoading(true);
    const r = await fetch(`${API}/ResumenCtaCteProveedores/`);
    const d = await r.json();
    if (d.status === 'success') {
      setProveedores(d.proveedores);
      setTotal(d.total_cartera);
    }
    setLoading(false);
  };

  useEffect(() => { cargar(); }, []);

  const filtrados = proveedores.filter(p =>
    !buscar || (p.nomfantasia || '').toLowerCase().includes(buscar.toLowerCase())
  );

  return (
    <div>
      <div style={{ display: 'flex', gap: '14px', marginBottom: '14px' }}>
        <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px',
          padding: '14px 20px', flex: 1, borderLeft: '4px solid #cf222e' }}>
          <div style={{ fontSize: '11px', fontWeight: '700', color: '#57606a', textTransform: 'uppercase' }}>Total a pagar</div>
          <div style={{ fontSize: '24px', fontWeight: '800', color: '#cf222e' }}>${parseFloat(totalCartera).toLocaleString('es-AR', { minimumFractionDigits: 2 })}</div>
        </div>
        <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px',
          padding: '14px 20px', flex: 1, borderLeft: '4px solid #e67e22' }}>
          <div style={{ fontSize: '11px', fontWeight: '700', color: '#57606a', textTransform: 'uppercase' }}>Proveedores con deuda</div>
          <div style={{ fontSize: '24px', fontWeight: '800', color: '#e67e22' }}>{proveedores.length}</div>
        </div>
      </div>

      <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', overflow: 'hidden' }}>
        <div style={{ padding: '12px 16px', borderBottom: '1px solid #d0d7de', display: 'flex', gap: '10px' }}>
          <input style={{ ...s.input, flex: 1 }} value={buscar} onChange={e => setBuscar(e.target.value)}
            placeholder="Filtrar por proveedor..." />
          <button onClick={cargar} style={s.btn('#0969da')}>🔄</button>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: '#f6f8fa', textAlign: 'left', borderBottom: '1px solid #d0d7de' }}>
              <th style={{ padding: '10px 12px' }}>Proveedor</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>Facturas</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>Total deuda</th>
              <th style={{ padding: '10px 12px', textAlign: 'center' }}>Acción</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={4} style={{ padding: '24px', textAlign: 'center', color: '#57606a' }}>Cargando...</td></tr>
            ) : filtrados.length === 0 ? (
              <tr><td colSpan={4} style={{ padding: '24px', textAlign: 'center', color: '#8c959f' }}>Sin deudas pendientes</td></tr>
            ) : filtrados.map(p => (
              <tr key={p.cod_prov} style={{ borderBottom: '1px solid #f0f0f0' }}>
                <td style={{ padding: '10px 12px', fontWeight: '700' }}>{p.nomfantasia}</td>
                <td style={{ padding: '10px 12px', textAlign: 'right', color: '#57606a' }}>{p.cant_facturas}</td>
                <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: '800', color: '#cf222e' }}>
                  ${parseFloat(p.total_deuda || 0).toLocaleString('es-AR', { minimumFractionDigits: 2 })}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                  <button onClick={() => onSeleccionarProv(p)} style={s.btn('#8250df')}>
                    💸 Pagar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Panel de Pago ─────────────────────────────────────────────────────────────
function PanelPago({ proveedor, onVolver }) {
  const [deudas,   setDeudas]   = useState([]);
  const [pagos,    setPagos]    = useState([]);
  const [medioPago, setMedioPago] = useState('EFE');
  const [referencia, setRef]    = useState('');
  const [cargando, setCargando] = useState(false);
  const [msg,      setMsg]      = useState(null);

  useEffect(() => {
    fetch(`${API}/ObtenerDeudaProveedor/?cod_prov=${proveedor.cod_prov}`)
      .then(r => r.json()).then(d => {
        if (d.status === 'success') {
          setDeudas(d.deudas);
          setPagos(d.deudas.map(f => ({ id: f.id, checked: false, pago: parseFloat(f.saldo || 0) })));
        }
      });
  }, [proveedor.cod_prov]);

  const toggle = id => setPagos(p => p.map(x => x.id === id ? { ...x, checked: !x.checked } : x));
  const cambiarPago = (id, val) => setPagos(p => p.map(x => x.id === id ? { ...x, pago: parseFloat(val) || 0 } : x));

  const totalSel = pagos.filter(p => p.checked).reduce((s, p) => s + p.pago, 0);

  const pagar = async () => {
    const sel = pagos.filter(p => p.checked);
    if (sel.length === 0) return setMsg({ tipo: 'error', texto: 'Seleccione al menos una factura.' });
    if (totalSel <= 0) return setMsg({ tipo: 'error', texto: 'El importe debe ser mayor a 0.' });

    setCargando(true); setMsg(null);
    const payload = {
      cod_prov:      proveedor.cod_prov,
      cajero:        1,
      usuario:       'admin',
      importe_total: parseFloat(totalSel.toFixed(2)),
      deudas_seleccionadas: sel.map(p => {
        const d = deudas.find(x => x.id === p.id);
        return { id: p.id, cod_comprob: d?.cod_comprob, nro_comprob: d?.nro_comprob, pago: p.pago };
      }),
      medios_pago: [{ tipo: medioPago, importe: parseFloat(totalSel.toFixed(2)), referencia }],
    };

    const r = await fetch(`${API}/RegistrarPagoProveedor/`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
    });
    const d = await r.json();
    if (r.ok && d.status === 'success') {
      setMsg({ tipo: 'ok', texto: `✅ ${d.mensaje}` });
      // Recargar deudas
      setTimeout(() => onVolver(), 1500);
    } else {
      setMsg({ tipo: 'error', texto: d.mensaje || 'Error al registrar.' });
    }
    setCargando(false);
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
        <button onClick={onVolver} style={s.btn('#57606a', true)}>← Volver</button>
        <h3 style={{ margin: 0, color: '#24292f' }}>
          💸 Pago a <span style={{ color: '#8250df' }}>{proveedor.nomfantasia}</span>
        </h3>
      </div>

      <Msg msg={msg} />

      {/* Facturas pendientes */}
      <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', overflow: 'hidden', marginBottom: '14px' }}>
        <div style={{ padding: '12px 16px', borderBottom: '1px solid #d0d7de', fontWeight: '700', fontSize: '13px', color: '#57606a' }}>
          Facturas pendientes
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: '#f6f8fa', textAlign: 'left', borderBottom: '1px solid #d0d7de' }}>
              <th style={{ padding: '9px 12px', width: 40 }}>Paga</th>
              <th style={{ padding: '9px 12px' }}>Fecha</th>
              <th style={{ padding: '9px 12px' }}>Comprobante</th>
              <th style={{ padding: '9px 12px', textAlign: 'right' }}>Saldo</th>
              <th style={{ padding: '9px 12px', textAlign: 'right' }}>Paga ahora</th>
            </tr>
          </thead>
          <tbody>
            {deudas.length === 0 ? (
              <tr><td colSpan={5} style={{ padding: '20px', textAlign: 'center', color: '#8c959f' }}>
                Sin facturas pendientes
              </td></tr>
            ) : deudas.map(d => {
              const pg = pagos.find(p => p.id === d.id);
              return (
                <tr key={d.id} style={{ borderBottom: '1px solid #f0f0f0', background: pg?.checked ? '#f0fff4' : '' }}>
                  <td style={{ padding: '9px 12px', textAlign: 'center' }}>
                    <input type="checkbox" checked={pg?.checked || false} onChange={() => toggle(d.id)} />
                  </td>
                  <td style={{ padding: '9px 12px', color: '#57606a' }}>
                    {new Date(d.fecha).toLocaleDateString()}
                  </td>
                  <td style={{ padding: '9px 12px', fontWeight: '700', color: '#8250df' }}>
                    {d.cod_comprob} N° {d.nro_comprob}
                  </td>
                  <td style={{ padding: '9px 12px', textAlign: 'right', fontWeight: '700', color: '#cf222e' }}>
                    ${fmt(d.saldo)}
                  </td>
                  <td style={{ padding: '9px 12px', textAlign: 'right' }}>
                    <input type="number" step="0.01" value={pg?.pago || 0}
                      onChange={e => cambiarPago(d.id, e.target.value)}
                      disabled={!pg?.checked}
                      style={{ width: '100px', padding: '5px 8px', border: '1px solid #d0d7de', borderRadius: '4px', textAlign: 'right' }} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Medio de pago + botón */}
      {deudas.length > 0 && (
        <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', padding: '16px',
          display: 'flex', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '180px' }}>
            <label style={s.label}>Medio de Pago</label>
            <select value={medioPago} onChange={e => setMedioPago(e.target.value)} style={s.input}>
              <option value="EFE">💵 Efectivo</option>
              <option value="CHE">🏦 Cheque</option>
              <option value="TRF">🔁 Transferencia</option>
            </select>
          </div>
          <div style={{ flex: 2, minWidth: '180px' }}>
            <label style={s.label}>Referencia / N° Operación</label>
            <input style={s.input} value={referencia} onChange={e => setRef(e.target.value)} placeholder="Opcional..." />
          </div>
          <div style={{ textAlign: 'right', minWidth: '200px' }}>
            <div style={{ fontSize: '20px', fontWeight: '800', color: '#1a7f37', marginBottom: '8px' }}>
              Total: ${fmt(totalSel)}
            </div>
            <button onClick={pagar} disabled={cargando || totalSel <= 0} style={s.btn('#8250df')}>
              {cargando ? 'Registrando...' : '💸 Registrar Pago'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Módulo principal ──────────────────────────────────────────────────────────
export default function CtaCteProveedores() {
  const [provSel, setProvSel] = useState(null);

  return (
    <div style={{ background: '#f6f8fa', minHeight: '100%', padding: '4px' }}>
      <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#24292f', fontWeight: '700' }}>
        🏢 Cuenta Corriente Proveedores
      </h2>
      {!provSel
        ? <ResumenDeuda onSeleccionarProv={setProvSel} />
        : <PanelPago proveedor={provSel} onVolver={() => setProvSel(null)} />
      }
    </div>
  );
}