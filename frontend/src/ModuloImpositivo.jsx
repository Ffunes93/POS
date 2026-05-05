/**
 * ModuloImpositivo.jsx — Módulo Informes Impositivos
 * Migración de Bejerman Web → React
 *
 * Submódulos:
 *  - Libro IVA Ventas / Compras
 *  - Libro IVA Digital (TXT)
 *  - Declaraciones Juradas
 *  - Análisis de Operaciones
 *  - Exportaciones (SICORE, SIFERE, Genérico)
 *  - Monotributistas (PDV, Rankings)
 */
import { useState, useEffect, useCallback } from 'react';
import * as XLSX from 'xlsx';
const API = `${import.meta.env.VITE_API_URL}/api/impositivo`;
const API_MAIN = import.meta.env.VITE_API_URL || `${import.meta.env.VITE_API_URL}`;

// ── UI helpers ────────────────────────────────────────────────────────────────
const fmt = (n) => Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const hoy = () => new Date().toISOString().slice(0, 10);
const primerDiaMes = () => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
};
const periodoActual = () => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
};

const s = {
    card: { background: '#fff', borderRadius: 10, boxShadow: '0 1px 4px rgba(0,0,0,.10)', padding: 20, marginBottom: 16 },
    th: { background: '#f8f9fa', padding: '8px 12px', textAlign: 'left', fontSize: 12, fontWeight: 700, color: '#555', borderBottom: '2px solid #dee2e6' },
    td: { padding: '7px 12px', fontSize: 13, borderBottom: '1px solid #f0f0f0' },
    tdr: { padding: '7px 12px', fontSize: 13, textAlign: 'right', borderBottom: '1px solid #f0f0f0' },
    label: { display: 'block', fontSize: 12, fontWeight: 700, color: '#555', marginBottom: 3 },
    input: { width: '100%', padding: '7px 10px', border: '1px solid #ccc', borderRadius: 6, fontSize: 13, boxSizing: 'border-box' },
    select: { width: '100%', padding: '7px 10px', border: '1px solid #ccc', borderRadius: 6, fontSize: 13, boxSizing: 'border-box' },
};

const Btn = ({ children, onClick, color = '#2563eb', secondary, disabled, sm }) => (
    <button onClick={onClick} disabled={disabled} style={{
        padding: sm ? '4px 12px' : '7px 18px',
        background: secondary ? '#fff' : (disabled ? '#94a3b8' : color),
        color: secondary ? color : '#fff',
        border: `1px solid ${disabled ? '#94a3b8' : color}`,
        borderRadius: 6, cursor: disabled ? 'not-allowed' : 'pointer',
        fontWeight: 600, fontSize: sm ? 12 : 13, whiteSpace: 'nowrap',
    }}>{children}</button>
);

const Msg = ({ msg }) => {
    if (!msg) return null;
    const ok = msg.tipo === 'ok';
    return (
        <div style={{
            padding: '10px 16px', borderRadius: 6, marginBottom: 14, fontSize: 13, fontWeight: 600,
            background: ok ? '#d1fae5' : '#fee2e2', color: ok ? '#065f46' : '#991b1b',
            border: `1px solid ${ok ? '#6ee7b7' : '#fca5a5'}`,
        }}>{msg.texto}</div>
    );
};

const Campo = ({ label, children, flex = '1 1 180px' }) => (
    <div style={{ flex }}>
        <label style={s.label}>{label}</label>
        {children}
    </div>
);

const Badge = ({ texto, color = '#3b82f6' }) => (
    <span style={{ background: color + '20', color, border: `1px solid ${color}50`, padding: '2px 10px', borderRadius: 12, fontSize: 11, fontWeight: 700 }}>
        {texto}
    </span>
);

// Descarga base64 como archivo
const descargar = (nombre, b64) => {
    const bytes = atob(b64);
    const arr = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
    const blob = new Blob([arr], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = nombre; a.click();
    URL.revokeObjectURL(url);
};

const exportarExcel = (rows, nombre) => {
    const ws = XLSX.utils.json_to_sheet(rows);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Datos');
    XLSX.writeFile(wb, `${nombre}.xlsx`);
};


// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: LIBRO IVA VENTAS / COMPRAS
// ═══════════════════════════════════════════════════════════════════════════════
function PanelLibroIVA({ circuito = 'V' }) {
    const titulo = circuito === 'V' ? '📗 Libro IVA Ventas' : '📕 Libro IVA Compras';
    const hoy = new Date().toISOString().split('T')[0];
    const primer = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0];

    const [desde, setDesde] = useState(primer);
    const [hasta, setHasta] = useState(hoy);
    const [datos, setDatos] = useState(null);
    const [cargando, setCargando] = useState(false);
    const [msg, setMsg] = useState(null);

    const consultar = async () => {
        setCargando(true); setMsg(null); setDatos(null);
        const url = circuito === 'V'
            ? `${API_MAIN}/api/InformeLibroIVAVentas/?desde=${desde}&hasta=${hasta}`
            : `${API_MAIN}/api/InformeEgresos/?desde=${desde}&hasta=${hasta}`;

        const r = await fetch(url);
        const d = await r.json();
        if (d.status === 'success') {
            setDatos(d);
        } else {
            setMsg({ tipo: 'error', texto: d.mensaje || 'Error al obtener datos.' });
        }
        setCargando(false);
    };

    return (
        <div style={s.card}>
            <h3 style={{ marginTop: 0, color: '#1e3a5f' }}>{titulo}</h3>
            <Msg msg={msg} />

            {/* Filtros */}
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: 16 }}>
                <Campo label='Fecha desde'>
                    <input type='date' style={s.input} value={desde}
                        onChange={e => setDesde(e.target.value)} />
                </Campo>
                <Campo label='Fecha hasta'>
                    <input type='date' style={s.input} value={hasta}
                        onChange={e => setHasta(e.target.value)} />
                </Campo>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
                    <Btn onClick={consultar} disabled={cargando} color='#0f766e'>
                        {cargando ? 'Consultando...' : '📊 Generar Libro'}
                    </Btn>
                    {datos && (
                        <Btn
                            color='#059669'
                            onClick={() => exportarExcel(
                                datos.comprobantes?.map(c => ({
                                    Fecha: new Date(c.fecha_fact || c.fecha_comprob).toLocaleDateString('es-AR'),
                                    Tipo: `${c.cod_comprob}${c.comprobante_letra || ''}`,
                                    'Pto/Nro': `${c.comprobante_pto_vta}-${String(c.nro_comprob || 0).padStart(8, '0')}`,
                                    [circuito === 'V' ? 'Cliente' : 'Proveedor']: c.denominacion || c.nom_proveedor || '',
                                    Neto: parseFloat(c.neto || 0),
                                    IVA: parseFloat(c.iva_1 || 0),
                                    Total: parseFloat(c.tot_general || 0),
                                })),
                                `LibroIVA_${circuito === 'V' ? 'Ventas' : 'Compras'}_${desde}_${hasta}`
                            )}
                        >
                            📥 Exportar Excel
                        </Btn>
                    )}
                </div>

            </div>

            {/* Totales */}
            {datos && (
                <>
                    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
                        {[
                            { label: 'Neto', val: datos.totales?.suma_neto },
                            { label: 'IVA', val: datos.totales?.suma_iva },
                            { label: 'Total', val: datos.totales?.suma_total },
                        ].map(({ label, val }) => (
                            <div key={label} style={{ background: '#f0f9ff', borderRadius: 8, padding: '10px 20px', flex: '1 1 120px', textAlign: 'center', border: '1px solid #bae6fd' }}>
                                <div style={{ fontSize: 11, color: '#888' }}>{label}</div>
                                <div style={{ fontSize: 18, fontWeight: 700, color: '#0369a1' }}>${fmt(val)}</div>
                            </div>
                        ))}
                        <div style={{ background: '#f5f3ff', borderRadius: 8, padding: '10px 20px', flex: '1 1 100px', textAlign: 'center', border: '1px solid #ddd6fe' }}>
                            <div style={{ fontSize: 11, color: '#888' }}>Comprobantes</div>
                            <div style={{ fontSize: 18, fontWeight: 700, color: '#7c3aed' }}>{datos.comprobantes?.length || 0}</div>
                        </div>
                    </div>

                    {/* Tabla */}
                    <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr>
                                    <th style={s.th}>Fecha</th>
                                    <th style={s.th}>Tipo</th>
                                    <th style={s.th}>Pto/Nro</th>
                                    <th style={s.th}>{circuito === 'V' ? 'Cliente' : 'Proveedor'}</th>
                                    <th style={{ ...s.th, textAlign: 'right' }}>Neto</th>
                                    <th style={{ ...s.th, textAlign: 'right' }}>IVA</th>
                                    <th style={{ ...s.th, textAlign: 'right' }}>Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {datos.comprobantes?.length === 0 && (
                                    <tr><td colSpan={7} style={{ ...s.td, textAlign: 'center', color: '#888' }}>Sin comprobantes para el período</td></tr>
                                )}
                                {datos.comprobantes?.map((c, i) => (
                                    <tr key={i}>
                                        <td style={s.td}>
                                            {new Date(c.fecha_fact || c.fecha_comprob).toLocaleDateString('es-AR')}
                                        </td>
                                        <td style={s.td}>{c.cod_comprob}{c.comprobante_letra || ''}</td>
                                        <td style={s.td}>{c.comprobante_pto_vta}-{String(c.nro_comprob || 0).padStart(8, '0')}</td>
                                        <td style={s.td}>{c.denominacion || c.nom_proveedor || '—'}</td>
                                        <td style={s.tdr}>${fmt(c.neto)}</td>
                                        <td style={s.tdr}>${fmt(c.iva_1)}</td>
                                        <td style={{ ...s.tdr, fontWeight: 700 }}>${fmt(c.tot_general)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: LIBRO IVA DIGITAL
// ═══════════════════════════════════════════════════════════════════════════════
function PanelIVADigital() {
    const [form, setForm] = useState({ periodo: periodoActual(), circuito: 'V', prorratea: false });
    const [resultado, setResult] = useState(null);
    const [cargando, setCargando] = useState(false);
    const [msg, setMsg] = useState(null);

    const generar = async () => {
        setCargando(true); setMsg(null); setResult(null);
        const r = await fetch(`${API}/iva-digital/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(form),
        });
        const d = await r.json();
        if (d.status === 'success') {
            setResult(d);
            setMsg({ tipo: 'ok', texto: `Archivo generado: ${d.registros} registros.` });
        } else {
            setMsg({ tipo: 'error', texto: d.mensaje });
        }
        setCargando(false);
    };

    return (
        <div style={s.card}>
            <h3 style={{ marginTop: 0, color: '#1e3a5f' }}>💾 Libro IVA Digital</h3>
            <p style={{ color: '#666', fontSize: 13, marginBottom: 16 }}>
                Genera el archivo .TXT para presentar al sistema IVA Digital de AFIP.
                <strong style={{ color: '#b45309' }}> ⚠️ Nota: el prorrateo por comprobante no está disponible en esta versión.</strong>
            </p>

            <Msg msg={msg} />

            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
                <Campo label='Período (YYYY-MM) *' flex='1 1 150px'>
                    <input style={s.input} value={form.periodo} placeholder='2026-05'
                        onChange={e => setForm(p => ({ ...p, periodo: e.target.value }))} />
                </Campo>
                <Campo label='Circuito' flex='1 1 150px'>
                    <select style={s.select} value={form.circuito} onChange={e => setForm(p => ({ ...p, circuito: e.target.value }))}>
                        <option value='V'>Ventas</option>
                        <option value='C'>Compras</option>
                    </select>
                </Campo>
                <Campo label='Prorrateo crédito fiscal' flex='1 1 180px'>
                    <div style={{ display: 'flex', gap: 16, paddingTop: 8 }}>
                        <label style={{ display: 'flex', gap: 6, alignItems: 'center', fontSize: 13 }}>
                            <input type='radio' checked={!form.prorratea} onChange={() => setForm(p => ({ ...p, prorratea: false }))} /> No prorrata
                        </label>
                        <label style={{ display: 'flex', gap: 6, alignItems: 'center', fontSize: 13 }}>
                            <input type='radio' checked={form.prorratea} onChange={() => setForm(p => ({ ...p, prorratea: true }))} /> Prorrata Global
                        </label>
                    </div>
                </Campo>
            </div>

            <div style={{ display: 'flex', gap: 10 }}>
                <Btn onClick={generar} disabled={cargando || !form.periodo} color='#0f766e'>
                    {cargando ? 'Generando...' : '⚡ Generar TXT'}
                </Btn>
                {resultado && (
                    <Btn color='#1d4ed8' onClick={() => descargar(resultado.nombre, resultado.contenido_b64)}>
                        ⬇ Descargar {resultado.nombre}
                    </Btn>
                )}
            </div>

            {resultado && (
                <div style={{ marginTop: 16, padding: 14, background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 8, fontSize: 13 }}>
                    <div style={{ fontWeight: 700, color: '#166534', marginBottom: 6 }}>✓ Archivo listo</div>
                    <div>Nombre: <b>{resultado.nombre}</b></div>
                    <div>Registros: <b>{resultado.registros}</b></div>
                    <div>Período: <b>{resultado.periodo}</b></div>
                </div>
            )}
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: DECLARACIONES JURADAS
// ═══════════════════════════════════════════════════════════════════════════════
function PanelDDJJ() {
    const [lista, setLista] = useState([]);
    const [form, setForm] = useState({ periodo: periodoActual(), version: 'V2', tipo_emision: 'O' });
    const [editando, setEditando] = useState(false);
    const [msg, setMsg] = useState(null);
    const [cargando, setCargando] = useState(false);

    const cargar = useCallback(async () => {
        const r = await fetch(`${API}/ddjj/`);
        const d = await r.json();
        if (d.status === 'success') setLista(d.data);
    }, []);

    useEffect(() => { cargar(); }, [cargar]);

    const emitir = async () => {
        setCargando(true); setMsg(null);
        const r = await fetch(`${API}/ddjj/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...form, usuario: 'admin' }),
        });
        const d = await r.json();
        if (d.status === 'success') {
            setMsg({ tipo: 'ok', texto: `${d.mensaje} | Débito: $${fmt(d.debito_fiscal)} | Crédito: $${fmt(d.credito_fiscal)} | Saldo: $${fmt(d.saldo_a_pagar)}` });
            setEditando(false);
            cargar();
        } else {
            setMsg({ tipo: 'error', texto: d.mensaje });
        }
        setCargando(false);
    };

    const rectificar = async (id) => {
        if (!window.confirm('¿Crear rectificativa de esta DDJJ?')) return;
        const r = await fetch(`${API}/ddjj/${id}/rectificar/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ usuario: 'admin' }),
        });
        const d = await r.json();
        if (d.status === 'success') { setMsg({ tipo: 'ok', texto: d.mensaje }); cargar(); }
        else setMsg({ tipo: 'error', texto: d.mensaje });
    };

    const marcarCG = async (id) => {
        const r = await fetch(`${API}/ddjj/${id}/pasar-cg/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        const d = await r.json();
        if (d.status === 'success') cargar();
    };

    const VERSION_LABELS = { V1: 'R.C. 3685', V2: 'IVA Estándar' };
    const EMISION_LABELS = { O: 'Original', R1: 'Rect. 1', R2: 'Rect. 2', R3: 'Rect. 3' };
    const EMISION_COLORS = { O: '#059669', R1: '#d97706', R2: '#dc2626', R3: '#7c3aed' };

    return (
        <div style={s.card}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ margin: 0, color: '#1e3a5f' }}>📋 Declaraciones Juradas Mensuales IVA</h3>
                <Btn onClick={() => setEditando(!editando)} color='#7c3aed'>
                    {editando ? '× Cancelar' : '+ Emitir DDJJ'}
                </Btn>
            </div>

            <Msg msg={msg} />

            {editando && (
                <div style={{ background: '#faf5ff', border: '1px solid #c4b5fd', borderRadius: 8, padding: 16, marginBottom: 16 }}>
                    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                        <Campo label='Período (YYYY-MM) *' flex='1 1 150px'>
                            <input style={s.input} value={form.periodo} placeholder='2026-05'
                                onChange={e => setForm(p => ({ ...p, periodo: e.target.value }))} />
                        </Campo>
                        <Campo label='Versión'>
                            <select style={s.select} value={form.version} onChange={e => setForm(p => ({ ...p, version: e.target.value }))}>
                                <option value='V2'>IVA Estándar (V2)</option>
                                <option value='V1'>R.C. 3685 (V1)</option>
                            </select>
                        </Campo>
                        <Campo label='Tipo de Emisión'>
                            <select style={s.select} value={form.tipo_emision} onChange={e => setForm(p => ({ ...p, tipo_emision: e.target.value }))}>
                                <option value='O'>Original</option>
                                <option value='R1'>Rectificativa N° 1</option>
                                <option value='R2'>Rectificativa N° 2</option>
                                <option value='R3'>Rectificativa N° 3</option>
                            </select>
                        </Campo>
                        <div style={{ paddingTop: 20 }}>
                            <Btn onClick={emitir} disabled={cargando} color='#7c3aed'>
                                {cargando ? 'Calculando...' : '📊 Calcular y Emitir'}
                            </Btn>
                        </div>
                    </div>
                </div>
            )}

            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                    <tr>
                        <th style={s.th}>Período</th>
                        <th style={s.th}>Versión</th>
                        <th style={s.th}>Emisión</th>
                        <th style={{ ...s.th, textAlign: 'right' }}>Débito Fiscal</th>
                        <th style={{ ...s.th, textAlign: 'right' }}>Crédito Fiscal</th>
                        <th style={{ ...s.th, textAlign: 'right' }}>Saldo a Pagar</th>
                        <th style={s.th}>Pasado CG</th>
                        <th style={s.th}>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {lista.length === 0
                        ? <tr><td colSpan={8} style={{ ...s.td, textAlign: 'center', color: '#888' }}>Sin declaraciones emitidas</td></tr>
                        : lista.map(dj => (
                            <tr key={dj.id}>
                                <td style={{ ...s.td, fontWeight: 700 }}>{new Date(dj.periodo + 'T12:00').toLocaleDateString('es-AR', { month: '2-digit', year: 'numeric' })}</td>
                                <td style={s.td}><Badge texto={VERSION_LABELS[dj.version] || dj.version} color='#0284c7' /></td>
                                <td style={s.td}><Badge texto={EMISION_LABELS[dj.tipo_emision] || dj.tipo_emision} color={EMISION_COLORS[dj.tipo_emision] || '#888'} /></td>
                                <td style={s.tdr}>${fmt(dj.total_debito_fiscal)}</td>
                                <td style={s.tdr}>${fmt(dj.total_credito_fiscal)}</td>
                                <td style={{ ...s.tdr, fontWeight: 700, color: dj.saldo_a_pagar > 0 ? '#dc2626' : '#059669' }}>
                                    ${fmt(dj.saldo_a_pagar)}
                                </td>
                                <td style={s.td}>
                                    {dj.pasado_cg
                                        ? <Badge texto='✓ Sí' color='#059669' />
                                        : <button onClick={() => marcarCG(dj.id)} style={{ fontSize: 11, color: '#0284c7', background: 'none', border: '1px solid #0284c7', borderRadius: 4, padding: '2px 8px', cursor: 'pointer' }}>Marcar</button>
                                    }
                                </td>
                                <td style={s.td}>
                                    <Btn sm color='#7c3aed' onClick={() => rectificar(dj.id)}>Rectificar</Btn>
                                </td>
                            </tr>
                        ))}
                </tbody>
            </table>
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: ANÁLISIS DE OPERACIONES
// ═══════════════════════════════════════════════════════════════════════════════
function PanelAnalisisOp() {
    const [form, setForm] = useState({ circuito: 'V', periodo_desde: periodoActual(), periodo_hasta: periodoActual(), formato: 'R' });
    const [datos, setDatos] = useState(null);
    const [cargando, setCargando] = useState(false);
    const [msg, setMsg] = useState(null);

    const consultar = async () => {
        setCargando(true); setMsg(null); setDatos(null);
        const r = await fetch(`${API}/analisis-operaciones/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(form),
        });
        const d = await r.json();
        if (d.status === 'success') setDatos(d);
        else setMsg({ tipo: 'error', texto: d.mensaje });
        setCargando(false);
    };

    return (
        <div style={s.card}>
            <h3 style={{ marginTop: 0, color: '#1e3a5f' }}>🔍 Análisis de Operaciones</h3>
            <Msg msg={msg} />

            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16, alignItems: 'flex-end' }}>
                <Campo label='Circuito' flex='1 1 150px'>
                    <select style={s.select} value={form.circuito} onChange={e => setForm(p => ({ ...p, circuito: e.target.value }))}>
                        <option value='V'>Ventas</option>
                        <option value='C'>Compras</option>
                    </select>
                </Campo>
                <Campo label='Período DDJJ Desde *' flex='1 1 150px'>
                    <input style={s.input} value={form.periodo_desde} placeholder='YYYY-MM'
                        onChange={e => setForm(p => ({ ...p, periodo_desde: e.target.value }))} />
                </Campo>
                <Campo label='Período DDJJ Hasta *' flex='1 1 150px'>
                    <input style={s.input} value={form.periodo_hasta} placeholder='YYYY-MM'
                        onChange={e => setForm(p => ({ ...p, periodo_hasta: e.target.value }))} />
                </Campo>
                <Campo label='Formato' flex='1 1 150px'>
                    <select style={s.select} value={form.formato} onChange={e => setForm(p => ({ ...p, formato: e.target.value }))}>
                        <option value='R'>Resumido</option>
                        <option value='D'>Detallado</option>
                    </select>
                </Campo>
                <div style={{ paddingTop: 20 }}>
                    <Btn onClick={consultar} disabled={cargando}>
                        {cargando ? 'Consultando...' : '🔍 Consultar'}
                    </Btn>
                </div>
            </div>

            {datos && (
                <>
                    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
                        {[
                            { label: 'Neto', val: datos.totales?.suma_neto },
                            { label: 'IVA', val: datos.totales?.suma_iva },
                            { label: 'Total', val: datos.totales?.suma_total },
                        ].map(({ label, val }) => (
                            <div key={label} style={{ background: '#f0f9ff', borderRadius: 8, padding: '10px 20px', flex: '1 1 120px', textAlign: 'center', border: '1px solid #bae6fd' }}>
                                <div style={{ fontSize: 11, color: '#888' }}>{label}</div>
                                <div style={{ fontSize: 18, fontWeight: 700, color: '#0369a1' }}>${fmt(val)}</div>
                            </div>
                        ))}
                        <div style={{ background: '#f5f3ff', borderRadius: 8, padding: '10px 20px', flex: '1 1 100px', textAlign: 'center', border: '1px solid #ddd6fe' }}>
                            <div style={{ fontSize: 11, color: '#888' }}>Registros</div>
                            <div style={{ fontSize: 18, fontWeight: 700, color: '#7c3aed' }}>{datos.cantidad}</div>
                        </div>
                    </div>

                    <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr>
                                    {form.formato === 'R' ? (
                                        <><th style={s.th}>Tipo</th><th style={{ ...s.th, textAlign: 'right' }}>Cantidad</th><th style={{ ...s.th, textAlign: 'right' }}>Neto</th><th style={{ ...s.th, textAlign: 'right' }}>IVA</th><th style={{ ...s.th, textAlign: 'right' }}>Total</th></>
                                    ) : (
                                        <><th style={s.th}>Fecha</th><th style={s.th}>Tipo</th><th style={s.th}>Nro</th><th style={{ ...s.th, textAlign: 'right' }}>Neto</th><th style={{ ...s.th, textAlign: 'right' }}>IVA</th><th style={{ ...s.th, textAlign: 'right' }}>Total</th></>
                                    )}
                                </tr>
                            </thead>
                            <tbody>
                                {datos.data?.map((row, i) =>
                                    form.formato === 'R' ? (
                                        <tr key={i}>
                                            <td style={s.td}>{row.cod_comprob}{row.comprobante_letra || ''}</td>
                                            <td style={s.tdr}>{row.cantidad}</td>
                                            <td style={s.tdr}>${fmt(row.suma_neto)}</td>
                                            <td style={s.tdr}>${fmt(row.suma_iva)}</td>
                                            <td style={{ ...s.tdr, fontWeight: 700 }}>${fmt(row.suma_total)}</td>
                                        </tr>
                                    ) : (
                                        <tr key={i}>
                                            <td style={s.td}>{String(row.fecha_fact || row.fecha_comprob || '').slice(0, 10)}</td>
                                            <td style={s.td}>{row.cod_comprob}{row.comprobante_letra || ''}</td>
                                            <td style={s.td}>{row.comprobante_pto_vta}-{String(row.nro_comprob || 0).padStart(8, '0')}</td>
                                            <td style={s.tdr}>${fmt(row.neto)}</td>
                                            <td style={s.tdr}>${fmt(row.iva_1)}</td>
                                            <td style={{ ...s.tdr, fontWeight: 700 }}>${fmt(row.tot_general)}</td>
                                        </tr>
                                    )
                                )}
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: EXPORTACIONES APLICATIVOS
// ═══════════════════════════════════════════════════════════════════════════════
function PanelExportaciones() {
    const [sub, setSub] = useState('SICORE');
    const [historial, setHistorial] = useState([]);
    const [cargando, setCargando] = useState(false);
    const [msg, setMsg] = useState(null);
    const [resultado, setResult] = useState(null);

    // Formularios por aplicativo
    const [sicore, setSicore] = useState({ circuito: 'V', fecha_desde: primerDiaMes(), fecha_hasta: hoy(), regimenes: [] });
    const [sifere, setSifere] = useState({ tipo_impuesto: 'P', fecha_desde: primerDiaMes(), fecha_hasta: hoy(), provincia: '' });
    const [generico, setGenerico] = useState({ aplicativo: 'SIACER', circuito: 'V', fecha_desde: primerDiaMes(), fecha_hasta: hoy() });

    const cargarHistorial = useCallback(async () => {
        const r = await fetch(`${API}/exportaciones/?aplicativo=${sub}`);
        const d = await r.json();
        if (d.status === 'success') setHistorial(d.data);
    }, [sub]);

    useEffect(() => { cargarHistorial(); }, [cargarHistorial]);

    const generar = async () => {
        setCargando(true); setMsg(null); setResult(null);
        let url, payload;
        if (sub === 'SICORE') { url = `${API}/exportaciones/sicore/`; payload = { ...sicore, usuario: 'admin' }; }
        else if (sub === 'SIFERE') { url = `${API}/exportaciones/sifere/`; payload = { ...sifere, usuario: 'admin' }; }
        else { url = `${API}/exportaciones/${sub.toLowerCase()}/`; payload = { ...generico, aplicativo: sub, usuario: 'admin' }; }

        const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        const d = await r.json();
        if (d.status === 'success') { setResult(d); setMsg({ tipo: 'ok', texto: d.mensaje }); cargarHistorial(); }
        else setMsg({ tipo: 'error', texto: d.mensaje });
        setCargando(false);
    };

    const APLICATIVOS = [
        { id: 'SICORE', label: 'SICORE' }, { id: 'SIFERE', label: 'SIFERE' },
        { id: 'SIACER', label: 'SIACER' }, { id: 'EARCIBA', label: 'e-ARCIBA' },
        { id: 'SICOL', label: 'SICOL' }, { id: 'ARBA', label: 'ARBA' },
        { id: 'SIRCAR', label: 'SIRCAR' }, { id: 'SIPRIB', label: 'SIPRIB' },
        { id: 'SIJP', label: 'SIJP' }, { id: 'SIRE', label: 'SIRE' },
        { id: 'F8001', label: 'F8001' }, { id: 'SIRFT', label: 'SIRFT' },
        { id: 'REGELEC', label: 'Reg. Electrónica' }, { id: 'DUPELEC', label: 'Duplicados' },
        { id: 'SVINCUL', label: 'Suj. Vinculados' },
    ];

    const renderForm = () => {
        if (sub === 'SICORE') return (
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                <Campo label='Circuito'><select style={s.select} value={sicore.circuito} onChange={e => setSicore(p => ({ ...p, circuito: e.target.value }))}><option value='V'>Ventas</option><option value='C'>Compras</option></select></Campo>
                <Campo label='Desde'><input type='date' style={s.input} value={sicore.fecha_desde} onChange={e => setSicore(p => ({ ...p, fecha_desde: e.target.value }))} /></Campo>
                <Campo label='Hasta'><input type='date' style={s.input} value={sicore.fecha_hasta} onChange={e => setSicore(p => ({ ...p, fecha_hasta: e.target.value }))} /></Campo>
            </div>
        );
        if (sub === 'SIFERE') return (
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                <Campo label='Tipo Impuesto'><select style={s.select} value={sifere.tipo_impuesto} onChange={e => setSifere(p => ({ ...p, tipo_impuesto: e.target.value }))}><option value='P'>Percepciones</option><option value='R'>Retenciones</option><option value='B'>Recaud. Bancarias</option><option value='A'>Perc. Aduaneras</option></select></Campo>
                <Campo label='Desde'><input type='date' style={s.input} value={sifere.fecha_desde} onChange={e => setSifere(p => ({ ...p, fecha_desde: e.target.value }))} /></Campo>
                <Campo label='Hasta'><input type='date' style={s.input} value={sifere.fecha_hasta} onChange={e => setSifere(p => ({ ...p, fecha_hasta: e.target.value }))} /></Campo>
                <Campo label='Provincia (vacío=Todas)' flex='1 1 150px'><input style={s.input} value={sifere.provincia} placeholder='ej: 01' onChange={e => setSifere(p => ({ ...p, provincia: e.target.value }))} /></Campo>
            </div>
        );
        return (
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                <Campo label='Circuito'><select style={s.select} value={generico.circuito} onChange={e => setGenerico(p => ({ ...p, circuito: e.target.value }))}><option value='V'>Ventas</option><option value='C'>Compras</option><option value='A'>Ambos</option></select></Campo>
                <Campo label='Desde'><input type='date' style={s.input} value={generico.fecha_desde} onChange={e => setGenerico(p => ({ ...p, fecha_desde: e.target.value }))} /></Campo>
                <Campo label='Hasta'><input type='date' style={s.input} value={generico.fecha_hasta} onChange={e => setGenerico(p => ({ ...p, fecha_hasta: e.target.value }))} /></Campo>
            </div>
        );
    };

    return (
        <div style={s.card}>
            <h3 style={{ marginTop: 0, color: '#1e3a5f' }}>📤 Exportación a Aplicativos AFIP / Provinciales</h3>

            {/* Selector de aplicativo */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 16 }}>
                {APLICATIVOS.map(a => (
                    <button key={a.id} onClick={() => setSub(a.id)} style={{
                        padding: '5px 14px', border: `1px solid ${sub === a.id ? '#1d4ed8' : '#d0d7de'}`,
                        borderRadius: 20, background: sub === a.id ? '#1d4ed8' : '#fff',
                        color: sub === a.id ? '#fff' : '#24292f', cursor: 'pointer', fontSize: 12, fontWeight: sub === a.id ? 700 : 400,
                    }}>{a.label}</button>
                ))}
            </div>

            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: 16, marginBottom: 16 }}>
                <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 12, color: '#1e3a5f' }}>Parámetros — {sub}</div>
                {renderForm()}
                <div style={{ marginTop: 12, display: 'flex', gap: 10 }}>
                    <Btn onClick={generar} disabled={cargando} color='#0f766e'>
                        {cargando ? 'Generando...' : `⚡ Generar ${sub}`}
                    </Btn>
                    {resultado && (
                        <Btn color='#1d4ed8' onClick={() => descargar(resultado.nombre, resultado.contenido_b64)}>
                            ⬇ Descargar {resultado.nombre}
                        </Btn>
                    )}
                </div>
            </div>

            <Msg msg={msg} />

            {/* Historial */}
            <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#555', marginBottom: 8 }}>Historial de exportaciones — {sub}</div>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr><th style={s.th}>Fecha</th><th style={s.th}>Período</th><th style={s.th}>Estado</th><th style={s.th}>Registros</th><th style={s.th}>Generado por</th><th style={s.th}>Descargar</th></tr>
                    </thead>
                    <tbody>
                        {historial.length === 0
                            ? <tr><td colSpan={6} style={{ ...s.td, textAlign: 'center', color: '#888' }}>Sin exportaciones para {sub}</td></tr>
                            : historial.map(h => (
                                <tr key={h.id}>
                                    <td style={s.td}>{new Date(h.generado_en).toLocaleDateString('es-AR')}</td>
                                    <td style={s.td}>{h.fecha_desde} → {h.fecha_hasta}</td>
                                    <td style={s.td}><Badge texto={h.estado} color={h.estado === 'COMPLETADO' ? '#059669' : h.estado === 'ERROR' ? '#dc2626' : '#0284c7'} /></td>
                                    <td style={s.tdr}>{h.cantidad_registros}</td>
                                    <td style={s.td}>{h.generado_por || '—'}</td>
                                    <td style={s.td}>
                                        {h.estado === 'COMPLETADO' && (
                                            <button onClick={async () => {
                                                const r = await fetch(`${API}/exportaciones/${h.id}/descargar/`);
                                                const d = await r.json();
                                                if (d.status === 'success') descargar(d.nombre, d.contenido_b64);
                                            }} style={{ fontSize: 12, color: '#1d4ed8', background: 'none', border: '1px solid #1d4ed8', borderRadius: 4, padding: '2px 10px', cursor: 'pointer' }}>
                                                ⬇ TXT
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: MONOTRIBUTISTAS
// ═══════════════════════════════════════════════════════════════════════════════
function PanelMonotributistas() {
    const [sub, setSub] = useState('pdv');
    const [form, setForm] = useState({ fecha_desde: primerDiaMes(), fecha_hasta: hoy(), top_n: 5 });
    const [datos, setDatos] = useState(null);
    const [cargando, setCargando] = useState(false);
    const [msg, setMsg] = useState(null);

    const consultar = async () => {
        setCargando(true); setMsg(null); setDatos(null);
        const urls = { pdv: `${API}/monotributistas/ventas-pdv/`, clientes: `${API}/monotributistas/ranking-clientes/`, proveedores: `${API}/monotributistas/ranking-proveedores/` };
        const r = await fetch(urls[sub], { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) });
        const d = await r.json();
        if (d.status === 'success') setDatos(d);
        else setMsg({ tipo: 'error', texto: d.mensaje });
        setCargando(false);
    };

    return (
        <div style={s.card}>
            <h3 style={{ marginTop: 0, color: '#1e3a5f' }}>📊 Monotributistas — Presentación Semestral</h3>

            <div style={{ display: 'flex', gap: 6, marginBottom: 16 }}>
                {[['pdv', '🏪 Ventas por PDV'], ['clientes', '👥 Ranking Clientes'], ['proveedores', '🏭 Ranking Proveedores']].map(([id, label]) => (
                    <button key={id} onClick={() => setSub(id)} style={{ padding: '6px 16px', border: `1px solid ${sub === id ? '#7c3aed' : '#d0d7de'}`, borderRadius: 6, background: sub === id ? '#7c3aed' : '#fff', color: sub === id ? '#fff' : '#24292f', cursor: 'pointer', fontSize: 13, fontWeight: sub === id ? 700 : 400 }}>{label}</button>
                ))}
            </div>

            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: 16 }}>
                <Campo label='Fecha desde'><input type='date' style={s.input} value={form.fecha_desde} onChange={e => setForm(p => ({ ...p, fecha_desde: e.target.value }))} /></Campo>
                <Campo label='Fecha hasta'><input type='date' style={s.input} value={form.fecha_hasta} onChange={e => setForm(p => ({ ...p, fecha_hasta: e.target.value }))} /></Campo>
                {sub !== 'pdv' && (
                    <Campo label='Top N' flex='1 1 100px'>
                        <input type='number' style={s.input} min={1} max={20} value={form.top_n} onChange={e => setForm(p => ({ ...p, top_n: parseInt(e.target.value) || 5 }))} />
                    </Campo>
                )}
                <div style={{ paddingTop: 20 }}>
                    <Btn onClick={consultar} disabled={cargando} color='#7c3aed'>
                        {cargando ? 'Consultando...' : '📊 Generar Informe'}
                    </Btn>
                </div>
            </div>

            <Msg msg={msg} />

            {datos && (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr>
                            {sub === 'pdv' ? (
                                <><th style={s.th}>Punto de Venta</th><th style={{ ...s.th, textAlign: 'right' }}>Comprobantes</th><th style={{ ...s.th, textAlign: 'right' }}>Neto</th><th style={{ ...s.th, textAlign: 'right' }}>Total</th></>
                            ) : (
                                <><th style={s.th}>Pos.</th><th style={s.th}>{sub === 'clientes' ? 'Cliente' : 'Proveedor'}</th><th style={s.th}>CUIT</th><th style={{ ...s.th, textAlign: 'right' }}>Cantidad</th><th style={{ ...s.th, textAlign: 'right' }}>Total</th></>
                            )}
                        </tr>
                    </thead>
                    <tbody>
                        {datos.data?.map((row, i) =>
                            sub === 'pdv' ? (
                                <tr key={i}>
                                    <td style={{ ...s.td, fontWeight: 700 }}>{row.comprobante_pto_vta || '—'}</td>
                                    <td style={s.tdr}>{row.cantidad}</td>
                                    <td style={s.tdr}>${fmt(row.neto)}</td>
                                    <td style={{ ...s.tdr, fontWeight: 700 }}>${fmt(row.total)}</td>
                                </tr>
                            ) : (
                                <tr key={i} style={{ background: i === 0 ? '#fffbeb' : 'transparent' }}>
                                    <td style={{ ...s.td, fontWeight: 700, color: i === 0 ? '#d97706' : 'inherit' }}>{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`}</td>
                                    <td style={s.td}>{row.denominacion || row.nom || '—'}</td>
                                    <td style={{ ...s.td, fontSize: 12 }}>{row.nro_cuit || '—'}</td>
                                    <td style={s.tdr}>{row.cantidad}</td>
                                    <td style={{ ...s.tdr, fontWeight: 700 }}>${fmt(row.total)}</td>
                                </tr>
                            )
                        )}
                        {sub === 'pdv' && datos.gran_total !== undefined && (
                            <tr style={{ background: '#f1f5f9' }}>
                                <td style={{ ...s.td, fontWeight: 700 }}>TOTAL GENERAL</td>
                                <td colSpan={2}></td>
                                <td style={{ ...s.tdr, fontWeight: 700 }}>${fmt(datos.gran_total)}</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            )}
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MÓDULO PRINCIPAL
// ═══════════════════════════════════════════════════════════════════════════════
const MENU_ITEMS = [
    { id: 'libro-v', label: '📗 Libro IVA Ventas', grupo: 'iva' },
    { id: 'libro-c', label: '📕 Libro IVA Compras', grupo: 'iva' },
    { id: 'iva-digital', label: '💾 IVA Digital (TXT)', grupo: 'iva' },
    { id: 'ddjj', label: '📋 Dec. Juradas (DDJJ)', grupo: 'ddjj' },
    { id: 'analisis', label: '🔍 Análisis Operaciones', grupo: 'ddjj' },
    { id: 'exportaciones', label: '📤 Exportaciones AFIP', grupo: 'expo' },
    { id: 'monotrib', label: '📊 Monotributistas', grupo: 'otros' },
];

const GRUPOS_IMP = [
    { id: 'iva', label: '💼 IVA' },
    { id: 'ddjj', label: '📋 DECLARACIONES' },
    { id: 'expo', label: '📤 EXPORTACIONES' },
    { id: 'otros', label: '📊 OTROS' },
];

export default function ModuloImpositivo() {
    const [activo, setActivo] = useState('libro-v');

    const renderPanel = () => {
        switch (activo) {
            case 'libro-v': return <PanelLibroIVA circuito='V' />;
            case 'libro-c': return <PanelLibroIVA circuito='C' />;
            case 'iva-digital': return <PanelIVADigital />;
            case 'ddjj': return <PanelDDJJ />;
            case 'analisis': return <PanelAnalisisOp />;
            case 'exportaciones': return <PanelExportaciones />;
            case 'monotrib': return <PanelMonotributistas />;
            default: return <PanelLibroIVA circuito='V' />;
        }
    };

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: '#f0f4f8' }}>
            {/* Sidebar */}
            <div style={{ width: 220, background: '#1e3a5f', color: '#fff', padding: '16px 0', flexShrink: 0, overflowY: 'auto' }}>
                <div style={{ padding: '0 16px 16px', borderBottom: '1px solid rgba(255,255,255,.15)' }}>
                    <div style={{ fontSize: 10, letterSpacing: 1, opacity: .5, marginBottom: 2 }}>MÓDULO</div>
                    <div style={{ fontWeight: 700, fontSize: 14 }}>🏛 Informes Impositivos</div>
                </div>
                {GRUPOS_IMP.map(g => (
                    <div key={g.id}>
                        <div style={{ padding: '12px 16px 4px', fontSize: 10, fontWeight: 700, opacity: .5, letterSpacing: 1 }}>{g.label}</div>
                        {MENU_ITEMS.filter(m => m.grupo === g.id).map(m => (
                            <button key={m.id} onClick={() => setActivo(m.id)} style={{
                                display: 'block', width: '100%', textAlign: 'left',
                                padding: '9px 16px', border: 'none', cursor: 'pointer',
                                background: activo === m.id ? 'rgba(255,255,255,.15)' : 'transparent',
                                color: activo === m.id ? '#fff' : 'rgba(255,255,255,.65)',
                                fontWeight: activo === m.id ? 700 : 400, fontSize: 12,
                                borderLeft: activo === m.id ? '3px solid #60a5fa' : '3px solid transparent',
                            }}>{m.label}</button>
                        ))}
                    </div>
                ))}
            </div>

            {/* Contenido */}
            <div style={{ flex: 1, padding: 24, overflowY: 'auto' }}>
                {renderPanel()}
            </div>
        </div>
    );
}