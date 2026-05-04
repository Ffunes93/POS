import { useState } from 'react';
import Facturacion           from './Facturacion';
import AperturaCierreCaja    from './AperturaCierreCaja';
import LibroIVAVentas        from './LibroIVAVentas';
import RentabilidadArticulos from './RentabilidadArticulos';
import AnulacionComprobantes from './AnulacionComprobantes';
import GestionRecibos        from './GestionRecibos';
import ModuloCotizaciones    from './ModuloCotizaciones';

const API = `${import.meta.env.VITE_API_URL}/api`;

// ── Widget de retiro rápido ────────────────────────────────────────────────────
function RetiroCajaWidget({ user, cajaId }) {
  const [importe,  setImporte]  = useState('');
  const [motivo,   setMotivo]   = useState('');
  const [msg,      setMsg]      = useState(null);
  const [cargando, setCargando] = useState(false);

  const registrar = async (e) => {
    e.preventDefault();
    if (!cajaId) return setMsg({ tipo: 'error', texto: 'No hay caja abierta.' });
    if (!importe || parseFloat(importe) <= 0) return setMsg({ tipo: 'error', texto: 'Ingrese un importe válido.' });
    setCargando(true); setMsg(null);
    const r = await fetch(`${API}/RegistrarRetiroCaja/`, {   // ✅ URL CORREGIDA
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cajero_id: user.id, importe: parseFloat(importe), motivo }),
    });
    const d = await r.json();
    if (r.ok && d.status === 'success') {
      setMsg({ tipo: 'ok', texto: `✅ ${d.mensaje}` });
      setImporte(''); setMotivo('');
    } else {
      setMsg({ tipo: 'error', texto: d.mensaje || 'Error.' });
    }
    setCargando(false);
  };

  return (
    <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px',
      padding: '24px', maxWidth: '480px', margin: '20px auto' }}>
      <h3 style={{ marginTop: 0, color: '#24292f' }}>💸 Retiro de Caja</h3>
      {!cajaId && (
        <div style={{ background: '#fff8c5', border: '1px solid #f0c000', borderRadius: '6px',
          padding: '12px', marginBottom: '16px', fontSize: '13px', color: '#735c0f' }}>
          ⚠️ No hay caja abierta.
        </div>
      )}
      {msg && (
        <div style={{ padding: '10px 16px', borderRadius: '6px', marginBottom: '14px', fontSize: '13px', fontWeight: '600',
          background: msg.tipo === 'ok' ? '#dafbe1' : '#ffebe9',
          color:      msg.tipo === 'ok' ? '#116329' : '#a40e26',
          border:     `1px solid ${msg.tipo === 'ok' ? '#56d364' : '#ff818266'}` }}>{msg.texto}</div>
      )}
      <form onSubmit={registrar} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: '#57606a', marginBottom: '4px', textTransform: 'uppercase' }}>
            Importe a retirar ($)
          </label>
          <input autoFocus required type="number" step="0.01" value={importe}
            onChange={e => setImporte(e.target.value)} placeholder="0.00"
            style={{ width: '100%', padding: '10px', border: '2px solid #0969da',
              borderRadius: '5px', fontSize: '20px', textAlign: 'right', boxSizing: 'border-box' }} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: '#57606a', marginBottom: '4px', textTransform: 'uppercase' }}>
            Motivo (opcional)
          </label>
          <input type="text" value={motivo} onChange={e => setMotivo(e.target.value)}
            placeholder="ej: Depósito banco, gastos..."
            style={{ width: '100%', padding: '9px 10px', border: '1px solid #d0d7de',
              borderRadius: '5px', fontSize: '14px', boxSizing: 'border-box' }} />
        </div>
        <button type="submit" disabled={cargando || !cajaId}
          style={{ padding: '12px', background: cajaId ? '#e67e22' : '#ccc', color: '#fff',
            border: 'none', borderRadius: '6px', fontSize: '15px', fontWeight: '700',
            cursor: cajaId ? 'pointer' : 'not-allowed' }}>
          {cargando ? 'Registrando...' : '💸 Registrar Retiro'}
        </button>
      </form>
    </div>
  );
}

// ── Módulo ────────────────────────────────────────────────────────────────────
export default function ModuloVentas({ user, cajaId, onAbrirCaja }) {
  const [submodulo, setSubmodulo] = useState(cajaId ? 'FACTURACION' : 'CAJAS');

  const menuItems = [
    { id: 'FACTURACION',  label: '🧾 Facturación' },
    { id: 'COTIZACIONES', label: '📋 Cotizaciones' },
    { id: 'ANULACION',    label: '🚫 Anulación' },
    { id: 'RECIBOS',      label: '🧾 Recibos de Cobro' },
    { id: 'CAJAS',        label: '💵 Apertura / Cierre' },
    { id: 'RETIRO',       label: '💸 Retiro de Caja' },
    { id: 'LIBRO_IVA',    label: '📘 Libro IVA' },
    { id: 'RENTABILIDAD', label: '📈 Rentabilidad' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '80vh', background: 'white',
      borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', overflow: 'hidden' }}>

      {/* Menú lateral */}
      <div style={{ width: '220px', background: '#2c3e50', color: 'white', flexShrink: 0 }}>
        <div style={{ padding: '18px 20px', background: '#1a252f', fontWeight: '700',
          fontSize: '15px', borderBottom: '1px solid rgba(255,255,255,.1)' }}>
          🛒 Módulo de Ventas
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', padding: '8px 0' }}>
          {menuItems.map(item => (
            <button key={item.id} onClick={() => setSubmodulo(item.id)} style={{
              padding: '12px 20px', textAlign: 'left',
              background: submodulo === item.id ? '#34495e' : 'transparent',
              color: submodulo === item.id ? '#2ecc71' : '#bdc3c7',
              border: 'none',
              borderLeft: submodulo === item.id ? '4px solid #2ecc71' : '4px solid transparent',
              cursor: 'pointer', fontSize: '13px',
              fontWeight: submodulo === item.id ? '700' : '400',
            }}>{item.label}</button>
          ))}
        </div>
      </div>

      {/* Área de trabajo */}
      <div style={{ flex: 1, padding: '20px', background: '#f9f9f9', overflowY: 'auto' }}>

        {submodulo === 'FACTURACION' && !cajaId && (
          <div style={{ background: '#f39c12', color: 'white', padding: '20px',
            borderRadius: '8px', textAlign: 'center' }}>
            <h2>⚠️ Caja Cerrada</h2>
            <p>Debe abrir su caja antes de facturar.</p>
            <button onClick={() => setSubmodulo('CAJAS')} style={{
              padding: '10px 20px', background: '#e67e22', border: 'none',
              color: 'white', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
              Ir a Cajas
            </button>
          </div>
        )}

        {submodulo === 'FACTURACION'  && cajaId  && <Facturacion user={user} cajaId={cajaId} />}
        {submodulo === 'COTIZACIONES'           && <ModuloCotizaciones cajaId={cajaId} user={user} />}
        {submodulo === 'ANULACION'              && <AnulacionComprobantes />}
        {submodulo === 'RECIBOS'                && <GestionRecibos />}
        {submodulo === 'CAJAS'                  && (
          <AperturaCierreCaja
            user={user}
            cajaId={cajaId}
            onCajaCambiada={(nuevoId) => {
              onAbrirCaja(nuevoId);
              if (nuevoId) setSubmodulo('FACTURACION');
            }}
          />
        )}
        {submodulo === 'RETIRO'                 && <RetiroCajaWidget user={user} cajaId={cajaId} />}
        {submodulo === 'LIBRO_IVA'              && <LibroIVAVentas />}
        {submodulo === 'RENTABILIDAD'           && <RentabilidadArticulos />}
      </div>
    </div>
  );
}