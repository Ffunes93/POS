import { useState } from 'react'
import PlanoMesas   from './PlanoMesas'
import TomarPedido  from './TomarPedido'
import VistaComanda from './VistaComanda'
import CierreMesa   from './CierreMesa'

export default function ModuloRestaurante({ user, cajaId }) {
  const [vista,        setVista]        = useState('plano')
  const [mesaActiva,   setMesaActiva]   = useState(null)   // { id, numero, sector }
  const [pedidoActivo, setPedidoActivo] = useState(null)   // pedido_id (int)

  const irAPedido = (mesa, pedidoId) => {
    setMesaActiva(mesa)
    setPedidoActivo(pedidoId)
    setVista('pedido')
  }

  const irACierre = () => setVista('cierre')

  const irAPlano = () => {
    setVista('plano')
    setMesaActiva(null)
    setPedidoActivo(null)
  }

  const tabs = [
    { key: 'plano',  label: '🗺 Mesas',   onClick: irAPlano },
    { key: 'cocina', label: '👨‍🍳 Cocina', onClick: () => setVista('cocina') },
  ]

  return (
    <div style={{ minHeight: '100vh', background: '#f0f2f5' }}>

      {/* ── Sub-navbar restaurante ──────────────────────────────────────── */}
      <div style={{
        background: '#1a252f', color: 'white',
        padding: '0 20px', height: '44px',
        display: 'flex', alignItems: 'center', gap: '16px',
        borderBottom: '2px solid #f39c12',
      }}>
        <span style={{ fontWeight: 800, color: '#f39c12', fontSize: '15px', letterSpacing: '0.5px' }}>
          🍽 Restaurante
        </span>
        <span style={{ color: '#4a6278' }}>│</span>

        {tabs.map(t => (
          <button key={t.key} onClick={t.onClick} style={{
            background: vista === t.key ? '#2c3e50' : 'transparent',
            color: vista === t.key ? 'white' : '#95a5a6',
            border: `1px solid ${vista === t.key ? '#566573' : 'transparent'}`,
            borderRadius: '4px', padding: '4px 12px',
            cursor: 'pointer', fontSize: '13px', fontWeight: 600,
          }}>{t.label}</button>
        ))}

        {/* Breadcrumb mesa activa */}
        {mesaActiva && vista !== 'plano' && (
          <>
            <span style={{ color: '#4a6278' }}>›</span>
            <span style={{ fontSize: '13px', color: '#f39c12', fontWeight: 600 }}>
              Mesa {mesaActiva.numero} — {mesaActiva.sector}
            </span>
            {vista === 'pedido' && (
              <button onClick={irACierre} style={{
                marginLeft: '8px', padding: '3px 10px',
                background: '#2980b9', color: 'white',
                border: 'none', borderRadius: '4px',
                cursor: 'pointer', fontSize: '12px', fontWeight: 600,
              }}>💵 Cerrar mesa</button>
            )}
          </>
        )}
      </div>

      {/* ── Contenido ──────────────────────────────────────────────────── */}
      <div style={{ padding: '20px' }}>
        {vista === 'plano'  && (
          <PlanoMesas user={user} onAbrirPedido={irAPedido} />
        )}
        {vista === 'pedido' && (
          <TomarPedido
            mesa={mesaActiva}
            pedidoId={pedidoActivo}
            user={user}
            cajaId={cajaId}
            onVolver={irAPlano}
            onPedirCuenta={irACierre}
          />
        )}
        {vista === 'cocina' && (
          <VistaComanda onVolver={irAPlano} />
        )}
        {vista === 'cierre' && (
          <CierreMesa
            mesa={mesaActiva}
            pedidoId={pedidoActivo}
            user={user}
            cajaId={cajaId}
            onFacturado={irAPlano}
            onVolver={() => setVista('pedido')}
          />
        )}
      </div>
    </div>
  )
}