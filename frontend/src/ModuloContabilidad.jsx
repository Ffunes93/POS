// ModuloContabilidad.jsx — versión extendida
// Nuevos paneles vs versión anterior:
//   - Ejercicios (CRUD)
//   - Tipos de Asiento (CRUD)
//   - Series de Numeración (CRUD)
//   - Modelos de Asientos (CRUD con líneas)
//   - Asientos Automáticos (Apertura, Cierre, Ajuste Inflación, etc.)
//   - Ingreso Manual mejorado (con tipo, serie, estado)
//   - Consulta de Saldos
//   - Importación de Asientos (JSON)
import { useState, useEffect, useCallback } from "react";

const API = `${import.meta.env.VITE_API_URL}/api/contab`;
const fmt = (n) =>
  Number(n || 0).toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const hoy = () => new Date().toISOString().slice(0, 10);
const primerDiaMes = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-01`;
};

// ── UI helpers ────────────────────────────────────────────────────────────────
const Badge = ({ ok }) => (
  <span style={{
    background: ok ? "#d1fae5" : "#fee2e2", color: ok ? "#065f46" : "#991b1b",
    padding: "2px 10px", borderRadius: 12, fontSize: 12, fontWeight: 700,
  }}>{ok ? "✓ Cuadra" : "✗ Descuadrado"}</span>
);

const Card = ({ children, style }) => (
  <div style={{ background: "#fff", borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,.10)", padding: 20, marginBottom: 16, ...style }}>
    {children}
  </div>
);

const Th = ({ children, right }) => (
  <th style={{ background: "#f8f9fa", padding: "8px 12px", textAlign: right ? "right" : "left", fontSize: 12, fontWeight: 700, color: "#555", borderBottom: "2px solid #dee2e6" }}>
    {children}
  </th>
);

const Td = ({ children, right, bold, color, colSpan }) => (
  <td colSpan={colSpan} style={{ padding: "7px 12px", fontSize: 13, textAlign: right ? "right" : "left", fontWeight: bold ? 700 : 400, color: color || "inherit", borderBottom: "1px solid #f0f0f0" }}>
    {children}
  </td>
);

const Btn = ({ children, onClick, color = "#2563eb", secondary, disabled, sm }) => (
  <button onClick={onClick} disabled={disabled} style={{
    padding: sm ? "4px 12px" : "7px 18px", background: secondary ? "#fff" : (disabled ? "#94a3b8" : color),
    color: secondary ? color : "#fff", border: `1px solid ${disabled ? "#94a3b8" : color}`,
    borderRadius: 6, cursor: disabled ? "not-allowed" : "pointer", fontWeight: 600, fontSize: sm ? 12 : 13,
  }}>{children}</button>
);

const Input = ({ label, value, onChange, type = "text", placeholder, required }) => (
  <label style={{ fontSize: 13 }}>
    {label}{required && <span style={{ color: "#dc2626" }}> *</span>}<br />
    <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
      style={{ width: "100%", padding: "7px 10px", border: "1px solid #ccc", borderRadius: 6, fontSize: 13, marginTop: 3 }} />
  </label>
);

const Select = ({ label, value, onChange, options, required }) => (
  <label style={{ fontSize: 13 }}>
    {label}{required && <span style={{ color: "#dc2626" }}> *</span>}<br />
    <select value={value} onChange={e => onChange(e.target.value)}
      style={{ width: "100%", padding: "7px 10px", border: "1px solid #ccc", borderRadius: 6, fontSize: 13, marginTop: 3 }}>
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  </label>
);

const Msg = ({ msg }) => {
  if (!msg) return null;
  const ok = msg.tipo === "ok";
  return (
    <div style={{ padding: "10px 16px", borderRadius: 6, marginBottom: 14, fontSize: 13, fontWeight: 600,
      background: ok ? "#d1fae5" : "#fee2e2", color: ok ? "#065f46" : "#991b1b",
      border: `1px solid ${ok ? "#6ee7b7" : "#fca5a5"}` }}>{msg.texto}</div>
  );
};

const FiltroFechas = ({ desde, hasta, onDesde, onHasta, onBuscar, cargando }) => (
  <div style={{ display: "flex", gap: 10, alignItems: "flex-end", flexWrap: "wrap", marginBottom: 16 }}>
    <Input label="Desde" type="date" value={desde} onChange={onDesde} />
    <Input label="Hasta" type="date" value={hasta} onChange={onHasta} />
    <div style={{ paddingTop: 20 }}>
      <Btn onClick={onBuscar} disabled={cargando}>{cargando ? "..." : "Consultar"}</Btn>
    </div>
  </div>
);

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: Ejercicios Contables
// ═══════════════════════════════════════════════════════════════════════════════
function PanelEjercicios() {
  const [lista,    setLista]    = useState([]);
  const [loading,  setLoading]  = useState(false);
  const [form,     setForm]     = useState({ anio_inicio: new Date().getFullYear(), anio_fin: new Date().getFullYear(), fecha_inicio: `${new Date().getFullYear()}-01-01`, fecha_fin: `${new Date().getFullYear()}-12-31`, estado: 'A', descripcion: '', usa_ajuste_inflacion: false });
  const [editando, setEditando] = useState(false);
  const [msg,      setMsg]      = useState(null);

  const cargar = useCallback(async () => {
    setLoading(true);
    try { const r = await fetch(`${API}/Ejercicios/`); setLista(await r.json()); } catch {}
    setLoading(false);
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  const guardar = async () => {
    setMsg(null);
    const method = form.id ? 'PUT' : 'POST';
    const url    = form.id ? `${API}/Ejercicios/${form.id}/` : `${API}/Ejercicios/`;
    const r  = await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) });
    const d  = await r.json();
    if (d.ok || d.id) { setMsg({ tipo: "ok", texto: "Ejercicio guardado." }); setEditando(false); setForm({ anio_inicio: new Date().getFullYear(), anio_fin: new Date().getFullYear(), fecha_inicio: `${new Date().getFullYear()}-01-01`, fecha_fin: `${new Date().getFullYear()}-12-31`, estado: 'A', descripcion: '', usa_ajuste_inflacion: false }); cargar(); }
    else setMsg({ tipo: "error", texto: d.error || "Error al guardar." });
  };

  const cerrar = async (id) => {
    const r = await fetch(`${API}/Ejercicios/${id}/`, { method: 'PUT', headers: { "Content-Type": "application/json" }, body: JSON.stringify({ estado: 'C' }) });
    const d = await r.json();
    if (d.ok) cargar();
  };

  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ margin: 0, color: "#1e3a5f" }}>📅 Ejercicios Contables</h3>
        <Btn onClick={() => setEditando(!editando)} color="#7c3aed">{editando ? "× Cancelar" : "+ Nuevo Ejercicio"}</Btn>
      </div>

      {msg && <Msg msg={msg} />}

      {editando && (
        <div style={{ background: "#f8f5ff", border: "1px solid #c4b5fd", borderRadius: 8, padding: 16, marginBottom: 16 }}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <div style={{ flex: "1 1 100px" }}><Input label="Año Inicio" type="number" value={form.anio_inicio} onChange={v => setForm(p => ({ ...p, anio_inicio: parseInt(v) }))} required /></div>
            <div style={{ flex: "1 1 100px" }}><Input label="Año Fin" type="number" value={form.anio_fin} onChange={v => setForm(p => ({ ...p, anio_fin: parseInt(v) }))} required /></div>
            <div style={{ flex: "1 1 140px" }}><Input label="Fecha Inicio" type="date" value={form.fecha_inicio} onChange={v => setForm(p => ({ ...p, fecha_inicio: v }))} required /></div>
            <div style={{ flex: "1 1 140px" }}><Input label="Fecha Fin" type="date" value={form.fecha_fin} onChange={v => setForm(p => ({ ...p, fecha_fin: v }))} required /></div>
            <div style={{ flex: "2 1 200px" }}><Input label="Descripción" value={form.descripcion} onChange={v => setForm(p => ({ ...p, descripcion: v }))} /></div>
            <div style={{ flex: "1 1 100px" }}>
              <Select label="Estado" value={form.estado} onChange={v => setForm(p => ({ ...p, estado: v }))}
                options={[{ value: 'A', label: 'Abierto' }, { value: 'C', label: 'Cerrado' }]} />
            </div>
          </div>
          <div style={{ marginTop: 10, display: "flex", gap: 10, alignItems: "center" }}>
            <label style={{ fontSize: 13, display: "flex", gap: 6, alignItems: "center" }}>
              <input type="checkbox" checked={form.usa_ajuste_inflacion} onChange={e => setForm(p => ({ ...p, usa_ajuste_inflacion: e.target.checked }))} />
              Usa Ajuste por Inflación
            </label>
            <Btn onClick={guardar} color="#7c3aed">Guardar</Btn>
          </div>
        </div>
      )}

      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead><tr><Th>Período</Th><Th>Descripción</Th><Th>Fechas</Th><Th>Inflación</Th><Th>Estado</Th><Th>Acciones</Th></tr></thead>
        <tbody>
          {loading ? <tr><Td colSpan={6} style={{ textAlign: "center" }}>Cargando...</Td></tr>
          : lista.map(e => (
            <tr key={e.id}>
              <Td bold>{e.anio_inicio} — {e.anio_fin}</Td>
              <Td>{e.descripcion || "—"}</Td>
              <Td>{e.fecha_inicio} / {e.fecha_fin}</Td>
              <Td>{e.usa_ajuste_inflacion ? "✓" : "—"}</Td>
              <Td>
                <span style={{ background: e.estado === 'A' ? "#d1fae5" : "#f1f5f9", color: e.estado === 'A' ? "#065f46" : "#475569", padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 700 }}>
                  {e.estado === 'A' ? 'Abierto' : 'Cerrado'}
                </span>
              </Td>
              <Td>
                {e.estado === 'A' && <Btn sm color="#b45309" onClick={() => { if (window.confirm('¿Cerrar este ejercicio?')) cerrar(e.id); }}>Cerrar</Btn>}
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: Tipos de Asiento
// ═══════════════════════════════════════════════════════════════════════════════
function PanelTiposAsiento() {
  const [lista, setLista] = useState([]);
  const [form, setForm]   = useState({ codigo: '', descripcion: '', habilitado: true, excluye_eecc: false });
  const [edit, setEdit]   = useState(false);
  const [msg,  setMsg]    = useState(null);

  const cargar = useCallback(async () => {
    const r = await fetch(`${API}/TiposAsiento/`);
    setLista(await r.json());
  }, []);
  useEffect(() => { cargar(); }, [cargar]);

  const guardar = async () => {
    const r = await fetch(`${API}/TiposAsiento/`, { method: 'POST', headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) });
    const d = await r.json();
    if (d.ok) { setMsg({ tipo: "ok", texto: "Guardado." }); setEdit(false); setForm({ codigo: '', descripcion: '', habilitado: true, excluye_eecc: false }); cargar(); }
    else setMsg({ tipo: "error", texto: d.error || "Error." });
  };

  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ margin: 0, color: "#1e3a5f" }}>🏷️ Tipos de Asiento</h3>
        <Btn color="#7c3aed" onClick={() => setEdit(!edit)}>{edit ? "× Cancelar" : "+ Nuevo"}</Btn>
      </div>
      <Msg msg={msg} />
      {edit && (
        <div style={{ background: "#f8f5ff", border: "1px solid #c4b5fd", borderRadius: 8, padding: 16, marginBottom: 16, display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end" }}>
          <div style={{ flex: "1 1 100px" }}><Input label="Código" value={form.codigo} onChange={v => setForm(p => ({ ...p, codigo: v.toUpperCase() }))} required /></div>
          <div style={{ flex: "3 1 200px" }}><Input label="Descripción" value={form.descripcion} onChange={v => setForm(p => ({ ...p, descripcion: v }))} required /></div>
          <label style={{ fontSize: 13, display: "flex", gap: 6, alignItems: "center" }}>
            <input type="checkbox" checked={form.habilitado} onChange={e => setForm(p => ({ ...p, habilitado: e.target.checked }))} /> Habilitado
          </label>
          <label style={{ fontSize: 13, display: "flex", gap: 6, alignItems: "center" }}>
            <input type="checkbox" checked={form.excluye_eecc} onChange={e => setForm(p => ({ ...p, excluye_eecc: e.target.checked }))} /> Excluye EECC
          </label>
          <Btn onClick={guardar} color="#7c3aed">Guardar</Btn>
        </div>
      )}
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead><tr><Th>Código</Th><Th>Descripción</Th><Th>Excluye EECC</Th><Th>Estado</Th></tr></thead>
        <tbody>
          {lista.map(t => (
            <tr key={t.codigo}>
              <Td bold>{t.codigo}</Td>
              <Td>{t.descripcion}</Td>
              <Td>{t.excluye_eecc ? "✓" : "—"}</Td>
              <Td><span style={{ background: t.habilitado ? "#d1fae5" : "#fee2e2", color: t.habilitado ? "#065f46" : "#991b1b", padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 700 }}>{t.habilitado ? "Activo" : "Inactivo"}</span></Td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: Series de Numeración
// ═══════════════════════════════════════════════════════════════════════════════
function PanelSeries() {
  const [lista, setLista] = useState([]);
  const [form, setForm]   = useState({ codigo: '', descripcion: '', ultimo_nro: 0, habilitada: true });
  const [edit, setEdit]   = useState(false);
  const [msg,  setMsg]    = useState(null);

  const cargar = useCallback(async () => {
    const r = await fetch(`${API}/Series/`);
    setLista(await r.json());
  }, []);
  useEffect(() => { cargar(); }, [cargar]);

  const guardar = async () => {
    const r = await fetch(`${API}/Series/`, { method: 'POST', headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) });
    const d = await r.json();
    if (d.ok) { setMsg({ tipo: "ok", texto: "Guardado." }); setEdit(false); setForm({ codigo: '', descripcion: '', ultimo_nro: 0, habilitada: true }); cargar(); }
    else setMsg({ tipo: "error", texto: d.error || "Error." });
  };

  const ajustarNro = async (codigo, nuevoNro) => {
    await fetch(`${API}/Series/${codigo}/`, { method: 'PUT', headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ultimo_nro: parseInt(nuevoNro) || 0 }) });
    cargar();
  };

  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ margin: 0, color: "#1e3a5f" }}>🔢 Series de Numeración</h3>
        <Btn color="#7c3aed" onClick={() => setEdit(!edit)}>{edit ? "× Cancelar" : "+ Nueva Serie"}</Btn>
      </div>
      <Msg msg={msg} />
      {edit && (
        <div style={{ background: "#f8f5ff", border: "1px solid #c4b5fd", borderRadius: 8, padding: 16, marginBottom: 16, display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end" }}>
          <div style={{ flex: "1 1 80px" }}><Input label="Código" value={form.codigo} onChange={v => setForm(p => ({ ...p, codigo: v.toUpperCase() }))} required /></div>
          <div style={{ flex: "3 1 200px" }}><Input label="Descripción" value={form.descripcion} onChange={v => setForm(p => ({ ...p, descripcion: v }))} required /></div>
          <div style={{ flex: "1 1 100px" }}><Input label="Desde N°" type="number" value={form.ultimo_nro} onChange={v => setForm(p => ({ ...p, ultimo_nro: parseInt(v) || 0 }))} /></div>
          <Btn onClick={guardar} color="#7c3aed">Guardar</Btn>
        </div>
      )}
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead><tr><Th>Código</Th><Th>Descripción</Th><Th right>Último N°</Th><Th>Estado</Th><Th>Ajustar</Th></tr></thead>
        <tbody>
          {lista.map(s => (
            <tr key={s.codigo}>
              <Td bold>{s.codigo}</Td>
              <Td>{s.descripcion}</Td>
              <Td right bold>{s.ultimo_nro}</Td>
              <Td><span style={{ background: s.habilitada ? "#d1fae5" : "#fee2e2", color: s.habilitada ? "#065f46" : "#991b1b", padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 700 }}>{s.habilitada ? "Activa" : "Inactiva"}</span></Td>
              <Td>
                <input type="number" defaultValue={s.ultimo_nro} id={`nro_${s.codigo}`}
                  style={{ width: 80, padding: "3px 6px", border: "1px solid #ccc", borderRadius: 4, fontSize: 12 }} />
                <Btn sm color="#0f766e" onClick={() => ajustarNro(s.codigo, document.getElementById(`nro_${s.codigo}`).value)}>✓</Btn>
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: Modelos de Asientos
// ═══════════════════════════════════════════════════════════════════════════════
function PanelModelos() {
  const [lista,    setLista]    = useState([]);
  const [cuentas,  setCuentas]  = useState([]);
  const [tipos,    setTipos]    = useState([]);
  const [form,     setForm]     = useState({ codigo: '', descripcion: '', habilitado: true, tipo_asiento: '', lineas: [] });
  const [edit,     setEdit]     = useState(false);
  const [expandido, setExpand]  = useState({});
  const [msg,      setMsg]      = useState(null);

  useEffect(() => {
    fetch(`${API}/Modelos/`).then(r => r.json()).then(setLista).catch(() => {});
    fetch(`${API}/PlanCuentas/?imputables=1`).then(r => r.json()).then(setCuentas).catch(() => {});
    fetch(`${API}/TiposAsiento/`).then(r => r.json()).then(setTipos).catch(() => {});
  }, []);

  const agregarLinea = () => setForm(p => ({ ...p, lineas: [...p.lineas, { cuenta: '', tipo: 'D', importe: 0, descripcion: '' }] }));
  const quitarLinea  = (i) => setForm(p => ({ ...p, lineas: p.lineas.filter((_, j) => j !== i) }));
  const cambiarLinea = (i, k, v) => setForm(p => ({ ...p, lineas: p.lineas.map((l, j) => j === i ? { ...l, [k]: v } : l) }));

  const guardar = async () => {
    const r = await fetch(`${API}/Modelos/`, { method: 'POST', headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) });
    const d = await r.json();
    if (d.ok) { setMsg({ tipo: "ok", texto: "Modelo guardado." }); setEdit(false); setForm({ codigo: '', descripcion: '', habilitado: true, tipo_asiento: '', lineas: [] }); const r2 = await fetch(`${API}/Modelos/`); setLista(await r2.json()); }
    else setMsg({ tipo: "error", texto: d.error || "Error." });
  };

  const eliminar = async (codigo) => {
    if (!window.confirm(`¿Eliminar modelo ${codigo}?`)) return;
    await fetch(`${API}/Modelos/${codigo}/`, { method: 'DELETE' });
    const r = await fetch(`${API}/Modelos/`); setLista(await r.json());
  };

  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ margin: 0, color: "#1e3a5f" }}>📋 Modelos de Asientos</h3>
        <Btn color="#7c3aed" onClick={() => setEdit(!edit)}>{edit ? "× Cancelar" : "+ Nuevo Modelo"}</Btn>
      </div>
      <Msg msg={msg} />

      {edit && (
        <div style={{ background: "#f8f5ff", border: "1px solid #c4b5fd", borderRadius: 8, padding: 16, marginBottom: 16 }}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 12 }}>
            <div style={{ flex: "1 1 100px" }}><Input label="Código" value={form.codigo} onChange={v => setForm(p => ({ ...p, codigo: v.toUpperCase() }))} required /></div>
            <div style={{ flex: "3 1 200px" }}><Input label="Descripción" value={form.descripcion} onChange={v => setForm(p => ({ ...p, descripcion: v }))} required /></div>
            <div style={{ flex: "1 1 150px" }}>
              <Select label="Tipo Asiento" value={form.tipo_asiento} onChange={v => setForm(p => ({ ...p, tipo_asiento: v }))}
                options={[{ value: '', label: '— ninguno —' }, ...tipos.map(t => ({ value: t.codigo, label: `${t.codigo} — ${t.descripcion}` }))]} />
            </div>
          </div>
          {/* Líneas */}
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "#555", marginBottom: 6 }}>LÍNEAS DEL MODELO</div>
            {form.lineas.map((l, i) => (
              <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6, alignItems: "center" }}>
                <select value={l.cuenta} onChange={e => cambiarLinea(i, 'cuenta', e.target.value)}
                  style={{ flex: 2, padding: "5px 8px", border: "1px solid #ccc", borderRadius: 5, fontSize: 12 }}>
                  <option value="">— cuenta —</option>
                  {cuentas.map(c => <option key={c.codigo} value={c.codigo}>{c.codigo} — {c.nombre}</option>)}
                </select>
                <select value={l.tipo} onChange={e => cambiarLinea(i, 'tipo', e.target.value)}
                  style={{ width: 80, padding: "5px 8px", border: "1px solid #ccc", borderRadius: 5, fontSize: 12 }}>
                  <option value="D">Debe</option>
                  <option value="H">Haber</option>
                </select>
                <input type="number" step="0.01" value={l.importe} onChange={e => cambiarLinea(i, 'importe', parseFloat(e.target.value) || 0)}
                  style={{ width: 100, padding: "5px 8px", border: "1px solid #ccc", borderRadius: 5, fontSize: 12 }} />
                <input placeholder="descripción" value={l.descripcion} onChange={e => cambiarLinea(i, 'descripcion', e.target.value)}
                  style={{ flex: 2, padding: "5px 8px", border: "1px solid #ccc", borderRadius: 5, fontSize: 12 }} />
                <button onClick={() => quitarLinea(i)} style={{ background: "none", border: "none", color: "#dc2626", cursor: "pointer", fontSize: 16 }}>✕</button>
              </div>
            ))}
            <button onClick={agregarLinea} style={{ fontSize: 12, color: "#7c3aed", background: "none", border: "1px dashed #c4b5fd", borderRadius: 5, padding: "4px 12px", cursor: "pointer" }}>+ Agregar línea</button>
          </div>
          <Btn onClick={guardar} color="#7c3aed">💾 Guardar Modelo</Btn>
        </div>
      )}

      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead><tr><Th>Código</Th><Th>Descripción</Th><Th>Tipo</Th><Th>Líneas</Th><Th>Acciones</Th></tr></thead>
        <tbody>
          {lista.length === 0 ? <tr><Td colSpan={5} style={{ textAlign: "center", color: "#888" }}>Sin modelos definidos</Td></tr>
          : lista.map(m => (
            <>
              <tr key={m.codigo} style={{ cursor: "pointer" }} onClick={() => setExpand(p => ({ ...p, [m.codigo]: !p[m.codigo] }))}>
                <Td bold>{m.codigo}</Td>
                <Td>{m.descripcion}</Td>
                <Td>{m.tipo_asiento || "—"}</Td>
                <Td>{m.lineas?.length || 0}</Td>
                <Td>
                  <Btn sm color="#dc2626" onClick={(e) => { e.stopPropagation(); eliminar(m.codigo); }}>Eliminar</Btn>
                </Td>
              </tr>
              {expandido[m.codigo] && m.lineas?.map((l, i) => (
                <tr key={i} style={{ background: "#faf5ff" }}>
                  <Td></Td><Td colSpan={2}><span style={{ marginLeft: 16, fontSize: 12 }}>{l.cuenta} — {l.nombre}</span></Td>
                  <Td><span style={{ fontSize: 12 }}>{l.tipo === 'D' ? 'Debe' : 'Haber'}: ${fmt(l.importe)}</span></Td>
                  <Td><span style={{ fontSize: 12, color: "#666" }}>{l.descripcion}</span></Td>
                </tr>
              ))}
            </>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: Asientos Automáticos
// ═══════════════════════════════════════════════════════════════════════════════
function PanelAsientosAutomaticos() {
  const [tipo,     setTipo]     = useState('apertura');
  const [fecha,    setFecha]    = useState(hoy());
  const [result,   setResult]   = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [cuentas,  setCuentas]  = useState([]);
  const [lineas,   setLineas]   = useState([{ cuenta: '', debe: 0, haber: 0, descripcion: '' }]);
  const [msg,      setMsg]      = useState(null);

  useEffect(() => {
    fetch(`${API}/PlanCuentas/?imputables=1`).then(r => r.json()).then(setCuentas).catch(() => {});
  }, []);

  const TIPOS = [
    { value: 'apertura',    label: '📂 Apertura' },
    { value: 'cierre',      label: '🔒 Cierre' },
    { value: 'inflacion',   label: '📈 Ajuste por Inflación' },
    { value: 'dif_cambio',  label: '💱 Diferencia de Cambio' },
    { value: 'refundicion', label: '🔄 Refundición de Resultados' },
  ];

  const necesitaLineas = ['inflacion', 'dif_cambio'].includes(tipo);

  const agregarLinea = () => setLineas(p => [...p, { cuenta: '', debe: 0, haber: 0, descripcion: '' }]);
  const quitarLinea  = (i) => setLineas(p => p.filter((_, j) => j !== i));
  const cambiarLinea = (i, k, v) => setLineas(p => p.map((l, j) => j === i ? { ...l, [k]: v } : l));

  const generar = async () => {
    if (!window.confirm(`¿Generar asiento de ${TIPOS.find(t => t.value === tipo)?.label}?`)) return;
    setLoading(true); setResult(null); setMsg(null);
    const payload = { tipo, fecha, usuario: 'admin', ...(necesitaLineas ? { lineas } : {}) };
    try {
      const r = await fetch(`${API}/AsientosAutomaticos/`, { method: 'POST', headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const d = await r.json();
      if (d.ok) { setResult(d); setMsg({ tipo: "ok", texto: `✅ Asiento #${d.id} generado correctamente` }); }
      else setMsg({ tipo: "error", texto: d.error || "Error al generar." });
    } catch (e) {
      setMsg({ tipo: "error", texto: "Error de conexión." });
    }
    setLoading(false);
  };

  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>⚙️ Generación de Asientos Automáticos</h3>

      <div style={{ background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 8, padding: 14, marginBottom: 16, fontSize: 13 }}>
        <strong>Tipos disponibles:</strong>
        <ul style={{ margin: "6px 0 0 0", paddingLeft: 18 }}>
          <li><b>Apertura:</b> genera asiento de apertura desde los saldos del ejercicio anterior</li>
          <li><b>Cierre:</b> refunde cuentas de resultado hacia Resultados No Asignados</li>
          <li><b>Ajuste por Inflación / Diferencia de Cambio:</b> requiere ingresar las líneas manualmente</li>
        </ul>
      </div>

      <Msg msg={msg} />

      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginBottom: 16 }}>
        <div style={{ flex: "1 1 200px" }}>
          <Select label="Tipo de Asiento" value={tipo} onChange={setTipo} options={TIPOS} />
        </div>
        <div style={{ flex: "1 1 150px" }}>
          <Input label="Fecha del Asiento" type="date" value={fecha} onChange={setFecha} required />
        </div>
      </div>

      {necesitaLineas && (
        <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 8, padding: 14, marginBottom: 16 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#555", marginBottom: 8 }}>LÍNEAS DEL ASIENTO</div>
          {lineas.map((l, i) => (
            <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6, alignItems: "center" }}>
              <select value={l.cuenta} onChange={e => cambiarLinea(i, 'cuenta', e.target.value)}
                style={{ flex: 3, padding: "5px 8px", border: "1px solid #ccc", borderRadius: 5, fontSize: 12 }}>
                <option value="">— seleccionar cuenta —</option>
                {cuentas.map(c => <option key={c.codigo} value={c.codigo}>{c.codigo} — {c.nombre}</option>)}
              </select>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 2 }}>
                <label style={{ fontSize: 11, color: "#888" }}>Debe</label>
                <input type="number" step="0.01" value={l.debe} onChange={e => cambiarLinea(i, 'debe', parseFloat(e.target.value) || 0)}
                  style={{ width: 100, padding: "4px 8px", border: "1px solid #ccc", borderRadius: 5, fontSize: 12, textAlign: "right" }} />
              </div>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 2 }}>
                <label style={{ fontSize: 11, color: "#888" }}>Haber</label>
                <input type="number" step="0.01" value={l.haber} onChange={e => cambiarLinea(i, 'haber', parseFloat(e.target.value) || 0)}
                  style={{ width: 100, padding: "4px 8px", border: "1px solid #ccc", borderRadius: 5, fontSize: 12, textAlign: "right" }} />
              </div>
              <input placeholder="descripción" value={l.descripcion} onChange={e => cambiarLinea(i, 'descripcion', e.target.value)}
                style={{ flex: 2, padding: "5px 8px", border: "1px solid #ccc", borderRadius: 5, fontSize: 12 }} />
              <button onClick={() => quitarLinea(i)} style={{ background: "none", border: "none", color: "#dc2626", cursor: "pointer" }}>✕</button>
            </div>
          ))}
          <button onClick={agregarLinea} style={{ fontSize: 12, color: "#2563eb", background: "none", border: "1px dashed #93c5fd", borderRadius: 5, padding: "4px 12px", cursor: "pointer" }}>+ Agregar línea</button>
        </div>
      )}

      <Btn onClick={generar} disabled={loading} color="#0f766e">
        {loading ? "Generando..." : `⚡ Generar ${TIPOS.find(t => t.value === tipo)?.label}`}
      </Btn>

      {result && (
        <div style={{ marginTop: 16, padding: 14, background: "#f0fdf4", border: "1px solid #86efac", borderRadius: 8, fontSize: 13 }}>
          <div style={{ fontWeight: 700, color: "#166534", marginBottom: 6 }}>Asiento #{result.id} generado</div>
          {result.lineas_generadas && <div>Líneas generadas: <b>{result.lineas_generadas}</b></div>}
          {result.resultado_neto !== undefined && (
            <div>Resultado del período: <b style={{ color: result.resultado_neto >= 0 ? "#065f46" : "#991b1b" }}>${fmt(result.resultado_neto)}</b></div>
          )}
        </div>
      )}
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: Ingreso Manual de Asientos (mejorado)
// ═══════════════════════════════════════════════════════════════════════════════
function PanelIngresoManual() {
  const [cuentas, setCuentas] = useState([]);
  const [tipos,   setTipos]   = useState([]);
  const [series,  setSeries]  = useState([]);
  const [form, setForm] = useState({
    fecha: hoy(), descripcion: '', tipo_asiento: '001', serie: 'DIA',
    estado: 'B', lineas: [
      { cuenta: '', debe: '0', haber: '0', descripcion: '' },
      { cuenta: '', debe: '0', haber: '0', descripcion: '' },
    ]
  });
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    fetch(`${API}/PlanCuentas/?imputables=1`).then(r => r.json()).then(setCuentas).catch(() => {});
    fetch(`${API}/TiposAsiento/`).then(r => r.json()).then(setTipos).catch(() => {});
    fetch(`${API}/Series/`).then(r => r.json()).then(setSeries).catch(() => {});
  }, []);

  const agregarLinea = () => setForm(p => ({ ...p, lineas: [...p.lineas, { cuenta: '', debe: '0', haber: '0', descripcion: '' }] }));
  const quitarLinea  = (i) => setForm(p => ({ ...p, lineas: p.lineas.filter((_, j) => j !== i) }));
  const cambiarLinea = (i, k, v) => setForm(p => ({ ...p, lineas: p.lineas.map((l, j) => j === i ? { ...l, [k]: v } : l) }));

  const td = form.lineas.reduce((s, l) => s + (parseFloat(l.debe)  || 0), 0);
  const th = form.lineas.reduce((s, l) => s + (parseFloat(l.haber) || 0), 0);
  const cuadra = Math.abs(td - th) < 0.02;

  const guardar = async () => {
    if (!cuadra) return setMsg({ tipo: "error", texto: `El asiento no cuadra: D=${td.toFixed(2)} H=${th.toFixed(2)}` });
    const payload = {
      ...form,
      lineas: form.lineas
        .filter(l => l.cuenta)
        .map(l => ({ cuenta: l.cuenta, debe: parseFloat(l.debe) || 0, haber: parseFloat(l.haber) || 0, descripcion: l.descripcion }))
    };
    const r = await fetch(`${API}/CrearAsiento/`, { method: 'POST', headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const d = await r.json();
    if (d.ok) {
      setMsg({ tipo: "ok", texto: `✅ Asiento #${d.id} creado correctamente.` });
      setForm({ fecha: hoy(), descripcion: '', tipo_asiento: '001', serie: 'DIA', estado: 'B', lineas: [{ cuenta: '', debe: '0', haber: '0', descripcion: '' }, { cuenta: '', debe: '0', haber: '0', descripcion: '' }] });
    } else {
      setMsg({ tipo: "error", texto: d.error || "Error al crear." });
    }
  };

  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>✍️ Ingreso Manual de Asientos</h3>
      <Msg msg={msg} />

      {/* Cabecera */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16 }}>
        <div style={{ flex: "1 1 140px" }}><Input label="Fecha" type="date" value={form.fecha} onChange={v => setForm(p => ({ ...p, fecha: v }))} required /></div>
        <div style={{ flex: "3 1 250px" }}><Input label="Concepto / Descripción" value={form.descripcion} onChange={v => setForm(p => ({ ...p, descripcion: v }))} required /></div>
        <div style={{ flex: "1 1 150px" }}>
          <Select label="Tipo de Asiento" value={form.tipo_asiento} onChange={v => setForm(p => ({ ...p, tipo_asiento: v }))}
            options={tipos.map(t => ({ value: t.codigo, label: `${t.codigo} — ${t.descripcion}` }))} />
        </div>
        <div style={{ flex: "1 1 120px" }}>
          <Select label="Serie" value={form.serie} onChange={v => setForm(p => ({ ...p, serie: v }))}
            options={series.map(s => ({ value: s.codigo, label: `${s.codigo} — ${s.descripcion}` }))} />
        </div>
        <div style={{ flex: "1 1 120px" }}>
          <Select label="Estado" value={form.estado} onChange={v => setForm(p => ({ ...p, estado: v }))}
            options={[{ value: 'B', label: 'Borrador' }, { value: 'L', label: 'Listo p/Mayorizar' }, { value: 'M', label: 'Mayorizado' }]} />
        </div>
      </div>

      {/* Tabla de líneas */}
      <div style={{ border: "1px solid #e2e8f0", borderRadius: 8, overflow: "hidden", marginBottom: 14 }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#f8f9fa" }}>
              <th style={{ padding: "8px 10px", textAlign: "left", fontSize: 12, fontWeight: 700, color: "#555" }}>Cuenta</th>
              <th style={{ padding: "8px 10px", textAlign: "right", fontSize: 12, fontWeight: 700, color: "#555", width: 110 }}>Debe</th>
              <th style={{ padding: "8px 10px", textAlign: "right", fontSize: 12, fontWeight: 700, color: "#555", width: 110 }}>Haber</th>
              <th style={{ padding: "8px 10px", fontSize: 12, fontWeight: 700, color: "#555" }}>Descripción</th>
              <th style={{ width: 32 }}></th>
            </tr>
          </thead>
          <tbody>
            {form.lineas.map((l, i) => (
              <tr key={i} style={{ borderTop: "1px solid #f0f0f0" }}>
                <td style={{ padding: "6px 8px" }}>
                  <select value={l.cuenta} onChange={e => cambiarLinea(i, 'cuenta', e.target.value)}
                    style={{ width: "100%", padding: "5px 8px", border: "1px solid #d0d7de", borderRadius: 5, fontSize: 12 }}>
                    <option value="">— seleccionar —</option>
                    {cuentas.map(c => <option key={c.codigo} value={c.codigo}>{c.codigo} — {c.nombre}</option>)}
                  </select>
                </td>
                <td style={{ padding: "6px 8px" }}>
                  <input type="number" step="0.01" value={l.debe} onChange={e => cambiarLinea(i, 'debe', e.target.value)}
                    style={{ width: "100%", padding: "5px 8px", border: "1px solid #d0d7de", borderRadius: 5, fontSize: 12, textAlign: "right" }} />
                </td>
                <td style={{ padding: "6px 8px" }}>
                  <input type="number" step="0.01" value={l.haber} onChange={e => cambiarLinea(i, 'haber', e.target.value)}
                    style={{ width: "100%", padding: "5px 8px", border: "1px solid #d0d7de", borderRadius: 5, fontSize: 12, textAlign: "right" }} />
                </td>
                <td style={{ padding: "6px 8px" }}>
                  <input value={l.descripcion} onChange={e => cambiarLinea(i, 'descripcion', e.target.value)}
                    style={{ width: "100%", padding: "5px 8px", border: "1px solid #d0d7de", borderRadius: 5, fontSize: 12 }} />
                </td>
                <td style={{ padding: "6px 8px", textAlign: "center" }}>
                  <button onClick={() => quitarLinea(i)} style={{ background: "none", border: "none", color: "#dc2626", cursor: "pointer", fontSize: 14 }}>✕</button>
                </td>
              </tr>
            ))}
            {/* Totales */}
            <tr style={{ background: "#f8f9fa", borderTop: "2px solid #dee2e6" }}>
              <td style={{ padding: "8px 10px", fontSize: 12, fontWeight: 700, color: "#555" }}>TOTALES</td>
              <td style={{ padding: "8px 10px", textAlign: "right", fontWeight: 700, color: "#1d4ed8", fontSize: 13 }}>{fmt(td)}</td>
              <td style={{ padding: "8px 10px", textAlign: "right", fontWeight: 700, color: "#065f46", fontSize: 13 }}>{fmt(th)}</td>
              <td colSpan={2} style={{ padding: "8px 10px" }}><Badge ok={cuadra} /></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <button onClick={agregarLinea} style={{ fontSize: 12, color: "#2563eb", background: "none", border: "1px dashed #93c5fd", borderRadius: 5, padding: "5px 14px", cursor: "pointer" }}>+ Agregar línea</button>
        <Btn onClick={guardar} disabled={!cuadra} color="#0f766e">💾 Guardar Asiento</Btn>
      </div>
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: Consulta de Saldos
// ═══════════════════════════════════════════════════════════════════════════════
function PanelConsultaSaldos() {
  const [desde,  setDesde]  = useState(primerDiaMes());
  const [hasta,  setHasta]  = useState(hoy());
  const [tipo,   setTipo]   = useState('');
  const [cuenta, setCuenta] = useState('');
  const [data,   setData]   = useState(null);
  const [loading, setLoading] = useState(false);

  const buscar = async () => {
    setLoading(true);
    const params = new URLSearchParams({ desde, hasta });
    if (tipo)   params.append('tipo', tipo);
    if (cuenta) params.append('cuenta', cuenta);
    const r = await fetch(`${API}/ConsultaSaldos/?${params}`);
    const d = await r.json();
    setData(d);
    setLoading(false);
  };

  const COLORES = { A: "#dbeafe", P: "#fce7f3", PN: "#d1fae5", I: "#fef9c3", E: "#fee2e2" };

  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>🔍 Consulta de Saldos</h3>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16, alignItems: "flex-end" }}>
        <Input label="Desde" type="date" value={desde} onChange={setDesde} />
        <Input label="Hasta" type="date" value={hasta} onChange={setHasta} />
        <div>
          <label style={{ fontSize: 13 }}>Tipos (A,P,PN,I,E)<br />
            <input value={tipo} onChange={e => setTipo(e.target.value)} placeholder="todos"
              style={{ padding: "7px 10px", border: "1px solid #ccc", borderRadius: 6, fontSize: 13 }} />
          </label>
        </div>
        <div>
          <label style={{ fontSize: 13 }}>Cuenta específica<br />
            <input value={cuenta} onChange={e => setCuenta(e.target.value)} placeholder="ej: 1.1.01.001"
              style={{ padding: "7px 10px", border: "1px solid #ccc", borderRadius: 6, fontSize: 13 }} />
          </label>
        </div>
        <div style={{ paddingTop: 20 }}>
          <Btn onClick={buscar} disabled={loading}>{loading ? "..." : "Consultar"}</Btn>
        </div>
      </div>

      {data && (
        <>
          <div style={{ fontSize: 12, color: "#666", marginBottom: 8 }}>{data.total} cuentas con movimientos</div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr><Th>Código</Th><Th>Cuenta</Th><Th>Tipo</Th><Th right>Suma Debe</Th><Th right>Suma Haber</Th><Th right>Saldo</Th></tr>
              </thead>
              <tbody>
                {data.filas?.map(f => (
                  <tr key={f.codigo}>
                    <Td><code style={{ fontSize: 12 }}>{f.codigo}</code></Td>
                    <Td>{f.nombre}</Td>
                    <Td>
                      <span style={{ background: COLORES[f.tipo] || "#f1f5f9", padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 600 }}>{f.tipo}</span>
                    </Td>
                    <Td right>{fmt(f.suma_debe)}</Td>
                    <Td right>{fmt(f.suma_haber)}</Td>
                    <Td right bold color={f.saldo < 0 ? "#dc2626" : f.saldo > 0 ? "#1d4ed8" : "#888"}>
                      {f.saldo < 0 ? "-" : ""}${fmt(Math.abs(f.saldo))}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: Importación de Asientos
// ═══════════════════════════════════════════════════════════════════════════════
function PanelImportacion() {
  const [json,   setJson]   = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg,    setMsg]    = useState(null);

  const ejemplo = JSON.stringify({
    asientos: [
      {
        fecha: hoy(), descripcion: "Asiento de ejemplo", tipo_asiento: "001", serie: "DIA",
        lineas: [
          { cuenta: "1.1.01.001", debe: 1000, haber: 0, descripcion: "Ingreso caja" },
          { cuenta: "4.1.01.001", debe: 0, haber: 1000, descripcion: "Venta" }
        ]
      }
    ]
  }, null, 2);

  const importar = async () => {
    let payload;
    try { payload = JSON.parse(json); } catch { setMsg({ tipo: "error", texto: "JSON inválido." }); return; }
    setLoading(true); setMsg(null); setResult(null);
    const r = await fetch(`${API}/ImportarAsientos/`, { method: 'POST', headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const d = await r.json();
    setResult(d);
    setMsg({ tipo: d.ok ? "ok" : "error", texto: d.ok ? `✅ ${d.importados} asientos importados` : `❌ ${d.importados} importados, ${d.errores?.length} errores` });
    setLoading(false);
  };

  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>📥 Importación de Asientos (JSON)</h3>
      <Msg msg={msg} />
      <div style={{ marginBottom: 10, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <label style={{ fontSize: 13, fontWeight: 600 }}>Pegar JSON con los asientos a importar:</label>
        <button onClick={() => setJson(ejemplo)} style={{ fontSize: 12, color: "#2563eb", background: "none", border: "1px solid #93c5fd", borderRadius: 5, padding: "3px 10px", cursor: "pointer" }}>Cargar ejemplo</button>
      </div>
      <textarea value={json} onChange={e => setJson(e.target.value)} rows={14}
        style={{ width: "100%", padding: "10px", fontFamily: "monospace", fontSize: 12, border: "1px solid #d0d7de", borderRadius: 8, boxSizing: "border-box", background: "#0f172a", color: "#e2e8f0" }}
        placeholder="Pegar JSON aquí..." />
      <div style={{ marginTop: 10 }}>
        <Btn onClick={importar} disabled={!json.trim() || loading} color="#0f766e">{loading ? "Importando..." : "📥 Importar Asientos"}</Btn>
      </div>
      {result && result.errores?.length > 0 && (
        <div style={{ marginTop: 12, padding: 12, background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 8, fontSize: 13 }}>
          <div style={{ fontWeight: 700, color: "#dc2626", marginBottom: 6 }}>Errores encontrados:</div>
          {result.errores.map((e, i) => <div key={i} style={{ color: "#b91c1c" }}>• {e}</div>)}
        </div>
      )}
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANELES EXISTENTES (sin cambios: Sincronizar, Libro Diario, Mayor,
//   Sumas y Saldos, Estado de Resultados, Balance General, Plan de Cuentas)
// Re-exportados directamente desde el módulo anterior para no duplicar código.
// ═══════════════════════════════════════════════════════════════════════════════

function PanelSincronizar() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const sincronizar = async () => {
    if (!window.confirm("¿Generar asientos para todas las operaciones sin asiento contable?")) return;
    setLoading(true);
    try { const r = await fetch(`${API}/Sincronizar/`, { method: "POST", headers: { "Content-Type": "application/json" } }); setResult(await r.json()); } catch { setResult({ error: "Error de conexión" }); }
    setLoading(false);
  };
  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>⚡ Sincronización de Asientos</h3>
      <p style={{ fontSize: 13, color: "#666", marginBottom: 20 }}>Genera automáticamente asientos para todas las ventas, compras y recibos que aún no tienen asiento contable. Seguro ejecutarlo múltiples veces.</p>
      <button onClick={sincronizar} disabled={loading} style={{ padding: "10px 28px", background: loading ? "#94a3b8" : "#0f766e", color: "#fff", border: "none", borderRadius: 8, cursor: loading ? "not-allowed" : "pointer", fontWeight: 700, fontSize: 14 }}>
        {loading ? "Procesando..." : "⚡ Sincronizar Ahora"}
      </button>
      {result && (
        <div style={{ marginTop: 20, padding: 16, background: result.error ? "#fef2f2" : "#f0fdf4", border: `1px solid ${result.error ? "#fca5a5" : "#86efac"}`, borderRadius: 8, fontSize: 13 }}>
          {result.error ? <span style={{ color: "#dc2626" }}>❌ {result.error}</span> : (
            <><div style={{ fontWeight: 700, color: "#166534", marginBottom: 8 }}>✓ {result.total} asientos generados</div>
            <div>Ventas: <strong>{result.generados?.ventas}</strong> | Compras: <strong>{result.generados?.compras}</strong> | Recibos: <strong>{result.generados?.recibos}</strong></div>
            {result.generados?.errores?.length > 0 && <div style={{ color: "#b45309", marginTop: 6 }}>Advertencias: {result.generados.errores.join(" | ")}</div>}</>
          )}
        </div>
      )}
    </Card>
  );
}

function PanelLibroDiario() {
  const [desde, setDesde] = useState(primerDiaMes());
  const [hasta, setHasta] = useState(hoy());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandido, setExpand] = useState({});
  const buscar = async () => { setLoading(true); try { const r = await fetch(`${API}/LibroDiario/?desde=${desde}&hasta=${hasta}`); setData(await r.json()); } catch {} setLoading(false); };
  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>📋 Libro Diario</h3>
      <FiltroFechas desde={desde} hasta={hasta} onDesde={setDesde} onHasta={setHasta} onBuscar={buscar} cargando={loading} />
      {data && (<>
        <div style={{ display: "flex", gap: 16, marginBottom: 16, flexWrap: "wrap" }}>
          {[{ label: "Total Debe", val: data.total_debe, color: "#1d4ed8" }, { label: "Total Haber", val: data.total_haber, color: "#065f46" }, { label: "Asientos", val: data.asientos?.length, color: "#7c3aed", nofmt: true }].map(x => (
            <div key={x.label} style={{ background: "#f8fafc", borderRadius: 8, padding: "10px 20px", textAlign: "center", flex: "1 1 140px" }}>
              <div style={{ fontSize: 11, color: "#888" }}>{x.label}</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: x.color }}>{x.nofmt ? x.val : `$${fmt(x.val)}`}</div>
            </div>
          ))}
          <div style={{ display: "flex", alignItems: "center" }}><Badge ok={data.cuadra} /></div>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead><tr><Th>#</Th><Th>Fecha</Th><Th>Descripción</Th><Th>Origen</Th><Th right>Debe</Th><Th right>Haber</Th><Th></Th></tr></thead>
            <tbody>
              {data.asientos?.map(a => (<>
                <tr key={a.id} style={{ cursor: "pointer", background: expandido[a.id] ? "#f0f9ff" : "" }} onClick={() => setExpand(p => ({ ...p, [a.id]: !p[a.id] }))}>
                  <Td>{a.id}</Td><Td>{a.fecha}</Td><Td>{a.descripcion}</Td>
                  <Td><span style={{ background: { VTA: "#dbeafe", CMP: "#fef9c3", REC: "#d1fae5", AJU: "#f3e8ff", ANU: "#fee2e2", APE: "#e0f2fe", CIE: "#fff7ed" }[a.origen] || "#f1f5f9", padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 600 }}>{a.origen}</span></Td>
                  <Td right bold>{fmt(a.lineas?.reduce((s, l) => s + l.debe, 0))}</Td>
                  <Td right bold>{fmt(a.lineas?.reduce((s, l) => s + l.haber, 0))}</Td>
                  <Td>{expandido[a.id] ? "▲" : "▼"}</Td>
                </tr>
                {expandido[a.id] && a.lineas?.map((l, i) => (
                  <tr key={i} style={{ background: "#f8fafc" }}>
                    <Td></Td><Td></Td>
                    <Td><span style={{ marginLeft: 24, color: "#555", fontSize: 12 }}>[{l.cuenta}] {l.nombre} {l.descripcion ? `— ${l.descripcion}` : ""}</span></Td>
                    <Td></Td>
                    <Td right>{l.debe > 0 ? fmt(l.debe) : ""}</Td>
                    <Td right>{l.haber > 0 ? fmt(l.haber) : ""}</Td>
                    <Td></Td>
                  </tr>
                ))}
              </>))}
            </tbody>
          </table>
        </div>
      </>)}
    </Card>
  );
}

function PanelMayorCuenta() {
  const [cuentas, setCuentas] = useState([]);
  const [cuenta, setCuenta] = useState("");
  const [desde, setDesde] = useState(primerDiaMes());
  const [hasta, setHasta] = useState(hoy());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => { fetch(`${API}/PlanCuentas/?imputables=1`).then(r => r.json()).then(setCuentas).catch(() => {}); }, []);
  const buscar = async () => { if (!cuenta) return alert("Seleccione una cuenta"); setLoading(true); try { const r = await fetch(`${API}/MayorCuenta/?cuenta=${cuenta}&desde=${desde}&hasta=${hasta}`); setData(await r.json()); } catch {} setLoading(false); };
  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>📖 Mayor de Cuentas</h3>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16, alignItems: "flex-end" }}>
        <label style={{ fontSize: 13, flex: "2 1 260px" }}>Cuenta<br />
          <select value={cuenta} onChange={e => setCuenta(e.target.value)} style={{ width: "100%", padding: "7px 10px", border: "1px solid #ccc", borderRadius: 6 }}>
            <option value="">— seleccionar —</option>
            {cuentas.map(c => <option key={c.codigo} value={c.codigo}>{c.codigo} — {c.nombre}</option>)}
          </select>
        </label>
        <Input label="Desde" type="date" value={desde} onChange={setDesde} />
        <Input label="Hasta" type="date" value={hasta} onChange={setHasta} />
        <div style={{ paddingTop: 20 }}><Btn onClick={buscar} disabled={loading}>{loading ? "..." : "Consultar"}</Btn></div>
      </div>
      {data && (<>
        <div style={{ marginBottom: 12, padding: "10px 16px", background: "#f0f9ff", borderRadius: 8 }}>
          <strong>{data.cuenta}</strong> — {data.nombre} &nbsp;| Saldo final: <strong style={{ color: "#1d4ed8" }}>${fmt(data.saldo_final)}</strong>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead><tr><Th>Fecha</Th><Th>#</Th><Th>Descripción</Th><Th>Origen</Th><Th right>Debe</Th><Th right>Haber</Th><Th right>Saldo</Th></tr></thead>
            <tbody>
              {data.movimientos?.map((m, i) => (
                <tr key={i}>
                  <Td>{m.fecha}</Td><Td>{m.asiento_id}</Td><Td>{m.descripcion}</Td>
                  <Td><span style={{ fontSize: 11 }}>{m.origen}</span></Td>
                  <Td right>{m.debe > 0 ? fmt(m.debe) : "-"}</Td>
                  <Td right>{m.haber > 0 ? fmt(m.haber) : "-"}</Td>
                  <Td right bold color={m.saldo < 0 ? "#dc2626" : "#1d4ed8"}>${fmt(m.saldo)}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </>)}
    </Card>
  );
}

function PanelBalanceSumasYSaldos() {
  const [desde, setDesde] = useState(primerDiaMes());
  const [hasta, setHasta] = useState(hoy());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const COLORES = { A: "#dbeafe", P: "#fce7f3", PN: "#d1fae5", I: "#fef9c3", E: "#fee2e2" };
  const buscar = async () => { setLoading(true); try { const r = await fetch(`${API}/BalanceSumasYSaldos/?desde=${desde}&hasta=${hasta}`); setData(await r.json()); } catch {} setLoading(false); };
  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>⚖ Balance de Sumas y Saldos</h3>
      <FiltroFechas desde={desde} hasta={hasta} onDesde={setDesde} onHasta={setHasta} onBuscar={buscar} cargando={loading} />
      {data && (<>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead><tr><Th>Código</Th><Th>Cuenta</Th><Th>Tipo</Th><Th right>Suma Debe</Th><Th right>Suma Haber</Th><Th right>Saldo Deudor</Th><Th right>Saldo Acreedor</Th></tr></thead>
            <tbody>
              {data.filas?.map(f => (
                <tr key={f.codigo}>
                  <Td>{f.codigo}</Td><Td>{f.nombre}</Td>
                  <Td><span style={{ background: COLORES[f.tipo] || "#f1f5f9", padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 600 }}>{f.tipo}</span></Td>
                  <Td right>{fmt(f.suma_debe)}</Td><Td right>{fmt(f.suma_haber)}</Td>
                  <Td right>{f.saldo_deudor > 0 ? fmt(f.saldo_deudor) : ""}</Td>
                  <Td right>{f.saldo_acreedor > 0 ? fmt(f.saldo_acreedor) : ""}</Td>
                </tr>
              ))}
              <tr style={{ background: "#f1f5f9", fontWeight: 700 }}>
                <Td colSpan={3} bold>TOTALES</Td>
                <Td right bold>{fmt(data.totales?.suma_debe)}</Td><Td right bold>{fmt(data.totales?.suma_haber)}</Td>
                <Td right bold>{fmt(data.totales?.saldo_deudor)}</Td><Td right bold>{fmt(data.totales?.saldo_acreedor)}</Td>
              </tr>
            </tbody>
          </table>
        </div>
        <div style={{ marginTop: 12 }}><Badge ok={data.cuadra} /></div>
      </>)}
    </Card>
  );
}

function PanelEstadoResultados() {
  const [desde, setDesde] = useState(primerDiaMes());
  const [hasta, setHasta] = useState(hoy());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const buscar = async () => { setLoading(true); try { const r = await fetch(`${API}/EstadoResultados/?desde=${desde}&hasta=${hasta}`); setData(await r.json()); } catch {} setLoading(false); };
  const Sec = ({ titulo, grupos, total, color }) => (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontWeight: 700, fontSize: 14, color: "#374151", marginBottom: 8, borderBottom: "2px solid #e5e7eb", paddingBottom: 4 }}>{titulo}</div>
      {grupos?.map((g, i) => (
        <div key={i} style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 12, color: "#6b7280", fontWeight: 600, marginBottom: 4 }}>{g.nombre}</div>
          {g.cuentas.map((c, j) => (
            <div key={j} style={{ display: "flex", justifyContent: "space-between", padding: "3px 16px", fontSize: 13 }}>
              <span style={{ color: "#4b5563" }}>{c.nombre}</span><span>${fmt(c.importe)}</span>
            </div>
          ))}
        </div>
      ))}
      <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderTop: "1px solid #e5e7eb", fontWeight: 700, fontSize: 14, color }}><span>Total {titulo}</span><span>${fmt(total)}</span></div>
    </div>
  );
  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>📊 Estado de Resultados</h3>
      <FiltroFechas desde={desde} hasta={hasta} onDesde={setDesde} onHasta={setHasta} onBuscar={buscar} cargando={loading} />
      {data && (
        <div style={{ maxWidth: 600 }}>
          <Sec titulo="Ingresos" grupos={data.ingresos?.grupos} total={data.ingresos?.total} color="#065f46" />
          <Sec titulo="Egresos" grupos={data.egresos?.grupos} total={data.egresos?.total} color="#991b1b" />
          <div style={{ background: data.resultado >= 0 ? "#d1fae5" : "#fee2e2", border: `2px solid ${data.resultado >= 0 ? "#6ee7b7" : "#fca5a5"}`, borderRadius: 10, padding: "14px 20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontWeight: 700, fontSize: 16 }}>{data.resultado >= 0 ? "✓ Resultado Positivo" : "✗ Resultado Negativo"}</span>
            <span style={{ fontWeight: 800, fontSize: 22, color: data.resultado >= 0 ? "#065f46" : "#991b1b" }}>${fmt(data.resultado)}</span>
          </div>
        </div>
      )}
    </Card>
  );
}

function PanelBalanceGeneral() {
  const [hasta, setHasta] = useState(hoy());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const buscar = async () => { setLoading(true); try { const r = await fetch(`${API}/BalanceGeneral/?hasta=${hasta}`); setData(await r.json()); } catch {} setLoading(false); };
  const Sec = ({ titulo, grupos, total, color }) => (
    <div style={{ flex: "1 1 260px" }}>
      <div style={{ fontWeight: 700, fontSize: 13, color: "#fff", background: color, padding: "8px 14px", borderRadius: "8px 8px 0 0" }}>{titulo}</div>
      <div style={{ border: `1px solid ${color}`, borderTop: "none", borderRadius: "0 0 8px 8px", overflow: "hidden" }}>
        {grupos?.map((g, i) => (
          <div key={i}>
            <div style={{ background: "#f8fafc", padding: "6px 12px", fontSize: 11, fontWeight: 700, color: "#6b7280", borderBottom: "1px solid #e5e7eb" }}>{g.nombre}</div>
            {g.cuentas.map((c, j) => (
              <div key={j} style={{ display: "flex", justifyContent: "space-between", padding: "5px 16px", fontSize: 12, borderBottom: "1px solid #f3f4f6" }}>
                <span>{c.nombre}</span><span>${fmt(c.saldo)}</span>
              </div>
            ))}
          </div>
        ))}
        <div style={{ display: "flex", justifyContent: "space-between", padding: "10px 14px", fontWeight: 700, fontSize: 14, background: "#f1f5f9", borderTop: `2px solid ${color}` }}>
          <span>TOTAL</span><span style={{ color }}>${fmt(total)}</span>
        </div>
      </div>
    </div>
  );
  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>🏛 Balance General</h3>
      <div style={{ display: "flex", gap: 10, alignItems: "flex-end", marginBottom: 20 }}>
        <Input label="Al cierre de" type="date" value={hasta} onChange={setHasta} />
        <div style={{ paddingTop: 20 }}><Btn onClick={buscar} disabled={loading}>{loading ? "..." : "Consultar"}</Btn></div>
      </div>
      {data && (<>
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 20 }}>
          <Sec titulo="ACTIVO" grupos={data.activo?.grupos} total={data.activo?.total} color="#1d4ed8" />
          <div style={{ flex: "1 1 260px", display: "flex", flexDirection: "column", gap: 16 }}>
            <Sec titulo="PASIVO" grupos={data.pasivo?.grupos} total={data.pasivo?.total} color="#b45309" />
            <div style={{ border: "1px solid #6d28d9", borderRadius: 8, overflow: "hidden" }}>
              <div style={{ background: "#6d28d9", color: "#fff", fontWeight: 700, fontSize: 13, padding: "8px 14px" }}>PATRIMONIO NETO</div>
              {data.patrimonio_neto?.grupos?.map((g, i) => (
                <div key={i}><div style={{ background: "#f8fafc", padding: "6px 12px", fontSize: 11, fontWeight: 700, color: "#6b7280" }}>{g.nombre}</div>
                  {g.cuentas.map((c, j) => <div key={j} style={{ display: "flex", justifyContent: "space-between", padding: "5px 16px", fontSize: 12 }}><span>{c.nombre}</span><span>${fmt(c.saldo)}</span></div>)}
                </div>
              ))}
              <div style={{ display: "flex", justifyContent: "space-between", padding: "5px 16px", fontSize: 12, background: "#faf5ff" }}>
                <span style={{ fontStyle: "italic" }}>Resultado del período</span>
                <span style={{ color: data.patrimonio_neto?.resultado_periodo >= 0 ? "#065f46" : "#991b1b" }}>${fmt(data.patrimonio_neto?.resultado_periodo)}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", padding: "10px 14px", fontWeight: 700, fontSize: 14, background: "#f1f5f9", borderTop: "2px solid #6d28d9" }}>
                <span>TOTAL</span><span style={{ color: "#6d28d9" }}>${fmt(data.patrimonio_neto?.total)}</span>
              </div>
            </div>
          </div>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 20px", borderRadius: 8, background: data.cuadra ? "#d1fae5" : "#fee2e2", border: `2px solid ${data.cuadra ? "#6ee7b7" : "#fca5a5"}` }}>
          <div>
            <div style={{ fontWeight: 700 }}>Activo: <span style={{ color: "#1d4ed8" }}>${fmt(data.activo?.total)}</span></div>
            <div style={{ fontSize: 12, color: "#555" }}>Pasivo + PN: ${fmt(data.total_pasivo_pn)}</div>
          </div>
          <Badge ok={data.cuadra} />
        </div>
      </>)}
    </Card>
  );
}

function PanelPlanCuentas() {
  const [cuentas, setCuentas] = useState([]);
  const [form, setForm] = useState({ codigo: "", nombre: "", tipo: "A", nivel: 4, padre: "", saldo_tipo: "D", es_imputable: true, activa: true, codigo_alt: "", col_impresion: 1 });
  const [editando, setEditando] = useState(false);
  const cargar = useCallback(() => { fetch(`${API}/PlanCuentas/`).then(r => r.json()).then(setCuentas).catch(() => {}); }, []);
  useEffect(() => { cargar(); }, [cargar]);
  const guardar = async () => {
    if (!form.codigo || !form.nombre) return alert("Código y nombre requeridos");
    await fetch(`${API}/GuardarCuenta/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) });
    setForm({ codigo: "", nombre: "", tipo: "A", nivel: 4, padre: "", saldo_tipo: "D", es_imputable: true, activa: true, codigo_alt: "", col_impresion: 1 });
    setEditando(false); cargar();
  };
  const COLORES = { A: "#dbeafe", P: "#fce7f3", PN: "#d1fae5", I: "#fef9c3", E: "#fee2e2" };
  const SANGRIA = { 1: 0, 2: 16, 3: 32, 4: 48 };
  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ margin: 0, color: "#1e3a5f" }}>📑 Plan de Cuentas</h3>
        <Btn color="#7c3aed" onClick={() => setEditando(!editando)}>{editando ? "× Cancelar" : "+ Nueva Cuenta"}</Btn>
      </div>
      {editando && (
        <div style={{ background: "#f8f5ff", border: "1px solid #c4b5fd", borderRadius: 8, padding: 16, marginBottom: 16 }}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {[{ label: "Código", key: "codigo", ph: "1.1.01.002" }, { label: "Nombre", key: "nombre", flex: 2, ph: "Banco BBVA" }, { label: "Padre", key: "padre", ph: "1.1.01" }, { label: "Cód. Alt.", key: "codigo_alt", ph: "" }].map(f => (
              <label key={f.key} style={{ fontSize: 13, flex: f.flex || "1 1 140px" }}>
                {f.label}<br />
                <input value={form[f.key]} placeholder={f.ph} onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
                  style={{ width: "100%", padding: "6px 10px", border: "1px solid #ccc", borderRadius: 6 }} />
              </label>
            ))}
            <div style={{ flex: "1 1 100px" }}>
              <Select label="Tipo" value={form.tipo} onChange={v => setForm(p => ({ ...p, tipo: v }))}
                options={[{ value: "A", label: "A — Activo" }, { value: "P", label: "P — Pasivo" }, { value: "PN", label: "PN — Patrimonio" }, { value: "I", label: "I — Ingreso" }, { value: "E", label: "E — Egreso" }]} />
            </div>
            <div style={{ flex: "1 1 80px" }}>
              <label style={{ fontSize: 13 }}>Nivel<br />
                <input type="number" min={1} max={4} value={form.nivel} onChange={e => setForm(p => ({ ...p, nivel: parseInt(e.target.value) }))}
                  style={{ width: "100%", padding: "6px 10px", border: "1px solid #ccc", borderRadius: 6 }} />
              </label>
            </div>
            <div style={{ flex: "1 1 100px" }}>
              <Select label="Saldo" value={form.saldo_tipo} onChange={v => setForm(p => ({ ...p, saldo_tipo: v }))}
                options={[{ value: "D", label: "Deudora" }, { value: "C", label: "Acreedora" }]} />
            </div>
            <div style={{ flex: "1 1 60px" }}>
              <label style={{ fontSize: 13 }}>Col. Bal.<br />
                <input type="number" min={1} max={2} value={form.col_impresion} onChange={e => setForm(p => ({ ...p, col_impresion: parseInt(e.target.value) }))}
                  style={{ width: "100%", padding: "6px 10px", border: "1px solid #ccc", borderRadius: 6 }} />
              </label>
            </div>
          </div>
          <div style={{ display: "flex", gap: 16, marginTop: 10, alignItems: "center" }}>
            <label style={{ fontSize: 13, display: "flex", gap: 6, alignItems: "center" }}>
              <input type="checkbox" checked={form.es_imputable} onChange={e => setForm(p => ({ ...p, es_imputable: e.target.checked }))} /> Es imputable
            </label>
            <Btn onClick={guardar} color="#7c3aed">Guardar</Btn>
          </div>
        </div>
      )}
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead><tr><Th>Código</Th><Th>Nombre</Th><Th>Tipo</Th><Th>Saldo</Th><Th>Imputable</Th><Th>Cód. Alt.</Th></tr></thead>
          <tbody>
            {cuentas.map(c => (
              <tr key={c.codigo} style={{ opacity: c.activa ? 1 : 0.45 }}>
                <Td><code style={{ paddingLeft: SANGRIA[c.nivel] || 0, fontSize: 12 }}>{c.codigo}</code></Td>
                <Td bold={c.nivel === 1}>{c.nombre}</Td>
                <Td><span style={{ background: COLORES[c.tipo] || "#f1f5f9", padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 600 }}>{c.tipo}</span></Td>
                <Td>{c.saldo_tipo === "D" ? "Deudora" : "Acreedora"}</Td>
                <Td>{c.es_imputable ? "✓" : ""}</Td>
                <Td>{c.codigo_alt || "—"}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MÓDULO PRINCIPAL
// ═══════════════════════════════════════════════════════════════════════════════
const MENU = [
  // Configuración
  { id: "ejercicios",   label: "📅 Ejercicios",            panel: PanelEjercicios,           grupo: "config" },
  { id: "tipos",        label: "🏷️ Tipos de Asiento",      panel: PanelTiposAsiento,          grupo: "config" },
  { id: "series",       label: "🔢 Series",                panel: PanelSeries,               grupo: "config" },
  { id: "modelos",      label: "📋 Modelos de Asientos",   panel: PanelModelos,              grupo: "config" },
  { id: "plan",         label: "📑 Plan de Cuentas",       panel: PanelPlanCuentas,          grupo: "config" },
  // Operaciones
  { id: "sincronizar",  label: "⚡ Sincronizar",           panel: PanelSincronizar,           grupo: "op" },
  { id: "manual",       label: "✍️ Ingreso Manual",        panel: PanelIngresoManual,         grupo: "op" },
  { id: "automatico",   label: "⚙️ Asientos Automáticos", panel: PanelAsientosAutomaticos,   grupo: "op" },
  { id: "importar",     label: "📥 Importación",           panel: PanelImportacion,           grupo: "op" },
  // Consultas e Informes
  { id: "saldos",       label: "🔍 Consulta de Saldos",   panel: PanelConsultaSaldos,        grupo: "info" },
  { id: "diario",       label: "📋 Libro Diario",          panel: PanelLibroDiario,           grupo: "info" },
  { id: "mayor",        label: "📖 Mayor de Cuentas",      panel: PanelMayorCuenta,           grupo: "info" },
  { id: "sumasaldos",   label: "⚖ Sumas y Saldos",         panel: PanelBalanceSumasYSaldos,   grupo: "info" },
  { id: "resultados",   label: "📊 Estado de Resultados",  panel: PanelEstadoResultados,      grupo: "info" },
  { id: "balance",      label: "🏛 Balance General",        panel: PanelBalanceGeneral,        grupo: "info" },
];

const GRUPOS = [
  { id: "config", label: "⚙️ CONFIGURACIÓN" },
  { id: "op",     label: "📝 OPERACIONES" },
  { id: "info",   label: "📊 CONSULTAS E INFORMES" },
];

export default function ModuloContabilidad() {
  const [activo, setActivo] = useState("sincronizar");
  const PanelActivo = MENU.find(m => m.id === activo)?.panel || PanelSincronizar;

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#f0f4f8" }}>
      {/* Sidebar */}
      <div style={{ width: 230, background: "#1e3a5f", color: "#fff", padding: "16px 0", flexShrink: 0, overflowY: "auto" }}>
        <div style={{ padding: "0 16px 16px", borderBottom: "1px solid rgba(255,255,255,.15)" }}>
          <div style={{ fontSize: 10, letterSpacing: 1, opacity: .5, marginBottom: 2 }}>MÓDULO</div>
          <div style={{ fontWeight: 700, fontSize: 15 }}>🏛 Contabilidad</div>
        </div>
        {GRUPOS.map(g => (
          <div key={g.id}>
            <div style={{ padding: "12px 16px 4px", fontSize: 10, fontWeight: 700, opacity: .5, letterSpacing: 1 }}>{g.label}</div>
            {MENU.filter(m => m.grupo === g.id).map(m => (
              <button key={m.id} onClick={() => setActivo(m.id)} style={{
                display: "block", width: "100%", textAlign: "left",
                padding: "9px 16px", border: "none", cursor: "pointer",
                background: activo === m.id ? "rgba(255,255,255,.15)" : "transparent",
                color: activo === m.id ? "#fff" : "rgba(255,255,255,.65)",
                fontWeight: activo === m.id ? 700 : 400, fontSize: 12,
                borderLeft: activo === m.id ? "3px solid #60a5fa" : "3px solid transparent",
              }}>
                {m.label}
              </button>
            ))}
          </div>
        ))}
      </div>

      {/* Contenido */}
      <div style={{ flex: 1, padding: 24, overflowY: "auto" }}>
        <PanelActivo />
      </div>
    </div>
  );
}