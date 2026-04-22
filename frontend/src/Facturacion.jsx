import { useState, useEffect, useRef } from 'react';

// --- ESTILOS COMUNES ---
const inputStyle = { width: '100%', padding: '10px', border: '1px solid #ccc', borderRadius: '4px', boxSizing: 'border-box' };
const dropdownStyle = {
  position: 'absolute', top: '100%', left: 0, right: 0,
  background: 'white', border: '1px solid #ddd', borderRadius: '4px',
  boxShadow: '0 4px 8px rgba(0,0,0,0.1)', zIndex: 100, maxHeight: '200px', overflowY: 'auto'
};
const dropdownItemStyle = { padding: '10px', cursor: 'pointer', borderBottom: '1px solid #eee' };

// ==========================================
//    COMPONENTE DE BÚSQUEDA AUTOSUGERIDA
// ==========================================
const AutoCompleteInput = ({ placeholder, onSelect, endpoint, valorActual, onChangeValor }) => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    if (!valorActual || valorActual.length < 2) {
      setResults([]);
      return;
    }

    const debounceTimer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await fetch(`${endpoint}?buscar=${valorActual}`);
        const data = await res.json();
        if (data.status === 'success') {
          setResults(data.data.slice(0, 10));
        }
      } catch (error) {
        console.error("Error en autocompletado");
      }
      setLoading(false);
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [valorActual, endpoint]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setResults([]);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (item) => {
    setResults([]);
    onSelect(item);
  };

  return (
    <div ref={dropdownRef} style={{ position: 'relative', flex: 1 }}>
      <input
        type="text"
        placeholder={placeholder}
        value={valorActual}
        onChange={(e) => onChangeValor(e.target.value)}
        style={{ ...inputStyle, padding: '10px', height: '100%' }}
      />
      {results.length > 0 && (
        <div style={dropdownStyle}>
          {results.map((item, index) => (
            <div
              key={index}
              style={dropdownItemStyle}
              onClick={() => handleSelect(item)}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f1f8ff'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              {item.denominacion || item.nombre}
            </div>
          ))}
        </div>
      )}
      {loading && (
        <div style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', fontSize: '12px', color: '#999' }}>
          ...
        </div>
      )}
    </div>
  );
};

// ==========================================
//         COMPONENTE DE FACTURACIÓN
// ==========================================
export default function Facturacion({ user, cajaId }) {
  // --- ESTADOS DE CABECERA ---
  const [cliente, setCliente] = useState({ cod_cli: '1', denominacion: 'CONSUMIDOR FINAL' });
  const [condVenta, setCondVenta] = useState('1'); 
  const [vendedor, setVendedor] = useState(user?.id || 1);
  const [tipoComprobante, setTipoComprobante] = useState('TK'); 
  
  // --- ESTADOS DE DETALLE (GRILLA) ---
  const [articuloSearchText, setArticuloSearchText] = useState('');
  const [items, setItems] = useState([]);

  // --- ESTADOS DEL BUSCADOR (MODAL F3) ---
  const [modalBusqueda, setModalBusqueda] = useState(false);
  const [tipoBusqueda, setTipoBusqueda] = useState('');
  const [textoBusqueda, setTextoBusqueda] = useState('');
  const [resultadosBusqueda, setResultadosBusqueda] = useState([]);
  const [buscando, setBuscando] = useState(false);

  // --- CÁLCULOS ---
  const subtotal = items.reduce((acc, item) => acc + (item.precio * item.cantidad), 0);
  const total = subtotal;

  const abrirBuscador = (tipo) => {
    setTipoBusqueda(tipo);
    setTextoBusqueda('');
    setResultadosBusqueda([]);
    setModalBusqueda(true);
  };

  const ejecutarBusqueda = async (e) => {
    e.preventDefault();
    setBuscando(true);
    try {
      const endpoint = tipoBusqueda === 'CLIENTE' 
        ? `http://localhost:8001/api/ListarClientes/?buscar=${textoBusqueda}`
        : `http://localhost:8001/api/ListarArticulosABM/?buscar=${textoBusqueda}`;
        
      const res = await fetch(endpoint);
      const data = await res.json();
      if (data.status === 'success') {
        setResultadosBusqueda(data.data);
      }
    } catch (error) {
      alert("Error en la búsqueda.");
    }
    setBuscando(false);
  };

  const seleccionarResultado = (item) => {
    if (tipoBusqueda === 'CLIENTE') {
      setCliente({ cod_cli: item.cod_cli, denominacion: item.denominacion });
    } else if (tipoBusqueda === 'ARTICULO') {
      agregarAlCarrito(item);
    }
    setModalBusqueda(false);
  };

  const agregarAlCarrito = (articuloDb) => {
    const nuevoItem = {
      id: Date.now() + Math.random(),
      codigo: articuloDb.cod_art,
      descripcion: articuloDb.nombre,
      cantidad: 1, 
      precio: parseFloat(articuloDb.precio_1),
    };
    setItems(prevItems => [...prevItems, nuevoItem]);
  };

  const buscarArticuloManual = async (e) => {
    e.preventDefault();
    if (!articuloSearchText) return;

    try {
      const res = await fetch(`http://localhost:8001/api/ListarArticulosABM/?buscar=${articuloSearchText}`);
      const data = await res.json();
      
      const articulo = data.data.find(a => 
        a.cod_art.toUpperCase() === articuloSearchText.toUpperCase() || 
        a.barra === articuloSearchText
      );

      if (articulo) {
        agregarAlCarrito(articulo);
        setArticuloSearchText(''); 
      } else {
        alert("❌ Artículo no encontrado. Verifique el código o use el buscador.");
      }
    } catch (error) {
      alert("Error conectando con la base de datos.");
    }
  };

  const eliminarItem = (id) => {
    setItems(items.filter(item => item.id !== id));
  };

  const procesarVenta = async () => {
    if (items.length === 0) return alert("No hay artículos para facturar.");

    const payloadVenta = {
      Cliente_Codigo: cliente.cod_cli,
      Comprobante_Tipo: tipoComprobante,
      Comprobante_Letra: "X",
      Comprobante_PtoVenta: 1,
      Comprobante_Numero: 1,
      Comprobante_FechaEmision: new Date().toISOString(),
      Comprobante_ImporteTotal: total,
      Comprobante_CondVenta: condVenta,
      nro_caja: cajaId,
      Vendedor_Codigo: vendedor,
      Comprobante_Items: items.map(i => ({
        Item_CodigoArticulo: i.codigo,
        Item_DescripArticulo: i.descripcion,
        Item_CantidadUM1: i.cantidad,
        Item_PrecioUnitario: i.precio,
        Item_ImporteTotal: i.precio * i.cantidad
      })),
      Comprobante_MediosPago: [
        { MedioPago: condVenta === '1' ? 'EFE' : 'CTA', MedioPago_Importe: total }
      ]
    };

    try {
      // 👇 ACÁ ESTÁ EL CAMBIO CLAVE: Reemplazamos GuardarVenta por IngresarComprobanteVentasJSON
      const res = await fetch('http://localhost:8001/api/IngresarComprobanteVentasJSON/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payloadVenta) // Tu JSON armado
      });
      
      const data = await res.json();
      
      if (res.ok && data.status === 'success') {
        alert("Venta guardada con éxito. Movim: " + data.movim);
        // setCarrito([]); // Limpiar carrito
      } else {
        alert("El servidor rechazó la venta:\n" + (data.mensaje || JSON.stringify(data.errores)));
      }
    } catch (error) {
      alert("Error de conexión al generar la venta.");
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      <h2 style={{ marginTop: 0, color: '#2c3e50', borderBottom: '2px solid #ecf0f1', paddingBottom: '10px' }}>🧾 Emisión de Comprobante</h2>
      
      {/* --- PANEL DE CABECERA AJUSTADO EN 2 FILAS --- */}
      <div style={{ background: 'white', padding: '20px', borderRadius: '6px', border: '1px solid #ddd', marginBottom: '20px', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '15px' }}>
        
        {/* FILA 1: CLIENTE OCUPA LAS 3 COLUMNAS */}
        <div style={{ gridColumn: 'span 3' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d', marginBottom: '5px' }}>Cliente</label>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'stretch' }}>
            <input 
              type="text" 
              value={cliente.cod_cli} 
              readOnly 
              style={{ width: '80px', padding: '10px', border: '1px solid #ccc', borderRadius: '4px', background: '#ecf0f1', textAlign: 'center', fontWeight: 'bold', boxSizing: 'border-box' }} 
              title="ID Cliente" 
            />
            
            <AutoCompleteInput 
              placeholder="Escriba para buscar o seleccione consumidor final..." 
              endpoint="http://localhost:8001/api/ListarClientes/" 
              valorActual={cliente.denominacion}
              onChangeValor={(val) => setCliente({ ...cliente, denominacion: val })}
              onSelect={(item) => setCliente({ cod_cli: item.cod_cli, denominacion: item.denominacion })}
            />
            
            <button type="button" onClick={() => abrirBuscador('CLIENTE')} style={{ padding: '0 20px', background: '#34495e', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', whiteSpace: 'nowrap' }} title="Abrir Buscador Avanzado">
              🔍 Búsqueda Avanzada
            </button>
          </div>
        </div>

        {/* FILA 2: DIVIDIDA EN 3 COLUMNAS IGUALES */}
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d', marginBottom: '5px' }}>Tipo Comprobante</label>
          <select value={tipoComprobante} onChange={e => setTipoComprobante(e.target.value)} style={inputStyle}>
            <option value="TK">TICKET (TK)</option>
            <option value="FA">FACTURA (FA)</option>
            <option value="PR">PRESUPUESTO (PR)</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d', marginBottom: '5px' }}>Condición de Venta</label>
          <select value={condVenta} onChange={e => setCondVenta(e.target.value)} style={inputStyle}>
            <option value="1">1 - Contado</option>
            <option value="2">2 - Cta. Corriente</option>
          </select>
        </div>
        
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d', marginBottom: '5px' }}>Código Vendedor</label>
          <input type="number" value={vendedor} onChange={e => setVendedor(e.target.value)} style={{ ...inputStyle, textAlign: 'center' }} />
        </div>
      </div>

      {/* --- INGRESO DE ARTÍCULOS --- */}
      <form onSubmit={buscarArticuloManual} style={{ display: 'flex', gap: '10px', marginBottom: '20px', background: '#2c3e50', padding: '15px', borderRadius: '6px' }}>
        <AutoCompleteInput 
          placeholder="Escanee el código de barras, SKU o escriba el nombre del artículo..." 
          endpoint="http://localhost:8001/api/ListarArticulosABM/" 
          valorActual={articuloSearchText}
          onChangeValor={setArticuloSearchText}
          onSelect={(item) => { agregarAlCarrito(item); setArticuloSearchText(''); }} 
        />
        <button type="submit" style={{ padding: '12px 20px', background: '#2ecc71', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '16px' }}>
          Agregar ↵
        </button>
        <button type="button" onClick={() => abrirBuscador('ARTICULO')} style={{ padding: '12px 20px', background: '#f39c12', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '16px' }}>
          🔍 Avanzada
        </button>
      </form>

      {/* --- GRILLA DE DETALLE --- */}
      <div style={{ minHeight: '200px', background: 'white', border: '1px solid #ddd', borderRadius: '6px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
          <thead>
            <tr style={{ background: '#ecf0f1', borderBottom: '2px solid #bdc3c7' }}>
              <th style={{ padding: '10px' }}>Código</th>
              <th style={{ padding: '10px' }}>Descripción</th>
              <th style={{ padding: '10px', textAlign: 'right' }}>Cant.</th>
              <th style={{ padding: '10px', textAlign: 'right' }}>Precio Unit.</th>
              <th style={{ padding: '10px', textAlign: 'right' }}>Subtotal</th>
              <th style={{ padding: '10px', textAlign: 'center' }}>X</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr><td colSpan="6" style={{ padding: '40px', textAlign: 'center', color: '#95a5a6' }}>Escanee un producto o comience a tipear su nombre.</td></tr>
            ) : items.map(item => (
              <tr key={item.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '10px', fontWeight: 'bold', color: '#2980b9' }}>{item.codigo}</td>
                <td style={{ padding: '10px', fontWeight: 'bold' }}>{item.descripcion}</td>
                <td style={{ padding: '10px', textAlign: 'right' }}>{item.cantidad}</td>
                <td style={{ padding: '10px', textAlign: 'right' }}>$ {item.precio.toFixed(2)}</td>
                <td style={{ padding: '10px', textAlign: 'right', fontWeight: 'bold', color: '#27ae60' }}>$ {(item.precio * item.cantidad).toFixed(2)}</td>
                <td style={{ padding: '10px', textAlign: 'center' }}>
                  <button type="button" onClick={() => eliminarItem(item.id)} style={{ background: '#e74c3c', color: 'white', border: 'none', borderRadius: '50%', width: '25px', height: '25px', cursor: 'pointer', fontWeight: 'bold' }}>X</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* --- PIE Y TOTALES --- */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: '20px' }}>
        <div style={{ color: '#7f8c8d' }}>
          Operando en Caja # {cajaId}
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '14px', color: '#7f8c8d' }}>Subtotal: $ {subtotal.toFixed(2)}</div>
            <div style={{ fontSize: '32px', color: '#27ae60', fontWeight: 'bold', margin: '5px 0' }}>Total: $ {total.toFixed(2)}</div>
          </div>
          <button onClick={procesarVenta} style={{ padding: '20px 40px', background: '#3498db', color: 'white', border: 'none', borderRadius: '8px', fontSize: '20px', fontWeight: 'bold', cursor: 'pointer', boxShadow: '0 4px 6px rgba(52,152,219,0.3)' }}>
            💰 COBRAR
          </button>
        </div>
      </div>

      {/* =========================================
                 MODAL DEL BUSCADOR (F3)
          ========================================= */}
      {modalBusqueda && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.7)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 9999 }}>
          <div style={{ background: 'white', width: '700px', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 10px 25px rgba(0,0,0,0.5)' }}>
            
            <div style={{ background: '#34495e', color: 'white', padding: '15px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0 }}>🔍 Buscador de {tipoBusqueda === 'CLIENTE' ? 'Clientes' : 'Artículos'}</h3>
              <button onClick={() => setModalBusqueda(false)} style={{ background: 'transparent', color: 'white', border: 'none', fontSize: '20px', cursor: 'pointer' }}>✖</button>
            </div>

            <div style={{ padding: '20px', background: '#ecf0f1' }}>
              <form onSubmit={ejecutarBusqueda} style={{ display: 'flex', gap: '10px' }}>
                <input 
                  autoFocus 
                  type="text" 
                  placeholder="Ingrese su búsqueda por cualquier parte del texto..." 
                  value={textoBusqueda} 
                  onChange={(e) => setTextoBusqueda(e.target.value)}
                  style={{ flex: 1, padding: '12px', fontSize: '16px', borderRadius: '4px', border: '1px solid #bdc3c7' }}
                />
                <button type="submit" style={{ padding: '12px 20px', background: '#2980b9', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                  Buscar
                </button>
              </form>
            </div>

            <div style={{ height: '350px', overflowY: 'auto' }}>
              {buscando ? (
                <div style={{ padding: '40px', textAlign: 'center', color: '#7f8c8d' }}>Buscando...</div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                  <thead>
                    <tr style={{ background: '#bdc3c7', textAlign: 'left' }}>
                      <th style={{ padding: '10px' }}>{tipoBusqueda === 'CLIENTE' ? 'ID' : 'Código'}</th>
                      <th style={{ padding: '10px' }}>{tipoBusqueda === 'CLIENTE' ? 'Razón Social / Nombre' : 'Descripción'}</th>
                      <th style={{ padding: '10px', textAlign: 'right' }}>{tipoBusqueda === 'CLIENTE' ? 'CUIT' : 'Precio'}</th>
                      {tipoBusqueda === 'ARTICULO' && <th style={{ padding: '10px', textAlign: 'right' }}>Stock</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {resultadosBusqueda.length === 0 ? (
                      <tr><td colSpan="4" style={{ padding: '20px', textAlign: 'center', color: '#95a5a6' }}>No hay resultados</td></tr>
                    ) : resultadosBusqueda.map((r, idx) => (
                      <tr 
                        key={idx} 
                        onClick={() => seleccionarResultado(r)}
                        style={{ borderBottom: '1px solid #eee', cursor: 'pointer' }}
                        onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f1f8ff'}
                        onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                      >
                        <td style={{ padding: '10px', fontWeight: 'bold' }}>{tipoBusqueda === 'CLIENTE' ? r.cod_cli : r.cod_art}</td>
                        <td style={{ padding: '10px' }}>{tipoBusqueda === 'CLIENTE' ? r.denominacion : r.nombre}</td>
                        <td style={{ padding: '10px', textAlign: 'right' }}>
                          {tipoBusqueda === 'CLIENTE' ? r.nro_cuit : `$ ${parseFloat(r.precio_1).toFixed(2)}`}
                        </td>
                        {tipoBusqueda === 'ARTICULO' && (
                          <td style={{ padding: '10px', textAlign: 'right', color: r.stock > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                            {r.stock}
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

          </div>
        </div>
      )}

    </div>
  );
}