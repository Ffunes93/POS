import { useState } from 'react'

export default function AperturaScreen({ user, onOpen }) {
  const [saldos, setSaldos] = useState({ billetes: 0, cupones: 0 })

  const abrirCaja = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/AbrirCaja/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cajero_id: user.id,
          saldo_ini_billetes: saldos.billetes,
          saldo_ini_cupones: saldos.cupones
        })
      })
      const data = await res.json()
      
      if (data.status === 'success') {
        onOpen(data.nro_caja)
      } else {
        alert(data.mensaje)
      }
    } catch (error) {
      alert("Error comunicando con el servidor.")
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', paddingTop: '50px' }}>
      <div style={{ background: 'white', padding: '30px', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', width: '400px' }}>
        <h3 style={{ textAlign: 'center', marginTop: 0 }}>Apertura de Caja</h3>
        <p style={{ textAlign: 'center', color: '#7f8c8d' }}>Declare su fondo de caja inicial</p>
        
        <label>Efectivo (Billetes):</label>
        <input type="number" placeholder="0.00" 
               style={{ width: '100%', padding: '10px', margin: '5px 0 15px 0', boxSizing: 'border-box' }}
               onChange={e => setSaldos({...saldos, billetes: e.target.value})} />

        <label>Cupones / Vouchers:</label>
        <input type="number" placeholder="0.00" 
               style={{ width: '100%', padding: '10px', margin: '5px 0 20px 0', boxSizing: 'border-box' }}
               onChange={e => setSaldos({...saldos, cupones: e.target.value})} />

        <button onClick={abrirCaja} style={{ width: '100%', padding: '12px', background: '#2ecc71', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
          ABRIR TURNO
        </button>
      </div>
    </div>
  )
}