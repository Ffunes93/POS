import { useState, useEffect } from 'react';

const inputStyle = { width: '100%', padding: '10px', border: '1px solid #ccc', borderRadius: '4px', boxSizing: 'border-box' };

export default function GestionRubros() {
  const [rubros, setRubros] = useState([]);
  const [subrubros, setSubrubros] = useState([]);
  
  // Modales
  const [modalRubro, setModalRubro] = useState(false);
  const [modalSubrubro, setModalSubrubro] = useState(false);
  const [formData, setFormData] = useState({});

  useEffect(() => {
    fetchRubros();
    fetchSubrubros();
  }, []);

  const fetchRubros = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/ListarRubros/');
      const data = await res.json();
      if (data.status === 'success') setRubros(data.data);
    } catch (e) { alert("Error cargando rubros"); }
  };

  const fetchSubrubros = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/ListarSubRubros/');
      const data = await res.json();
      if (data.status === 'success') setSubrubros(data.data);
    } catch (e) { alert("Error cargando subrubros"); }
  };

  const guardarRubro = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('http://localhost:8001/api/GuardarRubro/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') { 
        setModalRubro(false); 
        fetchRubros(); 
      } else {
        alert(data.mensaje);
      }
    } catch (e) { alert("Error guardando rubro"); }
  };

  const guardarSubrubro = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('http://localhost:8001/api/GuardarSubRubro/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') { 
        setModalSubrubro(false); 
        fetchSubrubros(); 
      } else {
        alert(data.mensaje);
      }
    } catch (e) { alert("Error guardando subrubro"); }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
      
      {/* PANEL IZQUIERDO: RUBROS */}
      <div style={{ background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
          <h3 style={{ margin: 0, color: '#2c3e50' }}>🗂️ Rubros</h3>
          <button 
            onClick={() => { setFormData({ codigo: '', nombre: '', is_new: true }); setModalRubro(true); }} 
            style={{ padding: '8px 12px', background: '#2ecc71', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
            + Nuevo Rubro
          </button>
        </div>

        <div style={{ maxHeight: '65vh', overflowY: 'auto', border: '1px solid #eee', borderRadius: '4px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead style={{ background: '#ecf0f1', textAlign: 'left' }}>
              <tr><th style={{ padding: '10px' }}>Código</th><th style={{ padding: '10px' }}>Nombre</th><th style={{ padding: '10px' }}></th></tr>
            </thead>
            <tbody>
              {rubros.map(r => (
                <tr key={r.codigo} style={{ borderBottom: '1px solid #eee' }} onMouseOver={e => e.currentTarget.style.backgroundColor='#f9f9f9'} onMouseOut={e => e.currentTarget.style.backgroundColor='white'}>
                  <td style={{ padding: '10px', fontWeight: 'bold', width: '60px', color: '#2980b9' }}>{r.codigo}</td>
                  <td style={{ padding: '10px', fontWeight: 'bold' }}>{r.nombre}</td>
                  <td style={{ padding: '10px', textAlign: 'right' }}>
                    <button 
                      onClick={() => { setFormData({...r, is_new: false}); setModalRubro(true); }} 
                      style={{ padding: '4px 8px', background: '#f39c12', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer' }}>
                      ✏️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* PANEL DERECHO: SUBRUBROS */}
      <div style={{ background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
          <h3 style={{ margin: 0, color: '#2c3e50' }}>📑 Subrubros</h3>
          <button 
            onClick={() => { setFormData({ codigo: '', nombre: '', is_new: true }); setModalSubrubro(true); }} 
            style={{ padding: '8px 12px', background: '#3498db', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
            + Nuevo Subrubro
          </button>
        </div>

        <div style={{ maxHeight: '65vh', overflowY: 'auto', border: '1px solid #eee', borderRadius: '4px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead style={{ background: '#ecf0f1', textAlign: 'left' }}>
              <tr><th style={{ padding: '10px' }}>Código</th><th style={{ padding: '10px' }}>Nombre</th><th style={{ padding: '10px' }}></th></tr>
            </thead>
            <tbody>
              {subrubros.map(sr => (
                <tr key={sr.codigo} style={{ borderBottom: '1px solid #eee' }} onMouseOver={e => e.currentTarget.style.backgroundColor='#f9f9f9'} onMouseOut={e => e.currentTarget.style.backgroundColor='white'}>
                  <td style={{ padding: '10px', fontWeight: 'bold', width: '60px', color: '#8e44ad' }}>{sr.codigo}</td>
                  <td style={{ padding: '10px', fontWeight: 'bold' }}>{sr.nombre}</td>
                  <td style={{ padding: '10px', textAlign: 'right' }}>
                    <button 
                      onClick={() => { setFormData({...sr, is_new: false}); setModalSubrubro(true); }} 
                      style={{ padding: '4px 8px', background: '#f39c12', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer' }}>
                      ✏️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* --- MODAL RUBRO --- */}
      {modalRubro && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 100 }}>
          <form onSubmit={guardarRubro} style={{ background: 'white', padding: '30px', borderRadius: '8px', width: '400px' }}>
            <h3>{formData.is_new ? 'Nuevo Rubro' : 'Editar Rubro'}</h3>
            
            <label style={{ display: 'block', marginBottom: '15px' }}>
              <b style={{ fontSize: '12px', color: '#7f8c8d' }}>Código (Máx 4 let/num):</b>
              <input autoFocus={formData.is_new} disabled={!formData.is_new} required maxLength="4" type="text" value={formData.codigo} onChange={e => setFormData({...formData, codigo: e.target.value.toUpperCase()})} style={{ ...inputStyle, marginTop: '5px', background: !formData.is_new ? '#ecf0f1' : 'white' }} />
            </label>

            <label style={{ display: 'block', marginBottom: '10px' }}>
              <b style={{ fontSize: '12px', color: '#7f8c8d' }}>Nombre del Rubro:</b>
              <input autoFocus={!formData.is_new} required maxLength="20" type="text" value={formData.nombre} onChange={e => setFormData({...formData, nombre: e.target.value.toUpperCase()})} style={{ ...inputStyle, marginTop: '5px' }} />
            </label>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
              <button type="button" onClick={() => setModalRubro(false)} style={{ padding: '10px', cursor: 'pointer' }}>Cancelar</button>
              <button type="submit" style={{ padding: '10px 20px', background: '#2ecc71', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}>Guardar</button>
            </div>
          </form>
        </div>
      )}

      {/* --- MODAL SUBRUBRO --- */}
      {modalSubrubro && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 100 }}>
          <form onSubmit={guardarSubrubro} style={{ background: 'white', padding: '30px', borderRadius: '8px', width: '400px' }}>
            <h3>{formData.is_new ? 'Nuevo Subrubro' : 'Editar Subrubro'}</h3>
            
            <label style={{ display: 'block', marginBottom: '15px' }}>
              <b style={{ fontSize: '12px', color: '#7f8c8d' }}>Código (Máx 4 let/num):</b>
              <input autoFocus={formData.is_new} disabled={!formData.is_new} required maxLength="4" type="text" value={formData.codigo} onChange={e => setFormData({...formData, codigo: e.target.value.toUpperCase()})} style={{ ...inputStyle, marginTop: '5px', background: !formData.is_new ? '#ecf0f1' : 'white' }} />
            </label>

            <label style={{ display: 'block', marginBottom: '10px' }}>
              <b style={{ fontSize: '12px', color: '#7f8c8d' }}>Nombre del Subrubro:</b>
              <input autoFocus={!formData.is_new} required maxLength="20" type="text" value={formData.nombre} onChange={e => setFormData({...formData, nombre: e.target.value.toUpperCase()})} style={{ ...inputStyle, marginTop: '5px' }} />
            </label>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
              <button type="button" onClick={() => setModalSubrubro(false)} style={{ padding: '10px', cursor: 'pointer' }}>Cancelar</button>
              <button type="submit" style={{ padding: '10px 20px', background: '#3498db', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}>Guardar</button>
            </div>
          </form>
        </div>
      )}

    </div>
  );
}