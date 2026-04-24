import React, { useState, useEffect } from 'react';

export default function ConfigParametros() {
  const [cargando, setCargando] = useState(false);
  const [pestaña, setPestaña] = useState('EMPRESA');

  // ESTADO INICIAL CON LOS +60 CAMPOS DEL MODELO
  const [params, setParams] = useState({
    puntoventa: 1, nombreempresa: '', nombresucursal: '', cond_iva: 1,
    tipo_impresora: 0, modelo_impresora: 0, puerto_impresora: 0, ip_impresora: '',
    usa_consfinal: 0, usa_cod_barra: 0, nro_lote: 0, cajero_activo: 0,
    promo_mayorista: 0, promo_limite: 0, paso_imagen: '', paso_documentos: '',
    habilitapresupuesto: 0, pasologobig: '', pasologopeque: '', barra_longitud: 0,
    barra_inicio_desde: 0, barra_inicio_hasta: 0, barra_codigo_desde: 0, barra_codigo_hasta: 0,
    barra_ipc_desde: 0, barra_ipc_hasta: 0, barra_ipc: '', punto_de_venta_fiscal: '',
    limtepidedatosclientevarios: 0, usapreciomayoristacomodescuento: 0, limitevalidezcotizaciones: 0,
    canalventa: '', canalventagrupo: '', punto_de_venta_manual: '', webservicebejerman: '',
    webservicesync: '', webservicelicencias: '', imprime_rollo1_continuo2: 1, pedidos_codigonp: '',
    pedidos_codigocliente: 0, no_usa_percepcion: 0, no_traer_clientes: 0,
    clave: '', mailfran: '', actuhora: '', compro_inter: '', clavefec: '',
    mercadopago: 0, datosadicionales: 0, noesperacierrecaja: 0, vendedorcentralizado: 0,
    tipocodigobarra: 0, modulofe: '', barra_pesable: 0, multicajeros: 0, monotributo: 0,
    presu_en_ticket: 0, limite5329: 0, porce5329: 0, nompresu: '',
    // Fechas (manejadas como string YYYY-MM-DD para simplificar)
    fecha_cierre_zeta: '', fecha_actualiz_central: '', fecha_envio_data: '', fec_cajin: '',
    // Libres
    libre1: 0, libre2: 0, libre3: '', libre4: '', libre5: '', libre6: 0, libre7: 0, libre8: 0,
    libre9: 0, libre10: 0, libre11: 0, libre12: 0, libre13: 0, libre14: 0, libre15: 0, libre16: 0,
    libre17: 0, libre18: 0, libre19: 0
  });

  useEffect(() => {
    cargarParametros();
  }, []);

  const cargarParametros = async () => {
    setCargando(true);
    try {
      const res = await fetch('http://localhost:8001/api/GestionarParametros/');
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'success' && data.data) {
          // Parseamos nulos a vacíos/ceros para no romper los inputs de React
          const cleanData = Object.keys(data.data).reduce((acc, key) => {
            acc[key] = data.data[key] !== null ? data.data[key] : (typeof params[key] === 'string' ? '' : 0);
            return acc;
          }, {});
          setParams(prev => ({ ...prev, ...cleanData }));
        }
      }
    } catch (error) {
      console.error("Error al cargar parámetros:", error);
    }
    setCargando(false);
  };

  const guardarParametros = async (e) => {
    e.preventDefault();
    setCargando(true);
    try {
      const res = await fetch('http://localhost:8001/api/GestionarParametros/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        alert("✅ Parámetros guardados correctamente.");
      } else {
        alert("Error al guardar:\n" + JSON.stringify(data.errores, null, 2));
      }
    } catch (error) {
      alert("Error de conexión al guardar.");
    }
    setCargando(false);
  };

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    // Convierte a número si el input es tipo 'number'
    setParams({ ...params, [name]: type === 'number' ? Number(value) : value });
  };

  // Helper para generar inputs más rápido en el JSX
  const InputField = ({ label, name, type = "text" }) => (
    <div style={{ marginBottom: '10px' }}>
      <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', color: '#7f8c8d' }}>{label}</label>
      <input type={type} name={name} value={params[name] || ''} onChange={handleChange} style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} />
    </div>
  );

  return (
    <div style={{ display: 'flex', background: 'white', borderRadius: '8px', minHeight: '80vh', border: '1px solid #ddd' }}>
      
      {/* MENÚ LATERAL DE CATEGORÍAS */}
      <div style={{ width: '250px', background: '#f8f9fa', borderRight: '1px solid #ddd', padding: '20px' }}>
        <h3 style={{ marginTop: 0, color: '#2c3e50' }}>⚙️ Configuración</h3>
        {['EMPRESA', 'HARDWARE', 'OPERACION', 'BALANZAS', 'INTEGRACIONES', 'LIBRES'].map(cat => (
          <button 
            key={cat} 
            type="button"
            onClick={() => setPestaña(cat)}
            style={{ display: 'block', width: '100%', padding: '10px', marginBottom: '5px', textAlign: 'left', background: pestaña === cat ? '#3498db' : 'transparent', color: pestaña === cat ? 'white' : '#2c3e50', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* ÁREA DEL FORMULARIO */}
      <div style={{ flex: 1, padding: '20px', overflowY: 'auto' }}>
        <form onSubmit={guardarParametros}>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid #ecf0f1', paddingBottom: '10px', marginBottom: '20px' }}>
            <h2 style={{ margin: 0, color: '#2980b9' }}>Parámetros: {pestaña}</h2>
            <button type="submit" disabled={cargando} style={{ padding: '10px 20px', background: '#27ae60', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}>
              {cargando ? 'Guardando...' : '💾 Guardar Cambios'}
            </button>
          </div>

          {pestaña === 'EMPRESA' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <InputField label="ID Punto Venta (Principal)" name="puntoventa" type="number" />
              <InputField label="Nombre de la Empresa" name="nombreempresa" />
              <InputField label="Nombre de la Sucursal" name="nombresucursal" />
              <InputField label="Condición IVA (1=Inscrip, etc)" name="cond_iva" type="number" />
              <InputField label="¿Es Monotributo? (1=Si, 0=No)" name="monotributo" type="number" />
              <InputField label="Canal de Venta" name="canalventa" />
              <InputField label="Canal Venta Grupo" name="canalventagrupo" />
              <InputField label="Mail Administración" name="mailfran" />
              <InputField label="Clave Administrativa" name="clave" />
            </div>
          )}

          {pestaña === 'HARDWARE' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <InputField label="Tipo de Impresora (1=Fiscal Hasar)" name="tipo_impresora" type="number" />
              <InputField label="Modelo de Impresora" name="modelo_impresora" type="number" />
              <InputField label="Puerto (COM)" name="puerto_impresora" type="number" />
              <InputField label="IP Impresora" name="ip_impresora" />
              <InputField label="Punto de Venta Fiscal" name="punto_de_venta_fiscal" />
              <InputField label="Punto de Venta Manual" name="punto_de_venta_manual" />
              <InputField label="Imprime Rollo(1) o Continuo(2)" name="imprime_rollo1_continuo2" type="number" />
              <InputField label="¿Presupuesto en Ticket? (1=Si)" name="presu_en_ticket" type="number" />
            </div>
          )}

          {pestaña === 'OPERACION' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <InputField label="¿Pide datos a Cons. Final? (1=Si)" name="usa_consfinal" type="number" />
              <InputField label="Límite Monto Pide Datos" name="limtepidedatosclientevarios" type="number" />
              <InputField label="Habilita Presupuestos (1=Si)" name="habilitapresupuesto" type="number" />
              <InputField label="Nombre Comprobante Presu." name="nompresu" />
              <InputField label="Usa Precio Mayorista como Dto." name="usapreciomayoristacomodescuento" type="number" />
              <InputField label="Validez Cotizaciones (Días)" name="limitevalidezcotizaciones" type="number" />
              <InputField label="¿No espera cierre caja? (1=Si)" name="noesperacierrecaja" type="number" />
              <InputField label="¿Multicajeros activos? (1=Si)" name="multicajeros" type="number" />
              <InputField label="Cajero Activo (ID)" name="cajero_activo" type="number" />
              <InputField label="Vendedor Centralizado (1=Si)" name="vendedorcentralizado" type="number" />
            </div>
          )}

          {pestaña === 'BALANZAS' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <InputField label="Habilita Código de Barras (1=Si)" name="usa_cod_barra" type="number" />
              <InputField label="Tipo Cod. Barra Pesable" name="tipocodigobarra" type="number" />
              <InputField label="Código Barra Longitud Total" name="barra_longitud" type="number" />
              <InputField label="Barra: Inicio Desde" name="barra_inicio_desde" type="number" />
              <InputField label="Barra: Inicio Hasta" name="barra_inicio_hasta" type="number" />
              <InputField label="Barra: Cod. Artículo Desde" name="barra_codigo_desde" type="number" />
              <InputField label="Barra: Cod. Artículo Hasta" name="barra_codigo_hasta" type="number" />
              <InputField label="Barra: Precio/Peso Desde" name="barra_ipc_desde" type="number" />
              <InputField label="Barra: Precio/Peso Hasta" name="barra_ipc_hasta" type="number" />
              <InputField label="Barra IPC (Identificador)" name="barra_ipc" />
              <InputField label="Habilitar Barra Pesable (1=Si)" name="barra_pesable" type="number" />
            </div>
          )}

          {pestaña === 'INTEGRACIONES' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <InputField label="WebService Bejerman" name="webservicebejerman" />
              <InputField label="WebService Sync" name="webservicesync" />
              <InputField label="WebService Licencias" name="webservicelicencias" />
              <InputField label="Módulo FE (Fact. Electrónica)" name="modulofe" />
              <InputField label="Usa MercadoPago (1=Si)" name="mercadopago" type="number" />
              <InputField label="Ruta Imágenes" name="paso_imagen" />
              <InputField label="Ruta Documentos" name="paso_documentos" />
              <InputField label="Ruta Logo Grande" name="pasologobig" />
              <InputField label="Ruta Logo Pequeño" name="pasologopeque" />
            </div>
          )}

          {pestaña === 'LIBRES' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
              {[1, 2, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19].map(num => (
                <InputField key={num} label={`Libre Numérico ${num}`} name={`libre${num}`} type="number" />
              ))}
              <InputField label="Libre Texto 3" name="libre3" />
              <InputField label="Libre Texto 4" name="libre4" />
              <InputField label="Libre Texto 5" name="libre5" />
            </div>
          )}

        </form>
      </div>
    </div>
  );
}