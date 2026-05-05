/**
 * PanelImportarARCA.jsx — Panel de importación de "Mis Comprobantes" ARCA.
 *
 * INTEGRACIÓN:
 *   Este componente está diseñado para vivir dentro del ModuloImpositivo.jsx
 *   existente. Hay dos formas de integrarlo:
 *
 *   OPCIÓN A — Archivo separado (recomendado, más prolijo):
 *     1. Guardar este archivo como `frontend/src/PanelImportarARCA.jsx`
 *     2. En `ModuloImpositivo.jsx`, agregar al inicio:
 *           import PanelImportarARCA from './PanelImportarARCA';
 *     3. En `MENU_ITEMS` agregar:
 *           { id: 'importar-arca', label: '📥 Importar de ARCA', grupo: 'iva' },
 *     4. En el switch de `renderPanel()` agregar:
 *           case 'importar-arca': return <PanelImportarARCA />;
 *
 *   OPCIÓN B — Pegar el componente al final del ModuloImpositivo.jsx
 *     (antes del default export). Igual hay que sumar la entrada al MENU_ITEMS
 *     y al switch.
 *
 * Reusa los helpers visuales (s, Btn, Msg, Campo, Badge, fmt) que ya tenés
 * definidos al principio de ModuloImpositivo.jsx — por eso este archivo
 * los IMPORTA en lugar de redefinirlos. Si preferís OPCIÓN B, borrá el import
 * de UI helpers y reusá los del archivo donde lo pegues.
 */
import { useState, useRef } from 'react';

// Helpers — DUPLICADOS porque este archivo es standalone. Si lo pegás dentro
// de ModuloImpositivo.jsx, eliminá esta sección entera y usá los helpers
// existentes del archivo.
const API = `${import.meta.env.VITE_API_URL}/api/impositivo`;

const fmt = (n) => Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const s = {
    card: { background: '#fff', borderRadius: 10, boxShadow: '0 1px 4px rgba(0,0,0,.10)', padding: 20, marginBottom: 16 },
    th: { background: '#f8f9fa', padding: '8px 12px', textAlign: 'left', fontSize: 12, fontWeight: 700, color: '#555', borderBottom: '2px solid #dee2e6' },
    td: { padding: '7px 12px', fontSize: 13, borderBottom: '1px solid #f0f0f0' },
    tdr: { padding: '7px 12px', fontSize: 13, textAlign: 'right', borderBottom: '1px solid #f0f0f0' },
    label: { display: 'block', fontSize: 12, fontWeight: 700, color: '#555', marginBottom: 3 },
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
    const colors = {
        ok:    { bg: '#d1fae5', color: '#065f46', border: '#6ee7b7' },
        error: { bg: '#fee2e2', color: '#991b1b', border: '#fca5a5' },
        warn:  { bg: '#fef3c7', color: '#92400e', border: '#fcd34d' },
    };
    const c = colors[msg.tipo] || colors.error;
    return (
        <div style={{ padding: '10px 16px', borderRadius: 6, marginBottom: 14, fontSize: 13, fontWeight: 600,
            background: c.bg, color: c.color, border: `1px solid ${c.border}` }}>{msg.texto}</div>
    );
};

const Badge = ({ texto, color = '#3b82f6' }) => (
    <span style={{ background: color + '20', color, border: `1px solid ${color}50`,
        padding: '2px 10px', borderRadius: 12, fontSize: 11, fontWeight: 700 }}>{texto}</span>
);

// ═══════════════════════════════════════════════════════════════════════════════
// COMPONENTE
// ═══════════════════════════════════════════════════════════════════════════════
export default function PanelImportarARCA() {
    const [archivo, setArchivo] = useState(null);
    const [circuito, setCircuito] = useState('C');   // C = Recibidos→Compras
    const [resultado, setResultado] = useState(null);
    const [cargando, setCargando] = useState(false);
    const [msg, setMsg] = useState(null);
    const [dragOver, setDragOver] = useState(false);
    const fileInputRef = useRef(null);

    // Detecta automáticamente el circuito desde el nombre del archivo
    const onArchivoSeleccionado = (f) => {
        if (!f) return;
        if (!f.name.toLowerCase().endsWith('.xlsx')) {
            setMsg({ tipo: 'error', texto: 'El archivo debe ser .xlsx (descargado de Mis Comprobantes ARCA).' });
            return;
        }
        setArchivo(f);
        setMsg(null);
        setResultado(null);
        const lower = f.name.toLowerCase();
        if (lower.includes('recibidos')) setCircuito('C');
        else if (lower.includes('emitidos')) setCircuito('V');
    };

    // Helpers para el flujo previsualizar/confirmar
    const enviar = async (modo) => {
        if (!archivo) {
            setMsg({ tipo: 'error', texto: 'Primero seleccioná el archivo .xlsx.' });
            return;
        }
        setCargando(true); setMsg(null);
        const formData = new FormData();
        formData.append('archivo', archivo);
        formData.append('circuito', circuito);
        formData.append('modo', modo);
        formData.append('usuario', 'admin');

        try {
            const r = await fetch(`${API}/importar-arca/`, { method: 'POST', body: formData });
            const d = await r.json();
            if (d.status === 'success') {
                setResultado({ ...d, modo });
                const t = d.totales;
                if (modo === 'previsualizar') {
                    setMsg({
                        tipo: t.errores > 0 ? 'warn' : 'ok',
                        texto: `Previsualización: ${t.leidos} leídos, ${t.ok} a importar, ${t.duplicados} duplicados, ${t.errores} con error.`
                    });
                } else {
                    setMsg({
                        tipo: t.errores > 0 ? 'warn' : 'ok',
                        texto: `Importación completa: ${t.ok} OK, ${t.duplicados} duplicados (omitidos), ${t.errores} errores.`
                    });
                }
                if (!d.coincide_cuit && d.cuit_archivo && d.cuit_empresa) {
                    setMsg(prev => ({
                        tipo: 'warn',
                        texto: `${prev.texto} ⚠️ El CUIT del archivo (${d.cuit_archivo}) NO coincide con el de la empresa (${d.cuit_empresa}). Verificá antes de continuar.`
                    }));
                }
            } else {
                setMsg({ tipo: 'error', texto: d.mensaje });
            }
        } catch (e) {
            setMsg({ tipo: 'error', texto: 'Error de red: ' + e.message });
        }
        setCargando(false);
    };

    const limpiar = () => {
        setArchivo(null);
        setResultado(null);
        setMsg(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    return (
        <div style={s.card}>
            <h3 style={{ marginTop: 0, color: '#1e3a5f' }}>📥 Importar de ARCA — Mis Comprobantes</h3>

            <div style={{ background: '#eff6ff', border: '1px solid #93c5fd', borderRadius: 8,
                padding: '12px 16px', marginBottom: 16, fontSize: 13, color: '#1e40af' }}>
                <strong>¿Qué hace?</strong> Importa un archivo Excel descargado desde el portal de
                ARCA (ex AFIP) → "Mis Comprobantes" → "Recibidos" o "Emitidos".
                <ul style={{ margin: '6px 0 0 18px', padding: 0 }}>
                    <li>Crea proveedores/clientes automáticamente si no existen.</li>
                    <li>Salta comprobantes ya cargados (anti-duplicado por tipo + pto + nro + CUIT).</li>
                    <li>NO toca stock ni costos (son comprobantes históricos para fines impositivos).</li>
                    <li>Convierte USD a pesos usando el tipo de cambio del archivo.</li>
                </ul>
            </div>

            <Msg msg={msg} />

            {/* Zona de carga */}
            <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => {
                    e.preventDefault();
                    setDragOver(false);
                    onArchivoSeleccionado(e.dataTransfer.files[0]);
                }}
                onClick={() => fileInputRef.current?.click()}
                style={{
                    border: `2px dashed ${dragOver ? '#1d4ed8' : (archivo ? '#10b981' : '#cbd5e1')}`,
                    borderRadius: 10,
                    background: dragOver ? '#dbeafe' : (archivo ? '#ecfdf5' : '#f8fafc'),
                    padding: 30, textAlign: 'center', cursor: 'pointer', marginBottom: 16,
                    transition: 'all .15s',
                }}
            >
                <input
                    ref={fileInputRef}
                    type='file'
                    accept='.xlsx'
                    style={{ display: 'none' }}
                    onChange={(e) => onArchivoSeleccionado(e.target.files[0])}
                />
                {archivo ? (
                    <>
                        <div style={{ fontSize: 28, marginBottom: 6 }}>📄</div>
                        <div style={{ fontWeight: 700, color: '#065f46', fontSize: 14 }}>{archivo.name}</div>
                        <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
                            {(archivo.size / 1024).toFixed(1)} KB · click o arrastrá otro archivo para reemplazar
                        </div>
                    </>
                ) : (
                    <>
                        <div style={{ fontSize: 32, marginBottom: 6 }}>⬆️</div>
                        <div style={{ fontWeight: 600, color: '#475569' }}>
                            Arrastrá el archivo .xlsx aquí o hacé click
                        </div>
                        <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>
                            Mis_Comprobantes_Recibidos_-_CUIT_XXX.xlsx<br />
                            Mis_Comprobantes_Emitidos_-_CUIT_XXX.xlsx
                        </div>
                    </>
                )}
            </div>

            {/* Selector de circuito */}
            <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', marginBottom: 16, flexWrap: 'wrap' }}>
                <div style={{ flex: '1 1 250px' }}>
                    <label style={s.label}>Tipo de archivo</label>
                    <select style={s.select} value={circuito} onChange={(e) => setCircuito(e.target.value)} disabled={cargando}>
                        <option value='C'>Recibidos → registrar como Compras</option>
                        <option value='V'>Emitidos → registrar como Ventas</option>
                    </select>
                </div>
                <Btn onClick={() => enviar('previsualizar')} disabled={!archivo || cargando} secondary color='#475569'>
                    👁️ Previsualizar
                </Btn>
                <Btn onClick={() => enviar('confirmar')} disabled={!archivo || cargando} color='#0f766e'>
                    {cargando ? 'Procesando...' : '✅ Importar al sistema'}
                </Btn>
                {(archivo || resultado) && (
                    <Btn onClick={limpiar} secondary color='#dc2626' sm>× Limpiar</Btn>
                )}
            </div>

            {/* Resultado */}
            {resultado && (
                <>
                    {/* Métricas */}
                    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
                        {[
                            { label: 'Leídos', val: resultado.totales.leidos, color: '#3b82f6' },
                            { label: 'OK', val: resultado.totales.ok, color: '#059669' },
                            { label: 'Duplicados', val: resultado.totales.duplicados, color: '#d97706' },
                            { label: 'Errores', val: resultado.totales.errores, color: '#dc2626' },
                        ].map(({ label, val, color }) => (
                            <div key={label} style={{
                                background: color + '15', borderRadius: 8, padding: '10px 20px',
                                flex: '1 1 100px', textAlign: 'center', border: `1px solid ${color}40`,
                            }}>
                                <div style={{ fontSize: 11, color: '#888' }}>{label}</div>
                                <div style={{ fontSize: 22, fontWeight: 700, color }}>{val}</div>
                            </div>
                        ))}
                    </div>

                    {resultado.modo === 'previsualizar' && resultado.totales.ok > 0 && (
                        <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: 6,
                            padding: '8px 12px', marginBottom: 16, fontSize: 12, color: '#78350f' }}>
                            🔎 Esta es solo una previsualización — no se guardó nada todavía.
                            Revisá los datos abajo y luego hacé click en "Importar al sistema".
                        </div>
                    )}

                    {/* Tabla de resultados OK */}
                    {resultado.ok.length > 0 && (
                        <div style={{ marginBottom: 16 }}>
                            <div style={{ fontSize: 13, fontWeight: 700, color: '#065f46', marginBottom: 6 }}>
                                ✓ {resultado.ok.length} comprobante{resultado.ok.length === 1 ? '' : 's'}
                                {resultado.modo === 'confirmar' ? ' importado' + (resultado.ok.length === 1 ? '' : 's') : ' a importar'}
                            </div>
                            <div style={{ maxHeight: 250, overflowY: 'auto', border: '1px solid #d1fae5', borderRadius: 6 }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                    <thead style={{ position: 'sticky', top: 0 }}>
                                        <tr>
                                            <th style={s.th}>Fila</th><th style={s.th}>Tipo</th>
                                            <th style={s.th}>Pto/Nro</th><th style={s.th}>CUIT</th>
                                            <th style={{ ...s.th, textAlign: 'right' }}>Total</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {resultado.ok.map((r, i) => (
                                            <tr key={i}>
                                                <td style={s.td}>{r.fila}</td>
                                                <td style={s.td}><Badge texto={r.tipo} color='#059669' /></td>
                                                <td style={s.td}>{r.pto}-{String(r.nro).padStart(8, '0')}</td>
                                                <td style={{ ...s.td, fontSize: 12 }}>{r.cuit}</td>
                                                <td style={{ ...s.tdr, fontWeight: 700 }}>${fmt(r.total)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Tabla de duplicados */}
                    {resultado.duplicados.length > 0 && (
                        <div style={{ marginBottom: 16 }}>
                            <div style={{ fontSize: 13, fontWeight: 700, color: '#92400e', marginBottom: 6 }}>
                                ⚠️ {resultado.duplicados.length} duplicado{resultado.duplicados.length === 1 ? '' : 's'} (ya estaban en el sistema, se omitieron)
                            </div>
                            <div style={{ maxHeight: 200, overflowY: 'auto', border: '1px solid #fcd34d', borderRadius: 6 }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                    <thead style={{ position: 'sticky', top: 0 }}>
                                        <tr>
                                            <th style={s.th}>Fila</th><th style={s.th}>Tipo</th>
                                            <th style={s.th}>Pto/Nro</th><th style={s.th}>CUIT</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {resultado.duplicados.map((r, i) => (
                                            <tr key={i}>
                                                <td style={s.td}>{r.fila}</td>
                                                <td style={s.td}><Badge texto={r.tipo} color='#d97706' /></td>
                                                <td style={s.td}>{r.pto}-{String(r.nro).padStart(8, '0')}</td>
                                                <td style={{ ...s.td, fontSize: 12 }}>{r.cuit || '—'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Tabla de errores */}
                    {resultado.errores.length > 0 && (
                        <div style={{ marginBottom: 16 }}>
                            <div style={{ fontSize: 13, fontWeight: 700, color: '#991b1b', marginBottom: 6 }}>
                                ✗ {resultado.errores.length} error{resultado.errores.length === 1 ? '' : 'es'}
                            </div>
                            <div style={{ maxHeight: 200, overflowY: 'auto', border: '1px solid #fca5a5', borderRadius: 6 }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                    <thead style={{ position: 'sticky', top: 0 }}>
                                        <tr>
                                            <th style={s.th}>Fila</th><th style={s.th}>Motivo</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {resultado.errores.map((r, i) => (
                                            <tr key={i}>
                                                <td style={s.td}>{r.fila}</td>
                                                <td style={{ ...s.td, color: '#991b1b' }}>{r.motivo}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}