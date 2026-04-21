import { useState } from 'react';
import GestionUsuarios from './GestionUsuarios';
import GestionClientes from './GestionClientes';
import GestionFormasPago from './GestionFormasPago'; // <-- Importar el nuevo

export default function ModuloGestion() {
  const [pestañaActual, setPestañaActual] = useState('CLIENTES');

  const tabStyle = (activa) => ({
    padding: '10px 20px',
    cursor: 'pointer',
    background: activa ? '#34495e' : '#ecf0f1',
    color: activa ? 'white' : '#2c3e50',
    border: 'none',
    borderRadius: '5px 5px 0 0',
    fontWeight: 'bold',
    fontSize: '16px',
    marginRight: '5px'
  });

  return (
    <div>
      <div style={{ display: 'flex', borderBottom: '3px solid #34495e', marginBottom: '20px' }}>
        <button style={tabStyle(pestañaActual === 'CLIENTES')} onClick={() => setPestañaActual('CLIENTES')}>
          👥 Clientes
        </button>
        <button style={tabStyle(pestañaActual === 'USUARIOS')} onClick={() => setPestañaActual('USUARIOS')}>
          🔐 Usuarios (Operadores)
        </button>
        {/* NUEVA PESTAÑA */}
        <button style={tabStyle(pestañaActual === 'FORMAS_PAGO')} onClick={() => setPestañaActual('FORMAS_PAGO')}>
          💳 Formas de Pago
        </button>
      </div>

      {pestañaActual === 'CLIENTES' && <GestionClientes />}
      {pestañaActual === 'USUARIOS' && <GestionUsuarios />}
      {pestañaActual === 'FORMAS_PAGO' && <GestionFormasPago />} {/* NUEVO RENDER */}
    </div>
  );
}