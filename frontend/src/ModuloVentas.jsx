import { useState } from 'react';
import Facturacion from './Facturacion';
import AperturaCierreCaja from './AperturaCierreCaja'; // <-- Acá importamos la pantalla que creamos recién
import LibroIVAVentas from './LibroIVAVentas';
import RentabilidadArticulos from './RentabilidadArticulos';

export default function ModuloVentas({ user, cajaId, onAbrirCaja }) {
  // Por defecto arranca en Facturación si hay caja, sino en Cajas
  const [submodulo, setSubmodulo] = useState(cajaId ? 'FACTURACION' : 'CAJAS');

  const menuItems = [
    { id: 'FACTURACION', label: '🧾 Facturación (Emisión)' },
    { id: 'LOTES', label: '📦 Facturación Lotes' },
    { id: 'ANULACION', label: '🚫 Anulación de comprobantes' },
    { id: 'PRESUPUESTOS', label: '📝 Presupuestos' },
    { id: 'CAJAS', label: '💵 Apertura y Cierre de Caja' },
    { id: 'CONSULTA_COMP', label: '🔍 Consulta de Comprobantes' },
    { id: 'CONSULTA_CAJAS', label: '🏦 Consulta de Cajas' },
    { id: 'LIBRO_IVA', label: '📘 Libro IVA Ventas' },
    { id: 'RENTABILIDAD', label: '📈 Consulta de Rentabilidad' },
    { id: 'PRECIOS', label: '🏷️ Actualizador de Precios' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '80vh', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', overflow: 'hidden' }}>
      
      {/* MENÚ LATERAL */}
      <div style={{ width: '260px', background: '#2c3e50', color: 'white', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '20px', background: '#1a252f', fontWeight: 'bold', fontSize: '18px' }}>
          🛒 Módulo de Ventas
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', padding: '10px 0' }}>
          {menuItems.map(item => (
            <button
              key={item.id}
              onClick={() => setSubmodulo(item.id)}
              style={{
                padding: '15px 20px', textAlign: 'left', background: submodulo === item.id ? '#34495e' : 'transparent',
                color: submodulo === item.id ? '#2ecc71' : '#bdc3c7', border: 'none', borderLeft: submodulo === item.id ? '4px solid #2ecc71' : '4px solid transparent',
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
        
        {/* Lógica de bloqueo: Si quiere facturar pero no hay caja */}
        {submodulo === 'FACTURACION' && !cajaId && (
          <div style={{ background: '#f39c12', color: 'white', padding: '20px', borderRadius: '8px', textAlign: 'center' }}>
            <h2>⚠️ Caja Cerrada</h2>
            <p>Debe abrir su caja en el submódulo "Apertura y Cierre de Caja" antes de facturar.</p>
            <button onClick={() => setSubmodulo('CAJAS')} style={{ padding: '10px 20px', background: '#e67e22', border: 'none', color: 'white', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>Ir a Cajas</button>
          </div>
        )}

        {/* RUTEO INTERNO */}
        {submodulo === 'FACTURACION' && cajaId && <Facturacion user={user} cajaId={cajaId} />}
        
        {/* Acá cargamos la pantalla de Apertura / Cierre */}
        {submodulo === 'CAJAS' && (
          <AperturaCierreCaja 
            user={user} 
            cajaId={cajaId} 
            onCajaCambiada={(nuevoId) => {
              onAbrirCaja(nuevoId); // Actualiza el estado global en App.jsx
              if (nuevoId) setSubmodulo('FACTURACION'); // Si abre caja, lo mandamos a facturar automáticamente
            }} 
          />
        )}

        {/* 👇 ACÁ AGREGAMOS EL LIBRO IVA */}
        {submodulo === 'LIBRO_IVA' && <LibroIVAVentas />}

        {submodulo === 'RENTABILIDAD' && <RentabilidadArticulos />}
        
        {/* Placeholders para el resto */}
        {['LOTES', 'ANULACION', 'PRESUPUESTOS', 'CONSULTA_COMP', 'CONSULTA_CAJAS', 'RENTABILIDAD', 'PRECIOS'].includes(submodulo) && (
          <div style={{ padding: '40px', textAlign: 'center', color: '#7f8c8d' }}>
            <h2>⚙️ Submódulo en construcción</h2>
            <p>Esta sección se conectará próximamente con la base de datos.</p>
          </div>
        )}

      </div>
    </div>
  );
}