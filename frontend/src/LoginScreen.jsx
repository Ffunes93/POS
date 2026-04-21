import { useState } from 'react'

export default function LoginScreen({ onLogin }) {
  const [form, setForm] = useState({ usuario: '', password: '' })
  const [error, setError] = useState('')

 const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const res = await fetch('http://localhost:8001/api/Login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      })
      const data = await res.json()
      
      if (data.status === 'success') {
        // ATENCIÓN ACÁ: Pasamos el usuario Y el estado de la caja
        onLogin(data.usuario, data.caja_id) 
      } else {
        setError(data.mensaje)
      }
    } catch (err) {
      setError('Error conectando al servidor de base de datos.')
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', paddingTop: '100px' }}>
      <form onSubmit={handleSubmit} style={{ background: 'white', padding: '30px', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', width: '300px' }}>
        <h2 style={{ textAlign: 'center', color: '#333' }}>POS - Login</h2>
        {error && <p style={{ color: 'red', fontSize: '14px', textAlign: 'center' }}>{error}</p>}
        
        <input type="text" placeholder="Usuario" required
               style={{ width: '100%', padding: '10px', margin: '10px 0', border: '1px solid #ccc', borderRadius: '4px', boxSizing: 'border-box' }}
               onChange={e => setForm({...form, usuario: e.target.value})} />
               
        <input type="password" placeholder="Contraseña" required
               style={{ width: '100%', padding: '10px', margin: '10px 0 20px 0', border: '1px solid #ccc', borderRadius: '4px', boxSizing: 'border-box' }}
               onChange={e => setForm({...form, password: e.target.value})} />
               
        <button type="submit" style={{ width: '100%', padding: '12px', background: '#3498db', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
          INGRESAR
        </button>
      </form>
    </div>
  )
}