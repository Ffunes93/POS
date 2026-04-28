import { useState } from 'react';
import GestionUsuarios       from './GestionUsuarios';
import GestionClientes       from './GestionClientes';
import GestionFormasPago     from './GestionFormasPago';
import ConfigParametros      from './ConfigParametros';
import GestionTipocomp       from './GestionTipocomp';
import FacturacionElectronica from './FacturacionElectronica';

export default function ModuloGestion() {
  const [submodulo, setSubmodulo] = useState('CLIENTES');

  const menuItems = [
    { id: 'CLIENTES',    label: '👥 Clientes' },
    { id: 'USUARIOS',    label: '🔐 Usuarios' },
    { id: 'FORMAS_PAGO', label: '💳 Formas de Pago' },
    { id: 'PARAMETROS',  label: '⚙️ Parámetros' },
    { id: 'TIPOCOMP',    label: '🧾 Comprobantes' },
    { id: 'FE',          label: '🏛 Fact. Electrónica' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '80vh', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', overflow: 'hidden' }}>

      <div style={{ width: '240px', background: '#2980b9', color: 'white', flexShrink: 0 }}>
        <div style={{ padding: '18px 20px', background: '#1f618d', fontWeight: '700', fontSize: '16px', borderBottom: '1px solid rgba(255,255,255,.15)' }}>
          ⚙️ Gestión y Ajustes
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', padding: '8px 0' }}>
          {menuItems.map(item => (
            <button
              key={item.id}
              onClick={() => setSubmodulo(item.id)}
              style={{
                padding: '13px 20px', textAlign: 'left',
                background: submodulo === item.id ? 'rgba(255,255,255,.18)' : 'transparent',
                color: 'white', border: 'none',
                borderLeft: submodulo === item.id ? '4px solid #f1c40f' : '4px solid transparent',
                cursor: 'pointer', fontSize: '13px',
                fontWeight: submodulo === item.id ? '700' : '400',
              }}>
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, padding: '20px', background: '#f9f9f9', overflowY: 'auto' }}>
        {submodulo === 'CLIENTES'    && <GestionClientes />}
        {submodulo === 'USUARIOS'    && <GestionUsuarios />}
        {submodulo === 'FORMAS_PAGO' && <GestionFormasPago />}
        {submodulo === 'PARAMETROS'  && <ConfigParametros />}
        {submodulo === 'TIPOCOMP'    && <GestionTipocomp />}
        {submodulo === 'FE'          && <FacturacionElectronica />}
      </div>
    </div>
  );
}