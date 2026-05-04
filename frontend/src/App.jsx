import { useState } from 'react'
import { Routes, Route, useNavigate, Navigate, useLocation } from 'react-router-dom'
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
import ModuloRestaurante  from './ModuloRestaurante'
import FacturacionElectronica from './FacturacionElectronica'
import ModuloImpositivo   from './ModuloImpositivo'

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
  IMPOSITIVO:   '🏛 Informes Impositivos',
}

export default function App() {
  // 1. Inicialización con localStorage para persistir F5
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('pos_user')
    return savedUser ? JSON.parse(savedUser) : null
  })

  const [cajaId, setCajaId] = useState(() => {
    return localStorage.getItem('pos_cajaId') || null
  })

  const navigate = useNavigate()
  const location = useLocation()

  // Mapeamos la URL actual a tu sistema original de VISTA_LABELS
  const routeMap = {
    '/dashboard':    'DASHBOARD',
    '/menu':         'MENU',
    '/ventas':       'VENTAS',
    '/cotizaciones': 'COTIZACIONES',
    '/compras':      'COMPRAS',
    '/stock':        'STOCK',
    '/gestion':      'GESTION',
    '/informes':     'INFORMES',
    '/contabilidad': 'CONTABILIDAD',
    '/kits-promos':  'KITS_PROMOS',
    '/fe':           'FE',
    '/restaurante':  'RESTAURANTE',
    '/impositivo':   'IMPOSITIVO'
  }
  
  // Obtenemos la clave de la vista según la URL, por defecto DASHBOARD
  const vistaActual = routeMap[location.pathname] || 'DASHBOARD'

  const handleLogin = (userData, openCajaId) => {
    setUser(userData)
    localStorage.setItem('pos_user', JSON.stringify(userData))
    
    if (openCajaId) {
      setCajaId(openCajaId)
      localStorage.setItem('pos_cajaId', openCajaId)
    }
    navigate('/dashboard')
  }

  const handleLogout = () => {
    setUser(null)
    setCajaId(null)
    localStorage.removeItem('pos_user')
    localStorage.removeItem('pos_cajaId')
    navigate('/')
  }

  // Nueva función para manejar la apertura/cierre de caja desde los módulos
  const handleAbrirCaja = (id) => {
    setCajaId(id)
    if (id) {
      localStorage.setItem('pos_cajaId', id)
    } else {
      localStorage.removeItem('pos_cajaId') // Si se cierra la caja, lo borramos
    }
  }

  // Función adaptadora para componentes hijos (Dashboard, MenuPrincipal) 
  // que todavía envían textos como 'VENTAS' o 'KITS_PROMOS' en el prop onNavegar
  const manejarNavegacion = (vista) => {
    const ruta = vista.toLowerCase().replace('_', '-')
    navigate(`/${ruta}`)
  }

  // Si no hay usuario logueado, retornamos la pantalla de login directamente
  if (!user) {
    return (
      <div style={{ fontFamily: 'sans-serif', backgroundColor: '#f0f2f5', minHeight: '100vh' }}>
        <LoginScreen onLogin={handleLogin} />
      </div>
    )
  }

  return (
    <div style={{ fontFamily: 'sans-serif', backgroundColor: '#f0f2f5', minHeight: '100vh' }}>

      {/* ── Barra de navegación ────────────────────────────────────────────── */}
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
            onClick={() => navigate('/dashboard')}
            title="Ir al Dashboard"
            style={{ cursor: 'pointer', fontWeight: '800', fontSize: '16px',
              color: '#f39c12', letterSpacing: '1px' }}>
            🏪 POS
          </span>

          <span style={{ color: '#4a6278', fontSize: '16px' }}>│</span>

          {/* Botón Menú Principal — SIEMPRE visible */}
          <button
            onClick={() => navigate('/menu')}
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
              onClick={() => navigate('/dashboard')}
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

      {/* ── Contenido enrutado ──────────────────────────────────────────────── */}
      <div>
        <Routes>
          {/* Redirección por defecto */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          
          <Route path="/dashboard" element={<Dashboard onNavegar={manejarNavegacion} />} />
          <Route path="/menu" element={<MenuPrincipal onNavegar={manejarNavegacion} />} />
          
          <Route path="/ventas" element={
            <div style={{ padding: '20px' }}>
              <ModuloVentas user={user} cajaId={cajaId} onAbrirCaja={handleAbrirCaja} />
            </div>
          } />
          
          <Route path="/cotizaciones" element={
            <div style={{ padding: '20px' }}>
              <ModuloCotizaciones cajaId={cajaId} user={user} />
            </div>
          } />
          
          <Route path="/gestion" element={<ModuloGestion />} />
          
          <Route path="/compras" element={<ModuloCompras />} />
          
          <Route path="/stock" element={
            <div style={{ padding: '20px' }}>
              <ModuloStock />
            </div>
          } />
          
          <Route path="/informes" element={
            <div style={{ padding: '20px' }}>
              <ModuloInformes />
            </div>
          } />
          
          <Route path="/contabilidad" element={<ModuloContabilidad />} />
          
          <Route path="/restaurante" element={<ModuloRestaurante user={user} cajaId={cajaId} />} />
          
          <Route path="/impositivo" element={<ModuloImpositivo />} />
          
          <Route path="/kits-promos" element={
            <div style={{ padding: '20px' }}>
              <ModuloKitsPromos />
            </div>
          } />
          
          <Route path="/fe" element={
            <div style={{ padding: '20px' }}>
              <FacturacionElectronica />
            </div>
          } />

          {/* Manejo de rutas inexistentes (404) */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </div>
  )
}