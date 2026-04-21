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
import GestionRubros from './GestionRubros';

export default function App() {
  const [user, setUser] = useState(null)
  const [cajaId, setCajaId] = useState(null)
  
  // ESTADO CENTRAL DE RUTEO: Arranca en LOGIN (null), luego pasa a MENU
  const [vistaActual, setVistaActual] = useState('MENU') 

  const handleLogin = (userData, openCajaId) => {
    setUser(userData);
    if (openCajaId) {
      setCajaId(openCajaId);
    }
    setVistaActual('MENU'); // Al loguear, aterriza en el Menú Principal
  }

  const handleLogout = () => {
    setUser(null)
    setCajaId(null)
    setVistaActual('MENU')
  }

  return (
    <div style={{ fontFamily: 'sans-serif', backgroundColor: '#f0f2f5', minHeight: '100vh' }}>
      
      {/* BARRA SUPERIOR DE ESTADO */}
      {user && (
        <div style={{ background: '#2c3e50', color: 'white', padding: '10px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>👤 Operador: <b>{user.nombre}</b> | Nivel: {user.nivel}</span>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            {/* BOTÓN "VOLVER AL MENÚ" (Se oculta si ya estamos en el menú) */}
            {vistaActual !== 'MENU' && (
              <button 
                onClick={() => setVistaActual('MENU')} 
                style={{ cursor: 'pointer', background: '#34495e', color: 'white', border: '1px solid #7f8c8d', padding: '6px 12px', borderRadius: '4px' }}>
                🏠 Volver al Menú
              </button>
            )}

            {cajaId && <span style={{ color: '#2ecc71', fontWeight: 'bold' }}>🟢 Caja # {cajaId} Abierta</span>}
            
            <button onClick={handleLogout} style={{ cursor: 'pointer', background: '#c0392b', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px' }}>
              Salir
            </button>
          </div>
        </div>
      )}

      {/* =========================================
                   MÁQUINA DE ESTADOS (RUTEO)
          ========================================= */}
      
      {/* 0. LOGIN */}
      {!user && <LoginScreen onLogin={handleLogin} />}

      {user && (
        <div>
          {/* 1. MENÚ PRINCIPAL */}
          {vistaActual === 'MENU' && <MenuPrincipal onNavegar={setVistaActual} />}

          {/* 2. MÓDULO DE VENTAS (Movimientos) */}
          {vistaActual === 'VENTAS' && (
            <div style={{ padding: '20px' }}>
              <ModuloVentas user={user} cajaId={cajaId} onAbrirCaja={setCajaId} />
            </div>
          )}

          {/* 3. MÓDULO DE GESTIÓN (ABM Usuarios, etc) */}
          {vistaActual === 'GESTION' && <ModuloGestion />}

          {/* 4. MÓDULO DE COMPRAS */}
          {vistaActual === 'COMPRAS' && <ModuloCompras />}

          {/* 5. MÓDULO DE STOCK (Artículos) */}
          {vistaActual === 'STOCK' && (
             <div style={{ padding: '20px' }}>
               <ModuloStock />
             </div>
          )}

          {/* 6. MÓDULO DE INFORMES */}
          {vistaActual === 'INFORMES' && (
             <div style={{ padding: '20px' }}>
               <ModuloInformes />
             </div>
          )}
        </div>
      )}
      
    </div>
  )
}
