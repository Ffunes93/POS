import { useState, useEffect } from 'react';

export default function GestionClientes() {
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  
  // Estados del Modal
  const [mostrarModal, setMostrarModal] = useState(false);
  const [formData, setFormData] = useState({});

  const fetchClientes = async (filtro = '') => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8001/api/ListarClientes/?buscar=${filtro}`);
      const data = await res.json();
      if (data.status === 'success') setClientes(data.data);
    } catch (error) {
      alert("Error cargando clientes.");
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchClientes();
  }, []);

  const handleBuscar = (e) => {
    e.preventDefault();
    fetchClientes(busqueda);
  };

  const abrirModal = (cliente = null) => {
    if (cliente) {
      setFormData(cliente); // Editar
    } else {
      // Nuevo [cite: 465, 470]
      setFormData({ cod_cli: null, denominacion: '', nro_cuit: '', domicilio: '', telefono: '', cond_iva: 5, estado_baja: 0 });
    }
    setMostrarModal(true);
  };

  const guardarCliente = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('http://localhost:8001/api/GuardarCliente/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (data.status === 'success') {
        setMostrarModal(false);
        fetchClientes(busqueda); // Recargamos
      } else {
        alert(data.mensaje);
      }
    } catch (error) {
      alert("Error guardando el cliente.");
    }
  };

  const mapCondIva = (codigo) => {
    const tipos = { 1: 'Resp. Inscripto', 4: 'Exento', 5: 'Consumidor Final', 6: 'Monotributo' };
    return tipos[codigo] || `Desconocido (${codigo})`;
  };

  return (
    <div style={{ background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
      
      {/* BARRA DE HERRAMIENTAS */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', alignItems: 'center' }}>
        <form onSubmit={handleBuscar} style={{ display: 'flex', gap: '10px' }}>
          <input 
            type="text" 
            placeholder="Filtrar por Nombre o CUIT..." 
            value={busqueda} 
            onChange={(e) => setBusqueda(e.target.value)}
            style={{ padding: '8px', width: '250px', borderRadius: '4px', border: '1px solid #ccc' }}
          />
          <button type="submit" style={{ padding: '8px 15px', background: '#34495e', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>🔍 Filtrar</button>
        </form>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={() => alert("Módulo de Cuenta Corriente en desarrollo...")} style={{ padding: '10px 15px', background: '#f39c12', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
            💳 Cuenta Corriente
          </button>
          <button onClick={() => abrirModal(null)} style={{ padding: '10px 15px', background: '#2ecc71', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
            + Nuevo Cliente
          </button>
        </div>
      </div>

      {/* GRILLA */}
      {loading ? <p>Cargando...</p> : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ background: '#ecf0f1', borderBottom: '2px solid #bdc3c7', textAlign: 'left' }}>
              <th style={{ padding: '10px' }}>ID</th>
              <th style={{ padding: '10px' }}>Nombre / Razón Social</th>
              <th style={{ padding: '10px' }}>CUIT/DNI</th>
              <th style={{ padding: '10px' }}>Domicilio</th>
              <th style={{ padding: '10px' }}>Teléfono</th>
              <th style={{ padding: '10px' }}>Cond. IVA</th>
              <th style={{ padding: '10px' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {clientes.map(c => (
              <tr key={c.cod_cli} style={{ borderBottom: '1px solid #eee', background: c.estado_baja === 1 ? '#ffeeee' : 'white' }}>
                <td style={{ padding: '10px' }}>{c.cod_cli}</td>
                <td style={{ padding: '10px', fontWeight: 'bold' }}>{c.denominacion}</td>
                <td style={{ padding: '10px' }}>{c.nro_cuit}</td>
                <td style={{ padding: '10px' }}>{c.domicilio}</td>
                <td style={{ padding: '10px' }}>{c.telefono}</td>
                <td style={{ padding: '10px' }}>{mapCondIva(c.cond_iva)}</td>
                <td style={{ padding: '10px' }}>
                  <button onClick={() => abrirModal(c)} style={{ padding: '5px 10px', background: '#3498db', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer' }}>✏️ Editar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* MODAL */}
      {mostrarModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div style={{ background: 'white', padding: '30px', borderRadius: '8px', width: '500px' }}>
            <h3>{formData.cod_cli ? 'Editar Cliente' : 'Nuevo Cliente'}</h3>
            <form onSubmit={guardarCliente} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <input required type="text" placeholder="Razón Social / Nombre" value={formData.denominacion} onChange={e => setFormData({...formData, denominacion: e.target.value})} style={{ padding: '8px' }} />
              <input required type="text" placeholder="CUIT / DNI" value={formData.nro_cuit} onChange={e => setFormData({...formData, nro_cuit: e.target.value})} style={{ padding: '8px' }} />
              <input type="text" placeholder="Domicilio" value={formData.domicilio} onChange={e => setFormData({...formData, domicilio: e.target.value})} style={{ padding: '8px' }} />
              <input type="text" placeholder="Teléfono" value={formData.telefono} onChange={e => setFormData({...formData, telefono: e.target.value})} style={{ padding: '8px' }} />
              
              <select value={formData.cond_iva} onChange={e => setFormData({...formData, cond_iva: parseInt(e.target.value)})} style={{ padding: '8px' }}>
                <option value={1}>Resp. Inscripto</option>
                <option value={4}>Exento</option>
                <option value={5}>Consumidor Final</option>
                <option value={6}>Monotributo</option>
              </select>

              <label style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <input type="checkbox" checked={formData.estado_baja === 1} onChange={e => setFormData({...formData, estado_baja: e.target.checked ? 1 : 0})} />
                Cliente de Baja (Inactivo)
              </label>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" onClick={() => setMostrarModal(false)} style={{ padding: '10px', cursor: 'pointer' }}>Cancelar</button>
                <button type="submit" style={{ padding: '10px', background: '#2ecc71', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}>Guardar</button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}