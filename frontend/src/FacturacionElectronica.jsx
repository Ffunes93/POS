import { useState, useEffect } from 'react';

const API = 'http://localhost:8001/api/fe';
const fmt = n => parseFloat(n || 0).toFixed(2);

const s = {
  card:  { background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', padding: '18px', marginBottom: '14px' },
  label: { display: 'block', fontSize: '11px', fontWeight: '700', color: '#57606a', marginBottom: '4px', textTransform: 'uppercase' },
  input: { width: '100%', padding: '9px 10px', border: '1px solid #d0d7de', borderRadius: '5px', fontSize: '14px', boxSizing: 'border-box' },
  btn:   (col, sec) => ({ padding: '9px 18px', background: sec ? '#fff' : col, color: sec ? col : '#fff', border: `1px solid ${col}`, borderRadius: '5px', cursor: 'pointer', fontWeight: '700', fontSize: '13px' }),
};

function Msg({ msg }) {
  if (!msg) return null;
  return (
    <div style={{ padding: '10px 16px', borderRadius: '6px', marginBottom: '12px', fontSize: '13px', fontWeight: '600',
      background: msg.tipo === 'ok' ? '#dafbe1' : '#ffebe9',
      color:      msg.tipo === 'ok' ? '#116329' : '#a40e26',
      border:     `1px solid ${msg.tipo === 'ok' ? '#56d364' : '#ff818266'}` }}>{msg.texto}</div>
  );
}

// ── Badge de estado ────────────────────────────────────────────────────────────
function Badge({ ok, textoOk, textoBad }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px',
      padding: '3px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: '700',
      background: ok ? '#dafbe1' : '#ffebe9',
      color:      ok ? '#116329' : '#cf222e' }}>
      {ok ? '✓' : '✗'} {ok ? textoOk : textoBad}
    </span>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// PANEL ESTADO
// ══════════════════════════════════════════════════════════════════════════════
function PanelEstado({ estado, onRecargar }) {
  const [testMsg, setTestMsg] = useState(null);
  const [testing, setTesting] = useState(false);

  const probar = async () => {
    setTesting(true); setTestMsg(null);
    const r = await fetch(`${API}/ProbarConexion/`, { method: 'POST' });
    const d = await r.json();
    setTestMsg({ tipo: d.status === 'success' ? 'ok' : 'error', texto: d.mensaje });
    setTesting(false);
  };

  return (
    <div>
      {/* Tarjetas de estado */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '12px', marginBottom: '20px' }}>
        {[
          { label: 'Configuración', val: estado.configurado, ok: estado.configurado, textoOk: 'OK', textoBad: 'Sin config' },
          { label: 'Ambiente',      val: estado.produccion ? '🟢 Producción' : '🟡 Homologación', ok: true },
          { label: 'Token AFIP',    val: estado.ta_activo, ok: estado.ta_activo, textoOk: 'Vigente', textoBad: 'Expirado/Nulo' },
          { label: 'Sin CAE',       val: estado.sin_cae, ok: estado.sin_cae === 0, textoOk: '0 pendientes', textoBad: `${estado.sin_cae} pendientes` },
        ].map(t => (
          <div key={t.label} style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', padding: '14px' }}>
            <div style={{ fontSize: '11px', color: '#57606a', fontWeight: '700', textTransform: 'uppercase', marginBottom: '6px' }}>{t.label}</div>
            {typeof t.ok === 'boolean'
              ? <Badge ok={t.ok} textoOk={t.textoOk} textoBad={t.textoBad} />
              : <span style={{ fontWeight: '700' }}>{t.val}</span>
            }
          </div>
        ))}
      </div>

      {/* Información de certificado */}
      <div style={s.card}>
        <div style={{ fontSize: '12px', fontWeight: '700', color: '#57606a', textTransform: 'uppercase', marginBottom: '10px' }}>
          Certificado configurado
        </div>
        <div style={{ fontSize: '13px', color: '#24292f', fontFamily: 'monospace',
          background: '#f6f8fa', padding: '8px 12px', borderRadius: '5px' }}>
          {estado.ruta_cert || '(sin ruta)'}
        </div>
        {estado.id_fnc && (
          <div style={{ marginTop: '6px', fontSize: '12px', color: '#57606a' }}>
            CUIT emisor: <b>{estado.id_fnc}</b>
          </div>
        )}
      </div>

      {/* Botón probar */}
      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
        <button onClick={probar} disabled={testing} style={s.btn('#0969da')}>
          {testing ? 'Probando...' : '🔌 Probar conexión WSFE'}
        </button>
        <button onClick={onRecargar} style={s.btn('#57606a', true)}>🔄 Actualizar estado</button>
      </div>
      {testMsg && <div style={{ marginTop: '12px' }}><Msg msg={testMsg} /></div>}

      {/* Guía rápida */}
      <div style={{ ...s.card, marginTop: '20px', background: '#fffbdd', borderColor: '#f0c000' }}>
        <div style={{ fontWeight: '700', fontSize: '13px', color: '#735c0f', marginBottom: '10px' }}>
          📋 Guía de configuración AFIP
        </div>
        <ol style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: '#735c0f', lineHeight: '1.8' }}>
          <li>Obtener certificado digital en <b>AFIP → Administración de Certificados Digitales</b></li>
          <li>Generar CSR con OpenSSL y subir a AFIP para obtener el <b>certificado .pem</b></li>
          <li>Combinar clave privada + certificado en un archivo <b>.pem</b> o <b>.p12</b></li>
          <li>Copiar el archivo al servidor Django (ej: <code>/documentos_json/cert.pem</code>)</li>
          <li>Configurar la ruta en la pestaña <b>Configuración</b></li>
          <li>Probar conexión con el botón de arriba</li>
        </ol>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// PANEL CONFIGURACIÓN
// ══════════════════════════════════════════════════════════════════════════════
function PanelConfiguracion({ estado }) {
  const [form, setForm] = useState({
    ruta_certificado: '',
    clave: '',
    produccion: false,
    razon_social: '',
    domicilio: '',
    condicion_iva: 'Responsable Inscripto',
    iibb: '',
    inicio_actividades: '',
    url_autentica: '',
    url_homologa: '',
    url_produccion: '',
  });
  const [msg,      setMsg]      = useState(null);
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    // Cargar valores actuales si existen
    if (estado.ruta_cert) {
      setForm(prev => ({ ...prev, ruta_certificado: estado.ruta_cert }));
    }
  }, [estado]);

  const guardar = async () => {
    setCargando(true); setMsg(null);
    const r = await fetch(`${API}/GuardarConfig/`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form),
    });
    const d = await r.json();
    setMsg({ tipo: d.status === 'success' ? 'ok' : 'error', texto: d.mensaje });
    setCargando(false);
  };

  const F = ({ label, name, type = 'text', placeholder }) => (
    <div>
      <label style={s.label}>{label}</label>
      <input type={type} style={s.input} placeholder={placeholder}
        value={form[name] || ''}
        onChange={e => setForm(prev => ({ ...prev, [name]: e.target.value }))} />
    </div>
  );

  return (
    <div>
      <Msg msg={msg} />

      <div style={{ ...s.card, borderLeft: form.produccion ? '4px solid #1a7f37' : '4px solid #f39c12' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
          <span style={{ fontWeight: '700', fontSize: '14px' }}>Ambiente de trabajo:</span>
          <button onClick={() => setForm(p => ({ ...p, produccion: false }))}
            style={{ ...s.btn(form.produccion ? '#d0d7de' : '#f39c12', form.produccion), fontSize: '12px', padding: '6px 14px' }}>
            🟡 Homologación (Pruebas)
          </button>
          <button onClick={() => setForm(p => ({ ...p, produccion: true }))}
            style={{ ...s.btn(!form.produccion ? '#d0d7de' : '#1a7f37', !form.produccion), fontSize: '12px', padding: '6px 14px' }}>
            🟢 Producción
          </button>
        </div>
        {form.produccion && (
          <div style={{ background: '#ffebe9', border: '1px solid #ff818266', borderRadius: '5px', padding: '10px', fontSize: '12px', color: '#cf222e', fontWeight: '600' }}>
            ⚠️ MODO PRODUCCIÓN: Los CAE generados serán REALES y válidos ante AFIP.
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
        <div style={s.card}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#57606a', textTransform: 'uppercase', marginBottom: '12px' }}>
            Certificado Digital
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <F label="Ruta del certificado (.pem o .p12) en el servidor"
               name="ruta_certificado" placeholder="/documentos_json/cert.pem" />
            <F label="Contraseña del certificado (si es .p12)" name="clave" type="password" />
          </div>
        </div>

        <div style={s.card}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#57606a', textTransform: 'uppercase', marginBottom: '12px' }}>
            Datos del Emisor
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <F label="Razón Social" name="razon_social" />
            <F label="Domicilio Fiscal" name="domicilio" />
            <F label="Condición IVA" name="condicion_iva" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <F label="N° IIBB" name="iibb" />
              <F label="Inicio Actividades" name="inicio_actividades" placeholder="01/01/2020" />
            </div>
          </div>
        </div>

        <div style={{ ...s.card, gridColumn: 'span 2' }}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#57606a', textTransform: 'uppercase', marginBottom: '12px' }}>
            URLs de servicios AFIP (dejar en blanco para usar valores por defecto)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
            <F label="WSAA (autenticación)" name="url_autentica" placeholder="Automático" />
            <F label="WSFE Homologación" name="url_homologa" placeholder="Automático" />
            <F label="WSFE Producción" name="url_produccion" placeholder="Automático" />
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button onClick={guardar} disabled={cargando} style={s.btn('#2da44e')}>
          {cargando ? 'Guardando...' : '💾 Guardar configuración'}
        </button>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// PANEL SIN CAE (reenvíos)
// ══════════════════════════════════════════════════════════════════════════════
function PanelSinCAE() {
  const [lista,    setLista]    = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [msgs,     setMsgs]     = useState({});    // { movim: { tipo, texto } }
  const [enviando, setEnviando] = useState({});

  const cargar = async () => {
    setLoading(true);
    const r = await fetch(`${API}/ListarSinCAE/`);
    const d = await r.json();
    if (d.status === 'success') setLista(d.data);
    setLoading(false);
  };

  useEffect(() => { cargar(); }, []);

  const solicitarCAE = async (movim) => {
    setEnviando(p => ({ ...p, [movim]: true }));
    setMsgs(p => ({ ...p, [movim]: null }));
    const r = await fetch(`${API}/SolicitarCAE/`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ movim }),
    });
    const d = await r.json();
    const ok = r.ok && d.status === 'success';
    setMsgs(p => ({ ...p, [movim]: { tipo: ok ? 'ok' : 'error', texto: ok ? `CAE: ${d.cae} (Vto: ${d.vto_cae})` : d.mensaje } }));
    if (ok) cargar();
    setEnviando(p => ({ ...p, [movim]: false }));
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div>
          <h3 style={{ margin: 0, color: '#24292f' }}>Comprobantes sin CAE</h3>
          <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#57606a' }}>
            Facturas ya ingresadas que no obtuvieron CAE (timeout, error de conexión, etc.)
          </p>
        </div>
        <button onClick={cargar} style={s.btn('#57606a', true)}>🔄 Actualizar</button>
      </div>

      {loading ? <div style={{ textAlign: 'center', padding: '30px', color: '#57606a' }}>Cargando...</div> : (
        lista.length === 0 ? (
          <div style={{ background: '#dafbe1', border: '1px solid #56d364', borderRadius: '8px',
            padding: '24px', textAlign: 'center', color: '#116329', fontWeight: '700' }}>
            ✅ Todos los comprobantes tienen CAE. ¡Todo en orden!
          </div>
        ) : (
          <div style={{ background: '#fff', border: '1px solid #d0d7de', borderRadius: '8px', overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: '#f6f8fa', borderBottom: '2px solid #d0d7de', textAlign: 'left' }}>
                  <th style={{ padding: '10px 12px' }}>Movim.</th>
                  <th style={{ padding: '10px 12px' }}>Comprobante</th>
                  <th style={{ padding: '10px 12px' }}>Fecha</th>
                  <th style={{ padding: '10px 12px' }}>Cliente</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>Total</th>
                  <th style={{ padding: '10px 12px', textAlign: 'center' }}>Acción</th>
                </tr>
              </thead>
              <tbody>
                {lista.map(v => (
                  <>
                    <tr key={v.movim} style={{ borderBottom: msgs[v.movim] ? 'none' : '1px solid #f0f0f0' }}>
                      <td style={{ padding: '10px 12px', color: '#57606a' }}>{v.movim}</td>
                      <td style={{ padding: '10px 12px', fontWeight: '700', color: '#cf222e' }}>
                        {v.comprobante_tipo}{v.comprobante_letra} {String(v.nro_comprob).padStart(8,'0')}
                        <div style={{ fontSize: '11px', color: '#57606a' }}>Pto: {v.comprobante_pto_vta}</div>
                      </td>
                      <td style={{ padding: '10px 12px', color: '#57606a' }}>
                        {v.fecha_fact ? new Date(v.fecha_fact).toLocaleDateString() : '-'}
                      </td>
                      <td style={{ padding: '10px 12px' }}>{v.nombre_cliente}</td>
                      <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: '700' }}>
                        ${fmt(v.tot_general)}
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                        <button onClick={() => solicitarCAE(v.movim)}
                          disabled={!!enviando[v.movim]}
                          style={s.btn('#8250df')}>
                          {enviando[v.movim] ? '⏳ Enviando...' : '📡 Solicitar CAE'}
                        </button>
                      </td>
                    </tr>
                    {msgs[v.movim] && (
                      <tr key={`msg-${v.movim}`}>
                        <td colSpan={6} style={{ padding: '0 12px 10px', borderBottom: '1px solid #f0f0f0' }}>
                          <div style={{ padding: '8px 12px', borderRadius: '5px', fontSize: '12px', fontWeight: '600',
                            background: msgs[v.movim].tipo === 'ok' ? '#dafbe1' : '#ffebe9',
                            color:      msgs[v.movim].tipo === 'ok' ? '#116329' : '#a40e26' }}>
                            {msgs[v.movim].tipo === 'ok' ? '✅' : '❌'} {msgs[v.movim].texto}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// MÓDULO PRINCIPAL
// ══════════════════════════════════════════════════════════════════════════════
export default function FacturacionElectronica() {
  const [sub,    setSub]    = useState('ESTADO');
  const [estado, setEstado] = useState({
    configurado: false, produccion: false, ta_activo: false, sin_cae: 0,
    ruta_cert: '', id_fnc: '',
  });

  const cargarEstado = async () => {
    try {
      const r = await fetch(`${API}/Estado/`);
      const d = await r.json();
      if (d.status === 'success') setEstado(d);
    } catch {}
  };

  useEffect(() => { cargarEstado(); }, []);

  const MENU = [
    ['ESTADO',  '📊 Estado'],
    ['SINCAE',  `⚠️ Sin CAE${estado.sin_cae > 0 ? ` (${estado.sin_cae})` : ''}`],
    ['CONFIG',  '⚙️ Configuración'],
  ];

  return (
    <div style={{ background: '#f6f8fa', minHeight: '100%', padding: '4px' }}>
      {/* Header con badge de ambiente */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px', color: '#24292f', fontWeight: '700' }}>
            🏛 Facturación Electrónica AFIP
          </h2>
          <div style={{ marginTop: '4px' }}>
            <Badge
              ok={estado.ta_activo}
              textoOk={`Token vigente — ${estado.produccion ? 'Producción' : 'Homologación'}`}
              textoBad="Token expirado o sin configurar"
            />
          </div>
        </div>
        {estado.sin_cae > 0 && (
          <div style={{ background: '#ffebe9', border: '1px solid #ff818266', borderRadius: '8px',
            padding: '10px 16px', color: '#cf222e', fontWeight: '700', fontSize: '14px' }}>
            ⚠️ {estado.sin_cae} comprobante{estado.sin_cae > 1 ? 's' : ''} sin CAE
          </div>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        {MENU.map(([id, label]) => (
          <button key={id} onClick={() => setSub(id)} style={{
            padding: '8px 16px', borderRadius: '5px', cursor: 'pointer', fontWeight: '700', fontSize: '13px',
            background: sub === id ? (id === 'SINCAE' && estado.sin_cae > 0 ? '#cf222e' : '#0969da') : '#fff',
            color:      sub === id ? '#fff' : '#57606a',
            border:     `1px solid ${sub === id ? (id === 'SINCAE' && estado.sin_cae > 0 ? '#cf222e' : '#0969da') : '#d0d7de'}`,
          }}>{label}</button>
        ))}
      </div>

      {sub === 'ESTADO' && <PanelEstado estado={estado} onRecargar={cargarEstado} />}
      {sub === 'SINCAE' && <PanelSinCAE />}
      {sub === 'CONFIG' && <PanelConfiguracion estado={estado} />}
    </div>
  );
}