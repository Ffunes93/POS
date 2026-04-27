import { useState, useEffect } from 'react';

const API = 'http://localhost:8001/api';

const fmt = (n) => parseFloat(n || 0).toLocaleString('es-AR', {
  minimumFractionDigits: 2, maximumFractionDigits: 2,
});

function KPICard({ titulo, valor, subtitulo, color, icono, onClick }) {
  return (
    <div
      onClick={onClick}
      style={{
        background: '#fff', border: '1px solid #e1e4e8', borderRadius: '10px',
        padding: '20px 22px', cursor: onClick ? 'pointer' : 'default',
        borderLeft: `4px solid ${color}`,
        transition: 'box-shadow .15s',
        boxShadow: '0 1px 3px rgba(0,0,0,.08)',
      }}
      onMouseOver={e => onClick && (e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,.13)')}
      onMouseOut={e  => onClick && (e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,.08)')}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#57606a',
            textTransform: 'uppercase', letterSpacing: '.5px', marginBottom: '6px' }}>
            {titulo}
          </div>
          <div style={{ fontSize: '26px', fontWeight: '800', color: color }}>
            {valor}
          </div>
          {subtitulo && (
            <div style={{ fontSize: '12px', color: '#8c959f', marginTop: '4px' }}>
              {subtitulo}
            </div>
          )}
        </div>
        <span style={{ fontSize: '32px', opacity: .7 }}>{icono}</span>
      </div>
    </div>
  );
}

function VariacionBadge({ pct }) {
  const subida = pct >= 0;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '3px',
      padding: '2px 8px', borderRadius: '12px', fontSize: '12px', fontWeight: '700',
      background: subida ? '#dafbe1' : '#ffebe9',
      color:      subida ? '#116329' : '#cf222e',
    }}>
      {subida ? '▲' : '▼'} {Math.abs(pct)}% vs ayer
    </span>
  );
}

export default function Dashboard({ onNavegar }) {
  const [datos,   setDatos]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  const cargar = async () => {
    setLoading(true); setError(null);
    try {
      const r = await fetch(`${API}/Dashboard/`);
      const d = await r.json();
      if (d.status === 'success') setDatos(d);
      else setError(d.mensaje);
    } catch (e) {
      setError('Error de conexión con el servidor.');
    }
    setLoading(false);
  };

  useEffect(() => { cargar(); }, []);

  if (loading) return (
    <div style={{ padding: '60px', textAlign: 'center', color: '#57606a', fontSize: '16px' }}>
      ⚙️ Cargando panel de control...
    </div>
  );

  if (error) return (
    <div style={{ padding: '40px' }}>
      <div style={{ background: '#ffebe9', border: '1px solid #ff818266', borderRadius: '8px',
        padding: '16px', color: '#a40e26', marginBottom: '14px' }}>
        ❌ {error}
      </div>
      <button onClick={cargar} style={{ padding: '8px 18px', background: '#0969da', color: '#fff',
        border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: '700' }}>
        Reintentar
      </button>
    </div>
  );

  const { ventas_hoy, ventas_mes, compras_mes, stock, cartera,
          cajas_abiertas, ultimas_ventas, top_articulos, fecha_hoy } = datos;

  return (
    <div style={{ padding: '24px', maxWidth: '1200px' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '22px', fontWeight: '800', color: '#24292f' }}>
            📊 Panel de Control
          </h1>
          <div style={{ fontSize: '13px', color: '#57606a', marginTop: '4px' }}>
            {new Date(fecha_hoy + 'T12:00:00').toLocaleDateString('es-AR', {
              weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
            })}
          </div>
        </div>
        <button onClick={cargar} style={{
          padding: '7px 14px', background: '#f3f4f6', border: '1px solid #d0d7de',
          borderRadius: '6px', cursor: 'pointer', fontSize: '13px', color: '#57606a',
        }}>
          🔄 Actualizar
        </button>
      </div>

      {/* KPIs principales */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '14px', marginBottom: '24px' }}>
        <KPICard
          titulo="Ventas del Día"
          valor={`$${fmt(ventas_hoy.total)}`}
          subtitulo={
            <span>
              {ventas_hoy.cantidad} operaciones &nbsp;
              <VariacionBadge pct={ventas_hoy.variacion_vs_ayer} />
            </span>
          }
          color="#1a7f37"
          icono="💰"
          onClick={() => onNavegar('VENTAS')}
        />
        <KPICard
          titulo="Ventas del Mes"
          valor={`$${fmt(ventas_mes.total)}`}
          subtitulo={`${ventas_mes.cantidad} comprobantes`}
          color="#0969da"
          icono="📈"
          onClick={() => onNavegar('INFORMES')}
        />
        <KPICard
          titulo="Compras del Mes"
          valor={`$${fmt(compras_mes.total)}`}
          subtitulo={`${compras_mes.cantidad} facturas`}
          color="#8250df"
          icono="📦"
          onClick={() => onNavegar('COMPRAS')}
        />
        <KPICard
          titulo="Cartera CTA CTE"
          valor={`$${fmt(cartera.total_deuda)}`}
          subtitulo={`${cartera.cant_clientes} clientes con deuda`}
          color="#e67e22"
          icono="💳"
          onClick={() => onNavegar('VENTAS')}
        />
        <KPICard
          titulo="Stock Crítico"
          valor={stock.sin_stock}
          subtitulo={`${stock.bajo_minimo} bajo mínimo`}
          color={stock.sin_stock > 0 ? '#cf222e' : '#1a7f37'}
          icono="⚠️"
          onClick={() => onNavegar('STOCK')}
        />
        <KPICard
          titulo="Cajas Abiertas"
          valor={cajas_abiertas}
          subtitulo="turnos activos ahora"
          color={cajas_abiertas > 0 ? '#1a7f37' : '#57606a'}
          icono="🏧"
          onClick={() => onNavegar('VENTAS')}
        />
      </div>

      {/* Tablas de detalle */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>

        {/* Últimas ventas */}
        <div style={{ background: '#fff', border: '1px solid #e1e4e8', borderRadius: '10px', overflow: 'hidden' }}>
          <div style={{ padding: '14px 18px', borderBottom: '1px solid #e1e4e8', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: '700', fontSize: '14px', color: '#24292f' }}>
              🧾 Últimas ventas del día
            </span>
            <button onClick={() => onNavegar('VENTAS')} style={{
              fontSize: '12px', color: '#0969da', background: 'none',
              border: 'none', cursor: 'pointer', fontWeight: '600',
            }}>Ver todo →</button>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ background: '#f6f8fa' }}>
                <th style={{ padding: '8px 14px', textAlign: 'left', fontWeight: '700', color: '#57606a' }}>Comprobante</th>
                <th style={{ padding: '8px 14px', textAlign: 'right', fontWeight: '700', color: '#57606a' }}>Total</th>
              </tr>
            </thead>
            <tbody>
              {ultimas_ventas.length === 0 ? (
                <tr><td colSpan={2} style={{ padding: '20px', textAlign: 'center', color: '#8c959f' }}>
                  Sin ventas hoy
                </td></tr>
              ) : ultimas_ventas.map((v, i) => (
                <tr key={i} style={{ borderTop: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '9px 14px' }}>
                    <span style={{ fontWeight: '700', color: '#0969da' }}>
                      {v.cod_comprob}{v.comprobante_letra || ''} {String(v.nro_comprob).padStart(6, '0')}
                    </span>
                    <div style={{ fontSize: '11px', color: '#8c959f' }}>
                      {new Date(v.fecha_fact).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </td>
                  <td style={{ padding: '9px 14px', textAlign: 'right', fontWeight: '700', color: '#1a7f37' }}>
                    ${fmt(v.tot_general)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Top artículos */}
        <div style={{ background: '#fff', border: '1px solid #e1e4e8', borderRadius: '10px', overflow: 'hidden' }}>
          <div style={{ padding: '14px 18px', borderBottom: '1px solid #e1e4e8', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: '700', fontSize: '14px', color: '#24292f' }}>
              🏆 Top artículos hoy
            </span>
            <button onClick={() => onNavegar('INFORMES')} style={{
              fontSize: '12px', color: '#0969da', background: 'none',
              border: 'none', cursor: 'pointer', fontWeight: '600',
            }}>Ver ranking →</button>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ background: '#f6f8fa' }}>
                <th style={{ padding: '8px 14px', textAlign: 'left', fontWeight: '700', color: '#57606a' }}>Artículo</th>
                <th style={{ padding: '8px 14px', textAlign: 'right', fontWeight: '700', color: '#57606a' }}>Cant.</th>
                <th style={{ padding: '8px 14px', textAlign: 'right', fontWeight: '700', color: '#57606a' }}>Total</th>
              </tr>
            </thead>
            <tbody>
              {top_articulos.length === 0 ? (
                <tr><td colSpan={3} style={{ padding: '20px', textAlign: 'center', color: '#8c959f' }}>
                  Sin artículos vendidos hoy
                </td></tr>
              ) : top_articulos.map((a, i) => (
                <tr key={i} style={{ borderTop: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '9px 14px' }}>
                    <span style={{ fontWeight: '600' }}>{a.detalle || a.cod_articulo}</span>
                    <div style={{ fontSize: '11px', color: '#8c959f' }}>{a.cod_articulo}</div>
                  </td>
                  <td style={{ padding: '9px 14px', textAlign: 'right', color: '#0969da', fontWeight: '700' }}>
                    {parseFloat(a.cant_vendida || 0).toFixed(0)}
                  </td>
                  <td style={{ padding: '9px 14px', textAlign: 'right', fontWeight: '700', color: '#1a7f37' }}>
                    ${fmt(a.total_venta)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Accesos rápidos */}
      <div style={{ marginTop: '20px', background: '#f6f8fa', borderRadius: '10px', padding: '16px 20px' }}>
        <div style={{ fontSize: '12px', fontWeight: '700', color: '#57606a',
          textTransform: 'uppercase', letterSpacing: '.5px', marginBottom: '12px' }}>
          Accesos rápidos
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {[
            { label: '🛒 Nueva Venta',     vista: 'VENTAS' },
            { label: '📦 Ingreso Compra',  vista: 'COMPRAS' },
            { label: '💳 Cobrar CTA CTE',  vista: 'VENTAS' },
            { label: '📋 Cotizaciones',    vista: 'COTIZACIONES' },
            { label: '🏢 Stock',           vista: 'STOCK' },
            { label: '📊 Informes',        vista: 'INFORMES' },
            { label: '🏛 Contabilidad',    vista: 'CONTABILIDAD' },
          ].map(({ label, vista }) => (
            <button key={vista + label} onClick={() => onNavegar(vista)} style={{
              padding: '8px 16px', background: '#fff', border: '1px solid #d0d7de',
              borderRadius: '6px', cursor: 'pointer', fontSize: '13px',
              fontWeight: '600', color: '#24292f', transition: 'background .1s',
            }}
              onMouseOver={e => e.currentTarget.style.background = '#f0f9ff'}
              onMouseOut={e  => e.currentTarget.style.background = '#fff'}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}