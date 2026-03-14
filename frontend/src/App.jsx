import { useState, useEffect } from "react";
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid
} from "recharts";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const CAT_COLORS = {
  Food: "#1D9E75", Transport: "#378ADD", Entertainment: "#D4537E",
  Shopping: "#D85A30", Utilities: "#BA7517", Rent: "#534AB7",
  Health: "#639922", Finance: "#5DCAA5", Others: "#888780",
};

function useApi(endpoint, token) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!token) return;
    fetch(`${API}${endpoint}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, [endpoint, token]);
  return { data, loading };
}

// ── Auth ─────────────────────────────────────────────────────────────────────

function AuthScreen({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");

  const submit = async () => {
    const res = await fetch(`${API}/auth/${mode}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (data.access_token) onLogin(data.access_token);
    else setErr(data.detail || "Something went wrong");
  };

  const demoLogin = async () => {
    await fetch(`${API}/demo/seed`);
    const res = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "demo@fintrack.app", password: "demo1234" }),
    });
    const data = await res.json();
    if (data.access_token) onLogin(data.access_token);
  };

  return (
    <div style={{ maxWidth: 420, margin: "80px auto", padding: "2rem" }}>
      <div style={{ fontFamily: "'DM Serif Display', serif", fontSize: 28, marginBottom: 8 }}>
        fin<span style={{ color: "#1D9E75" }}>track</span>
      </div>
      <p style={{ color: "#888", marginBottom: 24 }}>Personal finance, automated.</p>
      <input
        placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)}
        style={{ width: "100%", padding: "10px 14px", marginBottom: 10, borderRadius: 8,
          border: "1px solid #ddd", fontSize: 14 }}
      />
      <input
        placeholder="Password" type="password" value={password}
        onChange={(e) => setPassword(e.target.value)}
        style={{ width: "100%", padding: "10px 14px", marginBottom: 16, borderRadius: 8,
          border: "1px solid #ddd", fontSize: 14 }}
      />
      {err && <p style={{ color: "#D85A30", fontSize: 13, marginBottom: 10 }}>{err}</p>}
      <button onClick={submit}
        style={{ width: "100%", background: "#1D9E75", color: "#fff", border: "none",
          padding: "11px", borderRadius: 8, fontSize: 14, cursor: "pointer", marginBottom: 10 }}>
        {mode === "login" ? "Sign In" : "Create Account"}
      </button>
      <button onClick={demoLogin}
        style={{ width: "100%", background: "#EAF3DE", color: "#3B6D11", border: "none",
          padding: "11px", borderRadius: 8, fontSize: 14, cursor: "pointer", marginBottom: 16 }}>
        Try Demo Mode
      </button>
      <p style={{ fontSize: 13, color: "#888", textAlign: "center" }}>
        {mode === "login" ? "No account? " : "Have an account? "}
        <button onClick={() => setMode(mode === "login" ? "signup" : "login")}
          style={{ background: "none", border: "none", color: "#1D9E75", cursor: "pointer", fontSize: 13 }}>
          {mode === "login" ? "Sign up" : "Sign in"}
        </button>
      </p>
    </div>
  );
}

// ── Upload ────────────────────────────────────────────────────────────────────

function UploadBar({ token, onUpload }) {
  const [status, setStatus] = useState(null);

  const handleFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setStatus("Uploading...");
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API}/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    const data = await res.json();
    setStatus(data.message || "Done");
    onUpload();
  };

  return (
    <div style={{ background: "#fff", border: "1px dashed #ccc", borderRadius: 12,
      padding: "14px 20px", display: "flex", alignItems: "center", justifyContent: "space-between",
      marginBottom: 20 }}>
      <div>
        <div style={{ fontSize: 14, fontWeight: 500 }}>Upload bank statement</div>
        <div style={{ fontSize: 12, color: "#888", marginTop: 2 }}>
          {status || "CSV format — HDFC, ICICI, SBI, Axis Bank supported"}
        </div>
      </div>
      <label style={{ background: "#1D9E75", color: "#fff", padding: "7px 16px",
        borderRadius: 8, fontSize: 13, cursor: "pointer", fontWeight: 500 }}>
        Upload CSV
        <input type="file" accept=".csv" onChange={handleFile} style={{ display: "none" }} />
      </label>
    </div>
  );
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

function Dashboard({ token, month }) {
  const { data: summary } = useApi(`/transactions/summary?month=${month}`, token);
  const { data: anomalies } = useApi(`/transactions/anomalies?month=${month}`, token);

  if (!summary) return <p style={{ color: "#888", padding: 20 }}>Loading...</p>;

  const total = summary.reduce((s, r) => s + r.total, 0);
  const pieData = summary.map((r) => ({ name: r.category, value: r.total }));

  const monthlyTrend = [
    { month: "Sep", amount: 41200 }, { month: "Oct", amount: 38900 },
    { month: "Nov", amount: 45600 }, { month: "Dec", amount: 52100 },
    { month: "Jan", amount: 49800 }, { month: "Feb", amount: total },
  ];

  return (
    <div>
      {/* Metrics */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 16 }}>
        {[
          { label: "Total Spent", value: `₹${total.toLocaleString()}` },
          { label: "Transactions", value: summary.reduce((s, r) => s + r.count, 0) },
          { label: "Top Category", value: summary[0]?.category || "—" },
          { label: "Anomalies", value: anomalies?.length || 0, warn: true },
        ].map((m) => (
          <div key={m.label} style={{ background: "#f5f5f3", borderRadius: 8, padding: "14px 16px" }}>
            <div style={{ fontSize: 11, color: "#888", marginBottom: 6 }}>{m.label}</div>
            <div style={{ fontSize: 20, fontWeight: 600, fontFamily: "monospace",
              color: m.warn && m.value > 0 ? "#D85A30" : "#2C2C2A" }}>
              {m.value}
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 16 }}>
        <div style={{ background: "#fff", border: "1px solid #eee", borderRadius: 12, padding: "16px 20px" }}>
          <div style={{ fontSize: 11, color: "#888", fontWeight: 500, marginBottom: 16, textTransform: "uppercase" }}>
            Spending by Category
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
            {summary.map((r) => (
              <span key={r.category} style={{ fontSize: 11, display: "flex", alignItems: "center", gap: 4, color: "#666" }}>
                <span style={{ width: 8, height: 8, borderRadius: 2, background: CAT_COLORS[r.category] || "#888", display: "inline-block" }} />
                {r.category}
              </span>
            ))}
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} dataKey="value">
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={CAT_COLORS[entry.name] || "#888"} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => `₹${v.toLocaleString()}`} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div style={{ background: "#fff", border: "1px solid #eee", borderRadius: 12, padding: "16px 20px" }}>
          <div style={{ fontSize: 11, color: "#888", fontWeight: 500, marginBottom: 16, textTransform: "uppercase" }}>
            Monthly Trend
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={monthlyTrend}>
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#888" }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={(v) => `₹${v / 1000}k`} tick={{ fontSize: 11, fill: "#888" }} axisLine={false} tickLine={false} />
              <Tooltip formatter={(v) => `₹${v.toLocaleString()}`} />
              <Bar dataKey="amount" radius={[4, 4, 0, 0]}
                fill="#9FE1CB"
                label={false}>
                {monthlyTrend.map((entry, i) => (
                  <Cell key={i} fill={i === monthlyTrend.length - 1 ? "#1D9E75" : "#9FE1CB"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Anomalies */}
      {anomalies?.length > 0 && (
        <div style={{ background: "#fff", border: "1px solid #eee", borderRadius: 12, padding: "16px 20px" }}>
          <div style={{ fontSize: 11, color: "#888", fontWeight: 500, marginBottom: 12, textTransform: "uppercase" }}>
            ⚠ Anomaly Alerts
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {anomalies.map((a) => (
              <div key={a.id} style={{ background: "#FAECE7", border: "1px solid #F0997B", borderRadius: 8,
                padding: "10px 14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: "#4A1B0C" }}>
                    {a.description}
                    <span style={{ background: "#F0997B", color: "#4A1B0C", fontSize: 10,
                      padding: "2px 6px", borderRadius: 3, marginLeft: 8 }}>
                      {a.multiplier}× avg
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: "#993C1D", marginTop: 2 }}>
                    {a.date} · {a.category} · avg ₹{a.baseline_avg?.toLocaleString()}
                  </div>
                </div>
                <div style={{ fontFamily: "monospace", fontSize: 15, fontWeight: 600, color: "#D85A30" }}>
                  ₹{a.amount.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Transactions ──────────────────────────────────────────────────────────────

function Transactions({ token, month }) {
  const [category, setCategory] = useState("");
  const { data: txns } = useApi(
    `/transactions?month=${month}${category ? `&category=${category}` : ""}`,
    token
  );

  return (
    <div style={{ background: "#fff", border: "1px solid #eee", borderRadius: 12, overflow: "hidden" }}>
      <div style={{ padding: "14px 20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ fontSize: 11, color: "#888", fontWeight: 500, textTransform: "uppercase" }}>Transactions</div>
        <select value={category} onChange={(e) => setCategory(e.target.value)}
          style={{ fontSize: 12, padding: "4px 8px", borderRadius: 6, border: "1px solid #ddd", background: "#f5f5f3" }}>
          <option value="">All Categories</option>
          {Object.keys(CAT_COLORS).map((c) => <option key={c}>{c}</option>)}
        </select>
      </div>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr style={{ background: "#f5f5f3" }}>
            {["Date", "Description", "Category", "Amount", ""].map((h) => (
              <th key={h} style={{ textAlign: "left", padding: "8px 14px", fontSize: 10,
                fontWeight: 500, color: "#888", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {txns?.map((t) => (
            <tr key={t.id} style={{ background: t.is_anomaly ? "#FAECE7" : "white" }}>
              <td style={{ padding: "9px 14px", fontFamily: "monospace", fontSize: 11, color: "#888",
                borderBottom: "1px solid #f0f0f0" }}>{t.date}</td>
              <td style={{ padding: "9px 14px", borderBottom: "1px solid #f0f0f0" }}>{t.description}</td>
              <td style={{ padding: "9px 14px", borderBottom: "1px solid #f0f0f0" }}>
                <span style={{ background: (CAT_COLORS[t.category] || "#888") + "22",
                  color: CAT_COLORS[t.category] || "#888", fontSize: 11,
                  padding: "2px 8px", borderRadius: 3, fontFamily: "monospace" }}>
                  {t.category}
                </span>
              </td>
              <td style={{ padding: "9px 14px", fontFamily: "monospace", fontWeight: 500,
                color: t.is_anomaly ? "#D85A30" : "#2C2C2A", borderBottom: "1px solid #f0f0f0" }}>
                ₹{t.amount.toLocaleString()}
              </td>
              <td style={{ padding: "9px 14px", fontSize: 11, color: "#D85A30", borderBottom: "1px solid #f0f0f0" }}>
                {t.is_anomaly ? "⚠ Anomaly" : ""}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Budget ────────────────────────────────────────────────────────────────────

function Budget({ token, month }) {
  const { data: budgets, loading } = useApi("/budget", token);
  const { data: summary } = useApi(`/transactions/summary?month=${month}`, token);
  const [editing, setEditing] = useState({});

  const saveLimit = async (cat, val) => {
    await fetch(`${API}/budget?category=${cat}&limit=${val}`, {
      method: "POST", headers: { Authorization: `Bearer ${token}` },
    });
    setEditing((e) => ({ ...e, [cat]: false }));
  };

  const spentMap = {};
  summary?.forEach((r) => { spentMap[r.category] = r.total; });
  const budgetMap = {};
  budgets?.forEach((b) => { budgetMap[b.category] = b.monthly_limit; });

  const categories = [...new Set([...Object.keys(spentMap), ...Object.keys(budgetMap)])];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
      {categories.map((cat) => {
        const spent = spentMap[cat] || 0;
        const limit = budgetMap[cat] || 0;
        const pct = limit ? Math.min(100, Math.round((spent / limit) * 100)) : null;
        const over = pct > 100;
        const warn = pct > 80 && !over;
        const fillColor = over ? "#D85A30" : warn ? "#BA7517" : "#1D9E75";

        return (
          <div key={cat} style={{ background: "#fff", border: "1px solid #eee", borderRadius: 12, padding: "14px 18px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <div style={{ fontSize: 14, fontWeight: 500 }}>{cat}</div>
              <div style={{ fontSize: 12, color: "#888", fontFamily: "monospace" }}>
                ₹{spent.toLocaleString()} {limit ? `/ ₹${limit.toLocaleString()}` : ""}
              </div>
            </div>
            {pct !== null && (
              <>
                <div style={{ background: "#f0f0ee", borderRadius: 4, height: 6, marginBottom: 6 }}>
                  <div style={{ width: `${pct}%`, height: 6, borderRadius: 4, background: fillColor, transition: "width 0.4s" }} />
                </div>
                <div style={{ fontSize: 11, color: over ? "#D85A30" : warn ? "#BA7517" : "#888" }}>
                  {over ? "Over budget!" : warn ? `${100 - pct}% remaining` : `${pct}% used`}
                </div>
              </>
            )}
            <button onClick={() => setEditing((e) => ({ ...e, [cat]: !e[cat] }))}
              style={{ marginTop: 10, fontSize: 11, background: "none", border: "1px solid #ddd",
                padding: "3px 10px", borderRadius: 5, cursor: "pointer", color: "#666" }}>
              {limit ? "Edit limit" : "Set limit"}
            </button>
            {editing[cat] && (
              <div style={{ marginTop: 8, display: "flex", gap: 6 }}>
                <input id={`limit-${cat}`} type="number" defaultValue={limit}
                  style={{ flex: 1, padding: "5px 8px", borderRadius: 5, border: "1px solid #ddd", fontSize: 12 }} />
                <button onClick={() => saveLimit(cat, document.getElementById(`limit-${cat}`).value)}
                  style={{ background: "#1D9E75", color: "#fff", border: "none",
                    padding: "5px 10px", borderRadius: 5, fontSize: 12, cursor: "pointer" }}>
                  Save
                </button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Report ────────────────────────────────────────────────────────────────────

function Report({ token, month }) {
  const { data: summary } = useApi(`/transactions/summary?month=${month}`, token);
  const { data: anomalies } = useApi(`/transactions/anomalies?month=${month}`, token);
  const { data: budgets } = useApi("/budget", token);

  const downloadPDF = () => {
    window.open(`${API}/report/${month}?token=${token}`, "_blank");
  };

  const budgetMap = {};
  budgets?.forEach((b) => { budgetMap[b.category] = b.monthly_limit; });
  const total = summary?.reduce((s, r) => s + r.total, 0) || 0;

  return (
    <div>
      <div style={{ background: "#fff", border: "1px solid #eee", borderRadius: 12, padding: "16px 20px", marginBottom: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: "#888", fontWeight: 500, textTransform: "uppercase" }}>
            Monthly Summary — {month}
          </div>
          <button onClick={downloadPDF}
            style={{ background: "#1D9E75", color: "#fff", border: "none", padding: "7px 16px",
              borderRadius: 8, fontSize: 13, cursor: "pointer", fontWeight: 500 }}>
            ↓ Download PDF
          </button>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "#f5f5f3" }}>
              {["Category", "Transactions", "Spent", "Budget", "Status"].map((h) => (
                <th key={h} style={{ textAlign: "left", padding: "8px 12px", fontSize: 10,
                  fontWeight: 500, color: "#888", textTransform: "uppercase" }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {summary?.map((r) => {
              const limit = budgetMap[r.category] || 0;
              const over = limit && r.total > limit;
              return (
                <tr key={r.category}>
                  <td style={{ padding: "9px 12px", borderBottom: "1px solid #f0f0f0" }}>{r.category}</td>
                  <td style={{ padding: "9px 12px", borderBottom: "1px solid #f0f0f0" }}>{r.count}</td>
                  <td style={{ padding: "9px 12px", fontFamily: "monospace", borderBottom: "1px solid #f0f0f0" }}>₹{r.total.toLocaleString()}</td>
                  <td style={{ padding: "9px 12px", fontFamily: "monospace", color: "#888", borderBottom: "1px solid #f0f0f0" }}>
                    {limit ? `₹${limit.toLocaleString()}` : "—"}
                  </td>
                  <td style={{ padding: "9px 12px", color: over ? "#D85A30" : "#1D9E75", fontWeight: 500, fontSize: 12, borderBottom: "1px solid #f0f0f0" }}>
                    {limit ? (over ? "Over" : "Within") : "—"}
                  </td>
                </tr>
              );
            })}
            <tr style={{ background: "#f5f5f3" }}>
              <td colSpan={2} style={{ padding: "9px 12px", fontWeight: 600 }}>Total</td>
              <td style={{ padding: "9px 12px", fontFamily: "monospace", fontWeight: 600 }}>₹{total.toLocaleString()}</td>
              <td colSpan={2} />
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── App Shell ─────────────────────────────────────────────────────────────────

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("ft_token") || "");
  const [tab, setTab] = useState("dashboard");
  const [refresh, setRefresh] = useState(0);
  const month = "2025-02";

  const handleLogin = (tok) => {
    setToken(tok);
    localStorage.setItem("ft_token", tok);
  };

  const logout = () => {
    setToken("");
    localStorage.removeItem("ft_token");
  };

  if (!token) return <AuthScreen onLogin={handleLogin} />;

  const tabs = [
    { id: "dashboard", label: "Dashboard" },
    { id: "transactions", label: "Transactions" },
    { id: "budget", label: "Budget Goals" },
    { id: "report", label: "Monthly Report" },
  ];

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "1.5rem 1rem", fontFamily: "'DM Sans', system-ui, sans-serif" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: -0.5 }}>
          fin<span style={{ color: "#1D9E75" }}>track</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 12, color: "#888", fontFamily: "monospace" }}>{month}</span>
          <button onClick={logout} style={{ fontSize: 12, color: "#888", background: "none", border: "1px solid #ddd",
            padding: "4px 10px", borderRadius: 6, cursor: "pointer" }}>
            Logout
          </button>
        </div>
      </div>

      {/* Upload */}
      <UploadBar token={token} onUpload={() => setRefresh((r) => r + 1)} />

      {/* Nav */}
      <div style={{ display: "flex", gap: 4, marginBottom: 20, background: "#fff",
        padding: 4, borderRadius: 8, border: "1px solid #eee" }}>
        {tabs.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)}
            style={{ flex: 1, padding: "7px 0", fontSize: 13, border: "none", cursor: "pointer",
              borderRadius: 6, fontFamily: "inherit",
              background: tab === t.id ? "#f5f5f3" : "transparent",
              color: tab === t.id ? "#2C2C2A" : "#888",
              fontWeight: tab === t.id ? 500 : 400 }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {tab === "dashboard" && <Dashboard key={refresh} token={token} month={month} />}
      {tab === "transactions" && <Transactions key={refresh} token={token} month={month} />}
      {tab === "budget" && <Budget key={refresh} token={token} month={month} />}
      {tab === "report" && <Report key={refresh} token={token} month={month} />}
    </div>
  );
}
