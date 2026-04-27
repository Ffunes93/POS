import { useState } from 'react';
import GestionUsuarios from './GestionUsuarios';
import GestionClientes from './GestionClientes';
import GestionFormasPago from './GestionFormasPago'; 
import ConfigParametros from './ConfigParametros';
import GestionTipocomp from './GestionTipocomp';

export default function ModuloGestion() {
  // Cambiamos 'pestañaActual' por 'submodulo' para mantener el estándar de tu código
  const [submodulo, setSubmodulo] = useState('CLIENTES');

  // Definimos las opciones del menú lateral
  const menuItems = [
    { id: 'CLIENTES',    label: '👥 Clientes' },
    { id: 'USUARIOS',    label: '🔐 Usuarios (Operadores)' },
    { id: 'FORMAS_PAGO', label: '💳 Formas de Pago' },
    { id: 'PARAMETROS',  label: '⚙️ Parámetros' },
    { id: 'TIPOCOMP',    label: '🧾 Comprobantes' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '80vh', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', overflow: 'hidden' }}>

      {/* --- Menú lateral (Estilo azul vibrante) --- */}
      <div style={{ width: '240px', background: '#2980b9', color: 'white', flexShrink: 0 }}>
        
        {/* Cabecera del menú */}
        <div style={{ padding: '18px 20px', background: '#1f618d', fontWeight: '700', fontSize: '16px', borderBottom: '1px solid rgba(255,255,255,.15)' }}>
          ⚙️ Gestión y Ajustes
        </div>
        
        {/* Botones del menú */}
        <div style={{ display: 'flex', flexDirection: 'column', padding: '8px 0' }}>
          {menuItems.map(item => (
            <button 
              key={item.id} 
              onClick={() => setSubmodulo(item.id)} 
              style={{
                padding: '13px 20px', 
                textAlign: 'left',
                background: submodulo === item.id ? 'rgba(255,255,255,.18)' : 'transparent',
                color: 'white', 
                border: 'none',
                borderLeft: submodulo === item.id ? '4px solid #f1c40f' : '4px solid transparent',
                cursor: 'pointer', 
                fontSize: '13px',
                fontWeight: submodulo === item.id ? '700' : '400',
                transition: 'background 0.2s'
              }}
              onMouseOver={(e) => { if (submodulo !== item.id) e.currentTarget.style.backgroundColor = 'rgba(255,255,255,.05)' }}
              onMouseOut={(e) => { if (submodulo !== item.id) e.currentTarget.style.backgroundColor = 'transparent' }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* --- Área de trabajo (Contenido) --- */}
      <div style={{ flex: 1, padding: '20px', background: '#f9f9f9', overflowY: 'auto' }}>
        {submodulo === 'CLIENTES'    && <GestionClientes />}
        {submodulo === 'USUARIOS'    && <GestionUsuarios />}
        {submodulo === 'FORMAS_PAGO' && <GestionFormasPago />} 
        {submodulo === 'PARAMETROS'  && <ConfigParametros />}
        {submodulo === 'TIPOCOMP'    && <GestionTipocomp />} 
      </div>
      
    </div>
  );
}