import { useState } from 'react';
import GestionUsuarios from './GestionUsuarios';
import GestionClientes from './GestionClientes';
import GestionFormasPago from './GestionFormasPago'; 
import ConfigParametros from './ConfigParametros';
import GestionTipocomp from './GestionTipocomp'; // <-- Importado correctamente


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
        <button style={tabStyle(pestañaActual === 'FORMAS_PAGO')} onClick={() => setPestañaActual('FORMAS_PAGO')}>
          💳 Formas de Pago
        </button>
        {/* 👇 NUEVA PESTAÑA AGREGADA */}
        <button style={tabStyle(pestañaActual === 'PARAMETROS')} onClick={() => setPestañaActual('PARAMETROS')}>
          ⚙️ Parámetros
        </button>
        <button style={tabStyle(pestañaActual === 'TIPOCOMP')} onClick={() => setPestañaActual('TIPOCOMP')}>
          🧾 Comprobantes
        </button>
      </div>

      {pestañaActual === 'CLIENTES' && <GestionClientes />}
      {pestañaActual === 'USUARIOS' && <GestionUsuarios />}
      {pestañaActual === 'FORMAS_PAGO' && <GestionFormasPago />} 
      {pestañaActual === 'PARAMETROS' && <ConfigParametros />}
      {pestañaActual === 'TIPOCOMP' && <GestionTipocomp />} 
    </div>
  );
}