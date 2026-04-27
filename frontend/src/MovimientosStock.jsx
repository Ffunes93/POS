import { useState, useEffect, useRef } from 'react';

const API = 'http://localhost:8001/api';
const s = {
  card:  { background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', padding: '18px', marginBottom: '14px' },
  label: { display: 'block', fontSize: '11px', fontWeight: '700', color: '#57606a', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '.4px' },
  input: { width: '100%', padding: '9px 10px', border: '1px solid #d0d7de', borderRadius: '5px', fontSize: '14px', boxSizing: 'border-box' },
};

function ArticuloAutoComplete({ onSelect }) {
  const [text, setText]   = useState('');
  const [sugg, setSugg]   = useState([]);
  const ref = useRef(null);

  useEffect(() => {
    if (text.length < 2) { setSugg([]); return; }
    const t = setTimeout(async () => {
      const r = await fetch(`${API}/ListarArticulosABM/?buscar=${encodeURIComponent(text)}`);
      const d = await r.json();
      if (d.status === 'success') setSugg(d.data.slice(0, 8));
    }, 250);
    return () => clearTimeout(t);
  }, [text]);

  useEffect(() => {
    const fn = e => { if (ref.current && !ref.current.contains(e.target)) setSugg([]); };
    document.addEventListener('mousedown', fn);
    return () => document.removeEventListener('mousedown', fn);
  }, []);

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <input style={s.input} value={text} onChange={e => setText(e.target.value)}
        placeholder="Código, nombre o barra..." />
      {sugg.length > 0 && (
        <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100,
          background: '#fff', border: '1px solid #d0d7de', borderRadius: '5px',
          boxShadow: '0 8px 24px rgba(0,0,0,.1)', maxHeight: '200px', overflowY: 'auto' }}>
          {sugg.map((a, i) => (
            <div key={i} onClick={() => { onSelect(a); setText(''); setSugg([]); }}
              style={{ padding: '10px 14px', cursor: 'pointer', fontSize: '13px', borderBottom: '1px solid #f0f0f0' }}
              onMouseOver={e => e.currentTarget.style.background = '#f6f8fa'}
              onMouseOut={e  => e.currentTarget.style.background = ''}>
              <b>{a.cod_art}</b> — {a.nombre}
              <span style={{ float: 'right', color: a.stock > 0 ? '#1a7f37' : '#cf222e', fontWeight: '700' }}>
                Stock: {a.stock}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function FormMovimiento({ tipo }) {
  // tipo = 'IS' (entrada) | 'SS' (salida)
  const esEntrada = tipo === 'IS';
  const [items,    setItems]   = useState([]);
  const [cant,     setCant]    = useState('1');
  const [costo,    setCosto]   = useState('');
  const [artSel,   setArtSel]  = useState(null);
  const [observac, setObservac]= useState('');
  const [causas,   setCausas]  = useState([]);
  const [causa,    setCausa]   = useState('');
  const [cargando, setCargando]= useState(false);
  const [msg,      setMsg]     = useState(null);

  useEffect(() => {
    if (!esEntrada) {
      fetch(`${API}/ListarCausasEmision/`)
        .then(r => r.json())
        .then(d => { if (d.status === 'success') setCausas(d.data); });
    }
  }, [esEntrada]);

  const agregarItem = () => {
    if (!artSel) return setMsg({ tipo: 'error', texto: 'Seleccione un artículo.' });
    const cantidad = parseFloat(cant);
    if (!cantidad || cantidad <= 0) return setMsg({ tipo: 'error', texto: 'Cantidad inválida.' });
    setItems(prev => [...prev, {
      id:          Date.now(),
      cod_art:     artSel.cod_art,
      descripcion: artSel.nombre,
      stock_actual: parseFloat(artSel.stock || 0),
      cantidad,
      costo:       parseFloat(costo) || 0,
    }]);
    setArtSel(null); setCant('1'); setCosto(''); setMsg(null);
  };

  const limpiar = () => { setItems([]); setObservac(''); setCausa(''); setMsg(null); };

  const guardar = async () => {
    if (!observac || observac.length < 2) return setMsg({ tipo: 'error', texto: 'Ingrese un motivo (mín. 2 caracteres).' });
    if (items.length === 0) return setMsg({ tipo: 'error', texto: 'Agregue al menos un artículo.' });

    setCargando(true); setMsg(null);
    const endpoint = esEntrada ? 'RegistrarEntradaStock' : 'RegistrarSalidaStock';
    const payload  = {
      observac,
      cajero:  1,
      usuario: 'admin',
      items:   items.map(i => ({ cod_art: i.cod_art, descripcion: i.descripcion, cantidad: i.cantidad, costo: i.costo })),
      ...(esEntrada ? { cod_prov: 0 } : { causa_emision: causa }),
    };

    const r = await fetch(`${API}/${endpoint}/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const d = await r.json();
    if (r.ok && d.status === 'success') {
      setMsg({ tipo: 'ok', texto: `✅ ${d.mensaje}` });
      limpiar();
    } else {
      setMsg({ tipo: 'error', texto: d.mensaje || 'Error.' });
    }
    setCargando(false);
  };

  const colorAccent = esEntrada ? '#2da44e' : '#cf222e';

  return (
    <div>
      {msg && (
        <div style={{ padding: '10px 16px', borderRadius: '6px', marginBottom: '14px', fontSize: '13px', fontWeight: '600',
          background: msg.tipo === 'ok' ? '#dafbe1' : '#ffebe9',
          color:      msg.tipo === 'ok' ? '#116329' : '#a40e26',
          border:     `1px solid ${msg.tipo === 'ok' ? '#56d364' : '#ff818266'}` }}>{msg.texto}</div>
      )}

      {/* Observación + causa */}
      <div style={s.card}>
        <div style={{ display: 'grid', gridTemplateColumns: !esEntrada && causas.length ? '1fr 1fr' : '1fr', gap: '14px' }}>
          <div>
            <label style={s.label}>Motivo / Observación *</label>
            <input style={s.input} value={observac} onChange={e => setObservac(e.target.value)}
              placeholder="Descripción del movimiento (obligatorio)..." />
          </div>
          {!esEntrada && causas.length > 0 && (
            <div>
              <label style={s.label}>Causa de Emisión</label>
              <select style={s.input} value={causa} onChange={e => setCausa(e.target.value)}>
                <option value="">— Seleccionar —</option>
                {causas.map(c => <option key={c.codigo} value={c.codigo}>{c.codigo} — {c.detalle}</option>)}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Agregar artículo */}
      <div style={s.card}>
        <div style={{ fontSize: '12px', fontWeight: '700', color: '#57606a', textTransform: 'uppercase', marginBottom: '12px' }}>
          Artículo a {esEntrada ? 'ingresar' : 'egresar'}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: esEntrada ? '1fr 100px 130px auto' : '1fr 100px auto', gap: '10px', alignItems: 'flex-end' }}>
          <div>
            <label style={s.label}>Artículo</label>
            <ArticuloAutoComplete onSelect={(a) => { setArtSel(a); if (esEntrada && a.costo_ult) setCosto(parseFloat(a.costo_ult).toFixed(2)); }} />
            {artSel && <span style={{ fontSize: '12px', color: '#57606a' }}>Seleccionado: <b>{artSel.nombre}</b> | Stock actual: {artSel.stock}</span>}
          </div>
          <div>
            <label style={s.label}>Cantidad</label>
            <input type="number" step="0.001" value={cant} onChange={e => setCant(e.target.value)} style={s.input} />
          </div>
          {esEntrada && (
            <div>
              <label style={s.label}>Costo Unit. ($)</label>
              <input type="number" step="0.01" value={costo} onChange={e => setCosto(e.target.value)} placeholder="0.00" style={s.input} />
            </div>
          )}
          <button onClick={agregarItem} style={{ padding: '9px 16px', background: colorAccent, color: '#fff', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: '700' }}>
            + Agregar
          </button>
        </div>
      </div>

      {/* Grilla */}
      {items.length > 0 && (
        <div style={{ ...s.card, padding: 0, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ background: '#f6f8fa', textAlign: 'left', borderBottom: '1px solid #d0d7de' }}>
                <th style={{ padding: '9px 12px' }}>Código</th>
                <th style={{ padding: '9px 12px' }}>Descripción</th>
                <th style={{ padding: '9px 12px', textAlign: 'right' }}>Stock actual</th>
                <th style={{ padding: '9px 12px', textAlign: 'right' }}>Cantidad</th>
                {esEntrada && <th style={{ padding: '9px 12px', textAlign: 'right' }}>Costo</th>}
                <th style={{ padding: '9px 12px', width: '40px' }}></th>
              </tr>
            </thead>
            <tbody>
              {items.map(item => (
                <tr key={item.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '9px 12px', fontWeight: '700', color: '#0969da' }}>{item.cod_art}</td>
                  <td style={{ padding: '9px 12px' }}>{item.descripcion}</td>
                  <td style={{ padding: '9px 12px', textAlign: 'right', color: item.stock_actual <= 0 ? '#cf222e' : '#57606a' }}>{item.stock_actual}</td>
                  <td style={{ padding: '9px 12px', textAlign: 'right', fontWeight: '700', color: colorAccent }}>
                    {esEntrada ? '+' : '-'}{item.cantidad}
                  </td>
                  {esEntrada && <td style={{ padding: '9px 12px', textAlign: 'right' }}>${item.costo.toFixed(2)}</td>}
                  <td style={{ padding: '9px 12px', textAlign: 'center' }}>
                    <button onClick={() => setItems(prev => prev.filter(i => i.id !== item.id))}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#cf222e', fontSize: '16px' }}>✕</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {items.length > 0 && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button onClick={limpiar} style={{ padding: '9px 18px', background: '#f3f4f6', border: '1px solid #d0d7de', borderRadius: '5px', cursor: 'pointer', fontSize: '13px', color: '#57606a' }}>Limpiar</button>
          <button onClick={guardar} disabled={cargando} style={{ padding: '9px 24px', background: colorAccent, color: '#fff', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: '700', fontSize: '14px' }}>
            {cargando ? 'Guardando...' : `💾 Registrar ${esEntrada ? 'Entrada' : 'Salida'} (${items.length} art.)`}
          </button>
        </div>
      )}
    </div>
  );
}

export default function MovimientosStock() {
  const [sub, setSub] = useState('IS');

  return (
    <div style={{ background: '#f6f8fa', padding: '4px', minHeight: '100%' }}>
      <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#24292f', fontWeight: '700' }}>
        🔄 Movimientos Manuales de Stock
      </h2>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        {[['IS', '📥 Entrada de Stock'], ['SS', '📤 Salida de Stock']].map(([id, label]) => (
          <button key={id} onClick={() => setSub(id)} style={{
            padding: '8px 16px', borderRadius: '5px', cursor: 'pointer', fontWeight: '700', fontSize: '13px',
            background: sub === id ? (id === 'IS' ? '#2da44e' : '#cf222e') : '#fff',
            color:      sub === id ? '#fff' : '#57606a',
            border:     `1px solid ${sub === id ? (id === 'IS' ? '#2da44e' : '#cf222e') : '#d0d7de'}`,
          }}>{label}</button>
        ))}
      </div>
      <FormMovimiento tipo={sub} key={sub} />
    </div>
  );
}