import { useState, useEffect, useCallback } from 'react'

const API = `${import.meta.env.VITE_API_URL}/api/bodega`

// ── Helpers ──────────────────────────────────────────────────────────────────
const api = async (path, method = 'GET', body = null) => {
  const opts = { method, headers: { 'Content-Type': 'application/json' } }
  if (body) opts.body = JSON.stringify(body)
  const r = await fetch(`${API}/${path}`, opts)
  return r.json()
}

const Badge = ({ text, color = '#2980b9' }) => (
  <span style={{
    background: color, color: 'white', borderRadius: '4px',
    padding: '2px 8px', fontSize: '11px', fontWeight: '700', marginLeft: '6px',
  }}>{text}</span>
)

const Btn = ({ onClick, children, color = '#2980b9', disabled, small }) => (
  <button
    onClick={onClick} disabled={disabled}
    style={{
      background: disabled ? '#bdc3c7' : color, color: 'white', border: 'none',
      borderRadius: '5px', padding: small ? '4px 10px' : '7px 16px',
      cursor: disabled ? 'default' : 'pointer', fontSize: small ? '12px' : '13px',
      fontWeight: '600',
    }}>
    {children}
  </button>
)

const Card = ({ children, style }) => (
  <div style={{
    background: 'white', borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,.08)',
    padding: '20px', marginBottom: '16px', ...style,
  }}>{children}</div>
)

const Input = ({ label, value, onChange, type = 'text', required, placeholder, small }) => (
  <div style={{ marginBottom: '10px' }}>
    {label && <label style={{ fontSize: '12px', color: '#7f8c8d', display: 'block', marginBottom: '3px' }}>
      {label}{required && <span style={{ color: '#e74c3c' }}> *</span>}
    </label>}
    <input
      type={type} value={value || ''} onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        width: '100%', padding: '7px 10px', border: '1px solid #ddd',
        borderRadius: '5px', fontSize: small ? '12px' : '13px',
        boxSizing: 'border-box',
      }}
    />
  </div>
)

const Select = ({ label, value, onChange, options }) => (
  <div style={{ marginBottom: '10px' }}>
    {label && <label style={{ fontSize: '12px', color: '#7f8c8d', display: 'block', marginBottom: '3px' }}>{label}</label>}
    <select value={value || ''} onChange={e => onChange(e.target.value)}
      style={{ width: '100%', padding: '7px 10px', border: '1px solid #ddd', borderRadius: '5px', fontSize: '13px' }}>
      <option value="">— Seleccionar —</option>
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  </div>
)

const estadoLoteColor = { EB: '#e67e22', CR: '#8e44ad', LI: '#27ae60', EM: '#2c3e50', EP: '#2980b9', VE: '#16a085', AN: '#c0392b' }
const estadoRecColor  = { LI: '#27ae60', OC: '#e67e22', LA: '#3498db', MN: '#e74c3c', BA: '#95a5a6' }

// ─────────────────────────────────────────────────────────────────────────────
// DASHBOARD
// ─────────────────────────────────────────────────────────────────────────────
function DashboardBodega() {
  const [data, setData] = useState(null)
  const [campaña, setCampaña] = useState(new Date().getFullYear())

  useEffect(() => {
    api(`dashboard/?campaña=${campaña}`).then(r => r.ok && setData(r.data))
  }, [campaña])

  const kpiStyle = (color) => ({
    background: color, color: 'white', borderRadius: '8px',
    padding: '16px 20px', textAlign: 'center',
  })

  if (!data) return <p style={{ color: '#7f8c8d' }}>Cargando dashboard…</p>

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, color: '#2c3e50' }}>Campaña</h3>
        <input type="number" value={campaña} onChange={e => setCampaña(e.target.value)}
          style={{ width: '80px', padding: '5px 8px', border: '1px solid #ddd', borderRadius: '5px' }} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '12px', marginBottom: '20px' }}>
        <div style={kpiStyle('#e67e22')}>
          <div style={{ fontSize: '11px', opacity: .8 }}>Uva recibida</div>
          <div style={{ fontSize: '24px', fontWeight: '800' }}>
            {(data.kg_uva_recibidos / 1000).toFixed(1)} t
          </div>
        </div>
        <div style={kpiStyle('#2980b9')}>
          <div style={{ fontSize: '11px', opacity: .8 }}>Litros en stock</div>
          <div style={{ fontSize: '24px', fontWeight: '800' }}>
            {Math.round(data.litros_en_stock).toLocaleString('es-AR')}
          </div>
        </div>
        <div style={kpiStyle('#27ae60')}>
          <div style={{ fontSize: '11px', opacity: .8 }}>Recipientes libres</div>
          <div style={{ fontSize: '24px', fontWeight: '800' }}>{data?.recipientes?.libres ?? 0}</div>
        </div>
        <div style={kpiStyle('#8e44ad')}>
          <div style={{ fontSize: '11px', opacity: .8 }}>Barricas ocupadas</div>
          <div style={{ fontSize: '24px', fontWeight: '800' }}>{data?.barricas?.ocupadas ?? 0}</div>
        </div>
        <div style={kpiStyle('#c0392b')}>
          <div style={{ fontSize: '11px', opacity: .8 }}>Tickets pendientes</div>
          <div style={{ fontSize: '24px', fontWeight: '800' }}>{data.tickets_bascula_pendientes}</div>
        </div>
        <div style={kpiStyle('#16a085')}>
          <div style={{ fontSize: '11px', opacity: .8 }}>Órdenes embotellado</div>
          <div style={{ fontSize: '24px', fontWeight: '800' }}>{data.ordenes_embotellado_pendientes}</div>
        </div>
      </div>

      <Card>
        <h4 style={{ margin: '0 0 12px', color: '#2c3e50' }}>Lotes por estado</h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {data.lotes_por_estado.map(e => (
            <span key={e.estado} style={{
              background: estadoLoteColor[e.estado] || '#7f8c8d',
              color: 'white', borderRadius: '6px', padding: '6px 14px', fontSize: '13px',
            }}>
              {e.estado} — {e.cant} lote{e.cant !== 1 ? 's' : ''}
            </span>
          ))}
          {data.lotes_por_estado.length === 0 && <span style={{ color: '#7f8c8d' }}>Sin lotes en esta campaña</span>}
        </div>
      </Card>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// RECEPCIÓN (Tickets de báscula)
// ─────────────────────────────────────────────────────────────────────────────
function RecepcionTab({ varietales = [] }) {
  const [tickets, setTickets] = useState([])
  const [lotes, setLotes]     = useState([])
  const [form, setForm]       = useState({})
  const [msg, setMsg]         = useState('')
  const [mostrando, setMostrando] = useState('lista')

  const campaña = new Date().getFullYear()

  useEffect(() => {
    api(`tickets-bascula/?campaña=${campaña}`).then(r => setTickets(Array.isArray(r?.data) ? r.data : []))
    api('lotes/').then(r => setLotes(Array.isArray(r?.data) ? r.data : []))
  }, [])

  const setF = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const guardar = async () => {
    const payload = { ...form, campaña, fecha: form.fecha || new Date().toISOString() }
    const r = await api('tickets-bascula/', 'POST', payload)
    if (r.ok) {
      setMsg('✅ ' + r.msg)
      setForm({})
      api(`tickets-bascula/?campaña=${campaña}`).then(r2 => setTickets(Array.isArray(r2?.data) ? r2.data : []))
      setMostrando('lista')
    } else setMsg('❌ ' + r.msg)
  }

  const asignar = async (ticketId, loteId) => {
    if (!loteId) return
    const r = await api('tickets-bascula/asignar/', 'POST', { ticket_id: ticketId, lote_id: loteId })
    setMsg(r.ok ? '✅ ' + r.msg : '❌ ' + r.msg)
    api(`tickets-bascula/?campaña=${campaña}`).then(r2 => setTickets(Array.isArray(r2?.data) ? r2.data : []))
  }

  const estadoColor = { PE: '#e67e22', AS: '#27ae60', LI: '#3498db' }

  return (
    <div>
      {msg && <div style={{ background: '#ecf0f1', padding: '8px 12px', borderRadius: '6px', marginBottom: '12px', fontSize: '13px' }}>{msg}</div>}

      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
        <Btn onClick={() => setMostrando('lista')} color={mostrando === 'lista' ? '#2c3e50' : '#7f8c8d'}>Lista de tickets</Btn>
        <Btn onClick={() => setMostrando('nuevo')} color="#27ae60">+ Nuevo ticket</Btn>
      </div>

      {mostrando === 'nuevo' && (
        <Card>
          <h4 style={{ margin: '0 0 14px', color: '#2c3e50' }}>Registrar recepción de uva</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
            <Select label="Varietal *" value={form.varietal} onChange={v => setF('varietal', v)}
              options={varietales.map(v => ({ value: v.codigo, label: v.nombre }))} />
            <Input label="Fecha" value={form.fecha} onChange={v => setF('fecha', v)} type="datetime-local" />
            <Input label="Patente camión" value={form.patente_camion} onChange={v => setF('patente_camion', v)} placeholder="ABC 123" />
            <Input label="Proveedor / viñatero" value={form.nombre_prov} onChange={v => setF('nombre_prov', v)} />
            <Input label="Peso bruto (kg) *" value={form.peso_bruto} onChange={v => setF('peso_bruto', v)} type="number" />
            <Input label="Tara (kg)" value={form.tara} onChange={v => setF('tara', v)} type="number" />
            <Input label="°Brix" value={form.brix_entrada} onChange={v => setF('brix_entrada', v)} type="number" />
            <Input label="pH" value={form.ph_entrada} onChange={v => setF('ph_entrada', v)} type="number" />
            <Input label="Precio $/kg" value={form.precio_kg} onChange={v => setF('precio_kg', v)} type="number" />
            <Select label="Estado sanitario" value={form.estado_sanitario} onChange={v => setF('estado_sanitario', v)}
              options={['Óptimo', 'Bueno', 'Regular', 'Malo'].map(s => ({ value: s, label: s }))} />
          </div>
          {form.peso_bruto && form.tara && (
            <div style={{ background: '#eaf4fb', padding: '8px 12px', borderRadius: '6px', fontSize: '13px', marginBottom: '10px' }}>
              <strong>Peso neto estimado:</strong> {(form.peso_bruto - form.tara).toLocaleString('es-AR')} kg
            </div>
          )}
          <div style={{ display: 'flex', gap: '8px' }}>
            <Btn onClick={guardar} color="#27ae60">Guardar ticket</Btn>
            <Btn onClick={() => setMostrando('lista')} color="#7f8c8d">Cancelar</Btn>
          </div>
        </Card>
      )}

      {mostrando === 'lista' && (
        <div>
          <p style={{ color: '#7f8c8d', fontSize: '13px', margin: '0 0 10px' }}>
            {tickets.length} ticket{tickets.length !== 1 ? 's' : ''} — campaña {campaña}
          </p>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: '#2c3e50', color: 'white' }}>
                  {['#', 'Varietal', 'Proveedor', 'Fecha', 'Kg neto', 'Brix', 'Estado', 'Asignar a lote'].map(h => (
                    <th key={h} style={{ padding: '8px 10px', textAlign: 'left', fontWeight: '600' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tickets.map((t, i) => (
                  <tr key={t.id} style={{ background: i % 2 === 0 ? 'white' : '#f8f9fa' }}>
                    <td style={{ padding: '7px 10px' }}>{t.id}</td>
                    <td style={{ padding: '7px 10px' }}>{t.varietal_nombre}</td>
                    <td style={{ padding: '7px 10px' }}>{t.nombre_prov || '—'}</td>
                    <td style={{ padding: '7px 10px' }}>{t.fecha?.slice(0, 16).replace('T', ' ')}</td>
                    <td style={{ padding: '7px 10px', fontWeight: '700' }}>{t.peso_neto?.toLocaleString('es-AR')}</td>
                    <td style={{ padding: '7px 10px' }}>{t.brix_entrada || '—'}°</td>
                    <td style={{ padding: '7px 10px' }}>
                      <span style={{
                        background: estadoColor[t.estado] || '#7f8c8d',
                        color: 'white', borderRadius: '4px', padding: '2px 8px', fontSize: '11px',
                      }}>{t.estado_display}</span>
                    </td>
                    <td style={{ padding: '7px 10px' }}>
                      {t.estado === 'PE' ? (
                        <select
                          defaultValue=""
                          onChange={e => asignar(t.id, e.target.value)}
                          style={{ padding: '3px 6px', fontSize: '12px', border: '1px solid #ddd', borderRadius: '4px' }}>
                          <option value="">— lote —</option>
                          {lotes.filter(l => ['EB', 'LI'].includes(l.estado)).map(l => (
                            <option key={l.id} value={l.id}>{l.codigo} — {l.varietal_nombre}</option>
                          ))}
                        </select>
                      ) : (
                        <span style={{ color: '#7f8c8d', fontSize: '12px' }}>
                          {t.lote_destino_codigo || '—'}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
                {tickets.length === 0 && (
                  <tr><td colSpan={8} style={{ padding: '20px', textAlign: 'center', color: '#7f8c8d' }}>
                    Sin tickets registrados
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// LOTES DE GRANEL
// ─────────────────────────────────────────────────────────────────────────────
function LotesTab({ varietales = [], recipientes = [] }) {
  const [lotes, setLotes]     = useState([])
  const [form, setForm]       = useState({})
  const [selected, setSelected] = useState(null)
  const [ops, setOps]         = useState([])
  const [analisis, setAnalisis] = useState([])
  const [msg, setMsg]         = useState('')
  const [tab2, setTab2]       = useState('ops')

  useEffect(() => { api('lotes/').then(r => setLotes(Array.isArray(r?.data) ? r.data : [])) }, [])

  const setF = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const recargarLotes = () => api('lotes/').then(r => setLotes(Array.isArray(r?.data) ? r.data : []))

  const guardar = async () => {
    const r = await api('lotes/', 'POST', form)
    if (r.ok) {
      setMsg('✅ ' + r.msg)
      recargarLotes()
      setForm({})
    } else setMsg('❌ ' + r.msg)
  }

  const seleccionar = (lote) => {
    setSelected(lote)
    api(`operaciones/?lote_id=${lote.id}`).then(r => setOps(Array.isArray(r?.data) ? r.data : []))
    api(`analisis/?lote_id=${lote.id}`).then(r => setAnalisis(Array.isArray(r?.data) ? r.data : []))
  }

  const tiposVino  = [{ value: 'TI', label: 'Tinto' }, { value: 'BL', label: 'Blanco' },
                      { value: 'RO', label: 'Rosado' }, { value: 'ES', label: 'Espumante' }]
  const estadosLote = ['EB', 'CR', 'LI', 'EM', 'EP', 'VE', 'AN'].map(e => ({ value: e, label: e }))

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '16px' }}>
      {/* Panel izquierdo: lista + formulario */}
      <div>
        <Card>
          <h4 style={{ margin: '0 0 12px', color: '#2c3e50' }}>
            {form.id ? 'Editar lote' : 'Nuevo lote'}
          </h4>
          {msg && <div style={{ fontSize: '12px', marginBottom: '8px', color: msg.startsWith('✅') ? '#27ae60' : '#c0392b' }}>{msg}</div>}
          <Input label="Código *" value={form.codigo} onChange={v => setF('codigo', v)} placeholder="2024-MAL-001" />
          <Select label="Varietal *" value={form.varietal} onChange={v => setF('varietal', v)}
            options={varietales.map(v => ({ value: v.codigo, label: v.nombre }))} />
          <Select label="Tipo de vino" value={form.tipo_vino} onChange={v => setF('tipo_vino', v)} options={tiposVino} />
          <Input label="Campaña *" value={form.campaña} onChange={v => setF('campaña', v)} type="number" placeholder={new Date().getFullYear()} />
          <Input label="Fecha inicio" value={form.fecha_inicio} onChange={v => setF('fecha_inicio', v)} type="date" />
          <Input label="Litros iniciales" value={form.litros_iniciales} onChange={v => setF('litros_iniciales', v)} type="number" />
          <Select label="Recipiente actual" value={form.recipiente_id} onChange={v => setF('recipiente_id', v)}
            options={recipientes.map(r => ({ value: r.id, label: `${r.codigo} — ${r.nombre}` }))} />
          <Select label="Estado" value={form.estado} onChange={v => setF('estado', v)} options={estadosLote} />
          <Input label="Descripción" value={form.descripcion} onChange={v => setF('descripcion', v)} />
          <div style={{ display: 'flex', gap: '8px' }}>
            <Btn onClick={guardar} color="#8e44ad">Guardar lote</Btn>
            {form.id && <Btn onClick={() => setForm({})} color="#7f8c8d">Nuevo</Btn>}
          </div>
        </Card>

        <p style={{ color: '#7f8c8d', fontSize: '12px', margin: '0 0 8px' }}>{lotes.length} lote{lotes.length !== 1 ? 's' : ''}</p>
        {lotes.map(l => (
          <div key={l.id} onClick={() => seleccionar(l)}
            style={{
              background: selected?.id === l.id ? '#eaf4fb' : 'white',
              border: `2px solid ${selected?.id === l.id ? '#2980b9' : '#ecf0f1'}`,
              borderRadius: '8px', padding: '10px 14px', marginBottom: '8px',
              cursor: 'pointer',
            }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong style={{ fontSize: '13px' }}>{l.codigo}</strong>
              <span style={{
                background: estadoLoteColor[l.estado] || '#7f8c8d',
                color: 'white', borderRadius: '4px', padding: '1px 7px', fontSize: '11px',
              }}>{l.estado}</span>
            </div>
            <div style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '2px' }}>
              {l.varietal_nombre} {l.campaña} · {Math.round(l.litros_actuales || 0).toLocaleString('es-AR')} L
            </div>
          </div>
        ))}
      </div>

      {/* Panel derecho: detalle del lote seleccionado */}
      {selected ? (
        <div>
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h3 style={{ margin: '0 0 4px', color: '#2c3e50' }}>{selected.codigo}</h3>
                <p style={{ margin: '0', color: '#7f8c8d', fontSize: '13px' }}>
                  {selected.varietal_nombre} — {selected.tipo_vino_display} — Campaña {selected.campaña}
                </p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '22px', fontWeight: '800', color: '#2980b9' }}>
                  {Math.round(selected.litros_actuales || 0).toLocaleString('es-AR')} L
                </div>
                <div style={{ fontSize: '12px', color: '#7f8c8d' }}>
                  de {Math.round(selected.litros_iniciales || 0).toLocaleString('es-AR')} L iniciales
                </div>
              </div>
            </div>
            <div style={{ marginTop: '10px', background: '#f8f9fa', borderRadius: '6px', height: '8px', overflow: 'hidden' }}>
              <div style={{
                background: '#2980b9', height: '100%',
                width: `${selected.litros_iniciales > 0 ? Math.min(100, (selected.litros_actuales / selected.litros_iniciales) * 100) : 0}%`,
              }} />
            </div>
            <div style={{ fontSize: '11px', color: '#7f8c8d', marginTop: '3px' }}>
              Merma acumulada: {Math.round(selected.merma_total || 0).toLocaleString('es-AR')} L
            </div>
          </Card>

          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            {['ops', 'analisis'].map(t => (
              <Btn key={t} onClick={() => setTab2(t)} color={tab2 === t ? '#2c3e50' : '#7f8c8d'} small>
                {t === 'ops' ? '⚗️ Operaciones' : '🔬 Análisis'}
              </Btn>
            ))}
          </div>

          {tab2 === 'ops' && (
            <Card>
              <h4 style={{ margin: '0 0 12px' }}>Operaciones enológicas</h4>
              {ops.length === 0 ? (
                <p style={{ color: '#7f8c8d', fontSize: '13px' }}>Sin operaciones registradas</p>
              ) : ops.map(op => (
                <div key={op.id} style={{
                  borderBottom: '1px solid #ecf0f1', paddingBottom: '8px', marginBottom: '8px',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                    <strong>{op.tipo_display}</strong>
                    <span style={{ color: '#7f8c8d' }}>{op.fecha?.slice(0, 10)}</span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#7f8c8d' }}>{op.descripcion}</div>
                  {op.insumo_nombre && (
                    <div style={{ fontSize: '12px', color: '#8e44ad' }}>
                      {op.insumo_nombre}: {op.cantidad_insumo} {op.unidad_insumo}
                    </div>
                  )}
                  {op.densidad && <div style={{ fontSize: '12px', color: '#e67e22' }}>
                    Densidad: {op.densidad} | °real: {op.grado_real}% | T°: {op.temperatura}°C
                  </div>}
                </div>
              ))}
            </Card>
          )}

          {tab2 === 'analisis' && (
            <Card>
              <h4 style={{ margin: '0 0 12px' }}>Análisis de laboratorio</h4>
              {analisis.length === 0 ? (
                <p style={{ color: '#7f8c8d', fontSize: '13px' }}>Sin análisis registrados</p>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                    <thead>
                      <tr style={{ background: '#f8f9fa' }}>
                        {['Fecha', 'Origen', '°Alc', 'Acid.T', 'Acid.V', 'pH', 'Az.Res', 'SO2L', 'SO2T', 'Estado'].map(h => (
                          <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: '#7f8c8d' }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {analisis.map(a => (
                        <tr key={a.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                          <td style={{ padding: '5px 8px' }}>{a.fecha}</td>
                          <td style={{ padding: '5px 8px' }}>{a.origen}</td>
                          <td style={{ padding: '5px 8px' }}>{a.grado_alcohol ?? '—'}</td>
                          <td style={{ padding: '5px 8px' }}>{a.acidez_total ?? '—'}</td>
                          <td style={{ padding: '5px 8px' }}>{a.acidez_volatil ?? '—'}</td>
                          <td style={{ padding: '5px 8px' }}>{a.ph ?? '—'}</td>
                          <td style={{ padding: '5px 8px' }}>{a.azucar_residual ?? '—'}</td>
                          <td style={{ padding: '5px 8px' }}>{a.so2_libre ?? '—'}</td>
                          <td style={{ padding: '5px 8px' }}>{a.so2_total ?? '—'}</td>
                          <td style={{ padding: '5px 8px' }}>
                            {a.aprobado === null ? '⏳' : a.aprobado ? '✅' : '❌'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          )}
        </div>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '200px', color: '#bdc3c7', fontSize: '15px' }}>
          ← Seleccioná un lote para ver su detalle
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// MAPA DE DEPÓSITOS
// ─────────────────────────────────────────────────────────────────────────────
function DepositosTab() {
  const [recipientes, setRecipientes] = useState([])
  const [form, setForm]   = useState({})
  const [msg, setMsg]     = useState('')
  const [showForm, setShowForm] = useState(false)

  useEffect(() => { api('recipientes/').then(r => setRecipientes(Array.isArray(r?.data) ? r.data : [])) }, [])

  const setF = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const guardar = async () => {
    const r = await api('recipientes/', 'POST', form)
    if (r.ok) {
      setMsg('✅ Guardado'); setForm({}); setShowForm(false)
      api('recipientes/').then(r2 => setRecipientes(Array.isArray(r2?.data) ? r2.data : []))
    } else setMsg('❌ ' + r.msg)
  }

  const tipos = [
    { value: 'TA', label: 'Tanque acero' }, { value: 'PC', label: 'Pileta cemento' },
    { value: 'TR', label: 'Tanque roble' }, { value: 'BA', label: 'Barrica' },
    { value: 'TI', label: 'Tinaja' }, { value: 'OT', label: 'Otro' },
  ]
  const sectores = [...new Set(recipientes.map(r => r.sector).filter(Boolean))]

  return (
    <div>
      {msg && <div style={{ background: '#ecf0f1', padding: '8px 12px', borderRadius: '6px', marginBottom: '12px', fontSize: '13px' }}>{msg}</div>}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <p style={{ margin: 0, color: '#7f8c8d', fontSize: '13px' }}>
          {recipientes.length} recipientes ·{' '}
          <span style={{ color: '#27ae60' }}>{recipientes.filter(r => r.estado === 'LI').length} libres</span> ·{' '}
          <span style={{ color: '#e67e22' }}>{recipientes.filter(r => r.estado === 'OC').length} ocupados</span>
        </p>
        <Btn onClick={() => setShowForm(!showForm)} color="#2980b9">+ Nuevo recipiente</Btn>
      </div>

      {showForm && (
        <Card>
          <h4 style={{ margin: '0 0 14px' }}>Nuevo recipiente</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
            <Input label="Código *" value={form.codigo} onChange={v => setF('codigo', v)} placeholder="T-001" />
            <Input label="Nombre *" value={form.nombre} onChange={v => setF('nombre', v)} placeholder="Tanque 1 Malbec" />
            <Select label="Tipo" value={form.tipo} onChange={v => setF('tipo', v)} options={tipos} />
            <Input label="Capacidad (L) *" value={form.capacidad_litros} onChange={v => setF('capacidad_litros', v)} type="number" />
            <Input label="Sector" value={form.sector} onChange={v => setF('sector', v)} placeholder="Nave A" />
            <Input label="Fila" value={form.fila} onChange={v => setF('fila', v)} type="number" />
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Btn onClick={guardar} color="#27ae60">Guardar</Btn>
            <Btn onClick={() => setShowForm(false)} color="#7f8c8d">Cancelar</Btn>
          </div>
        </Card>
      )}

      {/* Agrupado por sector */}
      {(sectores.length > 0 ? sectores : ['']).map(sector => (
        <div key={sector || 'sin-sector'} style={{ marginBottom: '20px' }}>
          <h4 style={{ color: '#2c3e50', borderBottom: '2px solid #ecf0f1', paddingBottom: '6px', margin: '0 0 12px' }}>
            {sector || 'Sin sector asignado'}
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '10px' }}>
            {recipientes.filter(r => r.sector === sector || (!r.sector && !sector)).map(r => (
              <div key={r.id} style={{
                background: estadoRecColor[r.estado] || '#7f8c8d',
                borderRadius: '8px', padding: '12px', color: 'white',
                cursor: 'pointer',
              }} onClick={() => setForm(r)}>
                <div style={{ fontWeight: '700', fontSize: '14px' }}>{r.codigo}</div>
                <div style={{ fontSize: '11px', opacity: .85 }}>{r.nombre}</div>
                <div style={{ fontSize: '13px', fontWeight: '600', marginTop: '4px' }}>
                  {r.capacidad_litros.toLocaleString('es-AR')} L
                </div>
                <div style={{ fontSize: '11px', marginTop: '2px', opacity: .9 }}>{r.estado_display}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// BARRICAS
// ─────────────────────────────────────────────────────────────────────────────
function BarricasTab({ lotes = [] }) {
  const safeLotes = Array.isArray(lotes) ? lotes : []
  const [barricas, setBarricas] = useState([])
  const [form, setForm]   = useState({})
  const [msg, setMsg]     = useState('')
  const [showForm, setShowForm] = useState(false)
  const [filEst, setFilEst] = useState('')

  useEffect(() => {
    api('barricas/').then(r => setBarricas(Array.isArray(r?.data) ? r.data : []))
  }, [])

  const setF = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const guardar = async () => {
    const r = await api('barricas/', 'POST', form)
    if (r.ok) {
      setMsg('✅ Barrica guardada'); setForm({}); setShowForm(false)
      api('barricas/').then(r2 => setBarricas(Array.isArray(r2?.data) ? r2.data : []))
    } else setMsg('❌ ' + r.msg)
  }

  const maderas  = [{ value: 'FRA', label: 'Francés' }, { value: 'AME', label: 'Americano' }, { value: 'HUN', label: 'Húngaro' }]
  const tostados = [{ value: 'L', label: 'Ligero' }, { value: 'M', label: 'Medio' }, { value: 'MO', label: 'Medio+' }, { value: 'F', label: 'Fuerte' }]
  const estados  = [{ value: 'LI', label: 'Libre' }, { value: 'OC', label: 'Ocupada' }, { value: 'LA', label: 'En limpieza' }, { value: 'BA', label: 'Baja' }]

  const barricasFiltradas = filEst ? barricas.filter(b => b.estado === filEst) : barricas
  const pct = (b) => b.vida_util_usos ? Math.round((b.cantidad_usos / b.vida_util_usos) * 100) : 0

  return (
    <div>
      {msg && <div style={{ background: '#ecf0f1', padding: '8px 12px', borderRadius: '6px', marginBottom: '12px', fontSize: '13px' }}>{msg}</div>}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          {[{ v: '', l: `Todas (${barricas.length})` }, { v: 'LI', l: '🟢 Libres' }, { v: 'OC', l: '🟡 Ocupadas' }].map(f => (
            <Btn key={f.v} onClick={() => setFilEst(f.v)} color={filEst === f.v ? '#2c3e50' : '#7f8c8d'} small>{f.l}</Btn>
          ))}
        </div>
        <Btn onClick={() => setShowForm(!showForm)} color="#8e44ad">+ Nueva barrica</Btn>
      </div>

      {showForm && (
        <Card>
          <h4 style={{ margin: '0 0 14px' }}>Alta de barrica</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
            <Input label="Número *" value={form.numero} onChange={v => setF('numero', v)} placeholder="B-001" />
            <Input label="Capacidad (L)" value={form.capacidad_litros} onChange={v => setF('capacidad_litros', v)} type="number" placeholder="225" />
            <Select label="Madera" value={form.madera} onChange={v => setF('madera', v)} options={maderas} />
            <Select label="Tostado" value={form.tostado} onChange={v => setF('tostado', v)} options={tostados} />
            <Input label="Tonelero / Bodeguero" value={form.tonelero} onChange={v => setF('tonelero', v)} />
            <Input label="Año de compra" value={form.anio_compra} onChange={v => setF('anio_compra', v)} type="number" />
            <Input label="Vida útil (usos)" value={form.vida_util_usos} onChange={v => setF('vida_util_usos', v)} type="number" placeholder="4" />
            <Input label="Costo de compra" value={form.costo_compra} onChange={v => setF('costo_compra', v)} type="number" />
            <Input label="Sector / Nave" value={form.sector} onChange={v => setF('sector', v)} />
            <Input label="Fila" value={form.fila} onChange={v => setF('fila', v)} type="number" />
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Btn onClick={guardar} color="#27ae60">Guardar</Btn>
            <Btn onClick={() => setShowForm(false)} color="#7f8c8d">Cancelar</Btn>
          </div>
        </Card>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '10px' }}>
        {barricasFiltradas.map(b => {
          const v = pct(b)
          const vidaColor = v < 50 ? '#27ae60' : v < 80 ? '#e67e22' : '#c0392b'
          return (
            <div key={b.id} style={{
              background: 'white', border: `2px solid ${estadoRecColor[b.estado] || '#ddd'}`,
              borderRadius: '8px', padding: '12px',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <strong style={{ fontSize: '14px' }}>{b.numero}</strong>
                <span style={{
                  background: estadoRecColor[b.estado], color: 'white',
                  borderRadius: '4px', padding: '1px 7px', fontSize: '11px',
                }}>{b.estado_display}</span>
              </div>
              <div style={{ fontSize: '12px', color: '#7f8c8d', margin: '4px 0' }}>
                {b.madera_display} · {b.tostado_display} · {b.capacidad_litros} L
              </div>
              <div style={{ fontSize: '12px', color: '#7f8c8d' }}>
                Usos: {b.cantidad_usos}/{b.vida_util_usos}
              </div>
              <div style={{ background: '#ecf0f1', borderRadius: '4px', height: '6px', marginTop: '6px', overflow: 'hidden' }}>
                <div style={{ width: `${Math.min(100, v)}%`, height: '100%', background: vidaColor }} />
              </div>
              <div style={{ fontSize: '11px', color: vidaColor, marginTop: '2px' }}>{v}% vida útil consumida</div>
            </div>
          )
        })}
        {barricasFiltradas.length === 0 && (
          <p style={{ gridColumn: '1/-1', color: '#7f8c8d', textAlign: 'center', padding: '20px' }}>Sin barricas</p>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// EMBOTELLADO
// ─────────────────────────────────────────────────────────────────────────────
function EmbotelladoTab({ lotes = [] }) {
  const safeLotes = Array.isArray(lotes) ? lotes : []
  const [ordenes, setOrdenes] = useState([])
  const [form, setForm]   = useState({})
  const [confirm, setConfirm] = useState(null)
  const [msg, setMsg]     = useState('')

  useEffect(() => { api('embotellado/').then(r => setOrdenes(Array.isArray(r?.data) ? r.data : [])) }, [])
  const setF = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const guardar = async () => {
    const r = await api('embotellado/', 'POST', form)
    if (r.ok) {
      setMsg('✅ ' + r.msg); setForm({})
      api('embotellado/').then(r2 => setOrdenes(Array.isArray(r2?.data) ? r2.data : []))
    } else setMsg('❌ ' + r.msg)
  }

  const confirmarEmbotellado = async () => {
    const r = await api('embotellado/confirmar/', 'POST', {
      orden_id: confirm.id,
      botellas_real: confirm.botellas_real,
      botellas_merma: confirm.botellas_merma || 0,
      fecha_real: confirm.fecha_real || new Date().toISOString().slice(0, 10),
    })
    if (r.ok) {
      setMsg('✅ ' + r.msg); setConfirm(null)
      api('embotellado/').then(r2 => setOrdenes(Array.isArray(r2?.data) ? r2.data : []))
    } else setMsg('❌ ' + r.msg)
  }

  const estadoColor = { PL: '#e67e22', EN: '#3498db', CO: '#27ae60', AN: '#c0392b' }
  const formatos = ['375', '750', '1500', '3000', 'BIB', 'OTR'].map(f => ({ value: f, label: f + (f === '750' ? ' ml (std)' : f === '375' ? ' ml' : f === '1500' ? ' L' : '') }))

  return (
    <div>
      {msg && <div style={{ background: '#ecf0f1', padding: '8px 12px', borderRadius: '6px', marginBottom: '12px', fontSize: '13px' }}>{msg}</div>}

      {confirm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)', zIndex: 900, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: 'white', borderRadius: '10px', padding: '24px', width: '380px' }}>
            <h3 style={{ margin: '0 0 16px', color: '#2c3e50' }}>Confirmar embotellado</h3>
            <p style={{ fontSize: '13px', color: '#7f8c8d', margin: '0 0 14px' }}>
              Orden #{confirm.id} — {confirm.lote_codigo} — {confirm.formato} ml
            </p>
            <Input label="Botellas reales" value={confirm.botellas_real} type="number"
              onChange={v => setConfirm(c => ({ ...c, botellas_real: v }))} />
            <Input label="Botellas merma/rotas" value={confirm.botellas_merma} type="number"
              onChange={v => setConfirm(c => ({ ...c, botellas_merma: v }))} />
            <Input label="Fecha real" value={confirm.fecha_real} type="date"
              onChange={v => setConfirm(c => ({ ...c, fecha_real: v }))} />
            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              <Btn onClick={confirmarEmbotellado} color="#27ae60">Confirmar</Btn>
              <Btn onClick={() => setConfirm(null)} color="#7f8c8d">Cancelar</Btn>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '16px' }}>
        <Card>
          <h4 style={{ margin: '0 0 14px' }}>Nueva orden de embotellado</h4>
          <Select label="Lote *" value={form.lote_id} onChange={v => setF('lote_id', v)}
            options={safeLotes.filter(l => ['LI', 'EP', 'EB'].includes(l.estado)).map(l => ({
              value: l.id, label: `${l.codigo} (${Math.round(l.litros_actuales)} L)`,
            }))} />
          <Select label="Formato" value={form.formato} onChange={v => setF('formato', v)} options={formatos} />
          <Input label="Botellas planificadas *" value={form.botellas_plan} onChange={v => setF('botellas_plan', v)} type="number" />
          <Input label="Fecha planificada" value={form.fecha_plan} onChange={v => setF('fecha_plan', v)} type="date" />
          <Input label="Cód. artículo PT (ERP)" value={form.cod_art_pt} onChange={v => setF('cod_art_pt', v)} placeholder="VIN-MAL-750-24" />
          <Input label="N° RNOE" value={form.nro_rnoe} onChange={v => setF('nro_rnoe', v)} />
          <Input label="Cód. botella" value={form.cod_botella} onChange={v => setF('cod_botella', v)} />
          <Input label="Cód. corcho" value={form.cod_corcho} onChange={v => setF('cod_corcho', v)} />
          <Input label="Cód. etiqueta" value={form.cod_etiqueta} onChange={v => setF('cod_etiqueta', v)} />
          <Btn onClick={guardar} color="#e74c3c">Crear orden</Btn>
        </Card>

        <div>
          <p style={{ color: '#7f8c8d', fontSize: '13px', margin: '0 0 10px' }}>{ordenes.length} órdenes</p>
          {ordenes.map(o => (
            <div key={o.id} style={{
              background: 'white', border: '1px solid #ecf0f1', borderRadius: '8px',
              padding: '12px 16px', marginBottom: '10px',
              borderLeft: `4px solid ${estadoColor[o.estado] || '#ddd'}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <strong style={{ fontSize: '14px' }}>OE #{o.id} — {o.lote_codigo}</strong>
                  <span style={{
                    background: estadoColor[o.estado], color: 'white',
                    borderRadius: '4px', padding: '1px 8px', fontSize: '11px', marginLeft: '8px',
                  }}>{o.estado_display}</span>
                </div>
                {o.estado === 'PL' && (
                  <Btn onClick={() => setConfirm({ ...o, botellas_real: o.botellas_plan })}
                    color="#27ae60" small>✔ Confirmar</Btn>
                )}
              </div>
              <div style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '4px', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                <span>Formato: <strong>{o.formato} ml</strong></span>
                <span>Plan: <strong>{o.botellas_plan?.toLocaleString('es-AR')} bot.</strong></span>
                {o.botellas_real && <span>Real: <strong>{o.botellas_real?.toLocaleString('es-AR')} bot.</strong></span>}
                <span>~{o.litros_planificados?.toLocaleString('es-AR')} L</span>
                {o.fecha_plan && <span>Fecha: {o.fecha_plan}</span>}
                {o.nro_rnoe && <span>RNOE: {o.nro_rnoe}</span>}
              </div>
            </div>
          ))}
          {ordenes.length === 0 && (
            <p style={{ color: '#7f8c8d', textAlign: 'center', padding: '30px' }}>Sin órdenes de embotellado</p>
          )}
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// MÓDULO PRINCIPAL
// ─────────────────────────────────────────────────────────────────────────────
const TABS = [
  { id: 'dashboard',    label: '📊 Dashboard' },
  { id: 'vinedo',      label: '🌿 Viñedo' },
  { id: 'recepcion',   label: '🏗️ Recepción' },
  { id: 'elaboracion', label: '⚗️ Elaboración' },
  { id: 'lotes',       label: '🧪 Lotes' },
  { id: 'depositos',   label: '🗄️ Depósitos' },
  { id: 'barricas',    label: '🛢 Barricas' },
  { id: 'calidad',     label: '🔬 Calidad' },
  { id: 'embotellado', label: '🍾 Embotellado' },
  { id: 'costos',      label: '💰 Costos' },
  { id: 'trazabilidad',label: '🔗 Trazabilidad' },
  { id: 'fiscal',      label: '📋 Fiscal/INV' },
  { id: 'fermentacion',label: '🌡️ Fermentación' },
  { id: 'cata',        label: '🍷 Cata & SO₂' },
]

export default function ModuloBodega() {
  const [tab, setTab]       = useState('dashboard')
  const [varietales, setVarietales] = useState([])
  const [recipientes, setRecipientes] = useState([])
  const [lotes, setLotes]   = useState([])

  useEffect(() => {
    api('varietales/').then(r => setVarietales(Array.isArray(r?.data) ? r.data : []))
    api('recipientes/').then(r => setRecipientes(Array.isArray(r?.data) ? r.data : []))
    api('lotes/').then(r => setLotes(Array.isArray(r?.data) ? r.data : []))
  }, [])

  const tabStyle = (id) => ({
    padding: '9px 18px', border: 'none', cursor: 'pointer', fontWeight: '600',
    fontSize: '13px', borderBottom: tab === id ? '3px solid #8e44ad' : '3px solid transparent',
    background: tab === id ? '#f8f4ff' : 'white',
    color: tab === id ? '#8e44ad' : '#7f8c8d',
    transition: 'all .15s',
  })

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ background: 'linear-gradient(135deg, #6c3483, #8e44ad)', borderRadius: '10px', padding: '20px 28px', marginBottom: '20px', color: 'white' }}>
        <h2 style={{ margin: '0 0 4px', fontSize: '22px', fontWeight: '800' }}>🍷 Módulo Bodega</h2>
        <p style={{ margin: 0, opacity: .85, fontSize: '13px' }}>
          Gestión vitivinícola — De la viña a la botella · Mendoza, Argentina
        </p>
      </div>

      {/* Tabs */}
      <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 1px 4px rgba(0,0,0,.08)', marginBottom: '20px', display: 'flex', overflowX: 'auto' }}>
        {TABS.map(t => (
          <button key={t.id} style={tabStyle(t.id)} onClick={() => setTab(t.id)}>{t.label}</button>
        ))}
      </div>

      {/* Contenido */}
      {tab === 'dashboard'    && <DashboardBodega />}
      {tab === 'vinedo'       && <VinedoTab varietales={varietales} />}
      {tab === 'recepcion'    && <RecepcionTab varietales={varietales} />}
      {tab === 'elaboracion'  && <ElaboracionTab lotes={lotes} />}
      {tab === 'lotes'        && <LotesTab varietales={varietales} recipientes={recipientes} />}
      {tab === 'depositos'    && <DepositosTab />}
      {tab === 'barricas'     && <BarricasTab lotes={lotes} />}
      {tab === 'calidad'      && <CalidadTab lotes={lotes} varietales={varietales} />}
      {tab === 'embotellado'  && <EmbotelladoTab lotes={lotes} />}
      {tab === 'costos'       && <CostosTab lotes={lotes} />}
      {tab === 'trazabilidad' && <TrazabilidadTab lotes={lotes} />}
      {tab === 'fiscal'       && <FiscalTab lotes={lotes} varietales={varietales} />}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// VIÑEDO
// ─────────────────────────────────────────────────────────────────────────────
function VinedoTab({ varietales = [] }) {
  const [parcelas, setParcelas]   = useState([])
  const [labores, setLabores]     = useState([])
  const [tratos, setTratos]       = useState([])
  const [contratos, setContratos] = useState([])
  const [liqUva, setLiqUva]       = useState([])
  const [selected, setSelected]   = useState(null)
  const [sub, setSub]             = useState('labores')
  const [form, setForm]           = useState({})
  const [formParcela, setFormParcela] = useState({ tipo: 'P' })
  const [showFormParcela, setShowFormParcela] = useState(false)
  const [msg, setMsg]             = useState('')
  const campaña = new Date().getFullYear()

  const recargarParcelas = () =>
    api('parcelas/').then(r => setParcelas(Array.isArray(r?.data) ? r.data : []))

  useEffect(() => {
    recargarParcelas()
    api('contratos-uva/').then(r => setContratos(Array.isArray(r?.data) ? r.data : []))
    api(`liquidaciones-uva/?campaña=${campaña}`).then(r => setLiqUva(Array.isArray(r?.data) ? r.data : []))
  }, [])

  const seleccionar = (p) => {
    setSelected(p)
    setShowFormParcela(false)
    api(`labores/?parcela_id=${p.id}&campaña=${campaña}`).then(r => setLabores(Array.isArray(r?.data) ? r.data : []))
    api(`tratamientos/?parcela_id=${p.id}&campaña=${campaña}`).then(r => setTratos(Array.isArray(r?.data) ? r.data : []))
  }

  const setF  = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const setFP = (k, v) => setFormParcela(f => ({ ...f, [k]: v }))

  const guardarParcela = async () => {
    if (!formParcela.nombre)    return setMsg('❌ El nombre es obligatorio')
    if (!formParcela.varietal)  return setMsg('❌ Seleccioná un varietal')
    if (!formParcela.superficie_ha) return setMsg('❌ Ingresá la superficie')
    const r = await api('parcelas/', 'POST', { ...formParcela, usuario: 'admin' })
    if (r.ok) {
      setMsg('✅ Parcela creada')
      setFormParcela({ tipo: 'P' })
      setShowFormParcela(false)
      recargarParcelas()
    } else setMsg('❌ ' + r.msg)
  }

  const guardarLabor = async () => {
    const r = await api('labores/', 'POST', { ...form, parcela_id: selected?.id, campaña, usuario: 'admin' })
    if (r.ok) {
      setMsg('✅ Labor registrada'); setForm({})
      api(`labores/?parcela_id=${selected.id}&campaña=${campaña}`).then(r2 => setLabores(Array.isArray(r2?.data) ? r2.data : []))
    } else setMsg('❌ ' + r.msg)
  }

  const tiposLabor = [
    { value: 'POD', label: 'Poda' }, { value: 'DES', label: 'Desbrote' },
    { value: 'VEV', label: 'Vendimia en verde' }, { value: 'COS', label: 'Cosecha' },
    { value: 'RIE', label: 'Riego' }, { value: 'FER', label: 'Fertilización' },
    { value: 'LAB', label: 'Laboreo de suelo' }, { value: 'OTR', label: 'Otra' },
  ]

  const tiposParcela = [{ value: 'P', label: '🏠 Propia' }, { value: 'T', label: '🤝 Terceros' }]
  const coloresVarietal = { T: '#8e44ad', B: '#f39c12', R: '#e74c3c' }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '16px' }}>
      {/* Lista de parcelas + formulario de alta */}
      <div>
        {msg && (
          <div style={{
            background: msg.startsWith('✅') ? '#EAF3DE' : '#FCEBEB',
            color: msg.startsWith('✅') ? '#27500A' : '#A32D2D',
            padding: '8px 12px', borderRadius: '6px', marginBottom: '10px', fontSize: '13px',
          }}>{msg}</div>
        )}

        {/* Botón nueva parcela */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '12px', margin: 0 }}>
            {parcelas.length} parcela{parcelas.length !== 1 ? 's' : ''}
          </p>
          <Btn onClick={() => { setShowFormParcela(!showFormParcela); setSelected(null) }}
            color={showFormParcela ? '#7f8c8d' : '#27ae60'} small>
            {showFormParcela ? 'Cancelar' : '+ Nueva parcela'}
          </Btn>
        </div>

        {/* Formulario inline de alta de parcela */}
        {showFormParcela && (
          <div style={{
            background: 'var(--color-background-primary)',
            border: '1.5px solid #27ae60',
            borderRadius: '8px', padding: '14px', marginBottom: '12px',
          }}>
            <p style={{ margin: '0 0 12px', fontSize: '13px', fontWeight: '500', color: '#27ae60' }}>
              Nueva parcela
            </p>
            <Input label="Nombre *" value={formParcela.nombre} onChange={v => setFP('nombre', v)}
              placeholder="Ej: Cuartel 3 Norte" />
            <Select label="Varietal *" value={formParcela.varietal} onChange={v => setFP('varietal', v)}
              options={varietales.map(v => ({ value: v.codigo, label: `${v.nombre} (${v.color === 'T' ? 'Tinto' : v.color === 'B' ? 'Blanco' : 'Rosado'})` }))} />
            <Select label="Tipo" value={formParcela.tipo} onChange={v => setFP('tipo', v)} options={tiposParcela} />
            <Input label="Superficie (ha) *" value={formParcela.superficie_ha}
              onChange={v => setFP('superficie_ha', v)} type="number" placeholder="2.5" />
            <Input label="Finca" value={formParcela.finca} onChange={v => setFP('finca', v)}
              placeholder="Ej: Finca Los Álamos" />
            <Input label="Zona / DOC" value={formParcela.zona} onChange={v => setFP('zona', v)}
              placeholder="Ej: Luján de Cuyo, Valle de Uco" />
            <Input label="Año de plantación" value={formParcela.anio_plantacion}
              onChange={v => setFP('anio_plantacion', v)} type="number" placeholder="1998" />
            <Input label="Portainjerto" value={formParcela.portainjerto}
              onChange={v => setFP('portainjerto', v)} placeholder="Ej: 110 Richter, SO4" />
            <Input label="Altitud (msnm)" value={formParcela.altitud_msnm}
              onChange={v => setFP('altitud_msnm', v)} type="number" placeholder="900" />
            {formParcela.tipo === 'T' && (
              <Input label="Código proveedor (viñatero)" value={formParcela.cod_prov}
                onChange={v => setFP('cod_prov', v)} type="number" placeholder="ID del proveedor en ERP" />
            )}
            <Btn onClick={guardarParcela} color="#27ae60">Guardar parcela</Btn>
          </div>
        )}

        {/* Lista de parcelas */}
        {parcelas.map(p => (
          <div key={p.id} onClick={() => seleccionar(p)}
            style={{
              background: selected?.id === p.id ? '#eaf6ee' : 'var(--color-background-primary)',
              border: `2px solid ${selected?.id === p.id ? '#27ae60' : 'var(--color-border-tertiary)'}`,
              borderRadius: '8px', padding: '10px 14px', marginBottom: '8px', cursor: 'pointer',
              transition: 'border-color 0.15s',
            }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <strong style={{ fontSize: '13px' }}>{p.nombre}</strong>
              <span style={{
                background: coloresVarietal[p.varietal?.slice(-1)] || '#7f8c8d',
                color: 'white', borderRadius: '4px', padding: '1px 6px', fontSize: '10px',
              }}>
                {p.tipo === 'P' ? 'Propia' : 'Terceros'}
              </span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '3px' }}>
              {p.varietal_nombre} · {p.superficie_ha} ha
            </div>
            {(p.zona || p.finca) && (
              <div style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', marginTop: '2px' }}>
                {[p.finca, p.zona].filter(Boolean).join(' · ')}
              </div>
            )}
          </div>
        ))}

        {parcelas.length === 0 && !showFormParcela && (
          <div style={{
            textAlign: 'center', padding: '24px 16px',
            border: '1.5px dashed var(--color-border-secondary)',
            borderRadius: '8px', color: 'var(--color-text-tertiary)',
          }}>
            <div style={{ fontSize: '28px', marginBottom: '8px' }}>🌿</div>
            <p style={{ margin: '0 0 10px', fontSize: '13px' }}>Sin parcelas registradas</p>
            <Btn onClick={() => setShowFormParcela(true)} color="#27ae60" small>+ Crear primera parcela</Btn>
          </div>
        )}
      </div>

      {/* Detalle parcela seleccionada */}
      {selected ? (
        <div>
          <Card>
            <h3 style={{ margin: '0 0 4px', color: '#27ae60' }}>{selected.nombre}</h3>
            <p style={{ margin: 0, color: '#7f8c8d', fontSize: '13px' }}>
              {selected.varietal_nombre} · {selected.superficie_ha} ha · Campaña {campaña}
            </p>
          </Card>

          {msg && <div style={{ background: '#ecf0f1', padding: '8px 12px', borderRadius: '6px', marginBottom: '10px', fontSize: '13px' }}>{msg}</div>}

          <div style={{ display: 'flex', gap: '8px', marginBottom: '14px' }}>
            {['labores', 'tratamientos'].map(s => (
              <Btn key={s} onClick={() => setSub(s)} color={sub === s ? '#27ae60' : '#7f8c8d'} small>
                {s === 'labores' ? '🌱 Labores culturales' : '🧪 Tratamientos fitosanitarios'}
              </Btn>
            ))}
          </div>

          {sub === 'labores' && (
            <>
              <Card>
                <h4 style={{ margin: '0 0 12px' }}>Registrar labor</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 14px' }}>
                  <Select label="Tipo *" value={form.tipo} onChange={v => setF('tipo', v)} options={tiposLabor} />
                  <Input label="Fecha inicio *" value={form.fecha_inicio} onChange={v => setF('fecha_inicio', v)} type="date" />
                  <Input label="Fecha fin" value={form.fecha_fin} onChange={v => setF('fecha_fin', v)} type="date" />
                  <Input label="Responsable" value={form.responsable} onChange={v => setF('responsable', v)} />
                  <Input label="Jornales" value={form.jornales} onChange={v => setF('jornales', v)} type="number" />
                  <Input label="Costo jornal $" value={form.costo_jornal} onChange={v => setF('costo_jornal', v)} type="number" />
                  <Input label="Costo maquinaria $" value={form.costo_maquinaria} onChange={v => setF('costo_maquinaria', v)} type="number" />
                  <Input label="Costo insumos $" value={form.costo_insumos} onChange={v => setF('costo_insumos', v)} type="number" />
                </div>
                {form.jornales && form.costo_jornal && (
                  <div style={{ background: '#eaf6ee', padding: '8px 12px', borderRadius: '6px', fontSize: '13px', marginBottom: '10px' }}>
                    <strong>Costo total estimado:</strong> ${(
                      parseFloat(form.jornales || 0) * parseFloat(form.costo_jornal || 0)
                      + parseFloat(form.costo_maquinaria || 0)
                      + parseFloat(form.costo_insumos || 0)
                    ).toLocaleString('es-AR')}
                  </div>
                )}
                <Btn onClick={guardarLabor} color="#27ae60">Guardar labor</Btn>
              </Card>
              <Card>
                <h4 style={{ margin: '0 0 10px' }}>Labores registradas — Campaña {campaña}</h4>
                {labores.length === 0 ? <p style={{ color: '#7f8c8d', fontSize: '13px' }}>Sin labores este período</p> : (
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                    <thead>
                      <tr style={{ background: '#f8f9fa' }}>
                        {['Tipo', 'Fecha', 'Jornales', 'Costo total', 'Responsable'].map(h => (
                          <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: '#7f8c8d' }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {labores.map(l => (
                        <tr key={l.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                          <td style={{ padding: '5px 8px' }}><strong>{l.tipo_display}</strong></td>
                          <td style={{ padding: '5px 8px' }}>{l.fecha_inicio}</td>
                          <td style={{ padding: '5px 8px' }}>{l.jornales}</td>
                          <td style={{ padding: '5px 8px', color: '#27ae60', fontWeight: '700' }}>
                            ${parseFloat(l.costo_total || 0).toLocaleString('es-AR')}
                          </td>
                          <td style={{ padding: '5px 8px', color: '#7f8c8d' }}>{l.responsable || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </Card>
            </>
          )}

          {sub === 'tratamientos' && (
            <Card>
              <h4 style={{ margin: '0 0 10px' }}>Tratamientos fitosanitarios — Campaña {campaña}</h4>
              {tratos.length === 0 ? <p style={{ color: '#7f8c8d', fontSize: '13px' }}>Sin tratamientos registrados</p> : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ background: '#f8f9fa' }}>
                      {['Fecha', 'Producto', 'Dosis', 'Objetivo', 'Carencia', 'Fin carencia'].map(h => (
                        <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: '#7f8c8d' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tratos.map(t => (
                      <tr key={t.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                        <td style={{ padding: '5px 8px' }}>{t.fecha}</td>
                        <td style={{ padding: '5px 8px' }}><strong>{t.producto}</strong></td>
                        <td style={{ padding: '5px 8px' }}>{t.dosis_aplicada} {t.unidad}</td>
                        <td style={{ padding: '5px 8px', color: '#7f8c8d' }}>{t.objetivo || '—'}</td>
                        <td style={{ padding: '5px 8px' }}>{t.dias_carencia} días</td>
                        <td style={{ padding: '5px 8px', color: t.fecha_fin_carencia ? '#e74c3c' : '#27ae60' }}>
                          {t.fecha_fin_carencia || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Card>
          )}
        </div>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '200px', color: '#bdc3c7' }}>
          ← Seleccioná una parcela
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// ELABORACIÓN (órdenes + balance de masa)
// ─────────────────────────────────────────────────────────────────────────────
function ElaboracionTab({ lotes = [] }) {
  const safeLotes = Array.isArray(lotes) ? lotes : []
  const [ordenes, setOrdenes]   = useState([])
  const [balance, setBalance]   = useState(null)
  const [loteId, setLoteId]     = useState('')
  const [form, setForm]         = useState({})
  const [formBal, setFormBal]   = useState({})
  const [sub, setSub]           = useState('ordenes')
  const [msg, setMsg]           = useState('')

  useEffect(() => {
    api('ordenes-elaboracion/').then(r => setOrdenes(Array.isArray(r?.data) ? r.data : []))
  }, [])

  const setF  = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const setFB = (k, v) => setFormBal(f => ({ ...f, [k]: v }))

  const cargarBalance = (lid) => {
    setLoteId(lid)
    if (lid) api(`balance-masa/?lote_id=${lid}`).then(r => setBalance(r?.data || null))
  }

  const guardarOrden = async () => {
    const r = await api('ordenes-elaboracion/', 'POST', { ...form, usuario: 'admin' })
    if (r.ok) {
      setMsg('✅ Orden guardada'); setForm({})
      api('ordenes-elaboracion/').then(r2 => setOrdenes(Array.isArray(r2?.data) ? r2.data : []))
    } else setMsg('❌ ' + r.msg)
  }

  const guardarBalance = async () => {
    const r = await api('balance-masa/', 'POST', { ...formBal, lote_id: loteId, usuario: 'admin' })
    if (r.ok) {
      setMsg(`✅ Balance guardado — ${r.data?.rendimiento_lkg} L/kg`)
      cargarBalance(loteId)
    } else setMsg('❌ ' + r.msg)
  }

  const estadoColor = { PE: '#e67e22', EN: '#3498db', CO: '#27ae60', AN: '#c0392b' }

  return (
    <div>
      {msg && <div style={{ background: '#ecf0f1', padding: '8px 12px', borderRadius: '6px', marginBottom: '12px', fontSize: '13px' }}>{msg}</div>}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        {['ordenes', 'balance'].map(s => (
          <Btn key={s} onClick={() => setSub(s)} color={sub === s ? '#2c3e50' : '#7f8c8d'} small>
            {s === 'ordenes' ? '📋 Órdenes de elaboración' : '⚖️ Balance de masa'}
          </Btn>
        ))}
      </div>

      {sub === 'ordenes' && (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '16px' }}>
          <Card>
            <h4 style={{ margin: '0 0 12px' }}>Nueva orden</h4>
            <Select label="Lote *" value={form.lote_id} onChange={v => setF('lote_id', v)}
              options={safeLotes.filter(l => ['EB', 'CR'].includes(l.estado)).map(l => ({
                value: l.id, label: `${l.codigo} — ${l.varietal_nombre}`
              }))} />
            <Input label="Proceso *" value={form.proceso} onChange={v => setF('proceso', v)}
              placeholder="Ej: 2° trasiego post-FML" />
            <Input label="Fecha emisión *" value={form.fecha_emision} onChange={v => setF('fecha_emision', v)} type="date" />
            <Input label="Fecha ejecución" value={form.fecha_ejecucion} onChange={v => setF('fecha_ejecucion', v)} type="date" />
            <Input label="Responsable" value={form.responsable} onChange={v => setF('responsable', v)} />
            <div style={{ marginBottom: '10px' }}>
              <label style={{ fontSize: '12px', color: '#7f8c8d', display: 'block', marginBottom: '3px' }}>Instrucciones</label>
              <textarea value={form.instrucciones || ''} onChange={e => setF('instrucciones', e.target.value)}
                rows={3} style={{ width: '100%', padding: '7px 10px', border: '1px solid #ddd', borderRadius: '5px', fontSize: '13px', boxSizing: 'border-box', resize: 'vertical' }} />
            </div>
            <Btn onClick={guardarOrden} color="#e67e22">Crear orden</Btn>
          </Card>

          <div>
            {ordenes.map(o => (
              <div key={o.id} style={{
                background: 'white', border: `1px solid #ecf0f1`,
                borderLeft: `4px solid ${estadoColor[o.estado] || '#ddd'}`,
                borderRadius: '8px', padding: '12px 16px', marginBottom: '10px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <strong style={{ fontSize: '14px' }}>OE #{o.id}</strong>
                    <span style={{ background: estadoColor[o.estado], color: 'white', borderRadius: '4px', padding: '1px 8px', fontSize: '11px', marginLeft: '8px' }}>{o.estado_display}</span>
                  </div>
                  <span style={{ color: '#7f8c8d', fontSize: '12px' }}>{o.fecha_emision}</span>
                </div>
                <div style={{ fontWeight: '600', fontSize: '13px', margin: '4px 0 2px' }}>{o.proceso}</div>
                <div style={{ fontSize: '12px', color: '#7f8c8d' }}>
                  Lote: <strong>{o.lote_codigo}</strong>
                  {o.responsable && ` · Responsable: ${o.responsable}`}
                </div>
                {o.instrucciones && (
                  <div style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '4px', fontStyle: 'italic' }}>
                    {o.instrucciones.slice(0, 120)}{o.instrucciones.length > 120 ? '…' : ''}
                  </div>
                )}
              </div>
            ))}
            {ordenes.length === 0 && <p style={{ color: '#7f8c8d', textAlign: 'center', padding: '30px' }}>Sin órdenes de elaboración</p>}
          </div>
        </div>
      )}

      {sub === 'balance' && (
        <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '16px' }}>
          <Card>
            <h4 style={{ margin: '0 0 12px' }}>Balance de masa</h4>
            <Select label="Lote *" value={loteId} onChange={v => { setFB('lote_id', v); cargarBalance(v) }}
              options={safeLotes.map(l => ({ value: l.id, label: `${l.codigo} — ${l.varietal_nombre}` }))} />
            <Input label="Campaña *" value={formBal.campaña} onChange={v => setFB('campaña', v)} type="number" />
            <div style={{ background: '#f8f9fa', borderRadius: '6px', padding: '10px 12px', marginBottom: '10px' }}>
              <p style={{ fontSize: '11px', color: '#7f8c8d', margin: '0 0 8px', fontWeight: '700', textTransform: 'uppercase' }}>Entradas</p>
              <Input label="Kg uva total *" value={formBal.kg_uva_total} onChange={v => setFB('kg_uva_total', v)} type="number" small />
              <Input label="Kg uva propia" value={formBal.kg_uva_propia} onChange={v => setFB('kg_uva_propia', v)} type="number" small />
              <Input label="Kg uva comprada" value={formBal.kg_uva_comprada} onChange={v => setFB('kg_uva_comprada', v)} type="number" small />
            </div>
            <div style={{ background: '#f8f9fa', borderRadius: '6px', padding: '10px 12px', marginBottom: '10px' }}>
              <p style={{ fontSize: '11px', color: '#7f8c8d', margin: '0 0 8px', fontWeight: '700', textTransform: 'uppercase' }}>Masa sólida</p>
              <Input label="Kg escobajo" value={formBal.kg_escobajo} onChange={v => setFB('kg_escobajo', v)} type="number" small />
              <Input label="Kg orujo" value={formBal.kg_orujo} onChange={v => setFB('kg_orujo', v)} type="number" small />
              <Input label="Kg borras" value={formBal.kg_borras} onChange={v => setFB('kg_borras', v)} type="number" small />
            </div>
            <div style={{ background: '#f8f9fa', borderRadius: '6px', padding: '10px 12px', marginBottom: '10px' }}>
              <p style={{ fontSize: '11px', color: '#7f8c8d', margin: '0 0 8px', fontWeight: '700', textTransform: 'uppercase' }}>Litros obtenidos</p>
              <Input label="Litros mosto flor" value={formBal.litros_mosto_flor} onChange={v => setFB('litros_mosto_flor', v)} type="number" small />
              <Input label="Litros prensa" value={formBal.litros_prensa} onChange={v => setFB('litros_prensa', v)} type="number" small />
              <Input label="Litros totales *" value={formBal.litros_totales} onChange={v => setFB('litros_totales', v)} type="number" small />
            </div>
            <Input label="Fecha cierre *" value={formBal.fecha_cierre} onChange={v => setFB('fecha_cierre', v)} type="date" />
            {formBal.kg_uva_total && formBal.litros_totales && (
              <div style={{ background: '#eaf4fb', padding: '8px 12px', borderRadius: '6px', fontSize: '13px', marginBottom: '10px' }}>
                <strong>Rendimiento estimado:</strong>{' '}
                {(parseFloat(formBal.litros_totales) / parseFloat(formBal.kg_uva_total)).toFixed(3)} L/kg
              </div>
            )}
            <Btn onClick={guardarBalance} color="#2980b9">Guardar balance</Btn>
          </Card>

          {balance ? (
            <Card>
              <h4 style={{ margin: '0 0 14px', color: '#2c3e50' }}>Resultado del balance</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                {[
                  { label: 'Rendimiento', value: `${balance.rendimiento_lkg} L/kg`, color: '#2980b9' },
                  { label: 'Extracción', value: `${balance.porcentaje_extraccion}%`, color: '#27ae60' },
                  { label: 'Kg uva total', value: `${parseFloat(balance.kg_uva_total || 0).toLocaleString('es-AR')} kg`, color: '#e67e22' },
                  { label: 'Litros totales', value: `${parseFloat(balance.litros_totales || 0).toLocaleString('es-AR')} L`, color: '#8e44ad' },
                  { label: 'Escobajo + orujo', value: `${(parseFloat(balance.kg_escobajo || 0) + parseFloat(balance.kg_orujo || 0)).toLocaleString('es-AR')} kg`, color: '#7f8c8d' },
                  { label: 'Merma proceso', value: `${parseFloat(balance.litros_merma_proceso || 0).toLocaleString('es-AR')} L`, color: '#c0392b' },
                ].map(k => (
                  <div key={k.label} style={{ background: '#f8f9fa', borderRadius: '6px', padding: '10px 14px' }}>
                    <div style={{ fontSize: '11px', color: '#7f8c8d' }}>{k.label}</div>
                    <div style={{ fontSize: '20px', fontWeight: '800', color: k.color }}>{k.value}</div>
                  </div>
                ))}
              </div>
            </Card>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '200px', color: '#bdc3c7' }}>
              ← Seleccioná un lote para ver o cargar su balance
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// CALIDAD
// ─────────────────────────────────────────────────────────────────────────────
function CalidadTab({ lotes = [], varietales = [] }) {
  const safeLotes = Array.isArray(lotes) ? lotes : []
  const [fichas, setFichas] = useState([])
  const [ncs, setNcs]       = useState([])
  const [form, setForm]     = useState({})
  const [formNC, setFormNC] = useState({})
  const [sub, setSub]       = useState('fichas')
  const [msg, setMsg]       = useState('')

  useEffect(() => {
    api('fichas-producto/').then(r => setFichas(Array.isArray(r?.data) ? r.data : []))
    api('no-conformidades/').then(r => setNcs(Array.isArray(r?.data) ? r.data : []))
  }, [])

  const setF  = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const setFN = (k, v) => setFormNC(f => ({ ...f, [k]: v }))

  const guardarFicha = async () => {
    const r = await api('fichas-producto/', 'POST', { ...form, usuario: 'admin' })
    if (r.ok) {
      setMsg('✅ Ficha guardada'); setForm({})
      api('fichas-producto/').then(r2 => setFichas(Array.isArray(r2?.data) ? r2.data : []))
    } else setMsg('❌ ' + r.msg)
  }

  const guardarNC = async () => {
    const r = await api('no-conformidades/', 'POST', { ...formNC, usuario: 'admin' })
    if (r.ok) {
      setMsg('✅ NC registrada'); setFormNC({})
      api('no-conformidades/').then(r2 => setNcs(Array.isArray(r2?.data) ? r2.data : []))
    } else setMsg('❌ ' + r.msg)
  }

  const gravedadColor = { L: '#27ae60', M: '#e67e22', G: '#e74c3c', C: '#8e44ad' }
  const estadoNCColor = { AB: '#e74c3c', EN: '#e67e22', CE: '#27ae60', RE: '#8e44ad' }
  const tiposVino = [{ value: 'TI', label: 'Tinto' }, { value: 'BL', label: 'Blanco' }, { value: 'RO', label: 'Rosado' }, { value: 'ES', label: 'Espumante' }]
  const gravedades = [{ value: 'L', label: 'Leve' }, { value: 'M', label: 'Moderada' }, { value: 'G', label: 'Grave' }, { value: 'C', label: 'Crítica' }]
  const estadosNC = [{ value: 'AB', label: 'Abierta' }, { value: 'EN', label: 'En tratamiento' }, { value: 'CE', label: 'Cerrada' }]

  return (
    <div>
      {msg && <div style={{ background: '#ecf0f1', padding: '8px 12px', borderRadius: '6px', marginBottom: '12px', fontSize: '13px' }}>{msg}</div>}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        {['fichas', 'nc'].map(s => (
          <Btn key={s} onClick={() => setSub(s)} color={sub === s ? '#2c3e50' : '#7f8c8d'} small>
            {s === 'fichas' ? '📄 Fichas de producto' : '⚠️ No conformidades'}
          </Btn>
        ))}
      </div>

      {sub === 'fichas' && (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '16px' }}>
          <Card>
            <h4 style={{ margin: '0 0 12px' }}>Nueva ficha técnica</h4>
            <Input label="Código *" value={form.codigo} onChange={v => setF('codigo', v)} placeholder="FT-MAL-RSV" />
            <Input label="Nombre *" value={form.nombre} onChange={v => setF('nombre', v)} placeholder="Malbec Reserva" />
            <Select label="Varietal" value={form.varietal} onChange={v => setF('varietal', v)}
              options={varietales.map(v => ({ value: v.codigo, label: v.nombre }))} />
            <Select label="Tipo de vino" value={form.tipo_vino} onChange={v => setF('tipo_vino', v)} options={tiposVino} />
            <p style={{ fontSize: '11px', color: '#7f8c8d', fontWeight: '700', textTransform: 'uppercase', margin: '8px 0 6px' }}>Rangos analíticos</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 10px' }}>
              <Input label="Alcohol mín" value={form.alcohol_min} onChange={v => setF('alcohol_min', v)} type="number" small />
              <Input label="Alcohol máx" value={form.alcohol_max} onChange={v => setF('alcohol_max', v)} type="number" small />
              <Input label="pH mín" value={form.ph_min} onChange={v => setF('ph_min', v)} type="number" small />
              <Input label="pH máx" value={form.ph_max} onChange={v => setF('ph_max', v)} type="number" small />
              <Input label="SO₂ libre máx" value={form.so2_libre_max} onChange={v => setF('so2_libre_max', v)} type="number" small />
              <Input label="SO₂ total máx" value={form.so2_total_max} onChange={v => setF('so2_total_max', v)} type="number" small />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <label style={{ fontSize: '12px', color: '#7f8c8d', display: 'block', marginBottom: '3px' }}>Perfil sensorial</label>
              <textarea value={form.perfil_sensorial || ''} onChange={e => setF('perfil_sensorial', e.target.value)}
                rows={2} placeholder="Rojo rubí intenso, frutos negros, taninos sedosos..."
                style={{ width: '100%', padding: '7px', border: '1px solid #ddd', borderRadius: '5px', fontSize: '12px', boxSizing: 'border-box' }} />
            </div>
            <Btn onClick={guardarFicha} color="#16a085">Guardar ficha</Btn>
          </Card>
          <div>
            {fichas.map(f => (
              <div key={f.id} style={{ background: 'white', border: '1px solid #ecf0f1', borderRadius: '8px', padding: '12px 16px', marginBottom: '10px', borderLeft: '4px solid #16a085' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>{f.codigo} — {f.nombre}</strong>
                  <span style={{ color: '#7f8c8d', fontSize: '12px' }}>{f.varietal || '—'}</span>
                </div>
                {f.perfil_sensorial && <div style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '4px', fontStyle: 'italic' }}>{f.perfil_sensorial.slice(0, 100)}</div>}
                <div style={{ display: 'flex', gap: '12px', fontSize: '12px', marginTop: '6px', flexWrap: 'wrap' }}>
                  {f.alcohol_min && <span>🍷 {f.alcohol_min}–{f.alcohol_max}% alc.</span>}
                  {f.ph_min && <span>⚗️ pH {f.ph_min}–{f.ph_max}</span>}
                  {f.so2_total_max && <span>SO₂ ≤{f.so2_total_max} mg/L</span>}
                </div>
              </div>
            ))}
            {fichas.length === 0 && <p style={{ color: '#7f8c8d', textAlign: 'center', padding: '30px' }}>Sin fichas de producto</p>}
          </div>
        </div>
      )}

      {sub === 'nc' && (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '16px' }}>
          <Card>
            <h4 style={{ margin: '0 0 12px' }}>Registrar NC</h4>
            <Input label="Fecha *" value={formNC.fecha} onChange={v => setFN('fecha', v)} type="date" />
            <Input label="Origen *" value={formNC.origen} onChange={v => setFN('origen', v)} placeholder="Recepción / Lab / Elaboración" />
            <Select label="Gravedad" value={formNC.gravedad} onChange={v => setFN('gravedad', v)} options={gravedades} />
            <Select label="Lote afectado" value={formNC.lote_id} onChange={v => setFN('lote_id', v)}
              options={safeLotes.map(l => ({ value: l.id, label: `${l.codigo} — ${l.varietal_nombre}` }))} />
            <Input label="Responsable" value={formNC.responsable} onChange={v => setFN('responsable', v)} />
            <div style={{ marginBottom: '10px' }}>
              <label style={{ fontSize: '12px', color: '#7f8c8d', display: 'block', marginBottom: '3px' }}>Descripción *</label>
              <textarea value={formNC.descripcion || ''} onChange={e => setFN('descripcion', e.target.value)} rows={2}
                style={{ width: '100%', padding: '7px', border: '1px solid #ddd', borderRadius: '5px', fontSize: '12px', boxSizing: 'border-box' }} />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <label style={{ fontSize: '12px', color: '#7f8c8d', display: 'block', marginBottom: '3px' }}>Acción correctiva</label>
              <textarea value={formNC.accion_correctiva || ''} onChange={e => setFN('accion_correctiva', e.target.value)} rows={2}
                style={{ width: '100%', padding: '7px', border: '1px solid #ddd', borderRadius: '5px', fontSize: '12px', boxSizing: 'border-box' }} />
            </div>
            <Btn onClick={guardarNC} color="#e74c3c">Registrar NC</Btn>
          </Card>
          <div>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
              {['AB', 'EN', 'CE'].map(e => (
                <span key={e} style={{ background: estadoNCColor[e], color: 'white', borderRadius: '6px', padding: '4px 12px', fontSize: '12px', fontWeight: '700' }}>
                  {e === 'AB' ? 'Abiertas' : e === 'EN' ? 'En tratamiento' : 'Cerradas'}: {ncs.filter(n => n.estado === e).length}
                </span>
              ))}
            </div>
            {ncs.map(nc => (
              <div key={nc.id} style={{
                background: 'white', border: `1px solid #ecf0f1`,
                borderLeft: `4px solid ${gravedadColor[nc.gravedad] || '#ddd'}`,
                borderRadius: '8px', padding: '12px 16px', marginBottom: '10px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <strong>NC #{nc.id}</strong>
                    <span style={{ background: gravedadColor[nc.gravedad], color: 'white', borderRadius: '4px', padding: '1px 8px', fontSize: '11px', marginLeft: '6px' }}>{nc.gravedad_display}</span>
                    <span style={{ background: estadoNCColor[nc.estado], color: 'white', borderRadius: '4px', padding: '1px 8px', fontSize: '11px', marginLeft: '4px' }}>{nc.estado_display}</span>
                  </div>
                  <span style={{ color: '#7f8c8d', fontSize: '12px' }}>{nc.fecha}</span>
                </div>
                <div style={{ fontSize: '13px', margin: '4px 0 2px' }}>{nc.descripcion}</div>
                <div style={{ fontSize: '12px', color: '#7f8c8d' }}>Origen: {nc.origen}{nc.lote_codigo ? ` · Lote: ${nc.lote_codigo}` : ''}</div>
                {nc.accion_correctiva && <div style={{ fontSize: '12px', color: '#27ae60', marginTop: '4px' }}>✅ {nc.accion_correctiva.slice(0, 100)}</div>}
              </div>
            ))}
            {ncs.length === 0 && <p style={{ color: '#7f8c8d', textAlign: 'center', padding: '30px' }}>Sin no conformidades registradas</p>}
          </div>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// COSTOS
// ─────────────────────────────────────────────────────────────────────────────
function CostosTab({ lotes = [] }) {
  const safeLotes = Array.isArray(lotes) ? lotes : []
  const [resumen, setResumen]   = useState([])
  const [detalle, setDetalle]   = useState(null)
  const [loteId, setLoteId]     = useState('')
  const [form, setForm]         = useState({})
  const [msg, setMsg]           = useState('')

  useEffect(() => {
    api('costos/').then(r => setResumen(Array.isArray(r?.data) ? r.data : []))
  }, [])

  const setF = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const cargarDetalle = async (lid) => {
    setLoteId(lid)
    const r = await api(`costos/?lote_id=${lid}`)
    if (r.ok) setDetalle(r.data)
  }

  const actualizarCostos = async () => {
    const r = await api('costos/', 'POST', { ...form, lote_id: loteId, accion: 'actualizar_cabecera', usuario: 'admin' })
    if (r.ok) {
      setMsg(`✅ Recalculado — $${parseFloat(r.data?.costo_total_pt || 0).toLocaleString('es-AR')} / bot ${r.data?.costo_por_botella}`)
      cargarDetalle(loteId)
      api('costos/').then(r2 => setResumen(Array.isArray(r2?.data) ? r2.data : []))
    } else setMsg('❌ ' + r.msg)
  }

  const costoFields = [
    { key: 'costo_uva_propia', label: 'Uva propia $', color: '#27ae60' },
    { key: 'costo_uva_comprada', label: 'Uva comprada $', color: '#e67e22' },
    { key: 'costo_insumos_enologicos', label: 'Insumos enológicos $', color: '#3498db' },
    { key: 'costo_mano_obra_bodega', label: 'Mano de obra bodega $', color: '#9b59b6' },
    { key: 'costo_energia', label: 'Energía $', color: '#f39c12' },
    { key: 'costo_crianza_barricas', label: 'Crianza en barricas $', color: '#795548' },
    { key: 'costo_amortizacion_barrica', label: 'Amortización barricas $', color: '#607d8b' },
    { key: 'costo_gastos_indirectos', label: 'Gastos indirectos $', color: '#95a5a6' },
    { key: 'costo_materiales_emb', label: 'Materiales embotellado $', color: '#e74c3c' },
    { key: 'costo_mano_obra_emb', label: 'M.O. embotellado $', color: '#c0392b' },
  ]

  return (
    <div>
      {msg && <div style={{ background: '#ecf0f1', padding: '8px 12px', borderRadius: '6px', marginBottom: '12px', fontSize: '13px' }}>{msg}</div>}
      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '16px' }}>
        <div>
          <Card>
            <h4 style={{ margin: '0 0 12px' }}>Cargar costos por lote</h4>
            <Select label="Lote" value={loteId} onChange={v => cargarDetalle(v)}
              options={safeLotes.map(l => ({ value: l.id, label: `${l.codigo} — ${l.varietal_nombre}` }))} />
            {loteId && costoFields.map(f => (
              <Input key={f.key} label={f.label}
                value={form[f.key] ?? (detalle?.costo_lote?.[f.key] || '')}
                onChange={v => setF(f.key, v)} type="number" small />
            ))}
            {loteId && <Btn onClick={actualizarCostos} color="#16a085">Recalcular costos</Btn>}
          </Card>
        </div>

        <div>
          {detalle?.costo_lote && (
            <Card>
              <h4 style={{ margin: '0 0 14px' }}>Resumen — {detalle.costo_lote.lote_codigo}</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '10px', marginBottom: '16px' }}>
                {[
                  { label: 'Costo granel', value: detalle.costo_lote.costo_total_granel, color: '#2980b9', sub: `${detalle.costo_lote.costo_por_litro} $/L` },
                  { label: 'Costo PT total', value: detalle.costo_lote.costo_total_pt, color: '#8e44ad', sub: null },
                  { label: 'Costo por botella', value: detalle.costo_lote.costo_por_botella, color: '#27ae60', sub: '750 ml' },
                ].map(k => (
                  <div key={k.label} style={{ background: k.color, color: 'white', borderRadius: '8px', padding: '12px' }}>
                    <div style={{ fontSize: '11px', opacity: .85 }}>{k.label}</div>
                    <div style={{ fontSize: '20px', fontWeight: '800' }}>${parseFloat(k.value || 0).toLocaleString('es-AR')}</div>
                    {k.sub && <div style={{ fontSize: '11px', opacity: .75 }}>{k.sub}</div>}
                  </div>
                ))}
              </div>
              <h4 style={{ margin: '0 0 10px', fontSize: '13px', color: '#7f8c8d', textTransform: 'uppercase' }}>Detalle de imputaciones</h4>
              {detalle.detalles?.length > 0 ? (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ background: '#f8f9fa' }}>
                      {['Fecha', 'Categoría', 'Descripción', 'Cantidad', 'Precio unit.', 'Importe'].map(h => (
                        <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: '#7f8c8d' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {detalle.detalles.map(d => (
                      <tr key={d.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                        <td style={{ padding: '5px 8px' }}>{d.fecha}</td>
                        <td style={{ padding: '5px 8px' }}><Badge text={d.categoria_display} color="#7f8c8d" /></td>
                        <td style={{ padding: '5px 8px' }}>{d.descripcion}</td>
                        <td style={{ padding: '5px 8px' }}>{d.cantidad} {d.unidad}</td>
                        <td style={{ padding: '5px 8px' }}>${parseFloat(d.precio_unit).toLocaleString('es-AR')}</td>
                        <td style={{ padding: '5px 8px', fontWeight: '700', color: '#27ae60' }}>${parseFloat(d.importe).toLocaleString('es-AR')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : <p style={{ color: '#7f8c8d', fontSize: '13px' }}>Sin líneas de detalle aún</p>}
            </Card>
          )}
          <Card>
            <h4 style={{ margin: '0 0 12px' }}>Comparativa de costos por lote</h4>
            {resumen.map(c => (
              <div key={c.lote_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #f0f0f0', cursor: 'pointer' }}
                onClick={() => cargarDetalle(c.lote_id)}>
                <span style={{ fontSize: '13px', fontWeight: '600' }}>{c.lote_codigo}</span>
                <div style={{ display: 'flex', gap: '16px', fontSize: '12px' }}>
                  <span style={{ color: '#2980b9' }}>${parseFloat(c.costo_por_litro || 0).toFixed(2)}/L</span>
                  <span style={{ color: '#27ae60' }}>${parseFloat(c.costo_por_botella || 0).toFixed(2)}/bot</span>
                  <span style={{ color: '#8e44ad', fontWeight: '700' }}>${parseFloat(c.costo_total_pt || 0).toLocaleString('es-AR')}</span>
                </div>
              </div>
            ))}
            {resumen.length === 0 && <p style={{ color: '#7f8c8d', fontSize: '13px' }}>Sin costos cargados aún</p>}
          </Card>
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// TRAZABILIDAD
// ─────────────────────────────────────────────────────────────────────────────
function TrazabilidadTab({ lotes = [] }) {
  const safeLotes = Array.isArray(lotes) ? lotes : []
  const [loteId, setLoteId]       = useState('')
  const [direccion, setDireccion] = useState('atras')
  const [resultado, setResultado] = useState(null)
  const [loading, setLoading]     = useState(false)

  const buscar = async () => {
    if (!loteId) return
    setLoading(true)
    const r = await api(`trazabilidad/?lote_id=${loteId}&direccion=${direccion}`)
    setResultado(r.ok ? r.data : null)
    setLoading(false)
  }

  return (
    <div>
      <Card>
        <h4 style={{ margin: '0 0 14px' }}>Consulta de trazabilidad</h4>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <Select label="Lote a consultar" value={loteId} onChange={setLoteId}
              options={safeLotes.map(l => ({ value: l.id, label: `${l.codigo} — ${l.varietal_nombre} ${l.campaña}` }))} />
          </div>
          <div style={{ display: 'flex', gap: '6px', marginBottom: '10px' }}>
            {['atras', 'adelante'].map(d => (
              <Btn key={d} onClick={() => setDireccion(d)} color={direccion === d ? '#8e44ad' : '#7f8c8d'} small>
                {d === 'atras' ? '⬅️ Hacia atrás (origen)' : '➡️ Hacia adelante (destino)'}
              </Btn>
            ))}
          </div>
          <div style={{ marginBottom: '10px' }}>
            <Btn onClick={buscar} color="#2c3e50" disabled={!loteId || loading}>
              {loading ? 'Consultando…' : '🔍 Consultar'}
            </Btn>
          </div>
        </div>
      </Card>

      {resultado && (
        <div>
          <Card>
            <h4 style={{ margin: '0 0 10px', color: '#8e44ad' }}>
              Lote: {resultado.lote?.codigo} — {resultado.lote?.varietal_nombre} {resultado.lote?.campaña}
            </h4>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              {[
                { label: 'Litros actuales', value: `${Math.round(resultado.lote?.litros_actuales || 0).toLocaleString('es-AR')} L` },
                { label: 'Estado', value: resultado.lote?.estado_display },
              ].map(k => (
                <div key={k.label} style={{ background: '#f8f9fa', borderRadius: '6px', padding: '8px 14px' }}>
                  <div style={{ fontSize: '11px', color: '#7f8c8d' }}>{k.label}</div>
                  <div style={{ fontSize: '15px', fontWeight: '700' }}>{k.value}</div>
                </div>
              ))}
            </div>
          </Card>

          {direccion === 'atras' && (
            <>
              {resultado.tickets_uva?.length > 0 && (
                <Card>
                  <h4 style={{ margin: '0 0 10px', color: '#e67e22' }}>🚛 Tickets de uva recibida ({resultado.tickets_uva.length})</h4>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                    <thead><tr style={{ background: '#f8f9fa' }}>
                      {['Ticket', 'Fecha', 'Parcela', 'Varietal', 'Kg neto', 'Brix', 'Proveedor'].map(h => (
                        <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: '#7f8c8d' }}>{h}</th>
                      ))}
                    </tr></thead>
                    <tbody>
                      {resultado.tickets_uva.map(t => (
                        <tr key={t.ticket_id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                          <td style={{ padding: '5px 8px', fontWeight: '700' }}>#{t.ticket_id}</td>
                          <td style={{ padding: '5px 8px' }}>{t.fecha?.slice(0, 10)}</td>
                          <td style={{ padding: '5px 8px' }}>{t.parcela || '—'}</td>
                          <td style={{ padding: '5px 8px' }}>{t.varietal}</td>
                          <td style={{ padding: '5px 8px' }}>{parseFloat(t.kg_neto || 0).toLocaleString('es-AR')} kg</td>
                          <td style={{ padding: '5px 8px' }}>{t.brix ? `${t.brix}°` : '—'}</td>
                          <td style={{ padding: '5px 8px', color: '#7f8c8d' }}>{t.nombre_prov || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Card>
              )}
              {resultado.insumos_utilizados?.length > 0 && (
                <Card>
                  <h4 style={{ margin: '0 0 10px', color: '#3498db' }}>🧪 Insumos enológicos utilizados</h4>
                  {resultado.insumos_utilizados.map(i => (
                    <div key={i.operacion_id} style={{ display: 'flex', gap: '16px', fontSize: '13px', padding: '5px 0', borderBottom: '1px solid #f0f0f0' }}>
                      <span style={{ color: '#7f8c8d', minWidth: '80px' }}>{i.fecha?.slice(0, 10)}</span>
                      <strong>{i.insumo}</strong>
                      <span>{i.cantidad} {i.unidad}</span>
                      {i.lote_proveedor && <span style={{ color: '#7f8c8d' }}>Lote prov.: {i.lote_proveedor}</span>}
                    </div>
                  ))}
                </Card>
              )}
              {resultado.composicion_varietal?.length > 0 && (
                <Card>
                  <h4 style={{ margin: '0 0 10px', color: '#8e44ad' }}>🍇 Composición varietal (coupages)</h4>
                  {resultado.composicion_varietal.map((c, i) => (
                    <div key={i} style={{ display: 'flex', gap: '16px', fontSize: '13px', padding: '5px 0', borderBottom: '1px solid #f0f0f0' }}>
                      <strong style={{ minWidth: '100px' }}>{c.varietal}</strong>
                      {c.lote_origen_codigo && <span>Lote: {c.lote_origen_codigo}</span>}
                      <span>{parseFloat(c.litros || 0).toLocaleString('es-AR')} L</span>
                      {c.porcentaje && <Badge text={`${c.porcentaje}%`} color="#8e44ad" />}
                    </div>
                  ))}
                </Card>
              )}
            </>
          )}

          {direccion === 'adelante' && (
            <>
              {resultado.ordenes_embotellado?.length > 0 && (
                <Card>
                  <h4 style={{ margin: '0 0 10px', color: '#e74c3c' }}>🍾 Órdenes de embotellado</h4>
                  {resultado.ordenes_embotellado.map(o => (
                    <div key={o.orden_id} style={{ display: 'flex', gap: '16px', fontSize: '13px', padding: '6px 0', borderBottom: '1px solid #f0f0f0', flexWrap: 'wrap' }}>
                      <strong>OE #{o.orden_id}</strong>
                      <span>{o.formato} ml</span>
                      <span>{parseFloat(o.botellas || 0).toLocaleString('es-AR')} botellas</span>
                      {o.cod_art_pt && <Badge text={o.cod_art_pt} color="#2c3e50" />}
                      {o.nro_rnoe && <span style={{ color: '#7f8c8d' }}>RNOE: {o.nro_rnoe}</span>}
                      <span style={{ color: '#7f8c8d' }}>{o.fecha}</span>
                    </div>
                  ))}
                </Card>
              )}
              {resultado.guias_traslado?.length > 0 && (
                <Card>
                  <h4 style={{ margin: '0 0 10px', color: '#16a085' }}>📦 Guías de traslado emitidas</h4>
                  {resultado.guias_traslado.map(g => (
                    <div key={g.guia_id} style={{ display: 'flex', gap: '16px', fontSize: '13px', padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                      <strong>Guía #{g.guia_id}</strong>
                      <span>{g.fecha}</span>
                      <span>→ {g.destino}</span>
                      <span>{parseFloat(g.litros_o_unidades || 0).toLocaleString('es-AR')} L/u</span>
                    </div>
                  ))}
                </Card>
              )}
              {resultado.usado_en_lotes?.length > 0 && (
                <Card>
                  <h4 style={{ margin: '0 0 10px', color: '#8e44ad' }}>🔀 Usado como origen en coupages</h4>
                  {resultado.usado_en_lotes.map((u, i) => (
                    <div key={i} style={{ display: 'flex', gap: '16px', fontSize: '13px', padding: '5px 0', borderBottom: '1px solid #f0f0f0' }}>
                      <strong>{u.lote_destino_codigo}</strong>
                      <span>{parseFloat(u.litros || 0).toLocaleString('es-AR')} L</span>
                      {u.porcentaje && <Badge text={`${u.porcentaje}%`} color="#8e44ad" />}
                    </div>
                  ))}
                </Card>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// FISCAL / INV
// ─────────────────────────────────────────────────────────────────────────────
function FiscalTab({ lotes = [], varietales = [] }) {
  const safeLotes = Array.isArray(lotes) ? lotes : []
  const [declaraciones, setDeclaraciones] = useState([])
  const [guias, setGuias]                 = useState([])
  const [certs, setCerts]                 = useState([])
  const [sub, setSub]   = useState('declaraciones')
  const [form, setForm] = useState({})
  const [formG, setFormG] = useState({})
  const [msg, setMsg]   = useState('')

  useEffect(() => {
    api('declaraciones-inv/').then(r => setDeclaraciones(Array.isArray(r?.data) ? r.data : []))
    api('guias-traslado/').then(r => setGuias(Array.isArray(r?.data) ? r.data : []))
    api('certificados-analisis/').then(r => setCerts(Array.isArray(r?.data) ? r.data : []))
  }, [])

  const setF  = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const setFG = (k, v) => setFormG(f => ({ ...f, [k]: v }))

  const guardarDeclaracion = async () => {
    const r = await api('declaraciones-inv/', 'POST', { ...form, auto_calcular: form.auto_calcular || false, usuario: 'admin' })
    if (r.ok) {
      setMsg('✅ ' + r.msg); setForm({})
      api('declaraciones-inv/').then(r2 => setDeclaraciones(Array.isArray(r2?.data) ? r2.data : []))
    } else setMsg('❌ ' + r.msg)
  }

  const guardarGuia = async () => {
    const r = await api('guias-traslado/', 'POST', { ...formG, usuario: 'admin' })
    if (r.ok) {
      setMsg('✅ Guía #' + r.data?.id + ' emitida'); setFormG({})
      api('guias-traslado/').then(r2 => setGuias(Array.isArray(r2?.data) ? r2.data : []))
    } else setMsg('❌ ' + r.msg)
  }

  const estadoInvColor = { BO: '#e67e22', PR: '#3498db', AC: '#27ae60', OB: '#e74c3c' }
  const estadoGuiaColor = { EM: '#3498db', US: '#27ae60', AN: '#c0392b', VE: '#95a5a6' }
  const tiposDecl = [
    { value: 'COS', label: 'Declaración de cosecha' }, { value: 'PRO', label: 'Declaración de producción' },
    { value: 'EXI', label: 'Declaración de existencias' }, { value: 'ELA', label: 'Declaración de elaboración' },
  ]
  const tiposGuia = [{ value: 'GR', label: 'Granel' }, { value: 'PT', label: 'Producto terminado' }, { value: 'AM', label: 'Ambos' }]

  return (
    <div>
      {msg && <div style={{ background: '#ecf0f1', padding: '8px 12px', borderRadius: '6px', marginBottom: '12px', fontSize: '13px' }}>{msg}</div>}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        {['declaraciones', 'guias', 'certificados'].map(s => (
          <Btn key={s} onClick={() => setSub(s)} color={sub === s ? '#2c3e50' : '#7f8c8d'} small>
            {s === 'declaraciones' ? '📃 Declaraciones INV' : s === 'guias' ? '🚚 Guías de traslado' : '🏅 Certificados de análisis'}
          </Btn>
        ))}
      </div>

      {sub === 'declaraciones' && (
        <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '16px' }}>
          <Card>
            <h4 style={{ margin: '0 0 12px' }}>Nueva declaración</h4>
            <Select label="Tipo *" value={form.tipo} onChange={v => setF('tipo', v)} options={tiposDecl} />
            <Input label="Período *" value={form.periodo} onChange={v => setF('periodo', v)} type="date" />
            <Input label="Campaña" value={form.campaña} onChange={v => setF('campaña', v)} type="number" placeholder={new Date().getFullYear()} />
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <input type="checkbox" id="autoCalc" checked={!!form.auto_calcular}
                onChange={e => setF('auto_calcular', e.target.checked)} />
              <label htmlFor="autoCalc" style={{ fontSize: '13px', cursor: 'pointer' }}>
                Auto-calcular desde lotes del sistema
              </label>
            </div>
            {!form.auto_calcular && (
              <>
                <Input label="Kg uva declarados" value={form.kg_uva_declarados} onChange={v => setF('kg_uva_declarados', v)} type="number" small />
                <Input label="Litros declarados" value={form.litros_declarados} onChange={v => setF('litros_declarados', v)} type="number" small />
                <Input label="Litros existencias" value={form.litros_existencias} onChange={v => setF('litros_existencias', v)} type="number" small />
              </>
            )}
            <Input label="N° Expediente INV" value={form.nro_expediente_inv} onChange={v => setF('nro_expediente_inv', v)} placeholder="EXP-2024-..." />
            <Btn onClick={guardarDeclaracion} color="#c0392b">Generar declaración</Btn>
          </Card>

          <div>
            {declaraciones.map(d => (
              <div key={d.id} style={{
                background: 'white', border: `1px solid #ecf0f1`,
                borderLeft: `4px solid ${estadoInvColor[d.estado] || '#ddd'}`,
                borderRadius: '8px', padding: '12px 16px', marginBottom: '10px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <strong>{d.tipo_display}</strong>
                  <span style={{ background: estadoInvColor[d.estado], color: 'white', borderRadius: '4px', padding: '1px 8px', fontSize: '11px' }}>{d.estado_display}</span>
                </div>
                <div style={{ fontSize: '12px', color: '#7f8c8d', marginTop: '4px', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                  <span>Período: <strong>{d.periodo?.slice(0, 7)}</strong></span>
                  {d.campaña && <span>Campaña: {d.campaña}</span>}
                  <span>Kg uva: {parseFloat(d.kg_uva_declarados || 0).toLocaleString('es-AR')}</span>
                  <span>Litros: {parseFloat(d.litros_declarados || 0).toLocaleString('es-AR')} L</span>
                  <span>Existencias: {parseFloat(d.litros_existencias || 0).toLocaleString('es-AR')} L</span>
                  {d.nro_expediente_inv && <span style={{ color: '#3498db' }}>Exp: {d.nro_expediente_inv}</span>}
                </div>
              </div>
            ))}
            {declaraciones.length === 0 && <p style={{ color: '#7f8c8d', textAlign: 'center', padding: '30px' }}>Sin declaraciones generadas</p>}
          </div>
        </div>
      )}

      {sub === 'guias' && (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '16px' }}>
          <Card>
            <h4 style={{ margin: '0 0 12px' }}>Emitir guía de traslado</h4>
            <Input label="Fecha *" value={formG.fecha} onChange={v => setFG('fecha', v)} type="date" />
            <Select label="Tipo" value={formG.tipo} onChange={v => setFG('tipo', v)} options={tiposGuia} />
            <Input label="Establecimiento destino *" value={formG.establecimiento_destino} onChange={v => setFG('establecimiento_destino', v)} />
            <Input label="Domicilio destino" value={formG.domicilio_destino} onChange={v => setFG('domicilio_destino', v)} />
            <Select label="Lote" value={formG.lote_id} onChange={v => setFG('lote_id', v)}
              options={safeLotes.map(l => ({ value: l.id, label: `${l.codigo} — ${l.varietal_nombre}` }))} />
            <Input label="Descripción mercadería *" value={formG.descripcion_mercaderia} onChange={v => setFG('descripcion_mercaderia', v)} />
            <Input label="Litros / Unidades *" value={formG.litros_o_unidades} onChange={v => setFG('litros_o_unidades', v)} type="number" />
            <Input label="Campaña" value={formG.campaña} onChange={v => setFG('campaña', v)} type="number" />
            <Input label="Grado alcohol" value={formG.grado_alcohol} onChange={v => setFG('grado_alcohol', v)} type="number" />
            <Input label="Transportista" value={formG.transportista} onChange={v => setFG('transportista', v)} />
            <Input label="Patente vehículo" value={formG.patente_vehiculo} onChange={v => setFG('patente_vehiculo', v)} />
            <Btn onClick={guardarGuia} color="#16a085">Emitir guía</Btn>
          </Card>

          <div>
            {guias.map(g => (
              <div key={g.id} style={{
                background: 'white', border: `1px solid #ecf0f1`,
                borderLeft: `4px solid ${estadoGuiaColor[g.estado] || '#ddd'}`,
                borderRadius: '8px', padding: '12px 16px', marginBottom: '10px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>Guía #{g.id} — {g.tipo_display}</strong>
                  <span style={{ background: estadoGuiaColor[g.estado], color: 'white', borderRadius: '4px', padding: '1px 8px', fontSize: '11px' }}>{g.estado_display}</span>
                </div>
                <div style={{ fontSize: '13px', margin: '4px 0 2px' }}>→ <strong>{g.establecimiento_destino}</strong></div>
                <div style={{ fontSize: '12px', color: '#7f8c8d', display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
                  <span>Fecha: {g.fecha}</span>
                  {g.lote_codigo && <span>Lote: {g.lote_codigo}</span>}
                  <span>{parseFloat(g.litros_o_unidades || 0).toLocaleString('es-AR')} L/u</span>
                  {g.grado_alcohol && <span>{g.grado_alcohol}% alc.</span>}
                </div>
              </div>
            ))}
            {guias.length === 0 && <p style={{ color: '#7f8c8d', textAlign: 'center', padding: '30px' }}>Sin guías emitidas</p>}
          </div>
        </div>
      )}

      {sub === 'certificados' && (
        <Card>
          <h4 style={{ margin: '0 0 12px' }}>Certificados de análisis emitidos</h4>
          {certs.length === 0 ? (
            <p style={{ color: '#7f8c8d', fontSize: '13px' }}>Sin certificados. Se generan desde el módulo de Análisis al aprobar un lote y vincularlo con una guía de traslado.</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ background: '#f8f9fa' }}>
                  {['#', 'Lote', 'Fecha emisión', 'Vence', 'Lab.', '°Alc', 'Acid.T', 'Acid.V', 'SO₂T', 'Apto'].map(h => (
                    <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: '#7f8c8d' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {certs.map(c => (
                  <tr key={c.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '5px 8px', fontWeight: '700' }}>#{c.id}</td>
                    <td style={{ padding: '5px 8px' }}>{c.lote_codigo}</td>
                    <td style={{ padding: '5px 8px' }}>{c.fecha_emision}</td>
                    <td style={{ padding: '5px 8px', color: c.fecha_vencimiento ? '#e74c3c' : '#7f8c8d' }}>{c.fecha_vencimiento || '—'}</td>
                    <td style={{ padding: '5px 8px' }}>{c.laboratorio}</td>
                    <td style={{ padding: '5px 8px' }}>{c.grado_alcohol}%</td>
                    <td style={{ padding: '5px 8px' }}>{c.acidez_total}</td>
                    <td style={{ padding: '5px 8px' }}>{c.acidez_volatil}</td>
                    <td style={{ padding: '5px 8px' }}>{c.so2_total}</td>
                    <td style={{ padding: '5px 8px' }}>{c.apto_consumo ? '✅' : '❌'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// FERMENTACIÓN — Tab principal con sub-tabs: Diaria / Remontajes / FML
// ─────────────────────────────────────────────────────────────────────────────
function FermentacionTab({ lotes = [] }) {
  const safeLotes = Array.isArray(lotes) ? lotes : []
  const [loteId, setLoteId] = useState('')
  const [sub, setSub]       = useState('diaria')
  const [curva, setCurva]   = useState([])
  const [lecturas, setLecturas] = useState([])
  const [remontajes, setRemontajes] = useState([])
  const [fml, setFml]       = useState(null)
  const [form, setForm]     = useState({ turno: 'M', co2_activo: true, estado_sombrero: 'SN' })
  const [formRem, setFormRem] = useState({ tipo: 'REM', objetivo: 'EXT' })
  const [formFml, setFormFml] = useState({ tipo: 'INO', estado: 'PE' })
  const [formCroma, setFormCroma] = useState({ resultado: 'MA' })
  const [msg, setMsg]       = useState('')
  const [showFormRem, setShowFormRem] = useState(false)

  const setF   = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const setFR  = (k, v) => setFormRem(f => ({ ...f, [k]: v }))
  const setFF  = (k, v) => setFormFml(f => ({ ...f, [k]: v }))
  const setFC  = (k, v) => setFormCroma(f => ({ ...f, [k]: v }))

  const cargarLote = (lid) => {
    setLoteId(lid)
    if (!lid) return
    api(`fermentacion/curva/?lote_id=${lid}`).then(r => setCurva(Array.isArray(r?.data) ? r.data : []))
    api(`fermentacion/?lote_id=${lid}`).then(r => setLecturas(Array.isArray(r?.data) ? r.data : []))
    api(`remontajes/?lote_id=${lid}`).then(r => setRemontajes(Array.isArray(r?.data) ? r.data : []))
    api(`fml/?lote_id=${lid}`).then(r => { if (r.ok && r.data) setFml(r.data) })
  }

  const guardarLectura = async () => {
    if (!loteId) return setMsg('❌ Seleccioná un lote')
    const r = await api('fermentacion/', 'POST', {
      ...form, lote_id: loteId,
      fecha: form.fecha || new Date().toISOString().slice(0, 10),
      usuario: 'admin',
    })
    setMsg(r.ok ? (r.data?.alerta || '✅ Lectura guardada') : '❌ ' + r.msg)
    if (r.ok) {
      cargarLote(loteId)
      setForm(f => ({ turno: f.turno === 'M' ? 'T' : 'M', co2_activo: true, estado_sombrero: f.estado_sombrero }))
    }
  }

  const guardarRemontaje = async () => {
    const r = await api('remontajes/', 'POST', { ...formRem, lote_id: loteId, usuario: 'admin' })
    setMsg(r.ok ? '✅ ' + r.msg : '❌ ' + r.msg)
    if (r.ok) { cargarLote(loteId); setShowFormRem(false); setFormRem({ tipo: 'REM', objetivo: 'EXT' }) }
  }

  const guardarFml = async () => {
    const r = await api('fml/', 'POST', { ...formFml, lote_id: loteId, accion: 'guardar_fml', usuario: 'admin' })
    setMsg(r.ok ? '✅ FML guardada' + (r.data?.alerta ? ' — ' + r.data.alerta : '') : '❌ ' + r.msg)
    if (r.ok) cargarLote(loteId)
  }

  const agregarCroma = async () => {
    const r = await api('fml/', 'POST', { ...formCroma, lote_id: loteId, accion: 'agregar_croma', usuario: 'admin' })
    setMsg(r.ok ? '✅ ' + r.msg + (r.data?.fml_completada ? ' — 🎉 FML COMPLETADA' : '') : '❌ ' + r.msg)
    if (r.ok) cargarLote(loteId)
  }

  // ── Mini gráfico SVG de curva densidad ────────────────────────────────────
  const CurvaDensidad = ({ data }) => {
    if (!data || data.length < 2) return (
      <p style={{ color: 'var(--color-text-tertiary)', fontSize: '13px', textAlign: 'center', padding: '20px 0' }}>
        Sin suficientes lecturas para graficar
      </p>
    )
    const W = 560, H = 140, PAD = 36
    const dens = data.map(d => d.densidad)
    const temps = data.map(d => d.temperatura_c)
    const minD = Math.min(...dens) - 5
    const maxD = Math.max(...dens) + 5
    const minT = Math.min(...temps) - 2
    const maxT = Math.max(...temps) + 2
    const xScale = i => PAD + (i / (data.length - 1)) * (W - PAD * 2)
    const yDens  = v => H - PAD - ((v - minD) / (maxD - minD)) * (H - PAD * 2)
    const yTemp  = v => H - PAD - ((v - minT) / (maxT - minT)) * (H - PAD * 2)
    const pathD  = data.map((d, i) => `${i === 0 ? 'M' : 'L'}${xScale(i).toFixed(1)},${yDens(d.densidad).toFixed(1)}`).join(' ')
    const pathT  = data.map((d, i) => `${i === 0 ? 'M' : 'L'}${xScale(i).toFixed(1)},${yTemp(d.temperatura_c).toFixed(1)}`).join(' ')
    const trabados = data.filter(d => d.fermentacion_trabada)
    return (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', maxHeight: '150px' }}>
        {/* Línea densidad */}
        <path d={pathD} stroke="#2980b9" strokeWidth="2" fill="none" />
        {/* Línea temperatura */}
        <path d={pathT} stroke="#e74c3c" strokeWidth="1.5" fill="none" strokeDasharray="4 2" />
        {/* Puntos densidad */}
        {data.map((d, i) => (
          <circle key={i} cx={xScale(i)} cy={yDens(d.densidad)} r="3"
            fill={d.fermentacion_trabada ? '#e74c3c' : '#2980b9'} />
        ))}
        {/* Etiquetas eje X */}
        {data.filter((_, i) => i % Math.ceil(data.length / 6) === 0).map((d, i, arr) => {
          const origIdx = data.indexOf(d)
          return (
            <text key={i} x={xScale(origIdx)} y={H - 4} textAnchor="middle"
              style={{ fontSize: '9px', fill: 'var(--color-text-tertiary)' }}>
              {d.label}
            </text>
          )
        })}
        {/* Leyenda */}
        <line x1={W - 100} y1={12} x2={W - 88} y2={12} stroke="#2980b9" strokeWidth="2" />
        <text x={W - 84} y={16} style={{ fontSize: '10px', fill: 'var(--color-text-secondary)' }}>Densidad</text>
        <line x1={W - 100} y1={26} x2={W - 88} y2={26} stroke="#e74c3c" strokeWidth="1.5" strokeDasharray="4 2" />
        <text x={W - 84} y={30} style={{ fontSize: '10px', fill: 'var(--color-text-secondary)' }}>Temp °C</text>
      </svg>
    )
  }

  const tiposRem = [
    { value: 'REM', label: 'Remontaje (pump-over)' }, { value: 'DEL', label: 'Délestage (rack & return)' },
    { value: 'BAZ', label: 'Bazuqueo (pigeage)' },
  ]
  const objetivosRem = [
    { value: 'EXT', label: 'Extracción color/taninos' }, { value: 'AIR', label: 'Aireación' },
    { value: 'SOL', label: 'Disolución SO₂/levaduras' }, { value: 'ENF', label: 'Enfriamiento' },
    { value: 'HOM', label: 'Homogeneización' },
  ]
  const tiposFml = [{ value: 'INO', label: 'Inoculada' }, { value: 'ESP', label: 'Espontánea' }, { value: 'NO', label: 'No aplica' }]
  const estadosFml = [{ value: 'PE', label: 'Pendiente' }, { value: 'EN', label: 'En curso' }, { value: 'CO', label: 'Completada' }, { value: 'DE', label: 'Detenida' }]
  const resultCroma = [
    { value: 'MA', label: 'Málico presente — FML incompleta' },
    { value: 'TR', label: 'Traza — finalizando' },
    { value: 'AU', label: 'Málico ausente — FML completa ✅' },
  ]
  const estadoSombreroOpts = [
    { value: 'SN', label: 'Sin sombrero' }, { value: 'AL', label: 'Alto' },
    { value: 'ME', label: 'Medio' }, { value: 'BA', label: 'Bajo/hundido' },
  ]
  const ultimaLectura = lecturas[lecturas.length - 1]
  const fmlEstadoColor = { PE: '#95a5a6', EN: '#e67e22', CO: '#27ae60', DE: '#e74c3c', NA: '#bdc3c7' }

  return (
    <div>
      {msg && (
        <div style={{
          background: msg.includes('TRABADA') || msg.includes('❌') ? '#FCEBEB' : msg.includes('⚠️') ? '#FAEEDA' : '#EAF3DE',
          color: msg.includes('TRABADA') || msg.includes('❌') ? '#A32D2D' : msg.includes('⚠️') ? '#854F0B' : '#27500A',
          padding: '8px 14px', borderRadius: '6px', marginBottom: '12px', fontSize: '13px', fontWeight: '500',
        }}>{msg}</div>
      )}

      <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end', marginBottom: '16px', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '220px' }}>
          <Select label="Lote en fermentación" value={loteId} onChange={cargarLote}
            options={safeLotes.filter(l => ['EB', 'CR'].includes(l.estado)).map(l => ({
              value: l.id,
              label: `${l.codigo} — ${l.varietal_nombre} (${Math.round(l.litros_actuales || 0).toLocaleString('es-AR')} L)`,
            }))} />
        </div>
        <div style={{ display: 'flex', gap: '6px', marginBottom: '10px' }}>
          {['diaria', 'remontajes', 'fml'].map(s => (
            <Btn key={s} onClick={() => setSub(s)} color={sub === s ? '#2c3e50' : '#7f8c8d'} small>
              {s === 'diaria' ? '📊 Planilla diaria' : s === 'remontajes' ? '🔄 Remontajes' : '🧬 FML'}
            </Btn>
          ))}
        </div>
      </div>

      {/* ── Estado actual rápido ── */}
      {loteId && ultimaLectura && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: '8px', marginBottom: '16px' }}>
          {[
            { label: 'Densidad actual', value: `${ultimaLectura.densidad} g/L`, color: '#2980b9' },
            { label: 'Temperatura', value: `${ultimaLectura.temperatura_c}°C`, color: ultimaLectura.temperatura_c > 30 ? '#e74c3c' : '#27ae60' },
            { label: 'Alcohol probable', value: `${ultimaLectura.alcohol_probable}%`, color: '#8e44ad' },
            { label: 'Última lectura', value: `${ultimaLectura.fecha} ${ultimaLectura.turno_display}`, color: '#7f8c8d' },
          ].map(k => (
            <div key={k.label} style={{ background: 'var(--color-background-secondary)', borderRadius: '6px', padding: '8px 10px' }}>
              <div style={{ fontSize: '11px', color: 'var(--color-text-tertiary)' }}>{k.label}</div>
              <div style={{ fontSize: '15px', fontWeight: '500', color: k.color }}>{k.value}</div>
            </div>
          ))}
          {ultimaLectura.fermentacion_trabada && (
            <div style={{ gridColumn: '1/-1', background: '#FCEBEB', borderRadius: '6px', padding: '8px 12px', color: '#A32D2D', fontSize: '13px', fontWeight: '500' }}>
              ⚠️ FERMENTACIÓN POSIBLEMENTE TRABADA — delta densidad &lt; 1 g/L en última lectura
            </div>
          )}
        </div>
      )}

      {/* ── SUB-TAB: Planilla diaria ── */}
      {sub === 'diaria' && (
        <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '16px' }}>
          <Card>
            <h4 style={{ margin: '0 0 12px' }}>Registrar lectura</h4>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
              {[{ v: 'M', l: '🌅 Mañana' }, { v: 'T', l: '🌆 Tarde' }, { v: 'N', l: '🌙 Noche' }].map(t => (
                <button key={t.v} onClick={() => setF('turno', t.v)}
                  style={{ flex: 1, padding: '5px', borderRadius: '5px', border: '1px solid var(--color-border-secondary)',
                    background: form.turno === t.v ? '#2c3e50' : 'transparent',
                    color: form.turno === t.v ? 'white' : 'var(--color-text-secondary)',
                    cursor: 'pointer', fontSize: '12px', fontWeight: form.turno === t.v ? '500' : '400' }}>
                  {t.l}
                </button>
              ))}
            </div>
            <Input label="Fecha" value={form.fecha} onChange={v => setF('fecha', v)} type="date" />
            <Input label="Densidad (g/L) *" value={form.densidad} onChange={v => setF('densidad', v)} type="number" placeholder="1042.0" />
            <Input label="Temperatura (°C) *" value={form.temperatura_c} onChange={v => setF('temperatura_c', v)} type="number" placeholder="22.0" />
            <Input label="Brix (opcional)" value={form.brix} onChange={v => setF('brix', v)} type="number" />
            <Select label="Estado sombrero (tintos)" value={form.estado_sombrero} onChange={v => setF('estado_sombrero', v)} options={estadoSombreroOpts} />
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <input type="checkbox" id="co2" checked={!!form.co2_activo} onChange={e => setF('co2_activo', e.target.checked)} />
              <label htmlFor="co2" style={{ fontSize: '13px', cursor: 'pointer', color: 'var(--color-text-secondary)' }}>CO₂ activo visible</label>
            </div>
            {form.densidad && (
              <div style={{ background: 'var(--color-background-secondary)', padding: '8px 10px', borderRadius: '6px', fontSize: '13px', marginBottom: '10px' }}>
                <strong>Alcohol probable:</strong> ~{Math.max(0, (1000 - parseFloat(form.densidad)) / 7.4).toFixed(2)}% v/v
              </div>
            )}
            <Input label="Observaciones" value={form.observaciones} onChange={v => setF('observaciones', v)} />
            <Btn onClick={guardarLectura} color="#2980b9" disabled={!loteId}>Guardar lectura</Btn>
          </Card>

          <div>
            {curva.length >= 2 && (
              <Card>
                <h4 style={{ margin: '0 0 10px' }}>Curva fermentativa — densidad y temperatura</h4>
                <CurvaDensidad data={curva} />
                <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '6px' }}>
                  <span>Inicio: <strong>{curva[0]?.densidad} g/L</strong></span>
                  <span>Actual: <strong>{curva[curva.length - 1]?.densidad} g/L</strong></span>
                  <span>Lecturas: <strong>{curva.length}</strong></span>
                </div>
              </Card>
            )}

            <Card>
              <h4 style={{ margin: '0 0 10px' }}>Historial de lecturas</h4>
              {lecturas.length === 0 ? (
                <p style={{ color: 'var(--color-text-tertiary)', fontSize: '13px' }}>Sin lecturas registradas</p>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ background: 'var(--color-background-secondary)' }}>
                      {['Fecha', 'Turno', 'Densidad', 'T°C', '°Alc prob.', 'Sombrero', 'CO₂', ''].map(h => (
                        <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: 'var(--color-text-tertiary)', fontWeight: '500' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[...lecturas].reverse().map(l => (
                      <tr key={l.id} style={{
                        borderBottom: '0.5px solid var(--color-border-tertiary)',
                        background: l.fermentacion_trabada ? '#FCEBEB' : 'transparent',
                      }}>
                        <td style={{ padding: '5px 8px' }}>{l.fecha}</td>
                        <td style={{ padding: '5px 8px', color: 'var(--color-text-secondary)' }}>{l.turno_display}</td>
                        <td style={{ padding: '5px 8px', fontWeight: '500' }}>{l.densidad}</td>
                        <td style={{ padding: '5px 8px', color: l.temperatura_c > 30 ? '#A32D2D' : 'var(--color-text-primary)' }}>{l.temperatura_c}°</td>
                        <td style={{ padding: '5px 8px', color: '#8e44ad' }}>{l.alcohol_probable}%</td>
                        <td style={{ padding: '5px 8px', color: 'var(--color-text-secondary)', fontSize: '11px' }}>{l.estado_sombrero_display}</td>
                        <td style={{ padding: '5px 8px' }}>{l.co2_activo ? '✅' : '—'}</td>
                        <td style={{ padding: '5px 8px' }}>{l.fermentacion_trabada && <Badge text="TRABADA" color="#A32D2D" />}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Card>
          </div>
        </div>
      )}

      {/* ── SUB-TAB: Remontajes ── */}
      {sub === 'remontajes' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <p style={{ margin: 0, color: 'var(--color-text-secondary)', fontSize: '13px' }}>
              {remontajes.length} operación{remontajes.length !== 1 ? 'es' : ''} registrada{remontajes.length !== 1 ? 's' : ''}
            </p>
            <Btn onClick={() => setShowFormRem(!showFormRem)} color="#e67e22" small>+ Registrar operación</Btn>
          </div>

          {showFormRem && (
            <Card>
              <h4 style={{ margin: '0 0 12px' }}>Nueva operación mecánica</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 14px' }}>
                <Select label="Tipo *" value={formRem.tipo} onChange={v => setFR('tipo', v)} options={tiposRem} />
                <Select label="Objetivo" value={formRem.objetivo} onChange={v => setFR('objetivo', v)} options={objetivosRem} />
                <Input label="Fecha y hora *" value={formRem.fecha} onChange={v => setFR('fecha', v)} type="datetime-local" />
                <Input label="Temperatura mosto °C" value={formRem.temperatura_mosto_c} onChange={v => setFR('temperatura_mosto_c', v)} type="number" />
                <Input label="Volumen bombeado (L)" value={formRem.volumen_bombeado_l} onChange={v => setFR('volumen_bombeado_l', v)} type="number" />
                <Input label="Duración (min)" value={formRem.duracion_min} onChange={v => setFR('duracion_min', v)} type="number" />
                <Input label="Caudal bomba (L/h)" value={formRem.caudal_lh} onChange={v => setFR('caudal_lh', v)} type="number" />
                {formRem.tipo === 'DEL' && (
                  <Input label="Tiempo escurrido (min)" value={formRem.tiempo_escurrido_min} onChange={v => setFR('tiempo_escurrido_min', v)} type="number" />
                )}
                <div style={{ gridColumn: '1/-1' }}>
                  <Input label="Cambio de color observado" value={formRem.cambio_color} onChange={v => setFR('cambio_color', v)} placeholder="Ej: intensificación notable del color rojo" />
                </div>
                <div style={{ gridColumn: '1/-1' }}>
                  <Input label="Observaciones" value={formRem.observaciones} onChange={v => setFR('observaciones', v)} />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <Btn onClick={guardarRemontaje} color="#e67e22">Guardar operación</Btn>
                <Btn onClick={() => setShowFormRem(false)} color="#7f8c8d">Cancelar</Btn>
              </div>
            </Card>
          )}

          {remontajes.map(r => (
            <div key={r.id} style={{
              background: 'var(--color-background-primary)',
              border: '0.5px solid var(--color-border-tertiary)',
              borderLeft: `3px solid ${r.tipo === 'DEL' ? '#8e44ad' : r.tipo === 'BAZ' ? '#27ae60' : '#e67e22'}`,
              borderRadius: '0 8px 8px 0', padding: '10px 14px', marginBottom: '8px',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <strong style={{ fontSize: '13px' }}>{r.tipo_display}</strong>
                  <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginLeft: '8px' }}>— {r.objetivo_display}</span>
                </div>
                <span style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>
                  {r.fecha?.replace('T', ' ').slice(0, 16)}
                </span>
              </div>
              <div style={{ display: 'flex', gap: '14px', fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '4px', flexWrap: 'wrap' }}>
                {r.volumen_bombeado_l && <span>Vol: <strong>{r.volumen_bombeado_l} L</strong></span>}
                {r.duracion_min && <span>Duración: <strong>{r.duracion_min} min</strong></span>}
                {r.temperatura_mosto_c && <span>T° mosto: <strong>{r.temperatura_mosto_c}°C</strong></span>}
                {r.caudal_lh && <span>Caudal: <strong>{r.caudal_lh} L/h</strong></span>}
                {r.tiempo_escurrido_min && <span>Escurrido: <strong>{r.tiempo_escurrido_min} min</strong></span>}
              </div>
              {r.cambio_color && (
                <div style={{ fontSize: '12px', color: '#8e44ad', marginTop: '3px', fontStyle: 'italic' }}>
                  {r.cambio_color}
                </div>
              )}
            </div>
          ))}
          {remontajes.length === 0 && loteId && (
            <p style={{ color: 'var(--color-text-tertiary)', textAlign: 'center', padding: '30px' }}>Sin operaciones registradas para este lote</p>
          )}
        </div>
      )}

      {/* ── SUB-TAB: FML ── */}
      {sub === 'fml' && (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '16px' }}>
          <Card>
            <h4 style={{ margin: '0 0 12px' }}>{fml ? 'Editar seguimiento FML' : 'Iniciar seguimiento FML'}</h4>
            <Select label="Tipo de FML" value={formFml.tipo} onChange={v => setFF('tipo', v)} options={tiposFml} />
            <Select label="Estado" value={formFml.estado} onChange={v => setFF('estado', v)} options={estadosFml} />
            <Input label="Fecha inoculación" value={formFml.fecha_inoculacion} onChange={v => setFF('fecha_inoculacion', v)} type="date" />
            <Input label="Cepa bacteria" value={formFml.cepa_bacteria} onChange={v => setFF('cepa_bacteria', v)} placeholder="Ej: VP41, Enoferm Alpha" />
            <Input label="Dosis (g/hL)" value={formFml.dosis_ghl} onChange={v => setFF('dosis_ghl', v)} type="number" placeholder="2.5" />
            <Input label="Temperatura al inocular (°C)" value={formFml.temperatura_inicio_c} onChange={v => setFF('temperatura_inicio_c', v)} type="number" placeholder="mín 18°C" />
            <Input label="pH al inicio" value={formFml.ph_al_inicio} onChange={v => setFF('ph_al_inicio', v)} type="number" />
            <Input label="SO₂ libre al inicio (mg/L)" value={formFml.so2_libre_al_inicio} onChange={v => setFF('so2_libre_al_inicio', v)} type="number" placeholder="máx 15 mg/L" />
            {formFml.temperatura_inicio_c && parseFloat(formFml.temperatura_inicio_c) < 18 && (
              <div style={{ background: '#FAEEDA', color: '#854F0B', padding: '7px 10px', borderRadius: '5px', fontSize: '12px', marginBottom: '8px' }}>
                ⚠️ Temperatura baja — la bacteria puede inhibirse por debajo de 18°C
              </div>
            )}
            {formFml.so2_libre_al_inicio && parseFloat(formFml.so2_libre_al_inicio) > 15 && (
              <div style={{ background: '#FCEBEB', color: '#A32D2D', padding: '7px 10px', borderRadius: '5px', fontSize: '12px', marginBottom: '8px' }}>
                🚨 SO₂ libre alto — puede inhibir o matar la bacteria maloláctica
              </div>
            )}
            <Input label="Fecha completada" value={formFml.fecha_completada} onChange={v => setFF('fecha_completada', v)} type="date" />
            <Input label="Acidez total post-FML (g/L)" value={formFml.acidez_total_post} onChange={v => setFF('acidez_total_post', v)} type="number" />
            <Btn onClick={guardarFml} color="#16a085" disabled={!loteId}>Guardar FML</Btn>
          </Card>

          <div>
            {fml && (
              <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h4 style={{ margin: 0 }}>Estado FML — {fml.lote_id}</h4>
                  <span style={{ background: fmlEstadoColor[fml.estado] || '#7f8c8d', color: 'white', borderRadius: '6px', padding: '3px 12px', fontSize: '12px', fontWeight: '500' }}>
                    {fml.estado_display}
                  </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '14px' }}>
                  {[
                    { l: 'Tipo', v: fml.tipo_display },
                    { l: 'Cepa', v: fml.cepa_bacteria || '—' },
                    { l: 'Dosis', v: fml.dosis_ghl ? `${fml.dosis_ghl} g/hL` : '—' },
                    { l: 'Temp. inicio', v: fml.temperatura_inicio_c ? `${fml.temperatura_inicio_c}°C` : '—' },
                    { l: 'SO₂ al inicio', v: fml.so2_libre_al_inicio ? `${fml.so2_libre_al_inicio} mg/L` : '—' },
                    { l: 'Duración', v: fml.dias_duracion ? `${fml.dias_duracion} días` : '—' },
                    { l: 'Acidez post', v: fml.acidez_total_post ? `${fml.acidez_total_post} g/L` : '—' },
                  ].map(k => (
                    <div key={k.l} style={{ background: 'var(--color-background-secondary)', borderRadius: '5px', padding: '6px 10px' }}>
                      <div style={{ fontSize: '11px', color: 'var(--color-text-tertiary)' }}>{k.l}</div>
                      <div style={{ fontSize: '13px', fontWeight: '500' }}>{k.v}</div>
                    </div>
                  ))}
                </div>

                {/* Cromatografías */}
                <h4 style={{ margin: '0 0 10px', fontSize: '13px', color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                  Cromatografías de papel ({fml.cromatografias?.length || 0})
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 12px', marginBottom: '12px' }}>
                  <Select label="Resultado" value={formCroma.resultado} onChange={v => setFC('resultado', v)} options={resultCroma} />
                  <Input label="Fecha" value={formCroma.fecha} onChange={v => setFC('fecha', v)} type="date" />
                  <Input label="Temp. vino (°C)" value={formCroma.temperatura_vino} onChange={v => setFC('temperatura_vino', v)} type="number" />
                  <Input label="AV (g/L)" value={formCroma.acidez_volatil} onChange={v => setFC('acidez_volatil', v)} type="number" placeholder="control AV" />
                </div>
                <Btn onClick={agregarCroma} color="#16a085" small>Agregar cromatografía</Btn>

                {fml.cromatografias?.length > 0 && (
                  <div style={{ marginTop: '12px' }}>
                    {fml.cromatografias.map(c => {
                      const bg = c.resultado === 'AU' ? '#EAF3DE' : c.resultado === 'TR' ? '#FAEEDA' : 'var(--color-background-secondary)'
                      const col = c.resultado === 'AU' ? '#27500A' : c.resultado === 'TR' ? '#633806' : 'var(--color-text-primary)'
                      return (
                        <div key={c.id} style={{ background: bg, borderRadius: '5px', padding: '6px 10px', marginBottom: '5px', fontSize: '12px', color: col }}>
                          <strong>{c.fecha}</strong> — {c.resultado_display}
                          {c.temperatura_vino && ` | ${c.temperatura_vino}°C`}
                          {c.acidez_volatil && ` | AV: ${c.acidez_volatil} g/L`}
                        </div>
                      )
                    })}
                  </div>
                )}
              </Card>
            )}
            {!fml && loteId && (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '180px', color: 'var(--color-text-tertiary)' }}>
                ← Completá el formulario para iniciar el seguimiento FML
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// CATA TÉCNICA + GESTIÓN SO₂
// ─────────────────────────────────────────────────────────────────────────────
function CataSO2Tab({ lotes = [] }) {
  const safeLotes = Array.isArray(lotes) ? lotes : []
  const [sub, setSub]       = useState('cata')
  const [loteId, setLoteId] = useState('')
  const [catas, setCatas]   = useState([])
  const [histSO2, setHistSO2] = useState([])
  const [form, setForm]     = useState({ contexto: 'RU', conclusion: 'AP' })
  const [formSO2, setFormSO2] = useState({ so2_molecular_objetivo: 0.5, metodo_medicion: 'Ripper' })
  const [calcResult, setCalcResult] = useState(null)
  const [msg, setMsg]       = useState('')

  const setF  = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const setFS = (k, v) => setFormSO2(f => ({ ...f, [k]: v }))

  const cargarLote = (lid) => {
    setLoteId(lid)
    if (!lid) return
    api(`catas/?lote_id=${lid}`).then(r => setCatas(Array.isArray(r?.data) ? r.data : []))
    api(`so2/?lote_id=${lid}`).then(r => setHistSO2(Array.isArray(r?.data) ? r.data : []))
  }

  // Calculadora live de SO₂ sin guardar
  const calcularSO2 = async () => {
    const { so2_libre_medido, ph_actual, so2_molecular_objetivo } = formSO2
    if (!so2_libre_medido || !ph_actual) return
    const lote = safeLotes.find(l => l.id == loteId)
    const litros = lote?.litros_actuales || 1000
    const r = await api(`so2/calculadora/?libre=${so2_libre_medido}&ph=${ph_actual}&objetivo_molecular=${so2_molecular_objetivo || 0.5}&litros=${litros}`)
    if (r.ok) setCalcResult(r.data)
  }

  const guardarCata = async () => {
    if (!loteId) return setMsg('❌ Seleccioná un lote')
    const r = await api('catas/', 'POST', { ...form, lote_id: loteId, usuario: 'admin' })
    setMsg(r.ok ? `✅ Cata guardada — ${r.data?.conclusion_display || ''}` : '❌ ' + r.msg)
    if (r.ok) {
      cargarLote(loteId)
      setForm({ contexto: 'RU', conclusion: 'AP' })
    }
  }

  const guardarSO2 = async () => {
    if (!loteId) return setMsg('❌ Seleccioná un lote')
    const r = await api('so2/', 'POST', { ...formSO2, lote_id: loteId, fecha: formSO2.fecha || new Date().toISOString(), usuario: 'admin' })
    setMsg(r.ok ? r.data?.alerta || '✅ Guardado' : '❌ ' + r.msg)
    if (r.ok) { cargarLote(loteId); setCalcResult(r.data) }
  }

  const conclusionColor = { AP: '#27ae60', RC: '#e67e22', RE: '#e74c3c', PE: '#7f8c8d' }
  const alertaColor = { OK: '#27ae60', BAJO: '#e67e22', CRITICO: '#e74c3c' }
  const intensidades = [1, 2, 3, 4, 5].map(n => ({ value: n, label: `${n} — ${['Baja','Media-baja','Media','Media-alta','Alta'][n-1]}` }))
  const contextosOpts = [
    { value: 'RU', label: 'Control de rutina' }, { value: 'AE', label: 'Aprobación embotellado' },
    { value: 'CO', label: 'Comparativa de lotes' }, { value: 'BL', label: 'Evaluación previa a blend' },
    { value: 'DE', label: 'Control de defecto' }, { value: 'EX', label: 'Evaluación exportación' },
  ]
  const conclusionesOpts = [
    { value: 'AP', label: 'Apto — continúa normal' }, { value: 'RC', label: 'Requiere corrección' },
    { value: 'RE', label: 'Rechazado' }, { value: 'PE', label: 'Pendiente nueva evaluación' },
  ]

  return (
    <div>
      {msg && (
        <div style={{
          background: msg.includes('CRITICO') || msg.includes('❌') ? '#FCEBEB' : msg.includes('⚠️') ? '#FAEEDA' : '#EAF3DE',
          color: msg.includes('CRITICO') || msg.includes('❌') ? '#A32D2D' : msg.includes('⚠️') ? '#854F0B' : '#27500A',
          padding: '8px 14px', borderRadius: '6px', marginBottom: '12px', fontSize: '13px', fontWeight: '500',
        }}>{msg}</div>
      )}

      <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end', marginBottom: '16px', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '220px' }}>
          <Select label="Lote a evaluar" value={loteId} onChange={cargarLote}
            options={safeLotes.map(l => ({ value: l.id, label: `${l.codigo} — ${l.varietal_nombre} ${l.campaña}` }))} />
        </div>
        <div style={{ display: 'flex', gap: '6px', marginBottom: '10px' }}>
          <Btn onClick={() => setSub('cata')} color={sub === 'cata' ? '#2c3e50' : '#7f8c8d'} small>🍷 Cata técnica</Btn>
          <Btn onClick={() => setSub('so2')} color={sub === 'so2' ? '#2c3e50' : '#7f8c8d'} small>⚗️ Gestión SO₂</Btn>
        </div>
      </div>

      {/* ── SUB-TAB: CATA ── */}
      {sub === 'cata' && (
        <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '16px' }}>
          <Card>
            <h4 style={{ margin: '0 0 12px' }}>Nueva cata técnica</h4>
            <Input label="Fecha *" value={form.fecha} onChange={v => setF('fecha', v)} type="date" />
            <Select label="Contexto" value={form.contexto} onChange={v => setF('contexto', v)} options={contextosOpts} />
            <Input label="Catadores (separados por coma)" value={form.catadores} onChange={v => setF('catadores', v)} placeholder="J. Pérez, M. García" />
            <Input label="Temp. servicio (°C)" value={form.temperatura_servicio} onChange={v => setF('temperatura_servicio', v)} type="number" placeholder="18" />

            <div style={{ background: 'var(--color-background-secondary)', borderRadius: '6px', padding: '10px 12px', margin: '8px 0' }}>
              <p style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', fontWeight: '500', textTransform: 'uppercase', margin: '0 0 8px' }}>Vista</p>
              <Select label="Intensidad" value={form.color_intensidad} onChange={v => setF('color_intensidad', v)} options={intensidades} />
              <Input label="Tonalidad" value={form.color_tonalidad} onChange={v => setF('color_tonalidad', v)} placeholder="Rojo rubí con ribetes violáceos..." />
              <Input label="Limpidez" value={form.color_limpidez} onChange={v => setF('color_limpidez', v)} placeholder="Brillante / Limpio / Turbio" />
            </div>

            <div style={{ background: 'var(--color-background-secondary)', borderRadius: '6px', padding: '10px 12px', margin: '8px 0' }}>
              <p style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', fontWeight: '500', textTransform: 'uppercase', margin: '0 0 8px' }}>Nariz</p>
              <Select label="Intensidad" value={form.nariz_intensidad} onChange={v => setF('nariz_intensidad', v)} options={intensidades} />
              <Input label="Calidad" value={form.nariz_calidad} onChange={v => setF('nariz_calidad', v)} placeholder="Limpio / Con defecto leve..." />
              <Input label="Descriptores" value={form.nariz_descriptores} onChange={v => setF('nariz_descriptores', v)} placeholder="Frutos rojos, especias, vainilla..." />
            </div>

            <div style={{ background: 'var(--color-background-secondary)', borderRadius: '6px', padding: '10px 12px', margin: '8px 0' }}>
              <p style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', fontWeight: '500', textTransform: 'uppercase', margin: '0 0 8px' }}>Boca</p>
              <Input label="Ataque" value={form.boca_ataque} onChange={v => setF('boca_ataque', v)} placeholder="Fresco / Suave / Punzante" />
              <Select label="Acidez" value={form.boca_acidez} onChange={v => setF('boca_acidez', v)} options={intensidades} />
              <Input label="Taninos" value={form.boca_taninos} onChange={v => setF('boca_taninos', v)} placeholder="Sedosos / Firmes / Astringentes..." />
              <Input label="Cuerpo" value={form.boca_cuerpo} onChange={v => setF('boca_cuerpo', v)} placeholder="Ligero / Medio / Amplio" />
              <Input label="Persistencia (segundos)" value={form.boca_final_s} onChange={v => setF('boca_final_s', v)} type="number" />
              <Input label="Balance" value={form.boca_balance} onChange={v => setF('boca_balance', v)} placeholder="Equilibrado / En evolución..." />
            </div>

            <div style={{ background: '#FCEBEB', borderRadius: '6px', padding: '10px 12px', margin: '8px 0' }}>
              <p style={{ fontSize: '11px', color: '#A32D2D', fontWeight: '500', textTransform: 'uppercase', margin: '0 0 8px' }}>Defectos</p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
                {[
                  { k: 'defecto_brett', l: 'Brett (cuero/establo)' },
                  { k: 'defecto_reduccion', l: 'Reducción (azufre)' },
                  { k: 'defecto_va_alta', l: 'VA alta (vinagre)' },
                  { k: 'defecto_oxidacion', l: 'Oxidación' },
                  { k: 'defecto_turbidez', l: 'Turbidez' },
                ].map(d => (
                  <label key={d.k} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', cursor: 'pointer', color: '#791F1F' }}>
                    <input type="checkbox" checked={!!form[d.k]} onChange={e => setF(d.k, e.target.checked)} />
                    {d.l}
                  </label>
                ))}
              </div>
              <Input label="Otro defecto" value={form.defecto_otro} onChange={v => setF('defecto_otro', v)} />
            </div>

            <Input label="Puntaje (0-100)" value={form.puntaje} onChange={v => setF('puntaje', v)} type="number" />
            <Select label="Conclusión *" value={form.conclusion} onChange={v => setF('conclusion', v)} options={conclusionesOpts} />
            <div style={{ marginBottom: '10px' }}>
              <label style={{ fontSize: '12px', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '3px' }}>Acción recomendada</label>
              <textarea value={form.accion_recomendada || ''} onChange={e => setF('accion_recomendada', e.target.value)}
                rows={2} placeholder="Ej: agregar SO₂, trasiego, tiempo de reposo en barrica..."
                style={{ width: '100%', padding: '7px', border: '1px solid var(--color-border-secondary)', borderRadius: '5px', fontSize: '12px', boxSizing: 'border-box', background: 'var(--color-background-primary)', color: 'var(--color-text-primary)' }} />
            </div>
            <Btn onClick={guardarCata} color="#2c3e50">Guardar cata</Btn>
          </Card>

          <div>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px', margin: '0 0 10px' }}>{catas.length} cata{catas.length !== 1 ? 's' : ''} registrada{catas.length !== 1 ? 's' : ''}</p>
            {catas.map(c => (
              <div key={c.id} style={{
                background: 'var(--color-background-primary)',
                border: '0.5px solid var(--color-border-tertiary)',
                borderLeft: `3px solid ${conclusionColor[c.conclusion] || '#ddd'}`,
                borderRadius: '0 8px 8px 0', padding: '12px 16px', marginBottom: '10px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <span style={{ background: conclusionColor[c.conclusion], color: 'white', borderRadius: '4px', padding: '2px 10px', fontSize: '12px', fontWeight: '500' }}>
                      {c.conclusion_display}
                    </span>
                    {c.puntaje && <strong style={{ marginLeft: '10px', fontSize: '16px', color: 'var(--color-text-primary)' }}>{c.puntaje} pts</strong>}
                    {c.tiene_defectos && <Badge text="Defectos detectados" color="#A32D2D" />}
                  </div>
                  <span style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>{c.fecha} · {c.contexto_display}</span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '6px' }}>
                  <strong>Catadores:</strong> {c.catadores}
                </div>
                {c.nariz_descriptores && (
                  <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '3px', fontStyle: 'italic' }}>
                    🍇 {c.nariz_descriptores}
                  </div>
                )}
                {(c.defecto_brett || c.defecto_reduccion || c.defecto_va_alta || c.defecto_oxidacion || c.defecto_otro) && (
                  <div style={{ fontSize: '12px', color: '#A32D2D', marginTop: '4px' }}>
                    ⚠️ Defectos: {[
                      c.defecto_brett && 'Brett',
                      c.defecto_reduccion && 'Reducción',
                      c.defecto_va_alta && 'VA alta',
                      c.defecto_oxidacion && 'Oxidación',
                      c.defecto_otro,
                    ].filter(Boolean).join(', ')}
                  </div>
                )}
                {c.accion_recomendada && (
                  <div style={{ fontSize: '12px', color: '#e67e22', marginTop: '4px' }}>
                    → {c.accion_recomendada}
                  </div>
                )}
              </div>
            ))}
            {catas.length === 0 && loteId && (
              <p style={{ color: 'var(--color-text-tertiary)', textAlign: 'center', padding: '30px' }}>Sin catas registradas</p>
            )}
          </div>
        </div>
      )}

      {/* ── SUB-TAB: SO₂ ── */}
      {sub === 'so2' && (
        <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '16px' }}>
          <div>
            <Card>
              <h4 style={{ margin: '0 0 12px' }}>Calculadora SO₂</h4>
              <div style={{ background: 'var(--color-background-secondary)', borderRadius: '6px', padding: '10px 12px', marginBottom: '10px', fontSize: '12px', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                <strong>Fórmula:</strong><br />
                SO₂ molecular = libre ÷ (1 + 10^(pH − 1.81))<br />
                Objetivo: 0.5 mg/L tintos · 0.8 mg/L blancos/dulces
              </div>
              <Input label="SO₂ libre medido (mg/L) *" value={formSO2.so2_libre_medido} onChange={v => { setFS('so2_libre_medido', v); setCalcResult(null) }} type="number" placeholder="Ej: 28" />
              <Input label="pH actual *" value={formSO2.ph_actual} onChange={v => { setFS('ph_actual', v); setCalcResult(null) }} type="number" placeholder="Ej: 3.45" />
              <Input label="Objetivo SO₂ molecular (mg/L)" value={formSO2.so2_molecular_objetivo} onChange={v => setFS('so2_molecular_objetivo', v)} type="number" placeholder="0.5" />
              <Input label="Temperatura bodega (°C)" value={formSO2.temperatura_bodega_c} onChange={v => setFS('temperatura_bodega_c', v)} type="number" />
              <Input label="Método de medición" value={formSO2.metodo_medicion} onChange={v => setFS('metodo_medicion', v)} placeholder="Ripper / Aeration-Oxidation" />
              <Input label="Fecha medición" value={formSO2.fecha} onChange={v => setFS('fecha', v)} type="datetime-local" />
              <div style={{ display: 'flex', gap: '8px' }}>
                <Btn onClick={calcularSO2} color="#3498db" small>Calcular</Btn>
                <Btn onClick={guardarSO2} color="#2c3e50" disabled={!loteId} small>Guardar y calcular</Btn>
              </div>

              {calcResult && (
                <div style={{ marginTop: '14px', borderTop: '0.5px solid var(--color-border-tertiary)', paddingTop: '12px' }}>
                  <div style={{ background: alertaColor[calcResult.estado] || alertaColor[calcResult.alerta?.split(' ')[0]] || '#27ae60',
                    color: 'white', borderRadius: '6px', padding: '8px 12px', marginBottom: '10px', fontSize: '13px', fontWeight: '500', textAlign: 'center' }}>
                    {calcResult.estado === 'CRITICO' ? '🚨 CRÍTICO' : calcResult.estado === 'BAJO' ? '⚠️ POR DEBAJO' : '✅ EN RANGO'}
                  </div>
                  {[
                    { l: 'SO₂ molecular actual', v: `${calcResult.so2_molecular_actual} mg/L`, emph: true },
                    { l: 'SO₂ libre necesario', v: `${calcResult.so2_libre_necesario} mg/L` },
                    { l: 'Déficit a corregir', v: `${calcResult.deficit_so2 || 0} mg/L` },
                    { l: 'SO₂ puro necesario', v: `${calcResult.gramos_so2_puro || calcResult.gramos_so2_puro} g` },
                    { l: '🧪 Metabisulfito K a agregar', v: `${calcResult.gramos_metabisulfito || calcResult.gramos_metabisulfito_k} g`, emph: true },
                  ].map(k => (
                    <div key={k.l} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', padding: '4px 0', borderBottom: '0.5px solid var(--color-border-tertiary)' }}>
                      <span style={{ color: 'var(--color-text-secondary)' }}>{k.l}</span>
                      <strong style={{ color: k.emph ? 'var(--color-text-primary)' : 'var(--color-text-secondary)' }}>{k.v}</strong>
                    </div>
                  ))}
                  {calcResult.proxima_medicion && (
                    <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--color-text-tertiary)', textAlign: 'center' }}>
                      Próxima medición: <strong>{calcResult.proxima_medicion}</strong>
                    </div>
                  )}
                </div>
              )}
            </Card>
          </div>

          <div>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px', margin: '0 0 10px' }}>
              Historial SO₂ — {histSO2.length} registro{histSO2.length !== 1 ? 's' : ''}
            </p>
            {histSO2.map(g => (
              <div key={g.id} style={{
                background: 'var(--color-background-primary)',
                border: '0.5px solid var(--color-border-tertiary)',
                borderLeft: `3px solid ${alertaColor[g.alerta] || '#27ae60'}`,
                borderRadius: '0 8px 8px 0', padding: '10px 14px', marginBottom: '8px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ background: alertaColor[g.alerta], color: 'white', borderRadius: '4px', padding: '1px 8px', fontSize: '11px', fontWeight: '500' }}>
                    {g.alerta}
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>
                    {g.fecha?.slice(0, 16).replace('T', ' ')}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '16px', fontSize: '12px', marginTop: '6px', flexWrap: 'wrap' }}>
                  <span>SO₂ libre: <strong>{g.so2_libre_medido} mg/L</strong></span>
                  <span>pH: <strong>{g.ph_actual}</strong></span>
                  <span style={{ color: alertaColor[g.alerta] }}>SO₂ molecular: <strong>{g.so2_molecular_actual} mg/L</strong></span>
                  {g.deficit_so2 > 0 && <span style={{ color: '#e67e22' }}>Déficit: <strong>{g.deficit_so2} mg/L</strong></span>}
                  {g.gramos_metabisulfito > 0 && <span style={{ color: '#8e44ad' }}>MBK necesario: <strong>{g.gramos_metabisulfito} g</strong></span>}
                  {g.adicion_realizada && <Badge text={`✅ Adición realizada — ${g.gramos_agregados_real} g`} color="#27ae60" />}
                </div>
                {g.proxima_medicion && (
                  <div style={{ fontSize: '12px', color: 'var(--color-text-tertiary)', marginTop: '4px' }}>
                    Próxima medición: {g.proxima_medicion}
                  </div>
                )}
              </div>
            ))}
            {histSO2.length === 0 && loteId && (
              <p style={{ color: 'var(--color-text-tertiary)', textAlign: 'center', padding: '30px' }}>Sin registros de SO₂</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}