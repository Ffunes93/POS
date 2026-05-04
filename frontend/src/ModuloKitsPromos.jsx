import { useState, useEffect, useRef } from 'react';

const API = `${import.meta.env.VITE_API_URL}/api`;
const fmt = n => parseFloat(n || 0).toFixed(2);

const s = {
  card:  { background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', padding: '18px', marginBottom: '14px' },
  label: { display: 'block', fontSize: '11px', fontWeight: '700', color: '#57606a', marginBottom: '4px', textTransform: 'uppercase' },
  input: { width: '100%', padding: '9px 10px', border: '1px solid #d0d7de', borderRadius: '5px', fontSize: '14px', boxSizing: 'border-box' },
  btn:   (col, sec) => ({ padding: '8px 16px', background: sec ? '#fff' : col, color: sec ? col : '#fff', border: `1px solid ${col}`, borderRadius: '5px', cursor: 'pointer', fontWeight: '700', fontSize: '13px' }),
};

// ── AutoComplete artículo ─────────────────────────────────────────────────────
function ArtAutoComplete({ onSelect, placeholder }) {
  const [text, setText] = useState('');
  const [sugg, setSugg] = useState([]);
  const ref = useRef(null);

  useEffect(() => {
    if (text.length < 2) { setSugg([]); return; }
    const t = setTimeout(async () => {
      const r = await fetch(`${API}/ListarArticulosABM/?buscar=${encodeURIComponent(text)}`);
      const d = await r.json();
      if (d.status === 'success') setSugg(d.data.slice(0, 8));
    }, 260);
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
        placeholder={placeholder || 'Código, nombre o barra...'} />
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
              <span style={{ float: 'right', color: '#57606a', fontSize: '12px' }}>${fmt(a.precio_1)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Msg({ msg }) {
  if (!msg) return null;
  return (
    <div style={{ padding: '10px 16px', borderRadius: '6px', marginBottom: '12px', fontSize: '13px', fontWeight: '600',
      background: msg.tipo === 'ok' ? '#dafbe1' : '#ffebe9',
      color:      msg.tipo === 'ok' ? '#116329' : '#a40e26',
      border:     `1px solid ${msg.tipo === 'ok' ? '#56d364' : '#ff818266'}` }}>{msg.texto}</div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// PANEL KITS
// ══════════════════════════════════════════════════════════════════════════════
function PanelKits() {
  const [kits,     setKits]     = useState([]);
  const [loading,  setLoading]  = useState(false);
  const [buscar,   setBuscar]   = useState('');
  const [editKit,  setEditKit]  = useState(null); // null=cerrado, {}=nuevo, {cod_art,...}=editar
  const [hijos,    setHijos]    = useState([]);   // ítems del formulario activo
  const [cant,     setCant]     = useState('1');
  const [artPadreText, setArtPadreText] = useState('');
  const [artPadreSel,  setArtPadreSel]  = useState(null);
  const [msg,      setMsg]      = useState(null);
  const [cargando, setCargando] = useState(false);

  const cargar = async () => {
    setLoading(true);
    const r = await fetch(`${API}/ListarKits/?buscar=${encodeURIComponent(buscar)}`);
    const d = await r.json();
    if (d.status === 'success') setKits(d.data);
    setLoading(false);
  };

  useEffect(() => { cargar(); }, []);

  const abrirNuevo = () => {
    setEditKit({});
    setHijos([]);
    setArtPadreText(''); setArtPadreSel(null);
    setMsg(null);
  };

  const abrirEditar = (kit) => {
    setEditKit(kit);
    setHijos(kit.hijos.map(h => ({ ...h, _key: Date.now() + Math.random() })));
    setArtPadreText(kit.nombre);
    setArtPadreSel({ cod_art: kit.cod_art, nombre: kit.nombre });
    setMsg(null);
  };

  const agregarHijo = (art) => {
    if (hijos.find(h => h.cod_hijo === art.cod_art)) {
      setMsg({ tipo: 'error', texto: 'El artículo ya está en el kit.' });
      return;
    }
    setHijos(prev => [...prev, {
      _key: Date.now(), cod_hijo: art.cod_art, nombre_hijo: art.nombre,
      precio_hijo: parseFloat(art.precio_1 || 0), stock_hijo: parseFloat(art.stock || 0),
      cant_hijo: parseFloat(cant) || 1,
    }]);
    setCant('1'); setMsg(null);
  };

  const cambiarCant = (key, val) => {
    setHijos(prev => prev.map(h => h._key === key ? { ...h, cant_hijo: parseFloat(val) || 0 } : h));
  };

  const quitarHijo = (key) => setHijos(prev => prev.filter(h => h._key !== key));

  const guardar = async () => {
    if (!artPadreSel) return setMsg({ tipo: 'error', texto: 'Seleccione el artículo padre.' });
    if (hijos.length === 0) return setMsg({ tipo: 'error', texto: 'Agregue al menos un componente.' });
    setCargando(true); setMsg(null);
    const r = await fetch(`${API}/GuardarKit/`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cod_padre: artPadreSel.cod_art,
        hijos: hijos.map(h => ({ cod_hijo: h.cod_hijo, cant_hijo: h.cant_hijo })),
      }),
    });
    const d = await r.json();
    if (r.ok && d.status === 'success') {
      setMsg({ tipo: 'ok', texto: d.mensaje });
      setEditKit(null);
      cargar();
    } else {
      setMsg({ tipo: 'error', texto: d.mensaje });
    }
    setCargando(false);
  };

  const eliminar = async (cod_art) => {
    if (!window.confirm(`¿Eliminar el kit de ${cod_art}?`)) return;
    await fetch(`${API}/EliminarKit/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ cod_padre: cod_art }) });
    cargar();
  };

  if (editKit !== null) {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <button onClick={() => setEditKit(null)} style={s.btn('#57606a', true)}>← Volver</button>
          <h3 style={{ margin: 0, color: '#24292f' }}>
            {editKit.cod_art ? `✏️ Editar Kit: ${editKit.cod_art}` : '🆕 Nuevo Kit / Combo'}
          </h3>
        </div>
        <Msg msg={msg} />

        {/* Artículo padre */}
        <div style={s.card}>
          <label style={s.label}>Artículo Padre (el combo)</label>
          {editKit.cod_art ? (
            <div style={{ padding: '10px', background: '#f6f8fa', borderRadius: '5px', fontWeight: '700', color: '#0969da' }}>
              {editKit.cod_art} — {editKit.nombre}
            </div>
          ) : (
            <ArtAutoComplete placeholder="Buscar artículo que será el combo..." onSelect={(a) => { setArtPadreSel(a); setArtPadreText(a.nombre); }} />
          )}
          {artPadreSel && !editKit.cod_art && (
            <div style={{ marginTop: '6px', fontSize: '12px', color: '#57606a' }}>
              ✓ Seleccionado: <b>{artPadreSel.cod_art}</b> — {artPadreSel.nombre}
            </div>
          )}
        </div>

        {/* Agregar componente */}
        <div style={s.card}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#57606a', textTransform: 'uppercase', marginBottom: '12px' }}>
            Agregar componente
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 100px auto', gap: '10px', alignItems: 'flex-end' }}>
            <ArtAutoComplete placeholder="Artículo hijo..." onSelect={agregarHijo} />
            <div>
              <label style={s.label}>Cantidad</label>
              <input type="number" step="0.001" value={cant} onChange={e => setCant(e.target.value)} style={s.input} />
            </div>
            <div style={{ paddingTop: '20px' }}>
              <span style={{ fontSize: '12px', color: '#57606a' }}>↑ seleccionar agrega</span>
            </div>
          </div>
        </div>

        {/* Tabla de hijos */}
        {hijos.length > 0 && (
          <div style={{ ...s.card, padding: 0, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: '#f6f8fa', textAlign: 'left', borderBottom: '1px solid #d0d7de' }}>
                  <th style={{ padding: '9px 12px' }}>Código</th>
                  <th style={{ padding: '9px 12px' }}>Descripción</th>
                  <th style={{ padding: '9px 12px', textAlign: 'right' }}>Stock</th>
                  <th style={{ padding: '9px 12px', textAlign: 'right' }}>Cantidad en combo</th>
                  <th style={{ padding: '9px 12px', width: 40 }}></th>
                </tr>
              </thead>
              <tbody>
                {hijos.map(h => (
                  <tr key={h._key} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '9px 12px', fontWeight: '700', color: '#0969da' }}>{h.cod_hijo}</td>
                    <td style={{ padding: '9px 12px' }}>{h.nombre_hijo}</td>
                    <td style={{ padding: '9px 12px', textAlign: 'right', color: h.stock_hijo <= 0 ? '#cf222e' : '#57606a' }}>{h.stock_hijo}</td>
                    <td style={{ padding: '9px 12px', textAlign: 'right' }}>
                      <input type="number" step="0.001" value={h.cant_hijo}
                        onChange={e => cambiarCant(h._key, e.target.value)}
                        style={{ width: '90px', padding: '5px 8px', border: '1px solid #d0d7de', borderRadius: '4px', textAlign: 'right' }} />
                    </td>
                    <td style={{ padding: '9px 12px', textAlign: 'center' }}>
                      <button onClick={() => quitarHijo(h._key)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#cf222e', fontSize: '16px' }}>✕</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '4px' }}>
          <button onClick={() => setEditKit(null)} style={s.btn('#57606a', true)}>Cancelar</button>
          <button onClick={guardar} disabled={cargando} style={s.btn('#2da44e')}>
            {cargando ? 'Guardando...' : '💾 Guardar Kit'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', gap: '10px', marginBottom: '14px', alignItems: 'center' }}>
        <input style={{ ...s.input, flex: 1, maxWidth: '300px' }} value={buscar}
          onChange={e => setBuscar(e.target.value)} onKeyDown={e => e.key === 'Enter' && cargar()}
          placeholder="Buscar kits..." />
        <button onClick={cargar} style={s.btn('#0969da')}>🔍</button>
        <button onClick={abrirNuevo} style={{ ...s.btn('#2da44e'), marginLeft: 'auto' }}>
          + Nuevo Kit / Combo
        </button>
      </div>

      <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: '#f6f8fa', borderBottom: '2px solid #d0d7de', textAlign: 'left' }}>
              <th style={{ padding: '10px 12px' }}>Código</th>
              <th style={{ padding: '10px 12px' }}>Nombre</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>Precio</th>
              <th style={{ padding: '10px 12px', textAlign: 'center' }}>Componentes</th>
              <th style={{ padding: '10px 12px', textAlign: 'center' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={5} style={{ padding: '24px', textAlign: 'center', color: '#57606a' }}>Cargando...</td></tr>}
            {!loading && kits.length === 0 && (
              <tr><td colSpan={5} style={{ padding: '24px', textAlign: 'center', color: '#8c959f' }}>
                No hay kits. Cree el primero marcando un artículo como combo.
              </td></tr>
            )}
            {kits.map(kit => (
              <tr key={kit.cod_art} style={{ borderBottom: '1px solid #f0f0f0' }}>
                <td style={{ padding: '10px 12px', fontWeight: '700', color: '#0969da' }}>{kit.cod_art}</td>
                <td style={{ padding: '10px 12px' }}>
                  {kit.nombre}
                  {kit.hijos.length > 0 && (
                    <div style={{ fontSize: '11px', color: '#57606a', marginTop: '2px' }}>
                      {kit.hijos.map(h => `${h.cod_hijo}×${h.cant_hijo}`).join(' + ')}
                    </div>
                  )}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'right' }}>${fmt(kit.precio_1)}</td>
                <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                  <span style={{ background: '#dafbe1', color: '#116329', padding: '2px 10px', borderRadius: '10px', fontSize: '12px', fontWeight: '700' }}>
                    {kit.hijos.length} ítems
                  </span>
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                  <button onClick={() => abrirEditar(kit)} style={{ ...s.btn('#f39c12'), marginRight: '6px' }}>✏️</button>
                  <button onClick={() => eliminar(kit.cod_art)} style={s.btn('#cf222e')}>🗑️</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// PANEL PROMOCIONES
// ══════════════════════════════════════════════════════════════════════════════
function PanelPromociones() {
  const [promos,   setPromos]   = useState([]);
  const [loading,  setLoading]  = useState(false);
  const [editando, setEditando] = useState(null); // null=lista, {}=form
  const [msg,      setMsg]      = useState(null);
  const [cargando, setCargando] = useState(false);

  const formInicial = {
    id: null, nombre_promo: '', no_activa: 0, lleva: 3, paga: 2,
    no_paga_porcentaje: 0, acumulable: 0, codigo_erp: '',
    desde: '', hasta: '',
    dias: { lunes:1, martes:1, miercoles:1, jueves:1, viernes:1, sabado:1, domingo:1 },
    articulos: [],
  };
  const [form, setForm] = useState(formInicial);

  const cargar = async () => {
    setLoading(true);
    const r = await fetch(`${API}/ListarPromociones/`);
    const d = await r.json();
    if (d.status === 'success') setPromos(d.data);
    setLoading(false);
  };

  useEffect(() => { cargar(); }, []);

  const abrirNueva = () => { setForm({ ...formInicial }); setEditando('nuevo'); setMsg(null); };
  const abrirEditar = (p) => {
    setForm({
      ...p,
      dias: p.dias || formInicial.dias,
      articulos: (p.articulos || []).map(a => a.cod_art),
    });
    setEditando('editar');
    setMsg(null);
  };

  const agregarArt = (art) => {
    if (form.articulos.includes(art.cod_art)) return;
    setForm(prev => ({ ...prev, articulos: [...prev.articulos, art.cod_art] }));
  };

  const quitarArt = (cod) => setForm(prev => ({ ...prev, articulos: prev.articulos.filter(a => a !== cod) }));

  const guardar = async () => {
    if (!form.nombre_promo) return setMsg({ tipo: 'error', texto: 'Nombre requerido.' });
    if (parseInt(form.paga) >= parseInt(form.lleva))
      return setMsg({ tipo: 'error', texto: 'paga debe ser < lleva.' });
    setCargando(true); setMsg(null);
    const r = await fetch(`${API}/GuardarPromocion/`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    const d = await r.json();
    if (r.ok && d.status === 'success') {
      setMsg({ tipo: 'ok', texto: d.mensaje });
      setEditando(null);
      cargar();
    } else {
      setMsg({ tipo: 'error', texto: d.mensaje });
    }
    setCargando(false);
  };

  const toggleActiva = async (id) => {
    await fetch(`${API}/TogglePromocion/`, { method: 'POST',
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) });
    cargar();
  };

  const DIA_LABEL = ['lunes','martes','miercoles','jueves','viernes','sabado','domingo'];

  if (editando !== null) {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <button onClick={() => setEditando(null)} style={s.btn('#57606a', true)}>← Volver</button>
          <h3 style={{ margin: 0 }}>{editando === 'nuevo' ? '🆕 Nueva Promoción' : `✏️ Editar: ${form.nombre_promo}`}</h3>
        </div>
        <Msg msg={msg} />

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '16px' }}>
          {/* Columna izquierda */}
          <div>
            <div style={s.card}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                <div style={{ gridColumn: 'span 2' }}>
                  <label style={s.label}>Nombre de la Promoción</label>
                  <input style={s.input} value={form.nombre_promo}
                    onChange={e => setForm(p => ({ ...p, nombre_promo: e.target.value }))} />
                </div>
                <div>
                  <label style={s.label}>Lleva (cantidad)</label>
                  <input type="number" min="1" style={s.input} value={form.lleva}
                    onChange={e => setForm(p => ({ ...p, lleva: parseInt(e.target.value) || 1 }))} />
                </div>
                <div>
                  <label style={s.label}>Paga (menor cantidad)</label>
                  <input type="number" min="1" style={s.input} value={form.paga}
                    onChange={e => setForm(p => ({ ...p, paga: parseInt(e.target.value) || 1 }))} />
                </div>
                <div>
                  <label style={s.label}>% Descuento sobre ítem gratis (0=precio 0)</label>
                  <input type="number" min="0" max="100" style={s.input} value={form.no_paga_porcentaje}
                    onChange={e => setForm(p => ({ ...p, no_paga_porcentaje: parseInt(e.target.value) || 0 }))} />
                </div>
                <div>
                  <label style={s.label}>Código ERP (opcional)</label>
                  <input style={s.input} value={form.codigo_erp}
                    onChange={e => setForm(p => ({ ...p, codigo_erp: e.target.value }))} />
                </div>
                <div>
                  <label style={s.label}>Vigencia Desde</label>
                  <input type="date" style={s.input} value={form.desde}
                    onChange={e => setForm(p => ({ ...p, desde: e.target.value }))} />
                </div>
                <div>
                  <label style={s.label}>Vigencia Hasta</label>
                  <input type="date" style={s.input} value={form.hasta}
                    onChange={e => setForm(p => ({ ...p, hasta: e.target.value }))} />
                </div>
              </div>

              {/* Checkboxes días */}
              <div>
                <label style={{ ...s.label, marginBottom: '8px' }}>Días activos</label>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {DIA_LABEL.map(dia => (
                    <label key={dia} style={{ display: 'flex', alignItems: 'center', gap: '4px',
                      padding: '6px 10px', border: '1px solid #d0d7de', borderRadius: '5px',
                      cursor: 'pointer', fontSize: '12px', fontWeight: '600',
                      background: form.dias[dia] ? '#dafbe1' : '#f6f8fa',
                      color: form.dias[dia] ? '#116329' : '#57606a' }}>
                      <input type="checkbox" style={{ display: 'none' }}
                        checked={!!form.dias[dia]}
                        onChange={e => setForm(p => ({ ...p, dias: { ...p.dias, [dia]: e.target.checked ? 1 : 0 } }))} />
                      {dia.charAt(0).toUpperCase() + dia.slice(1, 3)}
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '16px', marginTop: '12px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
                  <input type="checkbox" checked={!!form.acumulable}
                    onChange={e => setForm(p => ({ ...p, acumulable: e.target.checked ? 1 : 0 }))} />
                  Acumulable con otras promos
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
                  <input type="checkbox" checked={!form.no_activa}
                    onChange={e => setForm(p => ({ ...p, no_activa: e.target.checked ? 0 : 1 }))} />
                  Activa
                </label>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button onClick={() => setEditando(null)} style={s.btn('#57606a', true)}>Cancelar</button>
              <button onClick={guardar} disabled={cargando} style={s.btn('#2da44e')}>
                {cargando ? 'Guardando...' : '💾 Guardar Promoción'}
              </button>
            </div>
          </div>

          {/* Columna derecha: artículos */}
          <div>
            <div style={s.card}>
              <div style={{ fontSize: '12px', fontWeight: '700', color: '#57606a', textTransform: 'uppercase', marginBottom: '10px' }}>
                Artículos que integran la promo
              </div>
              <ArtAutoComplete placeholder="Agregar artículo..." onSelect={agregarArt} />
              <div style={{ marginTop: '12px' }}>
                {form.articulos.length === 0 && (
                  <div style={{ textAlign: 'center', color: '#8c959f', fontSize: '13px', padding: '16px' }}>
                    Sin artículos asignados.<br />
                    <small>(Vacío = aplica a todos)</small>
                  </div>
                )}
                {form.articulos.map(cod => (
                  <div key={cod} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '8px 10px', borderBottom: '1px solid #f0f0f0', fontSize: '13px' }}>
                    <span style={{ fontWeight: '700', color: '#0969da' }}>{cod}</span>
                    <button onClick={() => quitarArt(cod)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#cf222e' }}>✕</button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <h3 style={{ margin: 0, color: '#24292f' }}>Promociones N-lleva M-paga</h3>
        <button onClick={abrirNueva} style={s.btn('#8250df')}>+ Nueva Promoción</button>
      </div>

      {loading ? <div style={{ textAlign: 'center', padding: '30px', color: '#57606a' }}>Cargando...</div> : (
        <div style={{ display: 'grid', gap: '12px' }}>
          {promos.length === 0 && (
            <div style={{ textAlign: 'center', padding: '40px', color: '#8c959f', background: '#fff', borderRadius: '8px', border: '1px solid #d0d7de' }}>
              No hay promociones configuradas.
            </div>
          )}
          {promos.map(p => (
            <div key={p.id} style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px',
              borderLeft: `4px solid ${p.no_activa ? '#d0d7de' : '#8250df'}`,
              padding: '14px 18px', display: 'flex', alignItems: 'center', gap: '14px' }}>
              {/* Estado */}
              <div style={{ minWidth: '70px', textAlign: 'center' }}>
                <span style={{ display: 'block', background: p.no_activa ? '#f6f8fa' : '#f0e6ff',
                  color: p.no_activa ? '#8c959f' : '#8250df', padding: '3px 8px',
                  borderRadius: '10px', fontSize: '11px', fontWeight: '700' }}>
                  {p.no_activa ? 'Inactiva' : 'Activa'}
                </span>
              </div>
              {/* Info */}
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: '700', color: '#24292f', fontSize: '14px' }}>{p.nombre_promo}</div>
                <div style={{ fontSize: '12px', color: '#57606a', marginTop: '2px' }}>
                  Lleva <b>{p.lleva}</b> — Paga <b>{p.paga}</b>
                  {p.desde && ` | Vigencia: ${p.desde} → ${p.hasta}`}
                  {p.articulos && p.articulos.length > 0 &&
                    ` | ${p.articulos.length} artículo${p.articulos.length > 1 ? 's' : ''}`}
                  {(!p.articulos || p.articulos.length === 0) && ' | Todos los artículos'}
                </div>
              </div>
              {/* Acciones */}
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={() => toggleActiva(p.id)}
                  style={s.btn(p.no_activa ? '#2da44e' : '#cf222e')}>
                  {p.no_activa ? '✅ Activar' : '⏸ Desactivar'}
                </button>
                <button onClick={() => abrirEditar(p)} style={s.btn('#f39c12')}>✏️</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// MÓDULO PRINCIPAL
// ══════════════════════════════════════════════════════════════════════════════
export default function ModuloKitsPromos() {
  const [sub, setSub] = useState('KITS');

  return (
    <div style={{ background: '#f6f8fa', minHeight: '100%', padding: '4px' }}>
      <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#24292f', fontWeight: '700' }}>
        🧩 Kits, Combos y Promociones
      </h2>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        {[
          ['KITS',   '📦 Kits / Combos BOM'],
          ['PROMOS', '⭐ Promociones N×M'],
        ].map(([id, label]) => (
          <button key={id} onClick={() => setSub(id)} style={{
            padding: '8px 18px', borderRadius: '5px', cursor: 'pointer', fontWeight: '700', fontSize: '13px',
            background: sub === id ? '#0969da' : '#fff',
            color:      sub === id ? '#fff' : '#57606a',
            border:     `1px solid ${sub === id ? '#0969da' : '#d0d7de'}`,
          }}>{label}</button>
        ))}
      </div>

      {sub === 'KITS'   && <PanelKits />}
      {sub === 'PROMOS' && <PanelPromociones />}
    </div>
  );
}