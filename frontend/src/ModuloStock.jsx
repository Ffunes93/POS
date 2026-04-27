import { useState } from 'react';
import GestionArticulos from './GestionArticulos';
import GestionRubros    from './GestionRubros';
import MovimientosStock from './MovimientosStock';

export default function ModuloStock() {
  const [submodulo, setSubmodulo] = useState('ARTICULOS');

  const menuItems = [
    { id: 'ARTICULOS',   label: '📦 ABM de Artículos' },
    { id: 'RUBROS',      label: '🗂️ Rubros y Subrubros' },
    { id: 'MOVIMIENTOS', label: '🔄 Movimientos de Stock' },  // NUEVO
    { id: 'LISTAS_PRECIOS', label: '📋 Listas de Precios' },
    { id: 'PROMOCIONES',    label: '⭐ Promociones' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '80vh', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', overflow: 'hidden' }}>

      {/* Menú lateral */}
      <div style={{ width: '240px', background: '#27ae60', color: 'white', flexShrink: 0 }}>
        <div style={{ padding: '18px 20px', background: '#1e8449', fontWeight: '700', fontSize: '16px', borderBottom: '1px solid rgba(255,255,255,.15)' }}>
          🏢 Stock y Catálogos
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', padding: '8px 0' }}>
          {menuItems.map(item => (
            <button key={item.id} onClick={() => setSubmodulo(item.id)} style={{
              padding: '13px 20px', textAlign: 'left',
              background: submodulo === item.id ? 'rgba(255,255,255,.18)' : 'transparent',
              color: 'white', border: 'none',
              borderLeft: submodulo === item.id ? '4px solid #f39c12' : '4px solid transparent',
              cursor: 'pointer', fontSize: '13px',
              fontWeight: submodulo === item.id ? '700' : '400',
            }}>{item.label}</button>
          ))}
        </div>
      </div>

      {/* Área de trabajo */}
      <div style={{ flex: 1, padding: '20px', background: '#f9f9f9', overflowY: 'auto' }}>
        {submodulo === 'ARTICULOS'   && <GestionArticulos />}
        {submodulo === 'RUBROS'      && <GestionRubros />}
        {submodulo === 'MOVIMIENTOS' && <MovimientosStock />}
        {['LISTAS_PRECIOS', 'PROMOCIONES'].includes(submodulo) && (
          <div style={{ padding: '60px', textAlign: 'center', color: '#7f8c8d' }}>
            <h2 style={{ fontSize: '40px', margin: '0 0 10px 0' }}>🚧</h2>
            <h3>Submódulo en construcción</h3>
            <p>{menuItems.find(m => m.id === submodulo)?.label}</p>
          </div>
        )}
      </div>
    </div>
  );
}