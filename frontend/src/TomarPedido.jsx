import { useState, useEffect, useCallback } from 'react'

const API = 'http://localhost:8001'

const ITEM_BG = {
  pendiente:      '#fff',
  enviado:        '#fef9e7',
  en_preparacion: '#fdf2e9',
  listo:          '#eafaf1',
  entregado:      '#f8f9fa',
  cancelado:      '#f8f9fa',
}

export default function TomarPedido({ mesa, pedidoId, user, cajaId, onVolver, onPedirCuenta }) {
  const [carta,       setCarta]       = useState([])
  const [pedido,      setPedido]      = useState(null)
  const [rubroActivo, setRubroActivo] = useState(null)
  const [busqueda,    setBusqueda]    = useState('')
  const [loading,     setLoading]     = useState(true)
  const [enviando,    setEnviando]    = useState(false)
  const [toast,       setToast]       = useState({ msg: '', tipo: 'ok' })
  const [obsModal,    setObsModal]    = useState(null)   // articulo para obs
  const [obs,         setObs]         = useState('')

  /* ── Fetch ───────────────────────────────────────────────────────── */
  const cargar = useCallback(async () => {
    try {
      const [rCarta, rPedido] = await Promise.all([
        fetch(`${API}/api/rest/carta_menu/`),
        fetch(`${API}/api/rest/pedido/${pedidoId}/`),
      ])
      const [dCarta, dPedido] = await Promise.all([rCarta.json(), rPedido.json()])
      if (dCarta.status === 'success') {
        setCarta(dCarta.data)
        if (!rubroActivo && dCarta.data.length > 0)
          setRubroActivo(dCarta.data[0].rubro_cod)
      }
      if (dPedido.status === 'success') setPedido(dPedido.data)
    } catch (e) {
      mostrarToast('Error al cargar datos', 'error')
    } finally {
      setLoading(false)
    }
  }, [pedidoId])

  useEffect(() => { cargar() }, [cargar])

  const mostrarToast = (msg, tipo = 'ok') => {
    setToast({ msg, tipo })
    setTimeout(() => setToast({ msg: '', tipo: 'ok' }), 3000)
  }

  /* ── Acciones pedido ────────────────────────────────────────────── */
  const agregarItem = async (art, observac = '') => {
    try {
      const r = await fetch(`${API}/api/rest/agregar_item/`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pedido_id: pedidoId,
          cod_art:   art.cod_art,
          cantidad:  1,
          observac:  observac.trim(),
          usuario:   user?.nombre_login || 'admin',
        }),
      })
      const d = await r.json()
      if (d.status === 'success') {
        mostrarToast(`✓ ${art.nombre} agregado`)
        cargar()
      } else {
        mostrarToast(d.mensaje || 'Error al agregar', 'error')
      }
    } catch {
      mostrarToast('Error de conexión', 'error')
    }
  }

  const quitarItem = async (itemId) => {
    try {
      await fetch(`${API}/api/rest/quitar_item/`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId }),
      })
      cargar()
    } catch {}
  }

  const enviarCocina = async () => {
    setEnviando(true)
    try {
      const r = await fetch(`${API}/api/rest/enviar_cocina/`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pedido_id: pedidoId, usuario: user?.nombre_login || 'admin' }),
      })
      const d = await r.json()
      mostrarToast(d.status === 'success' ? d.mensaje : (d.mensaje || 'Error'), d.status === 'success' ? 'ok' : 'error')
      if (d.status === 'success') cargar()
    } catch {
      mostrarToast('Error de conexión', 'error')
    } finally {
      setEnviando(false)
    }
  }

  const pedirCuenta = async () => {
    try {
      const r = await fetch(`${API}/api/rest/pedir_cuenta/`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pedido_id: pedidoId }),
      })
      const d = await r.json()
      if (d.status === 'success') onPedirCuenta()
      else mostrarToast(d.mensaje || 'Error', 'error')
    } catch {
      mostrarToast('Error de conexión', 'error')
    }
  }

  /* ── Filtrado carta ─────────────────────────────────────────────── */
  const artsFiltrados = (() => {
    const rubro = carta.find(r => r.rubro_cod === rubroActivo)
    if (!rubro) return []
    if (!busqueda.trim()) return rubro.articulos
    const q = busqueda.toLowerCase()
    return rubro.articulos.filter(a =>
      a.nombre.toLowerCase().includes(q) || a.cod_art.toLowerCase().includes(q)
    )
  })()

  const items        = pedido?.items?.filter(i => i.estado_item !== 'cancelado') || []
  const pendientes   = items.filter(i => i.estado_item === 'pendiente').length
  const total        = parseFloat(pedido?.total || 0)

  /* ── Estilos compartidos ─────────────────────────────────────────── */
  const card = {
    background: 'white', borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
    padding: '16px',
  }

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '80px', color: '#7f8c8d' }}>
      Cargando pedido...
    </div>
  )

  return (
    <div style={{ display: 'flex', gap: '16px', height: 'calc(100vh - 148px)', overflow: 'hidden' }}>

      {/* ══════════════════ PANEL IZQUIERDO — CARTA ══════════════════ */}
      <div style={{ ...card, flex: '0 0 56%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* Buscador */}
        <input
          placeholder="🔍 Buscar artículo o código..."
          value={busqueda}
          onChange={e => setBusqueda(e.target.value)}
          style={{
            padding: '10px 14px', border: '1.5px solid #dce3e8', borderRadius: '8px',
            fontSize: '14px', marginBottom: '12px', outline: 'none',
            transition: 'border-color 0.15s',
          }}
          onFocus={e  => e.target.style.borderColor = '#3498db'}
          onBlur={e   => e.target.style.borderColor = '#dce3e8'}
        />

        {/* Rubros */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '12px' }}>
          {carta.map(r => (
            <button
              key={r.rubro_cod}
              onClick={() => { setRubroActivo(r.rubro_cod); setBusqueda('') }}
              style={{
                padding: '5px 14px', borderRadius: '20px',
                fontSize: '12px', fontWeight: 700, cursor: 'pointer', border: 'none',
                background: rubroActivo === r.rubro_cod ? '#2c3e50' : '#ecf0f1',
                color:      rubroActivo === r.rubro_cod ? 'white' : '#555',
                transition: 'all 0.15s',
              }}
            >{r.rubro_nom}</button>
          ))}
        </div>

        {/* Grilla de artículos */}
        <div style={{
          flex: 1, overflowY: 'auto',
          display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(148px, 1fr))', gap: '10px',
        }}>
          {artsFiltrados.map(art => (
            <div key={art.cod_art} style={{
              border: '1.5px solid #eaecee', borderRadius: '10px', padding: '12px',
              display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
              transition: 'border-color 0.15s',
            }}
            onMouseOver={e => e.currentTarget.style.borderColor = '#3498db'}
            onMouseOut={e  => e.currentTarget.style.borderColor = '#eaecee'}
            >
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: '#2c3e50', lineHeight: 1.3, marginBottom: '3px' }}>
                  {art.nombre}
                </div>
                <div style={{ fontSize: '11px', color: '#95a5a6' }}>{art.cod_art}</div>
                <div style={{ fontSize: '13px', fontWeight: 700, color: '#27ae60', marginTop: '4px' }}>
                  ${parseFloat(art.precio_1 || 0).toFixed(2)}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '5px', marginTop: '10px' }}>
                <button
                  onClick={() => agregarItem(art)}
                  style={{
                    flex: 1, padding: '7px', background: '#27ae60', color: 'white',
                    border: 'none', borderRadius: '7px', cursor: 'pointer',
                    fontWeight: 800, fontSize: '17px', lineHeight: 1,
                  }}>+</button>
                <button
                  onClick={() => { setObsModal(art); setObs('') }}
                  title="Agregar con observación"
                  style={{
                    padding: '7px 9px', background: '#ecf0f1', color: '#7f8c8d',
                    border: 'none', borderRadius: '7px', cursor: 'pointer', fontSize: '12px',
                  }}>✏</button>
              </div>
            </div>
          ))}

          {artsFiltrados.length === 0 && (
            <div style={{
              gridColumn: '1/-1', textAlign: 'center', padding: '50px 20px',
              color: '#bdc3c7', fontSize: '13px',
            }}>
              {busqueda ? `Sin resultados para "${busqueda}"` : 'Sin artículos en esta categoría'}
            </div>
          )}
        </div>
      </div>

      {/* ══════════════════ PANEL DERECHO — CARRITO ══════════════════ */}
      <div style={{ ...card, flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* Header mesa */}
        <div style={{ borderBottom: '1px solid #eaecee', paddingBottom: '12px', marginBottom: '12px' }}>
          <div style={{ fontWeight: 700, fontSize: '15px', color: '#2c3e50' }}>
            Mesa {mesa?.numero}
            <span style={{ marginLeft: '8px', fontWeight: 400, color: '#7f8c8d', fontSize: '13px' }}>
              — {pedido?.mozo_nombre || 'sin mozo'}
            </span>
          </div>
          <div style={{ fontSize: '12px', color: '#95a5a6', marginTop: '2px' }}>
            {pedido?.comensales} comensal(es) · desde {pedido?.fecha_apertura}
          </div>
        </div>

        {/* Lista ítems */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {items.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '50px 20px', color: '#bdc3c7', fontSize: '13px' }}>
              Sin ítems todavía.<br/>Agregá desde la carta →
            </div>
          ) : items.map(it => (
            <div key={it.id} style={{
              display: 'flex', alignItems: 'flex-start', gap: '8px',
              padding: '8px 6px', borderBottom: '1px solid #f2f3f4',
              background: ITEM_BG[it.estado_item] || '#fff',
              borderRadius: '4px', marginBottom: '2px',
            }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '13px', fontWeight: 600, color: '#2c3e50' }}>
                  <span style={{ color: '#7f8c8d', marginRight: '4px' }}>{it.cantidad}×</span>
                  {it.nombre_art}
                </div>
                {it.observac && (
                  <div style={{ fontSize: '11px', color: '#e67e22', fontStyle: 'italic', marginTop: '1px' }}>
                    ✏ {it.observac}
                  </div>
                )}
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '2px' }}>
                  <span style={{
                    fontSize: '10px', fontWeight: 600, padding: '1px 6px', borderRadius: '8px',
                    background: it.estado_item === 'pendiente' ? '#eaecee'
                      : it.estado_item === 'listo'   ? '#d5f5e3' : '#fef9e7',
                    color: it.estado_item === 'listo' ? '#1e8449' : '#7f8c8d',
                  }}>
                    {it.estado_item}
                  </span>
                  <span style={{ fontSize: '12px', color: '#7f8c8d' }}>
                    ${parseFloat(it.subtotal).toFixed(2)}
                  </span>
                </div>
              </div>
              {it.estado_item === 'pendiente' && (
                <button onClick={() => quitarItem(it.id)} style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: '#e74c3c', fontSize: '15px', padding: '4px', lineHeight: 1,
                }}>✕</button>
              )}
            </div>
          ))}
        </div>

        {/* Total y acciones */}
        <div style={{ borderTop: '2px solid #eaecee', marginTop: '8px', paddingTop: '12px' }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
            fontWeight: 800, fontSize: '20px', color: '#2c3e50', marginBottom: '12px',
          }}>
            <span>Total</span>
            <span>${total.toFixed(2)}</span>
          </div>

          {/* Toast */}
          {toast.msg && (
            <div style={{
              padding: '9px 12px', borderRadius: '7px', fontSize: '13px', marginBottom: '10px',
              background: toast.tipo === 'ok' ? '#d5f5e3' : '#fadbd8',
              border: `1px solid ${toast.tipo === 'ok' ? '#27ae60' : '#e74c3c'}`,
              color:   toast.tipo === 'ok' ? '#1e8449' : '#922b21',
            }}>{toast.msg}</div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {pendientes > 0 && (
              <button onClick={enviarCocina} disabled={enviando} style={{
                padding: '12px 16px', background: enviando ? '#95a5a6' : '#e67e22',
                color: 'white', border: 'none', borderRadius: '8px',
                cursor: enviando ? 'not-allowed' : 'pointer', fontWeight: 700, fontSize: '14px',
              }}>
                {enviando ? 'Enviando...' : `📤 Enviar a Cocina (${pendientes} ítem${pendientes > 1 ? 's' : ''})`}
              </button>
            )}
            <button onClick={pedirCuenta} style={{
              padding: '12px', background: '#2980b9', color: 'white',
              border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 700, fontSize: '14px',
            }}>💵 Pedir Cuenta</button>
            <button onClick={onVolver} style={{
              padding: '10px', background: 'white', color: '#7f8c8d',
              border: '1px solid #dce3e8', borderRadius: '8px', cursor: 'pointer', fontSize: '13px',
            }}>← Volver al plano</button>
          </div>
        </div>
      </div>

      {/* ── Modal observación ────────────────────────────────────────── */}
      {obsModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
          <div style={{
            background: 'white', borderRadius: '14px', padding: '24px',
            width: '320px', boxShadow: '0 24px 50px rgba(0,0,0,0.2)',
          }}>
            <h4 style={{ margin: '0 0 4px', color: '#2c3e50' }}>{obsModal.nombre}</h4>
            <div style={{ fontSize: '13px', color: '#7f8c8d', marginBottom: '14px' }}>
              ${parseFloat(obsModal.precio_1 || 0).toFixed(2)}
            </div>
            <label style={{ fontSize: '12px', color: '#7f8c8d', fontWeight: 600 }}>
              Observación (opcional)
            </label>
            <input
              autoFocus
              value={obs}
              onChange={e => setObs(e.target.value)}
              placeholder="ej: sin sal, punto jugoso..."
              onKeyDown={e => { if (e.key === 'Enter') { agregarItem(obsModal, obs); setObsModal(null) } }}
              style={{
                width: '100%', padding: '9px 12px', boxSizing: 'border-box',
                border: '1.5px solid #dce3e8', borderRadius: '8px',
                fontSize: '14px', margin: '6px 0 16px',
              }}
            />
            <div style={{ display: 'flex', gap: '8px' }}>
              <button onClick={() => setObsModal(null)} style={{
                flex: 1, padding: '9px', background: '#ecf0f1', border: 'none',
                borderRadius: '7px', cursor: 'pointer', fontWeight: 600,
              }}>Cancelar</button>
              <button onClick={() => { agregarItem(obsModal, obs); setObsModal(null) }} style={{
                flex: 2, padding: '9px', background: '#27ae60', color: 'white',
                border: 'none', borderRadius: '7px', cursor: 'pointer', fontWeight: 700,
              }}>+ Agregar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}