import { useState } from 'react'

export default function CajaPOS() {
  const [estadoCaja, setEstadoCaja] = useState('CERRADA') // Puede ser 'CERRADA', 'ABIERTA', 'ARQUEO'
  const [nroCaja, setNroCaja] = useState(null)
  const [mensaje, setMensaje] = useState('')

  // Formularios
  const [saldoInicial, setSaldoInicial] = useState(0)
  
  const [arqueo, setArqueo] = useState({
    final_billetes: 0,
    final_cupones: 0,
    otros_ingresos: 0,
    otros_egresos: 0,
    deja_billetes: 0
  })

  const CAJERO_ID = 1 // Hardcodeado por ahora, luego se saca del login

  const abrirCaja = async () => {
    const res = await fetch('http://localhost:8001/api/AbrirCaja/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cajero_id: CAJERO_ID, saldo_ini_billetes: saldoInicial })
    })
    const data = await res.json()
    if (data.status === 'success') {
      setEstadoCaja('ABIERTA')
      setNroCaja(data.nro_caja)
      setMensaje('¡Caja abierta exitosamente! Lista para facturar.')
    } else {
      alert(data.mensaje)
    }
  }

  const cerrarCaja = async () => {
    const res = await fetch('http://localhost:8001/api/CerrarCaja/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cajero_id: CAJERO_ID,
        saldo_final_billetes: arqueo.final_billetes,
        saldo_final_cupones: arqueo.final_cupones,
        otros_ingresos: arqueo.otros_ingresos,
        otros_egresos: arqueo.otros_egresos,
        deja_billetes: arqueo.deja_billetes
      })
    })
    const data = await res.json()
    if (data.status === 'success') {
      setEstadoCaja('CERRADA')
      setNroCaja(null)
      alert(`Arqueo cerrado. Diferencia de caja: $${data.diferencia_efectivo}`)
      setMensaje('Turno finalizado.')
    }
  }

  return (
    <div style={{ maxWidth: '600px', margin: '40px auto', padding: '20px', border: '1px solid #ccc', borderRadius: '10px', backgroundColor: '#fdfdfd', fontFamily: 'sans-serif' }}>
      <h2 style={{ textAlign: 'center', color: '#2c3e50' }}>Control de Tesorería</h2>
      <div style={{ textAlign: 'center', marginBottom: '20px' }}>
        <span style={{ padding: '5px 15px', borderRadius: '20px', backgroundColor: estadoCaja === 'ABIERTA' ? '#2ecc71' : '#e74c3c', color: 'white', fontWeight: 'bold' }}>
          {estadoCaja === 'ABIERTA' ? `TURNO ABIERTO (Caja #${nroCaja})` : 'TURNO CERRADO'}
        </span>
      </div>

      {mensaje && <p style={{ color: 'blue', textAlign: 'center' }}>{mensaje}</p>}

      {estadoCaja === 'CERRADA' && (
        <div style={{ backgroundColor: '#ecf0f1', padding: '20px', borderRadius: '8px' }}>
          <h3>Apertura de Turno</h3>
          <label>Fondo de Caja (Efectivo Inicial): </label>
          <input 
            type="number" 
            style={{ width: '100%', padding: '10px', marginTop: '5px', marginBottom: '15px' }}
            onChange={e => setSaldoInicial(e.target.value)} 
            placeholder="0.00"
          />
          <button onClick={abrirCaja} style={{ width: '100%', padding: '15px', backgroundColor: '#3498db', color: 'white', border: 'none', fontWeight: 'bold', cursor: 'pointer' }}>
            ABRIR CAJA
          </button>
        </div>
      )}

      {estadoCaja === 'ABIERTA' && (
        <div style={{ backgroundColor: '#ecf0f1', padding: '20px', borderRadius: '8px' }}>
          <h3>Arqueo y Cierre de Turno</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div>
              <label>Efectivo Contado (Billetes):</label>
              <input type="number" onChange={e => setArqueo({...arqueo, final_billetes: e.target.value})} style={{ width: '100%', padding: '8px' }} />
            </div>
            <div>
              <label>Total Lote Tarjetas:</label>
              <input type="number" onChange={e => setArqueo({...arqueo, final_cupones: e.target.value})} style={{ width: '100%', padding: '8px' }} />
            </div>
            <div>
              <label>Otros Ingresos Extra:</label>
              <input type="number" onChange={e => setArqueo({...arqueo, otros_ingresos: e.target.value})} style={{ width: '100%', padding: '8px' }} />
            </div>
            <div>
              <label>Egresos / Retiros:</label>
              <input type="number" onChange={e => setArqueo({...arqueo, otros_egresos: e.target.value})} style={{ width: '100%', padding: '8px' }} />
            </div>
            <div style={{ gridColumn: '1 / span 2' }}>
              <label>Fondo que deja para el próximo turno:</label>
              <input type="number" onChange={e => setArqueo({...arqueo, deja_billetes: e.target.value})} style={{ width: '100%', padding: '8px' }} />
            </div>
          </div>

          <button onClick={cerrarCaja} style={{ width: '100%', padding: '15px', marginTop: '20px', backgroundColor: '#e67e22', color: 'white', border: 'none', fontWeight: 'bold', cursor: 'pointer' }}>
            CERRAR CAJA Y CALCULAR DIFERENCIA
          </button>
        </div>
      )}
    </div>
  )
}