import { useState } from 'react';
import GestionArticulos from './GestionArticulos';
import GestionRubros from './GestionRubros'

export default function ModuloStock() {
  const [submodulo, setSubmodulo] = useState('ARTICULOS');

  // Menú basado en las tablas y rutas de tu sistema legacy
  const menuItems = [
    { id: 'ARTICULOS', label: '📦 ABM de Artículos' },
    { id: 'RUBROS', label: '🗂️ Rubros y Subrubros' },
    { id: 'LISTAS_PRECIOS', label: '📋 Listas de Precios' },
    { id: 'PROMOCIONES', label: '⭐ Promociones y Descuentos' },
    { id: 'KITS', label: '🎁 Combos y Kits' },
    { id: 'ACTUALIZADOR', label: '🔄 Actualización Masiva' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '80vh', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', overflow: 'hidden' }}>
      
      {/* MENÚ LATERAL */}
      <div style={{ width: '260px', background: '#27ae60', color: 'white', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '20px', background: '#2ecc71', fontWeight: 'bold', fontSize: '18px', borderBottom: '1px solid #27ae60' }}>
          🏢 Stock y Catálogos
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', padding: '10px 0' }}>
          {menuItems.map(item => (
            <button
              key={item.id}
              onClick={() => setSubmodulo(item.id)}
              style={{
                padding: '15px 20px', textAlign: 'left', background: submodulo === item.id ? '#2196f3' : 'transparent',
                color: 'white', border: 'none', borderLeft: submodulo === item.id ? '4px solid #fff' : '4px solid transparent',
                cursor: 'pointer', fontSize: '14px', transition: 'all 0.2s', fontWeight: submodulo === item.id ? 'bold' : 'normal'
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* ÁREA DE TRABAJO (DERECHA) */}
      <div style={{ flex: 1, padding: '20px', background: '#f9f9f9', overflowY: 'auto' }}>
        
        {/* Renderizamos el componente que ya teníamos hecho */}
        {submodulo === 'ARTICULOS' && <GestionArticulos />}
        {submodulo === 'RUBROS' && <GestionRubros />}
        
        {/* Placeholders para los nuevos submódulos */}
        {submodulo !== 'ARTICULOS' && (
          <div style={{ padding: '60px', textAlign: 'center', color: '#7f8c8d' }}>
            <h2 style={{ fontSize: '40px', margin: '0 0 10px 0' }}>🚧</h2>
            <h3>Submódulo en construcción</h3>
            <p>Acá construiremos la pantalla para gestionar <b>{menuItems.find(m => m.id === submodulo).label}</b>.</p>
          </div>
        )}
        

      </div>
    </div>
  );
}