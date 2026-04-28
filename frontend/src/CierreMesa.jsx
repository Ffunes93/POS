import { useState, useEffect } from 'react'

const API = 'http://localhost:8001'

const TIPOS_COMPROB = [
  { cod: 'EB', label: 'Ticket B' },
  { cod: 'EA', label: 'Ticket A' },
  { cod: 'EC', label: 'Ticket C (Cons. Final)' },
  { cod: 'FB', label: 'Factura B' },
  { cod: 'FA', label: 'Factura A' },
]

const MEDIOS_PAGO = [
  { cod: 'EFE', label: '💵 Efectivo'     },
  { cod: 'TDB', label: '💳 Débito'       },
  { cod: 'TDC', label: '💳 Crédito'      },
  { cod: 'TRF', label: '🏦 Transferencia'},
  { cod: 'MP',  label: '📱 Mercado Pago' },
]

export default function CierreMesa({ mesa, pedidoId, user, cajaId, onFacturado, onVolver }) {
  const [pedido,       setPedido]       = useState(null)
  const [loading,      setLoading]      = useState(true)
  const [tipoComprob,  setTipoComprob]  = useState('EB')
  const [medioPago,    setMedioPago]    = useState('EFE')
  const [codCli,       setCodCli]       = useState(1)
  const [facturando,   setFacturando]   = useState(false)
  const [resultado,    setResultado]    = useState(null)  // { ok, movim, nro_comprob, msg }
  const [confirmar,    setConfirmar]    = useState(false)

  /* ── Carga pedido ────────────────────────────────────────────────── */
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API}/api/rest/pedido/${pedidoId}/`)
        const d = await r.json()
        if (d.status === 'success') setPedido(d.data)
      } catch {}
      setLoading(false)
    })()
  }, [pedidoId])

  /* ── Facturar ────────────────────────────────────────────────────── */
  const facturar = async () => {
    setFacturando(true)
    setResultado(null)
    try {
      const r = await fetch(`${API}/api/rest/facturar_mesa/`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pedido_id:   pedidoId,
          tipo_comprob: tipoComprob,
          cajero:      user?.id      || 1,
          nro_caja:    cajaId        || 1,
          usuario:     user?.nombre_login || 'admin',
          medio_pago:  medioPago,
          cod_cli:     codCli,
          pto_venta:   '0001',
        }),
      })
      const d = await r.json()
      setResultado({
        ok:         d.status === 'success',
        movim:      d.movim,
        nro_comprob:d.nro_comprob,
        msg:        d.mensaje || (d.status === 'success' ? 'Facturado correctamente' : 'Error al facturar'),
      })
      if (d.status === 'success') {
        setTimeout(() => onFacturado(), 2800)
      }
    } catch (e) {
      setResultado({ ok: false, msg: 'Error de conexión con el servidor.' })
    } finally {
      setFacturando(false)
      setConfirmar(false)
    }
  }

  /* ── Helpers ─────────────────────────────────────────────────────── */
  const items   = pedido?.items?.filter(i => i.estado_item !== 'cancelado') || []
  const total   = parseFloat(pedido?.total || 0)
  const tipoLbl = TIPOS_COMPROB.find(t => t.cod === tipoComprob)?.label || ''
  const pagoLbl = MEDIOS_PAGO  .find(p => p.cod === medioPago )?.label || ''

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '80px', color: '#7f8c8d' }}>
      Cargando resumen...
    </div>
  )

  /* ── Resultado final ─────────────────────────────────────────────── */
  if (resultado?.ok) return (
    <div style={{
      maxWidth: '480px', margin: '60px auto',
      background: 'white', borderRadius: '18px', padding: '40px',
      boxShadow: '0 8px 30px rgba(0,0,0,0.10)', textAlign: 'center',
    }}>
      <div style={{ fontSize: '56px', marginBottom: '16px' }}>✅</div>
      <h2 style={{ margin: '0 0 8px', color: '#27ae60', fontSize: '22px' }}>¡Facturado!</h2>
      <p style={{ color: '#7f8c8d', margin: '0 0 24px', fontSize: '14px' }}>{resultado.msg}</p>
      <div style={{ background: '#eafaf1', borderRadius: '10px', padding: '16px', marginBottom: '24px' }}>
        <div style={{ fontSize: '15px', fontWeight: 700, color: '#1e8449', marginBottom: '6px' }}>
          Venta #{resultado.movim} · {tipoLbl}
        </div>
        {resultado.nro_comprob && (
          <div style={{ fontSize: '13px', color: '#7f8c8d' }}>
            Comprobante Nº {resultado.nro_comprob}
          </div>
        )}
        <div style={{ fontSize: '20px', fontWeight: 800, color: '#2c3e50', marginTop: '8px' }}>
          ${total.toFixed(2)} · {pagoLbl}
        </div>
      </div>
      <div style={{ fontSize: '13px', color: '#95a5a6' }}>Volviendo al plano...</div>
    </div>
  )

  return (
    <div style={{ maxWidth: '680px', margin: '0 auto' }}>

      {/* ── Header ────────────────────────────────────────────────────── */}
      <div style={{
        background: 'white', borderRadius: '14px', padding: '20px 24px',
        marginBottom: '16px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div>
          <h2 style={{ margin: '0 0 4px', color: '#2c3e50', fontSize: '20px' }}>
            💵 Cerrar Mesa {mesa?.numero}
          </h2>
          <div style={{ fontSize: '13px', color: '#7f8c8d' }}>
            {pedido?.mozo_nombre} · {pedido?.comensales} comensal(es) · desde {pedido?.fecha_apertura}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '28px', fontWeight: 900, color: '#2c3e50' }}>
            ${total.toFixed(2)}
          </div>
          <div style={{ fontSize: '12px', color: '#7f8c8d' }}>Total a cobrar</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '16px', alignItems: 'start' }}>

        {/* ── Detalle de consumición ────────────────────────────────── */}
        <div style={{
          background: 'white', borderRadius: '14px', padding: '20px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}>
          <h3 style={{ margin: '0 0 14px', fontSize: '14px', color: '#7f8c8d', fontWeight: 600,
            textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Detalle del consumo
          </h3>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #eaecee' }}>
                <th style={{ textAlign: 'left', padding: '6px 4px', color: '#7f8c8d', fontWeight: 600 }}>Artículo</th>
                <th style={{ textAlign: 'center', padding: '6px 4px', color: '#7f8c8d', fontWeight: 600 }}>Cant.</th>
                <th style={{ textAlign: 'right', padding: '6px 4px', color: '#7f8c8d', fontWeight: 600 }}>Precio</th>
                <th style={{ textAlign: 'right', padding: '6px 4px', color: '#7f8c8d', fontWeight: 600 }}>Subtotal</th>
              </tr>
            </thead>
            <tbody>
              {items.map(it => (
                <tr key={it.id} style={{ borderBottom: '1px solid #f2f3f4' }}>
                  <td style={{ padding: '8px 4px', color: '#2c3e50', fontWeight: 500 }}>
                    {it.nombre_art}
                    {it.observac && (
                      <span style={{ fontSize: '11px', color: '#e67e22', display: 'block', fontStyle: 'italic' }}>
                        ✏ {it.observac}
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '8px 4px', textAlign: 'center', color: '#7f8c8d' }}>
                    {parseFloat(it.cantidad)}
                  </td>
                  <td style={{ padding: '8px 4px', textAlign: 'right', color: '#7f8c8d' }}>
                    ${parseFloat(it.precio_unit).toFixed(2)}
                  </td>
                  <td style={{ padding: '8px 4px', textAlign: 'right', fontWeight: 700, color: '#2c3e50' }}>
                    ${parseFloat(it.subtotal).toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr style={{ borderTop: '2px solid #2c3e50' }}>
                <td colSpan="3" style={{ padding: '10px 4px', fontWeight: 700, fontSize: '15px', color: '#2c3e50' }}>
                  TOTAL
                </td>
                <td style={{ padding: '10px 4px', textAlign: 'right', fontWeight: 900, fontSize: '18px', color: '#2c3e50' }}>
                  ${total.toFixed(2)}
                </td>
              </tr>
            </tfoot>
          </table>

          {items.length === 0 && (
            <div style={{ textAlign: 'center', padding: '30px', color: '#bdc3c7', fontSize: '13px' }}>
              Sin ítems en el pedido
            </div>
          )}
        </div>

        {/* ── Panel de cobro ────────────────────────────────────────── */}
        <div style={{
          background: 'white', borderRadius: '14px', padding: '20px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}>

          {/* Tipo comprobante */}
          <h3 style={{ margin: '0 0 10px', fontSize: '12px', color: '#7f8c8d', fontWeight: 700,
            textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Comprobante
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginBottom: '18px' }}>
            {TIPOS_COMPROB.map(t => (
              <button key={t.cod} onClick={() => setTipoComprob(t.cod)} style={{
                padding: '9px 6px', borderRadius: '8px', cursor: 'pointer',
                fontWeight: 700, fontSize: '12px', textAlign: 'center',
                background: tipoComprob === t.cod ? '#2c3e50' : '#f4f6f7',
                color:      tipoComprob === t.cod ? 'white'   : '#555',
                border:     tipoComprob === t.cod ? '2px solid #2c3e50' : '2px solid transparent',
                transition: 'all 0.12s',
              }}>{t.label}</button>
            ))}
          </div>

          {/* Medio de pago */}
          <h3 style={{ margin: '0 0 10px', fontSize: '12px', color: '#7f8c8d', fontWeight: 700,
            textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Medio de pago
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '18px' }}>
            {MEDIOS_PAGO.map(p => (
              <button key={p.cod} onClick={() => setMedioPago(p.cod)} style={{
                padding: '10px 14px', borderRadius: '8px', cursor: 'pointer',
                fontWeight: 600, fontSize: '13px', textAlign: 'left',
                background: medioPago === p.cod ? '#2980b9' : '#f4f6f7',
                color:      medioPago === p.cod ? 'white'   : '#555',
                border:     medioPago === p.cod ? '2px solid #2980b9' : '2px solid transparent',
                transition: 'all 0.12s', display: 'flex', alignItems: 'center', gap: '8px',
              }}>{p.label}</button>
            ))}
          </div>

          {/* Cliente (opcional) */}
          <h3 style={{ margin: '0 0 8px', fontSize: '12px', color: '#7f8c8d', fontWeight: 700,
            textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Código cliente
          </h3>
          <input
            type="number"
            value={codCli}
            onChange={e => setCodCli(parseInt(e.target.value) || 1)}
            style={{
              width: '100%', padding: '9px 12px', boxSizing: 'border-box',
              border: '1.5px solid #dce3e8', borderRadius: '8px', fontSize: '14px',
              marginBottom: '20px',
            }}
          />

          {/* Resumen selección */}
          <div style={{
            background: '#eaf2fb', borderRadius: '8px', padding: '12px',
            fontSize: '12px', color: '#1a5276', fontWeight: 600, marginBottom: '16px',
          }}>
            {tipoLbl} · {pagoLbl}
            <div style={{ fontSize: '18px', fontWeight: 900, marginTop: '4px', color: '#2c3e50' }}>
              ${total.toFixed(2)}
            </div>
          </div>

          {/* Error */}
          {resultado && !resultado.ok && (
            <div style={{
              background: '#fadbd8', borderRadius: '8px', padding: '10px 12px',
              fontSize: '13px', color: '#922b21', marginBottom: '14px',
              border: '1px solid #e74c3c',
            }}>⚠ {resultado.msg}</div>
          )}

          {/* Botones */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <button
              onClick={() => setConfirmar(true)}
              disabled={facturando || items.length === 0}
              style={{
                padding: '13px', background: facturando || items.length === 0 ? '#95a5a6' : '#27ae60',
                color: 'white', border: 'none', borderRadius: '10px',
                cursor: facturando || items.length === 0 ? 'not-allowed' : 'pointer',
                fontWeight: 800, fontSize: '15px', transition: 'background 0.15s',
              }}>
              {facturando ? '⏳ Procesando...' : '✓ Facturar Mesa'}
            </button>
            <button onClick={onVolver} style={{
              padding: '10px', background: 'white', color: '#7f8c8d',
              border: '1px solid #dce3e8', borderRadius: '8px', cursor: 'pointer', fontSize: '13px',
            }}>← Volver al pedido</button>
          </div>
        </div>
      </div>

      {/* ── Modal confirmación ────────────────────────────────────────── */}
      {confirmar && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
          <div style={{
            background: 'white', borderRadius: '16px', padding: '28px',
            width: '340px', boxShadow: '0 24px 60px rgba(0,0,0,0.25)', textAlign: 'center',
          }}>
            <div style={{ fontSize: '42px', marginBottom: '12px' }}>🧾</div>
            <h3 style={{ margin: '0 0 8px', color: '#2c3e50', fontSize: '17px' }}>Confirmar facturación</h3>
            <p style={{ color: '#7f8c8d', fontSize: '13px', margin: '0 0 16px' }}>
              ¿Facturar Mesa {mesa?.numero} por <strong>${total.toFixed(2)}</strong>?
              <br/>{tipoLbl} · {pagoLbl}
            </p>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={() => setConfirmar(false)} disabled={facturando} style={{
                flex: 1, padding: '11px', background: '#ecf0f1', border: 'none',
                borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '14px',
              }}>Cancelar</button>
              <button onClick={facturar} disabled={facturando} style={{
                flex: 2, padding: '11px',
                background: facturando ? '#95a5a6' : '#27ae60',
                color: 'white', border: 'none', borderRadius: '8px',
                cursor: facturando ? 'not-allowed' : 'pointer', fontWeight: 800, fontSize: '14px',
              }}>
                {facturando ? '⏳ Procesando...' : '✓ Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}