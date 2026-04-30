import { useState, useRef } from 'react'

const API = 'http://localhost:8001'

const TIPOS = [
  { cod: 'FA', label: 'Factura A' },
  { cod: 'FB', label: 'Factura B' },
  { cod: 'FC', label: 'Factura C' },
  { cod: 'FM', label: 'Factura M' },
  { cod: 'NCA', label: 'Nota Crédito A' },
  { cod: 'NCB', label: 'Nota Crédito B' },
  { cod: 'NDA', label: 'Nota Débito A' },
  { cod: 'NDB', label: 'Nota Débito B' },
]

const CONFIANZA_CFG = {
  alta:  { bg: '#d5f5e3', color: '#1e8449', label: '✅ Alta confianza'  },
  media: { bg: '#fef9e7', color: '#9a7d0a', label: '⚠️ Confianza media' },
  baja:  { bg: '#fadbd8', color: '#922b21', label: '❌ Baja confianza'  },
}

export default function AsistenteCompras({ user, cajaId, onVolver }) {
  const [etapa,       setEtapa]       = useState('upload')  // upload | procesando | revision | guardando | exito
  const [datos,       setDatos]       = useState(null)
  const [error,       setError]       = useState('')
  const [resultado,   setResultado]   = useState(null)
  const [dragging,    setDragging]    = useState(false)
  const [textoVisible,setTextoVisible]= useState(false)
  const inputRef = useRef()

  /* ── Subir y procesar PDF ─────────────────────────────────────────── */
  const procesarPDF = async (archivo) => {
    if (!archivo || !archivo.name.toLowerCase().endsWith('.pdf')) {
      setError('Solo se aceptan archivos PDF.')
      return
    }
    if (archivo.size > 20 * 1024 * 1024) {
      setError('El archivo supera los 20 MB.')
      return
    }

    setError('')
    setEtapa('procesando')

    const form = new FormData()
    form.append('archivo', archivo)

    try {
      const r = await fetch(`${API}/api/ia/procesar_factura/`, {
        method: 'POST',
        body:   form,
      })
      const d = await r.json()

      if (d.status === 'success') {
        setDatos({ ...d.datos, cajero: user?.id || 1, nro_caja: cajaId || 1, usuario: user?.nombre_login || 'admin' })
        setEtapa('revision')
      } else {
        setError(d.mensaje || 'Error al procesar el PDF')
        setEtapa('upload')
      }
    } catch {
      setError('Error de conexión con el servidor')
      setEtapa('upload')
    }
  }

  /* ── Confirmar y guardar ──────────────────────────────────────────── */
  const confirmar = async () => {
    setEtapa('guardando')
    try {
      const r = await fetch(`${API}/api/ia/confirmar_factura/`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(datos),
      })
      const d = await r.json()
      if (d.status === 'success') {
        setResultado(d)
        setEtapa('exito')
      } else {
        setError(d.mensaje || 'Error al guardar')
        setEtapa('revision')
      }
    } catch {
      setError('Error de conexión')
      setEtapa('revision')
    }
  }

  /* ── Helpers UI ───────────────────────────────────────────────────── */
  const campo = (label, key, tipo = 'text', opciones = null) => (
    <div style={{ marginBottom: '14px' }}>
      <label style={{ display: 'block', fontSize: '11px', fontWeight: 700,
        color: '#7f8c8d', textTransform: 'uppercase', marginBottom: '4px' }}>
        {label}
      </label>
      {opciones ? (
        <select
          value={datos[key] || ''}
          onChange={e => setDatos({ ...datos, [key]: e.target.value })}
          style={estiloInput}>
          <option value="">— Seleccionar —</option>
          {opciones.map(o => <option key={o.cod} value={o.cod}>{o.label}</option>)}
        </select>
      ) : (
        <input
          type={tipo}
          value={datos[key] ?? ''}
          onChange={e => setDatos({ ...datos, [key]: tipo === 'number' ? parseFloat(e.target.value) || 0 : e.target.value })}
          style={estiloInput}
        />
      )}
    </div>
  )

  const estiloInput = {
    width: '100%', padding: '9px 12px', boxSizing: 'border-box',
    border: '1.5px solid #dce3e8', borderRadius: '8px', fontSize: '14px',
    background: 'white', color: '#2c3e50',
  }

  const card = {
    background: 'white', borderRadius: '14px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.07)', padding: '24px',
  }

  /* ════════════════════════════════════════════════════════════════════
     ETAPA: UPLOAD
  ═══════════════════════════════════════════════════════════════════ */
  if (etapa === 'upload') return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <button onClick={onVolver} style={{
          background: 'none', border: 'none', cursor: 'pointer',
          color: '#7f8c8d', fontSize: '18px', padding: '4px',
        }}>←</button>
        <div>
          <h2 style={{ margin: 0, color: '#2c3e50', fontSize: '20px' }}>
            🤖 Asistente de carga — Facturas PDF
          </h2>
          <div style={{ fontSize: '13px', color: '#7f8c8d', marginTop: '2px' }}>
            Subí una factura PDF y el sistema extrae los datos automáticamente
          </div>
        </div>
      </div>

      {/* Zona de drop */}
      <div
        style={{
          ...card,
          border: `3px dashed ${dragging ? '#3498db' : '#dce3e8'}`,
          background: dragging ? '#eaf2fb' : 'white',
          textAlign: 'center', padding: '60px 40px',
          cursor: 'pointer', transition: 'all 0.15s',
        }}
        onClick={() => inputRef.current?.click()}
        onDragOver={e  => { e.preventDefault(); setDragging(true)  }}
        onDragLeave={() => setDragging(false)}
        onDrop={e => {
          e.preventDefault(); setDragging(false)
          const f = e.dataTransfer.files[0]
          if (f) procesarPDF(f)
        }}
      >
        <div style={{ fontSize: '52px', marginBottom: '16px' }}>📄</div>
        <div style={{ fontSize: '17px', fontWeight: 700, color: '#2c3e50', marginBottom: '8px' }}>
          Arrastrá el PDF acá o hacé clic para seleccionar
        </div>
        <div style={{ fontSize: '13px', color: '#7f8c8d' }}>
          Facturas AFIP · Notas de crédito/débito · Máx. 20 MB
        </div>
        <input
          ref={inputRef} type="file" accept=".pdf"
          style={{ display: 'none' }}
          onChange={e => { if (e.target.files[0]) procesarPDF(e.target.files[0]) }}
        />
      </div>

      {error && (
        <div style={{
          marginTop: '16px', padding: '12px 16px', borderRadius: '8px',
          background: '#fadbd8', border: '1px solid #e74c3c', color: '#922b21', fontSize: '14px',
        }}>⚠ {error}</div>
      )}

      {/* Info qué reconoce */}
      <div style={{ ...card, marginTop: '16px' }}>
        <div style={{ fontSize: '13px', color: '#7f8c8d', fontWeight: 700, marginBottom: '10px' }}>
          ✅ El sistema detecta automáticamente:
        </div>
        {[
          'Tipo de comprobante (A, B, C, M)',
          'Número y punto de venta',
          'CUIT y razón social del proveedor',
          'Fecha de emisión',
          'Neto, IVA 21%, IVA 10.5%, percepciones',
          'Importe total',
          'CAE y vencimiento',
          'Ítems / líneas de detalle',
        ].map((item, i) => (
          <div key={i} style={{ fontSize: '13px', color: '#555', padding: '3px 0' }}>
            · {item}
          </div>
        ))}
      </div>
    </div>
  )

  /* ════════════════════════════════════════════════════════════════════
     ETAPA: PROCESANDO
  ═══════════════════════════════════════════════════════════════════ */
  if (etapa === 'procesando') return (
    <div style={{ maxWidth: '500px', margin: '80px auto', textAlign: 'center' }}>
      <div style={{ ...card }}>
        <div style={{ fontSize: '52px', marginBottom: '16px' }}>⚙️</div>
        <div style={{ fontSize: '18px', fontWeight: 700, color: '#2c3e50', marginBottom: '8px' }}>
          Procesando PDF...
        </div>
        <div style={{ fontSize: '13px', color: '#7f8c8d', marginBottom: '24px' }}>
          Docling está extrayendo el texto y analizando los campos
        </div>
        <div style={{
          height: '6px', background: '#eaecee', borderRadius: '3px', overflow: 'hidden',
        }}>
          <div style={{
            height: '100%', background: '#3498db', borderRadius: '3px',
            animation: 'loading 1.5s ease-in-out infinite',
            width: '40%',
          }}/>
        </div>
        <style>{`@keyframes loading { 0%{margin-left:-40%} 100%{margin-left:100%} }`}</style>
      </div>
    </div>
  )

  /* ════════════════════════════════════════════════════════════════════
     ETAPA: REVISIÓN
  ═══════════════════════════════════════════════════════════════════ */
  if (etapa === 'revision' && datos) {
    const cfg = CONFIANZA_CFG[datos.confianza] || CONFIANZA_CFG.media
    return (
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
          <button onClick={() => setEtapa('upload')} style={{
            background: 'none', border: 'none', cursor: 'pointer', color: '#7f8c8d', fontSize: '18px',
          }}>←</button>
          <div style={{ flex: 1 }}>
            <h2 style={{ margin: 0, fontSize: '18px', color: '#2c3e50' }}>
              Revisar datos extraídos — {datos.nombre_archivo}
            </h2>
          </div>
          <div style={{
            padding: '6px 14px', borderRadius: '20px',
            background: cfg.bg, color: cfg.color, fontSize: '13px', fontWeight: 700,
          }}>{cfg.label}</div>
        </div>

        {/* Advertencias */}
        {datos.advertencias?.length > 0 && (
          <div style={{
            marginBottom: '16px', padding: '12px 16px', borderRadius: '8px',
            background: '#fef9e7', border: '1px solid #f39c12', color: '#9a7d0a', fontSize: '13px',
          }}>
            {datos.advertencias.map((a, i) => <div key={i}>⚠ {a}</div>)}
          </div>
        )}

        {error && (
          <div style={{
            marginBottom: '16px', padding: '12px 16px', borderRadius: '8px',
            background: '#fadbd8', border: '1px solid #e74c3c', color: '#922b21', fontSize: '13px',
          }}>⚠ {error}</div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>

          {/* ── Col izquierda: datos del comprobante ── */}
          <div style={card}>
            <h3 style={{ margin: '0 0 16px', fontSize: '14px', color: '#7f8c8d',
              fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Datos del comprobante
            </h3>
            {campo('Tipo comprobante', 'tipo_comprob', 'text', TIPOS)}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>{campo('Punto de venta', 'punto_venta')}</div>
              <div>{campo('Número', 'numero')}</div>
            </div>
            {campo('Fecha', 'fecha', 'date')}
            {campo('CAE', 'cae')}
            {campo('Vto. CAE', 'cae_vto', 'date')}
          </div>

          {/* ── Col derecha: proveedor + montos ── */}
          <div>
            <div style={{ ...card, marginBottom: '16px' }}>
              <h3 style={{ margin: '0 0 16px', fontSize: '14px', color: '#7f8c8d',
                fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Proveedor
              </h3>
              {campo('CUIT', 'proveedor_cuit')}
              {campo('Razón social', 'proveedor_razon')}
            </div>

            <div style={card}>
              <h3 style={{ margin: '0 0 16px', fontSize: '14px', color: '#7f8c8d',
                fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Montos
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>{campo('Neto gravado', 'neto', 'number')}</div>
                <div>{campo('IVA 21%', 'iva_21', 'number')}</div>
                <div>{campo('IVA 10.5%', 'iva_105', 'number')}</div>
                <div>{campo('Percep. IVA', 'percep_iva', 'number')}</div>
                <div>{campo('Percep. IIBB', 'percep_iibb', 'number')}</div>
                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 700,
                    color: '#27ae60', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Total
                  </label>
                  <input
                    type="number"
                    value={datos.total ?? 0}
                    onChange={e => setDatos({ ...datos, total: parseFloat(e.target.value) || 0 })}
                    style={{ ...estiloInput, fontWeight: 800, fontSize: '16px', color: '#27ae60', border: '2px solid #27ae60' }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Ítems / detalle ── */}
        {datos.items?.length > 0 && (
          <div style={{ ...card, marginTop: '16px' }}>
            <h3 style={{ margin: '0 0 14px', fontSize: '14px', color: '#7f8c8d',
              fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Detalle ({datos.items.length} ítems)
            </h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #eaecee' }}>
                  <th style={{ textAlign: 'left', padding: '6px', color: '#7f8c8d', fontWeight: 600 }}>Descripción</th>
                  <th style={{ textAlign: 'center', padding: '6px', color: '#7f8c8d', fontWeight: 600, width: '80px' }}>Cant.</th>
                  <th style={{ textAlign: 'right', padding: '6px', color: '#7f8c8d', fontWeight: 600, width: '110px' }}>P. Unit.</th>
                  <th style={{ textAlign: 'right', padding: '6px', color: '#7f8c8d', fontWeight: 600, width: '110px' }}>Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {datos.items.map((it, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #f2f3f4' }}>
                    <td style={{ padding: '6px' }}>
                      <input
                        value={it.descripcion}
                        onChange={e => {
                          const items = [...datos.items]
                          items[i] = { ...items[i], descripcion: e.target.value }
                          setDatos({ ...datos, items })
                        }}
                        style={{ ...estiloInput, padding: '5px 8px', fontSize: '12px' }}
                      />
                    </td>
                    <td style={{ padding: '6px' }}>
                      <input type="number"
                        value={it.cantidad}
                        onChange={e => {
                          const items = [...datos.items]
                          items[i] = { ...items[i], cantidad: parseFloat(e.target.value) || 0 }
                          setDatos({ ...datos, items })
                        }}
                        style={{ ...estiloInput, padding: '5px 8px', fontSize: '12px', textAlign: 'center' }}
                      />
                    </td>
                    <td style={{ padding: '6px' }}>
                      <input type="number"
                        value={it.precio_unit}
                        onChange={e => {
                          const items = [...datos.items]
                          items[i] = { ...items[i], precio_unit: parseFloat(e.target.value) || 0 }
                          setDatos({ ...datos, items })
                        }}
                        style={{ ...estiloInput, padding: '5px 8px', fontSize: '12px', textAlign: 'right' }}
                      />
                    </td>
                    <td style={{ padding: '6px', textAlign: 'right', fontWeight: 700, color: '#2c3e50' }}>
                      ${parseFloat(it.subtotal || 0).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Texto extraído (expandible para debug) */}
        <div style={{ marginTop: '12px' }}>
          <button onClick={() => setTextoVisible(v => !v)} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: '12px', color: '#7f8c8d', textDecoration: 'underline',
          }}>
            {textoVisible ? '▲ Ocultar' : '▼ Ver'} texto extraído del PDF
          </button>
          {textoVisible && (
            <pre style={{
              marginTop: '8px', padding: '12px', background: '#f8f9fa',
              borderRadius: '8px', fontSize: '11px', color: '#555',
              maxHeight: '200px', overflowY: 'auto', whiteSpace: 'pre-wrap',
            }}>{datos.texto_extraido}</pre>
          )}
        </div>

        {/* Botones finales */}
        <div style={{ display: 'flex', gap: '10px', marginTop: '20px', justifyContent: 'flex-end' }}>
          <button onClick={() => setEtapa('upload')} style={{
            padding: '12px 24px', background: 'white', color: '#7f8c8d',
            border: '1px solid #dce3e8', borderRadius: '8px', cursor: 'pointer',
            fontSize: '14px', fontWeight: 600,
          }}>← Cargar otro PDF</button>
          <button onClick={confirmar} style={{
            padding: '12px 32px', background: '#27ae60', color: 'white',
            border: 'none', borderRadius: '8px', cursor: 'pointer',
            fontSize: '14px', fontWeight: 800,
          }}>✓ Confirmar y Guardar</button>
        </div>
      </div>
    )
  }

  /* ════════════════════════════════════════════════════════════════════
     ETAPA: GUARDANDO
  ═══════════════════════════════════════════════════════════════════ */
  if (etapa === 'guardando') return (
    <div style={{ maxWidth: '400px', margin: '80px auto', textAlign: 'center' }}>
      <div style={card}>
        <div style={{ fontSize: '42px', marginBottom: '12px' }}>💾</div>
        <div style={{ fontWeight: 700, color: '#2c3e50', fontSize: '16px' }}>
          Guardando factura...
        </div>
      </div>
    </div>
  )

  /* ════════════════════════════════════════════════════════════════════
     ETAPA: ÉXITO
  ═══════════════════════════════════════════════════════════════════ */
  if (etapa === 'exito') return (
    <div style={{ maxWidth: '480px', margin: '80px auto', textAlign: 'center' }}>
      <div style={card}>
        <div style={{ fontSize: '56px', marginBottom: '16px' }}>✅</div>
        <h2 style={{ margin: '0 0 8px', color: '#27ae60' }}>¡Factura guardada!</h2>
        <p style={{ color: '#7f8c8d', fontSize: '14px', margin: '0 0 20px' }}>
          {resultado?.mensaje}
        </p>
        {resultado?.movim && (
          <div style={{
            background: '#eafaf1', borderRadius: '10px', padding: '14px',
            fontSize: '15px', fontWeight: 700, color: '#1e8449', marginBottom: '20px',
          }}>
            Compra registrada · Movimiento #{resultado.movim}
          </div>
        )}
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
          <button onClick={() => { setEtapa('upload'); setDatos(null); setResultado(null) }} style={{
            padding: '10px 20px', background: '#3498db', color: 'white',
            border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 700,
          }}>📄 Cargar otra factura</button>
          <button onClick={onVolver} style={{
            padding: '10px 20px', background: 'white', color: '#7f8c8d',
            border: '1px solid #dce3e8', borderRadius: '8px', cursor: 'pointer', fontWeight: 600,
          }}>← Volver</button>
        </div>
      </div>
    </div>
  )

  return null
}