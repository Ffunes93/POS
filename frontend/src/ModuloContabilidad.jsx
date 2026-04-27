// ModuloContabilidad.jsx
import { useState, useEffect, useCallback } from "react";

const API = "http://localhost:8001/api/contab";
const fmt = (n) =>
  Number(n || 0).toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const hoy = () => new Date().toISOString().slice(0, 10);
const primerDiaMes = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-01`;
};

// ── Helpers UI ───────────────────────────────────────────────────────────────
const Badge = ({ ok }) => (
  <span style={{
    background: ok ? "#d1fae5" : "#fee2e2",
    color: ok ? "#065f46" : "#991b1b",
    padding: "2px 10px", borderRadius: 12, fontSize: 12, fontWeight: 700,
  }}>
    {ok ? "✓ Cuadra" : "✗ Descuadrado"}
  </span>
);

const Card = ({ children, style }) => (
  <div style={{
    background: "#fff", borderRadius: 10,
    boxShadow: "0 1px 4px rgba(0,0,0,.10)",
    padding: 20, marginBottom: 16, ...style,
  }}>
    {children}
  </div>
);

const Th = ({ children, right }) => (
  <th style={{
    background: "#f8f9fa", padding: "8px 12px",
    textAlign: right ? "right" : "left",
    fontSize: 12, fontWeight: 700, color: "#555",
    borderBottom: "2px solid #dee2e6",
  }}>
    {children}
  </th>
);
const Td = ({ children, right, bold, color }) => (
  <td style={{
    padding: "7px 12px", fontSize: 13,
    textAlign: right ? "right" : "left",
    fontWeight: bold ? 700 : 400,
    color: color || "inherit",
    borderBottom: "1px solid #f0f0f0",
  }}>
    {children}
  </td>
);

const FiltroFechas = ({ desde, hasta, onDesde, onHasta, onBuscar, cargando }) => (
  <div style={{ display: "flex", gap: 10, alignItems: "flex-end", flexWrap: "wrap", marginBottom: 16 }}>
    <label style={{ fontSize: 13 }}>
      Desde<br />
      <input type="date" value={desde} onChange={e => onDesde(e.target.value)}
        style={{ padding: "6px 10px", border: "1px solid #ccc", borderRadius: 6 }} />
    </label>
    <label style={{ fontSize: 13 }}>
      Hasta<br />
      <input type="date" value={hasta} onChange={e => onHasta(e.target.value)}
        style={{ padding: "6px 10px", border: "1px solid #ccc", borderRadius: 6 }} />
    </label>
    <button onClick={onBuscar} disabled={cargando}
      style={{
        padding: "7px 20px", background: "#2563eb", color: "#fff",
        border: "none", borderRadius: 6, cursor: "pointer", fontWeight: 600,
      }}>
      {cargando ? "..." : "Consultar"}
    </button>
  </div>
);

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: Sincronización
// ═══════════════════════════════════════════════════════════════════════════════
function PanelSincronizar() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const sincronizar = async () => {
    if (!window.confirm("¿Generar asientos para todas las operaciones que aún no tienen asiento contable?")) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/Sincronizar/`, { method: "POST",
        headers: { "Content-Type": "application/json" } });
      const d = await r.json();
      setResult(d);
    } catch { setResult({ error: "Error de conexión" }); }
    setLoading(false);
  };

  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>Sincronización de Asientos</h3>
      <p style={{ fontSize: 13, color: "#666", marginBottom: 20 }}>
        Genera automáticamente los asientos contables para todas las ventas, compras y recibos
        registrados que todavía no tienen asiento. Es seguro ejecutarlo múltiples veces.
      </p>

      <div style={{
        background: "#eff6ff", border: "1px solid #bfdbfe",
        borderRadius: 8, padding: 16, marginBottom: 20, fontSize: 13,
      }}>
        <strong>¿Qué se genera?</strong>
        <ul style={{ margin: "8px 0 0 0", paddingLeft: 18 }}>
          <li>Venta contado → DB Caja / CR Ventas + IVA Débito</li>
          <li>Venta cta. cte. → DB Deudores / CR Ventas + IVA Débito</li>
          <li>Compra contado → DB Mercaderías + IVA CF / CR Caja</li>
          <li>Compra cta. cte. → DB Mercaderías + IVA CF / CR Proveedores</li>
          <li>Recibo de cobro → DB Caja / CR Deudores</li>
        </ul>
      </div>

      <button onClick={sincronizar} disabled={loading}
        style={{
          padding: "10px 28px", background: loading ? "#94a3b8" : "#0f766e",
          color: "#fff", border: "none", borderRadius: 8,
          cursor: loading ? "not-allowed" : "pointer", fontWeight: 700, fontSize: 14,
        }}>
        {loading ? "Procesando..." : "Sincronizar Ahora"}
      </button>

      {result && (
        <div style={{
          marginTop: 20, padding: 16,
          background: result.error ? "#fef2f2" : "#f0fdf4",
          border: `1px solid ${result.error ? "#fca5a5" : "#86efac"}`,
          borderRadius: 8, fontSize: 13,
        }}>
          {result.error ? (
            <span style={{ color: "#dc2626" }}>❌ {result.error}</span>
          ) : (
            <>
              <div style={{ fontWeight: 700, color: "#166534", marginBottom: 8 }}>
                ✓ Sincronización completada — {result.total} asientos generados
              </div>
              <div>Ventas: <strong>{result.generados?.ventas}</strong></div>
              <div>Compras: <strong>{result.generados?.compras}</strong></div>
              <div>Recibos: <strong>{result.generados?.recibos}</strong></div>
              {result.generados?.errores?.length > 0 && (
                <div style={{ color: "#b45309", marginTop: 8 }}>
                  Advertencias: {result.generados.errores.join(" | ")}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: Libro Diario
// ═══════════════════════════════════════════════════════════════════════════════
function PanelLibroDiario() {
  const [desde, setDesde] = useState(primerDiaMes());
  const [hasta, setHasta] = useState(hoy());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandido, setExpandido] = useState({});

  const buscar = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/LibroDiario/?desde=${desde}&hasta=${hasta}`);
      setData(await r.json());
    } catch { }
    setLoading(false);
  };

  const toggle = (id) => setExpandido(p => ({ ...p, [id]: !p[id] }));

  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>Libro Diario</h3>
      <FiltroFechas desde={desde} hasta={hasta} onDesde={setDesde} onHasta={setHasta}
        onBuscar={buscar} cargando={loading} />

      {data && (
        <>
          <div style={{ display: "flex", gap: 16, marginBottom: 16, flexWrap: "wrap" }}>
            {[
              { label: "Total Debe", val: data.total_debe, color: "#1d4ed8" },
              { label: "Total Haber", val: data.total_haber, color: "#065f46" },
              { label: "Asientos", val: data.asientos?.length, color: "#7c3aed", nofmt: true },
            ].map(x => (
              <div key={x.label} style={{
                background: "#f8fafc", borderRadius: 8, padding: "10px 20px",
                textAlign: "center", flex: "1 1 140px",
              }}>
                <div style={{ fontSize: 11, color: "#888" }}>{x.label}</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: x.color }}>
                  {x.nofmt ? x.val : `$${fmt(x.val)}`}
                </div>
              </div>
            ))}
            <div style={{ display: "flex", alignItems: "center" }}>
              <Badge ok={data.cuadra} />
            </div>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <Th>#</Th><Th>Fecha</Th><Th>Descripción</Th><Th>Origen</Th>
                  <Th right>Debe</Th><Th right>Haber</Th><Th></Th>
                </tr>
              </thead>
              <tbody>
                {data.asientos?.map(a => (
                  <>
                    <tr key={a.id} style={{ cursor: "pointer", background: expandido[a.id] ? "#f0f9ff" : "" }}
                      onClick={() => toggle(a.id)}>
                      <Td>{a.id}</Td>
                      <Td>{a.fecha}</Td>
                      <Td>{a.descripcion}</Td>
                      <Td>
                        <span style={{
                          background: { VTA: "#dbeafe", CMP: "#fef9c3", REC: "#d1fae5", AJU: "#f3e8ff", ANU: "#fee2e2" }[a.origen] || "#f1f5f9",
                          padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 600,
                        }}>{a.origen}</span>
                      </Td>
                      <Td right bold>{fmt(a.lineas?.reduce((s, l) => s + l.debe, 0))}</Td>
                      <Td right bold>{fmt(a.lineas?.reduce((s, l) => s + l.haber, 0))}</Td>
                      <Td>{expandido[a.id] ? "▲" : "▼"}</Td>
                    </tr>
                    {expandido[a.id] && a.lineas?.map((l, i) => (
                      <tr key={i} style={{ background: "#f8fafc" }}>
                        <Td></Td>
                        <Td></Td>
                        <Td><span style={{ marginLeft: 24, color: "#555", fontSize: 12 }}>
                          [{l.cuenta}] {l.nombre} {l.descripcion ? `— ${l.descripcion}` : ""}
                        </span></Td>
                        <Td></Td>
                        <Td right>{l.debe > 0 ? fmt(l.debe) : ""}</Td>
                        <Td right>{l.haber > 0 ? fmt(l.haber) : ""}</Td>
                        <Td></Td>
                      </tr>
                    ))}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: Mayor de Cuentas
// ═══════════════════════════════════════════════════════════════════════════════
function PanelMayorCuenta() {
  const [cuentas, setCuentas] = useState([]);
  const [cuenta, setCuenta] = useState("");
  const [desde, setDesde] = useState(primerDiaMes());
  const [hasta, setHasta] = useState(hoy());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API}/PlanCuentas/?imputables=1`)
      .then(r => r.json()).then(setCuentas).catch(() => {});
  }, []);

  const buscar = async () => {
    if (!cuenta) return alert("Seleccione una cuenta");
    setLoading(true);
    try {
      const r = await fetch(`${API}/MayorCuenta/?cuenta=${cuenta}&desde=${desde}&hasta=${hasta}`);
      setData(await r.json());
    } catch { }
    setLoading(false);
  };

  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>Mayor de Cuentas</h3>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16, alignItems: "flex-end" }}>
        <label style={{ fontSize: 13, flex: "2 1 260px" }}>
          Cuenta<br />
          <select value={cuenta} onChange={e => setCuenta(e.target.value)}
            style={{ width: "100%", padding: "7px 10px", border: "1px solid #ccc", borderRadius: 6 }}>
            <option value="">— seleccionar —</option>
            {cuentas.map(c => (
              <option key={c.codigo} value={c.codigo}>{c.codigo} — {c.nombre}</option>
            ))}
          </select>
        </label>
        <label style={{ fontSize: 13 }}>
          Desde<br />
          <input type="date" value={desde} onChange={e => setDesde(e.target.value)}
            style={{ padding: "6px 10px", border: "1px solid #ccc", borderRadius: 6 }} />
        </label>
        <label style={{ fontSize: 13 }}>
          Hasta<br />
          <input type="date" value={hasta} onChange={e => setHasta(e.target.value)}
            style={{ padding: "6px 10px", border: "1px solid #ccc", borderRadius: 6 }} />
        </label>
        <button onClick={buscar} disabled={loading}
          style={{ padding: "7px 20px", background: "#2563eb", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontWeight: 600 }}>
          {loading ? "..." : "Consultar"}
        </button>
      </div>

      {data && (
        <>
          <div style={{ marginBottom: 12, padding: "10px 16px", background: "#f0f9ff", borderRadius: 8 }}>
            <strong>{data.cuenta}</strong> — {data.nombre} &nbsp;|&nbsp;
            Saldo final: <strong style={{ color: "#1d4ed8" }}>${fmt(data.saldo_final)}</strong>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <Th>Fecha</Th><Th>#Asiento</Th><Th>Descripción</Th><Th>Origen</Th>
                  <Th right>Debe</Th><Th right>Haber</Th><Th right>Saldo</Th>
                </tr>
              </thead>
              <tbody>
                {data.movimientos?.map((m, i) => (
                  <tr key={i}>
                    <Td>{m.fecha}</Td>
                    <Td>{m.asiento_id}</Td>
                    <Td>{m.descripcion}</Td>
                    <Td><span style={{ fontSize: 11 }}>{m.origen}</span></Td>
                    <Td right>{m.debe > 0 ? fmt(m.debe) : "-"}</Td>
                    <Td right>{m.haber > 0 ? fmt(m.haber) : "-"}</Td>
                    <Td right bold color={m.saldo < 0 ? "#dc2626" : "#1d4ed8"}>${fmt(m.saldo)}</Td>
                  </tr>
                ))}
                {!data.movimientos?.length && (
                  <tr><Td colSpan={7} style={{ textAlign: "center", color: "#888" }}>Sin movimientos en el período</Td></tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: Balance de Sumas y Saldos
// ═══════════════════════════════════════════════════════════════════════════════
function PanelBalanceSumasYSaldos() {
  const [desde, setDesde] = useState(primerDiaMes());
  const [hasta, setHasta] = useState(hoy());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const COLORES_TIPO = { A: "#dbeafe", P: "#fce7f3", PN: "#d1fae5", I: "#fef9c3", E: "#fee2e2" };

  const buscar = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/BalanceSumasYSaldos/?desde=${desde}&hasta=${hasta}`);
      setData(await r.json());
    } catch { }
    setLoading(false);
  };

  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>Balance de Sumas y Saldos</h3>
      <FiltroFechas desde={desde} hasta={hasta} onDesde={setDesde} onHasta={setHasta}
        onBuscar={buscar} cargando={loading} />

      {data && (
        <>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <Th>Código</Th><Th>Cuenta</Th><Th>Tipo</Th>
                  <Th right>Suma Debe</Th><Th right>Suma Haber</Th>
                  <Th right>Saldo Deudor</Th><Th right>Saldo Acreedor</Th>
                </tr>
              </thead>
              <tbody>
                {data.filas?.map(f => (
                  <tr key={f.codigo}>
                    <Td>{f.codigo}</Td>
                    <Td>{f.nombre}</Td>
                    <Td>
                      <span style={{
                        background: COLORES_TIPO[f.tipo] || "#f1f5f9",
                        padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 600,
                      }}>{f.tipo}</span>
                    </Td>
                    <Td right>{fmt(f.suma_debe)}</Td>
                    <Td right>{fmt(f.suma_haber)}</Td>
                    <Td right>{f.saldo_deudor > 0 ? fmt(f.saldo_deudor) : ""}</Td>
                    <Td right>{f.saldo_acreedor > 0 ? fmt(f.saldo_acreedor) : ""}</Td>
                  </tr>
                ))}
                {/* Totales */}
                <tr style={{ background: "#f1f5f9", fontWeight: 700 }}>
                  <Td colSpan={3} bold>TOTALES</Td>
                  <Td right bold>{fmt(data.totales?.suma_debe)}</Td>
                  <Td right bold>{fmt(data.totales?.suma_haber)}</Td>
                  <Td right bold>{fmt(data.totales?.saldo_deudor)}</Td>
                  <Td right bold>{fmt(data.totales?.saldo_acreedor)}</Td>
                </tr>
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: 12 }}>
            <Badge ok={data.cuadra} />
          </div>
        </>
      )}
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: Estado de Resultados
// ═══════════════════════════════════════════════════════════════════════════════
function PanelEstadoResultados() {
  const [desde, setDesde] = useState(primerDiaMes());
  const [hasta, setHasta] = useState(hoy());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const buscar = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/EstadoResultados/?desde=${desde}&hasta=${hasta}`);
      setData(await r.json());
    } catch { }
    setLoading(false);
  };

  const SeccionPL = ({ titulo, grupos, total, colorTotal }) => (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontWeight: 700, fontSize: 14, color: "#374151", marginBottom: 8,
        borderBottom: "2px solid #e5e7eb", paddingBottom: 4 }}>
        {titulo}
      </div>
      {grupos?.map((g, i) => (
        <div key={i} style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 12, color: "#6b7280", fontWeight: 600, marginBottom: 4 }}>{g.nombre}</div>
          {g.cuentas.map((c, j) => (
            <div key={j} style={{ display: "flex", justifyContent: "space-between", padding: "3px 16px", fontSize: 13 }}>
              <span style={{ color: "#4b5563" }}>{c.nombre}</span>
              <span>${fmt(c.importe)}</span>
            </div>
          ))}
        </div>
      ))}
      <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0",
        borderTop: "1px solid #e5e7eb", fontWeight: 700, fontSize: 14, color: colorTotal }}>
        <span>Total {titulo}</span>
        <span>${fmt(total)}</span>
      </div>
    </div>
  );

  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>Estado de Resultados</h3>
      <FiltroFechas desde={desde} hasta={hasta} onDesde={setDesde} onHasta={setHasta}
        onBuscar={buscar} cargando={loading} />

      {data && (
        <div style={{ maxWidth: 600 }}>
          <SeccionPL titulo="Ingresos" grupos={data.ingresos?.grupos}
            total={data.ingresos?.total} colorTotal="#065f46" />
          <SeccionPL titulo="Egresos" grupos={data.egresos?.grupos}
            total={data.egresos?.total} colorTotal="#991b1b" />

          <div style={{
            background: data.resultado >= 0 ? "#d1fae5" : "#fee2e2",
            border: `2px solid ${data.resultado >= 0 ? "#6ee7b7" : "#fca5a5"}`,
            borderRadius: 10, padding: "14px 20px",
            display: "flex", justifyContent: "space-between", alignItems: "center",
          }}>
            <span style={{ fontWeight: 700, fontSize: 16 }}>
              {data.resultado >= 0 ? "✓ Resultado Positivo" : "✗ Resultado Negativo"}
            </span>
            <span style={{
              fontWeight: 800, fontSize: 22,
              color: data.resultado >= 0 ? "#065f46" : "#991b1b",
            }}>
              ${fmt(data.resultado)}
            </span>
          </div>
        </div>
      )}
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: Balance General
// ═══════════════════════════════════════════════════════════════════════════════
function PanelBalanceGeneral() {
  const [hasta, setHasta] = useState(hoy());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const buscar = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/BalanceGeneral/?hasta=${hasta}`);
      setData(await r.json());
    } catch { }
    setLoading(false);
  };

  const Seccion = ({ titulo, grupos, total, color }) => (
    <div style={{ flex: "1 1 260px" }}>
      <div style={{ fontWeight: 700, fontSize: 13, color: "#fff",
        background: color, padding: "8px 14px", borderRadius: "8px 8px 0 0" }}>
        {titulo}
      </div>
      <div style={{ border: `1px solid ${color}`, borderTop: "none", borderRadius: "0 0 8px 8px", overflow: "hidden" }}>
        {grupos?.map((g, i) => (
          <div key={i}>
            <div style={{ background: "#f8fafc", padding: "6px 12px",
              fontSize: 11, fontWeight: 700, color: "#6b7280", borderBottom: "1px solid #e5e7eb" }}>
              {g.nombre}
            </div>
            {g.cuentas.map((c, j) => (
              <div key={j} style={{ display: "flex", justifyContent: "space-between",
                padding: "5px 16px", fontSize: 12, borderBottom: "1px solid #f3f4f6" }}>
                <span>{c.nombre}</span>
                <span>${fmt(c.saldo)}</span>
              </div>
            ))}
          </div>
        ))}
        <div style={{ display: "flex", justifyContent: "space-between",
          padding: "10px 14px", fontWeight: 700, fontSize: 14,
          background: "#f1f5f9", borderTop: `2px solid ${color}` }}>
          <span>TOTAL</span>
          <span style={{ color }}>${fmt(total)}</span>
        </div>
      </div>
    </div>
  );

  return (
    <Card>
      <h3 style={{ marginTop: 0, color: "#1e3a5f" }}>Balance General</h3>
      <div style={{ display: "flex", gap: 10, alignItems: "flex-end", marginBottom: 20 }}>
        <label style={{ fontSize: 13 }}>
          Al cierre de<br />
          <input type="date" value={hasta} onChange={e => setHasta(e.target.value)}
            style={{ padding: "6px 10px", border: "1px solid #ccc", borderRadius: 6 }} />
        </label>
        <button onClick={buscar} disabled={loading}
          style={{ padding: "7px 20px", background: "#2563eb", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontWeight: 600 }}>
          {loading ? "..." : "Consultar"}
        </button>
      </div>

      {data && (
        <>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 20 }}>
            <Seccion titulo="ACTIVO" grupos={data.activo?.grupos}
              total={data.activo?.total} color="#1d4ed8" />
            <div style={{ flex: "1 1 260px", display: "flex", flexDirection: "column", gap: 16 }}>
              <Seccion titulo="PASIVO" grupos={data.pasivo?.grupos}
                total={data.pasivo?.total} color="#b45309" />
              <div style={{ border: "1px solid #6d28d9", borderRadius: 8, overflow: "hidden" }}>
                <div style={{ background: "#6d28d9", color: "#fff", fontWeight: 700,
                  fontSize: 13, padding: "8px 14px" }}>PATRIMONIO NETO</div>
                {data.patrimonio_neto?.grupos?.map((g, i) => (
                  <div key={i}>
                    <div style={{ background: "#f8fafc", padding: "6px 12px",
                      fontSize: 11, fontWeight: 700, color: "#6b7280" }}>{g.nombre}</div>
                    {g.cuentas.map((c, j) => (
                      <div key={j} style={{ display: "flex", justifyContent: "space-between",
                        padding: "5px 16px", fontSize: 12 }}>
                        <span>{c.nombre}</span><span>${fmt(c.saldo)}</span>
                      </div>
                    ))}
                  </div>
                ))}
                <div style={{ display: "flex", justifyContent: "space-between",
                  padding: "5px 16px", fontSize: 12, background: "#faf5ff" }}>
                  <span style={{ fontStyle: "italic" }}>Resultado del período</span>
                  <span style={{ color: data.patrimonio_neto?.resultado_periodo >= 0 ? "#065f46" : "#991b1b" }}>
                    ${fmt(data.patrimonio_neto?.resultado_periodo)}
                  </span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between",
                  padding: "10px 14px", fontWeight: 700, fontSize: 14,
                  background: "#f1f5f9", borderTop: "2px solid #6d28d9" }}>
                  <span>TOTAL</span>
                  <span style={{ color: "#6d28d9" }}>${fmt(data.patrimonio_neto?.total)}</span>
                </div>
              </div>
            </div>
          </div>

          <div style={{
            display: "flex", justifyContent: "space-between", alignItems: "center",
            padding: "12px 20px", borderRadius: 8,
            background: data.cuadra ? "#d1fae5" : "#fee2e2",
            border: `2px solid ${data.cuadra ? "#6ee7b7" : "#fca5a5"}`,
          }}>
            <div>
              <div style={{ fontWeight: 700 }}>Activo: <span style={{ color: "#1d4ed8" }}>${fmt(data.activo?.total)}</span></div>
              <div style={{ fontSize: 12, color: "#555" }}>
                Pasivo + PN: ${fmt(data.total_pasivo_pn)}
              </div>
            </div>
            <Badge ok={data.cuadra} />
          </div>
        </>
      )}
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANEL: Plan de Cuentas ABM
// ═══════════════════════════════════════════════════════════════════════════════
function PanelPlanCuentas() {
  const [cuentas, setCuentas] = useState([]);
  const [form, setForm] = useState({ codigo: "", nombre: "", tipo: "A", nivel: 4, padre: "", saldo_tipo: "D", es_imputable: true, activa: true });
  const [editando, setEditando] = useState(false);

  const cargar = useCallback(() => {
    fetch(`${API}/PlanCuentas/`).then(r => r.json()).then(setCuentas).catch(() => {});
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  const guardar = async () => {
    if (!form.codigo || !form.nombre) return alert("Código y nombre requeridos");
    await fetch(`${API}/GuardarCuenta/`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form),
    });
    setForm({ codigo: "", nombre: "", tipo: "A", nivel: 4, padre: "", saldo_tipo: "D", es_imputable: true, activa: true });
    setEditando(false);
    cargar();
  };

  const COLORES = { A: "#dbeafe", P: "#fce7f3", PN: "#d1fae5", I: "#fef9c3", E: "#fee2e2" };
  const SANGRIA = { 1: 0, 2: 16, 3: 32, 4: 48 };

  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ margin: 0, color: "#1e3a5f" }}>Plan de Cuentas</h3>
        <button onClick={() => setEditando(!editando)}
          style={{ padding: "7px 18px", background: "#7c3aed", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontWeight: 600 }}>
          {editando ? "× Cancelar" : "+ Nueva Cuenta"}
        </button>
      </div>

      {editando && (
        <div style={{ background: "#f8f5ff", border: "1px solid #c4b5fd", borderRadius: 8, padding: 16, marginBottom: 16 }}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {[
              { label: "Código", key: "codigo", type: "text", placeholder: "1.1.01.002" },
              { label: "Nombre", key: "nombre", type: "text", flex: 2, placeholder: "Banco BBVA" },
              { label: "Padre", key: "padre", type: "text", placeholder: "1.1.01" },
            ].map(f => (
              <label key={f.key} style={{ fontSize: 13, flex: f.flex || "1 1 140px" }}>
                {f.label}<br />
                <input value={form[f.key]} placeholder={f.placeholder}
                  onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
                  style={{ width: "100%", padding: "6px 10px", border: "1px solid #ccc", borderRadius: 6 }} />
              </label>
            ))}
            <label style={{ fontSize: 13, flex: "1 1 100px" }}>
              Tipo<br />
              <select value={form.tipo} onChange={e => setForm(p => ({ ...p, tipo: e.target.value }))}
                style={{ width: "100%", padding: "7px 8px", border: "1px solid #ccc", borderRadius: 6 }}>
                <option value="A">A - Activo</option>
                <option value="P">P - Pasivo</option>
                <option value="PN">PN - Patrimonio</option>
                <option value="I">I - Ingreso</option>
                <option value="E">E - Egreso</option>
              </select>
            </label>
            <label style={{ fontSize: 13, flex: "1 1 80px" }}>
              Nivel<br />
              <input type="number" min={1} max={4} value={form.nivel}
                onChange={e => setForm(p => ({ ...p, nivel: parseInt(e.target.value) }))}
                style={{ width: "100%", padding: "6px 10px", border: "1px solid #ccc", borderRadius: 6 }} />
            </label>
            <label style={{ fontSize: 13, flex: "1 1 100px" }}>
              Saldo<br />
              <select value={form.saldo_tipo} onChange={e => setForm(p => ({ ...p, saldo_tipo: e.target.value }))}
                style={{ width: "100%", padding: "7px 8px", border: "1px solid #ccc", borderRadius: 6 }}>
                <option value="D">Deudora</option>
                <option value="C">Acreedora</option>
              </select>
            </label>
          </div>
          <div style={{ display: "flex", gap: 16, marginTop: 10, alignItems: "center" }}>
            <label style={{ fontSize: 13, display: "flex", gap: 6, alignItems: "center" }}>
              <input type="checkbox" checked={form.es_imputable}
                onChange={e => setForm(p => ({ ...p, es_imputable: e.target.checked }))} />
              Es imputable
            </label>
            <button onClick={guardar}
              style={{ padding: "7px 20px", background: "#7c3aed", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontWeight: 600 }}>
              Guardar
            </button>
          </div>
        </div>
      )}

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr><Th>Código</Th><Th>Nombre</Th><Th>Tipo</Th><Th>Saldo</Th><Th>Imputable</Th></tr>
          </thead>
          <tbody>
            {cuentas.map(c => (
              <tr key={c.codigo} style={{ opacity: c.activa ? 1 : 0.45 }}>
                <Td><code style={{ paddingLeft: SANGRIA[c.nivel] || 0 }}>{c.codigo}</code></Td>
                <Td bold={c.nivel === 1}>{c.nombre}</Td>
                <Td>
                  <span style={{ background: COLORES[c.tipo] || "#f1f5f9", padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 600 }}>
                    {c.tipo}
                  </span>
                </Td>
                <Td>{c.saldo_tipo === "D" ? "Deudora" : "Acreedora"}</Td>
                <Td>{c.es_imputable ? "✓" : ""}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MÓDULO PRINCIPAL
// ═══════════════════════════════════════════════════════════════════════════════
const MENU = [
  { id: "sincronizar",  label: "⚡ Sincronizar",          panel: PanelSincronizar },
  { id: "diario",       label: "📋 Libro Diario",          panel: PanelLibroDiario },
  { id: "mayor",        label: "📖 Mayor de Cuentas",      panel: PanelMayorCuenta },
  { id: "sumasaldos",   label: "⚖ Sumas y Saldos",         panel: PanelBalanceSumasYSaldos },
  { id: "resultados",   label: "📊 Estado de Resultados",  panel: PanelEstadoResultados },
  { id: "balance",      label: "🏛 Balance General",        panel: PanelBalanceGeneral },
  { id: "plan",         label: "📑 Plan de Cuentas",        panel: PanelPlanCuentas },
];

export default function ModuloContabilidad() {
  const [activo, setActivo] = useState("sincronizar");
  const PanelActivo = MENU.find(m => m.id === activo)?.panel || PanelSincronizar;

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#f0f4f8" }}>
      {/* Sidebar */}
      <div style={{
        width: 220, background: "#1e3a5f", color: "#fff",
        padding: "24px 0", flexShrink: 0,
      }}>
        <div style={{ padding: "0 20px 20px", borderBottom: "1px solid rgba(255,255,255,.15)" }}>
          <div style={{ fontSize: 11, letterSpacing: 1, opacity: .6, marginBottom: 4 }}>MÓDULO</div>
          <div style={{ fontWeight: 700, fontSize: 16 }}>Contabilidad</div>
        </div>
        <nav style={{ marginTop: 12 }}>
          {MENU.map(m => (
            <button key={m.id} onClick={() => setActivo(m.id)}
              style={{
                display: "block", width: "100%", textAlign: "left",
                padding: "11px 20px", border: "none", cursor: "pointer",
                background: activo === m.id ? "rgba(255,255,255,.15)" : "transparent",
                color: activo === m.id ? "#fff" : "rgba(255,255,255,.7)",
                fontWeight: activo === m.id ? 700 : 400, fontSize: 13,
                borderLeft: activo === m.id ? "3px solid #60a5fa" : "3px solid transparent",
              }}>
              {m.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Contenido */}
      <div style={{ flex: 1, padding: 28, overflowY: "auto" }}>
        <PanelActivo />
      </div>
    </div>
  );
}
