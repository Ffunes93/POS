import { useState } from 'react'
import LoginScreen        from './LoginScreen'
import MenuPrincipal      from './MenuPrincipal'
import Dashboard          from './Dashboard'
import ModuloGestion      from './ModuloGestion'
import GestionArticulos   from './GestionArticulos'
import ModuloCompras      from './ModuloCompras'
import ModuloVentas       from './ModuloVentas'
import ModuloInformes     from './ModuloInformes'
import ModuloStock        from './ModuloStock'
import GestionRubros      from './GestionRubros'
import ModuloContabilidad from './ModuloContabilidad'
import ModuloCotizaciones from './ModuloCotizaciones'
import ModuloKitsPromos   from './ModuloKitsPromos'
import ModuloRestaurante from './ModuloRestaurante'
import FacturacionElectronica from './FacturacionElectronica'

// Mapa de etiquetas para la barra de título
const VISTA_LABELS = {
  DASHBOARD:    '📊 Dashboard',
  MENU:         '☰ Menú Principal',
  VENTAS:       '🛒 Ventas',
  COTIZACIONES: '📋 Cotizaciones',
  COMPRAS:      '📦 Compras',
  STOCK:        '🏢 Stock',
  GESTION:      '⚙️ Gestión',
  INFORMES:     '📈 Informes',
  CONTABILIDAD: '🏛 Contabilidad',
  KITS_PROMOS:  '🧩 Kits y Promos',
  FE:           '🏛 Fact. Electrónica',
  RESTAURANTE:  '🍽 Restaurante',
}

export default function App() {
  const [user,         setUser]        = useState(null)
  const [cajaId,       setCajaId]      = useState(null)
  const [vistaActual,  setVistaActual] = useState('DASHBOARD')

  const handleLogin = (userData, openCajaId) => {
    setUser(userData)
    if (openCajaId) setCajaId(openCajaId)
    setVistaActual('DASHBOARD')
  }

  const handleLogout = () => {
    setUser(null); setCajaId(null); setVistaActual('DASHBOARD')
  }

  const irA = (vista) => setVistaActual(vista)

  return (
    <div style={{ fontFamily: 'sans-serif', backgroundColor: '#f0f2f5', minHeight: '100vh' }}>

      {/* ── Barra de navegación ────────────────────────────────────────────── */}
      {user && (
        <div style={{
          background: '#2c3e50', color: 'white',
          padding: '0 20px', height: '48px',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          position: 'sticky', top: 0, zIndex: 500,
          boxShadow: '0 2px 8px rgba(0,0,0,.3)',
        }}>
          {/* Izquierda: logo + breadcrumb */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Logo / Dashboard */}
            <span
              onClick={() => irA('DASHBOARD')}
              title="Ir al Dashboard"
              style={{ cursor: 'pointer', fontWeight: '800', fontSize: '16px',
                color: '#f39c12', letterSpacing: '1px' }}>
              🏪 POS
            </span>

            <span style={{ color: '#4a6278', fontSize: '16px' }}>│</span>

            {/* Botón Menú Principal — SIEMPRE visible */}
            <button
              onClick={() => irA('MENU')}
              title="Menú Principal"
              style={{
                background: vistaActual === 'MENU' ? '#34495e' : 'transparent',
                color: 'white', border: '1px solid #4a6278',
                borderRadius: '5px', padding: '5px 12px',
                cursor: 'pointer', fontSize: '13px', fontWeight: '600',
                display: 'flex', alignItems: 'center', gap: '5px',
              }}>
              ☰ Menú
            </button>

            {/* Botón Dashboard */}
            {vistaActual !== 'DASHBOARD' && (
              <button
                onClick={() => irA('DASHBOARD')}
                style={{
                  background: 'transparent', color: '#bdc3c7',
                  border: '1px solid #4a6278', borderRadius: '5px',
                  padding: '5px 12px', cursor: 'pointer', fontSize: '13px',
                }}>
                📊 Dashboard
              </button>
            )}

            {/* Breadcrumb de vista actual */}
            {vistaActual !== 'DASHBOARD' && vistaActual !== 'MENU' && (
              <>
                <span style={{ color: '#4a6278' }}>›</span>
                <span style={{ color: '#ecf0f1', fontSize: '13px', fontWeight: '600' }}>
                  {VISTA_LABELS[vistaActual] || vistaActual}
                </span>
              </>
            )}
          </div>

          {/* Derecha: info usuario + caja + salir */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ color: '#95a5a6', fontSize: '12px' }}>
              <b style={{ color: '#ecf0f1' }}>{user.nombre || user.nombre_login}</b>
              &nbsp;· Nv.{user.nivel}
            </span>
            {cajaId
              ? <span style={{ color: '#2ecc71', fontWeight: '700', fontSize: '12px' }}>
                  🟢 Caja #{cajaId}
                </span>
              : <span style={{ color: '#e74c3c', fontSize: '12px' }}>🔴 Sin caja</span>
            }
            <button
              onClick={handleLogout}
              style={{ background: '#c0392b', color: 'white', border: 'none',
                padding: '5px 12px', borderRadius: '4px', fontSize: '12px',
                cursor: 'pointer', fontWeight: '600' }}>
              Salir
            </button>
          </div>
        </div>
      )}

      {/* ── Contenido ─────────────────────────────────────────────────────── */}
      {user === null && <LoginScreen onLogin={handleLogin} />}

      {user !== null && (
        <div>
          {vistaActual === 'DASHBOARD'    && <Dashboard onNavegar={irA} />}
          {vistaActual === 'MENU'         && <MenuPrincipal onNavegar={irA} />}
          {vistaActual === 'VENTAS'       && (
            <div style={{ padding: '20px' }}>
              <ModuloVentas user={user} cajaId={cajaId} onAbrirCaja={setCajaId} />
            </div>
          )}
          {vistaActual === 'COTIZACIONES' && (
            <div style={{ padding: '20px' }}>
              <ModuloCotizaciones cajaId={cajaId} user={user} />
            </div>
          )}
          {vistaActual === 'GESTION'      && <ModuloGestion />}
          {vistaActual === 'COMPRAS'      && <ModuloCompras />}
          {vistaActual === 'STOCK'        && (
            <div style={{ padding: '20px' }}>
              <ModuloStock />
            </div>
          )}
          {vistaActual === 'INFORMES'     && (
            <div style={{ padding: '20px' }}>
              <ModuloInformes />
            </div>
          )}
          {vistaActual === 'CONTABILIDAD' && <ModuloContabilidad />}
          {vistaActual === 'RESTAURANTE' && <ModuloRestaurante user={user} cajaId={cajaId} />}
          {vistaActual === 'KITS_PROMOS'  && (
            <div style={{ padding: '20px' }}>
              <ModuloKitsPromos />
            </div>
          )}
          {vistaActual === 'FE'           && (
            <div style={{ padding: '20px' }}>
              <FacturacionElectronica />
            </div>
          )}
        </div>
      )}
    </div>
  )
}