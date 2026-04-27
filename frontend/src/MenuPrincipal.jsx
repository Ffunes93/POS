export default function MenuPrincipal({ onNavegar }) {
  const cardStyle = {
    padding: '30px', borderRadius: '10px', color: 'white', cursor: 'pointer',
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'center', fontSize: '20px', fontWeight: 'bold',
    boxShadow: '0 4px 6px rgba(0,0,0,0.1)', transition: 'transform 0.2s',
    border: 'none', width: '100%', minHeight: '150px'
  };

  return (
    <div style={{ padding: '40px', maxWidth: '1000px', margin: '0 auto' }}>
      <h2 style={{ color: '#2c3e50', borderBottom: '2px solid #bdc3c7', paddingBottom: '10px', marginBottom: '30px' }}>
        Panel de Control Principal
      </h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
        <button style={{ ...cardStyle, background: '#3498db' }} onClick={() => onNavegar('VENTAS')}>
          <span style={{ fontSize: '40px', marginBottom: '10px' }}>🛒</span>Ventas (POS)
        </button>
        <button style={{ ...cardStyle, background: '#9b59b6' }} onClick={() => onNavegar('COMPRAS')}>
          <span style={{ fontSize: '40px', marginBottom: '10px' }}>📦</span>Compras
        </button>
        <button style={{ ...cardStyle, background: '#2ecc71' }} onClick={() => onNavegar('STOCK')}>
          <span style={{ fontSize: '40px', marginBottom: '10px' }}>🏢</span>Stock y Precios
        </button>
        <button style={{ ...cardStyle, background: '#e67e22' }} onClick={() => onNavegar('GESTION')}>
          <span style={{ fontSize: '40px', marginBottom: '10px' }}>👥</span>Gestión (ABM)
        </button>
        <button style={{ ...cardStyle, background: '#e74c3c' }} onClick={() => onNavegar('INFORMES')}>
          <span style={{ fontSize: '40px', marginBottom: '10px' }}>📊</span>Informes
        </button>
        <button style={{ ...cardStyle, background: '#1e3a5f' }} onClick={() => onNavegar('CONTABILIDAD')}>
          <span style={{ fontSize: '40px', marginBottom: '10px' }}>🏛</span>Contabilidad
        </button>
      </div>
    </div>
  );
}
