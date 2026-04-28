import { useState, useEffect, useCallback } from 'react'

const API = 'http://localhost:8001'

const urgencia = (min) => {
  if (min >= 20) return { color: '#e74c3c', label: 'Urgente' }
  if (min >= 10) return { color: '#e67e22', label: 'Demorado' }
  return { color: '#27ae60', label: 'A tiempo' }
}

export default function VistaComanda({ onVolver }) {
  const [grupos,      setGrupos]      = useState([])
  const [loading,     setLoading]     = useState(true)
  const [actualizando,setActualizando]= useState(false)
  const [ultimaAct,   setUltimaAct]   = useState(null)
  const [filtro,      setFiltro]      = useState('todos')  // 'todos' | 'enviado' | 'en_preparacion'

  const cargar = useCallback(async (silencioso = false) => {
    if (!silencioso) setActualizando(true)
    try {
      const r = await fetch(`${API}/api/rest/comandas/`)
      const d = await r.json()
      if (d.status === 'success') {
        setGrupos(d.data)
        setUltimaAct(new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }))
      }
    } catch (e) {
      console.error('Error cargando comandas', e)
    } finally {
      setLoading(false)
      setActualizando(false)
    }
  }, [])

  useEffect(() => {
    cargar()
    const t = setInterval(() => cargar(true), 20_000)
    return () => clearInterval(t)
  }, [cargar])

  const marcarItem = async (itemId, estado) => {
    try {
      await fetch(`${API}/api/rest/marcar_listo/`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId, estado }),
      })
      cargar(true)
    } catch {}
  }

  const marcarPedidoListo = async (pedidoId) => {
    try {
      await fetch(`${API}/api/rest/marcar_listo_pedido/`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pedido_id: pedidoId }),
      })
      cargar(true)
    } catch {}
  }

  /* ── Filtrado local ──────────────────────────────────────────────── */
  const gruposFiltrados = grupos.map(g => ({
    ...g,
    items: filtro === 'todos' ? g.items : g.items.filter(i => i.estado_item === filtro),
  })).filter(g => g.items.length > 0)

  const totalPendientes = grupos.reduce((acc, g) => acc + g.items.length, 0)

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '80px', color: '#7f8c8d' }}>
      Cargando comandas...
    </div>
  )

  return (
    <div>
      {/* ── Barra de control ─────────────────────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '12px',
        marginBottom: '20px', flexWrap: 'wrap',
      }}>
        <div>
          <h3 style={{ margin: '0 0 2px', color: '#2c3e50', fontSize: '17px' }}>
            👨‍🍳 Vista Cocina
            {totalPendientes > 0 && (
              <span style={{
                marginLeft: '8px', background: '#e74c3c', color: 'white',
                borderRadius: '12px', padding: '2px 9px', fontSize: '12px', fontWeight: 700,
              }}>{totalPendientes}</span>
            )}
          </h3>
          {ultimaAct && (
            <div style={{ fontSize: '12px', color: '#7f8c8d' }}>
              {actualizando ? '↻ Actualizando...' : `Actualizado: ${ultimaAct}`}
            </div>
          )}
        </div>

        {/* Filtros */}
        <div style={{ display: 'flex', gap: '6px', marginLeft: 'auto' }}>
          {[
            { key: 'todos',          label: 'Todos' },
            { key: 'enviado',        label: 'Recibidos' },
            { key: 'en_preparacion', label: 'En prep.' },
          ].map(f => (
            <button key={f.key} onClick={() => setFiltro(f.key)} style={{
              padding: '6px 14px', borderRadius: '6px', cursor: 'pointer',
              fontSize: '12px', fontWeight: 600, border: 'none',
              background: filtro === f.key ? '#2c3e50' : '#ecf0f1',
              color:      filtro === f.key ? 'white'  : '#555',
            }}>{f.label}</button>
          ))}
          <button onClick={() => cargar()} style={{
            padding: '6px 14px', background: '#3498db', color: 'white',
            border: 'none', borderRadius: '6px', cursor: 'pointer',
            fontSize: '12px', fontWeight: 700,
          }}>↻</button>
          <button onClick={onVolver} style={{
            padding: '6px 14px', background: '#ecf0f1', color: '#7f8c8d',
            border: '1px solid #dce3e8', borderRadius: '6px', cursor: 'pointer', fontSize: '12px',
          }}>← Plano</button>
        </div>
      </div>

      {/* ── Sin pedidos ──────────────────────────────────────────────── */}
      {gruposFiltrados.length === 0 && (
        <div style={{
          textAlign: 'center', padding: '80px 40px', background: 'white',
          borderRadius: '14px', color: '#7f8c8d',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}>
          <div style={{ fontSize: '52px', marginBottom: '12px' }}>✅</div>
          <div style={{ fontWeight: 700, fontSize: '17px', color: '#2c3e50' }}>
            {filtro === 'todos' ? 'Todo al día' : 'Sin pedidos con ese estado'}
          </div>
          <div style={{ fontSize: '13px', marginTop: '6px' }}>
            No hay ítems pendientes en cocina
          </div>
        </div>
      )}

      {/* ── Tarjetas por pedido ──────────────────────────────────────── */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: '16px',
        alignItems: 'start',
      }}>
        {gruposFiltrados.map(g => {
          const urg = urgencia(g.minutos)
          return (
            <div key={g.pedido_id} style={{
              background: 'white', borderRadius: '14px', overflow: 'hidden',
              boxShadow: '0 2px 10px rgba(0,0,0,0.08)',
              border: `2px solid ${urg.color}30`,
            }}>
              {/* Header mesa */}
              <div style={{
                background: urg.color, color: 'white', padding: '12px 16px',
                display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
              }}>
                <div>
                  <div style={{ fontWeight: 800, fontSize: '20px', lineHeight: 1 }}>
                    Mesa {g.mesa_numero}
                  </div>
                  <div style={{ fontSize: '12px', opacity: 0.9, marginTop: '2px' }}>
                    {g.mesa_sector} · Pedido #{g.pedido_id}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{
                    background: 'rgba(255,255,255,0.25)', borderRadius: '8px',
                    padding: '4px 10px', fontSize: '13px', fontWeight: 700,
                  }}>⏱ {g.minutos} min</div>
                  <div style={{ fontSize: '12px', opacity: 0.85, marginTop: '4px' }}>
                    👤 {g.mozo || '—'}
                  </div>
                </div>
              </div>

              {/* Ítems */}
              <div style={{ padding: '12px' }}>
                {g.items.map(it => (
                  <div key={it.id} style={{
                    display: 'flex', alignItems: 'flex-start', gap: '10px',
                    padding: '10px', marginBottom: '8px', borderRadius: '8px',
                    background: it.estado_item === 'en_preparacion' ? '#fdf2e9' : '#f8f9fa',
                    borderLeft: `4px solid ${it.estado_item === 'en_preparacion' ? '#e67e22' : '#3498db'}`,
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, fontSize: '14px', color: '#2c3e50' }}>
                        <span style={{ color: '#7f8c8d', marginRight: '4px' }}>{it.cantidad}×</span>
                        {it.nombre_art}
                      </div>
                      {it.observac && (
                        <div style={{ fontSize: '12px', color: '#e67e22', fontStyle: 'italic', marginTop: '2px' }}>
                          ✏ {it.observac}
                        </div>
                      )}
                      <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                        <span style={{ fontSize: '11px', color: '#7f8c8d' }}>#{it.nro_comanda}</span>
                        <span style={{
                          fontSize: '11px', fontWeight: 600, padding: '1px 6px', borderRadius: '8px',
                          background: it.estado_item === 'en_preparacion' ? '#fde8d8' : '#e8f4fd',
                          color:      it.estado_item === 'en_preparacion' ? '#e67e22' : '#3498db',
                        }}>
                          {it.estado_item === 'en_preparacion' ? 'En preparación' : 'Recibido'}
                        </span>
                      </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {it.estado_item === 'enviado' && (
                        <button onClick={() => marcarItem(it.id, 'en_preparacion')} style={{
                          padding: '5px 10px', background: '#e67e22', color: 'white',
                          border: 'none', borderRadius: '5px', cursor: 'pointer',
                          fontSize: '11px', fontWeight: 700, whiteSpace: 'nowrap',
                        }}>🔥 Prep.</button>
                      )}
                      <button onClick={() => marcarItem(it.id, 'listo')} style={{
                        padding: '5px 10px', background: '#27ae60', color: 'white',
                        border: 'none', borderRadius: '5px', cursor: 'pointer',
                        fontSize: '11px', fontWeight: 700,
                      }}>✓ Listo</button>
                    </div>
                  </div>
                ))}

                {/* Botón "todo listo" */}
                <button onClick={() => marcarPedidoListo(g.pedido_id)} style={{
                  width: '100%', marginTop: '4px', padding: '9px',
                  background: '#2c3e50', color: 'white',
                  border: 'none', borderRadius: '8px', cursor: 'pointer',
                  fontWeight: 700, fontSize: '13px',
                }}>✓ Todo listo — Mesa {g.mesa_numero}</button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}