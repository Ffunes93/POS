export default function MenuPrincipal({ onNavegar }) {
  const cardStyle = {
    padding: '30px', borderRadius: '10px', color: 'white', cursor: 'pointer',
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'center', fontSize: '18px', fontWeight: 'bold',
    boxShadow: '0 4px 6px rgba(0,0,0,0.1)', transition: 'transform 0.15s, box-shadow 0.15s',
    border: 'none', width: '100%', minHeight: '140px',
  };

  const items = [
    { vista: 'DASHBOARD',    bg: '#1e3a5f', icono: '📊', label: 'Panel de Control' },
    { vista: 'VENTAS',       bg: '#3498db', icono: '🛒', label: 'Ventas (POS)' },
    { vista: 'COTIZACIONES', bg: '#16a085', icono: '📋', label: 'Cotizaciones' },
    { vista: 'COMPRAS',      bg: '#9b59b6', icono: '📦', label: 'Compras' },
    { vista: 'STOCK',        bg: '#2ecc71', icono: '🏢', label: 'Stock y Precios' },
    { vista: 'GESTION',      bg: '#e67e22', icono: '👥', label: 'Gestión (ABM)' },
    { vista: 'INFORMES',     bg: '#e74c3c', icono: '📈', label: 'Informes' },
    { vista: 'CONTABILIDAD', bg: '#1e3a5f', icono: '🏛', label: 'Contabilidad' },
  ];

  return (
    <div style={{ padding: '40px', maxWidth: '1100px', margin: '0 auto' }}>
      <h2 style={{ color: '#2c3e50', borderBottom: '2px solid #bdc3c7',
        paddingBottom: '10px', marginBottom: '30px', fontSize: '20px' }}>
        Panel de Control Principal
      </h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '18px' }}>
        {items.map(({ vista, bg, icono, label }) => (
          <button
            key={vista}
            style={{ ...cardStyle, background: bg }}
            onClick={() => onNavegar(vista)}
            onMouseOver={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.2)'; }}
            onMouseOut={e  => { e.currentTarget.style.transform = 'none';              e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)'; }}
          >
            <span style={{ fontSize: '38px', marginBottom: '10px' }}>{icono}</span>
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}