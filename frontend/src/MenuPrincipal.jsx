export default function MenuPrincipal({ onNavegar }) {
  const cardStyle = {
    padding: '28px 20px',
    borderRadius: '10px',
    color: 'white',
    cursor: 'pointer',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '15px',
    fontWeight: 'bold',
    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
    transition: 'transform 0.15s, box-shadow 0.15s',
    border: 'none',
    width: '100%',
    minHeight: '130px',
    gap: '10px',
  };

  const items = [
    { vista: 'DASHBOARD',    bg: '#1e3a5f', icono: '📊', label: 'Panel de Control' },
    { vista: 'VENTAS',       bg: '#2980b9', icono: '🛒', label: 'Ventas (POS)' },
    { vista: 'COTIZACIONES', bg: '#16a085', icono: '📋', label: 'Cotizaciones' },
    { vista: 'COMPRAS',      bg: '#8e44ad', icono: '📦', label: 'Compras' },
    { vista: 'STOCK',        bg: '#27ae60', icono: '🏢', label: 'Stock y Precios' },
    { vista: 'KITS_PROMOS',  bg: '#d35400', icono: '🧩', label: 'Kits y Promociones' },
    { vista: 'GESTION',      bg: '#e67e22', icono: '⚙️', label: 'Gestión (ABM)' },
    { vista: 'INFORMES',     bg: '#c0392b', icono: '📈', label: 'Informes' },
    { vista: 'CONTABILIDAD', bg: '#2c3e50', icono: '🏛', label: 'Contabilidad' },
    { vista: 'FE',           bg: '#6c3483', icono: '🧾', label: 'Fact. Electrónica' },
    { vista: 'RESTAURANTE',  bg: '#16a085', icono: '🍽', label: 'Restaurante' },
  ];

  return (
    <div style={{ padding: '32px 40px', maxWidth: '1100px', margin: '0 auto' }}>
      <div style={{ marginBottom: '28px' }}>
        <h2 style={{ color: '#2c3e50', margin: '0 0 6px 0', fontSize: '22px', fontWeight: '800' }}>
          ☰ Menú Principal
        </h2>
        <p style={{ color: '#7f8c8d', margin: 0, fontSize: '14px' }}>
          Seleccioná el módulo al que querés acceder
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
        {items.map(({ vista, bg, icono, label }) => (
          <button
            key={vista}
            style={{ ...cardStyle, background: bg }}
            onClick={() => onNavegar(vista)}
            onMouseOver={e => {
              e.currentTarget.style.transform = 'translateY(-3px)';
              e.currentTarget.style.boxShadow = '0 8px 20px rgba(0,0,0,0.2)';
            }}
            onMouseOut={e => {
              e.currentTarget.style.transform = 'none';
              e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
            }}
          >
            <span style={{ fontSize: '36px' }}>{icono}</span>
            <span>{label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}