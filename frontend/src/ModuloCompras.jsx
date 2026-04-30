import { useState } from 'react';
import GestionProveedores          from './GestionProveedores';
import IngresoFacturaCompra        from './IngresoFacturaCompra';
import HistorialCompras            from './HistorialCompras';
import AnulacionCompraComprobantes from './AnulacionCompraComprobantes';
import CtaCteProveedores           from './CtaCteProveedores';
import AsistenteCompras            from './AsistenteCompras';

export default function ModuloCompras({ user, cajaId }) {
  const [sub, setSub] = useState('INGRESO');

  const menu = [
    { id: 'INGRESO',     label: '📦 Ingresar Factura' },
    { id: 'ASISTENTE',   label: '🤖 Cargar desde PDF' },
    { id: 'HISTORIAL',   label: '📋 Historial' },
    { id: 'ANULACION',   label: '🚫 Anulación' },
    { id: 'CTA_CTE',     label: '💸 CTA CTE Proveedores' },
    { id: 'PROVEEDORES', label: '🏢 Proveedores' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '80vh', background: 'white',
      borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', overflow: 'hidden' }}>

      {/* Menú lateral */}
      <div style={{ width: '220px', background: '#8e44ad', color: 'white', flexShrink: 0 }}>
        <div style={{ padding: '18px 20px', background: '#6c3483', fontWeight: '700',
          fontSize: '16px', borderBottom: '1px solid rgba(255,255,255,.15)' }}>
          📦 Módulo Compras
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', padding: '8px 0' }}>
          {menu.map(item => (
            <button key={item.id} onClick={() => setSub(item.id)}
              style={{
                padding: '13px 20px', textAlign: 'left',
                background: sub === item.id
                  ? (item.id === 'ASISTENTE' ? 'rgba(46,204,113,.3)' : 'rgba(255,255,255,.18)')
                  : 'transparent',
                color: 'white', border: 'none',
                borderLeft: sub === item.id ? '4px solid #f39c12' : '4px solid transparent',
                cursor: 'pointer', fontSize: '13px',
                fontWeight: sub === item.id ? '700' : '400',
              }}>
              {item.label}
              {item.id === 'ASISTENTE' && (
                <span style={{
                  marginLeft: '6px', fontSize: '10px', fontWeight: 700,
                  background: '#2ecc71', color: 'white',
                  padding: '1px 6px', borderRadius: '8px',
                }}>IA</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Área de trabajo */}
      <div style={{ flex: 1, padding: '20px', background: '#f9f9f9', overflowY: 'auto' }}>
        {sub === 'INGRESO'     && <IngresoFacturaCompra />}
        {sub === 'ASISTENTE'   && (
          <AsistenteCompras
            user={user}
            cajaId={cajaId}
            onVolver={() => setSub('INGRESO')}
          />
        )}
        {sub === 'HISTORIAL'   && <HistorialCompras />}
        {sub === 'ANULACION'   && <AnulacionCompraComprobantes />}
        {sub === 'CTA_CTE'     && <CtaCteProveedores />}
        {sub === 'PROVEEDORES' && <GestionProveedores />}
      </div>
    </div>
  );
}
