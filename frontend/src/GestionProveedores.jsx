import { useState, useEffect } from 'react';

export default function GestionProveedores() {
  const [proveedores, setProveedores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  
  const [mostrarModal, setMostrarModal] = useState(false);
  const [formData, setFormData] = useState({});

  const fetchProveedores = async (filtro = '') => {
    setLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/ListarProveedores/?buscar=${filtro}`);
      const data = await res.json();
      if (data.status === 'success') setProveedores(data.data);
    } catch (error) {
      alert("Error cargando proveedores.");
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchProveedores();
  }, []);

  const handleBuscar = (e) => {
    e.preventDefault();
    fetchProveedores(busqueda);
  };

  const abrirModal = (proveedor = null) => {
    if (proveedor) {
      setFormData(proveedor);
    } else {
      // Usamos nomfantasia y estado (nombres legacy)
      setFormData({ cod_prov: null, nomfantasia: '', nro_cuit: '', domicilio: '', telefono: '', mail: '', cond_iva: 1, estado: 0 });
    }
    setMostrarModal(true);
  };

  const guardarProveedor = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/GuardarProveedor/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (data.status === 'success') {
        setMostrarModal(false);
        fetchProveedores(busqueda);
      } else {
        alert(data.mensaje);
      }
    } catch (error) {
      alert("Error de red guardando el proveedor.");
    }
  };

  const mapCondIva = (codigo) => {
    const tipos = { 1: 'Resp. Inscripto', 4: 'Exento', 5: 'Consumidor Final', 6: 'Monotributo' };
    return tipos[codigo] || `Desconocido (${codigo})`;
  };

  return (
    <div style={{ background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', alignItems: 'center' }}>
        <form onSubmit={handleBuscar} style={{ display: 'flex', gap: '10px' }}>
          <input 
            type="text" 
            placeholder="Filtrar por Razón Social o CUIT..." 
            value={busqueda} 
            onChange={(e) => setBusqueda(e.target.value)}
            style={{ padding: '8px', width: '280px', borderRadius: '4px', border: '1px solid #ccc' }}
          />
          <button type="submit" style={{ padding: '8px 15px', background: '#8e44ad', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>🔍 Buscar</button>
        </form>

        <button onClick={() => abrirModal(null)} style={{ padding: '10px 15px', background: '#2ecc71', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
          + Nuevo Proveedor
        </button>
      </div>

      {loading ? <p>Cargando proveedores...</p> : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ background: '#ecf0f1', borderBottom: '2px solid #bdc3c7', textAlign: 'left' }}>
              <th style={{ padding: '10px' }}>ID</th>
              <th style={{ padding: '10px' }}>Razón Social</th>
              <th style={{ padding: '10px' }}>CUIT</th>
              <th style={{ padding: '10px' }}>Contacto</th>
              <th style={{ padding: '10px' }}>Cond. IVA</th>
              <th style={{ padding: '10px' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {proveedores.map(p => (
              <tr key={p.cod_prov} style={{ borderBottom: '1px solid #eee', background: p.estado === 1 ? '#fdf0f0' : 'white' }}>
                <td style={{ padding: '10px', color: '#7f8c8d', fontWeight: 'bold' }}>{p.cod_prov}</td>
                {/* Mostramos nomfantasia */}
                <td style={{ padding: '10px', fontWeight: 'bold', color: '#8e44ad' }}>{p.nomfantasia}</td>
                <td style={{ padding: '10px' }}>{p.nro_cuit}</td>
                <td style={{ padding: '10px', fontSize: '12px' }}>
                  <div>📞 {p.telefono || '-'}</div>
                  <div>✉️ {p.mail || '-'}</div>
                </td>
                <td style={{ padding: '10px' }}>{mapCondIva(p.cond_iva)}</td>
                <td style={{ padding: '10px' }}>
                  <button onClick={() => abrirModal(p)} style={{ padding: '5px 10px', background: '#3498db', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer' }}>✏️ Editar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {mostrarModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ background: 'white', padding: '30px', borderRadius: '8px', width: '500px' }}>
            <h3 style={{ marginTop: 0, color: '#8e44ad' }}>{formData.cod_prov ? 'Editar Proveedor' : 'Nuevo Proveedor'}</h3>
            
            <form onSubmit={guardarProveedor} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Razón Social</label>
                {/* Input atado a nomfantasia */}
                <input required type="text" value={formData.nomfantasia} onChange={e => setFormData({...formData, nomfantasia: e.target.value})} style={{ width: '100%', padding: '8px' }} />
              </div>
              
              <div>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>CUIT</label>
                <input required type="text" value={formData.nro_cuit} onChange={e => setFormData({...formData, nro_cuit: e.target.value})} style={{ width: '100%', padding: '8px' }} />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Condición IVA</label>
                <select value={formData.cond_iva} onChange={e => setFormData({...formData, cond_iva: parseInt(e.target.value)})} style={{ width: '100%', padding: '8px' }}>
                  <option value={1}>Resp. Inscripto</option>
                  <option value={6}>Monotributo</option>
                  <option value={4}>Exento</option>
                  <option value={5}>Consumidor Final</option>
                </select>
              </div>

              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Domicilio</label>
                <input type="text" value={formData.domicilio} onChange={e => setFormData({...formData, domicilio: e.target.value})} style={{ width: '100%', padding: '8px' }} />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Teléfono</label>
                <input type="text" value={formData.telefono} onChange={e => setFormData({...formData, telefono: e.target.value})} style={{ width: '100%', padding: '8px' }} />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Email</label>
                <input type="email" value={formData.mail} onChange={e => setFormData({...formData, mail: e.target.value})} style={{ width: '100%', padding: '8px' }} />
              </div>

              <div style={{ gridColumn: 'span 2', marginTop: '10px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
                  {/* Checkbox atado a estado */}
                  <input type="checkbox" checked={formData.estado === 1} onChange={e => setFormData({...formData, estado: e.target.checked ? 1 : 0})} />
                  <span style={{ color: '#e74c3c', fontWeight: 'bold' }}>Dar de Baja (Inactivar)</span>
                </label>
              </div>

              <div style={{ gridColumn: 'span 2', display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '15px' }}>
                <button type="button" onClick={() => setMostrarModal(false)} style={{ padding: '10px 20px', cursor: 'pointer', border: '1px solid #ccc', background: 'white', borderRadius: '4px' }}>Cancelar</button>
                <button type="submit" style={{ padding: '10px 20px', background: '#8e44ad', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 'bold', borderRadius: '4px' }}>💾 Guardar</button>
              </div>
            </form>

          </div>
        </div>
      )}

    </div>
  );
}