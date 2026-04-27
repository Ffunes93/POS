import { useState, useEffect, useRef } from 'react';

const API = 'http://localhost:8001/api';
const fmt = n => parseFloat(n || 0).toFixed(2);

const s = {
  input: { width: '100%', padding: '9px 10px', border: '1px solid #d0d7de', borderRadius: '5px', fontSize: '14px', boxSizing: 'border-box' },
  label: { display: 'block', fontSize: '11px', fontWeight: '700', color: '#57606a', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '.4px' },
  btn: (col, secondary) => ({
    padding: '9px 18px', background: secondary ? '#fff' : col, color: secondary ? col : '#fff',
    border: `1px solid ${col}`, borderRadius: '5px', cursor: 'pointer', fontWeight: '700', fontSize: '13px',
  }),
};

// ── AutoComplete artículo ─────────────────────────────────────────────────────
function ArtAutoComplete({ onSelect }) {
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
              <span style={{ float: 'right', color: '#0969da' }}>${fmt(a.precio_1)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Formulario Nueva / Editar Cotización ──────────────────────────────────────
function FormCotizacion({ movimEditar, onGuardado, onCancelar, cajaId, user }) {
  const [cliente,  setCliente]  = useState({ cod_cli: '1', denominacion: 'CONSUMIDOR FINAL' });
  const [cliText,  setCliText]  = useState('CONSUMIDOR FINAL');
  const [cliSugg,  setCliSugg]  = useState([]);
  const [items,    setItems]    = useState([]);
  const [cantidad, setCantidad] = useState('1');
  const [precio,   setPrecio]   = useState('');
  const [artSel,   setArtSel]   = useState(null);
  const [observac, setObservac] = useState('');
  const [cargando, setCargando] = useState(false);
  const [msg,      setMsg]      = useState(null);
  const cliRef = useRef(null);
  const hoy = new Date().toISOString().split('T')[0];

  // Cargar cotización existente para edición
  useEffect(() => {
    if (!movimEditar) return;
    fetch(`${API}/ObtenerCotizacion/${movimEditar}/`)
      .then(r => r.json()).then(d => {
        if (d.status === 'success') {
          const c = d.data;
          setCliente({ cod_cli: c.cod_cli, denominacion: c.nom_cli });
          setCliText(c.nom_cli);
          setObservac(c.observac || '');
          setItems(c.items.map(i => ({
            id:          Date.now() + Math.random(),
            cod_art:     i.cod_articulo,
            descripcion: i.detalle,
            cantidad:    parseFloat(i.cantidad),
            precio:      parseFloat(i.precio_unit),
            total:       parseFloat(i.total),
            p_iva:       parseFloat(i.p_iva || 21),
          })));
        }
      });
  }, [movimEditar]);

  // Buscar clientes
  useEffect(() => {
    if (cliText.length < 2) { setCliSugg([]); return; }
    const t = setTimeout(async () => {
      const r = await fetch(`${API}/ListarClientes/?buscar=${encodeURIComponent(cliText)}`);
      const d = await r.json();
      if (d.status === 'success') setCliSugg(d.data.slice(0, 8));
    }, 260);
    return () => clearTimeout(t);
  }, [cliText]);

  useEffect(() => {
    const fn = e => { if (cliRef.current && !cliRef.current.contains(e.target)) setCliSugg([]); };
    document.addEventListener('mousedown', fn);
    return () => document.removeEventListener('mousedown', fn);
  }, []);

  const agregarItem = () => {
    if (!artSel) return setMsg({ tipo: 'error', texto: 'Seleccione un artículo.' });
    const cant = parseFloat(cantidad);
    const prec = parseFloat(precio);
    if (!cant || cant <= 0) return setMsg({ tipo: 'error', texto: 'Cantidad inválida.' });
    if (isNaN(prec) || prec <= 0) return setMsg({ tipo: 'error', texto: 'Precio inválido.' });
    const p_iva = parseFloat(artSel.iva || 21);
    const subtotal = cant * prec;
    const v_iva = subtotal - subtotal / (1 + p_iva / 100);
    setItems(prev => [...prev, {
      id: Date.now(), cod_art: artSel.cod_art, descripcion: artSel.nombre,
      cantidad: cant, precio: prec, total: subtotal, p_iva, v_iva,
    }]);
    setArtSel(null); setCantidad('1'); setPrecio(''); setMsg(null);
  };

  const neto    = items.reduce((s, i) => s + i.total, 0);
  const ivaT    = items.reduce((s, i) => s + (i.v_iva || 0), 0);
  const total   = neto + ivaT;

  const guardar = async () => {
    if (items.length === 0) return setMsg({ tipo: 'error', texto: 'Agregue al menos un artículo.' });
    setCargando(true); setMsg(null);
    const payload = {
      movim:    movimEditar || null,
      cod_cli:  cliente.cod_cli,
      nom_cli:  cliente.denominacion,
      fecha_fact: new Date().toISOString(),
      observac,
      cajero:  cajaId || 1,
      nro_caja: cajaId || 1,
      usuario: user?.nombrelogin || 'admin',
      vendedor: user?.id || 1,
      items: items.map(i => ({
        cod_articulo: i.cod_art,
        descripcion:  i.descripcion,
        cantidad:     i.cantidad,
        precio_unit:  i.precio,
        total:        i.total,
        p_iva:        i.p_iva,
        v_iva:        i.v_iva || 0,
        descuento:    0,
      })),
    };
    const r  = await fetch(`${API}/GuardarCotizacion/`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
    });
    const d  = await r.json();
    if (r.ok && d.status === 'success') {
      setMsg({ tipo: 'ok', texto: `✅ ${d.mensaje}` });
      onGuardado(d);
    } else {
      setMsg({ tipo: 'error', texto: d.mensaje || 'Error al guardar.' });
    }
    setCargando(false);
  };

  return (
    <div>
      <h3 style={{ marginTop: 0, color: '#24292f' }}>
        {movimEditar ? '✏️ Editar Cotización' : '📋 Nueva Cotización / Presupuesto'}
      </h3>

      {msg && (
        <div style={{ padding: '10px 16px', borderRadius: '6px', marginBottom: '14px', fontSize: '13px', fontWeight: '600',
          background: msg.tipo === 'ok' ? '#dafbe1' : '#ffebe9',
          color:      msg.tipo === 'ok' ? '#116329' : '#a40e26',
          border:     `1px solid ${msg.tipo === 'ok' ? '#56d364' : '#ff818266'}` }}>{msg.texto}</div>
      )}

      {/* Cliente + observación */}
      <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', padding: '16px', marginBottom: '14px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '14px' }}>
          <div>
            <label style={s.label}>Cliente</label>
            <div ref={cliRef} style={{ position: 'relative' }}>
              <input style={s.input} value={cliText}
                onChange={e => { setCliText(e.target.value); setCliente({ ...cliente, denominacion: e.target.value }); }}
                placeholder="Buscar por nombre o CUIT..." />
              {cliSugg.length > 0 && (
                <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100,
                  background: '#fff', border: '1px solid #d0d7de', borderRadius: '5px',
                  boxShadow: '0 8px 24px rgba(0,0,0,.1)', maxHeight: '200px', overflowY: 'auto' }}>
                  {cliSugg.map((c, i) => (
                    <div key={i} onClick={() => { setCliente({ cod_cli: c.cod_cli, denominacion: c.denominacion }); setCliText(c.denominacion); setCliSugg([]); }}
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
          <div>
            <label style={s.label}>Observaciones</label>
            <input style={s.input} value={observac} onChange={e => setObservac(e.target.value)} placeholder="Opcional..." />
          </div>
        </div>
      </div>

      {/* Agregar artículo */}
      <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', padding: '16px', marginBottom: '14px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 100px 130px auto', gap: '10px', alignItems: 'flex-end' }}>
          <div>
            <label style={s.label}>Artículo</label>
            <ArtAutoComplete onSelect={a => { setArtSel(a); setPrecio(fmt(a.precio_1)); }} />
            {artSel && <span style={{ fontSize: '12px', color: '#57606a' }}>✓ {artSel.nombre}</span>}
          </div>
          <div>
            <label style={s.label}>Cantidad</label>
            <input type="number" step="0.001" value={cantidad} onChange={e => setCantidad(e.target.value)} style={s.input} />
          </div>
          <div>
            <label style={s.label}>Precio Unit.</label>
            <input type="number" step="0.01" value={precio} onChange={e => setPrecio(e.target.value)} style={s.input} />
          </div>
          <button onClick={agregarItem} style={s.btn('#2da44e')}>+ Agregar</button>
        </div>
      </div>

      {/* Grilla */}
      {items.length > 0 && (
        <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', overflow: 'hidden', marginBottom: '14px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ background: '#f6f8fa', textAlign: 'left', borderBottom: '1px solid #d0d7de' }}>
                <th style={{ padding: '9px 12px' }}>Código</th>
                <th style={{ padding: '9px 12px' }}>Descripción</th>
                <th style={{ padding: '9px 12px', textAlign: 'right' }}>Cant.</th>
                <th style={{ padding: '9px 12px', textAlign: 'right' }}>P. Unit.</th>
                <th style={{ padding: '9px 12px', textAlign: 'right' }}>Subtotal</th>
                <th style={{ padding: '9px 12px', width: 36 }}></th>
              </tr>
            </thead>
            <tbody>
              {items.map(i => (
                <tr key={i.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '9px 12px', fontWeight: '700', color: '#0969da' }}>{i.cod_art}</td>
                  <td style={{ padding: '9px 12px' }}>{i.descripcion}</td>
                  <td style={{ padding: '9px 12px', textAlign: 'right' }}>{i.cantidad}</td>
                  <td style={{ padding: '9px 12px', textAlign: 'right' }}>${fmt(i.precio)}</td>
                  <td style={{ padding: '9px 12px', textAlign: 'right', fontWeight: '700', color: '#1a7f37' }}>${fmt(i.total)}</td>
                  <td style={{ padding: '9px 12px', textAlign: 'center' }}>
                    <button onClick={() => setItems(p => p.filter(x => x.id !== i.id))}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#cf222e', fontSize: '16px' }}>✕</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Totales + botones */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', padding: '14px 18px' }}>
        <div style={{ display: 'flex', gap: '24px', fontSize: '14px' }}>
          <span>Neto: <b>${fmt(neto)}</b></span>
          <span>IVA: <b>${fmt(ivaT)}</b></span>
          <span style={{ fontSize: '18px' }}>TOTAL: <b style={{ color: '#1a7f37' }}>${fmt(total)}</b></span>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={onCancelar} style={s.btn('#57606a', true)}>Cancelar</button>
          <button onClick={guardar} disabled={cargando} style={s.btn(cargando ? '#94d3a2' : '#2da44e')}>
            {cargando ? 'Guardando...' : '💾 Guardar Cotización'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Modal convertir a factura ──────────────────────────────────────────────────
function ModalUtilizar({ cotiza, onConfirm, onCancelar }) {
  const [tipos,       setTipos]       = useState([]);
  const [tipoSel,     setTipoSel]     = useState('EA');
  const [medioPago,   setMedioPago]   = useState('EFE');
  const [cargando,    setCargando]    = useState(false);

  useEffect(() => {
    fetch(`${API}/GestionarTipocompCli/`).then(r => r.json()).then(d => {
      if (d.status === 'success') {
        const permitidos = ['EA', 'EB', 'EC', 'FA', 'FB', 'FC'];
        setTipos(d.data.filter(t => permitidos.includes(t.cod_compro)));
      }
    });
  }, []);

  const confirmar = async () => {
    setCargando(true);
    await onConfirm({ tipo_comprobante: tipoSel, medio_pago: medioPago });
    setCargando(false);
  };

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,.6)',
      display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 999 }}>
      <div style={{ background: '#fff', borderRadius: '10px', padding: '28px', width: '400px', boxShadow: '0 12px 32px rgba(0,0,0,.2)' }}>
        <h3 style={{ marginTop: 0, color: '#24292f' }}>🧾 Convertir a Factura</h3>
        <p style={{ fontSize: '13px', color: '#57606a', marginBottom: '20px' }}>
          Cotización N° <b>{cotiza.nro_comprob}</b> — Total: <b style={{ color: '#1a7f37' }}>${fmt(cotiza.tot_general)}</b>
        </p>
        <div style={{ marginBottom: '14px' }}>
          <label style={s.label}>Tipo de Comprobante</label>
          <select value={tipoSel} onChange={e => setTipoSel(e.target.value)} style={s.input}>
            {tipos.map(t => <option key={t.id_compro} value={t.cod_compro}>{t.cod_compro} — {t.nom_compro}</option>)}
          </select>
        </div>
        <div style={{ marginBottom: '20px' }}>
          <label style={s.label}>Medio de Pago</label>
          <select value={medioPago} onChange={e => setMedioPago(e.target.value)} style={s.input}>
            <option value="EFE">💵 Efectivo</option>
            <option value="TAR">💳 Tarjeta</option>
            <option value="TRF">🔁 Transferencia</option>
            <option value="CTA">📒 Cuenta Corriente</option>
          </select>
        </div>
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          <button onClick={onCancelar} style={s.btn('#57606a', true)}>Cancelar</button>
          <button onClick={confirmar} disabled={cargando} style={s.btn('#2da44e')}>
            {cargando ? 'Procesando...' : '✅ Confirmar y Facturar'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Listado ────────────────────────────────────────────────────────────────────
function ListadoCotizaciones({ onEditar, onNueva }) {
  const hoy    = new Date().toISOString().split('T')[0];
  const primer = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0];
  const [desde,    setDesde]    = useState(primer);
  const [hasta,    setHasta]    = useState(hoy);
  const [pendientes, setPend]   = useState(true);
  const [lista,    setLista]    = useState([]);
  const [loading,  setLoading]  = useState(false);
  const [msg,      setMsg]      = useState(null);
  const [utilizar, setUtilizar] = useState(null);

  const cargar = async () => {
    setLoading(true);
    const params = new URLSearchParams({ desde, hasta, ...(pendientes ? { pendientes: '1' } : {}) });
    const r = await fetch(`${API}/ListarCotizaciones/?${params}`);
    const d = await r.json();
    if (d.status === 'success') setLista(d.data);
    setLoading(false);
  };

  useEffect(() => { cargar(); }, []);

  const anular = async (movim) => {
    if (!window.confirm('¿Anular esta cotización?')) return;
    const r = await fetch(`${API}/AnularCotizacion/`, { method: 'POST',
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ movim }) });
    const d = await r.json();
    setMsg({ tipo: r.ok && d.status === 'success' ? 'ok' : 'error', texto: d.mensaje });
    cargar();
  };

  const confirmarUtilizar = async ({ tipo_comprobante, medio_pago }) => {
    const r = await fetch(`${API}/UtilizarCotizacion/`, { method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ movim: utilizar.movim, tipo_comprobante, medio_pago, cajero: 1, nro_caja: 1 }) });
    const d = await r.json();
    setMsg({ tipo: r.ok && d.status === 'success' ? 'ok' : 'error', texto: d.mensaje });
    setUtilizar(null);
    cargar();
  };

  return (
    <div>
      {utilizar && (
        <ModalUtilizar
          cotiza={utilizar}
          onConfirm={confirmarUtilizar}
          onCancelar={() => setUtilizar(null)}
        />
      )}

      {msg && (
        <div style={{ padding: '10px 16px', borderRadius: '6px', marginBottom: '14px', fontSize: '13px', fontWeight: '600',
          background: msg.tipo === 'ok' ? '#dafbe1' : '#ffebe9',
          color:      msg.tipo === 'ok' ? '#116329' : '#a40e26',
          border:     `1px solid ${msg.tipo === 'ok' ? '#56d364' : '#ff818266'}` }}>{msg.texto}</div>
      )}

      {/* Filtros */}
      <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', padding: '14px 18px',
        marginBottom: '14px', display: 'flex', gap: '14px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
        <div>
          <label style={s.label}>Desde</label>
          <input type="date" value={desde} onChange={e => setDesde(e.target.value)}
            style={{ padding: '8px 10px', border: '1px solid #d0d7de', borderRadius: '5px', fontSize: '13px' }} />
        </div>
        <div>
          <label style={s.label}>Hasta</label>
          <input type="date" value={hasta} onChange={e => setHasta(e.target.value)}
            style={{ padding: '8px 10px', border: '1px solid #d0d7de', borderRadius: '5px', fontSize: '13px' }} />
        </div>
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
          <input type="checkbox" checked={pendientes} onChange={e => setPend(e.target.checked)} />
          Solo pendientes
        </label>
        <button onClick={cargar} disabled={loading} style={s.btn('#0969da')}>
          {loading ? '...' : '🔍 Filtrar'}
        </button>
        <button onClick={onNueva} style={{ ...s.btn('#2da44e'), marginLeft: 'auto' }}>
          + Nueva Cotización
        </button>
      </div>

      {/* Tabla */}
      <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: '#f6f8fa', borderBottom: '2px solid #d0d7de', textAlign: 'left' }}>
              <th style={{ padding: '10px 12px' }}>N°</th>
              <th style={{ padding: '10px 12px' }}>Fecha</th>
              <th style={{ padding: '10px 12px' }}>Cliente</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>Total</th>
              <th style={{ padding: '10px 12px', textAlign: 'center' }}>Estado</th>
              <th style={{ padding: '10px 12px', textAlign: 'center' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={6} style={{ padding: '24px', textAlign: 'center', color: '#57606a' }}>Cargando...</td></tr>}
            {!loading && lista.length === 0 && (
              <tr><td colSpan={6} style={{ padding: '24px', textAlign: 'center', color: '#8c959f' }}>
                No hay cotizaciones en el período
              </td></tr>
            )}
            {lista.map(c => {
              const anulada  = c.anulado === 'S';
              const utilizada = c.utilizada === 1;
              const estadoColor = anulada ? '#cf222e' : utilizada ? '#8250df' : '#1a7f37';
              const estadoLabel = anulada ? 'Anulada' : utilizada ? 'Facturada' : 'Vigente';
              return (
                <tr key={c.movim} style={{ borderBottom: '1px solid #f0f0f0', background: anulada ? '#fff8f8' : '' }}>
                  <td style={{ padding: '10px 12px', fontWeight: '700', color: '#0969da' }}>PR-{c.nro_comprob}</td>
                  <td style={{ padding: '10px 12px', color: '#57606a' }}>{new Date(c.fecha_fact).toLocaleDateString()}</td>
                  <td style={{ padding: '10px 12px' }}>{c.denominacion || c.nom_cli}</td>
                  <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: '700', color: '#1a7f37' }}>
                    ${fmt(c.tot_general)}
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                    <span style={{ background: `${estadoColor}22`, color: estadoColor,
                      padding: '2px 10px', borderRadius: '10px', fontSize: '11px', fontWeight: '700' }}>
                      {estadoLabel}
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                    {!anulada && !utilizada && (
                      <div style={{ display: 'flex', gap: '6px', justifyContent: 'center' }}>
                        <button onClick={() => setUtilizar(c)}
                          style={{ padding: '4px 10px', background: '#2da44e', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px', fontWeight: '700' }}>
                          🧾 Facturar
                        </button>
                        <button onClick={() => onEditar(c.movim)}
                          style={{ padding: '4px 10px', background: '#f39c12', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>
                          ✏️
                        </button>
                        <button onClick={() => anular(c.movim)}
                          style={{ padding: '4px 10px', background: '#cf222e', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>
                          🚫
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Módulo principal ──────────────────────────────────────────────────────────
export default function ModuloCotizaciones({ cajaId, user }) {
  const [vista,       setVista]       = useState('LISTADO'); // LISTADO | FORM
  const [movimEditar, setMovimEditar] = useState(null);

  const handleGuardado = () => {
    setVista('LISTADO'); setMovimEditar(null);
  };

  return (
    <div style={{ background: '#f6f8fa', minHeight: '100%', padding: '4px' }}>
      <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#24292f', fontWeight: '700' }}>
        📋 Cotizaciones / Presupuestos
      </h2>

      {vista === 'LISTADO' && (
        <ListadoCotizaciones
          onEditar={movim => { setMovimEditar(movim); setVista('FORM'); }}
          onNueva={() => { setMovimEditar(null); setVista('FORM'); }}
        />
      )}
      {vista === 'FORM' && (
        <FormCotizacion
          movimEditar={movimEditar}
          cajaId={cajaId}
          user={user}
          onGuardado={handleGuardado}
          onCancelar={() => { setVista('LISTADO'); setMovimEditar(null); }}
        />
      )}
    </div>
  );
}