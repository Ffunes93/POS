import { useState } from 'react';
import GestionProveedores from './GestionProveedores';

export default function ModuloCompras() {
  const [pestañaActual, setPestañaActual] = useState('PROVEEDORES');

  const tabStyle = (activa) => ({
    padding: '10px 20px',
    cursor: 'pointer',
    background: activa ? '#8e44ad' : '#ecf0f1',
    color: activa ? 'white' : '#2c3e50',
    border: 'none',
    borderRadius: '5px 5px 0 0',
    fontWeight: 'bold',
    fontSize: '16px',
    marginRight: '5px'
  });

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', borderBottom: '3px solid #8e44ad', marginBottom: '20px' }}>
        <button style={tabStyle(pestañaActual === 'PROVEEDORES')} onClick={() => setPestañaActual('PROVEEDORES')}>
          🏢 Catálogo de Proveedores
        </button>
        <button 
          style={{ ...tabStyle(false), color: '#bdc3c7', cursor: 'not-allowed' }} 
          title="Próximamente"
        >
          🧾 Carga de Facturas / Remitos (Pronto)
        </button>
      </div>

      {pestañaActual === 'PROVEEDORES' && <GestionProveedores />}
    </div>
  );
}