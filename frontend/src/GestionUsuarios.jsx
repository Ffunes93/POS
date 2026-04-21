import { useState, useEffect } from 'react';

export default function GestionUsuarios() {
  const [usuarios, setUsuarios] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // --- ESTADOS DEL MODAL ---
  const [mostrarModal, setMostrarModal] = useState(false);
  const [modoEdicion, setModoEdicion] = useState(false);
  
  // Estado para el formulario (usamos los mismos campos que tu serializador de Django)
  const formInicial = {
    id: null,
    nombre: '',
    apellido: '',
    nombrelogin: '',
    password: '',
    email: '',
    nivel_usuario: 1,
    cajero: 1,
    vendedor: 1,
    autorizador: 0
  };
  const [formData, setFormData] = useState(formInicial);

  // --- CARGA DE DATOS ---
  const fetchUsuarios = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8001/api/ListarUsuarios/');
      const data = await res.json();
      if (data.status === 'success') {
        setUsuarios(data.data);
      }
    } catch (error) {
      alert("Error cargando usuarios: " + error.message);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchUsuarios();
  }, []);

  // --- BAJA LÓGICA ---
  const toggleEstadoUsuario = async (id, estadoActual) => {
    const nuevoEstado = estadoActual === 0 ? 1 : 0;
    const accion = nuevoEstado === 1 ? "dar de baja" : "reactivar";
    
    if (!window.confirm(`¿Seguro que desea ${accion} este usuario?`)) return;

    try {
      const res = await fetch('http://localhost:8001/api/BajaUsuario/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id, no_activo: nuevoEstado })
      });
      const data = await res.json();
      if (data.status === 'success') {
        fetchUsuarios();
      } else {
        alert(data.mensaje);
      }
    } catch (error) {
      alert("Error de red.");
    }
  };

  // --- MANEJO DEL MODAL Y FORMULARIO ---
  const abrirModalNuevo = () => {
    setFormData(formInicial);
    setModoEdicion(false);
    setMostrarModal(true);
  };

  const abrirModalEditar = (user) => {
    // Llenamos el formulario con los datos del usuario seleccionado
    setFormData({
      id: user.id,
      nombre: user.nombre || '',
      apellido: user.apellido || '',
      nombrelogin: user.nombrelogin || '',
      password: '', // La dejamos vacía por seguridad, si la llena, la cambia
      email: user.email || '',
      nivel_usuario: user.nivel_usuario || 1,
      cajero: user.cajero || 0,
      vendedor: user.vendedor || 0,
      autorizador: user.autorizador || 0
    });
    setModoEdicion(true);
    setMostrarModal(true);
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? (checked ? 1 : 0) : value // Los checkboxes devuelven 1 o 0 para MySQL
    });
  };

  const guardarUsuario = async (e) => {
    e.preventDefault();
    
    // Determinamos si llamamos a Crear o a Editar (que crearemos en Django)
    const url = modoEdicion ? 'http://localhost:8001/api/EditarUsuario/' : 'http://localhost:8001/api/CrearUsuario/';

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      
      if (res.ok && data.status === 'success') {
        alert(`✅ ${data.mensaje}`);
        setMostrarModal(false);
        fetchUsuarios(); // Recargar grilla
      } else {
        alert("Error:\n" + JSON.stringify(data.mensaje || data.errores, null, 2));
      }
    } catch (error) {
      alert("Error comunicando con el servidor.");
    }
  };

  // --- RENDER ---
  if (loading) return <p style={{ padding: '20px' }}>Cargando módulo de gestión...</p>;

  return (
    <div style={{ padding: '20px', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', position: 'relative' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ margin: 0 }}>👥 Gestión de Usuarios</h2>
          <p style={{ color: '#7f8c8d', margin: '5px 0 0 0' }}>Administración de accesos y permisos del sistema.</p>
        </div>
        <button onClick={abrirModalNuevo} style={{ padding: '10px 15px', background: '#2ecc71', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
          + Nuevo Usuario
        </button>
      </div>

      {/* GRILLA DE USUARIOS */}
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
        <thead>
          <tr style={{ background: '#34495e', color: 'white' }}>
            <th style={{ padding: '10px' }}>ID</th>
            <th style={{ padding: '10px' }}>Login</th>
            <th style={{ padding: '10px' }}>Nombre</th>
            <th style={{ padding: '10px' }}>Nivel</th>
            <th style={{ padding: '10px' }}>Permisos</th>
            <th style={{ padding: '10px' }}>Estado</th>
            <th style={{ padding: '10px' }}>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {usuarios.map(u => (
            <tr key={u.id} style={{ borderBottom: '1px solid #eee', background: u.no_activo === 1 ? '#fdf0f0' : 'white' }}>
              <td style={{ padding: '10px' }}>{u.id}</td>
              <td style={{ padding: '10px', fontWeight: 'bold' }}>{u.nombrelogin}</td>
              <td style={{ padding: '10px' }}>{u.nombre} {u.apellido}</td>
              <td style={{ padding: '10px' }}>{u.nivel_usuario}</td>
              <td style={{ padding: '10px', fontSize: '12px' }}>
                {u.cajero === 1 && <span style={{ background: '#3498db', color: 'white', padding: '2px 5px', borderRadius: '3px', marginRight: '5px' }}>Cajero</span>}
                {u.vendedor === 1 && <span style={{ background: '#9b59b6', color: 'white', padding: '2px 5px', borderRadius: '3px', marginRight: '5px' }}>Vendedor</span>}
                {u.autorizador === 1 && <span style={{ background: '#f39c12', color: 'white', padding: '2px 5px', borderRadius: '3px' }}>Autorizador</span>}
              </td>
              <td style={{ padding: '10px' }}>
                {u.no_activo === 0 ? <span style={{ color: 'green', fontWeight: 'bold' }}>Activo</span> : <span style={{ color: 'red', fontWeight: 'bold' }}>Inactivo</span>}
              </td>
              <td style={{ padding: '10px' }}>
                <button onClick={() => abrirModalEditar(u)} style={{ padding: '5px 10px', background: '#3498db', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer', marginRight: '5px' }}>
                  ✏️ Editar
                </button>
                <button onClick={() => toggleEstadoUsuario(u.id, u.no_activo)} style={{ padding: '5px 10px', background: u.no_activo === 0 ? '#e74c3c' : '#f39c12', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer' }}>
                  {u.no_activo === 0 ? "⛔ Baja" : "♻️ Alta"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* --- MODAL DE CREACIÓN / EDICIÓN --- */}
      {mostrarModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ background: 'white', padding: '30px', borderRadius: '8px', width: '500px', boxShadow: '0 4px 15px rgba(0,0,0,0.2)' }}>
            <h3 style={{ marginTop: 0 }}>{modoEdicion ? '✏️ Editar Usuario' : '✨ Nuevo Usuario'}</h3>
            
            <form onSubmit={guardarUsuario}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '5px' }}>Login (Usuario):</label>
                  <input required type="text" name="nombrelogin" value={formData.nombrelogin} onChange={handleInputChange} disabled={modoEdicion} style={{ width: '100%', padding: '8px', boxSizing: 'border-box', background: modoEdicion ? '#eee' : 'white' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '5px' }}>Contraseña:</label>
                  <input required={!modoEdicion} type="password" name="password" value={formData.password} onChange={handleInputChange} placeholder={modoEdicion ? "(Dejar vacía para no cambiar)" : ""} style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '5px' }}>Nombre:</label>
                  <input required type="text" name="nombre" value={formData.nombre} onChange={handleInputChange} style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '5px' }}>Apellido:</label>
                  <input type="text" name="apellido" value={formData.apellido} onChange={handleInputChange} style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }} />
                </div>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '5px' }}>Nivel de Acceso (1 a 5):</label>
                <input required type="number" min="1" max="5" name="nivel_usuario" value={formData.nivel_usuario} onChange={handleInputChange} style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }} />
              </div>

              <div style={{ background: '#f9f9f9', padding: '15px', borderRadius: '4px', marginBottom: '20px' }}>
                <p style={{ margin: '0 0 10px 0', fontSize: '14px', fontWeight: 'bold' }}>Permisos Adicionales</p>
                <label style={{ marginRight: '15px', cursor: 'pointer' }}>
                  <input type="checkbox" name="cajero" checked={formData.cajero === 1} onChange={handleInputChange} /> Es Cajero
                </label>
                <label style={{ marginRight: '15px', cursor: 'pointer' }}>
                  <input type="checkbox" name="vendedor" checked={formData.vendedor === 1} onChange={handleInputChange} /> Es Vendedor
                </label>
                <label style={{ cursor: 'pointer' }}>
                  <input type="checkbox" name="autorizador" checked={formData.autorizador === 1} onChange={handleInputChange} /> Es Autorizador
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" onClick={() => setMostrarModal(false)} style={{ padding: '10px 15px', background: '#95a5a6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Cancelar</button>
                <button type="submit" style={{ padding: '10px 15px', background: '#3498db', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                  {modoEdicion ? 'Guardar Cambios' : 'Crear Usuario'}
                </button>
              </div>
            </form>

          </div>
        </div>
      )}

    </div>
  );
}