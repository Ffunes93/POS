import { useState, useEffect } from 'react'

const API = 'http://localhost:8001'

const ESTADO_CFG = {
  libre:         { bg: '#d5f5e3', border: '#27ae60', text: '#1e8449', etiqueta: '🟢 Libre'        },
  ocupada:       { bg: '#fadbd8', border: '#e74c3c', text: '#922b21', etiqueta: '🔴 Ocupada'      },
  cuenta_pedida: { bg: '#fef9e7', border: '#f39c12', text: '#9a7d0a', etiqueta: '🟡 Cuenta'       },
  reservada:     { bg: '#d6eaf8', border: '#3498db', text: '#1a5276', etiqueta: '🔵 Reservada'    },
}

export default function PlanoMesas({ user, onAbrirPedido }) {
  const [sectores,    setSectores]    = useState([])
  const [sectorId,    setSectorId]    = useState(null)
  const [loading,     setLoading]     = useState(true)
  const [error,       setError]       = useState('')
  const [modal,       setModal]       = useState(null)   // mesa a abrir
  const [comensales,  setComensales]  = useState(2)
  const [mozo,        setMozo]        = useState(user?.nombre || '')
  const [abriendo,    setAbriendo]    = useState(false)

  /* ── Carga plano ─────────────────────────────────────────────────── */
  const cargarPlano = async (silencioso = false) => {
    if (!silencioso) setLoading(true)
    setError('')
    try {
      const r = await fetch(`${API}/api/rest/plano/`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const d = await r.json()
      if (d.status === 'success') {
        setSectores(d.data)
        if (d.data.length > 0 && !sectorId) setSectorId(d.data[0].id)
      }
    } catch (e) {
      setError('No se pudo conectar con el servidor. Verificá que el backend esté corriendo.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    cargarPlano()
    const t = setInterval(() => cargarPlano(true), 30_000)
    return () => clearInterval(t)
  }, [])

  /* ── Abrir mesa ──────────────────────────────────────────────────── */
  const handleMesaClick = (mesa, sectorNombre) => {
    if (mesa.estado === 'libre') {
      setModal({ ...mesa, sectorNombre })
      setMozo(user?.nombre || '')
      setComensales(2)
      return
    }
    // Mesa ocupada/cuenta → ir directamente al pedido activo
    if (mesa.pedido_id) {
      onAbrirPedido({ id: mesa.id, numero: mesa.numero, sector: sectorNombre }, mesa.pedido_id)
    }
  }

  const abrirMesa = async () => {
    if (!modal) return
    setAbriendo(true)
    try {
      const r = await fetch(`${API}/api/rest/abrir_mesa/`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mesa_id:     modal.id,
          mozo_nombre: mozo.trim() || 'Mozo',
          mozo_id:     user?.id || 1,
          comensales:  comensales,
          usuario:     user?.nombre_login || 'admin',
          cod_cli:     1,
        }),
      })
      const d = await r.json()
      if (d.status === 'success') {
        setModal(null)
        onAbrirPedido(
          { id: modal.id, numero: modal.numero, sector: modal.sectorNombre },
          d.pedido_id,
        )
      } else {
        alert(d.mensaje || 'Error al abrir la mesa')
      }
    } catch {
      alert('Error de conexión')
    } finally {
      setAbriendo(false)
    }
  }

  /* ── Render ──────────────────────────────────────────────────────── */
  const sectorActual = sectores.find(s => s.id === sectorId)
  const mesas        = sectorActual?.mesas || []

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '80px 40px', color: '#7f8c8d', fontSize: '15px' }}>
      Cargando plano de mesas...
    </div>
  )

  if (error) return (
    <div style={{
      background: '#fadbd8', border: '1px solid #e74c3c', borderRadius: '10px',
      padding: '20px 24px', color: '#922b21', fontSize: '14px',
    }}>
      {error}
      <button onClick={() => cargarPlano()} style={{
        marginLeft: '16px', padding: '6px 14px', background: '#e74c3c', color: 'white',
        border: 'none', borderRadius: '6px', cursor: 'pointer',
      }}>Reintentar</button>
    </div>
  )

  return (
    <div>
      {/* ── Sector tabs ──────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap', alignItems: 'center' }}>
        {sectores.map(s => (
          <button key={s.id} onClick={() => setSectorId(s.id)} style={{
            padding: '9px 22px', borderRadius: '8px', cursor: 'pointer',
            fontWeight: 700, fontSize: '14px',
            background: sectorId === s.id ? s.color : '#ecf0f1',
            color:      sectorId === s.id ? 'white' : '#555',
            border: `2px solid ${sectorId === s.id ? s.color : '#dce3e8'}`,
            transition: 'all 0.15s',
          }}>
            {s.nombre}
            <span style={{ marginLeft: '6px', fontWeight: 400, fontSize: '12px', opacity: 0.8 }}>
              ({s.mesas?.length || 0})
            </span>
          </button>
        ))}
        <button onClick={() => cargarPlano(true)} style={{
          marginLeft: 'auto', padding: '8px 16px', background: 'white',
          border: '1px solid #dce3e8', borderRadius: '6px', cursor: 'pointer',
          fontSize: '13px', color: '#7f8c8d', fontWeight: 600,
        }}>↻ Actualizar</button>
      </div>

      {/* ── Grilla de mesas ──────────────────────────────────────────── */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))',
        gap: '14px',
      }}>
        {mesas.map(mesa => {
          const cfg = ESTADO_CFG[mesa.estado] || ESTADO_CFG.libre
          return (
            <div
              key={mesa.id}
              onClick={() => handleMesaClick(mesa, sectorActual?.nombre)}
              style={{
                background:  cfg.bg,
                border:      `2.5px solid ${cfg.border}`,
                borderRadius:'14px',
                padding:     '16px',
                cursor:      'pointer',
                transition:  'transform 0.15s, box-shadow 0.15s',
                boxShadow:   '0 2px 6px rgba(0,0,0,0.07)',
                userSelect:  'none',
              }}
              onMouseOver={e => {
                e.currentTarget.style.transform  = 'translateY(-3px)'
                e.currentTarget.style.boxShadow  = '0 8px 20px rgba(0,0,0,0.15)'
              }}
              onMouseOut={e => {
                e.currentTarget.style.transform  = ''
                e.currentTarget.style.boxShadow  = '0 2px 6px rgba(0,0,0,0.07)'
              }}
            >
              {/* Número y capacidad */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <span style={{ fontSize: '28px', fontWeight: '900', color: cfg.text, lineHeight: 1 }}>
                  {mesa.numero}
                </span>
                <span style={{
                  fontSize: '11px', color: cfg.text,
                  background: 'rgba(255,255,255,0.55)',
                  padding: '2px 7px', borderRadius: '10px', fontWeight: 700,
                }}>
                  {mesa.capacidad}p
                </span>
              </div>

              {/* Estado */}
              <div style={{ fontSize: '12px', fontWeight: 700, color: cfg.text, margin: '6px 0 2px' }}>
                {cfg.etiqueta}
              </div>

              {/* Info del pedido activo */}
              {mesa.estado !== 'libre' && (
                <div style={{ marginTop: '6px', borderTop: `1px solid ${cfg.border}40`, paddingTop: '6px' }}>
                  {mesa.mozo_nombre && (
                    <div style={{ fontSize: '12px', color: cfg.text, marginBottom: '3px', fontWeight: 600 }}>
                      👤 {mesa.mozo_nombre}
                    </div>
                  )}
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#666' }}>
                    <span>🍽 {mesa.pedido_items} ítems</span>
                    <span>⏱ {mesa.minutos_abierto}min</span>
                  </div>
                  {mesa.pedido_total > 0 && (
                    <div style={{ fontSize: '15px', fontWeight: 800, color: cfg.text, marginTop: '4px' }}>
                      ${mesa.pedido_total.toFixed(2)}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}

        {mesas.length === 0 && (
          <div style={{
            gridColumn: '1/-1', textAlign: 'center', padding: '60px 40px',
            background: 'white', borderRadius: '12px', color: '#bdc3c7', fontSize: '14px',
          }}>
            No hay mesas configuradas en este sector.
          </div>
        )}
      </div>

      {/* ── Leyenda ──────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: '18px', marginTop: '24px', flexWrap: 'wrap' }}>
        {Object.entries(ESTADO_CFG).map(([k, c]) => (
          <div key={k} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#7f8c8d' }}>
            <div style={{ width: '14px', height: '14px', borderRadius: '4px', background: c.bg, border: `1.5px solid ${c.border}` }}/>
            {c.etiqueta}
          </div>
        ))}
      </div>

      {/* ── Modal: abrir mesa ─────────────────────────────────────────── */}
      {modal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
          <div style={{
            background: 'white', borderRadius: '16px', padding: '28px',
            width: '340px', boxShadow: '0 24px 60px rgba(0,0,0,0.3)',
          }}>
            <h3 style={{ margin: '0 0 20px', color: '#2c3e50', fontSize: '17px' }}>
              Abrir Mesa {modal.numero}
              <span style={{ fontSize: '13px', color: '#7f8c8d', fontWeight: 400, marginLeft: '8px' }}>
                ({modal.sectorNombre})
              </span>
            </h3>

            <label style={{ display: 'block', fontSize: '12px', color: '#7f8c8d', fontWeight: 600, marginBottom: '5px' }}>
              Mozo / camarero
            </label>
            <input
              value={mozo}
              onChange={e => setMozo(e.target.value)}
              placeholder="Nombre del mozo"
              style={{
                width: '100%', padding: '10px 12px', boxSizing: 'border-box',
                border: '1.5px solid #dce3e8', borderRadius: '8px',
                fontSize: '14px', marginBottom: '16px',
              }}
            />

            <label style={{ display: 'block', fontSize: '12px', color: '#7f8c8d', fontWeight: 600, marginBottom: '5px' }}>
              Comensales
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
              <button onClick={() => setComensales(c => Math.max(1, c - 1))}
                style={{ width: '36px', height: '36px', fontSize: '18px', fontWeight: 700,
                  background: '#ecf0f1', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>−</button>
              <span style={{ fontSize: '20px', fontWeight: 700, color: '#2c3e50', minWidth: '32px', textAlign: 'center' }}>
                {comensales}
              </span>
              <button onClick={() => setComensales(c => Math.min(20, c + 1))}
                style={{ width: '36px', height: '36px', fontSize: '18px', fontWeight: 700,
                  background: '#ecf0f1', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>+</button>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={() => setModal(null)} style={{
                flex: 1, padding: '11px', background: '#ecf0f1', border: 'none',
                borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '14px',
              }}>Cancelar</button>
              <button onClick={abrirMesa} disabled={abriendo} style={{
                flex: 2, padding: '11px',
                background: abriendo ? '#95a5a6' : '#27ae60',
                color: 'white', border: 'none', borderRadius: '8px',
                cursor: abriendo ? 'not-allowed' : 'pointer',
                fontWeight: 700, fontSize: '14px',
              }}>
                {abriendo ? 'Abriendo...' : '✓ Abrir Mesa'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}