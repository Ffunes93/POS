import { useState, useEffect } from 'react';

export default function GestionFormasPago() {
  const [formas, setFormas] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [mostrarModal, setMostrarModal] = useState(false);
  const [modoEdicion, setModoEdicion] = useState(false);
  const [formData, setFormData] = useState({});

  const fetchFormas = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8001/api/ListarFormasPago/');
      const data = await res.json();
      if (data.status === 'success') setFormas(data.data);
    } catch (error) {
      alert("Error cargando formas de pago.");
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchFormas();
  }, []);

  const abrirModal = (forma = null) => {
    if (forma) {
      setFormData({ ...forma, is_new: false });
      setModoEdicion(true);
    } else {
      setFormData({ codigo: '', descripcion: '', activa: 1, moneda: 1, is_new: true });
      setModoEdicion(false);
    }
    setMostrarModal(true);
  };

  const guardarForma = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('http://localhost:8001/api/GuardarFormaPago/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (data.status === 'success') {
        setMostrarModal(false);
        fetchFormas();
      } else {
        alert(data.mensaje);
      }
    } catch (error) {
      alert("Error guardando forma de pago.");
    }
  };

  return (
    <div style={{ background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', alignItems: 'center' }}>
        <h3 style={{ margin: 0, color: '#2c3e50' }}>Medios de Cobro</h3>
        <button onClick={() => abrirModal(null)} style={{ padding: '10px 15px', background: '#2ecc71', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
          + Nueva Forma de Pago
        </button>
      </div>

      {loading ? <p>Cargando datos...</p> : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ background: '#ecf0f1', borderBottom: '2px solid #bdc3c7', textAlign: 'left' }}>
              <th style={{ padding: '10px' }}>Código</th>
              <th style={{ padding: '10px' }}>Descripción</th>
              <th style={{ padding: '10px' }}>Moneda</th>
              <th style={{ padding: '10px' }}>Activa</th>
              <th style={{ padding: '10px' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {formas.map(f => (
              <tr key={f.codigo} style={{ borderBottom: '1px solid #eee', background: f.activa === 1 ? 'white' : '#fdf0f0' }}>
                <td style={{ padding: '10px', fontWeight: 'bold', color: '#2980b9' }}>{f.codigo}</td>
                <td style={{ padding: '10px', fontWeight: 'bold' }}>{f.descripcion}</td>
                <td style={{ padding: '10px' }}>{f.moneda === 1 ? '1 - Pesos' : f.moneda}</td>
                <td style={{ padding: '10px' }}>
                  {f.activa === 1 
                    ? <span style={{ color: 'green', fontWeight: 'bold' }}>Sí</span> 
                    : <span style={{ color: 'red', fontWeight: 'bold' }}>No</span>}
                </td>
                <td style={{ padding: '10px' }}>
                  <button onClick={() => abrirModal(f)} style={{ padding: '5px 10px', background: '#f39c12', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer' }}>✏️ Editar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* MODAL */}
      {mostrarModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ background: 'white', padding: '30px', borderRadius: '8px', width: '400px' }}>
            <h3>{modoEdicion ? 'Editar Forma de Pago' : 'Nueva Forma de Pago'}</h3>
            
            <form onSubmit={guardarForma} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              
              <div>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Código (3 letras)</label>
                <input required disabled={modoEdicion} type="text" maxLength="3" value={formData.codigo} onChange={e => setFormData({...formData, codigo: e.target.value.toUpperCase()})} style={{ width: '100%', padding: '8px', background: modoEdicion ? '#ecf0f1' : 'white', textTransform: 'uppercase' }} />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Descripción</label>
                <input required type="text" value={formData.descripcion} onChange={e => setFormData({...formData, descripcion: e.target.value.toUpperCase()})} style={{ width: '100%', padding: '8px', textTransform: 'uppercase' }} />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Moneda</label>
                <select value={formData.moneda} onChange={e => setFormData({...formData, moneda: parseInt(e.target.value)})} style={{ width: '100%', padding: '8px' }}>
                  <option value={1}>1 - Pesos (Local)</option>
                  <option value={2}>2 - Dólares</option>
                </select>
              </div>

              <div style={{ marginTop: '10px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
                  <input type="checkbox" checked={formData.activa === 1} onChange={e => setFormData({...formData, activa: e.target.checked ? 1 : 0})} />
                  <span style={{ fontWeight: 'bold' }}>Habilitada para cobros</span>
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '15px' }}>
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