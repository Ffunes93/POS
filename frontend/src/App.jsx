import { useState } from 'react'
import LoginScreen from './LoginScreen'
import AperturaScreen from './AperturaScreen'
import PosInterface from './PosInterface'
import ModuloGestion from './ModuloGestion'
import MenuPrincipal from './MenuPrincipal'
import GestionArticulos from './GestionArticulos'
import ModuloCompras from './ModuloCompras'
import ModuloVentas from './ModuloVentas'
import ModuloInformes from './ModuloInformes'
import ModuloStock from './ModuloStock'
import GestionRubros from './GestionRubros'
import ModuloContabilidad from './ModuloContabilidad'

export default function App() {
  const [user, setUser] = useState(null)
  const [cajaId, setCajaId] = useState(null)
  const [vistaActual, setVistaActual] = useState('MENU')

  const handleLogin = (userData, openCajaId) => {
    setUser(userData)
    if (openCajaId) setCajaId(openCajaId)
    setVistaActual('MENU')
  }
  const handleLogout = () => {
    setUser(null); setCajaId(null); setVistaActual('MENU')
  }

  return (
    <div style={{ fontFamily: 'sans-serif', backgroundColor: '#f0f2f5', minHeight: '100vh' }}>
      {user && (
        <div style={{ background: '#2c3e50', color: 'white', padding: '10px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Operador: <b>{user.nombre}</b> | Nivel: {user.nivel}</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            {vistaActual !== 'MENU' && (
              <button onClick={() => setVistaActual('MENU')}
                style={{ cursor: 'pointer', background: '#34495e', color: 'white', border: '1px solid #7f8c8d', padding: '6px 12px', borderRadius: '4px' }}>
                Volver al Menu
              </button>
            )}
            {cajaId && <span style={{ color: '#2ecc71', fontWeight: 'bold' }}>Caja # {cajaId} Abierta</span>}
            <button onClick={handleLogout}
              style={{ cursor: 'pointer', background: '#c0392b', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px' }}>
              Salir
            </button>
          </div>
        </div>
      )}
      {user === null && <LoginScreen onLogin={handleLogin} />}
      {user !== null && (
        <div>
          {vistaActual === 'MENU'         && <MenuPrincipal onNavegar={setVistaActual} />}
          {vistaActual === 'VENTAS'       && <div style={{ padding: '20px' }}><ModuloVentas user={user} cajaId={cajaId} onAbrirCaja={setCajaId} /></div>}
          {vistaActual === 'GESTION'      && <ModuloGestion />}
          {vistaActual === 'COMPRAS'      && <ModuloCompras />}
          {vistaActual === 'STOCK'        && <div style={{ padding: '20px' }}><ModuloStock /></div>}
          {vistaActual === 'INFORMES'     && <div style={{ padding: '20px' }}><ModuloInformes /></div>}
          {vistaActual === 'CONTABILIDAD' && <ModuloContabilidad />}
        </div>
      )}
    </div>
  )
}
