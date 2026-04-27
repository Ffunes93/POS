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

  return (
    <div style={{ fontFamily: 'sans-serif', backgroundColor: '#f0f2f5', minHeight: '100vh' }}>

      {/* Barra de navegación */}
      {user && (
        <div style={{
          background: '#2c3e50', color: 'white',
          padding: '10px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span
              style={{ cursor: 'pointer', fontWeight: '800', fontSize: '16px', color: '#f39c12' }}
              onClick={() => setVistaActual('DASHBOARD')}
            >
              🏪 POS
            </span>
            <span style={{ color: '#bdc3c7' }}>|</span>
            <span style={{ color: '#ecf0f1', fontSize: '13px' }}>
              Operador: <b>{user.nombre || user.nombre_login}</b>
              &nbsp;· Nivel {user.nivel}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {vistaActual !== 'DASHBOARD' && vistaActual !== 'MENU' && (
              <button onClick={() => setVistaActual('DASHBOARD')}
                style={{ cursor: 'pointer', background: '#34495e', color: 'white',
                  border: '1px solid #7f8c8d', padding: '6px 12px', borderRadius: '4px', fontSize: '12px' }}>
                🏠 Inicio
              </button>
            )}
            {cajaId
              ? <span style={{ color: '#2ecc71', fontWeight: 'bold', fontSize: '13px' }}>
                  🟢 Caja # {cajaId}
                </span>
              : <span style={{ color: '#e74c3c', fontSize: '13px' }}>🔴 Sin caja</span>
            }
            <button onClick={handleLogout}
              style={{ cursor: 'pointer', background: '#c0392b', color: 'white',
                border: 'none', padding: '6px 12px', borderRadius: '4px', fontSize: '12px' }}>
              Salir
            </button>
          </div>
        </div>
      )}

      {/* Contenido */}
      {user === null && <LoginScreen onLogin={handleLogin} />}

      {user !== null && (
        <div>
          {vistaActual === 'DASHBOARD'     && (
            <Dashboard onNavegar={setVistaActual} />
          )}
          {vistaActual === 'MENU'          && (
            <MenuPrincipal onNavegar={setVistaActual} />
          )}
          {vistaActual === 'VENTAS'        && (
            <div style={{ padding: '20px' }}>
              <ModuloVentas user={user} cajaId={cajaId} onAbrirCaja={setCajaId} />
            </div>
          )}
          {vistaActual === 'COTIZACIONES'  && (
            <div style={{ padding: '20px' }}>
              <ModuloCotizaciones cajaId={cajaId} user={user} />
            </div>
          )}
          {vistaActual === 'GESTION'       && <ModuloGestion />}
          {vistaActual === 'COMPRAS'       && <ModuloCompras />}
          {vistaActual === 'STOCK'         && (
            <div style={{ padding: '20px' }}>
              <ModuloStock />
            </div>
          )}
          {vistaActual === 'INFORMES'      && (
            <div style={{ padding: '20px' }}>
              <ModuloInformes />
            </div>
          )}
          {vistaActual === 'CONTABILIDAD'  && <ModuloContabilidad />}
        </div>
      )}
    </div>
  )
}