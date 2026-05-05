import { useState, useEffect } from 'react'

const API = `${import.meta.env.VITE_API_URL}/api/bodega`

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
  <button onClick={onClick} disabled={disabled} style={{
    background: disabled ? '#bdc3c7' : color, color: 'white', border: 'none',
    borderRadius: '5px', padding: small ? '4px 10px' : '7px 16px',
    cursor: disabled ? 'default' : 'pointer', fontSize: small ? '12px' : '13px', fontWeight: '600',
  }}>{children}</button>
)

const Card = ({ children, style }) => (
  <div style={{
    background: 'white', borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,.08)', padding: '20px', marginBottom: '16px', ...style,
  }}>{children}</div>
)

const Input = ({ label, value, onChange, type = 'text', required, placeholder, small }) => (
  <div style={{ marginBottom: '10px' }}>
    {label && <label style={{ fontSize: '12px', color: '#7f8c8d', display: 'block', marginBottom: '3px' }}>
      {label}{required && <span style={{ color: '#e74c3c' }}> *</span>}
    </label>}
    <input type={type} value={value || ''} onChange={e => onChange(e.target.value)} placeholder={placeholder}
      style={{ width: '100%', padding: '7px 10px', border: '1px solid #ddd', borderRadius: '5px',
        fontSize: small ? '12px' : '13px', boxSizing: 'border-box' }} />
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

const estadoLoteColor = { EB:'#e67e22', CR:'#8e44ad', LI:'#27ae60', EM:'#2c3e50', EP:'#2980b9', VE:'#16a085', AN:'#c0392b' }
const estadoRecColor  = { LI:'#27ae60', OC:'#e67e22', LA:'#3498db', MN:'#e74c3c', BA:'#95a5a6' }
const movTipoColor    = { IN:'#27ae60', EG:'#c0392b', TR:'#3498db', ME:'#e67e22', CO:'#8e44ad', CL:'#7f8c8d', VE:'#16a085' }

// ─────────────────────────────────────────────────────────────────────────────
// DASHBOARD
// ─────────────────────────────────────────────────────────────────────────────
function DashboardBodega() {
  const [data, setData] = useState(null)
  const [campaña, setCampaña] = useState(new Date().getFullYear())
  useEffect(() => { api(`dashboard/?campaña=${campaña}`).then(r => r.ok && setData(r.data)) }, [campaña])
  const kpiStyle = (color) => ({ background: color, color: 'white', borderRadius: '8px', padding: '16px 20px', textAlign: 'center' })
  if (!data) return <p style={{ color: '#7f8c8d' }}>Cargando dashboard…</p>
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, color: '#2c3e50' }}>Campaña</h3>
        <input type="number" value={campaña} onChange={e => setCampaña(e.target.value)}
          style={{ width: '80px', padding: '5px 8px', border: '1px solid #ddd', borderRadius: '5px' }} />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '12px', marginBottom: '20px' }}>
        <div style={kpiStyle('#e67e22')}><div style={{ fontSize:'11px', opacity:.8 }}>Uva recibida</div><div style={{ fontSize:'24px', fontWeight:'800' }}>{(data.kg_uva_recibidos/1000).toFixed(1)} t</div></div>
        <div style={kpiStyle('#2980b9')}><div style={{ fontSize:'11px', opacity:.8 }}>Litros en stock</div><div style={{ fontSize:'24px', fontWeight:'800' }}>{Math.round(data.litros_en_stock).toLocaleString('es-AR')}</div></div>
        <div style={kpiStyle('#27ae60')}><div style={{ fontSize:'11px', opacity:.8 }}>Recipientes libres</div><div style={{ fontSize:'24px', fontWeight:'800' }}>{data?.recipientes?.libres ?? 0}</div></div>
        <div style={kpiStyle('#8e44ad')}><div style={{ fontSize:'11px', opacity:.8 }}>Barricas ocupadas</div><div style={{ fontSize:'24px', fontWeight:'800' }}>{data?.barricas?.ocupadas ?? 0}</div></div>
        <div style={kpiStyle('#c0392b')}><div style={{ fontSize:'11px', opacity:.8 }}>Tickets pendientes</div><div style={{ fontSize:'24px', fontWeight:'800' }}>{data.tickets_bascula_pendientes}</div></div>
        <div style={kpiStyle('#16a085')}><div style={{ fontSize:'11px', opacity:.8 }}>Órdenes embotellado</div><div style={{ fontSize:'24px', fontWeight:'800' }}>{data.ordenes_embotellado_pendientes}</div></div>
      </div>
      <Card>
        <h4 style={{ margin: '0 0 12px', color: '#2c3e50' }}>Lotes por estado</h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {data.lotes_por_estado.map(e => (
            <span key={e.estado} style={{ background: estadoLoteColor[e.estado] || '#7f8c8d', color:'white', borderRadius:'6px', padding:'6px 14px', fontSize:'13px' }}>
              {e.estado} — {e.cant} lote{e.cant !== 1 ? 's' : ''}
            </span>
          ))}
          {data.lotes_por_estado.length === 0 && <span style={{ color:'#7f8c8d' }}>Sin lotes en esta campaña</span>}
        </div>
      </Card>
    </div>
  )
}


// ─────────────────────────────────────────────────────────────────────────────
// RECEPCIÓN
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
    const r = await api('tickets-bascula/', 'POST', { ...form, campaña, fecha: form.fecha || new Date().toISOString() })
    if (r.ok) { setMsg('✅ ' + r.msg); setForm({}); api(`tickets-bascula/?campaña=${campaña}`).then(r2 => setTickets(Array.isArray(r2?.data) ? r2.data : [])); setMostrando('lista') }
    else setMsg('❌ ' + r.msg)
  }
  const asignar = async (ticketId, loteId) => {
    if (!loteId) return
    const r = await api('tickets-bascula/asignar/', 'POST', { ticket_id: ticketId, lote_id: loteId })
    setMsg(r.ok ? '✅ ' + r.msg : '❌ ' + r.msg)
    api(`tickets-bascula/?campaña=${campaña}`).then(r2 => setTickets(Array.isArray(r2?.data) ? r2.data : []))
  }
  const estadoColor = { PE:'#e67e22', AS:'#27ae60', LI:'#3498db' }
  return (
    <div>
      {msg && <div style={{ background:'#ecf0f1', padding:'8px 12px', borderRadius:'6px', marginBottom:'12px', fontSize:'13px' }}>{msg}</div>}
      <div style={{ display:'flex', gap:'10px', marginBottom:'16px' }}>
        <Btn onClick={() => setMostrando('lista')} color={mostrando==='lista'?'#2c3e50':'#7f8c8d'}>Lista de tickets</Btn>
        <Btn onClick={() => setMostrando('nuevo')} color="#27ae60">+ Nuevo ticket</Btn>
      </div>
      {mostrando === 'nuevo' && (
        <Card>
          <h4 style={{ margin:'0 0 14px', color:'#2c3e50' }}>Registrar recepción de uva</h4>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0 16px' }}>
            <Select label="Varietal *" value={form.varietal} onChange={v => setF('varietal', v)} options={varietales.map(v => ({ value:v.codigo, label:v.nombre }))} />
            <Input label="Fecha" value={form.fecha} onChange={v => setF('fecha', v)} type="datetime-local" />
            <Input label="Patente camión" value={form.patente_camion} onChange={v => setF('patente_camion', v)} placeholder="ABC 123" />
            <Input label="Proveedor / viñatero" value={form.nombre_prov} onChange={v => setF('nombre_prov', v)} />
            <Input label="Peso bruto (kg) *" value={form.peso_bruto} onChange={v => setF('peso_bruto', v)} type="number" />
            <Input label="Tara (kg)" value={form.tara} onChange={v => setF('tara', v)} type="number" />
            <Input label="°Brix" value={form.brix_entrada} onChange={v => setF('brix_entrada', v)} type="number" />
            <Input label="pH" value={form.ph_entrada} onChange={v => setF('ph_entrada', v)} type="number" />
            <Input label="Precio $/kg" value={form.precio_kg} onChange={v => setF('precio_kg', v)} type="number" />
            <Select label="Estado sanitario" value={form.estado_sanitario} onChange={v => setF('estado_sanitario', v)} options={['Óptimo','Bueno','Regular','Malo'].map(s=>({value:s,label:s}))} />
          </div>
          {form.peso_bruto && form.tara && <div style={{ background:'#eaf4fb', padding:'8px 12px', borderRadius:'6px', fontSize:'13px', marginBottom:'10px' }}>Peso neto estimado: <strong>{(form.peso_bruto - form.tara).toLocaleString('es-AR')} kg</strong></div>}
          <div style={{ display:'flex', gap:'8px' }}>
            <Btn onClick={guardar} color="#27ae60">Guardar ticket</Btn>
            <Btn onClick={() => setMostrando('lista')} color="#7f8c8d">Cancelar</Btn>
          </div>
        </Card>
      )}
      {mostrando === 'lista' && (
        <div>
          <p style={{ color:'#7f8c8d', fontSize:'13px', margin:'0 0 10px' }}>{tickets.length} ticket{tickets.length!==1?'s':''} — campaña {campaña}</p>
          <div style={{ overflowX:'auto' }}>
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:'13px' }}>
              <thead><tr style={{ background:'#2c3e50', color:'white' }}>
                {['#','Varietal','Proveedor','Fecha','Kg neto','Brix','Estado','Asignar a lote'].map(h => <th key={h} style={{ padding:'8px 10px', textAlign:'left' }}>{h}</th>)}
              </tr></thead>
              <tbody>
                {tickets.map((t,i) => (
                  <tr key={t.id} style={{ background: i%2===0?'white':'#f8f9fa' }}>
                    <td style={{ padding:'7px 10px' }}>{t.id}</td>
                    <td style={{ padding:'7px 10px' }}>{t.varietal_nombre}</td>
                    <td style={{ padding:'7px 10px' }}>{t.nombre_prov||'—'}</td>
                    <td style={{ padding:'7px 10px' }}>{t.fecha?.slice(0,16).replace('T',' ')}</td>
                    <td style={{ padding:'7px 10px', fontWeight:'700' }}>{t.peso_neto?.toLocaleString('es-AR')}</td>
                    <td style={{ padding:'7px 10px' }}>{t.brix_entrada||'—'}°</td>
                    <td style={{ padding:'7px 10px' }}><span style={{ background:estadoColor[t.estado]||'#7f8c8d', color:'white', borderRadius:'4px', padding:'2px 8px', fontSize:'11px' }}>{t.estado_display}</span></td>
                    <td style={{ padding:'7px 10px' }}>
                      {t.estado==='PE' ? (
                        <select defaultValue="" onChange={e => asignar(t.id, e.target.value)} style={{ padding:'3px 6px', fontSize:'12px', border:'1px solid #ddd', borderRadius:'4px' }}>
                          <option value="">— lote —</option>
                          {lotes.filter(l=>['EB','LI'].includes(l.estado)).map(l => <option key={l.id} value={l.id}>{l.codigo} — {l.varietal_nombre}</option>)}
                        </select>
                      ) : <span style={{ color:'#7f8c8d', fontSize:'12px' }}>{t.lote_destino_codigo||'—'}</span>}
                    </td>
                  </tr>
                ))}
                {tickets.length===0 && <tr><td colSpan={8} style={{ padding:'20px', textAlign:'center', color:'#7f8c8d' }}>Sin tickets registrados</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}


// ─────────────────────────────────────────────────────────────────────────────
// LOTES DE GRANEL — MEJORA: formularios de operaciones, análisis y movimientos
// ─────────────────────────────────────────────────────────────────────────────
function LotesTab({ varietales = [], recipientes = [] }) {
  const [lotes, setLotes]       = useState([])
  const [form, setForm]         = useState({})
  const [selected, setSelected] = useState(null)
  const [ops, setOps]           = useState([])
  const [analisis, setAnalisis] = useState([])
  const [movimientos, setMovimientos] = useState([])
  const [insumos, setInsumos]   = useState([])
  const [msg, setMsg]           = useState('')
  const [tab2, setTab2]         = useState('ops')
  // Sub-formularios
  const [formOp,  setFormOp]    = useState({ tipo:'AIC' })
  const [formAn,  setFormAn]    = useState({ origen:'INT' })
  const [formMov, setFormMov]   = useState({ tipo:'TR' })
  const [showFormOp,  setShowFormOp]  = useState(false)
  const [showFormAn,  setShowFormAn]  = useState(false)
  const [showFormMov, setShowFormMov] = useState(false)
  const [alertasFicha, setAlertasFicha] = useState([])

  useEffect(() => {
    api('lotes/').then(r => setLotes(Array.isArray(r?.data) ? r.data : []))
    api('insumos/').then(r => setInsumos(Array.isArray(r?.data) ? r.data : []))
  }, [])

  const setF  = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const setFO = (k, v) => setFormOp(f => ({ ...f, [k]: v }))
  const setFA = (k, v) => setFormAn(f => ({ ...f, [k]: v }))
  const setFM = (k, v) => setFormMov(f => ({ ...f, [k]: v }))

  const recargarLotes = () => api('lotes/').then(r => setLotes(Array.isArray(r?.data) ? r.data : []))

  const guardar = async () => {
    const r = await api('lotes/', 'POST', form)
    if (r.ok) { setMsg('✅ ' + r.msg); recargarLotes(); setForm({}) } else setMsg('❌ ' + r.msg)
  }

  const seleccionar = (lote) => {
    setSelected(lote); setAlertasFicha([])
    api(`operaciones/?lote_id=${lote.id}`).then(r => setOps(Array.isArray(r?.data) ? r.data : []))
    api(`analisis/?lote_id=${lote.id}`).then(r => setAnalisis(Array.isArray(r?.data) ? r.data : []))
    api(`movimientos/?lote_id=${lote.id}`).then(r => setMovimientos(Array.isArray(r?.data) ? r.data : []))
  }

  const guardarOp = async () => {
    if (!selected) return setMsg('❌ Seleccioná un lote')
    const r = await api('operaciones/', 'POST', {
      ...formOp, lote_id: selected.id,
      fecha: formOp.fecha || new Date().toISOString(), usuario: 'admin',
    })
    setMsg(r.ok ? '✅ ' + r.msg : '❌ ' + r.msg)
    if (r.ok) {
      setShowFormOp(false); setFormOp({ tipo:'AIC' })
      api(`operaciones/?lote_id=${selected.id}`).then(r2 => setOps(Array.isArray(r2?.data) ? r2.data : []))
    }
  }

  const guardarAnalisis = async () => {
    if (!selected) return setMsg('❌ Seleccioná un lote')
    const r = await api('analisis/', 'POST', { ...formAn, lote_id: selected.id, usuario: 'admin' })
    setMsg(r.ok ? '✅ ' + r.msg : '❌ ' + r.msg)
    if (r.ok) {
      setAlertasFicha(r.data?.alertas_ficha || [])
      setShowFormAn(false); setFormAn({ origen:'INT' })
      api(`analisis/?lote_id=${selected.id}`).then(r2 => setAnalisis(Array.isArray(r2?.data) ? r2.data : []))
    }
  }

  const guardarMov = async () => {
    if (!selected) return setMsg('❌ Seleccioná un lote')
    const r = await api('movimientos/', 'POST', {
      ...formMov, lote_id: selected.id,
      fecha: formMov.fecha || new Date().toISOString(), usuario: 'admin',
    })
    setMsg(r.ok ? '✅ ' + r.msg : '❌ ' + r.msg)
    if (r.ok) {
      setShowFormMov(false); setFormMov({ tipo:'TR' })
      api(`movimientos/?lote_id=${selected.id}`).then(r2 => setMovimientos(Array.isArray(r2?.data) ? r2.data : []))
      recargarLotes()
    }
  }

  const tiposOp = [
    {value:'AIC',label:'Adición de insumo/corrector'},{value:'CLA',label:'Clarificación'},
    {value:'FIL',label:'Filtración'},{value:'SOL',label:'Sulfitado'},
    {value:'FER',label:'Fermentación (registro)'},{value:'COR',label:'Corrección enológica'},{value:'OTR',label:'Otra práctica'},
  ]
  const tiposVino   = [{value:'TI',label:'Tinto'},{value:'BL',label:'Blanco'},{value:'RO',label:'Rosado'},{value:'ES',label:'Espumante'}]
  const estadosLote = ['EB','CR','LI','EM','EP','VE','AN'].map(e=>({value:e,label:e}))
  const tiposMov    = [
    {value:'IN',label:'Ingreso'},{value:'EG',label:'Egreso'},
    {value:'TR',label:'Trasvase entre recipientes'},{value:'ME',label:'Merma declarada'},
    {value:'CO',label:'Coupage / Mezcla'},{value:'VE',label:'Venta a granel'},
  ]
  const origenes = [{value:'INT',label:'Lab. interno'},{value:'EXT',label:'Lab. externo'},{value:'INV',label:'INV'}]

  const inlineForm = (bg, border) => ({
    background: bg, border: `1px solid ${border}`, borderRadius: '8px', padding: '14px', marginBottom: '14px',
  })

  return (
    <div style={{ display:'grid', gridTemplateColumns:'340px 1fr', gap:'16px' }}>
      {/* Panel izquierdo */}
      <div>
        <Card>
          <h4 style={{ margin:'0 0 12px', color:'#2c3e50' }}>{form.id ? 'Editar lote' : 'Nuevo lote'}</h4>
          {msg && <div style={{ fontSize:'12px', marginBottom:'8px', color: msg.startsWith('✅')?'#27ae60':'#c0392b' }}>{msg}</div>}
          <Input label="Código *" value={form.codigo} onChange={v => setF('codigo',v)} placeholder="2024-MAL-001" />
          <Select label="Varietal *" value={form.varietal} onChange={v => setF('varietal',v)} options={varietales.map(v=>({value:v.codigo,label:v.nombre}))} />
          <Select label="Tipo de vino" value={form.tipo_vino} onChange={v => setF('tipo_vino',v)} options={tiposVino} />
          <Input label="Campaña *" value={form.campaña} onChange={v => setF('campaña',v)} type="number" placeholder={new Date().getFullYear()} />
          <Input label="Fecha inicio" value={form.fecha_inicio} onChange={v => setF('fecha_inicio',v)} type="date" />
          <Input label="Litros iniciales" value={form.litros_iniciales} onChange={v => setF('litros_iniciales',v)} type="number" />
          <Select label="Recipiente actual" value={form.recipiente_id} onChange={v => setF('recipiente_id',v)} options={recipientes.map(r=>({value:r.id,label:`${r.codigo} — ${r.nombre}`}))} />
          <Select label="Estado" value={form.estado} onChange={v => setF('estado',v)} options={estadosLote} />
          <Input label="Descripción" value={form.descripcion} onChange={v => setF('descripcion',v)} />
          <div style={{ display:'flex', gap:'8px' }}>
            <Btn onClick={guardar} color="#8e44ad">Guardar lote</Btn>
            {form.id && <Btn onClick={() => setForm({})} color="#7f8c8d">Nuevo</Btn>}
          </div>
        </Card>
        <p style={{ color:'#7f8c8d', fontSize:'12px', margin:'0 0 8px' }}>{lotes.length} lote{lotes.length!==1?'s':''}</p>
        {lotes.map(l => (
          <div key={l.id} onClick={() => seleccionar(l)} style={{
            background: selected?.id===l.id ? '#eaf4fb' : 'white',
            border: `2px solid ${selected?.id===l.id ? '#2980b9' : '#ecf0f1'}`,
            borderRadius:'8px', padding:'10px 14px', marginBottom:'8px', cursor:'pointer',
          }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
              <strong style={{ fontSize:'13px' }}>{l.codigo}</strong>
              <span style={{ background:estadoLoteColor[l.estado]||'#7f8c8d', color:'white', borderRadius:'4px', padding:'1px 7px', fontSize:'11px' }}>{l.estado}</span>
            </div>
            <div style={{ fontSize:'12px', color:'#7f8c8d', marginTop:'2px' }}>
              {l.varietal_nombre} {l.campaña} · {Math.round(l.litros_actuales||0).toLocaleString('es-AR')} L
            </div>
          </div>
        ))}
      </div>

      {/* Panel derecho */}
      {selected ? (
        <div>
          <Card>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
              <div>
                <h3 style={{ margin:'0 0 4px', color:'#2c3e50' }}>{selected.codigo}</h3>
                <p style={{ margin:0, color:'#7f8c8d', fontSize:'13px' }}>{selected.varietal_nombre} — {selected.tipo_vino_display} — Campaña {selected.campaña}</p>
              </div>
              <div style={{ textAlign:'right' }}>
                <div style={{ fontSize:'22px', fontWeight:'800', color:'#2980b9' }}>{Math.round(selected.litros_actuales||0).toLocaleString('es-AR')} L</div>
                <div style={{ fontSize:'12px', color:'#7f8c8d' }}>de {Math.round(selected.litros_iniciales||0).toLocaleString('es-AR')} L iniciales</div>
              </div>
            </div>
            <div style={{ marginTop:'10px', background:'#f8f9fa', borderRadius:'6px', height:'8px', overflow:'hidden' }}>
              <div style={{ background:'#2980b9', height:'100%', width:`${selected.litros_iniciales>0?Math.min(100,(selected.litros_actuales/selected.litros_iniciales)*100):0}%` }} />
            </div>
            <div style={{ fontSize:'11px', color:'#7f8c8d', marginTop:'3px' }}>Merma acumulada: {Math.round(selected.merma_total||0).toLocaleString('es-AR')} L</div>
          </Card>

          <div style={{ display:'flex', gap:'8px', marginBottom:'12px' }}>
            {[['ops','⚗️ Operaciones'],['analisis','🔬 Análisis'],['movimientos','🔄 Movimientos']].map(([t,l]) => (
              <Btn key={t} onClick={() => setTab2(t)} color={tab2===t?'#2c3e50':'#7f8c8d'} small>{l}</Btn>
            ))}
          </div>

          {/* ── TAB Operaciones ── */}
          {tab2 === 'ops' && (
            <Card>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'12px' }}>
                <h4 style={{ margin:0 }}>Operaciones enológicas</h4>
                <Btn onClick={() => setShowFormOp(!showFormOp)} color="#e67e22" small>{showFormOp?'Cancelar':'+ Nueva operación'}</Btn>
              </div>
              {showFormOp && (
                <div style={inlineForm('#fef9ef','#f0c040')}>
                  <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0 14px' }}>
                    <Select label="Tipo *" value={formOp.tipo} onChange={v => setFO('tipo',v)} options={tiposOp} />
                    <Input label="Fecha y hora *" value={formOp.fecha} onChange={v => setFO('fecha',v)} type="datetime-local" />
                    <div style={{ gridColumn:'1/-1' }}><Input label="Descripción *" value={formOp.descripcion} onChange={v => setFO('descripcion',v)} placeholder="Detalle de la operación..." /></div>
                    {formOp.tipo === 'AIC' && <>
                      <Select label="Insumo" value={formOp.insumo_id} onChange={v => setFO('insumo_id',v)} options={insumos.map(i=>({value:i.id,label:`${i.nombre} (${i.tipo_display})`}))} />
                      <Input label="Cantidad" value={formOp.cantidad_insumo} onChange={v => setFO('cantidad_insumo',v)} type="number" />
                      <Input label="Unidad" value={formOp.unidad_insumo} onChange={v => setFO('unidad_insumo',v)} placeholder="kg / g / L" />
                      <Input label="Lote proveedor insumo" value={formOp.lote_insumo_prov} onChange={v => setFO('lote_insumo_prov',v)} />
                    </>}
                    {formOp.tipo === 'FER' && <>
                      <Input label="Temperatura °C" value={formOp.temperatura} onChange={v => setFO('temperatura',v)} type="number" />
                      <Input label="Densidad g/L" value={formOp.densidad} onChange={v => setFO('densidad',v)} type="number" />
                      <Input label="Grado real %" value={formOp.grado_real} onChange={v => setFO('grado_real',v)} type="number" />
                    </>}
                    <div style={{ gridColumn:'1/-1' }}><Input label="Resultado observado" value={formOp.resultado} onChange={v => setFO('resultado',v)} /></div>
                  </div>
                  <Btn onClick={guardarOp} color="#e67e22">Guardar operación</Btn>
                </div>
              )}
              {ops.length===0 ? <p style={{ color:'#7f8c8d', fontSize:'13px' }}>Sin operaciones registradas</p>
              : ops.map(op => (
                <div key={op.id} style={{ borderBottom:'1px solid #ecf0f1', paddingBottom:'8px', marginBottom:'8px' }}>
                  <div style={{ display:'flex', justifyContent:'space-between', fontSize:'13px' }}>
                    <strong>{op.tipo_display}</strong>
                    <span style={{ color:'#7f8c8d' }}>{op.fecha?.slice(0,16).replace('T',' ')}</span>
                  </div>
                  <div style={{ fontSize:'12px', color:'#7f8c8d' }}>{op.descripcion}</div>
                  {op.insumo_nombre && <div style={{ fontSize:'12px', color:'#8e44ad' }}>{op.insumo_nombre}: {op.cantidad_insumo} {op.unidad_insumo}</div>}
                  {op.densidad && <div style={{ fontSize:'12px', color:'#e67e22' }}>Densidad: {op.densidad} | °real: {op.grado_real}% | T°: {op.temperatura}°C</div>}
                </div>
              ))}
            </Card>
          )}

          {/* ── TAB Análisis ── */}
          {tab2 === 'analisis' && (
            <Card>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'12px' }}>
                <h4 style={{ margin:0 }}>Análisis de laboratorio</h4>
                <Btn onClick={() => setShowFormAn(!showFormAn)} color="#3498db" small>{showFormAn?'Cancelar':'+ Nuevo análisis'}</Btn>
              </div>
              {alertasFicha.length > 0 && (
                <div style={{ background:'#FAEEDA', border:'1px solid #f0c040', borderRadius:'6px', padding:'10px 14px', marginBottom:'12px' }}>
                  <strong style={{ fontSize:'13px', color:'#633806' }}>⚠️ Parámetros fuera de spec (ficha técnica)</strong>
                  {alertasFicha.map((a,i) => (
                    <div key={i} style={{ fontSize:'12px', color:'#854F0B', marginTop:'4px' }}>
                      {a.etiqueta}: <strong>{a.valor}</strong> {a.unidad||''} — límite {a.tipo==='alto'?'máx':'mín'}: {a.limite} {a.unidad||''}
                    </div>
                  ))}
                </div>
              )}
              {showFormAn && (
                <div style={inlineForm('#eaf4fb','#85b7eb')}>
                  <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0 14px' }}>
                    <Input label="Fecha *" value={formAn.fecha} onChange={v => setFA('fecha',v)} type="date" />
                    <Select label="Origen" value={formAn.origen} onChange={v => setFA('origen',v)} options={origenes} />
                    <Input label="Laboratorio" value={formAn.laboratorio} onChange={v => setFA('laboratorio',v)} placeholder="Nombre del lab." />
                    <Input label="Grado alcohólico (%)" value={formAn.grado_alcohol} onChange={v => setFA('grado_alcohol',v)} type="number" />
                    <Input label="Acidez total (g/L)" value={formAn.acidez_total} onChange={v => setFA('acidez_total',v)} type="number" />
                    <Input label="Acidez volátil (g/L)" value={formAn.acidez_volatil} onChange={v => setFA('acidez_volatil',v)} type="number" />
                    <Input label="pH" value={formAn.ph} onChange={v => setFA('ph',v)} type="number" />
                    <Input label="Azúcar residual (g/L)" value={formAn.azucar_residual} onChange={v => setFA('azucar_residual',v)} type="number" />
                    <Input label="SO₂ libre (mg/L)" value={formAn.so2_libre} onChange={v => setFA('so2_libre',v)} type="number" />
                    <Input label="SO₂ total (mg/L)" value={formAn.so2_total} onChange={v => setFA('so2_total',v)} type="number" />
                    <Input label="Turbidez (NTU)" value={formAn.turbidez_ntu} onChange={v => setFA('turbidez_ntu',v)} type="number" />
                    <Select label="Resultado" value={formAn.aprobado} onChange={v => setFA('aprobado',v)}
                      options={[{value:'true',label:'✅ Aprobado'},{value:'false',label:'❌ Rechazado'},{value:'',label:'⏳ Pendiente'}]} />
                  </div>
                  <Input label="Observaciones" value={formAn.observaciones} onChange={v => setFA('observaciones',v)} />
                  <Btn onClick={guardarAnalisis} color="#3498db">Guardar análisis</Btn>
                </div>
              )}
              {analisis.length===0 ? <p style={{ color:'#7f8c8d', fontSize:'13px' }}>Sin análisis registrados</p>
              : <div style={{ overflowX:'auto' }}>
                  <table style={{ width:'100%', borderCollapse:'collapse', fontSize:'12px' }}>
                    <thead><tr style={{ background:'#f8f9fa' }}>
                      {['Fecha','Origen','°Alc','Acid.T','Acid.V','pH','Az.Res','SO2L','SO2T','Est.'].map(h => <th key={h} style={{ padding:'6px 8px', textAlign:'left', color:'#7f8c8d' }}>{h}</th>)}
                    </tr></thead>
                    <tbody>
                      {analisis.map(a => (
                        <tr key={a.id} style={{ borderBottom:'1px solid #f0f0f0' }}>
                          <td style={{ padding:'5px 8px' }}>{a.fecha}</td>
                          <td style={{ padding:'5px 8px' }}>{a.origen}</td>
                          <td style={{ padding:'5px 8px' }}>{a.grado_alcohol??'—'}</td>
                          <td style={{ padding:'5px 8px' }}>{a.acidez_total??'—'}</td>
                          <td style={{ padding:'5px 8px' }}>{a.acidez_volatil??'—'}</td>
                          <td style={{ padding:'5px 8px' }}>{a.ph??'—'}</td>
                          <td style={{ padding:'5px 8px' }}>{a.azucar_residual??'—'}</td>
                          <td style={{ padding:'5px 8px' }}>{a.so2_libre??'—'}</td>
                          <td style={{ padding:'5px 8px' }}>{a.so2_total??'—'}</td>
                          <td style={{ padding:'5px 8px' }}>{a.aprobado===null?'⏳':a.aprobado?'✅':'❌'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>}
            </Card>
          )}

          {/* ── TAB Movimientos ── */}
          {tab2 === 'movimientos' && (
            <Card>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'12px' }}>
                <h4 style={{ margin:0 }}>Movimientos de granel (libro de bodega)</h4>
                <Btn onClick={() => setShowFormMov(!showFormMov)} color="#2c3e50" small>{showFormMov?'Cancelar':'+ Registrar movimiento'}</Btn>
              </div>
              {showFormMov && (
                <div style={inlineForm('#f4f0fb','#afa9ec')}>
                  <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0 14px' }}>
                    <Select label="Tipo *" value={formMov.tipo} onChange={v => setFM('tipo',v)} options={tiposMov} />
                    <Input label="Fecha y hora *" value={formMov.fecha} onChange={v => setFM('fecha',v)} type="datetime-local" />
                    <Input label="Litros *" value={formMov.litros} onChange={v => setFM('litros',v)} type="number" />
                    <Input label="Temperatura °C" value={formMov.temperatura} onChange={v => setFM('temperatura',v)} type="number" />
                    <Select label="Recipiente origen" value={formMov.recipiente_origen_id} onChange={v => setFM('recipiente_origen_id',v)} options={recipientes.map(r=>({value:r.id,label:`${r.codigo} — ${r.nombre}`}))} />
                    <Select label="Recipiente destino" value={formMov.recipiente_destino_id} onChange={v => setFM('recipiente_destino_id',v)} options={recipientes.map(r=>({value:r.id,label:`${r.codigo} — ${r.nombre}`}))} />
                    <div style={{ gridColumn:'1/-1' }}><Input label="Descripción" value={formMov.descripcion} onChange={v => setFM('descripcion',v)} /></div>
                  </div>
                  <Btn onClick={guardarMov} color="#2c3e50">Guardar movimiento</Btn>
                </div>
              )}
              {movimientos.length===0 ? <p style={{ color:'#7f8c8d', fontSize:'13px' }}>Sin movimientos registrados</p>
              : movimientos.map(m => (
                <div key={m.id} style={{ borderLeft:`3px solid ${movTipoColor[m.tipo]||'#7f8c8d'}`, padding:'7px 12px', marginBottom:'6px', borderRadius:'0 6px 6px 0', background:'#f8f9fa' }}>
                  <div style={{ display:'flex', justifyContent:'space-between', fontSize:'13px' }}>
                    <strong style={{ color:movTipoColor[m.tipo] }}>{m.tipo_display}</strong>
                    <span style={{ color:'#7f8c8d' }}>{m.fecha?.slice(0,16).replace('T',' ')}</span>
                  </div>
                  <div style={{ display:'flex', gap:'14px', fontSize:'12px', color:'#7f8c8d', marginTop:'2px', flexWrap:'wrap' }}>
                    <span style={{ fontWeight:'700', color:'#2c3e50' }}>{parseFloat(m.litros).toLocaleString('es-AR')} L</span>
                    {m.recipiente_origen && <span>De: {m.recipiente_origen}</span>}
                    {m.recipiente_destino && <span>→ {m.recipiente_destino}</span>}
                    {m.descripcion && <span style={{ fontStyle:'italic' }}>{m.descripcion}</span>}
                  </div>
                </div>
              ))}
            </Card>
          )}
        </div>
      ) : (
        <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'200px', color:'#bdc3c7', fontSize:'15px' }}>
          ← Seleccioná un lote para ver su detalle
        </div>
      )}
    </div>
  )
}


// ─────────────────────────────────────────────────────────────────────────────
// VIÑEDO — MEJORA: tratamientos con formulario + sub-tabs contratos/liquidaciones
// ─────────────────────────────────────────────────────────────────────────────
function VinedoTab({ varietales = [] }) {
  const [parcelas, setParcelas]   = useState([])
  const [labores, setLabores]     = useState([])
  const [tratos, setTratos]       = useState([])
  const [contratos, setContratos] = useState([])
  const [liquidaciones, setLiquidaciones] = useState([])
  const [selected, setSelected]   = useState(null)
  const [sub, setSub]             = useState('parcelas')   // ← default: lista de parcelas
  const [formP, setFormP]   = useState({ tipo:'P' })       // alta/edición parcela
  const [formL, setFormL]   = useState({})                 // labor
  const [formT, setFormT]   = useState({})                 // tratamiento
  const [formC, setFormC]   = useState({ tipo_precio:'FI' }) // contrato
  const [formLiq, setFormLiq] = useState({})               // liquidación
  const [showFormT, setShowFormT]   = useState(false)
  const [showFormC, setShowFormC]   = useState(false)
  const [showFormLiq, setShowFormLiq] = useState(false)
  const [editParcela, setEditParcela] = useState(false)    // true = editar parcela existente
  const [msg, setMsg] = useState('')
  const campaña = new Date().getFullYear()

  const setFP  = (k,v) => setFormP(f => ({...f,[k]:v}))
  const setFL  = (k,v) => setFormL(f => ({...f,[k]:v}))
  const setFT  = (k,v) => setFormT(f => ({...f,[k]:v}))
  const setFC  = (k,v) => setFormC(f => ({...f,[k]:v}))
  const setFLiq = (k,v) => setFormLiq(f => ({...f,[k]:v}))

  const cargarParcelas = () =>
    api('parcelas/').then(r => setParcelas(Array.isArray(r?.data) ? r.data : []))

  useEffect(() => {
    cargarParcelas()
    api(`contratos-uva/?campaña=${campaña}`).then(r => setContratos(Array.isArray(r?.data) ? r.data : []))
    api(`liquidaciones-uva/?campaña=${campaña}`).then(r => setLiquidaciones(Array.isArray(r?.data) ? r.data : []))
  }, [])

  // Al seleccionar una parcela cargamos sus labores y tratamientos
  const seleccionar = (p) => {
    setSelected(p); setEditParcela(false)
    api(`labores/?parcela_id=${p.id}&campaña=${campaña}`).then(r => setLabores(Array.isArray(r?.data) ? r.data : []))
    api(`tratamientos/?parcela_id=${p.id}&campaña=${campaña}`).then(r => setTratos(Array.isArray(r?.data) ? r.data : []))
  }

  // Ir directo a labores o tratamientos desde la tarjeta de parcela
  const irA = (p, destino) => {
    seleccionar(p)
    setSub(destino)
  }

  // ── Guardar parcela (nueva o edición) ────────────────────────────────────
  const guardarParcela = async () => {
    if (!formP.nombre || !formP.varietal || !formP.superficie_ha)
      return setMsg('❌ Nombre, varietal y superficie son obligatorios')
    const r = await api('parcelas/', 'POST', { ...formP, activa: true, usuario:'admin' })
    if (r.ok) {
      setMsg('✅ Parcela guardada')
      setFormP({ tipo:'P' }); setEditParcela(false)
      cargarParcelas()
      // Si editamos la seleccionada, actualizar el selected
      if (formP.id) seleccionar({ ...selected, ...formP })
    } else setMsg('❌ ' + r.msg)
  }

  const empezarEdicion = (p) => {
    setFormP({ id:p.id, nombre:p.nombre, varietal:p.varietal, tipo:p.tipo,
               superficie_ha:p.superficie_ha, finca:p.finca, zona:p.zona,
               anio_plantacion:p.anio_plantacion, altitud_msnm:p.altitud_msnm,
               cod_prov:p.cod_prov })
    setEditParcela(true)
  }

  const guardarLabor = async () => {
    if (!selected) return setMsg('❌ Seleccioná una parcela primero')
    const r = await api('labores/', 'POST', { ...formL, parcela_id:selected.id, campaña, usuario:'admin' })
    if (r.ok) {
      setMsg('✅ Labor registrada'); setFormL({})
      api(`labores/?parcela_id=${selected.id}&campaña=${campaña}`).then(r2 => setLabores(Array.isArray(r2?.data) ? r2.data : []))
    } else setMsg('❌ ' + r.msg)
  }

  const guardarTrato = async () => {
    if (!selected) return setMsg('❌ Seleccioná una parcela primero')
    const r = await api('tratamientos/', 'POST', { ...formT, parcela_id:selected.id, campaña, usuario:'admin' })
    if (r.ok) {
      setMsg('✅ Tratamiento registrado'); setFormT({}); setShowFormT(false)
      api(`tratamientos/?parcela_id=${selected.id}&campaña=${campaña}`).then(r2 => setTratos(Array.isArray(r2?.data) ? r2.data : []))
    } else setMsg('❌ ' + r.msg)
  }

  const guardarContrato = async () => {
    const r = await api('contratos-uva/', 'POST', { ...formC, campaña, usuario:'admin' })
    if (r.ok) {
      setMsg('✅ Contrato guardado'); setFormC({ tipo_precio:'FI' }); setShowFormC(false)
      api(`contratos-uva/?campaña=${campaña}`).then(r2 => setContratos(Array.isArray(r2?.data) ? r2.data : []))
    } else setMsg('❌ ' + r.msg)
  }

  const guardarLiq = async () => {
    const r = await api('liquidaciones-uva/', 'POST', { ...formLiq, campaña, usuario:'admin' })
    if (r.ok) {
      const neto = r.data?.importe_neto
      setMsg(`✅ Liquidación por $${parseFloat(neto||0).toLocaleString('es-AR')}`)
      setFormLiq({}); setShowFormLiq(false)
      api(`liquidaciones-uva/?campaña=${campaña}`).then(r2 => setLiquidaciones(Array.isArray(r2?.data) ? r2.data : []))
    } else setMsg('❌ ' + r.msg)
  }

  // ── Opciones de selects ───────────────────────────────────────────────────
  const tiposLabor   = [{value:'POD',label:'Poda'},{value:'DES',label:'Desbrote'},
    {value:'VEV',label:'Vendimia en verde'},{value:'COS',label:'Cosecha'},
    {value:'RIE',label:'Riego'},{value:'FER',label:'Fertilización'},
    {value:'LAB',label:'Laboreo de suelo'},{value:'OTR',label:'Otra'}]
  const tiposParcela = [{value:'P',label:'Propia'},{value:'T',label:'Terceros'}]
  const tiposPrecio  = [{value:'FI',label:'Precio fijo'},{value:'GR',label:'Por grado brix'},
    {value:'ME',label:'Mercado'},{value:'AC',label:'A confirmar'}]
  const COLOR_VAR    = { TI:'#8e44ad', MA:'#8e44ad', CA:'#2c3e50', ME:'#c0392b',
                         CH:'#f39c12', VI:'#7f8c8d', BO:'#c0392b', TO:'#8B4513' }
  const colorVar = (cod) => COLOR_VAR[cod?.slice(0,2).toUpperCase()] || '#7f8c8d'

  const SUBTABS = [
    { id:'parcelas',     label:'🌿 Parcelas' },
    { id:'labores',      label:'🌱 Labores' },
    { id:'tratamientos', label:'🧪 Tratamientos' },
    { id:'contratos',    label:'📝 Contratos uva' },
    { id:'liquidaciones',label:'💵 Liquidaciones' },
  ]

  return (
    <div>
      {msg && (
        <div style={{ padding:'8px 14px', borderRadius:'7px', fontSize:'13px', marginBottom:'12px',
          background:msg.startsWith('✅')?'#EAF7EE':'#FCEBEB',
          color:msg.startsWith('✅')?'#1A6634':'#A32D2D', fontWeight:'600' }}>
          {msg}
        </div>
      )}

      {/* Sub-tabs */}
      <div style={{ display:'flex', gap:'4px', marginBottom:'18px', flexWrap:'wrap' }}>
        {SUBTABS.map(t => (
          <button key={t.id} onClick={() => setSub(t.id)} style={{
            padding:'7px 16px', border:'none', cursor:'pointer', borderRadius:'6px',
            fontWeight:'600', fontSize:'13px',
            background: sub === t.id ? '#2c3e50' : '#ecf0f1',
            color:       sub === t.id ? 'white'    : '#7f8c8d',
          }}>{t.label}</button>
        ))}
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          PARCELAS — lista completa + alta/edición
         ═══════════════════════════════════════════════════════════════════ */}
      {sub === 'parcelas' && (
        <div style={{ display:'grid', gridTemplateColumns:'360px 1fr', gap:'20px', alignItems:'start' }}>

          {/* Formulario alta / edición */}
          <div style={{ background:'white', borderRadius:'10px', padding:'18px',
            boxShadow:'0 2px 8px rgba(0,0,0,.07)',
            border: editParcela ? '2px solid #e67e22' : '2px solid #ecf0f1' }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'14px' }}>
              <h4 style={{ margin:0, fontSize:'14px', color:'#2c3e50', fontWeight:'700' }}>
                {editParcela ? '✏️ Editar parcela' : '➕ Nueva parcela'}
              </h4>
              {editParcela && (
                <button onClick={() => { setFormP({tipo:'P'}); setEditParcela(false) }}
                  style={{ background:'none', border:'1px solid #ddd', borderRadius:'5px',
                    padding:'3px 10px', cursor:'pointer', fontSize:'12px', color:'#7f8c8d' }}>
                  Cancelar
                </button>
              )}
            </div>
            <Input label="Nombre *" value={formP.nombre} onChange={v=>setFP('nombre',v)} placeholder="Cuartel Norte 3" />
            <Select label="Varietal *" value={formP.varietal} onChange={v=>setFP('varietal',v)}
              options={varietales.map(v=>({value:v.codigo,label:v.nombre}))} />
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0 12px' }}>
              <Select label="Tipo" value={formP.tipo} onChange={v=>setFP('tipo',v)} options={tiposParcela} />
              <Input label="Superficie (ha) *" value={formP.superficie_ha} onChange={v=>setFP('superficie_ha',v)} type="number" placeholder="2.5" />
              <Input label="Finca" value={formP.finca} onChange={v=>setFP('finca',v)} placeholder="Finca Los Álamos" />
              <Input label="Zona / DOC" value={formP.zona} onChange={v=>setFP('zona',v)} placeholder="Luján de Cuyo" />
              <Input label="Año de plantación" value={formP.anio_plantacion} onChange={v=>setFP('anio_plantacion',v)} type="number" />
              <Input label="Altitud (msnm)" value={formP.altitud_msnm} onChange={v=>setFP('altitud_msnm',v)} type="number" />
            </div>
            {formP.tipo === 'T' && (
              <Input label="Cód. proveedor viñatero" value={formP.cod_prov} onChange={v=>setFP('cod_prov',v)} type="number" />
            )}
            <button onClick={guardarParcela} style={{
              width:'100%', padding:'10px', marginTop:'4px',
              background: editParcela ? '#e67e22' : '#27ae60',
              color:'white', border:'none', borderRadius:'7px',
              cursor:'pointer', fontWeight:'700', fontSize:'13px',
            }}>
              {editParcela ? 'Guardar cambios' : 'Crear parcela'}
            </button>
          </div>

          {/* Lista de parcelas */}
          <div>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'12px' }}>
              <h4 style={{ margin:0, color:'#2c3e50' }}>
                {parcelas.length} parcela{parcelas.length !== 1 ? 's' : ''} registrada{parcelas.length !== 1 ? 's' : ''}
              </h4>
              <span style={{ fontSize:'12px', color:'#7f8c8d' }}>Campaña {campaña}</span>
            </div>

            {parcelas.length === 0 ? (
              <div style={{ background:'white', borderRadius:'10px', padding:'40px',
                textAlign:'center', color:'#bdc3c7', boxShadow:'0 2px 8px rgba(0,0,0,.07)' }}>
                <div style={{ fontSize:'40px', marginBottom:'10px' }}>🌿</div>
                <p style={{ margin:0, fontSize:'14px' }}>No hay parcelas registradas aún.</p>
                <p style={{ margin:'6px 0 0', fontSize:'12px' }}>Usá el formulario de la izquierda para crear la primera.</p>
              </div>
            ) : (
              <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(250px,1fr))', gap:'12px' }}>
                {parcelas.map(p => (
                  <div key={p.id} style={{ background:'white', borderRadius:'10px', padding:'14px 16px',
                    boxShadow:'0 2px 8px rgba(0,0,0,.07)',
                    border: selected?.id === p.id ? '2px solid #27ae60' : '1px solid #ecf0f1',
                    transition:'box-shadow .15s',
                  }}>
                    {/* Cabecera tarjeta */}
                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:'8px' }}>
                      <div>
                        <strong style={{ fontSize:'14px', color:'#2c3e50' }}>{p.nombre}</strong>
                        <div style={{ fontSize:'12px', color:'#7f8c8d', marginTop:'2px' }}>
                          {p.varietal_nombre} · {p.superficie_ha} ha
                        </div>
                      </div>
                      <span style={{ background: colorVar(p.varietal) + '22',
                        color: colorVar(p.varietal),
                        borderRadius:'5px', padding:'2px 8px', fontSize:'11px', fontWeight:'700',
                        flexShrink:0, marginLeft:'8px' }}>
                        {p.tipo === 'P' ? 'Propia' : 'Terceros'}
                      </span>
                    </div>

                    {/* Info adicional */}
                    {(p.zona || p.finca) && (
                      <div style={{ fontSize:'11px', color:'#95a5a6', marginBottom:'6px' }}>
                        📍 {[p.finca, p.zona].filter(Boolean).join(' · ')}
                      </div>
                    )}
                    {p.anio_plantacion && (
                      <div style={{ fontSize:'11px', color:'#95a5a6', marginBottom:'6px' }}>
                        🗓️ Plantación: {p.anio_plantacion}
                        {p.altitud_msnm && ` · ${p.altitud_msnm} msnm`}
                      </div>
                    )}

                    {/* Acciones */}
                    <div style={{ display:'flex', gap:'6px', marginTop:'10px', borderTop:'1px solid #f0f0f0', paddingTop:'10px' }}>
                      <button onClick={() => irA(p, 'labores')} style={{
                        flex:1, padding:'5px 0', background:'#f0f7ff', color:'#2980b9',
                        border:'1px solid #d0e8f8', borderRadius:'5px', cursor:'pointer',
                        fontSize:'11px', fontWeight:'600',
                      }}>🌱 Labores</button>
                      <button onClick={() => irA(p, 'tratamientos')} style={{
                        flex:1, padding:'5px 0', background:'#fff5f5', color:'#e74c3c',
                        border:'1px solid #fdd', borderRadius:'5px', cursor:'pointer',
                        fontSize:'11px', fontWeight:'600',
                      }}>🧪 Tratam.</button>
                      <button onClick={() => empezarEdicion(p)} style={{
                        padding:'5px 10px', background:'#f8f9fa', color:'#7f8c8d',
                        border:'1px solid #ddd', borderRadius:'5px', cursor:'pointer',
                        fontSize:'11px', fontWeight:'600',
                      }}>✏️</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════
          LABORES
         ═══════════════════════════════════════════════════════════════════ */}
      {sub === 'labores' && (
        <div style={{ display:'grid', gridTemplateColumns:'220px 1fr', gap:'16px' }}>
          {/* Selector de parcela */}
          <div>
            <p style={{ fontSize:'11px', fontWeight:'700', color:'#7f8c8d', textTransform:'uppercase',
              letterSpacing:'.5px', margin:'0 0 8px' }}>Parcela</p>
            {parcelas.length === 0 ? (
              <div style={{ background:'white', borderRadius:'8px', padding:'14px', fontSize:'12px',
                color:'#7f8c8d', textAlign:'center', border:'1px solid #ecf0f1' }}>
                No hay parcelas.<br/>
                <button onClick={() => setSub('parcelas')}
                  style={{ background:'none', border:'none', cursor:'pointer', color:'#27ae60',
                    fontWeight:'600', fontSize:'12px', marginTop:'6px' }}>
                  + Crear una
                </button>
              </div>
            ) : parcelas.map(p => (
              <div key={p.id} onClick={() => seleccionar(p)} style={{
                background: selected?.id===p.id ? '#eaf6ee' : 'white',
                border: `2px solid ${selected?.id===p.id ? '#27ae60' : '#ecf0f1'}`,
                borderRadius:'8px', padding:'9px 12px', marginBottom:'6px', cursor:'pointer',
              }}>
                <strong style={{ fontSize:'12px' }}>{p.nombre}</strong>
                <div style={{ fontSize:'11px', color:'#7f8c8d' }}>{p.varietal_nombre} · {p.superficie_ha} ha</div>
              </div>
            ))}
          </div>

          {/* Labores */}
          {selected ? (
            <div>
              <Card>
                <h4 style={{ margin:'0 0 4px', color:'#27ae60' }}>{selected.nombre}</h4>
                <p style={{ margin:'0 0 14px', color:'#7f8c8d', fontSize:'13px' }}>{selected.varietal_nombre} · Campaña {campaña}</p>
                <h5 style={{ margin:'0 0 10px', color:'#2c3e50', fontSize:'13px' }}>Registrar labor</h5>
                <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0 14px' }}>
                  <Select label="Tipo *" value={formL.tipo} onChange={v=>setFL('tipo',v)} options={tiposLabor} />
                  <Input label="Fecha inicio *" value={formL.fecha_inicio} onChange={v=>setFL('fecha_inicio',v)} type="date" />
                  <Input label="Fecha fin" value={formL.fecha_fin} onChange={v=>setFL('fecha_fin',v)} type="date" />
                  <Input label="Responsable" value={formL.responsable} onChange={v=>setFL('responsable',v)} />
                  <Input label="Jornales" value={formL.jornales} onChange={v=>setFL('jornales',v)} type="number" />
                  <Input label="Costo jornal $" value={formL.costo_jornal} onChange={v=>setFL('costo_jornal',v)} type="number" />
                  <Input label="Costo maquinaria $" value={formL.costo_maquinaria} onChange={v=>setFL('costo_maquinaria',v)} type="number" />
                  <Input label="Costo insumos $" value={formL.costo_insumos} onChange={v=>setFL('costo_insumos',v)} type="number" />
                </div>
                <Btn onClick={guardarLabor} color="#27ae60">Guardar labor</Btn>
              </Card>
              <Card>
                <h4 style={{ margin:'0 0 10px' }}>Labores campaña {campaña} ({labores.length})</h4>
                {labores.length === 0
                  ? <p style={{ color:'#7f8c8d', fontSize:'13px' }}>Sin labores registradas</p>
                  : <table style={{ width:'100%', borderCollapse:'collapse', fontSize:'12px' }}>
                      <thead><tr style={{ background:'#f8f9fa' }}>
                        {['Tipo','Fecha inicio','Jornales','Costo total','Responsable'].map(h =>
                          <th key={h} style={{ padding:'6px 8px', textAlign:'left', color:'#7f8c8d' }}>{h}</th>)}
                      </tr></thead>
                      <tbody>{labores.map(l => (
                        <tr key={l.id} style={{ borderBottom:'1px solid #f0f0f0' }}>
                          <td style={{ padding:'5px 8px' }}><strong>{l.tipo_display}</strong></td>
                          <td style={{ padding:'5px 8px' }}>{l.fecha_inicio}</td>
                          <td style={{ padding:'5px 8px' }}>{l.jornales}</td>
                          <td style={{ padding:'5px 8px', color:'#27ae60', fontWeight:'700' }}>
                            ${parseFloat(l.costo_total||0).toLocaleString('es-AR')}
                          </td>
                          <td style={{ padding:'5px 8px', color:'#7f8c8d' }}>{l.responsable||'—'}</td>
                        </tr>
                      ))}</tbody>
                    </table>}
              </Card>
            </div>
          ) : (
            <div style={{ display:'flex', alignItems:'center', justifyContent:'center',
              height:'200px', color:'#bdc3c7', fontSize:'14px' }}>
              ← Seleccioná una parcela
            </div>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════
          TRATAMIENTOS
         ═══════════════════════════════════════════════════════════════════ */}
      {sub === 'tratamientos' && (
        <div style={{ display:'grid', gridTemplateColumns:'220px 1fr', gap:'16px' }}>
          <div>
            <p style={{ fontSize:'11px', fontWeight:'700', color:'#7f8c8d', textTransform:'uppercase',
              letterSpacing:'.5px', margin:'0 0 8px' }}>Parcela</p>
            {parcelas.length === 0 ? (
              <div style={{ background:'white', borderRadius:'8px', padding:'14px', fontSize:'12px',
                color:'#7f8c8d', textAlign:'center', border:'1px solid #ecf0f1' }}>
                <button onClick={() => setSub('parcelas')} style={{ background:'none', border:'none',
                  cursor:'pointer', color:'#27ae60', fontWeight:'600', fontSize:'12px' }}>
                  + Crear parcela primero
                </button>
              </div>
            ) : parcelas.map(p => (
              <div key={p.id} onClick={() => seleccionar(p)} style={{
                background: selected?.id===p.id ? '#fff0f0' : 'white',
                border: `2px solid ${selected?.id===p.id ? '#e74c3c' : '#ecf0f1'}`,
                borderRadius:'8px', padding:'9px 12px', marginBottom:'6px', cursor:'pointer',
              }}>
                <strong style={{ fontSize:'12px' }}>{p.nombre}</strong>
                <div style={{ fontSize:'11px', color:'#7f8c8d' }}>{p.varietal_nombre}</div>
              </div>
            ))}
          </div>
          {selected ? (
            <Card>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'12px' }}>
                <div>
                  <h4 style={{ margin:'0 0 2px', color:'#e74c3c' }}>{selected.nombre}</h4>
                  <p style={{ margin:0, fontSize:'12px', color:'#7f8c8d' }}>{selected.varietal_nombre} · Campaña {campaña}</p>
                </div>
                <Btn onClick={() => setShowFormT(!showFormT)} color="#e74c3c" small>
                  {showFormT ? 'Cancelar' : '+ Nuevo tratamiento'}
                </Btn>
              </div>
              {showFormT && (
                <div style={{ background:'#fff5f5', border:'1px solid #fdd', borderRadius:'8px',
                  padding:'14px', marginBottom:'14px' }}>
                  <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0 14px' }}>
                    <Input label="Fecha *" value={formT.fecha} onChange={v=>setFT('fecha',v)} type="date" />
                    <Input label="Producto *" value={formT.producto} onChange={v=>setFT('producto',v)} placeholder="Nombre comercial" />
                    <Input label="Principio activo" value={formT.principio_activo} onChange={v=>setFT('principio_activo',v)} />
                    <Input label="Dosis aplicada *" value={formT.dosis_aplicada} onChange={v=>setFT('dosis_aplicada',v)} type="number" />
                    <Input label="Unidad" value={formT.unidad} onChange={v=>setFT('unidad',v)} placeholder="cc/ha" />
                    <Input label="Días de carencia" value={formT.dias_carencia} onChange={v=>setFT('dias_carencia',v)} type="number" />
                    <Input label="Objetivo (plaga/enf.)" value={formT.objetivo} onChange={v=>setFT('objetivo',v)} />
                    <Input label="Operario" value={formT.operario} onChange={v=>setFT('operario',v)} />
                    <Input label="Costo $" value={formT.costo} onChange={v=>setFT('costo',v)} type="number" />
                    <Input label="Lote del producto" value={formT.lote_producto} onChange={v=>setFT('lote_producto',v)} />
                  </div>
                  <Btn onClick={guardarTrato} color="#e74c3c">Guardar tratamiento</Btn>
                </div>
              )}
              {tratos.length === 0
                ? <p style={{ color:'#7f8c8d', fontSize:'13px' }}>Sin tratamientos registrados para esta campaña</p>
                : <table style={{ width:'100%', borderCollapse:'collapse', fontSize:'12px' }}>
                    <thead><tr style={{ background:'#f8f9fa' }}>
                      {['Fecha','Producto','Dosis','Objetivo','Carencia','Fin carencia'].map(h =>
                        <th key={h} style={{ padding:'6px 8px', textAlign:'left', color:'#7f8c8d' }}>{h}</th>)}
                    </tr></thead>
                    <tbody>{tratos.map(t => (
                      <tr key={t.id} style={{ borderBottom:'1px solid #f0f0f0' }}>
                        <td style={{ padding:'5px 8px' }}>{t.fecha}</td>
                        <td style={{ padding:'5px 8px' }}><strong>{t.producto}</strong><br/><span style={{ color:'#7f8c8d', fontSize:'11px' }}>{t.principio_activo}</span></td>
                        <td style={{ padding:'5px 8px' }}>{t.dosis_aplicada} {t.unidad}</td>
                        <td style={{ padding:'5px 8px', color:'#7f8c8d' }}>{t.objetivo||'—'}</td>
                        <td style={{ padding:'5px 8px' }}>{t.dias_carencia}d</td>
                        <td style={{ padding:'5px 8px', color:'#e74c3c', fontWeight:'600' }}>{t.fecha_fin_carencia||'—'}</td>
                      </tr>
                    ))}</tbody>
                  </table>}
            </Card>
          ) : (
            <div style={{ display:'flex', alignItems:'center', justifyContent:'center',
              height:'200px', color:'#bdc3c7', fontSize:'14px' }}>
              ← Seleccioná una parcela
            </div>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════
          CONTRATOS UVA
         ═══════════════════════════════════════════════════════════════════ */}
      {sub === 'contratos' && (
        <div>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'14px' }}>
            <h4 style={{ margin:0 }}>Contratos de compra de uva — campaña {campaña}</h4>
            <Btn onClick={() => setShowFormC(!showFormC)} color="#8e44ad" small>
              {showFormC ? 'Cancelar' : '+ Nuevo contrato'}
            </Btn>
          </div>
          {showFormC && (
            <Card>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0 16px' }}>
                <Input label="Nombre proveedor / viñatero *" value={formC.nombre_prov} onChange={v=>setFC('nombre_prov',v)} />
                <Input label="Cód. proveedor ERP" value={formC.cod_prov} onChange={v=>setFC('cod_prov',v)} type="number" />
                <Select label="Varietal *" value={formC.varietal} onChange={v=>setFC('varietal',v)}
                  options={varietales.map(v=>({value:v.codigo,label:v.nombre}))} />
                <Input label="Kg estimados" value={formC.kg_estimados} onChange={v=>setFC('kg_estimados',v)} type="number" />
                <Select label="Tipo de precio" value={formC.tipo_precio} onChange={v=>setFC('tipo_precio',v)} options={tiposPrecio} />
                <Input label="Precio base $/kg" value={formC.precio_base_kg} onChange={v=>setFC('precio_base_kg',v)} type="number" />
                <Input label="Anticipo $" value={formC.anticipo} onChange={v=>setFC('anticipo',v)} type="number" />
              </div>
              <div style={{ marginBottom:'10px' }}>
                <label style={{ fontSize:'12px', color:'#7f8c8d', display:'block', marginBottom:'3px', fontWeight:'600' }}>
                  Condiciones / observaciones
                </label>
                <textarea value={formC.condiciones||''} onChange={e=>setFC('condiciones',e.target.value)} rows={2}
                  style={{ width:'100%', padding:'7px', border:'1px solid #ddd', borderRadius:'5px',
                    fontSize:'13px', boxSizing:'border-box' }} />
              </div>
              <Btn onClick={guardarContrato} color="#8e44ad">Guardar contrato</Btn>
            </Card>
          )}
          {contratos.length === 0
            ? <p style={{ color:'#7f8c8d', textAlign:'center', padding:'30px' }}>Sin contratos para esta campaña</p>
            : contratos.map(c => (
                <div key={c.id} style={{ background:'white', border:'1px solid #ecf0f1',
                  borderLeft:'4px solid #8e44ad', borderRadius:'8px', padding:'12px 16px', marginBottom:'10px' }}>
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
                    <div>
                      <strong style={{ fontSize:'14px' }}>{c.nombre_prov}</strong>
                      <span style={{ fontSize:'12px', color:'#8e44ad', marginLeft:'10px' }}>{c.varietal_nombre}</span>
                    </div>
                    <span style={{ fontSize:'12px', color:'#7f8c8d' }}>{c.tipo_precio_display}</span>
                  </div>
                  <div style={{ display:'flex', gap:'16px', fontSize:'12px', color:'#7f8c8d', marginTop:'6px', flexWrap:'wrap' }}>
                    {c.kg_estimados && <span>Kg est.: <strong>{parseFloat(c.kg_estimados).toLocaleString('es-AR')}</strong></span>}
                    {c.precio_base_kg && <span>Precio: <strong>${c.precio_base_kg}/kg</strong></span>}
                    {c.anticipo > 0 && <span>Anticipo: <strong>${parseFloat(c.anticipo).toLocaleString('es-AR')}</strong></span>}
                    {c.condiciones && <span style={{ fontStyle:'italic' }}>{c.condiciones}</span>}
                  </div>
                </div>
              ))}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════
          LIQUIDACIONES
         ═══════════════════════════════════════════════════════════════════ */}
      {sub === 'liquidaciones' && (
        <div>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'14px' }}>
            <h4 style={{ margin:0 }}>Liquidaciones de uva — campaña {campaña}</h4>
            <Btn onClick={() => setShowFormLiq(!showFormLiq)} color="#16a085" small>
              {showFormLiq ? 'Cancelar' : '+ Nueva liquidación'}
            </Btn>
          </div>
          {showFormLiq && (
            <Card>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0 16px' }}>
                <Input label="Proveedor *" value={formLiq.nombre_prov} onChange={v=>setFLiq('nombre_prov',v)} />
                <Input label="Cód. proveedor ERP *" value={formLiq.cod_prov} onChange={v=>setFLiq('cod_prov',v)} type="number" />
                <Input label="Fecha *" value={formLiq.fecha} onChange={v=>setFLiq('fecha',v)} type="date" />
                <Input label="Kg liquidados *" value={formLiq.kg_liquidados} onChange={v=>setFLiq('kg_liquidados',v)} type="number" />
                <Input label="Precio $/kg *" value={formLiq.precio_kg} onChange={v=>setFLiq('precio_kg',v)} type="number" />
                <Input label="Descuentos $" value={formLiq.descuentos} onChange={v=>setFLiq('descuentos',v)} type="number" />
                <Input label="Anticipo aplicado $" value={formLiq.anticipo_aplicado} onChange={v=>setFLiq('anticipo_aplicado',v)} type="number" />
              </div>
              {formLiq.kg_liquidados && formLiq.precio_kg && (
                <div style={{ background:'#eaf6ee', padding:'8px 12px', borderRadius:'6px',
                  fontSize:'13px', marginBottom:'10px', fontWeight:'600', color:'#1A6634' }}>
                  Importe neto estimado: ${(
                    parseFloat(formLiq.kg_liquidados) * parseFloat(formLiq.precio_kg)
                    - parseFloat(formLiq.descuentos||0)
                    - parseFloat(formLiq.anticipo_aplicado||0)
                  ).toLocaleString('es-AR')}
                </div>
              )}
              <Btn onClick={guardarLiq} color="#16a085">Crear liquidación</Btn>
            </Card>
          )}
          {liquidaciones.length === 0
            ? <p style={{ color:'#7f8c8d', textAlign:'center', padding:'30px' }}>Sin liquidaciones para esta campaña</p>
            : <table style={{ width:'100%', borderCollapse:'collapse', fontSize:'13px', background:'white',
                boxShadow:'0 1px 3px rgba(0,0,0,.1)', borderRadius:'8px', overflow:'hidden' }}>
                <thead><tr style={{ background:'#2c3e50', color:'white' }}>
                  {['Proveedor','Fecha','Kg liq.','Precio/kg','Importe bruto','Desc.','Anticipo','Neto','Estado'].map(h =>
                    <th key={h} style={{ padding:'8px 10px', textAlign:'left' }}>{h}</th>)}
                </tr></thead>
                <tbody>
                  {liquidaciones.map((l,i) => (
                    <tr key={l.id} style={{ background:i%2===0?'white':'#f8f9fa', borderBottom:'1px solid #f0f0f0' }}>
                      <td style={{ padding:'7px 10px' }}>{l.nombre_prov}</td>
                      <td style={{ padding:'7px 10px' }}>{l.fecha}</td>
                      <td style={{ padding:'7px 10px' }}>{parseFloat(l.kg_liquidados).toLocaleString('es-AR')}</td>
                      <td style={{ padding:'7px 10px' }}>${l.precio_kg}</td>
                      <td style={{ padding:'7px 10px' }}>${parseFloat(l.importe_bruto).toLocaleString('es-AR')}</td>
                      <td style={{ padding:'7px 10px', color:'#c0392b' }}>-${parseFloat(l.descuentos).toLocaleString('es-AR')}</td>
                      <td style={{ padding:'7px 10px', color:'#c0392b' }}>-${parseFloat(l.anticipo_aplicado).toLocaleString('es-AR')}</td>
                      <td style={{ padding:'7px 10px', fontWeight:'700', color:'#27ae60' }}>
                        ${parseFloat(l.importe_neto).toLocaleString('es-AR')}
                      </td>
                      <td style={{ padding:'7px 10px' }}>
                        <span style={{ background:l.estado==='PA'?'#27ae60':l.estado==='EM'?'#3498db':'#e67e22',
                          color:'white', borderRadius:'4px', padding:'2px 8px', fontSize:'11px' }}>
                          {l.estado_display}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>}
        </div>
      )}
    </div>
  )
}

function CalidadTab({ lotes = [], varietales = [] }) {
  const safeLotes = Array.isArray(lotes) ? lotes : []
  const [fichas, setFichas]   = useState([])
  const [ncs, setNcs]         = useState([])
  const [form, setForm]       = useState({})
  const [formNC, setFormNC]   = useState({})
  const [sub, setSub]         = useState('fichas')
  const [msg, setMsg]         = useState('')
  const [ncAbierta, setNcAbierta] = useState(null) // NC expandida para acciones

  useEffect(() => {
    api('fichas-producto/').then(r => setFichas(Array.isArray(r?.data) ? r.data : []))
    api('no-conformidades/').then(r => setNcs(Array.isArray(r?.data) ? r.data : []))
  }, [])

  const setF  = (k,v) => setForm(f=>({...f,[k]:v}))
  const setFN = (k,v) => setFormNC(f=>({...f,[k]:v}))

  const guardarFicha = async () => {
    const r = await api('fichas-producto/', 'POST', { ...form, usuario:'admin' })
    if (r.ok) { setMsg('✅ Ficha guardada'); setForm({}); api('fichas-producto/').then(r2=>setFichas(Array.isArray(r2?.data)?r2.data:[])) }
    else setMsg('❌ ' + r.msg)
  }

  const guardarNC = async () => {
    const r = await api('no-conformidades/', 'POST', { ...formNC, usuario:'admin' })
    if (r.ok) { setMsg('✅ NC registrada'); setFormNC({}); api('no-conformidades/').then(r2=>setNcs(Array.isArray(r2?.data)?r2.data:[])) }
    else setMsg('❌ ' + r.msg)
  }

  // MEJORA: cambio de estado directo sin recrear el registro
  const cambiarEstadoNC = async (ncId, nuevoEstado, accionCorrectiva) => {
    const r = await api('no-conformidades/', 'POST', {
      accion:'cambiar_estado', id:ncId, estado:nuevoEstado,
      accion_correctiva: accionCorrectiva || '',
      usuario:'admin',
    })
    if (r.ok) {
      setMsg(`✅ NC #${ncId} → ${r.data?.estado_display}`)
      setNcAbierta(null)
      api('no-conformidades/').then(r2=>setNcs(Array.isArray(r2?.data)?r2.data:[]))
    } else setMsg('❌ ' + r.msg)
  }

  const gravedadColor = { L:'#27ae60', M:'#e67e22', G:'#e74c3c', C:'#8e44ad' }
  const estadoNCColor = { AB:'#e74c3c', EN:'#e67e22', CE:'#27ae60', RE:'#8e44ad' }
  const estadoNCNext  = { AB:'EN', EN:'CE', CE:'AB' }  // transición circular
  const estadoNCLabel = { AB:'→ En tratamiento', EN:'→ Cerrar NC', CE:'→ Reabrir' }
  const tiposVino     = [{value:'TI',label:'Tinto'},{value:'BL',label:'Blanco'},{value:'RO',label:'Rosado'},{value:'ES',label:'Espumante'}]
  const gravedades    = [{value:'L',label:'Leve'},{value:'M',label:'Moderada'},{value:'G',label:'Grave'},{value:'C',label:'Crítica'}]

  return (
    <div>
      {msg && <div style={{ background:msg.startsWith('✅')?'#EAF3DE':'#FCEBEB', color:msg.startsWith('✅')?'#27500A':'#A32D2D', padding:'8px 12px', borderRadius:'6px', marginBottom:'12px', fontSize:'13px' }}>{msg}</div>}
      <div style={{ display:'flex', gap:'8px', marginBottom:'16px' }}>
        {['fichas','nc'].map(s=><Btn key={s} onClick={()=>setSub(s)} color={sub===s?'#2c3e50':'#7f8c8d'} small>{s==='fichas'?'📄 Fichas de producto':'⚠️ No conformidades'}</Btn>)}
      </div>

      {sub==='fichas' && (
        <div style={{ display:'grid', gridTemplateColumns:'320px 1fr', gap:'16px' }}>
          <Card>
            <h4 style={{ margin:'0 0 12px' }}>Nueva ficha técnica</h4>
            <Input label="Código *" value={form.codigo} onChange={v=>setF('codigo',v)} placeholder="FT-MAL-RSV" />
            <Input label="Nombre *" value={form.nombre} onChange={v=>setF('nombre',v)} placeholder="Malbec Reserva" />
            <Select label="Varietal" value={form.varietal} onChange={v=>setF('varietal',v)} options={varietales.map(v=>({value:v.codigo,label:v.nombre}))} />
            <Select label="Tipo de vino" value={form.tipo_vino} onChange={v=>setF('tipo_vino',v)} options={tiposVino} />
            <p style={{ fontSize:'11px', color:'#7f8c8d', fontWeight:'700', textTransform:'uppercase', margin:'8px 0 6px' }}>Rangos analíticos</p>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0 10px' }}>
              <Input label="Alcohol mín" value={form.alcohol_min} onChange={v=>setF('alcohol_min',v)} type="number" small />
              <Input label="Alcohol máx" value={form.alcohol_max} onChange={v=>setF('alcohol_max',v)} type="number" small />
              <Input label="pH mín" value={form.ph_min} onChange={v=>setF('ph_min',v)} type="number" small />
              <Input label="pH máx" value={form.ph_max} onChange={v=>setF('ph_max',v)} type="number" small />
              <Input label="Acid. total mín (g/L)" value={form.acidez_total_min} onChange={v=>setF('acidez_total_min',v)} type="number" small />
              <Input label="Acid. total máx (g/L)" value={form.acidez_total_max} onChange={v=>setF('acidez_total_max',v)} type="number" small />
              <Input label="SO₂ libre máx (mg/L)" value={form.so2_libre_max} onChange={v=>setF('so2_libre_max',v)} type="number" small />
              <Input label="SO₂ total máx (mg/L)" value={form.so2_total_max} onChange={v=>setF('so2_total_max',v)} type="number" small />
            </div>
            <div style={{ marginBottom:'10px' }}>
              <label style={{ fontSize:'12px', color:'#7f8c8d', display:'block', marginBottom:'3px' }}>Perfil sensorial</label>
              <textarea value={form.perfil_sensorial||''} onChange={e=>setF('perfil_sensorial',e.target.value)} rows={2} placeholder="Rojo rubí, frutos negros, taninos sedosos..." style={{ width:'100%', padding:'7px', border:'1px solid #ddd', borderRadius:'5px', fontSize:'12px', boxSizing:'border-box' }} />
            </div>
            <Btn onClick={guardarFicha} color="#16a085">Guardar ficha</Btn>
          </Card>
          <div>
            {fichas.map(f=>(
              <div key={f.id} style={{ background:'white', border:'1px solid #ecf0f1', borderRadius:'8px', padding:'12px 16px', marginBottom:'10px', borderLeft:'4px solid #16a085' }}>
                <div style={{ display:'flex', justifyContent:'space-between' }}>
                  <strong>{f.codigo} — {f.nombre}</strong>
                  <span style={{ color:'#7f8c8d', fontSize:'12px' }}>{f.varietal||'—'}</span>
                </div>
                {f.perfil_sensorial && <div style={{ fontSize:'12px', color:'#7f8c8d', marginTop:'4px', fontStyle:'italic' }}>{f.perfil_sensorial.slice(0,100)}</div>}
                <div style={{ display:'flex', gap:'12px', fontSize:'12px', marginTop:'6px', flexWrap:'wrap' }}>
                  {f.alcohol_min && <span>🍷 {f.alcohol_min}–{f.alcohol_max}% alc.</span>}
                  {f.ph_min && <span>⚗️ pH {f.ph_min}–{f.ph_max}</span>}
                  {f.so2_total_max && <span>SO₂ ≤{f.so2_total_max} mg/L</span>}
                </div>
              </div>
            ))}
            {fichas.length===0 && <p style={{ color:'#7f8c8d', textAlign:'center', padding:'30px' }}>Sin fichas de producto</p>}
          </div>
        </div>
      )}

      {sub==='nc' && (
        <div style={{ display:'grid', gridTemplateColumns:'320px 1fr', gap:'16px' }}>
          <Card>
            <h4 style={{ margin:'0 0 12px' }}>Registrar NC</h4>
            <Input label="Fecha *" value={formNC.fecha} onChange={v=>setFN('fecha',v)} type="date" />
            <Input label="Origen *" value={formNC.origen} onChange={v=>setFN('origen',v)} placeholder="Recepción / Lab / Elaboración" />
            <Select label="Gravedad" value={formNC.gravedad} onChange={v=>setFN('gravedad',v)} options={gravedades} />
            <Select label="Lote afectado" value={formNC.lote_id} onChange={v=>setFN('lote_id',v)} options={safeLotes.map(l=>({value:l.id,label:`${l.codigo} — ${l.varietal_nombre}`}))} />
            <Input label="Responsable" value={formNC.responsable} onChange={v=>setFN('responsable',v)} />
            <div style={{ marginBottom:'10px' }}>
              <label style={{ fontSize:'12px', color:'#7f8c8d', display:'block', marginBottom:'3px' }}>Descripción *</label>
              <textarea value={formNC.descripcion||''} onChange={e=>setFN('descripcion',e.target.value)} rows={2} style={{ width:'100%', padding:'7px', border:'1px solid #ddd', borderRadius:'5px', fontSize:'12px', boxSizing:'border-box' }} />
            </div>
            <div style={{ marginBottom:'10px' }}>
              <label style={{ fontSize:'12px', color:'#7f8c8d', display:'block', marginBottom:'3px' }}>Acción correctiva</label>
              <textarea value={formNC.accion_correctiva||''} onChange={e=>setFN('accion_correctiva',e.target.value)} rows={2} style={{ width:'100%', padding:'7px', border:'1px solid #ddd', borderRadius:'5px', fontSize:'12px', boxSizing:'border-box' }} />
            </div>
            <Btn onClick={guardarNC} color="#e74c3c">Registrar NC</Btn>
          </Card>

          <div>
            {/* Resumen de estados */}
            <div style={{ display:'flex', gap:'8px', marginBottom:'12px', flexWrap:'wrap' }}>
              {['AB','EN','CE'].map(e=>(
                <span key={e} style={{ background:estadoNCColor[e], color:'white', borderRadius:'6px', padding:'4px 12px', fontSize:'12px', fontWeight:'700' }}>
                  {e==='AB'?'Abiertas':e==='EN'?'En tratamiento':'Cerradas'}: {ncs.filter(n=>n.estado===e).length}
                </span>
              ))}
            </div>

            {ncs.map(nc => (
              <div key={nc.id} style={{ background:'white', border:`1px solid #ecf0f1`, borderLeft:`4px solid ${gravedadColor[nc.gravedad]||'#ddd'}`, borderRadius:'8px', padding:'12px 16px', marginBottom:'10px' }}>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
                  <div>
                    <strong>NC #{nc.id}</strong>
                    <span style={{ background:gravedadColor[nc.gravedad], color:'white', borderRadius:'4px', padding:'1px 8px', fontSize:'11px', marginLeft:'6px' }}>{nc.gravedad_display}</span>
                    <span style={{ background:estadoNCColor[nc.estado], color:'white', borderRadius:'4px', padding:'1px 8px', fontSize:'11px', marginLeft:'4px' }}>{nc.estado_display}</span>
                  </div>
                  <span style={{ color:'#7f8c8d', fontSize:'12px' }}>{nc.fecha}</span>
                </div>
                <div style={{ fontSize:'13px', margin:'4px 0 2px' }}>{nc.descripcion}</div>
                <div style={{ fontSize:'12px', color:'#7f8c8d' }}>Origen: {nc.origen}{nc.lote_codigo?` · Lote: ${nc.lote_codigo}`:''}</div>
                {nc.accion_correctiva && <div style={{ fontSize:'12px', color:'#27ae60', marginTop:'4px' }}>✅ {nc.accion_correctiva.slice(0,100)}</div>}

                {/* MEJORA: Botones de cambio de estado + panel expandible */}
                <div style={{ display:'flex', gap:'8px', marginTop:'8px', alignItems:'center' }}>
                  {nc.estado !== 'CE' && (
                    <Btn onClick={() => setNcAbierta(ncAbierta===nc.id?null:nc.id)} color="#7f8c8d" small>
                      {estadoNCLabel[nc.estado] || 'Cambiar estado'}
                    </Btn>
                  )}
                  {nc.estado === 'CE' && (
                    <Btn onClick={() => cambiarEstadoNC(nc.id, 'AB', '')} color="#e67e22" small>↩ Reabrir</Btn>
                  )}
                </div>

                {ncAbierta === nc.id && nc.estado !== 'CE' && (
                  <div style={{ background:'#f8f9fa', borderRadius:'6px', padding:'10px 12px', marginTop:'8px' }}>
                    {nc.estado === 'EN' && (
                      <>
                        <label style={{ fontSize:'12px', color:'#7f8c8d', display:'block', marginBottom:'4px' }}>Acción correctiva ejecutada</label>
                        <textarea id={`ac-${nc.id}`} defaultValue={nc.accion_correctiva||''} rows={2}
                          style={{ width:'100%', padding:'6px', border:'1px solid #ddd', borderRadius:'5px', fontSize:'12px', boxSizing:'border-box', marginBottom:'8px' }} />
                      </>
                    )}
                    <Btn onClick={() => {
                      const ac = document.getElementById(`ac-${nc.id}`)?.value
                      cambiarEstadoNC(nc.id, estadoNCNext[nc.estado], ac)
                    }} color={estadoNCColor[estadoNCNext[nc.estado]]} small>
                      Confirmar: {estadoNCLabel[nc.estado]}
                    </Btn>
                  </div>
                )}
              </div>
            ))}
            {ncs.length===0 && <p style={{ color:'#7f8c8d', textAlign:'center', padding:'30px' }}>Sin no conformidades registradas</p>}
          </div>
        </div>
      )}
    </div>
  )
}


// ─────────────────────────────────────────────────────────────────────────────
// FISCAL / INV — MEJORA: sub-tab libro de bodega
// ─────────────────────────────────────────────────────────────────────────────
function FiscalTab({ lotes = [], varietales = [] }) {
  const safeLotes = Array.isArray(lotes) ? lotes : []
  const [declaraciones, setDeclaraciones] = useState([])
  const [guias, setGuias]                 = useState([])
  const [certs, setCerts]                 = useState([])
  const [libro, setLibro]                 = useState(null)
  const [sub, setSub]     = useState('declaraciones')
  const [form, setForm]   = useState({})
  const [formG, setFormG] = useState({})
  const [filtrosLibro, setFiltrosLibro] = useState({ campaña: new Date().getFullYear() })
  const [loadingLibro, setLoadingLibro] = useState(false)
  const [msg, setMsg]     = useState('')

  useEffect(() => {
    api('declaraciones-inv/').then(r => setDeclaraciones(Array.isArray(r?.data) ? r.data : []))
    api('guias-traslado/').then(r => setGuias(Array.isArray(r?.data) ? r.data : []))
    api('certificados-analisis/').then(r => setCerts(Array.isArray(r?.data) ? r.data : []))
  }, [])

  const setF  = (k,v) => setForm(f=>({...f,[k]:v}))
  const setFG = (k,v) => setFormG(f=>({...f,[k]:v}))
  const setFL = (k,v) => setFiltrosLibro(f=>({...f,[k]:v}))

  const cargarLibro = async () => {
    setLoadingLibro(true)
    const params = new URLSearchParams(Object.fromEntries(Object.entries(filtrosLibro).filter(([,v])=>v)))
    const r = await api(`libro-bodega/?${params}`)
    if (r.ok) setLibro(r.data)
    else setMsg('❌ ' + r.msg)
    setLoadingLibro(false)
  }

  const guardarDeclaracion = async () => {
    const r = await api('declaraciones-inv/', 'POST', { ...form, auto_calcular: form.auto_calcular||false, usuario:'admin' })
    if (r.ok) { setMsg('✅ ' + r.msg); setForm({}); api('declaraciones-inv/').then(r2=>setDeclaraciones(Array.isArray(r2?.data)?r2.data:[])) }
    else setMsg('❌ ' + r.msg)
  }

  const guardarGuia = async () => {
    const r = await api('guias-traslado/', 'POST', { ...formG, usuario:'admin' })
    if (r.ok) { setMsg('✅ Guía #' + r.data?.id + ' emitida'); setFormG({}); api('guias-traslado/').then(r2=>setGuias(Array.isArray(r2?.data)?r2.data:[])) }
    else setMsg('❌ ' + r.msg)
  }

  const estadoInvColor  = { BO:'#e67e22', PR:'#3498db', AC:'#27ae60', OB:'#e74c3c' }
  const estadoGuiaColor = { EM:'#3498db', US:'#27ae60', AN:'#c0392b', VE:'#95a5a6' }
  const tiposDecl = [{value:'COS',label:'Declaración de cosecha'},{value:'PRO',label:'Declaración de producción'},
    {value:'EXI',label:'Declaración de existencias'},{value:'ELA',label:'Declaración de elaboración'}]
  const tiposGuia = [{value:'GR',label:'Granel'},{value:'PT',label:'Producto terminado'},{value:'AM',label:'Ambos'}]

  return (
    <div>
      {msg && <div style={{ background:msg.startsWith('✅')?'#EAF3DE':'#FCEBEB', color:msg.startsWith('✅')?'#27500A':'#A32D2D', padding:'8px 12px', borderRadius:'6px', marginBottom:'12px', fontSize:'13px' }}>{msg}</div>}
      <div style={{ display:'flex', gap:'8px', marginBottom:'16px' }}>
        {['declaraciones','guias','certificados','libro'].map(s=>(
          <Btn key={s} onClick={()=>setSub(s)} color={sub===s?'#2c3e50':'#7f8c8d'} small>
            {s==='declaraciones'?'📃 Declaraciones INV':s==='guias'?'🚚 Guías de traslado':s==='certificados'?'🏅 Certificados':'📖 Libro de bodega'}
          </Btn>
        ))}
      </div>

      {sub==='declaraciones' && (
        <div style={{ display:'grid', gridTemplateColumns:'300px 1fr', gap:'16px' }}>
          <Card>
            <h4 style={{ margin:'0 0 12px' }}>Nueva declaración</h4>
            <Select label="Tipo *" value={form.tipo} onChange={v=>setF('tipo',v)} options={tiposDecl} />
            <Input label="Período *" value={form.periodo} onChange={v=>setF('periodo',v)} type="date" />
            <Input label="Campaña" value={form.campaña} onChange={v=>setF('campaña',v)} type="number" placeholder={new Date().getFullYear()} />
            <div style={{ display:'flex', alignItems:'center', gap:'8px', marginBottom:'10px' }}>
              <input type="checkbox" id="autoCalc" checked={!!form.auto_calcular} onChange={e=>setF('auto_calcular',e.target.checked)} />
              <label htmlFor="autoCalc" style={{ fontSize:'13px', cursor:'pointer' }}>Auto-calcular desde el sistema</label>
            </div>
            {!form.auto_calcular && (
              <>
                <Input label="Kg uva declarados" value={form.kg_uva_declarados} onChange={v=>setF('kg_uva_declarados',v)} type="number" small />
                <Input label="Litros declarados" value={form.litros_declarados} onChange={v=>setF('litros_declarados',v)} type="number" small />
                <Input label="Litros existencias" value={form.litros_existencias} onChange={v=>setF('litros_existencias',v)} type="number" small />
              </>
            )}
            <Input label="N° Expediente INV" value={form.nro_expediente_inv} onChange={v=>setF('nro_expediente_inv',v)} placeholder="EXP-2024-..." />
            <Btn onClick={guardarDeclaracion} color="#c0392b">Generar declaración</Btn>
          </Card>
          <div>
            {declaraciones.map(d=>(
              <div key={d.id} style={{ background:'white', border:`1px solid #ecf0f1`, borderLeft:`4px solid ${estadoInvColor[d.estado]||'#ddd'}`, borderRadius:'8px', padding:'12px 16px', marginBottom:'10px' }}>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
                  <strong>{d.tipo_display}</strong>
                  <span style={{ background:estadoInvColor[d.estado], color:'white', borderRadius:'4px', padding:'1px 8px', fontSize:'11px' }}>{d.estado_display}</span>
                </div>
                <div style={{ fontSize:'12px', color:'#7f8c8d', marginTop:'4px', display:'flex', gap:'16px', flexWrap:'wrap' }}>
                  <span>Período: <strong>{d.periodo?.slice(0,7)}</strong></span>
                  {d.campaña && <span>Campaña: {d.campaña}</span>}
                  <span>Kg uva: {parseFloat(d.kg_uva_declarados||0).toLocaleString('es-AR')}</span>
                  <span>Litros: {parseFloat(d.litros_declarados||0).toLocaleString('es-AR')} L</span>
                  <span>Existencias: {parseFloat(d.litros_existencias||0).toLocaleString('es-AR')} L</span>
                  {d.nro_expediente_inv && <span style={{ color:'#3498db' }}>Exp: {d.nro_expediente_inv}</span>}
                </div>
              </div>
            ))}
            {declaraciones.length===0 && <p style={{ color:'#7f8c8d', textAlign:'center', padding:'30px' }}>Sin declaraciones generadas</p>}
          </div>
        </div>
      )}

      {sub==='guias' && (
        <div style={{ display:'grid', gridTemplateColumns:'320px 1fr', gap:'16px' }}>
          <Card>
            <h4 style={{ margin:'0 0 12px' }}>Emitir guía de traslado</h4>
            <Input label="Fecha *" value={formG.fecha} onChange={v=>setFG('fecha',v)} type="date" />
            <Select label="Tipo" value={formG.tipo} onChange={v=>setFG('tipo',v)} options={tiposGuia} />
            <Input label="Establecimiento destino *" value={formG.establecimiento_destino} onChange={v=>setFG('establecimiento_destino',v)} />
            <Input label="Domicilio destino" value={formG.domicilio_destino} onChange={v=>setFG('domicilio_destino',v)} />
            <Select label="Lote" value={formG.lote_id} onChange={v=>setFG('lote_id',v)} options={safeLotes.map(l=>({value:l.id,label:`${l.codigo} — ${l.varietal_nombre}`}))} />
            <Input label="Descripción mercadería *" value={formG.descripcion_mercaderia} onChange={v=>setFG('descripcion_mercaderia',v)} />
            <Input label="Litros / Unidades *" value={formG.litros_o_unidades} onChange={v=>setFG('litros_o_unidades',v)} type="number" />
            <Input label="Campaña" value={formG.campaña} onChange={v=>setFG('campaña',v)} type="number" />
            <Input label="Grado alcohol" value={formG.grado_alcohol} onChange={v=>setFG('grado_alcohol',v)} type="number" />
            <Input label="Transportista" value={formG.transportista} onChange={v=>setFG('transportista',v)} />
            <Input label="Patente vehículo" value={formG.patente_vehiculo} onChange={v=>setFG('patente_vehiculo',v)} />
            <Btn onClick={guardarGuia} color="#16a085">Emitir guía</Btn>
          </Card>
          <div>
            {guias.map(g=>(
              <div key={g.id} style={{ background:'white', border:`1px solid #ecf0f1`, borderLeft:`4px solid ${estadoGuiaColor[g.estado]||'#ddd'}`, borderRadius:'8px', padding:'12px 16px', marginBottom:'10px' }}>
                <div style={{ display:'flex', justifyContent:'space-between' }}>
                  <strong>Guía #{g.id} — {g.tipo_display}</strong>
                  <span style={{ background:estadoGuiaColor[g.estado], color:'white', borderRadius:'4px', padding:'1px 8px', fontSize:'11px' }}>{g.estado_display}</span>
                </div>
                <div style={{ fontSize:'13px', margin:'4px 0 2px' }}>→ <strong>{g.establecimiento_destino}</strong></div>
                <div style={{ fontSize:'12px', color:'#7f8c8d', display:'flex', gap:'14px', flexWrap:'wrap' }}>
                  <span>Fecha: {g.fecha}</span>
                  {g.lote_codigo && <span>Lote: {g.lote_codigo}</span>}
                  <span>{parseFloat(g.litros_o_unidades||0).toLocaleString('es-AR')} L/u</span>
                  {g.grado_alcohol && <span>{g.grado_alcohol}% alc.</span>}
                </div>
              </div>
            ))}
            {guias.length===0 && <p style={{ color:'#7f8c8d', textAlign:'center', padding:'30px' }}>Sin guías emitidas</p>}
          </div>
        </div>
      )}

      {sub==='certificados' && (
        <div>
          <h4 style={{ margin:'0 0 12px' }}>Certificados de análisis emitidos</h4>
          {certs.length===0 ? <p style={{ color:'#7f8c8d', fontSize:'13px' }}>Sin certificados.</p>
          : <table style={{ width:'100%', borderCollapse:'collapse', fontSize:'12px' }}>
              <thead><tr style={{ background:'#f8f9fa' }}>{['#','Lote','Fecha emisión','Vence','Lab.','°Alc','Acid.T','Acid.V','SO₂T','Apto'].map(h=><th key={h} style={{ padding:'6px 8px', textAlign:'left', color:'#7f8c8d' }}>{h}</th>)}</tr></thead>
              <tbody>{certs.map(c=><tr key={c.id} style={{ borderBottom:'1px solid #f0f0f0' }}>
                <td style={{ padding:'5px 8px', fontWeight:'700' }}>#{c.id}</td>
                <td style={{ padding:'5px 8px' }}>{c.lote_codigo}</td>
                <td style={{ padding:'5px 8px' }}>{c.fecha_emision}</td>
                <td style={{ padding:'5px 8px', color:c.fecha_vencimiento?'#e74c3c':'#7f8c8d' }}>{c.fecha_vencimiento||'—'}</td>
                <td style={{ padding:'5px 8px' }}>{c.laboratorio}</td>
                <td style={{ padding:'5px 8px' }}>{c.grado_alcohol}%</td>
                <td style={{ padding:'5px 8px' }}>{c.acidez_total}</td>
                <td style={{ padding:'5px 8px' }}>{c.acidez_volatil}</td>
                <td style={{ padding:'5px 8px' }}>{c.so2_total}</td>
                <td style={{ padding:'5px 8px' }}>{c.apto_consumo?'✅':'❌'}</td>
              </tr>)}</tbody>
            </table>}
        </div>
      )}

      {/* MEJORA — Libro de bodega INV */}
      {sub==='libro' && (
        <div>
          <Card>
            <h4 style={{ margin:'0 0 12px' }}>Libro de bodega — INV</h4>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(180px,1fr))', gap:'0 16px' }}>
              <Input label="Campaña" value={filtrosLibro.campaña} onChange={v=>setFL('campaña',v)} type="number" />
              <Select label="Varietal (opcional)" value={filtrosLibro.varietal} onChange={v=>setFL('varietal',v)} options={varietales.map(v=>({value:v.codigo,label:v.nombre}))} />
              <Input label="Fecha desde" value={filtrosLibro.fecha_desde} onChange={v=>setFL('fecha_desde',v)} type="date" />
              <Input label="Fecha hasta" value={filtrosLibro.fecha_hasta} onChange={v=>setFL('fecha_hasta',v)} type="date" />
            </div>
            <Btn onClick={cargarLibro} color="#2c3e50" disabled={loadingLibro}>{loadingLibro?'Consultando…':'🔍 Generar libro'}</Btn>
          </Card>

          {libro && (
            <>
              {/* Existencias actuales */}
              <Card>
                <h4 style={{ margin:'0 0 12px', color:'#2c3e50' }}>Existencias actuales por varietal</h4>
                <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(180px,1fr))', gap:'10px' }}>
                  {Object.entries(libro.existencias_actuales).map(([cod,e]) => (
                    <div key={cod} style={{ background:'#eaf4fb', borderRadius:'6px', padding:'10px 14px' }}>
                      <div style={{ fontSize:'12px', color:'#7f8c8d' }}>{e.varietal_nombre}</div>
                      <div style={{ fontSize:'20px', fontWeight:'700', color:'#2980b9' }}>{Math.round(e.litros).toLocaleString('es-AR')} L</div>
                    </div>
                  ))}
                  {Object.keys(libro.existencias_actuales).length===0 && <p style={{ color:'#7f8c8d', fontSize:'13px' }}>Sin existencias activas</p>}
                </div>
              </Card>

              {/* Movimientos por varietal */}
              {Object.entries(libro.movimientos_por_varietal).map(([cod, data]) => (
                <Card key={cod}>
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'12px' }}>
                    <h4 style={{ margin:0, color:'#8e44ad' }}>{data.varietal_nombre}</h4>
                    <div style={{ display:'flex', gap:'16px', fontSize:'13px' }}>
                      <span style={{ color:'#27ae60' }}>↑ Ingresos: <strong>{Math.round(data.total_ingresos).toLocaleString('es-AR')} L</strong></span>
                      <span style={{ color:'#c0392b' }}>↓ Egresos: <strong>{Math.round(data.total_egresos).toLocaleString('es-AR')} L</strong></span>
                      <span style={{ color:'#2980b9' }}>Saldo: <strong>{Math.round(data.saldo_movimientos).toLocaleString('es-AR')} L</strong></span>
                    </div>
                  </div>
                  <div style={{ overflowX:'auto' }}>
                    <table style={{ width:'100%', borderCollapse:'collapse', fontSize:'12px' }}>
                      <thead><tr style={{ background:'#f8f9fa' }}>{['Fecha','Tipo','Lote','Campaña','Litros','R. Origen','R. Destino','Descripción','Usuario'].map(h=><th key={h} style={{ padding:'5px 8px', textAlign:'left', color:'#7f8c8d' }}>{h}</th>)}</tr></thead>
                      <tbody>
                        {data.detalle.map((m,i) => (
                          <tr key={i} style={{ borderBottom:'1px solid #f0f0f0', background: m.es_egreso ? '#fff5f5' : 'white' }}>
                            <td style={{ padding:'4px 8px' }}>{m.fecha?.slice(0,16).replace('T',' ')}</td>
                            <td style={{ padding:'4px 8px' }}><span style={{ background:movTipoColor[m.tipo]||'#7f8c8d', color:'white', borderRadius:'3px', padding:'1px 6px', fontSize:'10px' }}>{m.tipo_display}</span></td>
                            <td style={{ padding:'4px 8px', fontWeight:'600' }}>{m.lote}</td>
                            <td style={{ padding:'4px 8px' }}>{m.campaña}</td>
                            <td style={{ padding:'4px 8px', fontWeight:'700', color: m.es_egreso?'#c0392b':'#27ae60' }}>{m.es_egreso?'-':''}{parseFloat(m.litros).toLocaleString('es-AR')} L</td>
                            <td style={{ padding:'4px 8px', color:'#7f8c8d' }}>{m.recipiente_origen||'—'}</td>
                            <td style={{ padding:'4px 8px', color:'#7f8c8d' }}>{m.recipiente_destino||'—'}</td>
                            <td style={{ padding:'4px 8px', color:'#7f8c8d', fontStyle:'italic' }}>{m.descripcion||'—'}</td>
                            <td style={{ padding:'4px 8px', color:'#95a5a6' }}>{m.usuario||'—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              ))}
              {Object.keys(libro.movimientos_por_varietal).length===0 && <p style={{ color:'#7f8c8d', textAlign:'center', padding:'30px' }}>Sin movimientos para los filtros seleccionados</p>}
            </>
          )}
        </div>
      )}
    </div>
  )
}


// ─────────────────────────────────────────────────────────────────────────────
// DEPÓSITOS, BARRICAS, ELABORACIÓN, EMBOTELLADO, COSTOS, TRAZABILIDAD
// (sin cambios respecto a la versión original — se incluyen completos)
// ─────────────────────────────────────────────────────────────────────────────
function DepositosTab() {
  const [recipientes, setRecipientes] = useState([])
  const [form, setForm]   = useState({})
  const [msg, setMsg]     = useState('')
  const [showForm, setShowForm] = useState(false)
  useEffect(() => { api('recipientes/').then(r => setRecipientes(Array.isArray(r?.data) ? r.data : [])) }, [])
  const setF = (k,v) => setForm(f=>({...f,[k]:v}))
  const guardar = async () => {
    const r = await api('recipientes/', 'POST', form)
    if (r.ok) { setMsg('✅ Guardado'); setForm({}); setShowForm(false); api('recipientes/').then(r2=>setRecipientes(Array.isArray(r2?.data)?r2.data:[])) } else setMsg('❌ '+r.msg)
  }
  const tipos = [{value:'TA',label:'Tanque acero'},{value:'PC',label:'Pileta cemento'},{value:'TR',label:'Tanque roble'},{value:'BA',label:'Barrica'},{value:'TI',label:'Tinaja'},{value:'OT',label:'Otro'}]
  const sectores = [...new Set(recipientes.map(r=>r.sector).filter(Boolean))]
  return (
    <div>
      {msg && <div style={{ background:'#ecf0f1', padding:'8px 12px', borderRadius:'6px', marginBottom:'12px', fontSize:'13px' }}>{msg}</div>}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'16px' }}>
        <p style={{ margin:0, color:'#7f8c8d', fontSize:'13px' }}>
          {recipientes.length} recipientes · <span style={{ color:'#27ae60' }}>{recipientes.filter(r=>r.estado==='LI').length} libres</span> · <span style={{ color:'#e67e22' }}>{recipientes.filter(r=>r.estado==='OC').length} ocupados</span>
        </p>
        <Btn onClick={()=>setShowForm(!showForm)} color="#2980b9">+ Nuevo recipiente</Btn>
      </div>
      {showForm && (
        <Card>
          <h4 style={{ margin:'0 0 14px' }}>Nuevo recipiente</h4>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0 16px' }}>
            <Input label="Código *" value={form.codigo} onChange={v=>setF('codigo',v)} placeholder="T-001" />
            <Input label="Nombre *" value={form.nombre} onChange={v=>setF('nombre',v)} placeholder="Tanque 1 Malbec" />
            <Select label="Tipo" value={form.tipo} onChange={v=>setF('tipo',v)} options={tipos} />
            <Input label="Capacidad (L) *" value={form.capacidad_litros} onChange={v=>setF('capacidad_litros',v)} type="number" />
            <Input label="Sector" value={form.sector} onChange={v=>setF('sector',v)} placeholder="Nave A" />
            <Input label="Fila" value={form.fila} onChange={v=>setF('fila',v)} type="number" />
          </div>
          <div style={{ display:'flex', gap:'8px' }}>
            <Btn onClick={guardar} color="#27ae60">Guardar</Btn>
            <Btn onClick={()=>setShowForm(false)} color="#7f8c8d">Cancelar</Btn>
          </div>
        </Card>
      )}
      {(sectores.length>0?sectores:['']).map(sector=>(
        <div key={sector||'sin-sector'} style={{ marginBottom:'20px' }}>
          <h4 style={{ color:'#2c3e50', borderBottom:'2px solid #ecf0f1', paddingBottom:'6px', margin:'0 0 12px' }}>{sector||'Sin sector asignado'}</h4>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(160px, 1fr))', gap:'10px' }}>
            {recipientes.filter(r=>r.sector===sector||(!r.sector&&!sector)).map(r=>(
              <div key={r.id} style={{ background:estadoRecColor[r.estado]||'#7f8c8d', borderRadius:'8px', padding:'12px', color:'white', cursor:'pointer' }} onClick={()=>setForm(r)}>
                <div style={{ fontWeight:'700', fontSize:'14px' }}>{r.codigo}</div>
                <div style={{ fontSize:'11px', opacity:.85 }}>{r.nombre}</div>
                <div style={{ fontSize:'13px', fontWeight:'600', marginTop:'4px' }}>{r.capacidad_litros.toLocaleString('es-AR')} L</div>
                <div style={{ fontSize:'11px', marginTop:'2px', opacity:.9 }}>{r.estado_display}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

function BarricasTab({ lotes=[] }) {
  const [barricas,setBarricas]=useState([]);const [form,setForm]=useState({});const [msg,setMsg]=useState('');const [showForm,setShowForm]=useState(false);const [filEst,setFilEst]=useState('')
  useEffect(()=>{api('barricas/').then(r=>setBarricas(Array.isArray(r?.data)?r.data:[]))},[])
  const setF=(k,v)=>setForm(f=>({...f,[k]:v}))
  const guardar=async()=>{const r=await api('barricas/','POST',form);if(r.ok){setMsg('✅ Guardada');setForm({});setShowForm(false);api('barricas/').then(r2=>setBarricas(Array.isArray(r2?.data)?r2.data:[]))}else setMsg('❌ '+r.msg)}
  const maderas=[{value:'FRA',label:'Francés'},{value:'AME',label:'Americano'},{value:'HUN',label:'Húngaro'}]
  const tostados=[{value:'L',label:'Ligero'},{value:'M',label:'Medio'},{value:'MO',label:'Medio+'},{value:'F',label:'Fuerte'}]
  const barricasFiltradas=filEst?barricas.filter(b=>b.estado===filEst):barricas
  const pct=b=>b.vida_util_usos?Math.round((b.cantidad_usos/b.vida_util_usos)*100):0
  return (
    <div>
      {msg&&<div style={{background:'#ecf0f1',padding:'8px 12px',borderRadius:'6px',marginBottom:'12px',fontSize:'13px'}}>{msg}</div>}
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'16px'}}>
        <div style={{display:'flex',gap:'8px'}}>
          {[{v:'',l:`Todas (${barricas.length})`},{v:'LI',l:'🟢 Libres'},{v:'OC',l:'🟡 Ocupadas'}].map(f=><Btn key={f.v} onClick={()=>setFilEst(f.v)} color={filEst===f.v?'#2c3e50':'#7f8c8d'} small>{f.l}</Btn>)}
        </div>
        <Btn onClick={()=>setShowForm(!showForm)} color="#8e44ad">+ Nueva barrica</Btn>
      </div>
      {showForm&&<Card><h4 style={{margin:'0 0 14px'}}>Alta de barrica</h4><div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'0 16px'}}><Input label="Número *" value={form.numero} onChange={v=>setF('numero',v)} placeholder="B-001"/><Input label="Capacidad (L)" value={form.capacidad_litros} onChange={v=>setF('capacidad_litros',v)} type="number" placeholder="225"/><Select label="Madera" value={form.madera} onChange={v=>setF('madera',v)} options={maderas}/><Select label="Tostado" value={form.tostado} onChange={v=>setF('tostado',v)} options={tostados}/><Input label="Tonelero" value={form.tonelero} onChange={v=>setF('tonelero',v)}/><Input label="Año de compra" value={form.anio_compra} onChange={v=>setF('anio_compra',v)} type="number"/><Input label="Vida útil (usos)" value={form.vida_util_usos} onChange={v=>setF('vida_util_usos',v)} type="number" placeholder="4"/><Input label="Costo de compra $" value={form.costo_compra} onChange={v=>setF('costo_compra',v)} type="number"/><Input label="Sector / Nave" value={form.sector} onChange={v=>setF('sector',v)}/><Input label="Fila" value={form.fila} onChange={v=>setF('fila',v)} type="number"/></div><div style={{display:'flex',gap:'8px'}}><Btn onClick={guardar} color="#27ae60">Guardar</Btn><Btn onClick={()=>setShowForm(false)} color="#7f8c8d">Cancelar</Btn></div></Card>}
      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill, minmax(200px, 1fr))',gap:'10px'}}>
        {barricasFiltradas.map(b=>{const v=pct(b);const vc=v<50?'#27ae60':v<80?'#e67e22':'#c0392b';return(
          <div key={b.id} style={{background:'white',border:`2px solid ${estadoRecColor[b.estado]||'#ddd'}`,borderRadius:'8px',padding:'12px'}}>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start'}}><strong style={{fontSize:'14px'}}>{b.numero}</strong><span style={{background:estadoRecColor[b.estado],color:'white',borderRadius:'4px',padding:'1px 7px',fontSize:'11px'}}>{b.estado_display}</span></div>
            <div style={{fontSize:'12px',color:'#7f8c8d',margin:'4px 0'}}>{b.madera_display} · {b.tostado_display} · {b.capacidad_litros} L</div>
            <div style={{fontSize:'12px',color:'#7f8c8d'}}>Usos: {b.cantidad_usos}/{b.vida_util_usos}</div>
            <div style={{background:'#ecf0f1',borderRadius:'4px',height:'6px',marginTop:'6px',overflow:'hidden'}}><div style={{width:`${Math.min(100,v)}%`,height:'100%',background:vc}}/></div>
            <div style={{fontSize:'11px',color:vc,marginTop:'2px'}}>{v}% vida útil consumida</div>
          </div>
        )})}
        {barricasFiltradas.length===0&&<p style={{gridColumn:'1/-1',color:'#7f8c8d',textAlign:'center',padding:'20px'}}>Sin barricas</p>}
      </div>
    </div>
  )
}

function ElaboracionTab({ lotes=[] }) {
  const safeLotes=Array.isArray(lotes)?lotes:[]
  const [ordenes,setOrdenes]=useState([]);const [balance,setBalance]=useState(null);const [loteId,setLoteId]=useState('');const [form,setForm]=useState({});const [formBal,setFormBal]=useState({});const [sub,setSub]=useState('ordenes');const [msg,setMsg]=useState('')
  useEffect(()=>{api('ordenes-elaboracion/').then(r=>setOrdenes(Array.isArray(r?.data)?r.data:[]))},[])
  const setF=(k,v)=>setForm(f=>({...f,[k]:v}));const setFB=(k,v)=>setFormBal(f=>({...f,[k]:v}))
  const cargarBalance=lid=>{setLoteId(lid);if(lid)api(`balance-masa/?lote_id=${lid}`).then(r=>setBalance(r?.data||null))}
  const guardarOrden=async()=>{const r=await api('ordenes-elaboracion/','POST',{...form,usuario:'admin'});if(r.ok){setMsg('✅ Orden guardada');setForm({});api('ordenes-elaboracion/').then(r2=>setOrdenes(Array.isArray(r2?.data)?r2.data:[]))}else setMsg('❌ '+r.msg)}
  const guardarBalance=async()=>{const r=await api('balance-masa/','POST',{...formBal,lote_id:loteId,usuario:'admin'});if(r.ok){setMsg(`✅ ${r.msg}`);cargarBalance(loteId)}else setMsg('❌ '+r.msg)}
  const estadoColor={PE:'#e67e22',EN:'#3498db',CO:'#27ae60',AN:'#c0392b'}
  return (
    <div>
      {msg&&<div style={{background:'#ecf0f1',padding:'8px 12px',borderRadius:'6px',marginBottom:'12px',fontSize:'13px'}}>{msg}</div>}
      <div style={{display:'flex',gap:'8px',marginBottom:'16px'}}>
        {['ordenes','balance'].map(s=><Btn key={s} onClick={()=>setSub(s)} color={sub===s?'#2c3e50':'#7f8c8d'} small>{s==='ordenes'?'📋 Órdenes de elaboración':'⚖️ Balance de masa'}</Btn>)}
      </div>
      {sub==='ordenes'&&<div style={{display:'grid',gridTemplateColumns:'320px 1fr',gap:'16px'}}>
        <Card>
          <h4 style={{margin:'0 0 12px'}}>Nueva orden</h4>
          <Select label="Lote *" value={form.lote_id} onChange={v=>setF('lote_id',v)} options={safeLotes.filter(l=>['EB','CR'].includes(l.estado)).map(l=>({value:l.id,label:`${l.codigo} — ${l.varietal_nombre}`}))}/>
          <Input label="Proceso *" value={form.proceso} onChange={v=>setF('proceso',v)} placeholder="Ej: 2° trasiego post-FML"/>
          <Input label="Fecha emisión *" value={form.fecha_emision} onChange={v=>setF('fecha_emision',v)} type="date"/>
          <Input label="Fecha ejecución" value={form.fecha_ejecucion} onChange={v=>setF('fecha_ejecucion',v)} type="date"/>
          <Input label="Responsable" value={form.responsable} onChange={v=>setF('responsable',v)}/>
          <div style={{marginBottom:'10px'}}><label style={{fontSize:'12px',color:'#7f8c8d',display:'block',marginBottom:'3px'}}>Instrucciones</label><textarea value={form.instrucciones||''} onChange={e=>setF('instrucciones',e.target.value)} rows={3} style={{width:'100%',padding:'7px 10px',border:'1px solid #ddd',borderRadius:'5px',fontSize:'13px',boxSizing:'border-box',resize:'vertical'}}/></div>
          <Btn onClick={guardarOrden} color="#e67e22">Crear orden</Btn>
        </Card>
        <div>
          {ordenes.map(o=><div key={o.id} style={{background:'white',border:`1px solid #ecf0f1`,borderLeft:`4px solid ${estadoColor[o.estado]||'#ddd'}`,borderRadius:'8px',padding:'12px 16px',marginBottom:'10px'}}>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start'}}><div><strong>OE #{o.id}</strong><span style={{background:estadoColor[o.estado],color:'white',borderRadius:'4px',padding:'1px 8px',fontSize:'11px',marginLeft:'8px'}}>{o.estado_display}</span></div><span style={{color:'#7f8c8d',fontSize:'12px'}}>{o.fecha_emision}</span></div>
            <div style={{fontWeight:'600',fontSize:'13px',margin:'4px 0 2px'}}>{o.proceso}</div>
            <div style={{fontSize:'12px',color:'#7f8c8d'}}>Lote: <strong>{o.lote_codigo}</strong>{o.responsable&&` · ${o.responsable}`}</div>
          </div>)}
          {ordenes.length===0&&<p style={{color:'#7f8c8d',textAlign:'center',padding:'30px'}}>Sin órdenes</p>}
        </div>
      </div>}
      {sub==='balance'&&<div style={{display:'grid',gridTemplateColumns:'340px 1fr',gap:'16px'}}>
        <Card>
          <h4 style={{margin:'0 0 12px'}}>Balance de masa</h4>
          <Select label="Lote *" value={loteId} onChange={v=>{setFB('lote_id',v);cargarBalance(v)}} options={safeLotes.map(l=>({value:l.id,label:`${l.codigo} — ${l.varietal_nombre}`}))}/>
          <Input label="Campaña *" value={formBal.campaña} onChange={v=>setFB('campaña',v)} type="number"/>
          <div style={{background:'#f8f9fa',borderRadius:'6px',padding:'10px 12px',marginBottom:'10px'}}>
            <p style={{fontSize:'11px',color:'#7f8c8d',margin:'0 0 8px',fontWeight:'700',textTransform:'uppercase'}}>Entradas</p>
            <Input label="Kg uva total *" value={formBal.kg_uva_total} onChange={v=>setFB('kg_uva_total',v)} type="number" small/>
            <Input label="Kg uva propia" value={formBal.kg_uva_propia} onChange={v=>setFB('kg_uva_propia',v)} type="number" small/>
            <Input label="Kg uva comprada" value={formBal.kg_uva_comprada} onChange={v=>setFB('kg_uva_comprada',v)} type="number" small/>
          </div>
          <div style={{background:'#f8f9fa',borderRadius:'6px',padding:'10px 12px',marginBottom:'10px'}}>
            <p style={{fontSize:'11px',color:'#7f8c8d',margin:'0 0 8px',fontWeight:'700',textTransform:'uppercase'}}>Masa sólida</p>
            <Input label="Kg escobajo" value={formBal.kg_escobajo} onChange={v=>setFB('kg_escobajo',v)} type="number" small/>
            <Input label="Kg orujo" value={formBal.kg_orujo} onChange={v=>setFB('kg_orujo',v)} type="number" small/>
            <Input label="Kg borras" value={formBal.kg_borras} onChange={v=>setFB('kg_borras',v)} type="number" small/>
          </div>
          <Input label="Litros totales *" value={formBal.litros_totales} onChange={v=>setFB('litros_totales',v)} type="number"/>
          <Input label="Litros mosto flor" value={formBal.litros_mosto_flor} onChange={v=>setFB('litros_mosto_flor',v)} type="number"/>
          <Input label="Litros prensa" value={formBal.litros_prensa} onChange={v=>setFB('litros_prensa',v)} type="number"/>
          <Input label="Fecha cierre *" value={formBal.fecha_cierre} onChange={v=>setFB('fecha_cierre',v)} type="date"/>
          {formBal.kg_uva_total&&formBal.litros_totales&&<div style={{background:'#eaf4fb',padding:'8px 12px',borderRadius:'6px',fontSize:'13px',marginBottom:'10px'}}>Rendimiento estimado: <strong>{(parseFloat(formBal.litros_totales)/parseFloat(formBal.kg_uva_total)).toFixed(3)} L/kg</strong></div>}
          <Btn onClick={guardarBalance} color="#2980b9">Guardar balance</Btn>
        </Card>
        {balance?<Card>
          <h4 style={{margin:'0 0 14px',color:'#2c3e50'}}>Resultado del balance</h4>
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'10px'}}>
            {[{label:'Rendimiento',value:`${balance.rendimiento_lkg} L/kg`,color:'#2980b9'},{label:'Extracción',value:`${balance.porcentaje_extraccion}%`,color:'#27ae60'},{label:'Kg uva total',value:`${parseFloat(balance.kg_uva_total||0).toLocaleString('es-AR')} kg`,color:'#e67e22'},{label:'Litros totales',value:`${parseFloat(balance.litros_totales||0).toLocaleString('es-AR')} L`,color:'#8e44ad'}].map(k=>(
              <div key={k.label} style={{background:'#f8f9fa',borderRadius:'6px',padding:'10px 14px'}}><div style={{fontSize:'11px',color:'#7f8c8d'}}>{k.label}</div><div style={{fontSize:'20px',fontWeight:'800',color:k.color}}>{k.value}</div></div>
            ))}
          </div>
        </Card>:<div style={{display:'flex',alignItems:'center',justifyContent:'center',height:'200px',color:'#bdc3c7'}}>← Seleccioná un lote</div>}
      </div>}
    </div>
  )
}

function EmbotelladoTab({ lotes=[] }) {
  const safeLotes=Array.isArray(lotes)?lotes:[]
  const [ordenes,setOrdenes]=useState([]);const [form,setForm]=useState({});const [confirm,setConfirm]=useState(null);const [msg,setMsg]=useState('')
  useEffect(()=>{api('embotellado/').then(r=>setOrdenes(Array.isArray(r?.data)?r.data:[]))},[])
  const setF=(k,v)=>setForm(f=>({...f,[k]:v}))
  const guardar=async()=>{const r=await api('embotellado/','POST',form);if(r.ok){setMsg('✅ '+r.msg);setForm({});api('embotellado/').then(r2=>setOrdenes(Array.isArray(r2?.data)?r2.data:[]))}else setMsg('❌ '+r.msg)}
  const confirmarEmbotellado=async()=>{const r=await api('embotellado/confirmar/','POST',{orden_id:confirm.id,botellas_real:confirm.botellas_real,botellas_merma:confirm.botellas_merma||0,fecha_real:confirm.fecha_real||new Date().toISOString().slice(0,10)});if(r.ok){setMsg('✅ '+r.msg);setConfirm(null);api('embotellado/').then(r2=>setOrdenes(Array.isArray(r2?.data)?r2.data:[]))}else setMsg('❌ '+r.msg)}
  const estadoColor={PL:'#e67e22',EN:'#3498db',CO:'#27ae60',AN:'#c0392b'}
  const formatos=['375','750','1500','3000','BIB','OTR'].map(f=>({value:f,label:f+(f==='750'?' ml (std)':f==='375'?' ml':f==='1500'?' L':'')}))
  return (
    <div>
      {msg&&<div style={{background:'#ecf0f1',padding:'8px 12px',borderRadius:'6px',marginBottom:'12px',fontSize:'13px'}}>{msg}</div>}
      {confirm&&<div style={{position:'fixed',inset:0,background:'rgba(0,0,0,.5)',zIndex:900,display:'flex',alignItems:'center',justifyContent:'center'}}>
        <div style={{background:'white',borderRadius:'10px',padding:'24px',width:'380px'}}>
          <h3 style={{margin:'0 0 16px',color:'#2c3e50'}}>Confirmar embotellado</h3>
          <p style={{fontSize:'13px',color:'#7f8c8d',margin:'0 0 14px'}}>Orden #{confirm.id} — {confirm.lote_codigo} — {confirm.formato} ml</p>
          <Input label="Botellas reales" value={confirm.botellas_real} type="number" onChange={v=>setConfirm(c=>({...c,botellas_real:v}))}/>
          <Input label="Botellas merma/rotas" value={confirm.botellas_merma} type="number" onChange={v=>setConfirm(c=>({...c,botellas_merma:v}))}/>
          <Input label="Fecha real" value={confirm.fecha_real} type="date" onChange={v=>setConfirm(c=>({...c,fecha_real:v}))}/>
          <div style={{display:'flex',gap:'8px',marginTop:'12px'}}>
            <Btn onClick={confirmarEmbotellado} color="#27ae60">Confirmar</Btn>
            <Btn onClick={()=>setConfirm(null)} color="#7f8c8d">Cancelar</Btn>
          </div>
        </div>
      </div>}
      <div style={{display:'grid',gridTemplateColumns:'320px 1fr',gap:'16px'}}>
        <Card>
          <h4 style={{margin:'0 0 14px'}}>Nueva orden de embotellado</h4>
          <Select label="Lote *" value={form.lote_id} onChange={v=>setF('lote_id',v)} options={safeLotes.filter(l=>['LI','EP','EB'].includes(l.estado)).map(l=>({value:l.id,label:`${l.codigo} (${Math.round(l.litros_actuales)} L)`}))}/>
          <Select label="Formato" value={form.formato} onChange={v=>setF('formato',v)} options={formatos}/>
          <Input label="Botellas planificadas *" value={form.botellas_plan} onChange={v=>setF('botellas_plan',v)} type="number"/>
          <Input label="Fecha planificada" value={form.fecha_plan} onChange={v=>setF('fecha_plan',v)} type="date"/>
          <Input label="Cód. artículo PT (ERP)" value={form.cod_art_pt} onChange={v=>setF('cod_art_pt',v)} placeholder="VIN-MAL-750-24"/>
          <Input label="N° RNOE" value={form.nro_rnoe} onChange={v=>setF('nro_rnoe',v)}/>
          <Btn onClick={guardar} color="#e74c3c">Crear orden</Btn>
        </Card>
        <div>
          {ordenes.map(o=><div key={o.id} style={{background:'white',border:'1px solid #ecf0f1',borderRadius:'8px',padding:'12px 16px',marginBottom:'10px',borderLeft:`4px solid ${estadoColor[o.estado]||'#ddd'}`}}>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start'}}>
              <div><strong>OE #{o.id} — {o.lote_codigo}</strong><span style={{background:estadoColor[o.estado],color:'white',borderRadius:'4px',padding:'1px 8px',fontSize:'11px',marginLeft:'8px'}}>{o.estado_display}</span></div>
              {o.estado==='PL'&&<Btn onClick={()=>setConfirm({...o,botellas_real:o.botellas_plan})} color="#27ae60" small>✔ Confirmar</Btn>}
            </div>
            <div style={{fontSize:'12px',color:'#7f8c8d',marginTop:'4px',display:'flex',gap:'16px',flexWrap:'wrap'}}>
              <span>Formato: <strong>{o.formato} ml</strong></span>
              <span>Plan: <strong>{o.botellas_plan?.toLocaleString('es-AR')} bot.</strong></span>
              {o.botellas_real&&<span>Real: <strong>{o.botellas_real?.toLocaleString('es-AR')} bot.</strong></span>}
              <span>~{o.litros_planificados?.toLocaleString('es-AR')} L</span>
            </div>
          </div>)}
          {ordenes.length===0&&<p style={{color:'#7f8c8d',textAlign:'center',padding:'30px'}}>Sin órdenes de embotellado</p>}
        </div>
      </div>
    </div>
  )
}

function CostosTab({ lotes=[] }) {
  const safeLotes=Array.isArray(lotes)?lotes:[]
  const [resumen,setResumen]=useState([]);const [detalle,setDetalle]=useState(null);const [loteId,setLoteId]=useState('');const [form,setForm]=useState({});const [msg,setMsg]=useState('')
  useEffect(()=>{api('costos/').then(r=>setResumen(Array.isArray(r?.data)?r.data:[]))},[])
  const setF=(k,v)=>setForm(f=>({...f,[k]:v}))
  const cargarDetalle=async lid=>{setLoteId(lid);const r=await api(`costos/?lote_id=${lid}`);if(r.ok)setDetalle(r.data)}
  const actualizarCostos=async()=>{const r=await api('costos/','POST',{...form,lote_id:loteId,accion:'actualizar_cabecera',usuario:'admin'});if(r.ok){setMsg(`✅ Recalculado`);cargarDetalle(loteId);api('costos/').then(r2=>setResumen(Array.isArray(r2?.data)?r2.data:[]))}else setMsg('❌ '+r.msg)}
  const costoFields=[{key:'costo_uva_propia',label:'Uva propia $'},{key:'costo_uva_comprada',label:'Uva comprada $'},{key:'costo_insumos_enologicos',label:'Insumos enológicos $'},{key:'costo_mano_obra_bodega',label:'M.O. bodega $'},{key:'costo_energia',label:'Energía $'},{key:'costo_crianza_barricas',label:'Crianza barricas $'},{key:'costo_amortizacion_barrica',label:'Amort. barricas $'},{key:'costo_gastos_indirectos',label:'Gastos indirectos $'},{key:'costo_materiales_emb',label:'Materiales emb. $'},{key:'costo_mano_obra_emb',label:'M.O. embotellado $'}]
  return (
    <div>
      {msg&&<div style={{background:'#ecf0f1',padding:'8px 12px',borderRadius:'6px',marginBottom:'12px',fontSize:'13px'}}>{msg}</div>}
      <div style={{display:'grid',gridTemplateColumns:'340px 1fr',gap:'16px'}}>
        <Card>
          <h4 style={{margin:'0 0 12px'}}>Cargar costos por lote</h4>
          <Select label="Lote" value={loteId} onChange={v=>cargarDetalle(v)} options={safeLotes.map(l=>({value:l.id,label:`${l.codigo} — ${l.varietal_nombre}`}))}/>
          {loteId&&costoFields.map(f=><Input key={f.key} label={f.label} value={form[f.key]??(detalle?.costo_lote?.[f.key]||'')} onChange={v=>setF(f.key,v)} type="number" small/>)}
          {loteId&&<Btn onClick={actualizarCostos} color="#16a085">Recalcular costos</Btn>}
        </Card>
        <div>
          {detalle?.costo_lote&&<Card>
            <h4 style={{margin:'0 0 14px'}}>Resumen — {detalle.costo_lote.lote_codigo}</h4>
            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill, minmax(160px, 1fr))',gap:'10px',marginBottom:'16px'}}>
              {[{label:'Costo granel',value:detalle.costo_lote.costo_total_granel,color:'#2980b9'},{label:'Costo PT total',value:detalle.costo_lote.costo_total_pt,color:'#8e44ad'},{label:'Costo/botella',value:detalle.costo_lote.costo_por_botella,color:'#27ae60'}].map(k=><div key={k.label} style={{background:k.color,color:'white',borderRadius:'8px',padding:'12px'}}><div style={{fontSize:'11px',opacity:.85}}>{k.label}</div><div style={{fontSize:'20px',fontWeight:'800'}}>${parseFloat(k.value||0).toLocaleString('es-AR')}</div></div>)}
            </div>
          </Card>}
          <Card>
            <h4 style={{margin:'0 0 12px'}}>Comparativa de costos por lote</h4>
            {resumen.map(c=><div key={c.lote_id} style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'8px 0',borderBottom:'1px solid #f0f0f0',cursor:'pointer'}} onClick={()=>cargarDetalle(c.lote_id)}>
              <span style={{fontSize:'13px',fontWeight:'600'}}>{c.lote_codigo}</span>
              <div style={{display:'flex',gap:'16px',fontSize:'12px'}}>
                <span style={{color:'#2980b9'}}>${parseFloat(c.costo_por_litro||0).toFixed(2)}/L</span>
                <span style={{color:'#27ae60'}}>${parseFloat(c.costo_por_botella||0).toFixed(2)}/bot</span>
                <span style={{color:'#8e44ad',fontWeight:'700'}}>${parseFloat(c.costo_total_pt||0).toLocaleString('es-AR')}</span>
              </div>
            </div>)}
            {resumen.length===0&&<p style={{color:'#7f8c8d',fontSize:'13px'}}>Sin costos cargados aún</p>}
          </Card>
        </div>
      </div>
    </div>
  )
}

function TrazabilidadTab({ lotes=[] }) {
  const safeLotes=Array.isArray(lotes)?lotes:[]
  const [loteId,setLoteId]=useState('');const [direccion,setDireccion]=useState('atras');const [resultado,setResultado]=useState(null);const [loading,setLoading]=useState(false)
  const buscar=async()=>{if(!loteId)return;setLoading(true);const r=await api(`trazabilidad/?lote_id=${loteId}&direccion=${direccion}`);setResultado(r.ok?r.data:null);setLoading(false)}
  return (
    <div>
      <Card>
        <h4 style={{margin:'0 0 14px'}}>Consulta de trazabilidad</h4>
        <div style={{display:'flex',gap:'12px',alignItems:'flex-end',flexWrap:'wrap'}}>
          <div style={{flex:1,minWidth:'200px'}}><Select label="Lote a consultar" value={loteId} onChange={setLoteId} options={safeLotes.map(l=>({value:l.id,label:`${l.codigo} — ${l.varietal_nombre} ${l.campaña}`}))}/></div>
          <div style={{display:'flex',gap:'6px',marginBottom:'10px'}}>
            {['atras','adelante'].map(d=><Btn key={d} onClick={()=>setDireccion(d)} color={direccion===d?'#8e44ad':'#7f8c8d'} small>{d==='atras'?'⬅️ Origen':'➡️ Destino'}</Btn>)}
          </div>
          <div style={{marginBottom:'10px'}}><Btn onClick={buscar} color="#2c3e50" disabled={!loteId||loading}>{loading?'Consultando…':'🔍 Consultar'}</Btn></div>
        </div>
      </Card>
      {resultado&&<div>
        <Card>
          <h4 style={{margin:'0 0 10px',color:'#8e44ad'}}>Lote: {resultado.lote?.codigo} — {resultado.lote?.varietal_nombre} {resultado.lote?.campaña}</h4>
          <div style={{display:'flex',gap:'10px',flexWrap:'wrap'}}>
            <div style={{background:'#f8f9fa',borderRadius:'6px',padding:'8px 14px'}}><div style={{fontSize:'11px',color:'#7f8c8d'}}>Litros actuales</div><div style={{fontSize:'15px',fontWeight:'700'}}>{Math.round(resultado.lote?.litros_actuales||0).toLocaleString('es-AR')} L</div></div>
            <div style={{background:'#f8f9fa',borderRadius:'6px',padding:'8px 14px'}}><div style={{fontSize:'11px',color:'#7f8c8d'}}>Estado</div><div style={{fontSize:'15px',fontWeight:'700'}}>{resultado.lote?.estado_display}</div></div>
          </div>
        </Card>
        {direccion==='atras'&&<>
          {resultado.tickets_uva?.length>0&&<Card><h4 style={{margin:'0 0 10px',color:'#e67e22'}}>🚛 Tickets de uva ({resultado.tickets_uva.length})</h4>
            {resultado.tickets_uva.map(t=><div key={t.ticket_id} style={{display:'flex',gap:'14px',fontSize:'13px',padding:'5px 0',borderBottom:'1px solid #f0f0f0',flexWrap:'wrap'}}><strong>#{t.ticket_id}</strong><span>{t.fecha?.slice(0,10)}</span><span>{t.varietal}</span><span><strong>{parseFloat(t.kg_neto||0).toLocaleString('es-AR')} kg</strong></span>{t.brix&&<span>{t.brix}°Bx</span>}{t.nombre_prov&&<span style={{color:'#7f8c8d'}}>{t.nombre_prov}</span>}</div>)}
          </Card>}
          {resultado.insumos_utilizados?.length>0&&<Card><h4 style={{margin:'0 0 10px',color:'#3498db'}}>🧪 Insumos utilizados</h4>
            {resultado.insumos_utilizados.map(i=><div key={i.operacion_id} style={{display:'flex',gap:'14px',fontSize:'13px',padding:'5px 0',borderBottom:'1px solid #f0f0f0'}}><span style={{color:'#7f8c8d',minWidth:'80px'}}>{i.fecha?.slice(0,10)}</span><strong>{i.insumo}</strong><span>{i.cantidad} {i.unidad}</span>{i.lote_proveedor&&<span style={{color:'#7f8c8d'}}>Lote: {i.lote_proveedor}</span>}</div>)}
          </Card>}
        </>}
        {direccion==='adelante'&&<>
          {resultado.ordenes_embotellado?.length>0&&<Card><h4 style={{margin:'0 0 10px',color:'#e74c3c'}}>🍾 Órdenes de embotellado</h4>
            {resultado.ordenes_embotellado.map(o=><div key={o.orden_id} style={{display:'flex',gap:'14px',fontSize:'13px',padding:'5px 0',borderBottom:'1px solid #f0f0f0',flexWrap:'wrap'}}><strong>OE #{o.orden_id}</strong><span>{o.formato} ml</span><span>{parseFloat(o.botellas||0).toLocaleString('es-AR')} botellas</span>{o.cod_art_pt&&<Badge text={o.cod_art_pt} color="#2c3e50"/>}<span style={{color:'#7f8c8d'}}>{o.fecha}</span></div>)}
          </Card>}
          {resultado.guias_traslado?.length>0&&<Card><h4 style={{margin:'0 0 10px',color:'#16a085'}}>📦 Guías de traslado</h4>
            {resultado.guias_traslado.map(g=><div key={g.guia_id} style={{display:'flex',gap:'14px',fontSize:'13px',padding:'5px 0',borderBottom:'1px solid #f0f0f0'}}><strong>Guía #{g.guia_id}</strong><span>{g.fecha}</span><span>→ {g.destino}</span><span>{parseFloat(g.litros_o_unidades||0).toLocaleString('es-AR')} L/u</span></div>)}
          </Card>}
        </>}
      </div>}
    </div>
  )
}


// ─────────────────────────────────────────────────────────────────────────────
// FERMENTACIÓN, CATA Y SO₂ — se incluyen sin cambios (implementación completa)
// Los tabs de fermentacion y cata ahora SÍ se renderizan (corrección de bug)
// ─────────────────────────────────────────────────────────────────────────────

// [FermentacionTab y CataSO2Tab se mantienen idénticos a la versión original]
// Se omite su código aquí para no duplicar — copiarlos del archivo original
// a continuación de este bloque, antes de la función ModuloBodega.

// ─────────────────────────────────────────────────────────────────────────────
// FERMENTACIÓN — Seguimiento diario, remontajes y FML
// ─────────────────────────────────────────────────────────────────────────────
function FermentacionTab({ lotes = [] }) {
  const safeLotes = Array.isArray(lotes) ? lotes : []
  const [loteId, setLoteId]   = useState('')
  const [curva, setCurva]     = useState([])
  const [lecturas, setLecturas] = useState([])
  const [remontajes, setRemontajes] = useState([])
  const [fml, setFml]         = useState(null)
  const [sub, setSub]         = useState('curva')
  const [form, setForm]       = useState({ turno:'M' })
  const [formRem, setFormRem] = useState({ tipo:'REM', objetivo:'EXT' })
  const [formFml, setFormFml] = useState({ tipo:'INO', estado:'PE' })
  const [formCroma, setFormCroma] = useState({})
  const [msg, setMsg]         = useState('')
  const [showFormRem, setShowFormRem] = useState(false)

  const setF  = (k,v) => setForm(f => ({...f,[k]:v}))
  const setFR = (k,v) => setFormRem(f => ({...f,[k]:v}))
  const setFF = (k,v) => setFormFml(f => ({...f,[k]:v}))
  const setFC = (k,v) => setFormCroma(f => ({...f,[k]:v}))

  const cargarDatos = (lid) => {
    api(`fermentacion/?lote_id=${lid}`).then(r => setLecturas(Array.isArray(r?.data) ? r.data : []))
    api(`fermentacion/curva/?lote_id=${lid}`).then(r => setCurva(Array.isArray(r?.data) ? r.data : []))
    api(`remontajes/?lote_id=${lid}`).then(r => setRemontajes(Array.isArray(r?.data) ? r.data : []))
    api(`fml/?lote_id=${lid}`).then(r => setFml(r?.data || null))
  }
  const seleccionarLote = (lid) => { setLoteId(lid); if (lid) cargarDatos(lid) }

  const guardarLectura = async () => {
    if (!loteId) return setMsg('❌ Seleccioná un lote')
    const r = await api('fermentacion/', 'POST', {
      ...form, lote_id: loteId,
      fecha: form.fecha || new Date().toISOString().slice(0,10), usuario: 'admin',
    })
    setMsg(r.ok ? (r.data?.alerta ? '⚠️ '+r.data.alerta : '✅ Lectura guardada') : '❌ '+r.msg)
    if (r.ok) { setForm({turno:'M'}); cargarDatos(loteId) }
  }

  const guardarRemontaje = async () => {
    if (!loteId) return setMsg('❌ Seleccioná un lote')
    const r = await api('remontajes/', 'POST', {
      ...formRem, lote_id: loteId,
      fecha: formRem.fecha || new Date().toISOString(), usuario: 'admin',
    })
    setMsg(r.ok ? '✅ Remontaje registrado' : '❌ '+r.msg)
    if (r.ok) { setFormRem({tipo:'REM',objetivo:'EXT'}); setShowFormRem(false); cargarDatos(loteId) }
  }

  const guardarFml = async () => {
    if (!loteId) return setMsg('❌ Seleccioná un lote')
    const r = await api('fml/', 'POST', { ...formFml, lote_id: loteId, accion:'guardar_fml', usuario:'admin' })
    setMsg(r.ok ? (r.data?.alerta ? '⚠️ '+r.data.alerta : '✅ FML guardada') : '❌ '+r.msg)
    if (r.ok) cargarDatos(loteId)
  }

  const guardarCroma = async () => {
    if (!loteId) return setMsg('❌ Seleccioná un lote')
    const r = await api('fml/', 'POST', { ...formCroma, lote_id: loteId, accion:'agregar_croma', usuario:'admin' })
    setMsg(r.ok ? (r.data?.fml_completada ? '🎉 FML COMPLETADA' : '✅ Cromatografía registrada') : '❌ '+r.msg)
    if (r.ok) { setFormCroma({}); cargarDatos(loteId) }
  }

  const turnoOpts   = [{value:'M',label:'🌅 Mañana'},{value:'T',label:'☀️ Tarde'},{value:'N',label:'🌙 Noche'}]
  const tiposRem    = [{value:'REM',label:'Remontaje'},{value:'DEL',label:'Délestage'},{value:'PIJ',label:'Pigeage'},{value:'OTR',label:'Otra práctica'}]
  const objetivosRem= [{value:'EXT',label:'Extracción color/taninos'},{value:'OXI',label:'Oxigenación'},{value:'TEM',label:'Homogenizar temperatura'},{value:'SOM',label:'Humedecer sombrero'},{value:'OTR',label:'Otro'}]
  const tiposFml    = [{value:'INO',label:'Inoculación bacteriana'},{value:'ENA',label:'FML espontánea'},{value:'INH',label:'Inhibición FML'}]
  const estadosFml  = [{value:'PE',label:'Pendiente'},{value:'AC',label:'En curso'},{value:'CO',label:'Completada'},{value:'FA',label:'Fallida'}]
  const resultCromas= [{value:'PE',label:'⏳ Pendiente'},{value:'TP',label:'🟡 Trazas málico'},{value:'AU',label:'✅ Ausente (FML completa)'},{value:'AL',label:'🔴 Alto málico'}]
  const lotesFer    = safeLotes.filter(l => ['EB','CR'].includes(l.estado))
  const ultima      = lecturas[lecturas.length - 1]
  const trabada     = lecturas.length >= 3 && lecturas.slice(-3).every(l => l.fermentacion_trabada)

  const CurvaChart = () => {
    if (curva.length < 2) return <p style={{color:'#bdc3c7',fontSize:'12px',textAlign:'center',padding:'20px'}}>Mínimo 2 lecturas para ver la curva</p>
    const W=500, H=120, PAD=30
    const dens = curva.map(c => c.densidad)
    const minD = Math.min(...dens)-5, maxD = Math.max(...dens)+5
    const xS = i => PAD+(i/(curva.length-1))*(W-PAD*2)
    const yS = d => PAD+(1-(d-minD)/(maxD-minD))*(H-PAD*2)
    const pathD = curva.map((c,i) => `${i===0?'M':'L'}${xS(i).toFixed(1)},${yS(c.densidad).toFixed(1)}`).join(' ')
    const pathT = curva.map((c,i) => `${i===0?'M':'L'}${xS(i).toFixed(1)},${(PAD+(1-(c.temperatura_c-10)/30)*(H-PAD*2)).toFixed(1)}`).join(' ')
    return (
      <div style={{overflowX:'auto'}}>
        <svg viewBox={`0 0 ${W} ${H}`} style={{width:'100%',maxWidth:W,display:'block',margin:'0 auto'}}>
          <path d={pathD} fill="none" stroke="#8e44ad" strokeWidth="2.5" strokeLinejoin="round"/>
          <path d={pathT} fill="none" stroke="#e74c3c" strokeWidth="1.5" strokeDasharray="4,3" strokeLinejoin="round"/>
          {curva.map((c,i) => i%Math.max(1,Math.floor(curva.length/8))===0 && (
            <g key={i}><circle cx={xS(i)} cy={yS(c.densidad)} r="3" fill="#8e44ad"/>
              <text x={xS(i)} y={H-4} textAnchor="middle" fontSize="8" fill="#999">{c.label}</text></g>
          ))}
        </svg>
        <div style={{display:'flex',gap:'16px',justifyContent:'center',fontSize:'11px',color:'#7f8c8d',marginTop:'4px'}}>
          <span><span style={{color:'#8e44ad',fontWeight:'700'}}>—</span> Densidad</span>
          <span><span style={{color:'#e74c3c',fontWeight:'700'}}>- -</span> Temperatura</span>
        </div>
      </div>
    )
  }

  return (
    <div>
      {msg && <div style={{padding:'8px 14px',borderRadius:'7px',fontSize:'13px',marginBottom:'12px',
        background:msg.startsWith('🎉')||msg.startsWith('✅')?'#EAF7EE':msg.startsWith('⚠️')?'#FFF8E1':'#FCEBEB',
        color:msg.startsWith('🎉')||msg.startsWith('✅')?'#1A6634':msg.startsWith('⚠️')?'#856404':'#A32D2D'}}>{msg}</div>}
      <div style={{display:'grid',gridTemplateColumns:'260px 1fr',gap:'16px'}}>
        <Card>
          <h4 style={{margin:'0 0 10px',fontSize:'13px',color:'#2c3e50',fontWeight:'700'}}>Lote en fermentación</h4>
          <select value={loteId} onChange={e=>seleccionarLote(e.target.value)}
            style={{width:'100%',padding:'8px 10px',border:'1px solid #ddd',borderRadius:'6px',fontSize:'13px',marginBottom:'12px'}}>
            <option value="">— Seleccionar lote —</option>
            {lotesFer.map(l=><option key={l.id} value={l.id}>{l.codigo} · {l.varietal_nombre}</option>)}
          </select>
          {loteId && ultima && (
            <div>
              <p style={{fontSize:'11px',color:'#7f8c8d',fontWeight:'700',textTransform:'uppercase',margin:'0 0 8px'}}>Última lectura</p>
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'6px'}}>
                {[{label:'Densidad',val:ultima.densidad,unit:'g/L',color:'#8e44ad'},
                  {label:'Temperatura',val:ultima.temperatura_c,unit:'°C',color:'#e74c3c'},
                  {label:'°Alc probable',val:ultima.alcohol_probable?.toFixed(1),unit:'%',color:'#27ae60'}
                ].map(k=>(
                  <div key={k.label} style={{background:'#f8f9fa',borderRadius:'6px',padding:'8px',textAlign:'center'}}>
                    <div style={{fontSize:'10px',color:'#7f8c8d'}}>{k.label}</div>
                    <div style={{fontSize:'16px',fontWeight:'800',color:k.color}}>{k.val}</div>
                    <div style={{fontSize:'10px',color:'#aaa'}}>{k.unit}</div>
                  </div>
                ))}
              </div>
              {trabada && <div style={{background:'#FFEBEE',border:'1px solid #FFCDD2',borderRadius:'6px',padding:'8px 10px',marginTop:'8px',fontSize:'12px',color:'#c62828',fontWeight:'700'}}>⚠️ POSIBLE FERMENTACIÓN TRABADA</div>}
            </div>
          )}
          {loteId && (
            <div style={{marginTop:'14px'}}>
              <h4 style={{fontSize:'12px',color:'#2c3e50',fontWeight:'700',margin:'0 0 8px'}}>Registrar lectura</h4>
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'0 8px'}}>
                <Select label="Turno" value={form.turno} onChange={v=>setF('turno',v)} options={turnoOpts}/>
                <Input label="Fecha" value={form.fecha} onChange={v=>setF('fecha',v)} type="date"/>
                <Input label="Densidad *" value={form.densidad} onChange={v=>setF('densidad',v)} type="number"/>
                <Input label="Temp. °C *" value={form.temperatura_c} onChange={v=>setF('temperatura_c',v)} type="number"/>
                <Input label="°Brix" value={form.brix} onChange={v=>setF('brix',v)} type="number"/>
              </div>
              <Select label="Sombrero" value={form.estado_sombrero} onChange={v=>setF('estado_sombrero',v)} options={[{value:'SN',label:'Sin sombrero'},{value:'FO',label:'Formado'},{value:'CO',label:'Compacto'},{value:'CA',label:'Caído'}]}/>
              <Input label="Observaciones" value={form.observaciones} onChange={v=>setF('observaciones',v)}/>
              <Btn onClick={guardarLectura} color="#8e44ad">Guardar lectura</Btn>
            </div>
          )}
        </Card>
        {loteId ? (
          <div>
            <div style={{display:'flex',gap:'8px',marginBottom:'12px',flexWrap:'wrap'}}>
              {[['curva','📈 Curva'],['lecturas','📋 Lecturas'],['remontajes','🔄 Remontajes'],['fml','🦠 FML']].map(([t,l])=>(
                <Btn key={t} onClick={()=>setSub(t)} color={sub===t?'#2c3e50':'#7f8c8d'} small>{l}</Btn>
              ))}
            </div>
            {sub==='curva' && <Card><h4 style={{margin:'0 0 14px'}}>Curva fermentativa</h4><CurvaChart /></Card>}
            {sub==='lecturas' && <Card>
              <h4 style={{margin:'0 0 12px'}}>Historial de lecturas ({lecturas.length})</h4>
              {lecturas.length===0 ? <p style={{color:'#7f8c8d',fontSize:'13px'}}>Sin lecturas</p>
              : <div style={{overflowX:'auto'}}><table style={{width:'100%',borderCollapse:'collapse',fontSize:'12px'}}>
                  <thead><tr style={{background:'#f8f9fa'}}>{['Fecha','Turno','Densidad','T°C','°Brix','°Alc.','Sombrero','Estado'].map(h=><th key={h} style={{padding:'6px 8px',textAlign:'left',color:'#7f8c8d'}}>{h}</th>)}</tr></thead>
                  <tbody>{lecturas.map(l=><tr key={l.id} style={{borderBottom:'1px solid #f0f0f0',background:l.fermentacion_trabada?'#FFF8F8':'white'}}>
                    <td style={{padding:'5px 8px'}}>{l.fecha}</td><td style={{padding:'5px 8px'}}>{l.turno_display}</td>
                    <td style={{padding:'5px 8px',fontWeight:'700',color:'#8e44ad'}}>{l.densidad}</td>
                    <td style={{padding:'5px 8px',color:'#e74c3c'}}>{l.temperatura_c}°</td>
                    <td style={{padding:'5px 8px'}}>{l.brix??'—'}</td>
                    <td style={{padding:'5px 8px',color:'#27ae60'}}>{l.alcohol_probable?.toFixed(1)??'—'}%</td>
                    <td style={{padding:'5px 8px'}}>{l.estado_sombrero}</td>
                    <td style={{padding:'5px 8px'}}>{l.fermentacion_trabada?<span style={{color:'#e74c3c',fontSize:'11px',fontWeight:'700'}}>⚠️ TRABADA</span>:'OK'}</td>
                  </tr>)}</tbody>
                </table></div>}
            </Card>}
            {sub==='remontajes' && <Card>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'12px'}}>
                <h4 style={{margin:0}}>Remontajes y délestages</h4>
                <Btn onClick={()=>setShowFormRem(!showFormRem)} color="#e67e22" small>{showFormRem?'Cancelar':'+ Registrar'}</Btn>
              </div>
              {showFormRem && <div style={{background:'#fef9ef',border:'1px solid #f0c040',borderRadius:'8px',padding:'14px',marginBottom:'14px'}}>
                <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'0 14px'}}>
                  <Select label="Tipo *" value={formRem.tipo} onChange={v=>setFR('tipo',v)} options={tiposRem}/>
                  <Input label="Fecha y hora *" value={formRem.fecha} onChange={v=>setFR('fecha',v)} type="datetime-local"/>
                  <Select label="Objetivo" value={formRem.objetivo} onChange={v=>setFR('objetivo',v)} options={objetivosRem}/>
                  <Input label="Vol. bombeado (L)" value={formRem.volumen_bombeado_l} onChange={v=>setFR('volumen_bombeado_l',v)} type="number"/>
                  <Input label="Duración (min)" value={formRem.duracion_min} onChange={v=>setFR('duracion_min',v)} type="number"/>
                  <Input label="T° mosto °C" value={formRem.temperatura_mosto_c} onChange={v=>setFR('temperatura_mosto_c',v)} type="number"/>
                  <div style={{gridColumn:'1/-1'}}><Input label="Observaciones" value={formRem.observaciones} onChange={v=>setFR('observaciones',v)}/></div>
                </div>
                <Btn onClick={guardarRemontaje} color="#e67e22">Guardar</Btn>
              </div>}
              {remontajes.length===0 ? <p style={{color:'#7f8c8d',fontSize:'13px'}}>Sin registros</p>
              : remontajes.map(r=><div key={r.id} style={{borderLeft:'3px solid #e67e22',padding:'7px 12px',marginBottom:'6px',borderRadius:'0 6px 6px 0',background:'#fef9ef'}}>
                  <div style={{display:'flex',justifyContent:'space-between',fontSize:'13px'}}><strong>{r.tipo_display}</strong><span style={{color:'#7f8c8d'}}>{r.fecha?.slice(0,16).replace('T',' ')}</span></div>
                  <div style={{fontSize:'12px',color:'#7f8c8d',marginTop:'2px',display:'flex',gap:'12px',flexWrap:'wrap'}}>
                    <span>{r.objetivo_display}</span>
                    {r.volumen_bombeado_l&&<span>{parseFloat(r.volumen_bombeado_l).toLocaleString('es-AR')} L</span>}
                    {r.duracion_min&&<span>{r.duracion_min} min</span>}
                  </div>
                </div>)}
            </Card>}
            {sub==='fml' && <Card>
              <h4 style={{margin:'0 0 12px'}}>Fermentación Malo-Láctica (FML)</h4>
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'16px'}}>
                <div>
                  <h5 style={{margin:'0 0 10px',color:'#7f8c8d',fontSize:'12px',textTransform:'uppercase'}}>Configuración</h5>
                  <Select label="Tipo" value={formFml.tipo} onChange={v=>setFF('tipo',v)} options={tiposFml}/>
                  <Select label="Estado" value={formFml.estado} onChange={v=>setFF('estado',v)} options={estadosFml}/>
                  <Input label="Fecha inoculación" value={formFml.fecha_inoculacion} onChange={v=>setFF('fecha_inoculacion',v)} type="date"/>
                  <Input label="Cepa bacteria" value={formFml.cepa_bacteria} onChange={v=>setFF('cepa_bacteria',v)} placeholder="Oenococcus oeni..."/>
                  <Input label="Dosis (g/hL)" value={formFml.dosis_ghl} onChange={v=>setFF('dosis_ghl',v)} type="number"/>
                  <Input label="pH al inicio" value={formFml.ph_al_inicio} onChange={v=>setFF('ph_al_inicio',v)} type="number"/>
                  <Input label="SO₂ libre inicio (mg/L)" value={formFml.so2_libre_al_inicio} onChange={v=>setFF('so2_libre_al_inicio',v)} type="number"/>
                  <Btn onClick={guardarFml} color="#27ae60">Guardar FML</Btn>
                </div>
                <div>
                  <h5 style={{margin:'0 0 10px',color:'#7f8c8d',fontSize:'12px',textTransform:'uppercase'}}>Cromatografías</h5>
                  {fml?.cromatografias?.map(c=>(
                    <div key={c.id} style={{display:'flex',justifyContent:'space-between',padding:'6px 10px',borderRadius:'5px',marginBottom:'4px',background:c.resultado==='AU'?'#EAF7EE':c.resultado==='AL'?'#FFEBEE':'#f8f9fa',fontSize:'12px'}}>
                      <span>{c.fecha}</span><strong style={{color:c.resultado==='AU'?'#1A6634':c.resultado==='AL'?'#c62828':'#7f8c8d'}}>{c.resultado_display}</strong>
                    </div>
                  ))}
                  {(!fml?.cromatografias||fml.cromatografias.length===0)&&<p style={{color:'#bdc3c7',fontSize:'12px'}}>Sin cromatografías</p>}
                  <div style={{marginTop:'12px',paddingTop:'12px',borderTop:'1px solid #ecf0f1'}}>
                    <p style={{fontSize:'12px',color:'#7f8c8d',fontWeight:'700',margin:'0 0 8px'}}>Agregar cromatografía</p>
                    <Input label="Fecha *" value={formCroma.fecha} onChange={v=>setFC('fecha',v)} type="date"/>
                    <Select label="Resultado *" value={formCroma.resultado} onChange={v=>setFC('resultado',v)} options={resultCromas}/>
                    <Input label="Acidez volátil (g/L)" value={formCroma.acidez_volatil} onChange={v=>setFC('acidez_volatil',v)} type="number"/>
                    <Btn onClick={guardarCroma} color="#3498db">Registrar</Btn>
                  </div>
                </div>
              </div>
            </Card>}
          </div>
        ) : (
          <div style={{display:'flex',alignItems:'center',justifyContent:'center',height:'220px',color:'#bdc3c7',fontSize:'14px'}}>
            ← Seleccioná un lote en fermentación
          </div>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// CATA TÉCNICA Y GESTIÓN SO₂
// ─────────────────────────────────────────────────────────────────────────────
function CataSO2Tab({ lotes = [] }) {
  const safeLotes = Array.isArray(lotes) ? lotes : []
  const [sub, setSub]         = useState('cata')
  const [loteId, setLoteId]   = useState('')
  const [catas, setCatas]     = useState([])
  const [histSO2, setHistSO2] = useState([])
  const [form, setForm]       = useState({ contexto:'RU', conclusion:'AP' })
  const [formSO2, setFormSO2] = useState({ so2_molecular_objetivo:'0.5' })
  const [calc, setCalc]       = useState(null)
  const [msg, setMsg]         = useState('')

  const setF  = (k,v) => setForm(f=>({...f,[k]:v}))
  const setFS = (k,v) => setFormSO2(f=>({...f,[k]:v}))

  const cargarDatos = (lid) => {
    api(`catas/?lote_id=${lid}`).then(r => setCatas(Array.isArray(r?.data) ? r.data : []))
    api(`so2/?lote_id=${lid}`).then(r => setHistSO2(Array.isArray(r?.data) ? r.data : []))
  }
  const seleccionarLote = (lid) => { setLoteId(lid); if (lid) cargarDatos(lid) }

  const guardarCata = async () => {
    if (!loteId||!form.fecha) return setMsg('❌ Seleccioná lote y fecha')
    const r = await api('catas/', 'POST', { ...form, lote_id: loteId, usuario:'admin' })
    setMsg(r.ok ? '✅ Cata guardada' : '❌ '+r.msg)
    if (r.ok) { setForm({contexto:'RU',conclusion:'AP'}); cargarDatos(loteId) }
  }

  const guardarSO2 = async () => {
    if (!loteId) return setMsg('❌ Seleccioná un lote')
    const r = await api('so2/', 'POST', {
      ...formSO2, lote_id: loteId,
      fecha: formSO2.fecha || new Date().toISOString().slice(0,10), usuario:'admin',
    })
    setMsg(r.ok ? '✅ '+r.msg : '❌ '+r.msg)
    if (r.ok) { setCalc(r.data); cargarDatos(loteId) }
  }

  const calcularSO2 = async () => {
    if (!formSO2.so2_libre_medido||!formSO2.ph_actual) return
    const lote = safeLotes.find(l => String(l.id)===String(loteId))
    const litros = lote?.litros_actuales || 1000
    const r = await api(`so2/calculadora/?libre=${formSO2.so2_libre_medido}&ph=${formSO2.ph_actual}&objetivo_molecular=${formSO2.so2_molecular_objetivo||0.5}&litros=${litros}`)
    if (r.ok) setCalc(r.data)
  }

  const contextos   = [{value:'RU',label:'Rutina'},{value:'EM',label:'Pre-embotellado'},{value:'EV',label:'Evaluación calidad'},{value:'CO',label:'Coupage'},{value:'EX',label:'Exportación'}]
  const conclusiones= [{value:'AP',label:'✅ Aprobado'},{value:'RA',label:'⚠️ Con reservas'},{value:'RE',label:'❌ Rechazado'},{value:'PD',label:'⏳ Pendiente'}]
  const escala      = ['1','2','3','4','5'].map(v=>({value:v,label:`${v} – ${{1:'Muy def.',2:'Def.',3:'Correcto',4:'Bueno',5:'Excelente'}[v]}`}))
  const conclusionColor = { AP:'#27ae60', RA:'#e67e22', RE:'#e74c3c', PD:'#7f8c8d' }
  const alertaColor = { OK:'#27ae60', BAJO:'#e67e22', CRITICO:'#e74c3c' }

  return (
    <div>
      {msg && <div style={{padding:'8px 14px',borderRadius:'7px',fontSize:'13px',marginBottom:'12px',
        background:msg.startsWith('✅')?'#EAF7EE':'#FCEBEB',color:msg.startsWith('✅')?'#1A6634':'#A32D2D'}}>{msg}</div>}
      <div style={{display:'flex',gap:'16px',alignItems:'flex-start',marginBottom:'16px',flexWrap:'wrap'}}>
        <div style={{flex:'0 0 260px'}}>
          <label style={{fontSize:'12px',color:'#7f8c8d',display:'block',marginBottom:'4px',fontWeight:'600'}}>Lote</label>
          <select value={loteId} onChange={e=>seleccionarLote(e.target.value)}
            style={{width:'100%',padding:'8px 10px',border:'1px solid #ddd',borderRadius:'6px',fontSize:'13px'}}>
            <option value="">— Seleccionar lote —</option>
            {safeLotes.map(l=><option key={l.id} value={l.id}>{l.codigo} · {l.varietal_nombre} {l.campaña}</option>)}
          </select>
        </div>
        <div style={{display:'flex',gap:'8px',alignItems:'flex-end',paddingBottom:'2px'}}>
          {[['cata','🍷 Cata técnica'],['so2','🧊 Gestión SO₂']].map(([t,l])=>(
            <Btn key={t} onClick={()=>setSub(t)} color={sub===t?'#2c3e50':'#7f8c8d'} small>{l}</Btn>
          ))}
        </div>
      </div>

      {sub==='cata' && (
        <div style={{display:'grid',gridTemplateColumns:'320px 1fr',gap:'16px'}}>
          <Card>
            <h4 style={{margin:'0 0 12px'}}>Nueva cata técnica</h4>
            <Input label="Fecha *" value={form.fecha} onChange={v=>setF('fecha',v)} type="date"/>
            <Select label="Contexto *" value={form.contexto} onChange={v=>setF('contexto',v)} options={contextos}/>
            <Input label="Catadores" value={form.catadores} onChange={v=>setF('catadores',v)} placeholder="E. Torres, M. López"/>
            <p style={{fontSize:'11px',color:'#7f8c8d',fontWeight:'700',textTransform:'uppercase',letterSpacing:'.5px',margin:'8px 0 6px'}}>Nariz</p>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'0 10px'}}>
              <Select label="Intensidad" value={form.nariz_intensidad} onChange={v=>setF('nariz_intensidad',v)} options={escala}/>
              <Input label="Calidad" value={form.nariz_calidad} onChange={v=>setF('nariz_calidad',v)} placeholder="Limpia, expresiva..."/>
            </div>
            <Input label="Descriptores" value={form.nariz_descriptores} onChange={v=>setF('nariz_descriptores',v)} placeholder="Frutos negros, especias, roble..."/>
            <p style={{fontSize:'11px',color:'#7f8c8d',fontWeight:'700',textTransform:'uppercase',letterSpacing:'.5px',margin:'8px 0 6px'}}>Boca</p>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'0 10px'}}>
              <Select label="Acidez" value={form.boca_acidez} onChange={v=>setF('boca_acidez',v)} options={escala}/>
              <Input label="Taninos" value={form.boca_taninos} onChange={v=>setF('boca_taninos',v)} placeholder="Sedosos, astringentes..."/>
              <Input label="Cuerpo" value={form.boca_cuerpo} onChange={v=>setF('boca_cuerpo',v)} placeholder="Ligero, medio, potente"/>
              <Select label="Final (seg)" value={form.boca_final_s} onChange={v=>setF('boca_final_s',v)} options={escala}/>
            </div>
            <p style={{fontSize:'11px',color:'#7f8c8d',fontWeight:'700',textTransform:'uppercase',letterSpacing:'.5px',margin:'8px 0 6px'}}>Defectos</p>
            <div style={{display:'flex',flexWrap:'wrap',gap:'8px',marginBottom:'10px'}}>
              {[['defecto_brett','Brett'],['defecto_reduccion','Reducción'],['defecto_va_alta','VA alta'],['defecto_oxidacion','Oxidación'],['defecto_turbidez','Turbidez']].map(([k,l])=>(
                <label key={k} style={{display:'flex',alignItems:'center',gap:'4px',fontSize:'12px',cursor:'pointer',color:form[k]?'#e74c3c':'#7f8c8d',fontWeight:form[k]?'700':'400'}}>
                  <input type="checkbox" checked={!!form[k]} onChange={e=>setF(k,e.target.checked)}/>{l}
                </label>
              ))}
            </div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'0 10px'}}>
              <Select label="Puntaje" value={form.puntaje} onChange={v=>setF('puntaje',v)} options={escala}/>
              <Select label="Conclusión *" value={form.conclusion} onChange={v=>setF('conclusion',v)} options={conclusiones}/>
            </div>
            <Input label="Acción recomendada" value={form.accion_recomendada} onChange={v=>setF('accion_recomendada',v)}/>
            <Btn onClick={guardarCata} color="#8e44ad">Guardar cata</Btn>
          </Card>
          <div>
            {catas.length===0 ? <Card><p style={{color:'#bdc3c7',textAlign:'center',padding:'20px',margin:0}}>Sin catas para este lote</p></Card>
            : catas.map(c=>(
              <div key={c.id} style={{background:'white',border:'1px solid #ecf0f1',borderLeft:`4px solid ${conclusionColor[c.conclusion]||'#ddd'}`,borderRadius:'8px',padding:'14px 16px',marginBottom:'10px'}}>
                <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:'6px'}}>
                  <div>
                    <strong>{c.contexto_display}</strong>
                    <span style={{background:conclusionColor[c.conclusion]+'22',color:conclusionColor[c.conclusion],borderRadius:'4px',padding:'1px 9px',fontSize:'11px',fontWeight:'700',marginLeft:'8px'}}>{c.conclusion_display}</span>
                    {c.tiene_defectos&&<span style={{background:'#FFEBEE',color:'#c62828',borderRadius:'4px',padding:'1px 9px',fontSize:'11px',fontWeight:'700',marginLeft:'4px'}}>⚠️ Defectos</span>}
                  </div>
                  <span style={{fontSize:'12px',color:'#7f8c8d'}}>{c.fecha}</span>
                </div>
                {c.nariz_descriptores&&<div style={{fontSize:'12px',color:'#7f8c8d',marginBottom:'2px'}}>👃 {c.nariz_descriptores}</div>}
                {c.accion_recomendada&&<p style={{fontSize:'12px',color:'#e67e22',margin:'4px 0 0',fontWeight:'600'}}>→ {c.accion_recomendada}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {sub==='so2' && (
        <div style={{display:'grid',gridTemplateColumns:'320px 1fr',gap:'16px'}}>
          <Card>
            <h4 style={{margin:'0 0 12px'}}>Calculadora SO₂ molecular</h4>
            <Input label="SO₂ libre medido (mg/L) *" value={formSO2.so2_libre_medido} onChange={v=>setFS('so2_libre_medido',v)} type="number"/>
            <Input label="pH actual *" value={formSO2.ph_actual} onChange={v=>setFS('ph_actual',v)} type="number"/>
            <Input label="SO₂ molecular objetivo (mg/L)" value={formSO2.so2_molecular_objetivo} onChange={v=>setFS('so2_molecular_objetivo',v)} type="number"/>
            <Input label="T° bodega °C" value={formSO2.temperatura_bodega_c} onChange={v=>setFS('temperatura_bodega_c',v)} type="number" placeholder="15"/>
            <Btn onClick={calcularSO2} color="#3498db" small>🔢 Solo calcular</Btn>
            {calc && (
              <div style={{background:'#f8f9fa',borderRadius:'8px',padding:'12px',margin:'10px 0'}}>
                <div style={{display:'flex',justifyContent:'space-between',marginBottom:'8px'}}>
                  <span style={{fontSize:'12px',fontWeight:'700',color:'#7f8c8d'}}>Resultado</span>
                  <span style={{background:alertaColor[calc.estado]+'22',color:alertaColor[calc.estado],borderRadius:'4px',padding:'2px 10px',fontSize:'11px',fontWeight:'700'}}>{calc.estado}</span>
                </div>
                {[{label:'SO₂ molecular actual',val:`${calc.so2_molecular_actual} mg/L`,color:alertaColor[calc.estado]},
                  {label:'SO₂ libre necesario',val:`${calc.so2_libre_necesario} mg/L`,color:'#2c3e50'},
                  {label:'Déficit',val:`${calc.deficit_so2} mg/L`,color:calc.deficit_so2>0?'#e74c3c':'#27ae60'},
                  {label:'Metabisulfito K',val:`${calc.gramos_metabisulfito_k} g`,color:'#8e44ad'},
                ].map(k=>(
                  <div key={k.label} style={{display:'flex',justifyContent:'space-between',padding:'4px 0',borderBottom:'1px solid #f0f0f0',fontSize:'12px'}}>
                    <span style={{color:'#7f8c8d'}}>{k.label}</span><strong style={{color:k.color}}>{k.val}</strong>
                  </div>
                ))}
              </div>
            )}
            {loteId && <>
              <Input label="Fecha medición *" value={formSO2.fecha} onChange={v=>setFS('fecha',v)} type="date"/>
              <Select label="Método" value={formSO2.metodo_medicion} onChange={v=>setFS('metodo_medicion',v)} options={[{value:'Ripper',label:'Ripper'},{value:'AO',label:'Aireación/oxidación'},{value:'ENZ',label:'Enzimático'},{value:'OTR',label:'Otro'}]}/>
              <div style={{display:'flex',alignItems:'center',gap:'8px',marginBottom:'10px'}}>
                <input type="checkbox" id="adicion" checked={!!formSO2.adicion_realizada} onChange={e=>setFS('adicion_realizada',e.target.checked)}/>
                <label htmlFor="adicion" style={{fontSize:'13px',cursor:'pointer'}}>Adición realizada</label>
              </div>
              {formSO2.adicion_realizada&&<Input label="Gramos MBK agregados (real)" value={formSO2.gramos_agregados_real} onChange={v=>setFS('gramos_agregados_real',v)} type="number"/>}
              <Btn onClick={guardarSO2} color="#27ae60">💾 Guardar en historial</Btn>
            </>}
          </Card>
          <div>
            {histSO2.length===0 ? <Card><p style={{color:'#bdc3c7',textAlign:'center',padding:'20px',margin:0}}>Sin historial SO₂</p></Card>
            : <Card style={{padding:0}}>
                <div style={{overflowX:'auto'}}>
                  <table style={{width:'100%',borderCollapse:'collapse',fontSize:'12px'}}>
                    <thead><tr style={{background:'#f8f9fa'}}>{['Fecha','SO₂ L.','pH','Mol. actual','Necesario','Déficit','MBK (g)','Próx. medición','Alerta'].map(h=><th key={h} style={{padding:'8px 10px',textAlign:'left',color:'#7f8c8d'}}>{h}</th>)}</tr></thead>
                    <tbody>{histSO2.map((s,i)=>(
                      <tr key={s.id} style={{borderBottom:'1px solid #f0f0f0',background:i%2===0?'white':'#fafafa'}}>
                        <td style={{padding:'7px 10px',fontWeight:'600'}}>{s.fecha}</td>
                        <td style={{padding:'7px 10px'}}>{s.so2_libre_medido}</td>
                        <td style={{padding:'7px 10px'}}>{s.ph_actual}</td>
                        <td style={{padding:'7px 10px',fontWeight:'700',color:alertaColor[s.alerta]||'#7f8c8d'}}>{s.so2_molecular_actual?.toFixed(3)||'—'}</td>
                        <td style={{padding:'7px 10px'}}>{s.so2_libre_necesario?.toFixed(1)||'—'}</td>
                        <td style={{padding:'7px 10px',color:parseFloat(s.deficit_so2)>0?'#e74c3c':'#27ae60',fontWeight:'700'}}>{s.deficit_so2?.toFixed(1)||'0'}</td>
                        <td style={{padding:'7px 10px',color:'#8e44ad',fontWeight:'700'}}>{s.gramos_metabisulfito?.toFixed(1)||'—'}</td>
                        <td style={{padding:'7px 10px',color:'#3498db'}}>{s.proxima_medicion||'—'}</td>
                        <td style={{padding:'7px 10px'}}><span style={{background:alertaColor[s.alerta]+'22',color:alertaColor[s.alerta],borderRadius:'20px',padding:'2px 9px',fontSize:'11px',fontWeight:'700'}}>{s.alerta}</span></td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              </Card>}
          </div>
        </div>
      )}
    </div>
  )
}


// ─────────────────────────────────────────────────────────────────────────────
// MÓDULO PRINCIPAL — MEJORA: agrega fermentacion y cata al render
// ─────────────────────────────────────────────────────────────────────────────
// MaestrosTab — ABM completo para catálogos del módulo Bodega
// Entidades: Varietales · Insumos enológicos · Fichas de producto · Recipientes
//
// INTEGRACIÓN en ModuloBodega.jsx:
//   1. Copiar este componente antes de la constante TABS
//   2. Agregar { id:'maestros', label:'⚙️ Maestros' } al array TABS
//   3. Agregar al render:
//        {tab === 'maestros' && <MaestrosTab onRefresh={() => {
//            api('varietales/').then(r => setVarietales(Array.isArray(r?.data)?r.data:[]))
//            api('recipientes/').then(r => setRecipientes(Array.isArray(r?.data)?r.data:[]))
//        }} />}
// ─────────────────────────────────────────────────────────────────────────────

function MaestrosTab({ onRefresh }) {
  const [sub, setSub] = useState('varietales')

  const SUB_TABS = [
    { id: 'varietales', icon: '🍇', label: 'Varietales' },
    { id: 'insumos',    icon: '🧪', label: 'Insumos enológicos' },
    { id: 'fichas',     icon: '📋', label: 'Fichas de producto' },
    { id: 'recipientes',icon: '🗄️', label: 'Recipientes' },
  ]

  return (
    <div>
      {/* Sub-tab bar */}
      <div style={{
        display: 'flex', gap: '4px', marginBottom: '20px',
        background: 'white', borderRadius: '10px',
        padding: '6px', boxShadow: '0 2px 8px rgba(0,0,0,.07)',
        width: 'fit-content',
      }}>
        {SUB_TABS.map(t => (
          <button key={t.id} onClick={() => setSub(t.id)} style={{
            padding: '8px 18px', border: 'none', cursor: 'pointer',
            borderRadius: '7px', fontWeight: '600', fontSize: '13px',
            background: sub === t.id ? '#2c3e50' : 'transparent',
            color: sub === t.id ? 'white' : '#7f8c8d',
            transition: 'all .15s',
          }}>
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {sub === 'varietales'  && <VarietalesABM  onRefresh={onRefresh} />}
      {sub === 'insumos'     && <InsumosABM     onRefresh={onRefresh} />}
      {sub === 'fichas'      && <FichasABM />}
      {sub === 'recipientes' && <RecipientesABM onRefresh={onRefresh} />}
    </div>
  )
}

// =============================================================================
// HELPERS LOCALES
// =============================================================================

function ABMMsg({ msg }) {
  if (!msg) return null
  const ok = msg.startsWith('✅')
  return (
    <div style={{
      padding: '10px 14px', borderRadius: '7px', fontSize: '13px',
      fontWeight: '600', marginBottom: '14px',
      background: ok ? '#EAF7EE' : '#FCEBEB',
      color:      ok ? '#1A6634' : '#A32D2D',
      border: `1px solid ${ok ? '#A8DFB8' : '#F5C6C6'}`,
    }}>{msg}</div>
  )
}

// Badge de estado activo/inactivo
function EstadoBadge({ activo }) {
  return (
    <span style={{
      display: 'inline-block', padding: '2px 9px', borderRadius: '20px',
      fontSize: '11px', fontWeight: '700',
      background: activo ? '#EAF7EE' : '#F5F5F5',
      color:      activo ? '#1A6634' : '#999',
      border: `1px solid ${activo ? '#A8DFB8' : '#DDD'}`,
    }}>
      {activo ? '● Activo' : '○ Inactivo'}
    </span>
  )
}

// Layout ABM estándar: formulario izq + tabla der
function ABMLayout({ titulo, formContent, onSubmit, onNew, editando, children, msg }) {
  return (
    <div>
      <ABMMsg msg={msg} />
      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '20px', alignItems: 'start' }}>

        {/* Panel formulario */}
        <div style={{
          background: 'white', borderRadius: '10px', padding: '20px',
          boxShadow: '0 2px 8px rgba(0,0,0,.07)',
          border: editando ? '2px solid #e67e22' : '2px solid #ecf0f1',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h4 style={{ margin: 0, color: '#2c3e50', fontSize: '14px', fontWeight: '700' }}>
              {editando ? '✏️ Editando' : `➕ Nuevo ${titulo}`}
            </h4>
            {editando && (
              <button onClick={onNew} style={{
                background: 'none', border: '1px solid #ddd', borderRadius: '5px',
                padding: '3px 10px', cursor: 'pointer', fontSize: '12px', color: '#7f8c8d',
              }}>
                Nuevo
              </button>
            )}
          </div>
          {formContent}
          <button onClick={onSubmit} style={{
            width: '100%', padding: '10px', marginTop: '4px',
            background: editando ? '#e67e22' : '#2c3e50',
            color: 'white', border: 'none', borderRadius: '7px',
            cursor: 'pointer', fontWeight: '700', fontSize: '13px',
          }}>
            {editando ? 'Guardar cambios' : `Crear ${titulo}`}
          </button>
        </div>

        {/* Panel lista */}
        <div style={{ background: 'white', borderRadius: '10px', boxShadow: '0 2px 8px rgba(0,0,0,.07)', overflow: 'hidden' }}>
          {children}
        </div>
      </div>
    </div>
  )
}

// Celda de tabla
const TC = ({ children, bold, right, muted, color }) => (
  <td style={{
    padding: '10px 14px', fontSize: '13px',
    fontWeight: bold ? '700' : '400',
    textAlign: right ? 'right' : 'left',
    color: color || (muted ? '#95a5a6' : '#2c3e50'),
    whiteSpace: 'nowrap',
  }}>{children}</td>
)

// Encabezado de tabla
function THead({ cols }) {
  return (
    <thead>
      <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #ecf0f1' }}>
        {cols.map(c => (
          <th key={c} style={{ padding: '10px 14px', textAlign: 'left', fontSize: '11px',
            fontWeight: '700', color: '#7f8c8d', textTransform: 'uppercase', letterSpacing: '.5px' }}>
            {c}
          </th>
        ))}
      </tr>
    </thead>
  )
}

// Fila vacía
function TEmpty({ cols, texto }) {
  return (
    <tr><td colSpan={cols} style={{ padding: '30px', textAlign: 'center', color: '#bdc3c7', fontSize: '13px' }}>
      {texto || 'Sin registros'}
    </td></tr>
  )
}

// Botón editar / desactivar inline
function BtnTabla({ onClick, color = '#3498db', children }) {
  return (
    <button onClick={onClick} style={{
      background: 'none', border: `1px solid ${color}`, borderRadius: '5px',
      padding: '3px 10px', cursor: 'pointer', fontSize: '12px',
      color, fontWeight: '600', marginLeft: '6px',
    }}>{children}</button>
  )
}

// Input y Select reutilizables (versión compacta para el ABM)
const FInput = ({ label, value, onChange, type = 'text', placeholder, disabled, required }) => (
  <div style={{ marginBottom: '10px' }}>
    <label style={{ fontSize: '12px', color: '#7f8c8d', display: 'block', marginBottom: '3px', fontWeight: '600' }}>
      {label}{required && <span style={{ color: '#e74c3c' }}> *</span>}
    </label>
    <input type={type} value={value || ''} onChange={e => onChange(e.target.value)}
      placeholder={placeholder} disabled={disabled}
      style={{
        width: '100%', padding: '8px 10px', border: '1px solid #ddd', borderRadius: '6px',
        fontSize: '13px', boxSizing: 'border-box',
        background: disabled ? '#f8f9fa' : 'white',
        color: disabled ? '#7f8c8d' : '#2c3e50',
      }} />
  </div>
)

const FSelect = ({ label, value, onChange, options, required }) => (
  <div style={{ marginBottom: '10px' }}>
    <label style={{ fontSize: '12px', color: '#7f8c8d', display: 'block', marginBottom: '3px', fontWeight: '600' }}>
      {label}{required && <span style={{ color: '#e74c3c' }}> *</span>}
    </label>
    <select value={value || ''} onChange={e => onChange(e.target.value)}
      style={{ width: '100%', padding: '8px 10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '13px' }}>
      <option value="">— Seleccionar —</option>
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  </div>
)

const FTextarea = ({ label, value, onChange, rows = 2, placeholder }) => (
  <div style={{ marginBottom: '10px' }}>
    <label style={{ fontSize: '12px', color: '#7f8c8d', display: 'block', marginBottom: '3px', fontWeight: '600' }}>{label}</label>
    <textarea value={value || ''} onChange={e => onChange(e.target.value)}
      rows={rows} placeholder={placeholder}
      style={{ width: '100%', padding: '8px 10px', border: '1px solid #ddd', borderRadius: '6px',
        fontSize: '13px', boxSizing: 'border-box', resize: 'vertical' }} />
  </div>
)

// =============================================================================
// ABM — VARIETALES
// =============================================================================
const COLORES_VARIETAL = [
  { value: 'T',  label: '🟣 Tinto' },
  { value: 'B',  label: '🟡 Blanco' },
  { value: 'R',  label: '🩷 Rosado' },
  { value: 'Ti', label: '🟤 Tintorera' },
]
const COLOR_CHIP = { T: '#8e44ad', B: '#f39c12', R: '#e74c3c', Ti: '#784212' }

function VarietalesABM({ onRefresh }) {
  const emptyForm = { codigo: '', nombre: '', color: 'T' }
  const [lista, setLista]   = useState([])
  const [form,  setForm]    = useState(emptyForm)
  const [msg,   setMsg]     = useState('')
  const [busq,  setBusq]    = useState('')

  const cargar = () => api('varietales/').then(r => setLista(Array.isArray(r?.data) ? r.data : []))
  useEffect(() => { cargar() }, [])

  const setF = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const editar = (v) => setForm({ codigo: v.codigo, nombre: v.nombre, color: v.color })

  const guardar = async () => {
    if (!form.codigo || !form.nombre) return setMsg('❌ Código y nombre son obligatorios')
    const r = await api('varietales/', 'POST', form)
    if (r.ok) {
      setMsg(`✅ Varietal "${form.nombre}" guardado`)
      setForm(emptyForm); cargar(); onRefresh?.()
    } else setMsg('❌ ' + r.msg)
  }

  const desactivar = async (codigo, nombre) => {
    if (!confirm(`¿Desactivar el varietal "${nombre}"?`)) return
    const r = await api('varietales/', 'POST', { codigo, nombre, activo: false })
    if (r.ok) { setMsg(`✅ "${nombre}" desactivado`); cargar(); onRefresh?.() }
    else setMsg('❌ ' + r.msg)
  }

  const filtrados = lista.filter(v =>
    `${v.codigo} ${v.nombre}`.toLowerCase().includes(busq.toLowerCase())
  )

  const isEditing = lista.some(v => v.codigo === form.codigo)

  return (
    <ABMLayout
      titulo="varietal" editando={isEditing}
      msg={msg}
      onNew={() => setForm(emptyForm)}
      onSubmit={guardar}
      formContent={
        <>
          <FInput label="Código" value={form.codigo} onChange={v => setF('codigo', v)}
            placeholder="MAL, CAB, TOR..." required disabled={isEditing} />
          {isEditing && <p style={{ fontSize: '11px', color: '#e67e22', marginTop: '-8px', marginBottom: '8px' }}>
            El código no puede modificarse
          </p>}
          <FInput label="Nombre" value={form.nombre} onChange={v => setF('nombre', v)}
            placeholder="Malbec, Cabernet Sauvignon..." required />
          <FSelect label="Color de uva" value={form.color} onChange={v => setF('color', v)}
            options={COLORES_VARIETAL} required />
          {form.color && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '8px 12px', borderRadius: '6px', background: '#f8f9fa',
              fontSize: '12px', color: '#7f8c8d', marginBottom: '4px',
            }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '50%',
                background: COLOR_CHIP[form.color] || '#7f8c8d', display: 'inline-block' }} />
              {COLORES_VARIETAL.find(c => c.value === form.color)?.label}
            </div>
          )}
        </>
      }
    >
      {/* Lista */}
      <div style={{ padding: '14px 16px', borderBottom: '1px solid #ecf0f1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '13px', color: '#7f8c8d', fontWeight: '600' }}>
          {lista.length} varietal{lista.length !== 1 ? 'es' : ''} cargados
        </span>
        <input value={busq} onChange={e => setBusq(e.target.value)} placeholder="Buscar..."
          style={{ padding: '5px 10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '12px', width: '160px' }} />
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <THead cols={['Código', 'Nombre', 'Color', 'Estado', 'Acciones']} />
          <tbody>
            {filtrados.length === 0 && <TEmpty cols={5} />}
            {filtrados.map((v, i) => (
              <tr key={v.codigo} style={{ background: i % 2 === 0 ? 'white' : '#fafafa', borderBottom: '1px solid #f0f0f0' }}>
                <TC bold><code style={{ background: '#f0f0f0', padding: '2px 7px', borderRadius: '4px', fontSize: '12px' }}>{v.codigo}</code></TC>
                <TC>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '10px', height: '10px', borderRadius: '50%',
                      background: COLOR_CHIP[v.color] || '#7f8c8d', flexShrink: 0 }} />
                    <strong>{v.nombre}</strong>
                  </div>
                </TC>
                <TC muted>{COLORES_VARIETAL.find(c => c.value === v.color)?.label?.replace(/\S+\s/, '') || v.color}</TC>
                <TC><EstadoBadge activo={v.activo !== false} /></TC>
                <TC>
                  <BtnTabla onClick={() => editar(v)} color="#3498db">✏️ Editar</BtnTabla>
                  {v.activo !== false
                    ? <BtnTabla onClick={() => desactivar(v.codigo, v.nombre)} color="#e74c3c">⊘ Desactivar</BtnTabla>
                    : <BtnTabla onClick={() => api('varietales/', 'POST', { codigo: v.codigo, nombre: v.nombre, color: v.color, activo: true }).then(() => { cargar(); onRefresh?.() })} color="#27ae60">↺ Activar</BtnTabla>
                  }
                </TC>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </ABMLayout>
  )
}

// =============================================================================
// ABM — INSUMOS ENOLÓGICOS
// =============================================================================
const TIPOS_INSUMO = [
  { value: 'SO2', label: 'Dióxido de azufre / Sulfitante' },
  { value: 'LV',  label: 'Levadura enológica' },
  { value: 'EN',  label: 'Enzima' },
  { value: 'FC',  label: 'Finning agent / Clarificante' },
  { value: 'CO',  label: 'Corrector de mosto' },
  { value: 'CL',  label: 'Coloide protector' },
  { value: 'OTR', label: 'Otro insumo' },
]
const TIPO_CHIP = {
  SO2: '#e74c3c', LV: '#27ae60', EN: '#3498db',
  FC: '#9b59b6', CO: '#e67e22', CL: '#16a085', OTR: '#7f8c8d',
}

function InsumosABM({ onRefresh }) {
  const emptyForm = { cod_art: '', nombre: '', tipo: '', unidad: '', dosis_max_gl: '' }
  const [lista, setLista] = useState([])
  const [form,  setForm]  = useState(emptyForm)
  const [msg,   setMsg]   = useState('')
  const [busq,  setBusq]  = useState('')
  const [filTipo, setFilTipo] = useState('')

  const cargar = () => api('insumos/').then(r => setLista(Array.isArray(r?.data) ? r.data : []))
  useEffect(() => { cargar() }, [])

  const setF = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const editar = (i) => setForm({ ...i })
  const esNuevo = !form.id

  const guardar = async () => {
    if (!form.cod_art || !form.nombre || !form.tipo) return setMsg('❌ Completá los campos obligatorios')
    const r = await api('insumos/', 'POST', { ...form, activo: true })
    if (r.ok) {
      setMsg(`✅ Insumo "${form.nombre}" guardado`)
      setForm(emptyForm); cargar(); onRefresh?.()
    } else setMsg('❌ ' + r.msg)
  }

  const toggleActivo = async (ins) => {
    if (ins.activo !== false && !confirm(`¿Desactivar "${ins.nombre}"?`)) return
    const r = await api('insumos/', 'POST', {
      id: ins.id, cod_art: ins.cod_art, nombre: ins.nombre, tipo: ins.tipo,
      unidad: ins.unidad, dosis_max_gl: ins.dosis_max_gl,
      activo: ins.activo === false,
    })
    if (r.ok) { setMsg(`✅ ${ins.nombre} ${ins.activo === false ? 'activado' : 'desactivado'}`); cargar() }
    else setMsg('❌ ' + r.msg)
  }

  const filtrados = lista.filter(i => {
    const matchBusq = `${i.cod_art} ${i.nombre}`.toLowerCase().includes(busq.toLowerCase())
    const matchTipo = !filTipo || i.tipo === filTipo
    return matchBusq && matchTipo
  })

  return (
    <ABMLayout
      titulo="insumo" editando={!!form.id} msg={msg}
      onNew={() => setForm(emptyForm)} onSubmit={guardar}
      formContent={
        <>
          <FInput label="Código artículo (ERP)" value={form.cod_art} onChange={v => setF('cod_art', v)}
            placeholder="INS-SO2-MBK" required disabled={!!form.id} />
          <FInput label="Nombre" value={form.nombre} onChange={v => setF('nombre', v)}
            placeholder="Metabisulfito de potasio" required />
          <FSelect label="Tipo" value={form.tipo} onChange={v => setF('tipo', v)} options={TIPOS_INSUMO} required />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 10px' }}>
            <FInput label="Unidad" value={form.unidad} onChange={v => setF('unidad', v)} placeholder="kg / g / L" />
            <FInput label="Dosis máx (g/hL)" value={form.dosis_max_gl} onChange={v => setF('dosis_max_gl', v)} type="number" />
          </div>
          {form.tipo && (
            <div style={{ padding: '8px 12px', borderRadius: '6px', background: '#f8f9fa', fontSize: '12px', color: '#7f8c8d', marginBottom: '4px' }}>
              <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: TIPO_CHIP[form.tipo], marginRight: '6px' }} />
              {TIPOS_INSUMO.find(t => t.value === form.tipo)?.label}
            </div>
          )}
        </>
      }
    >
      <div style={{ padding: '14px 16px', borderBottom: '1px solid #ecf0f1', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '13px', color: '#7f8c8d', fontWeight: '600' }}>
          {filtrados.length} de {lista.length} insumos
        </span>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <input value={busq} onChange={e => setBusq(e.target.value)} placeholder="Buscar..."
            style={{ padding: '5px 10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '12px', width: '150px' }} />
          <select value={filTipo} onChange={e => setFilTipo(e.target.value)}
            style={{ padding: '5px 10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '12px' }}>
            <option value="">Todos los tipos</option>
            {TIPOS_INSUMO.map(t => <option key={t.value} value={t.value}>{t.label.split('/')[0].trim()}</option>)}
          </select>
        </div>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <THead cols={['Código', 'Nombre', 'Tipo', 'Unidad', 'Dosis máx.', 'Estado', 'Acciones']} />
          <tbody>
            {filtrados.length === 0 && <TEmpty cols={7} />}
            {filtrados.map((i, idx) => (
              <tr key={i.id} style={{ background: idx % 2 === 0 ? 'white' : '#fafafa', borderBottom: '1px solid #f0f0f0' }}>
                <TC><code style={{ background: '#f0f0f0', padding: '2px 7px', borderRadius: '4px', fontSize: '11px' }}>{i.cod_art}</code></TC>
                <TC bold>{i.nombre}</TC>
                <TC>
                  <span style={{ background: TIPO_CHIP[i.tipo] + '22', color: TIPO_CHIP[i.tipo],
                    borderRadius: '20px', padding: '2px 10px', fontSize: '11px', fontWeight: '700' }}>
                    {i.tipo_display || i.tipo}
                  </span>
                </TC>
                <TC muted>{i.unidad}</TC>
                <TC muted>{i.dosis_max_gl ? `${i.dosis_max_gl} g/hL` : '—'}</TC>
                <TC><EstadoBadge activo={i.activo !== false} /></TC>
                <TC>
                  <BtnTabla onClick={() => editar(i)} color="#3498db">✏️ Editar</BtnTabla>
                  <BtnTabla onClick={() => toggleActivo(i)} color={i.activo === false ? '#27ae60' : '#e74c3c'}>
                    {i.activo === false ? '↺ Activar' : '⊘ Desact.'}
                  </BtnTabla>
                </TC>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </ABMLayout>
  )
}

// =============================================================================
// ABM — FICHAS DE PRODUCTO
// =============================================================================
const TIPOS_VINO_F = [
  { value: 'TI', label: 'Tinto' }, { value: 'BL', label: 'Blanco' },
  { value: 'RO', label: 'Rosado' }, { value: 'ES', label: 'Espumante' },
]

function FichasABM() {
  const emptyForm = { codigo: '', nombre: '', varietal: '', tipo_vino: 'TI', descripcion: '',
    alcohol_min: '', alcohol_max: '', acidez_total_min: '', acidez_total_max: '',
    ph_min: '', ph_max: '', azucar_max: '', so2_libre_max: '', so2_total_max: '',
    perfil_sensorial: '', proceso_elaboracion: '' }
  const [lista,      setLista]      = useState([])
  const [varietales, setVarietales] = useState([])
  const [form,       setForm]       = useState(emptyForm)
  const [msg,        setMsg]        = useState('')
  const [expanded,   setExpanded]   = useState(null)
  const [busq,       setBusq]       = useState('')

  const cargar = () => {
    api('fichas-producto/').then(r => setLista(Array.isArray(r?.data) ? r.data : []))
    api('varietales/').then(r => setVarietales(Array.isArray(r?.data) ? r.data : []))
  }
  useEffect(() => { cargar() }, [])

  const setF = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const editar = (f) => { setForm({ ...f }); window.scrollTo(0, 0) }

  const guardar = async () => {
    if (!form.codigo || !form.nombre) return setMsg('❌ Código y nombre son obligatorios')
    const r = await api('fichas-producto/', 'POST', { ...form, usuario: 'admin' })
    if (r.ok) {
      setMsg(`✅ Ficha "${form.nombre}" guardada`)
      setForm(emptyForm); cargar()
    } else setMsg('❌ ' + r.msg)
  }

  const toggleActiva = async (f) => {
    const r = await api('fichas-producto/', 'POST', { ...f, activa: !f.activa, usuario: 'admin' })
    if (r.ok) { setMsg(`✅ Ficha "${f.nombre}" ${f.activa ? 'desactivada' : 'activada'}`); cargar() }
    else setMsg('❌ ' + r.msg)
  }

  const tipoVColor = { TI: '#8e44ad', BL: '#f39c12', RO: '#e74c3c', ES: '#3498db' }
  const filtradas = lista.filter(f => `${f.codigo} ${f.nombre} ${f.varietal || ''}`.toLowerCase().includes(busq.toLowerCase()))

  return (
    <ABMLayout
      titulo="ficha" editando={!!form.id} msg={msg}
      onNew={() => setForm(emptyForm)} onSubmit={guardar}
      formContent={
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 10px' }}>
            <FInput label="Código *" value={form.codigo} onChange={v => setF('codigo', v)}
              placeholder="FT-MAL-RSV" disabled={!!form.id} />
            <FSelect label="Tipo de vino *" value={form.tipo_vino} onChange={v => setF('tipo_vino', v)} options={TIPOS_VINO_F} />
          </div>
          <FInput label="Nombre *" value={form.nombre} onChange={v => setF('nombre', v)} placeholder="Malbec Reserva" />
          <FSelect label="Varietal" value={form.varietal} onChange={v => setF('varietal', v)}
            options={varietales.map(v => ({ value: v.codigo, label: v.nombre }))} />
          <FTextarea label="Descripción" value={form.descripcion} onChange={v => setF('descripcion', v)} />

          <p style={{ fontSize: '11px', fontWeight: '700', color: '#7f8c8d', textTransform: 'uppercase', margin: '12px 0 8px', letterSpacing: '.5px' }}>
            Rangos analíticos (spec del producto)
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 10px' }}>
            <FInput label="Alcohol mín (%)" value={form.alcohol_min} onChange={v => setF('alcohol_min', v)} type="number" />
            <FInput label="Alcohol máx (%)" value={form.alcohol_max} onChange={v => setF('alcohol_max', v)} type="number" />
            <FInput label="pH mín" value={form.ph_min} onChange={v => setF('ph_min', v)} type="number" />
            <FInput label="pH máx" value={form.ph_max} onChange={v => setF('ph_max', v)} type="number" />
            <FInput label="Acid. total mín (g/L)" value={form.acidez_total_min} onChange={v => setF('acidez_total_min', v)} type="number" />
            <FInput label="Acid. total máx (g/L)" value={form.acidez_total_max} onChange={v => setF('acidez_total_max', v)} type="number" />
            <FInput label="SO₂ libre máx (mg/L)" value={form.so2_libre_max} onChange={v => setF('so2_libre_max', v)} type="number" />
            <FInput label="SO₂ total máx (mg/L)" value={form.so2_total_max} onChange={v => setF('so2_total_max', v)} type="number" />
            <div style={{ gridColumn: '1/-1' }}>
              <FInput label="Azúcar residual máx (g/L)" value={form.azucar_max} onChange={v => setF('azucar_max', v)} type="number" />
            </div>
          </div>
          <FTextarea label="Perfil sensorial" value={form.perfil_sensorial} onChange={v => setF('perfil_sensorial', v)}
            placeholder="Rojo rubí, frutos negros, especias, taninos sedosos..." rows={3} />
          <FTextarea label="Proceso de elaboración" value={form.proceso_elaboracion} onChange={v => setF('proceso_elaboracion', v)}
            placeholder="Maceración pre-fermentativa 3-5 días, fermentación a 26-28°C..." rows={3} />
        </>
      }
    >
      <div style={{ padding: '14px 16px', borderBottom: '1px solid #ecf0f1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '13px', color: '#7f8c8d', fontWeight: '600' }}>{filtradas.length} ficha{filtradas.length !== 1 ? 's' : ''}</span>
        <input value={busq} onChange={e => setBusq(e.target.value)} placeholder="Buscar ficha..."
          style={{ padding: '5px 10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '12px', width: '180px' }} />
      </div>
      <div>
        {filtradas.length === 0 && <div style={{ padding: '30px', textAlign: 'center', color: '#bdc3c7', fontSize: '13px' }}>Sin fichas</div>}
        {filtradas.map(f => (
          <div key={f.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
            {/* Cabecera */}
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '12px 16px', cursor: 'pointer',
              background: expanded === f.id ? '#fafbff' : 'white',
            }} onClick={() => setExpanded(expanded === f.id ? null : f.id)}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{
                  background: tipoVColor[f.tipo_vino] + '22', color: tipoVColor[f.tipo_vino],
                  borderRadius: '5px', padding: '2px 8px', fontSize: '11px', fontWeight: '700',
                }}>
                  {TIPOS_VINO_F.find(t => t.value === f.tipo_vino)?.label || f.tipo_vino}
                </span>
                <div>
                  <strong style={{ fontSize: '13px' }}>{f.codigo} — {f.nombre}</strong>
                  {f.varietal && <span style={{ fontSize: '12px', color: '#7f8c8d', marginLeft: '8px' }}>· {f.varietal}</span>}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <EstadoBadge activo={f.activa !== false} />
                <span style={{ fontSize: '16px', color: '#bdc3c7' }}>{expanded === f.id ? '▲' : '▼'}</span>
              </div>
            </div>

            {/* Detalle expandible */}
            {expanded === f.id && (
              <div style={{ padding: '0 16px 14px', background: '#fafbff' }}>
                {/* Rangos analíticos */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '10px' }}>
                  {[
                    { label: '🍷 Alcohol', val: f.alcohol_min && f.alcohol_max ? `${f.alcohol_min}–${f.alcohol_max}%` : null },
                    { label: '⚗️ pH',      val: f.ph_min && f.ph_max ? `${f.ph_min}–${f.ph_max}` : null },
                    { label: '🧪 Acid. T', val: f.acidez_total_max ? `≤${f.acidez_total_max} g/L` : null },
                    { label: '🧊 SO₂ L',  val: f.so2_libre_max ? `≤${f.so2_libre_max} mg/L` : null },
                    { label: '🧊 SO₂ T',  val: f.so2_total_max ? `≤${f.so2_total_max} mg/L` : null },
                    { label: '🍯 Az.Res', val: f.azucar_max ? `≤${f.azucar_max} g/L` : null },
                  ].filter(x => x.val).map(x => (
                    <span key={x.label} style={{ background: '#f0f0f0', borderRadius: '5px', padding: '3px 10px', fontSize: '12px', color: '#2c3e50' }}>
                      <strong>{x.label}</strong>: {x.val}
                    </span>
                  ))}
                </div>
                {f.perfil_sensorial && (
                  <p style={{ fontSize: '12px', color: '#7f8c8d', fontStyle: 'italic', margin: '0 0 8px' }}>
                    "{f.perfil_sensorial}"
                  </p>
                )}
                <div style={{ display: 'flex', gap: '8px' }}>
                  <BtnTabla onClick={() => editar(f)} color="#3498db">✏️ Editar</BtnTabla>
                  <BtnTabla onClick={() => toggleActiva(f)} color={f.activa === false ? '#27ae60' : '#e74c3c'}>
                    {f.activa === false ? '↺ Activar' : '⊘ Desactivar'}
                  </BtnTabla>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </ABMLayout>
  )
}

// =============================================================================
// ABM — RECIPIENTES / DEPÓSITOS
// =============================================================================
const TIPOS_RECIPIENTE = [
  { value: 'TA', label: '🔵 Tanque acero inoxidable' },
  { value: 'PC', label: '⬜ Pileta de cemento' },
  { value: 'TR', label: '🟫 Tanque de roble' },
  { value: 'BA', label: '🛢 Barrica' },
  { value: 'TI', label: '🏺 Tinaja / Vasija' },
  { value: 'OT', label: '⬛ Otro' },
]
const ESTADOS_REC = [
  { value: 'LI', label: '🟢 Libre' },
  { value: 'OC', label: '🟡 Ocupado' },
  { value: 'LA', label: '🔵 En lavado' },
  { value: 'MN', label: '🔴 En mantenimiento' },
  { value: 'BA', label: '⚪ De baja' },
]
const TIPO_REC_COLOR = { TA: '#3498db', PC: '#7f8c8d', TR: '#784212', BA: '#8e44ad', TI: '#e67e22', OT: '#95a5a6' }
const ESTADO_REC_COLOR = { LI: '#27ae60', OC: '#e67e22', LA: '#3498db', MN: '#e74c3c', BA: '#bdc3c7' }

function RecipientesABM({ onRefresh }) {
  const emptyForm = { codigo: '', nombre: '', tipo: 'TA', capacidad_litros: '', sector: '', fila: '', posicion: '', estado: 'LI', observaciones: '' }
  const [lista,  setLista]  = useState([])
  const [form,   setForm]   = useState(emptyForm)
  const [msg,    setMsg]    = useState('')
  const [busq,   setBusq]   = useState('')
  const [filTipo,setFilTipo] = useState('')
  const [filEst, setFilEst]  = useState('')

  const cargar = () => api('recipientes/').then(r => setLista(Array.isArray(r?.data) ? r.data : []))
  useEffect(() => { cargar() }, [])

  const setF = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const editar = (r) => setForm({ ...r })

  const guardar = async () => {
    if (!form.codigo || !form.nombre || !form.capacidad_litros)
      return setMsg('❌ Código, nombre y capacidad son obligatorios')
    const r = await api('recipientes/', 'POST', { ...form, activo: true })
    if (r.ok) {
      setMsg(`✅ Recipiente "${form.nombre}" guardado`)
      setForm(emptyForm); cargar(); onRefresh?.()
    } else setMsg('❌ ' + r.msg)
  }

  const cambiarEstado = async (rec, nuevoEstado) => {
    const r = await api('recipientes/', 'POST', { ...rec, estado: nuevoEstado })
    if (r.ok) { setMsg(`✅ ${rec.codigo} → ${ESTADOS_REC.find(e => e.value === nuevoEstado)?.label}`); cargar(); onRefresh?.() }
    else setMsg('❌ ' + r.msg)
  }

  const sectores = [...new Set(lista.map(r => r.sector).filter(Boolean))]

  const filtrados = lista.filter(r => {
    const matchBusq = `${r.codigo} ${r.nombre} ${r.sector || ''}`.toLowerCase().includes(busq.toLowerCase())
    const matchTipo = !filTipo || r.tipo === filTipo
    const matchEst  = !filEst  || r.estado === filEst
    return matchBusq && matchTipo && matchEst
  })

  const totalCapacidad = filtrados.reduce((a, r) => a + (parseFloat(r.capacidad_litros) || 0), 0)

  return (
    <ABMLayout
      titulo="recipiente" editando={!!form.id} msg={msg}
      onNew={() => setForm(emptyForm)} onSubmit={guardar}
      formContent={
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 10px' }}>
            <FInput label="Código *" value={form.codigo} onChange={v => setF('codigo', v)}
              placeholder="T-001" disabled={!!form.id} />
            <FSelect label="Estado" value={form.estado} onChange={v => setF('estado', v)} options={ESTADOS_REC} />
          </div>
          <FInput label="Nombre *" value={form.nombre} onChange={v => setF('nombre', v)} placeholder="Tanque 1 Malbec" />
          <FSelect label="Tipo *" value={form.tipo} onChange={v => setF('tipo', v)} options={TIPOS_RECIPIENTE} />
          <FInput label="Capacidad (L) *" value={form.capacidad_litros} onChange={v => setF('capacidad_litros', v)} type="number" placeholder="50000" />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0 10px' }}>
            <FInput label="Sector / Nave" value={form.sector} onChange={v => setF('sector', v)} placeholder="Nave A" />
            <FInput label="Fila" value={form.fila} onChange={v => setF('fila', v)} type="number" />
            <FInput label="Posición" value={form.posicion} onChange={v => setF('posicion', v)} type="number" />
          </div>
          <FTextarea label="Observaciones" value={form.observaciones} onChange={v => setF('observaciones', v)} />
        </>
      }
    >
      {/* Stats rápidos */}
      <div style={{ display: 'flex', gap: '1px', borderBottom: '2px solid #ecf0f1' }}>
        {[
          { label: 'Total', val: lista.length, color: '#2c3e50' },
          { label: 'Libres', val: lista.filter(r => r.estado === 'LI').length, color: '#27ae60' },
          { label: 'Ocupados', val: lista.filter(r => r.estado === 'OC').length, color: '#e67e22' },
          { label: 'Capacidad total', val: `${(lista.reduce((a, r) => a + (parseFloat(r.capacidad_litros) || 0), 0) / 1000).toFixed(0)} kL`, color: '#3498db' },
        ].map(s => (
          <div key={s.label} style={{ flex: 1, padding: '10px 14px', background: 'white' }}>
            <div style={{ fontSize: '10px', color: '#7f8c8d', fontWeight: '700', textTransform: 'uppercase' }}>{s.label}</div>
            <div style={{ fontSize: '18px', fontWeight: '800', color: s.color }}>{s.val}</div>
          </div>
        ))}
      </div>

      {/* Filtros */}
      <div style={{ padding: '10px 14px', borderBottom: '1px solid #ecf0f1', display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
        <input value={busq} onChange={e => setBusq(e.target.value)} placeholder="Buscar..."
          style={{ padding: '5px 10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '12px', width: '140px' }} />
        <select value={filTipo} onChange={e => setFilTipo(e.target.value)}
          style={{ padding: '5px 10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '12px' }}>
          <option value="">Todos los tipos</option>
          {TIPOS_RECIPIENTE.map(t => <option key={t.value} value={t.value}>{t.label.replace(/\S+\s/, '')}</option>)}
        </select>
        <select value={filEst} onChange={e => setFilEst(e.target.value)}
          style={{ padding: '5px 10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '12px' }}>
          <option value="">Todos los estados</option>
          {ESTADOS_REC.map(e => <option key={e.value} value={e.value}>{e.label.replace(/\S+\s/, '')}</option>)}
        </select>
        {(busq || filTipo || filEst) && (
          <button onClick={() => { setBusq(''); setFilTipo(''); setFilEst('') }}
            style={{ background: 'none', border: '1px solid #ddd', borderRadius: '6px', padding: '4px 10px', cursor: 'pointer', fontSize: '12px', color: '#7f8c8d' }}>
            ✕ Limpiar
          </button>
        )}
        {filtrados.length !== lista.length && (
          <span style={{ fontSize: '12px', color: '#7f8c8d' }}>
            {filtrados.length} de {lista.length} · {(totalCapacidad / 1000).toFixed(0)} kL filtrados
          </span>
        )}
      </div>

      {/* Tabla */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <THead cols={['Código', 'Nombre', 'Tipo', 'Sector', 'Capacidad', 'Estado', 'Acciones']} />
          <tbody>
            {filtrados.length === 0 && <TEmpty cols={7} />}
            {filtrados.map((r, i) => (
              <tr key={r.id} style={{ background: i % 2 === 0 ? 'white' : '#fafafa', borderBottom: '1px solid #f0f0f0' }}>
                <TC bold>
                  <code style={{ background: '#f0f0f0', padding: '2px 7px', borderRadius: '4px', fontSize: '11px' }}>{r.codigo}</code>
                </TC>
                <TC>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '2px', flexShrink: 0,
                      background: TIPO_REC_COLOR[r.tipo] || '#7f8c8d' }} />
                    {r.nombre}
                  </div>
                </TC>
                <TC muted>{TIPOS_RECIPIENTE.find(t => t.value === r.tipo)?.label?.replace(/\S+\s/, '') || r.tipo}</TC>
                <TC muted>{[r.sector, r.fila && `F${r.fila}`, r.posicion && `P${r.posicion}`].filter(Boolean).join(' ') || '—'}</TC>
                <TC right>
                  <strong>{parseFloat(r.capacidad_litros).toLocaleString('es-AR')}</strong>
                  <span style={{ fontSize: '11px', color: '#7f8c8d', marginLeft: '3px' }}>L</span>
                </TC>
                <TC>
                  <span style={{
                    background: ESTADO_REC_COLOR[r.estado] + '22',
                    color: ESTADO_REC_COLOR[r.estado],
                    borderRadius: '20px', padding: '2px 10px', fontSize: '11px', fontWeight: '700',
                  }}>
                    {ESTADOS_REC.find(e => e.value === r.estado)?.label?.replace(/\S+\s/, '') || r.estado}
                  </span>
                </TC>
                <TC>
                  <BtnTabla onClick={() => editar(r)} color="#3498db">✏️ Editar</BtnTabla>
                  {r.estado !== 'LA' && (
                    <BtnTabla onClick={() => cambiarEstado(r, r.estado === 'LI' ? 'MN' : 'LI')} color="#e67e22">
                      {r.estado === 'LI' ? '🔧 Mant.' : '🟢 Liberar'}
                    </BtnTabla>
                  )}
                </TC>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mapa por sector */}
      {sectores.length > 0 && (
        <div style={{ padding: '16px', borderTop: '2px solid #ecf0f1' }}>
          <p style={{ fontSize: '11px', fontWeight: '700', color: '#7f8c8d', textTransform: 'uppercase', letterSpacing: '.5px', margin: '0 0 12px' }}>
            Vista por sector
          </p>
          {sectores.map(sector => (
            <div key={sector} style={{ marginBottom: '14px' }}>
              <p style={{ fontSize: '12px', fontWeight: '700', color: '#2c3e50', margin: '0 0 6px' }}>{sector}</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {lista.filter(r => r.sector === sector).map(r => (
                  <div key={r.id} style={{
                    background: ESTADO_REC_COLOR[r.estado] || '#7f8c8d',
                    color: 'white', borderRadius: '6px', padding: '5px 10px',
                    fontSize: '12px', cursor: 'pointer', minWidth: '70px', textAlign: 'center',
                  }} onClick={() => editar(r)} title={`${r.nombre} — ${r.capacidad_litros.toLocaleString('es-AR')} L`}>
                    <div style={{ fontWeight: '700' }}>{r.codigo}</div>
                    <div style={{ fontSize: '10px', opacity: .85 }}>{(parseFloat(r.capacidad_litros) / 1000).toFixed(0)} kL</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </ABMLayout>
  )
}


// ─────────────────────────────────────────────────────────────────────────────
// ─────────────────────────────────────────────────────────────────────────────
// MÓDULO PRINCIPAL — layout con sidebar lateral (estilo ModuloInformes)
// ─────────────────────────────────────────────────────────────────────────────

const MENU_BODEGA = [
  // ─── Producción ───────────────────────────────────────────────────────────
  { id: 'dashboard',    label: '📊 Dashboard',         grupo: 'Producción' },
  { id: 'vinedo',       label: '🌿 Viñedo',             grupo: 'Producción' },
  { id: 'recepcion',    label: '🏗️ Recepción uva',      grupo: 'Producción' },
  { id: 'elaboracion',  label: '⚗️ Elaboración',        grupo: 'Producción' },
  { id: 'fermentacion', label: '🌡️ Fermentación',       grupo: 'Producción' },
  { id: 'cata',         label: '🍷 Cata & SO₂',         grupo: 'Producción' },
  // ─── Depósito ─────────────────────────────────────────────────────────────
  { id: 'lotes',        label: '🧪 Lotes de granel',    grupo: 'Depósito' },
  { id: 'depositos',    label: '🗄️ Mapa de depósitos',  grupo: 'Depósito' },
  { id: 'barricas',     label: '🛢 Barricas',            grupo: 'Depósito' },
  // ─── Calidad y Terminación ────────────────────────────────────────────────
  { id: 'calidad',      label: '🔬 Calidad',             grupo: 'Calidad' },
  { id: 'embotellado',  label: '🍾 Embotellado',         grupo: 'Calidad' },
  // ─── Gestión ──────────────────────────────────────────────────────────────
  { id: 'costos',       label: '💰 Costos',              grupo: 'Gestión' },
  { id: 'trazabilidad', label: '🔗 Trazabilidad',        grupo: 'Gestión' },
  { id: 'fiscal',       label: '📋 Fiscal / INV',        grupo: 'Gestión' },
  // ─── Configuración ────────────────────────────────────────────────────────
  { id: 'maestros',     label: '⚙️ Maestros',            grupo: 'Configuración' },
]

export default function ModuloBodega() {
  const [tab, setTab]               = useState('dashboard')
  const [varietales, setVarietales] = useState([])
  const [recipientes, setRecipientes] = useState([])
  const [lotes, setLotes]           = useState([])

  useEffect(() => {
    api('varietales/').then(r => setVarietales(Array.isArray(r?.data) ? r.data : []))
    api('recipientes/').then(r => setRecipientes(Array.isArray(r?.data) ? r.data : []))
    api('lotes/').then(r => setLotes(Array.isArray(r?.data) ? r.data : []))
  }, [])

  // Agrupar items del menú por grupo
  const grupos = [...new Set(MENU_BODEGA.map(m => m.grupo))]

  return (
    <div style={{
      display: 'flex', minHeight: '85vh',
      background: 'white', borderRadius: '10px',
      boxShadow: '0 2px 8px rgba(0,0,0,.1)', overflow: 'hidden',
    }}>

      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <div style={{ width: '220px', background: '#2c3e50', color: 'white', flexShrink: 0, display: 'flex', flexDirection: 'column' }}>

        {/* Header del módulo */}
        <div style={{
          padding: '18px 20px', background: '#1a252f',
          borderBottom: '1px solid rgba(255,255,255,.1)',
        }}>
          <div style={{ fontSize: '17px', fontWeight: '800', color: '#f1c40f', letterSpacing: '.3px' }}>
            🍷 Bodega
          </div>
          <div style={{ fontSize: '11px', color: 'rgba(255,255,255,.45)', marginTop: '3px' }}>
            Gestión vitivinícola
          </div>
        </div>

        {/* Items del menú agrupados */}
        <div style={{ overflowY: 'auto', flex: 1, padding: '8px 0' }}>
          {grupos.map(grupo => (
            <div key={grupo}>
              {/* Encabezado de grupo */}
              <div style={{
                padding: '10px 16px 4px',
                fontSize: '10px', fontWeight: '700',
                color: 'rgba(255,255,255,.35)',
                textTransform: 'uppercase', letterSpacing: '1px',
              }}>
                {grupo}
              </div>
              {/* Items del grupo */}
              {MENU_BODEGA.filter(m => m.grupo === grupo).map(item => (
                <button key={item.id} onClick={() => setTab(item.id)} style={{
                  width: '100%', padding: '10px 20px',
                  textAlign: 'left', border: 'none', cursor: 'pointer',
                  background: tab === item.id ? '#34495e' : 'transparent',
                  color:      tab === item.id ? '#2ecc71' : '#ecf0f1',
                  borderLeft: tab === item.id ? '4px solid #2ecc71' : '4px solid transparent',
                  fontSize: '13px',
                  fontWeight: tab === item.id ? '700' : '400',
                  transition: 'all .12s',
                }}>
                  {item.label}
                </button>
              ))}
            </div>
          ))}
        </div>

        {/* Footer sidebar */}
        <div style={{
          padding: '12px 16px',
          borderTop: '1px solid rgba(255,255,255,.08)',
          fontSize: '10px', color: 'rgba(255,255,255,.3)',
        }}>
          {lotes.length} lotes · {varietales.length} varietales
        </div>
      </div>

      {/* ── Contenido ───────────────────────────────────────────────────── */}
      <div style={{ flex: 1, padding: '24px', background: '#f9f9f9', overflowY: 'auto' }}>

        {/* Breadcrumb / título de sección */}
        <div style={{ marginBottom: '20px', borderBottom: '2px solid #ecf0f1', paddingBottom: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <span style={{ fontSize: '11px', color: '#95a5a6', textTransform: 'uppercase', letterSpacing: '.5px' }}>
              {MENU_BODEGA.find(m => m.id === tab)?.grupo}
            </span>
            <h2 style={{ margin: '2px 0 0', fontSize: '18px', color: '#2c3e50', fontWeight: '800' }}>
              {MENU_BODEGA.find(m => m.id === tab)?.label}
            </h2>
          </div>
        </div>

        {/* Render del tab activo */}
        {tab === 'dashboard'    && <DashboardBodega />}
        {tab === 'vinedo'       && <VinedoTab varietales={varietales} />}
        {tab === 'recepcion'    && <RecepcionTab varietales={varietales} />}
        {tab === 'elaboracion'  && <ElaboracionTab lotes={lotes} />}
        {tab === 'fermentacion' && <FermentacionTab lotes={lotes} />}
        {tab === 'cata'         && <CataSO2Tab lotes={lotes} />}
        {tab === 'lotes'        && <LotesTab varietales={varietales} recipientes={recipientes} />}
        {tab === 'depositos'    && <DepositosTab />}
        {tab === 'barricas'     && <BarricasTab lotes={lotes} />}
        {tab === 'calidad'      && <CalidadTab lotes={lotes} varietales={varietales} />}
        {tab === 'embotellado'  && <EmbotelladoTab lotes={lotes} />}
        {tab === 'costos'       && <CostosTab lotes={lotes} />}
        {tab === 'trazabilidad' && <TrazabilidadTab lotes={lotes} />}
        {tab === 'fiscal'       && <FiscalTab lotes={lotes} varietales={varietales} />}
        {tab === 'maestros'     && <MaestrosTab onRefresh={() => {
          api('varietales/').then(r => setVarietales(Array.isArray(r?.data) ? r.data : []))
          api('recipientes/').then(r => setRecipientes(Array.isArray(r?.data) ? r.data : []))
        }} />}
      </div>
    </div>
  )
}