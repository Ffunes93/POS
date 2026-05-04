import { useState, useEffect } from 'react';

export default function GestionArticulos() {
  const [articulos, setArticulos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  
  const [mostrarModal, setMostrarModal] = useState(false);
  const [modoEdicion, setModoEdicion] = useState(false);
  const [formData, setFormData] = useState({});

  const fetchArticulos = async (filtro = '') => {
    setLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/ListarArticulosABM/?buscar=${filtro}`);
      const data = await res.json();
      if (data.status === 'success') setArticulos(data.data);
    } catch (error) {
      alert("Error cargando artículos.");
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchArticulos();
  }, []);

  const handleBuscar = (e) => {
    e.preventDefault();
    fetchArticulos(busqueda);
  };

  const abrirModal = (articulo = null) => {
    if (articulo) {
      setFormData({ ...articulo, is_new: false });
      setModoEdicion(true);
    } else {
      setFormData({ cod_art: '', nombre: '', barra: '', precio_1: 0, costo_ult: 0, iva: 21, is_new: true });
      setModoEdicion(false);
    }
    setMostrarModal(true);
  };

  const guardarArticulo = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/GuardarArticulo/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (data.status === 'success') {
        setMostrarModal(false);
        fetchArticulos(busqueda);
      } else {
        alert(data.mensaje);
      }
    } catch (error) {
      alert("Error guardando el artículo.");
    }
  };

  return (
    <div style={{ background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
      
      {/* BARRA DE HERRAMIENTAS */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', alignItems: 'center' }}>
        <form onSubmit={handleBuscar} style={{ display: 'flex', gap: '10px' }}>
          <input 
            type="text" 
            placeholder="Nombre, Código o Barra..." 
            value={busqueda} 
            onChange={(e) => setBusqueda(e.target.value)}
            style={{ padding: '8px', width: '250px', borderRadius: '4px', border: '1px solid #ccc' }}
          />
          <button type="submit" style={{ padding: '8px 15px', background: '#2c3e50', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>🔍 Buscar</button>
        </form>

        <button onClick={() => abrirModal(null)} style={{ padding: '10px 15px', background: '#2ecc71', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
          + Nuevo Artículo
        </button>
      </div>

      {/* GRILLA */}
      {loading ? <p>Cargando catálogo...</p> : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ background: '#34495e', color: 'white', textAlign: 'left' }}>
              <th style={{ padding: '10px' }}>Código</th>
              <th style={{ padding: '10px' }}>Descripción</th>
              <th style={{ padding: '10px' }}>Cód. Barra</th>
              <th style={{ padding: '10px' }}>Stock</th>
              <th style={{ padding: '10px' }}>Costo</th>
              <th style={{ padding: '10px' }}>Precio Vta.</th>
              <th style={{ padding: '10px' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {articulos.map(a => (
              <tr key={a.cod_art} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '10px', fontWeight: 'bold', color: '#2980b9' }}>{a.cod_art}</td>
                <td style={{ padding: '10px', fontWeight: 'bold' }}>{a.nombre}</td>
                <td style={{ padding: '10px' }}>{a.barra}</td>
                <td style={{ padding: '10px' }}>
                  <span style={{ background: a.stock <= 0 ? '#e74c3c' : '#2ecc71', color: 'white', padding: '2px 6px', borderRadius: '4px' }}>
                    {a.stock}
                  </span>
                </td>
                <td style={{ padding: '10px', color: '#7f8c8d' }}>$ {parseFloat(a.costo_ult).toFixed(2)}</td>
                <td style={{ padding: '10px', fontSize: '16px', color: '#27ae60', fontWeight: 'bold' }}>$ {parseFloat(a.precio_1).toFixed(2)}</td>
                <td style={{ padding: '10px' }}>
                  <button onClick={() => abrirModal(a)} style={{ padding: '5px 10px', background: '#f39c12', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer' }}>✏️ Editar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* MODAL */}
      {mostrarModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ background: 'white', padding: '30px', borderRadius: '8px', width: '600px' }}>
            <h3>{modoEdicion ? 'Editar Artículo' : 'Nuevo Artículo'}</h3>
            
            <form onSubmit={guardarArticulo} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
              
              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Código Interno (SKU)</label>
                <input required disabled={modoEdicion} type="text" value={formData.cod_art} onChange={e => setFormData({...formData, cod_art: e.target.value})} style={{ width: '100%', padding: '8px', background: modoEdicion ? '#ecf0f1' : 'white' }} />
              </div>

              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Descripción del Producto</label>
                <input required type="text" value={formData.nombre} onChange={e => setFormData({...formData, nombre: e.target.value})} style={{ width: '100%', padding: '8px' }} />
              </div>

              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Código de Barras</label>
                <input type="text" value={formData.barra} onChange={e => setFormData({...formData, barra: e.target.value})} style={{ width: '100%', padding: '8px' }} />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Costo Último ($)</label>
                <input type="number" step="0.01" value={formData.costo_ult} onChange={e => setFormData({...formData, costo_ult: e.target.value})} style={{ width: '100%', padding: '8px' }} />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Precio Público ($)</label>
                <input required type="number" step="0.01" value={formData.precio_1} onChange={e => setFormData({...formData, precio_1: e.target.value})} style={{ width: '100%', padding: '8px', border: '2px solid #2ecc71' }} />
              </div>

              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Tasa de IVA (%)</label>
                <select value={formData.iva} onChange={e => setFormData({...formData, iva: e.target.value})} style={{ width: '100%', padding: '8px' }}>
                  <option value={21}>21.0% - Tasa General</option>
                  <option value={10.5}>10.5% - Tasa Reducida</option>
                  <option value={0}>0.0% - Exento</option>
                </select>
              </div>

              <div style={{ gridColumn: 'span 2', display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '15px' }}>
                <button type="button" onClick={() => setMostrarModal(false)} style={{ padding: '10px', cursor: 'pointer' }}>Cancelar</button>
                <button type="submit" style={{ padding: '10px 20px', background: '#2ecc71', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}>💾 Guardar</button>
              </div>
            </form>

          </div>
        </div>
      )}

    </div>
  );
}