import React, { useState, useEffect } from 'react';

export default function GestionTipocomp() {
  const [comprobantes, setComprobantes] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [modoEdicion, setModoEdicion] = useState(false);

  const estadoInicial = {
    id_compro: '', cod_compro: '', nom_compro: '', 
    ultnro: 0, copias: 1, ultdia: new Date().toISOString().split('T')[0]
  };
  const [formData, setFormData] = useState(estadoInicial);

  useEffect(() => {
    cargarComprobantes();
  }, []);

  const cargarComprobantes = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/GestionarTipocompCli/');
      const data = await res.json();
      if (data.status === 'success') {
        setComprobantes(data.data);
      }
    } catch (error) {
      console.error("Error al cargar:", error);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setCargando(true);
    
    const payload = { ...formData, ultdia: formData.ultdia + 'T00:00:00Z' };

    try {
      const url = 'http://localhost:8001/api/GestionarTipocompCli/';
      const method = modoEdicion ? 'PUT' : 'POST';
      
      const res = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        alert("✅ " + data.mensaje);
        setFormData(estadoInicial);
        setModoEdicion(false);
        cargarComprobantes();
      } else {
        alert("Error:\n" + JSON.stringify(data.errores || data.mensaje));
      }
    } catch (error) {
      alert("Error de conexión.");
    }
    setCargando(false);
  };

  const editar = (comp) => {
    setFormData({
      id_compro: comp.id_compro,
      cod_compro: comp.cod_compro,
      nom_compro: comp.nom_compro,
      ultnro: comp.ultnro,
      copias: comp.copias,
      ultdia: comp.ultdia ? comp.ultdia.split('T')[0] : ''
    });
    setModoEdicion(true);
  };

  return (
    <div style={{ display: 'flex', gap: '20px', minHeight: '80vh' }}>
      
      {/* FORMULARIO */}
      <div style={{ width: '350px', background: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #ddd' }}>
        <h3 style={{ marginTop: 0, color: '#2c3e50', borderBottom: '2px solid #ecf0f1', paddingBottom: '10px' }}>
          {modoEdicion ? '✏️ Ajustar Numeración' : '➕ Nuevo Comprobante'}
        </h3>
        
        {modoEdicion && (
          <div style={{ background: '#e8f8f5', padding: '10px', borderRadius: '4px', marginBottom: '15px', fontSize: '12px', color: '#16a085', border: '1px solid #1abc9c' }}>
            ℹ️ Por seguridad, en comprobantes existentes solo se puede modificar el último número emitido.
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <div>
            <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d' }}>ID (Único)</label>
            <input required type="number" name="id_compro" value={formData.id_compro} onChange={handleChange} disabled={modoEdicion} style={{ width: '100%', padding: '8px', boxSizing: 'border-box', background: modoEdicion ? '#ecf0f1' : 'white' }} />
          </div>
          <div>
            <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d' }}>Código (Ej: FA, NC)</label>
            <input required maxLength="2" type="text" name="cod_compro" value={formData.cod_compro} onChange={handleChange} disabled={modoEdicion} style={{ width: '100%', padding: '8px', boxSizing: 'border-box', textTransform: 'uppercase', background: modoEdicion ? '#ecf0f1' : 'white' }} />
          </div>
          <div>
            <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d' }}>Nombre Descriptivo</label>
            <input required maxLength="20" type="text" name="nom_compro" value={formData.nom_compro} onChange={handleChange} disabled={modoEdicion} style={{ width: '100%', padding: '8px', boxSizing: 'border-box', background: modoEdicion ? '#ecf0f1' : 'white' }} />
          </div>
          
          {/* 👇 ESTE ES EL ÚNICO CAMPO SIEMPRE HABILITADO */}
          <div style={{ background: '#fff3cd', padding: '10px', borderRadius: '4px', border: '1px solid #ffeeba' }}>
            <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#856404' }}>Último N° Emitido</label>
            <input required type="number" name="ultnro" value={formData.ultnro} onChange={handleChange} style={{ width: '100%', padding: '8px', boxSizing: 'border-box', fontWeight: 'bold' }} />
          </div>

          <div>
            <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d' }}>Cantidad de Copias</label>
            <input required type="number" name="copias" value={formData.copias} onChange={handleChange} disabled={modoEdicion} style={{ width: '100%', padding: '8px', boxSizing: 'border-box', background: modoEdicion ? '#ecf0f1' : 'white' }} />
          </div>
          <div>
            <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d' }}>Último Día de Emisión</label>
            <input required type="date" name="ultdia" value={formData.ultdia} onChange={handleChange} disabled={modoEdicion} style={{ width: '100%', padding: '8px', boxSizing: 'border-box', background: modoEdicion ? '#ecf0f1' : 'white' }} />
          </div>

          <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
            <button type="submit" disabled={cargando} style={{ flex: 1, padding: '10px', background: '#27ae60', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}>
              {cargando ? 'Guardando...' : '💾 Guardar'}
            </button>
            {modoEdicion && (
              <button type="button" onClick={() => { setModoEdicion(false); setFormData(estadoInicial); }} style={{ padding: '10px', background: '#95a5a6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                Cancelar
              </button>
            )}
          </div>
        </form>
      </div>

      {/* GRILLA */}
      <div style={{ flex: 1, background: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #ddd', overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ background: '#34495e', color: 'white', textAlign: 'left' }}>
              <th style={{ padding: '10px' }}>ID</th>
              <th style={{ padding: '10px' }}>Cód.</th>
              <th style={{ padding: '10px' }}>Nombre</th>
              <th style={{ padding: '10px', textAlign: 'right' }}>Último N°</th>
              <th style={{ padding: '10px', textAlign: 'center' }}>Ajustar</th>
            </tr>
          </thead>
          <tbody>
            {comprobantes.map(comp => (
              <tr key={comp.id_compro} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '10px', fontWeight: 'bold' }}>{comp.id_compro}</td>
                <td style={{ padding: '10px', color: '#2980b9', fontWeight: 'bold' }}>{comp.cod_compro}</td>
                <td style={{ padding: '10px' }}>{comp.nom_compro}</td>
                <td style={{ padding: '10px', textAlign: 'right', fontWeight: 'bold', color: '#e67e22' }}>{comp.ultnro}</td>
                <td style={{ padding: '10px', textAlign: 'center' }}>
                  {/* 👇 Botón de eliminar removido, solo queda el de editar */}
                  <button onClick={() => editar(comp)} style={{ background: '#f39c12', color: 'white', border: 'none', padding: '5px 15px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                    ✏️ Ajustar N°
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}