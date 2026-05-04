import { useState, useEffect, useRef } from 'react';

const API = `${import.meta.env.VITE_API_URL}/api`;

const inputStyle = {
  width: '100%', padding: '9px 10px', border: '1px solid #d0d7de',
  borderRadius: '5px', fontSize: '14px', boxSizing: 'border-box',
  transition: 'border-color .15s',
};
const labelStyle = { display: 'block', fontSize: '11px', fontWeight: '700',
  color: '#57606a', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '.4px' };

// ── AutoComplete genérico ─────────────────────────────────────────────────────
function AutoComplete({ placeholder, endpoint, valor, onChangeValor, onSelect, displayKey }) {
  const [results, setResults] = useState([]);
  const ref = useRef(null);

  useEffect(() => {
    if (!valor || valor.length < 2) { setResults([]); return; }
    const t = setTimeout(async () => {
      try {
        const r = await fetch(`${endpoint}?buscar=${encodeURIComponent(valor)}`);
        const d = await r.json();
        if (d.status === 'success') setResults(d.data.slice(0, 8));
      } catch {}
    }, 280);
    return () => clearTimeout(t);
  }, [valor, endpoint]);

  useEffect(() => {
    const fn = (e) => { if (ref.current && !ref.current.contains(e.target)) setResults([]); };
    document.addEventListener('mousedown', fn);
    return () => document.removeEventListener('mousedown', fn);
  }, []);

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <input
        type="text" value={valor} placeholder={placeholder}
        onChange={(e) => onChangeValor(e.target.value)}
        style={inputStyle}
      />
      {results.length > 0 && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 200,
          background: '#fff', border: '1px solid #d0d7de', borderRadius: '5px',
          boxShadow: '0 8px 24px rgba(0,0,0,.12)', maxHeight: '220px', overflowY: 'auto',
        }}>
          {results.map((item, i) => (
            <div key={i}
              onClick={() => { onSelect(item); setResults([]); }}
              style={{ padding: '10px 14px', cursor: 'pointer', fontSize: '13px', borderBottom: '1px solid #f0f0f0' }}
              onMouseOver={(e) => e.currentTarget.style.background = '#f6f8fa'}
              onMouseOut={(e)  => e.currentTarget.style.background = ''}
            >
              {item[displayKey]}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Componente principal ──────────────────────────────────────────────────────
export default function IngresoFacturaCompra() {
  const hoy = new Date().toISOString().split('T')[0];

  // Cabecera
  const [proveedor,     setProveedor]     = useState({ cod_prov: null, nomfantasia: '', cond_iva: '' });
  const [letra,         setLetra]         = useState('A');
  const [ptoVta,        setPtoVta]        = useState('0001');
  const [nroComprob,    setNroComprob]    = useState('');
  const [fechaEmision,  setFechaEmision]  = useState(hoy);
  const [condCompra,    setCondCompra]    = useState('CONTADO');
  const [categoria,     setCategoria]     = useState('');

  // Importes cabecera
  const [iva,          setIva]          = useState('');
  const [retIva,       setRetIva]       = useState('0');
  const [retGan,       setRetGan]       = useState('0');
  const [retIibb,      setRetIibb]      = useState('0');

  // Ítem actual
  const [artText,      setArtText]      = useState('');
  const [artSel,       setArtSel]       = useState(null);
  const [cantidad,     setCantidad]     = useState('1');
  const [precioUnit,   setPrecioUnit]   = useState('');

  // Grilla de ítems
  const [items, setItems]     = useState([]);
  const [cargando, setCargando] = useState(false);
  const [msg, setMsg]           = useState(null); // { tipo: 'ok'|'error', texto }

  // Proveedores buscador texto
  const [provText, setProvText] = useState('');

  // Neto calculado desde items
  const neto      = items.reduce((s, i) => s + i.total, 0);
  const ivaNum    = parseFloat(iva) || 0;
  const total     = neto + ivaNum
                    + (parseFloat(retIva) || 0)
                    + (parseFloat(retGan) || 0)
                    + (parseFloat(retIibb) || 0);

  // Auto-calcula IVA 21% cuando letra = A y se agrega item
  useEffect(() => {
    if (letra === 'A') {
      setIva((Math.round(neto * 0.21 * 100) / 100).toFixed(2));
    } else {
      setIva('0');
    }
  }, [neto, letra]);

  // Cuando cambia proveedor, auto-selecciona letra por cond_iva
  const handleSelectProveedor = (p) => {
    setProveedor(p);
    setProvText(p.nomfantasia);
    const cond = parseInt(p.cond_iva || 0);
    // 1=Inscripto→A, 5=ConsumFinal→B, 6=Monotributo→B
    setLetra(cond === 1 ? 'A' : 'B');
  };

  const agregarItem = () => {
    if (!artSel) return setMsg({ tipo: 'error', texto: 'Seleccione un artículo.' });
    const cant = parseFloat(cantidad);
    const precio = parseFloat(precioUnit);
    if (!cant || cant <= 0) return setMsg({ tipo: 'error', texto: 'Cantidad inválida.' });
    if (isNaN(precio)) return setMsg({ tipo: 'error', texto: 'Precio unitario inválido.' });

    setItems(prev => [...prev, {
      id:          Date.now(),
      cod_art:     artSel.cod_art,
      descripcion: artSel.nombre,
      cantidad:    cant,
      precio:      precio,
      total:       Math.round(precio * cant * 100) / 100,
    }]);
    setArtText(''); setArtSel(null); setCantidad('1'); setPrecioUnit(''); setMsg(null);
  };

  const eliminarItem = (id) => setItems(prev => prev.filter(i => i.id !== id));

  const limpiarForm = () => {
    setProveedor({ cod_prov: null, nomfantasia: '', cond_iva: '' });
    setProvText(''); setLetra('A'); setPtoVta('0001'); setNroComprob('');
    setFechaEmision(hoy); setCondCompra('CONTADO'); setCategoria('');
    setIva(''); setRetIva('0'); setRetGan('0'); setRetIibb('0');
    setItems([]); setArtText(''); setArtSel(null); setCantidad('1'); setPrecioUnit('');
    setMsg(null);
  };

  const guardar = async () => {
    if (!proveedor.cod_prov) return setMsg({ tipo: 'error', texto: 'Seleccione un proveedor.' });
    if (!nroComprob)         return setMsg({ tipo: 'error', texto: 'Ingrese el número de comprobante.' });
    if (items.length === 0)  return setMsg({ tipo: 'error', texto: 'Agregue al menos un artículo.' });

    setCargando(true); setMsg(null);

    const payload = {
      Proveedor_Codigo:          proveedor.cod_prov,
      Comprobante_Tipo:          'F' + letra,
      Comprobante_Letra:         letra,
      Comprobante_PtoVenta:      ptoVta.padStart(4, '0'),
      Comprobante_Numero:        parseInt(nroComprob),
      Comprobante_FechaEmision:  fechaEmision + 'T00:00:00',
      Comprobante_Neto:          parseFloat(neto.toFixed(2)),
      Comprobante_IVA:           parseFloat(ivaNum.toFixed(2)),
      Comprobante_ImporteTotal:  parseFloat(total.toFixed(2)),
      Comprobante_Ret_IVA:       parseFloat(retIva) || 0,
      Comprobante_Ret_Ganancias: parseFloat(retGan)  || 0,
      Comprobante_Ret_IIBB:      parseFloat(retIibb) || 0,
      Comprobante_CondCompra:    condCompra,
      Comprobante_Categoria:     categoria,
      Comprobante_Items: items.map(i => ({
        Item_CodigoArticulo:  i.cod_art,
        Item_DescripArticulo: i.descripcion,
        Item_CantidadUM1:     i.cantidad,
        Item_PrecioUnitario:  i.precio,
        Item_TasaIVAInscrip:  letra === 'A' ? 21 : 0,
        Item_ImporteTotal:    i.total,
      })),
    };

    try {
      const res  = await fetch(`${API}/IngresarComprobanteComprasJSON/`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setMsg({ tipo: 'ok', texto: `✅ Compra registrada. Movim #${data.movim}` });
        limpiarForm();
      } else {
        setMsg({ tipo: 'error', texto: data.mensaje || 'Error al guardar.' });
      }
    } catch {
      setMsg({ tipo: 'error', texto: 'Error de conexión.' });
    }
    setCargando(false);
  };

  // ── UI ──────────────────────────────────────────────────────────────────────
  return (
    <div style={{ background: '#f6f8fa', minHeight: '100%', padding: '4px' }}>

      {/* Título */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h2 style={{ margin: 0, fontSize: '18px', color: '#24292f', fontWeight: '700' }}>
          📦 Ingreso de Factura de Compra
        </h2>
        <button onClick={limpiarForm} style={{
          padding: '7px 14px', background: '#f3f4f6', border: '1px solid #d0d7de',
          borderRadius: '5px', cursor: 'pointer', fontSize: '13px', color: '#57606a',
        }}>+ Nueva</button>
      </div>

      {/* Mensaje */}
      {msg && (
        <div style={{
          padding: '10px 16px', borderRadius: '6px', marginBottom: '14px', fontSize: '13px', fontWeight: '600',
          background: msg.tipo === 'ok' ? '#dafbe1' : '#ffebe9',
          color:      msg.tipo === 'ok' ? '#116329' : '#a40e26',
          border:     `1px solid ${msg.tipo === 'ok' ? '#56d364' : '#ff818266'}`,
        }}>{msg.texto}</div>
      )}

      {/* ── SECCIÓN CABECERA ── */}
      <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', padding: '18px', marginBottom: '14px' }}>
        <div style={{ fontSize: '12px', fontWeight: '700', color: '#57606a', textTransform: 'uppercase', letterSpacing: '.5px', marginBottom: '14px' }}>
          Datos del Comprobante
        </div>

        {/* Fila 1: Proveedor */}
        <div style={{ marginBottom: '14px' }}>
          <label style={labelStyle}>Proveedor</label>
          <AutoComplete
            placeholder="Buscar por razón social o CUIT..."
            endpoint={`${API}/ListarProveedores/`}
            valor={provText}
            onChangeValor={setProvText}
            onSelect={handleSelectProveedor}
            displayKey="nomfantasia"
          />
          {proveedor.cod_prov && (
            <span style={{ fontSize: '12px', color: '#57606a' }}>
              Cód: <b>{proveedor.cod_prov}</b> — CUIT: {proveedor.nro_cuit || '—'}
            </span>
          )}
        </div>

        {/* Fila 2: datos comprobante */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px', marginBottom: '14px' }}>
          <div>
            <label style={labelStyle}>Letra</label>
            <select value={letra} onChange={e => setLetra(e.target.value)} style={inputStyle}>
              <option value="A">A</option>
              <option value="B">B</option>
              <option value="C">C</option>
              <option value="X">X</option>
            </select>
          </div>
          <div>
            <label style={labelStyle}>Pto. Venta</label>
            <input type="number" value={ptoVta} onChange={e => setPtoVta(e.target.value)} style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>N° Factura</label>
            <input type="number" value={nroComprob} onChange={e => setNroComprob(e.target.value)}
              placeholder="ej: 12345" style={{ ...inputStyle, borderColor: nroComprob ? '#d0d7de' : '#f85149' }} />
          </div>
          <div>
            <label style={labelStyle}>Fecha Emisión</label>
            <input type="date" value={fechaEmision} onChange={e => setFechaEmision(e.target.value)} style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Categoría</label>
            <input type="text" value={categoria} onChange={e => setCategoria(e.target.value)}
              placeholder="Opcional" style={inputStyle} maxLength={4} />
          </div>
        </div>

        {/* Fila 3: condición + retenciones */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1fr 1fr', gap: '12px' }}>
          <div>
            <label style={labelStyle}>Condición de Compra</label>
            <select value={condCompra} onChange={e => setCondCompra(e.target.value)} style={inputStyle}>
              <option value="CONTADO">CONTADO</option>
              <option value="CTA.CTE.">CTA.CTE.</option>
            </select>
          </div>
          {letra === 'A' && (
            <>
              <div>
                <label style={labelStyle}>Ret. IVA ($)</label>
                <input type="number" step="0.01" value={retIva} onChange={e => setRetIva(e.target.value)} style={inputStyle} />
              </div>
              <div>
                <label style={labelStyle}>Ret. Ganancias ($)</label>
                <input type="number" step="0.01" value={retGan} onChange={e => setRetGan(e.target.value)} style={inputStyle} />
              </div>
              <div>
                <label style={labelStyle}>Ret. IIBB ($)</label>
                <input type="number" step="0.01" value={retIibb} onChange={e => setRetIibb(e.target.value)} style={inputStyle} />
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── SECCIÓN ÍTEMS ── */}
      <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', padding: '18px', marginBottom: '14px' }}>
        <div style={{ fontSize: '12px', fontWeight: '700', color: '#57606a', textTransform: 'uppercase', letterSpacing: '.5px', marginBottom: '14px' }}>
          Artículos Recibidos
        </div>

        {/* Barra de ingreso */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 100px 130px auto', gap: '10px', alignItems: 'flex-end', marginBottom: '16px' }}>
          <div>
            <label style={labelStyle}>Artículo</label>
            <AutoComplete
              placeholder="Código, nombre o barra..."
              endpoint={`${API}/ListarArticulosABM/`}
              valor={artText}
              onChangeValor={(v) => { setArtText(v); setArtSel(null); }}
              onSelect={(a) => {
                setArtSel(a);
                setArtText(a.nombre);
                // Pre-carga el último costo conocido
                if (a.costo_ult) setPrecioUnit(parseFloat(a.costo_ult).toFixed(2));
              }}
              displayKey="nombre"
            />
          </div>
          <div>
            <label style={labelStyle}>Cantidad</label>
            <input type="number" step="0.001" value={cantidad} onChange={e => setCantidad(e.target.value)} style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Precio Unit. (neto)</label>
            <input type="number" step="0.01" value={precioUnit} onChange={e => setPrecioUnit(e.target.value)}
              placeholder="0.00" style={inputStyle} />
          </div>
          <button onClick={agregarItem} style={{
            padding: '9px 18px', background: '#2da44e', color: '#fff', border: 'none',
            borderRadius: '5px', cursor: 'pointer', fontWeight: '700', fontSize: '14px',
          }}>+ Agregar</button>
        </div>

        {/* Grilla */}
        <div style={{ border: '1px solid #d0d7de', borderRadius: '6px', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ background: '#f6f8fa', borderBottom: '1px solid #d0d7de', textAlign: 'left' }}>
                <th style={{ padding: '9px 12px' }}>Código</th>
                <th style={{ padding: '9px 12px' }}>Descripción</th>
                <th style={{ padding: '9px 12px', textAlign: 'right' }}>Cant.</th>
                <th style={{ padding: '9px 12px', textAlign: 'right' }}>P. Unit.</th>
                <th style={{ padding: '9px 12px', textAlign: 'right' }}>Subtotal</th>
                <th style={{ padding: '9px 12px', width: '40px' }}></th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr><td colSpan={6} style={{ padding: '28px', textAlign: 'center', color: '#8c959f', fontSize: '13px' }}>
                  Sin artículos cargados
                </td></tr>
              ) : items.map(item => (
                <tr key={item.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '9px 12px', fontWeight: '700', color: '#0969da' }}>{item.cod_art}</td>
                  <td style={{ padding: '9px 12px' }}>{item.descripcion}</td>
                  <td style={{ padding: '9px 12px', textAlign: 'right' }}>{item.cantidad}</td>
                  <td style={{ padding: '9px 12px', textAlign: 'right' }}>${item.precio.toFixed(2)}</td>
                  <td style={{ padding: '9px 12px', textAlign: 'right', fontWeight: '700' }}>${item.total.toFixed(2)}</td>
                  <td style={{ padding: '9px 12px', textAlign: 'center' }}>
                    <button onClick={() => eliminarItem(item.id)} style={{
                      background: 'none', border: 'none', cursor: 'pointer', color: '#cf222e', fontSize: '16px',
                    }}>✕</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── TOTALES + GUARDAR ── */}
      <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', padding: '18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '30px', fontSize: '14px' }}>
          <div>
            <span style={{ color: '#57606a' }}>Neto: </span>
            <span style={{ fontWeight: '700' }}>${neto.toFixed(2)}</span>
          </div>
          <div>
            <label style={{ color: '#57606a' }}>IVA: </label>
            <input type="number" step="0.01" value={iva} onChange={e => setIva(e.target.value)}
              style={{ width: '90px', padding: '4px 8px', border: '1px solid #d0d7de', borderRadius: '4px', fontSize: '14px', fontWeight: '700' }} />
          </div>
          {letra === 'A' && (parseFloat(retIva) + parseFloat(retGan) + parseFloat(retIibb)) > 0 && (
            <div>
              <span style={{ color: '#57606a' }}>Retenciones: </span>
              <span style={{ fontWeight: '700', color: '#cf222e' }}>
                ${(parseFloat(retIva) + parseFloat(retGan) + parseFloat(retIibb)).toFixed(2)}
              </span>
            </div>
          )}
          <div style={{ fontSize: '18px' }}>
            <span style={{ color: '#57606a' }}>TOTAL: </span>
            <span style={{ fontWeight: '800', color: '#1a7f37' }}>${total.toFixed(2)}</span>
          </div>
        </div>

        <button onClick={guardar} disabled={cargando} style={{
          padding: '12px 28px', background: cargando ? '#94d3a2' : '#2da44e', color: '#fff',
          border: 'none', borderRadius: '6px', fontSize: '15px', fontWeight: '700', cursor: cargando ? 'not-allowed' : 'pointer',
          boxShadow: '0 2px 6px rgba(45,164,78,.35)',
        }}>
          {cargando ? 'Guardando...' : '💾 Registrar Compra'}
        </button>
      </div>
    </div>
  );
}