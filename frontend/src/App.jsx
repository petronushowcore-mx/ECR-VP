import { useState, useEffect, useRef, useCallback } from "react";
import * as api from "./api";

// ═══════════════════════════════════════════════════════════════════════════
// DESIGN SYSTEM
// ═══════════════════════════════════════════════════════════════════════════

const COLORS = {
  bg: "#08090A",
  bgCard: "#0F1210",
  bgCardHover: "#141A16",
  bgPanel: "#111613",
  border: "#1E2A22",
  borderLight: "#2A3D30",
  borderGold: "#6B5A3E",
  gold: "#B8965A",
  goldMuted: "#8A7044",
  goldLight: "#D4B877",
  amber: "#D97706",
  amberLight: "#F59E0B",
  amberDark: "#B45309",
  green: "#22C55E",
  greenMuted: "#16A34A",
  greenDark: "#15803D",
  greenSubtle: "#1A3A2A",
  greenGlow: "rgba(34, 197, 94, 0.08)",
  text: "#E4E0D6",
  textMuted: "#9B978D",
  textDim: "#6B6860",
  red: "#EF4444",
  redMuted: "#DC2626",
};

const FONTS = {
  display: "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace",
  body: "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
  mono: "'JetBrains Mono', 'SF Mono', monospace",
};

// ═══════════════════════════════════════════════════════════════════════════
// PROTOCOL CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

const PROTOCOL_MODES = [
  { key: "Rc", label: "Rc Mode", desc: "Architecture as class" },
  { key: "Ri", label: "Ri Mode", desc: "Invariants & prohibitions" },
  { key: "DET", label: "Declarative Epistemic Typology", desc: "Epistemic layer classification" },
  { key: "Ra", label: "Ra Mode", desc: "Engineering realizability" },
  { key: "Failure", label: "Failure Mode", desc: "Failure & risk analysis" },
  { key: "Novelty", label: "Novelty & Positioning", desc: "Structural novelty" },
  { key: "Verdict", label: "Verdict", desc: "Engineering verdict" },
  { key: "Maturity", label: "Project Maturity Summary", desc: "Operational readiness" },
];

const PROVIDERS = [
  { id: "anthropic", name: "Anthropic", models: ["claude-opus-4-6", "claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001"] },
  { id: "openai", name: "OpenAI", models: ["gpt-5.3", "gpt-5.2", "gpt-5", "o3", "o4-mini"] },
  { id: "google", name: "Google", models: ["gemini-3-pro", "gemini-2.5-pro", "gemini-2.0-flash"] },
  { id: "xai", name: "xAI", models: ["grok-4", "grok-4-fast"] },
  { id: "deepseek", name: "DeepSeek", models: ["deepseek-r1-v3.2", "deepseek-v3.2-chat"] },
  { id: "perplexity", name: "Perplexity", models: ["sonar-deep-research", "sonar-pro"] },
  { id: "mistral", name: "Mistral", models: ["mistral-large-latest", "mistral-small-latest", "codestral-latest"] },
  { id: "microsoft", name: "Microsoft", models: ["phi-4", "phi-4-mini"] },
  { id: "ollama", name: "Ollama (Local)", models: ["llama3.3:70b", "qwen3:72b", "qwen2.5:14b", "llama3.1:8b", "deepseek-r1:14b", "mistral:7b"] },
];

// ═══════════════════════════════════════════════════════════════════════════
// API STATE HOOK
// ═══════════════════════════════════════════════════════════════════════════

function useApi(fetcher, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    fetcher()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, deps);
  useEffect(() => { reload(); }, [reload]);
  return { data, loading, error, reload };
}

const EmptyState = ({ icon, title, children }) => (
  <div style={{
    textAlign: "center", padding: "48px 20px",
    background: COLORS.bgCard, border: `1px solid ${COLORS.border}`,
    borderRadius: 6,
  }}>
    <Icon type={icon} size={28} color={COLORS.textDim} />
    <div style={{ fontFamily: FONTS.mono, fontSize: 13, color: COLORS.textMuted, marginTop: 12 }}>{title}</div>
    {children && <div style={{ fontFamily: FONTS.body, fontSize: 12, color: COLORS.textDim, marginTop: 6 }}>{children}</div>}
  </div>
);

const Spinner = () => (
  <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
    <div style={{
      width: 20, height: 20, borderRadius: "50%",
      border: `2px solid ${COLORS.border}`,
      borderTopColor: COLORS.amber,
      animation: "spin 0.8s linear infinite",
    }} />
    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
  </div>
);

const ErrorBanner = ({ message, onRetry }) => (
  <div style={{
    padding: "10px 16px", borderRadius: 4, marginBottom: 16,
    background: "rgba(239,68,68,0.06)", border: `1px solid rgba(239,68,68,0.15)`,
    display: "flex", justifyContent: "space-between", alignItems: "center",
  }}>
    <span style={{ fontFamily: FONTS.mono, fontSize: 11, color: COLORS.red }}>
      {message}
    </span>
    {onRetry && <Button variant="ghost" small onClick={onRetry}>Retry</Button>}
  </div>
);

// ═══════════════════════════════════════════════════════════════════════════
// ICONS (inline SVG for zero dependencies)
// ═══════════════════════════════════════════════════════════════════════════

const Icon = ({ type, size = 18, color = COLORS.textMuted }) => {
  const props = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: color, strokeWidth: 1.5, strokeLinecap: "round", strokeLinejoin: "round" };
  const icons = {
    folder: <svg {...props}><path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>,
    play: <svg {...props}><polygon points="5 3 19 12 5 21 5 3" fill={color} stroke="none"/></svg>,
    check: <svg {...props}><polyline points="20 6 9 17 4 12"/></svg>,
    alert: <svg {...props}><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>,
    upload: <svg {...props}><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>,
    download: <svg {...props}><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>,
    shield: <svg {...props}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>,
    eye: <svg {...props}><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>,
    grid: <svg {...props}><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>,
    layers: <svg {...props}><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>,
    hash: <svg {...props}><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></svg>,
    clock: <svg {...props}><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>,
    zap: <svg {...props}><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" fill={color} stroke="none"/></svg>,
    plus: <svg {...props}><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>,
    file: <svg {...props}><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>,
    lock: <svg {...props}><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>,
    compass: <svg {...props}><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>,
    x: <svg {...props}><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
    chevron: <svg {...props}><polyline points="9 18 15 12 9 6"/></svg>,
    menu: <svg {...props}><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>,
  };
  return icons[type] || null;
};

// ═══════════════════════════════════════════════════════════════════════════
// SHARED COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════

const StatusBadge = ({ status }) => {
  const map = {
    completed: { bg: "rgba(34,197,94,0.12)", color: COLORS.green, label: "COMPLETED" },
    awaiting_synthesis: { bg: "rgba(217,119,6,0.12)", color: COLORS.amber, label: "AWAITING SYNTHESIS" },
    executing: { bg: "rgba(59,130,246,0.15)", color: "#60A5FA", label: "EXECUTING" },
    failed: { bg: "rgba(239,68,68,0.12)", color: COLORS.red, label: "FAILED" },
    locked: { bg: "rgba(184,150,90,0.12)", color: COLORS.gold, label: "LOCKED" },
    preparing: { bg: "rgba(107,104,96,0.15)", color: COLORS.textDim, label: "PREPARING" },
  };
  const s = map[status] || map.preparing;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      padding: "3px 10px", borderRadius: 3,
      background: s.bg, color: s.color,
      fontSize: 10, fontFamily: FONTS.mono, fontWeight: 600,
      letterSpacing: "0.08em", textTransform: "uppercase",
    }}>
      <span style={{ width: 5, height: 5, borderRadius: "50%", background: s.color, boxShadow: `0 0 6px ${s.color}` }} />
      {s.label}
    </span>
  );
};

const GoldDivider = ({ style }) => (
  <div style={{
    height: 1,
    background: `linear-gradient(90deg, transparent, ${COLORS.borderGold}, ${COLORS.goldMuted}, ${COLORS.borderGold}, transparent)`,
    margin: "16px 0",
    opacity: 0.5,
    ...style,
  }} />
);

const SectionTitle = ({ children, icon, action }) => (
  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      {icon && <Icon type={icon} size={16} color={COLORS.gold} />}
      <h2 style={{
        margin: 0, fontSize: 11, fontFamily: FONTS.mono,
        color: COLORS.gold, letterSpacing: "0.12em",
        textTransform: "uppercase", fontWeight: 600,
      }}>{children}</h2>
    </div>
    {action}
  </div>
);

const Button = ({ children, variant = "primary", onClick, disabled, small, icon }) => {
  const [hovered, setHovered] = useState(false);
  const styles = {
    primary: {
      bg: hovered ? COLORS.amber : COLORS.amberDark,
      color: "#000",
      border: "none",
    },
    secondary: {
      bg: hovered ? COLORS.bgCardHover : "transparent",
      color: COLORS.gold,
      border: `1px solid ${COLORS.borderGold}`,
    },
    ghost: {
      bg: hovered ? "rgba(184,150,90,0.08)" : "transparent",
      color: COLORS.textMuted,
      border: `1px solid ${hovered ? COLORS.borderGold : COLORS.border}`,
    },
  };
  const s = styles[variant];
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: "inline-flex", alignItems: "center", gap: 6,
        padding: small ? "5px 12px" : "8px 18px",
        borderRadius: 4,
        background: disabled ? COLORS.bgCard : s.bg,
        color: disabled ? COLORS.textDim : s.color,
        border: s.border,
        fontSize: small ? 11 : 12,
        fontFamily: FONTS.mono,
        fontWeight: 600,
        letterSpacing: "0.04em",
        cursor: disabled ? "not-allowed" : "pointer",
        transition: "all 0.15s ease",
        opacity: disabled ? 0.5 : 1,
      }}
    >
      {icon && <Icon type={icon} size={small ? 13 : 15} color={disabled ? COLORS.textDim : s.color} />}
      {children}
    </button>
  );
};

const Card = ({ children, onClick, style, glow }) => {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered && onClick ? COLORS.bgCardHover : COLORS.bgCard,
        border: `1px solid ${glow ? COLORS.borderGold : COLORS.border}`,
        borderRadius: 6,
        padding: 20,
        cursor: onClick ? "pointer" : "default",
        transition: "all 0.2s ease",
        boxShadow: glow ? `0 0 20px rgba(184,150,90,0.04)` : "none",
        ...style,
      }}
    >
      {children}
    </div>
  );
};

const ModeTag = ({ mode, detected, style }) => (
  <span style={{
    display: "inline-flex", alignItems: "center", gap: 4,
    padding: "2px 8px", borderRadius: 3,
    background: detected ? "rgba(34,197,94,0.08)" : "rgba(239,68,68,0.08)",
    border: `1px solid ${detected ? "rgba(34,197,94,0.2)" : "rgba(239,68,68,0.2)"}`,
    color: detected ? COLORS.greenMuted : COLORS.redMuted,
    fontSize: 10, fontFamily: FONTS.mono, fontWeight: 500,
    ...style,
  }}>
    {detected ? "✓" : "✗"} {mode}
  </span>
);

// ═══════════════════════════════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════════════════════════════

const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard", icon: "compass" },
  { key: "corpus", label: "Corpus", icon: "folder" },
  { key: "sessions", label: "Sessions", icon: "layers" },
  { key: "results", label: "Results", icon: "eye" },
  { key: "synthesis", label: "Synthesis", icon: "grid" },
  { key: "install", label: "How to Install", icon: "zap" },
  { key: "guide", label: "How to Use", icon: "file" },
];

const Sidebar = ({ active, onNavigate, license, onLogout }) => (
  <nav style={{
    width: 220, minHeight: "100vh",
    background: COLORS.bgCard,
    borderRight: `1px solid ${COLORS.border}`,
    display: "flex", flexDirection: "column",
    padding: "0",
    position: "fixed", left: 0, top: 0, bottom: 0,
    zIndex: 100,
  }}>
    {/* Logo */}
    <div style={{ padding: "24px 20px 20px" }}>
      <div style={{
        fontFamily: FONTS.mono, fontSize: 13, fontWeight: 700,
        color: COLORS.gold, letterSpacing: "0.08em",
      }}>
        ECR-VP
      </div>
      <div style={{
        fontFamily: FONTS.mono, fontSize: 9,
        color: COLORS.textDim, letterSpacing: "0.15em",
        marginTop: 3, textTransform: "uppercase",
      }}>
        Verification Protocol Shell
      </div>
      <div style={{
        height: 2, width: 32, marginTop: 12,
        background: `linear-gradient(90deg, ${COLORS.amber}, ${COLORS.gold}, transparent)`,
        borderRadius: 1,
      }} />
    </div>

    {/* Nav Items */}
    <div style={{ padding: "8px 10px", flex: 1 }}>
      {NAV_ITEMS.map((item, idx) => {
        const isActive = active === item.key;
        const isGuide = item.key === "install";
        return (
          <div key={item.key}>
            {isGuide && (
              <div style={{
                height: 1, margin: "8px 12px 10px",
                background: `linear-gradient(90deg, transparent, ${COLORS.borderGold}, transparent)`,
                opacity: 0.4,
              }} />
            )}
            <div
              onClick={() => onNavigate(item.key)}
              style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "10px 12px", borderRadius: 4, marginBottom: 2,
                background: isActive ? "rgba(184,150,90,0.08)" : "transparent",
                borderLeft: isActive ? `2px solid ${COLORS.amber}` : "2px solid transparent",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              <Icon type={item.icon} size={15} color={isActive ? COLORS.gold : COLORS.textDim} />
              <span style={{
                fontFamily: FONTS.mono, fontSize: 11,
                color: isActive ? COLORS.gold : COLORS.textMuted,
                fontWeight: isActive ? 600 : 400,
                letterSpacing: "0.04em",
              }}>
                {item.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>

    {/* License Info */}
    {license && (
      <div style={{ padding: "12px 20px", borderTop: `1px solid ${COLORS.border}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
          <Icon type="check" size={10} color={COLORS.green} />
          <span style={{ fontFamily: FONTS.mono, fontSize: 9, color: COLORS.greenMuted, letterSpacing: "0.1em", textTransform: "uppercase" }}>
            Licensed
          </span>
        </div>
        <div style={{ fontFamily: FONTS.mono, fontSize: 9, color: COLORS.textDim, marginBottom: 8 }}>
          {license.status === "offline" ? "Offline mode" : license.customerName || "Active"}
        </div>
        <div
          onClick={onLogout}
          style={{
            fontFamily: FONTS.mono, fontSize: 9, color: COLORS.textDim,
            cursor: "pointer", letterSpacing: "0.06em",
            transition: "color 0.15s",
          }}
          onMouseEnter={e => e.target.style.color = COLORS.red}
          onMouseLeave={e => e.target.style.color = COLORS.textDim}
        >
          Deactivate License
        </div>
      </div>
    )}

    {/* Protocol Integrity */}
    <div style={{ padding: "16px 20px", borderTop: `1px solid ${COLORS.border}` }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
        <Icon type="shield" size={12} color={COLORS.greenMuted} />
        <span style={{ fontFamily: FONTS.mono, fontSize: 9, color: COLORS.greenMuted, letterSpacing: "0.1em", textTransform: "uppercase" }}>
          Protocol Integrity
        </span>
      </div>
      <div style={{ fontFamily: FONTS.mono, fontSize: 9, color: COLORS.textDim, lineHeight: 1.6 }}>
        Observation ≠ Control<br />
        No scoring · No feedback<br />
        No optimization
      </div>
    </div>
  </nav>
);

// ═══════════════════════════════════════════════════════════════════════════
// PAGE: DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════

const DashboardPage = ({ onNavigate }) => {
  const health = useApi(() => api.getHealth(), []);
  const sessions = useApi(() => api.listSessions().then(r => r.sessions), []);
  const files = useApi(() => api.listFiles().then(r => r.files), []);

  const sessionList = sessions.data || [];
  const fileList = files.data || [];
  const awaitingSynthesis = sessionList.filter(s => s.state === "awaiting_synthesis").length;
  const totalRuns = sessionList.reduce((sum, s) => sum + (s.run_count || 0), 0);

  const connected = !!health.data;
  const stats = [
    { label: "Active Sessions", value: String(sessionList.length), icon: "layers", color: COLORS.amber },
    { label: "Corpus Files", value: String(fileList.length), icon: "file", color: COLORS.gold },
    { label: "Interpreter Runs", value: String(totalRuns), icon: "zap", color: COLORS.green },
    { label: "Awaiting Synthesis", value: String(awaitingSynthesis), icon: "eye", color: COLORS.amberLight },
  ];

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{
          margin: 0, fontFamily: FONTS.display, fontSize: 22, fontWeight: 400,
          color: COLORS.text, letterSpacing: "0.02em",
        }}>
          Verification <span style={{ color: COLORS.gold }}>Dashboard</span>
        </h1>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 6 }}>
          <p style={{ margin: 0, fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted }}>
            ECR-VP v1.0 — Epistemic Coherence Review and Verification Protocol
          </p>
          <span style={{
            display: "inline-flex", alignItems: "center", gap: 4,
            fontFamily: FONTS.mono, fontSize: 9, letterSpacing: "0.08em",
            color: connected ? COLORS.greenMuted : COLORS.redMuted,
          }}>
            <span style={{ width: 5, height: 5, borderRadius: "50%", background: connected ? COLORS.green : COLORS.red, boxShadow: connected ? `0 0 6px ${COLORS.green}` : "none" }} />
            {connected ? "BACKEND CONNECTED" : "BACKEND OFFLINE"}
          </span>
        </div>
      </div>

      {!connected && !health.loading && (
        <ErrorBanner message="Backend not reachable at /api. Start it with: cd backend && uvicorn app.main:app --port 8000" onRetry={health.reload} />
      )}

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 28 }}>
        {stats.map((s, i) => (
          <Card key={i} style={{ padding: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <div style={{ fontFamily: FONTS.mono, fontSize: 28, fontWeight: 300, color: s.color, lineHeight: 1 }}>
                  {s.value}
                </div>
                <div style={{ fontFamily: FONTS.mono, fontSize: 9, color: COLORS.textDim, letterSpacing: "0.1em", marginTop: 6, textTransform: "uppercase" }}>
                  {s.label}
                </div>
              </div>
              <Icon type={s.icon} size={18} color={s.color} />
            </div>
          </Card>
        ))}
      </div>

      {/* Recent Sessions */}
      <SectionTitle icon="clock">Recent Sessions</SectionTitle>
      {sessions.loading ? <Spinner /> : sessionList.length === 0 ? (
        <EmptyState icon="layers" title="No sessions yet">Start by uploading a corpus and creating a passport.</EmptyState>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {[...sessionList].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).map(session => (
            <Card key={session.session_id} onClick={() => onNavigate("results")} glow={session.state === "awaiting_synthesis"}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                    <span style={{ fontFamily: FONTS.mono, fontSize: 10, color: COLORS.textDim }}>{session.session_id?.slice(0, 8)}</span>
                    <StatusBadge status={session.state} />
                  </div>
                  <div style={{ fontFamily: FONTS.body, fontSize: 14, color: COLORS.text, marginBottom: 4 }}>
                    {session.purpose}
                  </div>
                  <div style={{ display: "flex", gap: 16, fontFamily: FONTS.mono, fontSize: 10, color: COLORS.textDim }}>
                    <span><Icon type="zap" size={10} color={COLORS.textDim} /> {session.run_count} interpreters</span>
                    <span>{new Date(session.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                <Icon type="chevron" size={16} color={COLORS.textDim} />
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Protocol Modes Reference */}
      <div style={{ marginTop: 28 }}>
        <SectionTitle icon="hash">Protocol Modes</SectionTitle>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
          {PROTOCOL_MODES.map((m, i) => (
            <div key={m.key} style={{
              padding: "10px 12px",
              background: COLORS.bgCard,
              border: `1px solid ${COLORS.border}`,
              borderRadius: 4,
            }}>
              <div style={{
                fontFamily: FONTS.mono, fontSize: 11, fontWeight: 600,
                color: COLORS.gold, marginBottom: 3,
              }}>
                {i + 1}. {m.key}
              </div>
              <div style={{ fontFamily: FONTS.body, fontSize: 10, color: COLORS.textDim }}>
                {m.desc}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════
// PAGE: CORPUS MANAGER
// ═══════════════════════════════════════════════════════════════════════════

const CorpusPage = () => {
  const filesApi = useApi(() => api.listFiles().then(r => r.files), []);
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [passport, setPassport] = useState(null);
  const [passportError, setPassportError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  // Form state
  const [purpose, setPurpose] = useState("");
  const [canonVersion, setCanonVersion] = useState("");
  const [archStatus, setArchStatus] = useState("closed");
  const [constraints, setConstraints] = useState("");

  useEffect(() => {
    if (filesApi.data) setFiles(filesApi.data);
  }, [filesApi.data]);

  const handleUpload = async (fileList) => {
    if (!fileList?.length) return;
    setUploading(true);
    try {
      const result = await api.uploadFiles(fileList);
      setFiles(prev => [...prev, ...result.uploaded]);
    } catch (e) {
      alert("Upload failed: " + e.message);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleUpload(e.dataTransfer.files);
  };

  const handleCreatePassport = async () => {
    if (!files.length) return;
    setPassportError(null);
    try {
      const result = await api.createPassport({
        purpose: purpose || "Verification session",
        canonVersion: canonVersion || "unspecified",
        architecturalStatus: archStatus,
        constraints: constraints ? constraints.split(";").map(s => s.trim()) : [],
        fileIds: files.map(f => f.file_id || f.filename),
      });
      setPassport(result);
    } catch (e) {
      setPassportError(e.message);
    }
  };

  const inputStyle = {
    width: "100%", padding: "8px 12px", borderRadius: 4, boxSizing: "border-box",
    background: COLORS.bg, border: `1px solid ${COLORS.border}`,
    color: COLORS.text, fontFamily: FONTS.body, fontSize: 12, outline: "none",
  };

  const labelStyle = {
    fontFamily: FONTS.mono, fontSize: 9, color: COLORS.textDim,
    letterSpacing: "0.1em", textTransform: "uppercase", display: "block", marginBottom: 5,
  };

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ margin: 0, fontFamily: FONTS.display, fontSize: 22, fontWeight: 400, color: COLORS.text }}>
          Corpus <span style={{ color: COLORS.gold }}>Manager</span>
        </h1>
        <p style={{ margin: "6px 0 0", fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted }}>
          Upload files, compute hashes, generate Corpus Passport. Canon Lock before execution.
        </p>
      </div>

      {/* Upload Zone */}
      <input ref={fileInputRef} type="file" multiple style={{ display: "none" }}
        onChange={e => handleUpload(e.target.files)} />
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${dragOver ? COLORS.amber : COLORS.borderGold}`,
          borderRadius: 8, padding: "36px 20px", textAlign: "center",
          marginBottom: 24, cursor: "pointer",
          background: dragOver ? "rgba(217,119,6,0.04)" : "transparent",
          transition: "all 0.2s ease",
        }}
      >
        {uploading ? <Spinner /> : (
          <>
            <Icon type="upload" size={28} color={dragOver ? COLORS.amber : COLORS.goldMuted} />
            <div style={{ fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted, marginTop: 10 }}>
              Drop corpus files here or <span style={{ color: COLORS.amber }}>browse</span>
            </div>
            <div style={{ fontFamily: FONTS.mono, fontSize: 10, color: COLORS.textDim, marginTop: 4 }}>
              PDF · DOCX · MD · TXT · PY · JSON · PNG · JPG
            </div>
          </>
        )}
      </div>

      {/* File List */}
      <SectionTitle icon="file">Corpus Files ({files.length})</SectionTitle>
      {files.length === 0 ? (
        <EmptyState icon="upload" title="No files uploaded yet" />
      ) : (
        <Card style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                {["#", "Filename", "Size", ""].map(h => (
                  <th key={h} style={{ padding: "10px 14px", textAlign: "left", fontFamily: FONTS.mono, fontSize: 9, color: COLORS.textDim, letterSpacing: "0.1em", textTransform: "uppercase", fontWeight: 600, ...(h === "" ? { width: 40 } : {}) }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {files.map((f, i) => (
                <tr key={i} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                  <td style={{ padding: "10px 14px", fontFamily: FONTS.mono, fontSize: 11, color: COLORS.textDim }}>{String(i + 1).padStart(3, "0")}</td>
                  <td style={{ padding: "10px 14px", fontFamily: FONTS.mono, fontSize: 12, color: COLORS.text }}>{f.filename}</td>
                  <td style={{ padding: "10px 14px", fontFamily: FONTS.mono, fontSize: 11, color: COLORS.textMuted }}>{((f.size_bytes || 0) / 1024).toFixed(0)} KB</td>
                  <td style={{ padding: "10px 14px", textAlign: "center" }}>
                    <span
                      onClick={async (e) => {
                        e.stopPropagation();
                        if (!confirm(`Delete "${f.filename}"?`)) return;
                        try {
                          await api.deleteFile(f.file_id || f.filename);
                          setFiles(prev => prev.filter((_, idx) => idx !== i));
                        } catch (err) {
                          alert("Delete failed: " + err.message);
                        }
                      }}
                      style={{
                        cursor: "pointer", fontFamily: FONTS.mono, fontSize: 14,
                        color: COLORS.textDim, transition: "color 0.15s",
                      }}
                      onMouseEnter={e => e.target.style.color = COLORS.red}
                      onMouseLeave={e => e.target.style.color = COLORS.textDim}
                      title="Remove file"
                    >✕</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* Passport Generator */}
      <div style={{ marginTop: 24 }}>
        <SectionTitle icon="lock">Canon Lock — Corpus Passport</SectionTitle>
        <Card glow>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            <div>
              <label style={labelStyle}>Purpose</label>
              <input type="text" placeholder="e.g., Pre-grant verification of NC2.5 core"
                value={purpose} onChange={e => setPurpose(e.target.value)} style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Canon Version</label>
              <input type="text" placeholder="e.g., CANON v1.0"
                value={canonVersion} onChange={e => setCanonVersion(e.target.value)} style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Architectural Status</label>
              <select value={archStatus} onChange={e => setArchStatus(e.target.value)} style={inputStyle}>
                <option value="closed">Closed</option>
                <option value="open">Open</option>
              </select>
            </div>
            <div>
              <label style={labelStyle}>Constraints (semicolon-separated)</label>
              <input type="text" placeholder="e.g., Formal mathematics not evaluated"
                value={constraints} onChange={e => setConstraints(e.target.value)} style={inputStyle} />
            </div>
          </div>
          <div style={{ marginTop: 16, display: "flex", justifyContent: "flex-end" }}>
            <Button icon="lock" onClick={handleCreatePassport} disabled={files.length === 0}>
              Generate Corpus Passport
            </Button>
          </div>
          {passportError && <ErrorBanner message={passportError} />}
          {passport && (
            <div style={{ marginTop: 14, padding: "10px 14px", borderRadius: 4, background: "rgba(34,197,94,0.06)", border: `1px solid rgba(34,197,94,0.15)` }}>
              <div style={{ fontFamily: FONTS.mono, fontSize: 11, color: COLORS.green }}>
                ✓ Corpus Passport generated. Canon Lock active. ID: {passport.passport_id?.slice(0, 12)}... · {passport.files_count} files sealed.
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════
// PAGE: SESSIONS
// ═══════════════════════════════════════════════════════════════════════════

const SessionsPage = () => {
  const [showCreate, setShowCreate] = useState(false);
  const [selectedProviders, setSelectedProviders] = useState(new Set());
  const [executing, setExecuting] = useState(false);
  const [sessionType, setSessionType] = useState("strict_verifier");
  const [sourceSessionId, setSourceSessionId] = useState("");
  const sessions = useApi(() => api.listSessions().then(r => r.sessions), []);
  const passports = useApi(() => api.listPassports().then(r => r.passports), []);

  const toggleProvider = (pid, model) => {
    const key = `${pid}:${model}`;
    setSelectedProviders(prev => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 32 }}>
        <div>
          <h1 style={{ margin: 0, fontFamily: FONTS.display, fontSize: 22, fontWeight: 400, color: COLORS.text }}>
            Verification <span style={{ color: COLORS.gold }}>Sessions</span>
          </h1>
          <p style={{ margin: "6px 0 0", fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted }}>
            Create and execute protocol sessions with isolated interpreter runs.
          </p>
        </div>
        <Button icon="plus" onClick={() => setShowCreate(!showCreate)}>New Session</Button>
      </div>

      {/* Create Session Panel */}
      {showCreate && (
        <Card glow style={{ marginBottom: 24 }}>
          <SectionTitle icon="compass">Session Mode</SectionTitle>
          <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
            {[
              { id: "strict_verifier", label: "Strict Verifier", desc: "Find logical holes, contradictions, gaps" },
              { id: "position_aggregator", label: "Position Aggregator", desc: "Map divergence across a completed session" },
              { id: "formalization", label: "Formalization", desc: "Translate theory into formal structures" },
            ].map(mode => (
              <div key={mode.id} onClick={() => setSessionType(mode.id)} style={{
                flex: 1, padding: "10px 14px", borderRadius: 4, cursor: "pointer",
                background: sessionType === mode.id ? "rgba(217,119,6,0.1)" : COLORS.bg,
                border: `1.5px solid ${sessionType === mode.id ? COLORS.amber : COLORS.border}`,
                transition: "all 0.2s",
              }}>
                <div style={{ fontFamily: FONTS.mono, fontSize: 11, fontWeight: 600, color: sessionType === mode.id ? COLORS.gold : COLORS.text, marginBottom: 4 }}>
                  {mode.label}
                </div>
                <div style={{ fontFamily: FONTS.body, fontSize: 10, color: COLORS.textDim, lineHeight: 1.3 }}>
                  {mode.desc}
                </div>
              </div>
            ))}
          </div>
          {sessionType === "position_aggregator" && sessions.data?.length > 0 && (
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontFamily: FONTS.mono, fontSize: 10, color: COLORS.textDim, display: "block", marginBottom: 4 }}>
                SOURCE SESSION (required)
              </label>
              <select value={sourceSessionId} onChange={e => setSourceSessionId(e.target.value)} style={{
                width: "100%", padding: "8px 10px", fontFamily: FONTS.mono, fontSize: 11,
                background: COLORS.bg, color: COLORS.text, border: `1px solid ${COLORS.border}`,
                borderRadius: 4, outline: "none",
              }}>
                <option value="">Select a completed session...</option>
                {sessions.data.filter(s => s.state === "awaiting_synthesis" || s.state === "completed").map(s => (
                  <option key={s.session_id} value={s.session_id}>
                    {s.session_id.slice(0,8)} — {s.purpose} [{s.state}]
                  </option>
                ))}
              </select>
            </div>
          )}
          <SectionTitle icon="zap">Select Interpreters</SectionTitle>
          <p style={{ fontFamily: FONTS.body, fontSize: 11, color: COLORS.textDim, margin: "0 0 14px" }}>
            {sessionType === "strict_verifier" ? "Minimum 3 recommended · Identical prompt for all · No adaptation per model" : sessionType === "position_aggregator" ? "Select 1 strong model to analyze interpreter outputs" : "Select 1-2 models with strong formal reasoning"}
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
            {PROVIDERS.map(prov => (
              <div key={prov.id} style={{
                padding: "12px 14px", borderRadius: 4,
                background: COLORS.bg, border: `1px solid ${COLORS.border}`,
              }}>
                <div style={{
                  fontFamily: FONTS.mono, fontSize: 11, fontWeight: 600,
                  color: COLORS.gold, marginBottom: 8,
                }}>
                  {prov.name}
                </div>
                {prov.models.map(model => {
                  const key = `${prov.id}:${model}`;
                  const selected = selectedProviders.has(key);
                  return (
                    <div
                      key={model}
                      onClick={() => toggleProvider(prov.id, model)}
                      style={{
                        display: "flex", alignItems: "center", gap: 8,
                        padding: "5px 8px", marginBottom: 3, borderRadius: 3,
                        background: selected ? "rgba(217,119,6,0.08)" : "transparent",
                        border: `1px solid ${selected ? COLORS.amberDark : "transparent"}`,
                        cursor: "pointer",
                        transition: "all 0.15s",
                      }}
                    >
                      <div style={{
                        width: 14, height: 14, borderRadius: 3,
                        border: `1.5px solid ${selected ? COLORS.amber : COLORS.textDim}`,
                        background: selected ? COLORS.amber : "transparent",
                        display: "flex", alignItems: "center", justifyContent: "center",
                      }}>
                        {selected && <span style={{ fontSize: 10, color: "#000", fontWeight: 700 }}>✓</span>}
                      </div>
                      <span style={{
                        fontFamily: FONTS.mono, fontSize: 10,
                        color: selected ? COLORS.text : COLORS.textMuted,
                      }}>
                        {model}
                      </span>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
          <div style={{ marginTop: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontFamily: FONTS.mono, fontSize: 10, color: COLORS.textDim }}>
              {selectedProviders.size} interpreter{selectedProviders.size !== 1 ? "s" : ""} selected
              {selectedProviders.size > 0 && selectedProviders.size < 3 && (
                <span style={{ color: COLORS.amber, marginLeft: 8 }}>⚠ ECR-VP recommends ≥3</span>
              )}
            </span>
            <div style={{ display: "flex", gap: 8 }}>
              <Button variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button icon="play" disabled={selectedProviders.size === 0 || executing || !passports.data?.length}
                onClick={async () => {
                  const latestPassport = passports.data?.[passports.data.length - 1];
                  if (!latestPassport) return alert("Create a Corpus Passport first (Corpus tab).");
                  setExecuting(true);
                  try {
                    const interpreters = [...selectedProviders].map(k => {
                      const [provider, model] = k.split(":");
                      return { provider, model, displayName: `${provider}/${model}` };
                    });
                    const sess = await api.createSession({ passportId: latestPassport.passport_id, interpreters, sessionType, sourceSessionId: sourceSessionId || null });
                    await api.executeSession(sess.session_id, { parallel: true });
                    sessions.reload();
                    setShowCreate(false);
                    setSelectedProviders(new Set());
                  } catch (e) {
                    alert("Execution error: " + e.message);
                  } finally {
                    setExecuting(false);
                  }
                }}>
                {executing ? "Executing..." : "Execute Protocol"}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Session List */}
      <SectionTitle icon="layers">All Sessions</SectionTitle>
      {sessions.loading ? <Spinner /> : !sessions.data?.length ? (
        <EmptyState icon="layers" title="No sessions yet">Create a corpus passport, then start a new session above.</EmptyState>
      ) : [...sessions.data].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).map(session => (
        <Card key={session.session_id} style={{ marginBottom: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                <span style={{ fontFamily: FONTS.mono, fontSize: 10, color: COLORS.textDim }}>{session.session_id?.slice(0,8)}</span>
                <StatusBadge status={session.state} />
              </div>
              <div style={{ fontFamily: FONTS.body, fontSize: 14, color: COLORS.text }}>{session.purpose}</div>
            </div>
            <span style={{ fontFamily: FONTS.mono, fontSize: 10, color: COLORS.textDim }}>
              {new Date(session.created_at).toLocaleDateString()}
            </span>
          </div>
          <GoldDivider style={{ margin: "10px 0" }} />
          <div style={{ fontFamily: FONTS.mono, fontSize: 10, color: COLORS.textDim }}>
            {session.run_count} interpreter run{session.run_count !== 1 ? "s" : ""}
          </div>
        </Card>
      ))}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════
// PAGE: RESULTS VIEWER
// ═══════════════════════════════════════════════════════════════════════════

const ResultsPage = () => {
  const [activeRun, setActiveRun] = useState(0);
  const [responseText, setResponseText] = useState("");
  const [responseLoading, setResponseLoading] = useState(false);
  const [responseMeta, setResponseMeta] = useState(null);
  const [exportState, setExportState] = useState("idle"); // idle | loading | done | error
  const [exportProgress, setExportProgress] = useState(0);
  const sessions = useApi(() => api.listSessions().then(r => r.sessions), []);
  const [selectedSession, setSelectedSession] = useState(null);
  const [sessionDetail, setSessionDetail] = useState(null);

  // Sort sessions newest first
  const sortedSessions = (sessions.data || []).slice().sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

  // Load first session's details
  useEffect(() => {
    if (sortedSessions.length && !selectedSession) {
      const sid = sortedSessions[0].session_id;
      setSelectedSession(sid);
      api.getSession(sid).then(setSessionDetail).catch(() => {});
    }
  }, [sessions.data]);

  // When session changes, reload detail
  const handleSessionChange = (sid) => {
    setSelectedSession(sid);
    setActiveRun(0);
    setResponseText("");
    setResponseMeta(null);
    setSessionDetail(null);
    api.getSession(sid).then(setSessionDetail).catch(() => {});
  };

  const runs = sessionDetail?.runs || [];

  // Load run response when active run changes
  useEffect(() => {
    if (!selectedSession || !runs.length) return;
    const run = runs[activeRun];
    if (!run?.response) {
      setResponseText(""); setResponseMeta(null);
      return;
    }
    setResponseLoading(true);
    api.getRunResponse(selectedSession, run.run_id)
      .then(r => { setResponseText(r.raw_text || ""); setResponseMeta(r); })
      .catch(() => setResponseText("[Error loading response]"))
      .finally(() => setResponseLoading(false));
  }, [activeRun, selectedSession, runs.length]);

  if (sessions.loading) return <Spinner />;
  if (!sessions.data?.length) return (
    <div>
      <h1 style={{ margin: 0, fontFamily: FONTS.display, fontSize: 22, fontWeight: 400, color: COLORS.text }}>
        Interpreter <span style={{ color: COLORS.gold }}>Results</span>
      </h1>
      <div style={{ marginTop: 24 }}>
        <EmptyState icon="eye" title="No completed sessions">Execute a protocol session first to see results here.</EmptyState>
      </div>
    </div>
  );

  const detectedModes = responseMeta?.detected_modes?.map(m => m.mode) || [];
  const missingModes = responseMeta?.missing_modes || [];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontFamily: FONTS.display, fontSize: 22, fontWeight: 400, color: COLORS.text }}>
          Interpreter <span style={{ color: COLORS.gold }}>Results</span>
        </h1>
        <p style={{ margin: "6px 0 0", fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted }}>
          Immutable interpreter outputs — read-only, no editing permitted.
        </p>
      </div>

      {/* Session Selector + Export */}
      <div style={{ marginBottom: 18 }}>
        <label style={{ fontFamily: FONTS.mono, fontSize: 9, color: COLORS.textDim, letterSpacing: "0.1em", textTransform: "uppercase", display: "block", marginBottom: 5 }}>
          Select Session
        </label>
        <div style={{ display: "flex", gap: 8 }}>
          <select
            value={selectedSession || ""}
            onChange={e => handleSessionChange(e.target.value)}
            style={{
              flex: 1, padding: "8px 12px", borderRadius: 4, boxSizing: "border-box",
              background: COLORS.bg, border: `1px solid ${COLORS.border}`,
              color: COLORS.text, fontFamily: FONTS.mono, fontSize: 12, outline: "none",
              cursor: "pointer",
            }}
          >
            {sortedSessions.map(s => (
              <option key={s.session_id} value={s.session_id}>
                {s.session_id?.slice(0,8)} — {s.purpose} — {new Date(s.created_at).toLocaleDateString()} [{s.state}]
              </option>
            ))}
          </select>
          <button
            onClick={() => {
              if (!selectedSession || exportState === "loading") return;
              setExportState("loading");
              setExportProgress(0);
              api.exportSession(selectedSession, (p) => {
                setExportProgress(p < 0 ? -1 : p);
              })
                .then(() => {
                  setExportState("done");
                  setTimeout(() => setExportState("idle"), 2500);
                })
                .catch(e => {
                  setExportState("error");
                  setTimeout(() => setExportState("idle"), 3000);
                });
            }}
            disabled={!selectedSession || !runs.length || exportState === "loading"}
            style={{
              padding: "8px 16px", borderRadius: 4, border: `1px solid ${COLORS.borderGold}`,
              background: "transparent",
              color: exportState === "done" ? COLORS.green : exportState === "error" ? COLORS.red : COLORS.gold,
              fontFamily: FONTS.mono, fontSize: 11, fontWeight: 600,
              letterSpacing: "0.06em",
              cursor: !selectedSession || !runs.length || exportState === "loading" ? "not-allowed" : "pointer",
              opacity: !selectedSession || !runs.length ? 0.4 : 1,
              transition: "all 0.15s", whiteSpace: "nowrap",
              display: "flex", alignItems: "center", gap: 6,
              position: "relative", overflow: "hidden", minWidth: 130,
            }}
          >
            {/* Progress bar background */}
            {exportState === "loading" && (
              <div style={{
                position: "absolute", left: 0, top: 0, bottom: 0,
                width: exportProgress < 0 ? "100%" : `${exportProgress}%`,
                background: exportProgress < 0
                  ? "rgba(184,150,90,0.1)"
                  : "rgba(184,150,90,0.12)",
                transition: exportProgress < 0 ? "none" : "width 0.3s ease",
                animation: exportProgress < 0 ? "exportPulse 1.5s ease-in-out infinite" : "none",
              }} />
            )}
            <span style={{ position: "relative", display: "inline-flex", alignItems: "center", gap: 6, pointerEvents: "none" }}>
              <Icon
                type={exportState === "done" ? "check" : "download"}
                size={13}
                color={exportState === "done" ? COLORS.green : exportState === "error" ? COLORS.red : COLORS.gold}
              />
              {exportState === "loading"
                ? (exportProgress < 0 ? "Exporting..." : `${exportProgress}%`)
                : exportState === "done"
                ? "Downloaded"
                : exportState === "error"
                ? "Failed"
                : "Export ZIP"}
            </span>
          </button>
        </div>
      </div>

      {/* Run Tabs */}
      {runs.length > 0 && (
        <div style={{ display: "flex", gap: 6, marginBottom: 16 }}>
          {runs.map((run, i) => (
            <div key={run.run_id} onClick={() => setActiveRun(i)}
              style={{
                padding: "8px 16px", borderRadius: "4px 4px 0 0",
                background: i === activeRun ? COLORS.bgCard : "transparent",
                border: `1px solid ${i === activeRun ? COLORS.borderGold : COLORS.border}`,
                borderBottom: i === activeRun ? `1px solid ${COLORS.bgCard}` : `1px solid ${COLORS.border}`,
                cursor: "pointer", transition: "all 0.15s",
              }}>
              <div style={{ fontFamily: FONTS.mono, fontSize: 10, fontWeight: 600, color: i === activeRun ? COLORS.gold : COLORS.textDim }}>
                {run.interpreter?.provider}
              </div>
              <div style={{ fontFamily: FONTS.mono, fontSize: 9, color: COLORS.textDim }}>{run.interpreter?.model}</div>
            </div>
          ))}
        </div>
      )}

      {/* Mode Indicators */}
      {responseMeta && (
        <Card style={{ marginBottom: 16, padding: 14 }}>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
            <span style={{ fontFamily: FONTS.mono, fontSize: 9, color: COLORS.textDim, marginRight: 4, textTransform: "uppercase", letterSpacing: "0.1em" }}>Modes:</span>
            {PROTOCOL_MODES.map(m => (
              <ModeTag key={m.key} mode={m.key} detected={!missingModes.includes(m.key) && !missingModes.includes(m.label)} />
            ))}
          </div>
        </Card>
      )}

      {/* Response Content — read-only scrollable viewer */}
      <Card style={{ padding: 0 }}>
        <div style={{ padding: "12px 16px", borderBottom: `1px solid ${COLORS.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Icon type="lock" size={12} color={COLORS.greenMuted} />
            <span style={{ fontFamily: FONTS.mono, fontSize: 9, color: COLORS.greenMuted, letterSpacing: "0.1em", textTransform: "uppercase" }}>Immutable Artifact</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            {responseMeta && (
              <span style={{ fontFamily: FONTS.mono, fontSize: 9, color: COLORS.textDim }}>
                {responseMeta.token_count_input ? `${responseMeta.token_count_input.toLocaleString()} in / ${responseMeta.token_count_output?.toLocaleString()} out` : ""}
              </span>
            )}
            <span style={{ fontFamily: FONTS.mono, fontSize: 9, color: COLORS.textDim }}>
              {responseMeta?.captured_at ? `Captured: ${new Date(responseMeta.captured_at).toLocaleString()}` : ""}
            </span>
          </div>
        </div>
        <div style={{
          padding: "20px 24px", maxHeight: "calc(100vh - 380px)", minHeight: 300,
          overflowY: "auto", fontFamily: FONTS.body, fontSize: 13,
          color: COLORS.text, lineHeight: 1.75, whiteSpace: "pre-wrap",
          userSelect: "text", cursor: "text",
        }}>
          {responseLoading ? <Spinner /> : !responseText ? (
            <div style={{ color: COLORS.textDim, textAlign: "center", padding: 40 }}>No response data for this run.</div>
          ) : (
            responseText.split("\n\n").map((para, i) => {
              // Main section headers (## style or mode names)
              if (para.match(/^#{1,3}\s/) || para.match(/^(Rc|Ri|Ra|Failure|Verdict|Novelty|Declarative|Project)\s/)) {
                return (
                  <div key={i} style={{
                    fontFamily: FONTS.mono, fontSize: 14, fontWeight: 600, color: COLORS.gold,
                    margin: "28px 0 12px", paddingBottom: 8,
                    borderBottom: `1px solid ${COLORS.borderGold}`, letterSpacing: "0.04em",
                  }}>{para.replace(/^#{1,3}\s*/, "")}</div>
                );
              }
              // Sub-headers
              if (para.match(/^\*\*[^*]+\*\*/)) {
                return (
                  <div key={i} style={{
                    fontFamily: FONTS.mono, fontSize: 12, fontWeight: 600, color: COLORS.goldLight,
                    margin: "20px 0 8px",
                  }}>{para.replace(/\*\*/g, "")}</div>
                );
              }
              // Horizontal rule
              if (para.match(/^-{3,}$/)) {
                return <GoldDivider key={i} />;
              }
              return <p key={i} style={{ margin: "0 0 14px" }}>{para}</p>;
            })
          )}
        </div>
      </Card>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════
// PAGE: SYNTHESIS WORKSPACE
// ═══════════════════════════════════════════════════════════════════════════

const SynthesisPage = () => {
  const [activeLayer, setActiveLayer] = useState("overlap");
  const layers = [
    { key: "overlap", label: "Overlap", desc: "Consistent across interpreters", color: COLORS.green },
    { key: "unique", label: "Unique Observations", desc: "Per-interpreter insights", color: COLORS.amber },
    { key: "divergence", label: "Divergence", desc: "Non-understanding & gaps", color: COLORS.red },
  ];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontFamily: FONTS.display, fontSize: 22, fontWeight: 400, color: COLORS.text }}>
          Synthesis <span style={{ color: COLORS.gold }}>Workspace</span>
        </h1>
        <p style={{ margin: "6px 0 0", fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted }}>
          Human-generated coherence map and Author's Response. This layer does not alter interpreter outputs.
        </p>
      </div>

      {/* Human Layer Warning */}
      <div style={{
        padding: "10px 16px", marginBottom: 20, borderRadius: 4,
        background: "rgba(184,150,90,0.06)",
        border: `1px solid ${COLORS.borderGold}`,
        display: "flex", alignItems: "center", gap: 10,
      }}>
        <Icon type="alert" size={14} color={COLORS.gold} />
        <span style={{ fontFamily: FONTS.mono, fontSize: 10, color: COLORS.gold }}>
          HUMAN SYNTHESIS LAYER — All content here is human-generated and clearly separated from interpreter observations.
        </span>
      </div>

      {/* Coherence Map */}
      <SectionTitle icon="grid">Coherence Map</SectionTitle>

      {/* Layer Tabs */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        {layers.map(l => (
          <div
            key={l.key}
            onClick={() => setActiveLayer(l.key)}
            style={{
              flex: 1, padding: "12px 14px", borderRadius: 4,
              background: activeLayer === l.key ? "rgba(184,150,90,0.06)" : COLORS.bgCard,
              border: `1px solid ${activeLayer === l.key ? l.color + "44" : COLORS.border}`,
              cursor: "pointer",
              transition: "all 0.15s",
            }}
          >
            <div style={{
              fontFamily: FONTS.mono, fontSize: 11, fontWeight: 600,
              color: activeLayer === l.key ? l.color : COLORS.textMuted,
              marginBottom: 3,
            }}>
              Layer: {l.label}
            </div>
            <div style={{ fontFamily: FONTS.body, fontSize: 10, color: COLORS.textDim }}>
              {l.desc}
            </div>
          </div>
        ))}
      </div>

      {/* Editor Area */}
      <Card style={{ marginBottom: 24 }}>
        <textarea
          placeholder={
            activeLayer === "overlap"
              ? "Record elements identified consistently by most interpreters. This is the primary indicator of corpus readability..."
              : activeLayer === "unique"
              ? "Record unique observations per interpreter. The goal is not to select a 'correct' view, but to reveal distinct angles..."
              : "Record areas of non-understanding and divergence. This is the most productive output — identifies where the corpus insufficiently fixes invariants..."
          }
          style={{
            width: "100%", minHeight: 180, padding: 14, borderRadius: 4, boxSizing: "border-box",
            background: COLORS.bg, border: `1px solid ${COLORS.border}`,
            color: COLORS.text, fontFamily: FONTS.body, fontSize: 13,
            lineHeight: 1.7, resize: "vertical", outline: "none",
          }}
        />
      </Card>

      {/* Author's Response */}
      <GoldDivider />
      <SectionTitle icon="hash">Author's Response</SectionTitle>
      <p style={{ fontFamily: FONTS.body, fontSize: 11, color: COLORS.textDim, margin: "0 0 14px" }}>
        Mandatory appendix per ECR-VP §2.12. Not a defense — a fixation of intent vs. transmitted structure.
      </p>
      <Card>
        <textarea
          placeholder="Record what interpreters understood correctly, what they misunderstood and why, and where the corpus genuinely requires clarification. The author is prohibited from modifying the corpus within the same verification session..."
          style={{
            width: "100%", minHeight: 200, padding: 14, borderRadius: 4, boxSizing: "border-box",
            background: COLORS.bg, border: `1px solid ${COLORS.border}`,
            color: COLORS.text, fontFamily: FONTS.body, fontSize: 13,
            lineHeight: 1.7, resize: "vertical", outline: "none",
          }}
        />
        <div style={{ marginTop: 12, display: "flex", justifyContent: "flex-end" }}>
          <Button variant="secondary" icon="lock">Seal Author's Response</Button>
        </div>
      </Card>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════
// PAGE: HOW TO USE
// ═══════════════════════════════════════════════════════════════════════════

const GuideStep = ({ number, title, children }) => (
  <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
    <div style={{
      width: 32, height: 32, minWidth: 32, borderRadius: 4,
      background: "rgba(217,119,6,0.1)",
      border: `1px solid ${COLORS.amberDark}`,
      display: "flex", alignItems: "center", justifyContent: "center",
      fontFamily: FONTS.mono, fontSize: 13, fontWeight: 700,
      color: COLORS.amber,
    }}>
      {number}
    </div>
    <div style={{ flex: 1 }}>
      <div style={{
        fontFamily: FONTS.mono, fontSize: 13, fontWeight: 600,
        color: COLORS.gold, marginBottom: 6,
      }}>
        {title}
      </div>
      <div style={{
        fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted,
        lineHeight: 1.75,
      }}>
        {children}
      </div>
    </div>
  </div>
);

const GuideKeyValue = ({ label, children }) => (
  <div style={{ marginBottom: 10 }}>
    <span style={{
      fontFamily: FONTS.mono, fontSize: 10, color: COLORS.goldMuted,
      letterSpacing: "0.08em", textTransform: "uppercase",
    }}>
      {label}:
    </span>{" "}
    <span style={{ fontFamily: FONTS.body, fontSize: 12, color: COLORS.textMuted }}>
      {children}
    </span>
  </div>
);

const GuidePage = () => (
  <div>
    <div style={{ marginBottom: 32 }}>
      <h1 style={{ margin: 0, fontFamily: FONTS.display, fontSize: 22, fontWeight: 400, color: COLORS.text }}>
        How to <span style={{ color: COLORS.gold }}>Use</span>
      </h1>
      <p style={{ margin: "6px 0 0", fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted }}>
        Protocol guide and interface walkthrough
      </p>
    </div>

    {/* ── What is ECR-VP ── */}
    <SectionTitle icon="shield">What is ECR-VP</SectionTitle>
    <Card glow style={{ marginBottom: 28 }}>
      <p style={{
        fontFamily: FONTS.body, fontSize: 14, color: COLORS.text,
        lineHeight: 1.85, margin: 0,
      }}>
        ECR-VP (Epistemic Coherence Review and Verification Protocol) is a formal procedure for
        verifying the structural coherence, readability, and engineering realizability of complex
        architectural corpora — without relying on metrics, optimization, consensus, or feedback
        between interpreters.
      </p>
      <GoldDivider />
      <p style={{
        fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted,
        lineHeight: 1.8, margin: 0, marginBottom: 16,
      }}>
        The protocol uses multiple isolated LLMs as independent, non-causal observers.
        Each interpreter receives the same corpus in a clean session and produces a structured report.
        The interpreters never see each other's outputs, never receive feedback from the author,
        and are never tuned toward any expected result. Final synthesis is always performed by a human.
      </p>

      <div style={{
        padding: "14px 18px", borderRadius: 4,
        background: COLORS.bg,
        border: `1px solid ${COLORS.border}`,
      }}>
        <div style={{
          fontFamily: FONTS.mono, fontSize: 10, color: COLORS.gold,
          letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 12,
        }}>
          Core Principles
        </div>
        <GuideKeyValue label="Identity fixation">
          The corpus is sealed before analysis begins — no substitution, no drift, no edits during verification.
        </GuideKeyValue>
        <GuideKeyValue label="Interpreter isolation">
          Each interpreter works alone. No cross-contamination, no hints, no author influence.
        </GuideKeyValue>
        <GuideKeyValue label="Strict mode separation">
          Hypotheses, invariants, realizability, risks, and verdict are kept in separate logical regimes that do not mix.
        </GuideKeyValue>
        <GuideKeyValue label="No numerical scoring">
          The protocol deliberately excludes ratings, rankings, and aggregation. Only qualitative axes.
        </GuideKeyValue>
        <GuideKeyValue label="Human synthesis is mandatory">
          The final coherence map and Author's Response are produced by a human, not automated.
        </GuideKeyValue>
      </div>

      <GoldDivider />

      <p style={{
        fontFamily: FONTS.body, fontSize: 12, color: COLORS.textDim,
        lineHeight: 1.75, margin: 0, fontStyle: "italic",
      }}>
        ECR-VP does not claim objective truth or universal verification. Its purpose is to ensure
        that an architecture is readable, verifiable, and reproducibly coherent without the author's
        participation — and to identify structural weak points before moving to grants, pilots,
        or engineering implementation.
      </p>
    </Card>

    {/* ── What this shell does ── */}
    <SectionTitle icon="compass">What This Shell Does</SectionTitle>
    <Card style={{ marginBottom: 28 }}>
      <p style={{
        fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted,
        lineHeight: 1.8, margin: "0 0 14px",
      }}>
        This application is an execution shell for ECR-VP v1.0. It handles the operational side of
        the protocol: file management, cryptographic hashing, session orchestration, interpreter
        isolation, immutable artifact storage, and providing a workspace for human synthesis. 
        It does not interpret, evaluate, or draw conclusions — that responsibility belongs to you.
      </p>
      <div style={{
        display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12,
      }}>
        <div style={{
          padding: "10px 14px", borderRadius: 4,
          background: "rgba(34,197,94,0.04)", border: `1px solid rgba(34,197,94,0.12)`,
        }}>
          <div style={{ fontFamily: FONTS.mono, fontSize: 10, color: COLORS.greenMuted, marginBottom: 6, letterSpacing: "0.08em" }}>
            ✓ THE SHELL DOES
          </div>
          <div style={{ fontFamily: FONTS.body, fontSize: 11, color: COLORS.textMuted, lineHeight: 1.7 }}>
            Fix corpus identity (SHA-256 hashes) · Generate Corpus Passports · Send identical
            input to all interpreters · Enforce mode separation · Store outputs as immutable artifacts ·
            Provide a workspace for human synthesis
          </div>
        </div>
        <div style={{
          padding: "10px 14px", borderRadius: 4,
          background: "rgba(239,68,68,0.04)", border: `1px solid rgba(239,68,68,0.12)`,
        }}>
          <div style={{ fontFamily: FONTS.mono, fontSize: 10, color: COLORS.redMuted, marginBottom: 6, letterSpacing: "0.08em" }}>
            ✗ THE SHELL DOES NOT
          </div>
          <div style={{ fontFamily: FONTS.body, fontSize: 11, color: COLORS.textMuted, lineHeight: 1.7 }}>
            Score or rank results · Aggregate or average interpretations · Give feedback to
            interpreters · Learn from protocol outputs · Adapt prompts per model · Automate
            correctness evaluation
          </div>
        </div>
      </div>
    </Card>

    {/* ── Step by step ── */}
    <SectionTitle icon="zap">Interface Walkthrough</SectionTitle>
    <Card style={{ marginBottom: 28 }}>
      <GuideStep number={1} title="Upload your corpus → Corpus page">
        Go to the <strong style={{ color: COLORS.gold }}>Corpus</strong> tab.
        Drag and drop all files that constitute your architecture:
        PDFs, markdown, code, diagrams, appendices, the Canon document.
        The system computes SHA-256 hashes for every file automatically.
        File order matters — it becomes the canonical loading order for interpreters.
      </GuideStep>

      <GuideStep number={2} title="Generate Corpus Passport (Canon Lock)">
        Still on the Corpus page, fill in the passport fields:
        the purpose of this verification session, the canon version,
        architectural status (open or closed), and any scope constraints.
        Click <strong style={{ color: COLORS.amber }}>Generate Corpus Passport</strong>.
        From this moment, the corpus is frozen — any change requires a new session with new hashes.
      </GuideStep>

      <GuideStep number={3} title="Choose session mode and interpreters → Sessions page">
        Go to the <strong style={{ color: COLORS.gold }}>Sessions</strong> tab.
        Click <strong style={{ color: COLORS.amber }}>New Session</strong>.
        First, choose a <strong style={{ color: COLORS.gold }}>Session Mode</strong>:{" "}
        <strong style={{ color: COLORS.amber }}>Strict Verifier</strong> for finding logical holes and contradictions (the core protocol),{" "}
        <strong style={{ color: COLORS.amber }}>Formalization</strong> for translating theory into pseudocode and formal definitions, or{" "}
        <strong style={{ color: COLORS.amber }}>Position Aggregator</strong> to map divergence across a completed session (this mode intentionally breaks isolation and is a convenience layer, not a verification instrument).
        Then select which LLM interpreters to use.
        For Strict Verifier, the protocol recommends at least 3 and preferably 5,
        with different architectural lineages (e.g., Claude Opus 4.6 + GPT-5.2 + DeepSeek R1 + Grok 4 + a local model).
        The system sends the exact same prompt and corpus to every interpreter — no adaptation per model.
      </GuideStep>

      <GuideStep number={4} title="Execute the protocol">
        Click <strong style={{ color: COLORS.amber }}>Execute Protocol</strong>.
        The system opens a clean session for each interpreter,
        sends the Corpus Passport, then the files in canonical order,
        then the fixed completion phrase.
        For large corpora, files are sent in sequential segments with an instruction
        not to form conclusions until the final message.
        You can monitor progress in real time on the session card.
      </GuideStep>

      <GuideStep number={5} title="Review interpreter outputs → Results page">
        Once all runs complete, go to the <strong style={{ color: COLORS.gold }}>Results</strong> tab.
        Each interpreter's report is stored as an immutable artifact —
        it cannot be edited, rewritten, or merged.
        The system detects mode boundaries (Rc, Ri, Ra, etc.) and flags
        missing or out-of-order modes. Use the tabs to switch between interpreters
        and compare their reports side by side.
      </GuideStep>

      <GuideStep number={6} title="Build the Coherence Map → Synthesis page">
        Go to the <strong style={{ color: COLORS.gold }}>Synthesis</strong> tab.
        This is the human layer — only you work here, not the machine.
        Build the coherence map in three layers:{" "}
        <strong style={{ color: COLORS.green }}>Overlap</strong> (what most interpreters agree on — the primary indicator of corpus readability),{" "}
        <strong style={{ color: COLORS.amber }}>Unique Observations</strong> (distinct angles from individual interpreters),{" "}
        <strong style={{ color: COLORS.red }}>Divergence</strong> (non-understanding, gaps, and contradictions — the most productive output).
      </GuideStep>

      <GuideStep number={7} title="Write the Author's Response">
        Below the coherence map, write the mandatory Author's Response appendix.
        Record what was understood correctly, what was misunderstood and why,
        and where the corpus genuinely requires clarification.
        This is not a defense — it is a fixation of mismatches between your intent
        and the structure that was actually transmitted.
        You cannot modify the corpus in the same session.
        Click <strong style={{ color: COLORS.gold }}>Seal Author's Response</strong> to finalize.
      </GuideStep>
    </Card>

    {/* ── Repeat cycles ── */}
    <SectionTitle icon="clock">After Verification</SectionTitle>
    <Card>
      <p style={{
        fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted,
        lineHeight: 1.8, margin: "0 0 14px",
      }}>
        If the session reveals gaps, ambiguities, or structural drift, revise your corpus
        and run a new session. Each new session gets a fresh Corpus Passport with new hashes
        and a new date. You can compare coherence maps across sessions:
      </p>
      <div style={{
        padding: "12px 16px", borderRadius: 4,
        background: COLORS.bg, border: `1px solid ${COLORS.border}`,
        fontFamily: FONTS.body, fontSize: 12, color: COLORS.textMuted,
        lineHeight: 1.8,
      }}>
        <span style={{ color: COLORS.green }}>↑ Overlap grows + ↓ Divergence shrinks</span>
        {" → "}readability and fixation improving.
        <br />
        <span style={{ color: COLORS.red }}>↓ Overlap shrinks + ↑ Divergence grows</span>
        {" → "}architectural drift — consider rollback or canon clarification.
      </div>
      <GoldDivider />
      <p style={{
        fontFamily: FONTS.body, fontSize: 12, color: COLORS.textDim,
        lineHeight: 1.75, margin: 0,
      }}>
        The corpus is considered ready for external presentation when independent
        interpreters consistently identify the engineering core, correctly understand key
        prohibitions, and describe an implementable middleware layer without inventing
        critical definitions. If interpreters repeatedly request operational criteria
        the corpus does not provide, it is not yet ready — regardless of conceptual strength.
      </p>
    </Card>
  </div>
);

// ═══════════════════════════════════════════════════════════════════════════
// PAGE: HOW TO INSTALL
// ═══════════════════════════════════════════════════════════════════════════

const InstallStep = ({ number, title, children }) => (
  <div style={{ display: "flex", gap: 16, marginBottom: 20 }}>
    <div style={{
      width: 32, height: 32, minWidth: 32, borderRadius: 4,
      background: "rgba(34,197,94,0.1)",
      border: `1px solid ${COLORS.greenDark}`,
      display: "flex", alignItems: "center", justifyContent: "center",
      fontFamily: FONTS.mono, fontSize: 13, fontWeight: 700,
      color: COLORS.green,
    }}>
      {number}
    </div>
    <div style={{ flex: 1 }}>
      <div style={{
        fontFamily: FONTS.mono, fontSize: 13, fontWeight: 600,
        color: COLORS.gold, marginBottom: 6,
      }}>
        {title}
      </div>
      <div style={{
        fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted,
        lineHeight: 1.75,
      }}>
        {children}
      </div>
    </div>
  </div>
);

const CodeBlock = ({ children }) => (
  <pre style={{
    padding: "12px 16px", borderRadius: 4, margin: "8px 0",
    background: COLORS.bg, border: `1px solid ${COLORS.border}`,
    fontFamily: FONTS.mono, fontSize: 11, color: COLORS.green,
    lineHeight: 1.7, overflowX: "auto", whiteSpace: "pre-wrap",
  }}>{children}</pre>
);

const InstallPage = () => (
  <div>
    <div style={{ marginBottom: 32 }}>
      <h1 style={{ margin: 0, fontFamily: FONTS.display, fontSize: 22, fontWeight: 400, color: COLORS.text }}>
        How to <span style={{ color: COLORS.gold }}>Install</span>
      </h1>
      <p style={{ margin: "6px 0 0", fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted }}>
        Local installation guide — everything runs on your machine
      </p>
    </div>

    {/* Prerequisites */}
    <SectionTitle icon="shield">Prerequisites</SectionTitle>
    <Card glow style={{ marginBottom: 28 }}>
      <p style={{ fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted, lineHeight: 1.8, margin: "0 0 16px" }}>
        ECR-VP runs entirely on your local machine. You need two things installed:
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
        <div style={{ padding: "12px 16px", borderRadius: 4, background: COLORS.bg, border: `1px solid ${COLORS.border}` }}>
          <div style={{ fontFamily: FONTS.mono, fontSize: 11, fontWeight: 600, color: COLORS.amber, marginBottom: 4 }}>
            Python 3.10+
          </div>
          <div style={{ fontFamily: FONTS.body, fontSize: 11, color: COLORS.textDim, lineHeight: 1.6 }}>
            Backend server. Download from{" "}
            <a href="https://python.org" target="_blank" rel="noopener noreferrer" style={{ color: COLORS.gold, textDecoration: "none" }}>python.org</a>
            {" "} — check "Add to PATH" during installation.
          </div>
        </div>
        <div style={{ padding: "12px 16px", borderRadius: 4, background: COLORS.bg, border: `1px solid ${COLORS.border}` }}>
          <div style={{ fontFamily: FONTS.mono, fontSize: 11, fontWeight: 600, color: COLORS.amber, marginBottom: 4 }}>
            Node.js 18+
          </div>
          <div style={{ fontFamily: FONTS.body, fontSize: 11, color: COLORS.textDim, lineHeight: 1.6 }}>
            Frontend dev server. Download from{" "}
            <a href="https://nodejs.org" target="_blank" rel="noopener noreferrer" style={{ color: COLORS.gold, textDecoration: "none" }}>nodejs.org</a>
            {" "} — LTS version recommended.
          </div>
        </div>
      </div>
    </Card>

    {/* Installation Steps */}
    <SectionTitle icon="zap">Installation Steps</SectionTitle>
    <Card style={{ marginBottom: 28 }}>
      <InstallStep number={1} title="Clone or download the repository">
        <CodeBlock>{"git clone https://github.com/petronushowcore-mx/ECR-VP.git\ncd ECR-VP"}</CodeBlock>
        Or download the ZIP from GitHub and extract it.
      </InstallStep>

      <InstallStep number={2} title="Set up the Python backend">
        <CodeBlock>{"cd backend\npython -m venv venv\n\n# Windows:\n.\\venv\\Scripts\\activate\n\n# macOS/Linux:\n# source venv/bin/activate\n\npip install -r requirements.txt"}</CodeBlock>
      </InstallStep>

      <InstallStep number={3} title="Configure API keys">
        Create a file <strong style={{ color: COLORS.gold }}>backend/.env</strong> and add the API keys for the providers you want to use:
        <CodeBlock>{"ANTHROPIC_API_KEY=sk-ant-...\nOPENAI_API_KEY=sk-...\nGOOGLE_API_KEY=...\nDEEPSEEK_API_KEY=sk-...\nXAI_API_KEY=xai-...\nPERPLEXITY_API_KEY=pplx-...\nMISTRAL_API_KEY=...\nAZURE_API_KEY=..."}</CodeBlock>
        <span style={{ fontFamily: FONTS.body, fontSize: 12, color: COLORS.textDim }}>
          You only need keys for providers you plan to use. At minimum, one cloud provider key is enough.
        </span>
      </InstallStep>

      <InstallStep number={4} title="Start the backend">
        <CodeBlock>{"cd backend\n.\\venv\\Scripts\\activate\npython -m uvicorn app.main:app --reload --port 8000"}</CodeBlock>
        Wait for <strong style={{ color: COLORS.green }}>Application startup complete</strong>.
      </InstallStep>

      <InstallStep number={5} title="Start the frontend (in a new terminal)">
        <CodeBlock>{"cd frontend\nnpm install\nnpm run dev"}</CodeBlock>
        Open <strong style={{ color: COLORS.amber }}>http://localhost:3000</strong> in your browser.
      </InstallStep>
    </Card>

    {/* Local Models */}
    <SectionTitle icon="compass">Local Models with Ollama (Free)</SectionTitle>
    <Card glow style={{ marginBottom: 28 }}>
      <p style={{ fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted, lineHeight: 1.8, margin: "0 0 16px" }}>
        ECR-VP supports <strong style={{ color: COLORS.gold }}>Ollama</strong> for running open-source models locally — completely free, no API keys needed.
        Ollama must be installed separately.
      </p>
      <div style={{ padding: "14px 18px", borderRadius: 4, background: COLORS.bg, border: `1px solid ${COLORS.border}`, marginBottom: 14 }}>
        <div style={{ fontFamily: FONTS.mono, fontSize: 10, color: COLORS.amber, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 10 }}>
          Ollama Setup
        </div>
        <GuideKeyValue label="1. Install">
          Download from{" "}
          <a href="https://ollama.com" target="_blank" rel="noopener noreferrer" style={{ color: COLORS.gold, textDecoration: "none" }}>ollama.com</a>
          {" "}(Windows, macOS, Linux)
        </GuideKeyValue>
        <GuideKeyValue label="2. Pull a model">
          <span style={{ fontFamily: FONTS.mono, fontSize: 11, color: COLORS.green }}>ollama pull llama3.1:8b</span>
          {" "}(8 GB VRAM) or{" "}
          <span style={{ fontFamily: FONTS.mono, fontSize: 11, color: COLORS.green }}>ollama pull qwen2.5:14b</span>
          {" "}(16 GB VRAM)
        </GuideKeyValue>
        <GuideKeyValue label="3. Run">
          <span style={{ fontFamily: FONTS.mono, fontSize: 11, color: COLORS.green }}>ollama serve</span>
          {" "} — it runs on port 11434 by default. ECR-VP detects it automatically.
        </GuideKeyValue>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
        {[
          { name: "llama3.3:70b", vram: "48 GB+", tier: "Flagship" },
          { name: "qwen3:72b", vram: "48 GB+", tier: "Flagship" },
          { name: "qwen2.5:14b", vram: "16 GB", tier: "Standard" },
          { name: "llama3.1:8b", vram: "8 GB", tier: "Fast" },
          { name: "deepseek-r1:14b", vram: "16 GB", tier: "Reasoning" },
          { name: "mistral:7b", vram: "8 GB", tier: "Fast" },
        ].map(m => (
          <div key={m.name} style={{ padding: "8px 10px", borderRadius: 4, background: COLORS.bgCard, border: `1px solid ${COLORS.border}` }}>
            <div style={{ fontFamily: FONTS.mono, fontSize: 10, color: COLORS.gold }}>{m.name}</div>
            <div style={{ fontFamily: FONTS.mono, fontSize: 9, color: COLORS.textDim }}>{m.vram} · {m.tier}</div>
          </div>
        ))}
      </div>
      <p style={{ fontFamily: FONTS.body, fontSize: 11, color: COLORS.textDim, margin: "12px 0 0", fontStyle: "italic" }}>
        Local models are free and private — your data never leaves your machine.
        For best ECR-VP results, combine at least one cloud model with one local model.
      </p>
    </Card>

    {/* Cloud API Keys */}
    <SectionTitle icon="hash">Cloud Provider API Keys</SectionTitle>
    <Card style={{ marginBottom: 28 }}>
      <p style={{ fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted, lineHeight: 1.8, margin: "0 0 14px" }}>
        Get API keys from each provider's developer portal. ECR-VP uses your own keys (BYOK model) — you pay directly to the provider at their standard rates.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        {[
          { provider: "Anthropic (Claude)", url: "console.anthropic.com", env: "ANTHROPIC_API_KEY" },
          { provider: "OpenAI (GPT)", url: "platform.openai.com", env: "OPENAI_API_KEY" },
          { provider: "Google (Gemini)", url: "aistudio.google.com", env: "GOOGLE_API_KEY" },
          { provider: "DeepSeek", url: "platform.deepseek.com", env: "DEEPSEEK_API_KEY" },
          { provider: "xAI (Grok)", url: "console.x.ai", env: "XAI_API_KEY" },
          { provider: "Perplexity", url: "docs.perplexity.ai", env: "PERPLEXITY_API_KEY" },
          { provider: "Mistral", url: "console.mistral.ai", env: "MISTRAL_API_KEY" },
          { provider: "Microsoft (Phi)", url: "ai.azure.com", env: "AZURE_API_KEY" },
        ].map(p => (
          <div key={p.env} style={{ padding: "8px 12px", borderRadius: 4, background: COLORS.bg, border: `1px solid ${COLORS.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontFamily: FONTS.mono, fontSize: 10, color: COLORS.gold }}>{p.provider}</div>
              <div style={{ fontFamily: FONTS.mono, fontSize: 9, color: COLORS.textDim }}>{p.url}</div>
            </div>
            <span style={{ fontFamily: FONTS.mono, fontSize: 9, color: COLORS.greenMuted }}>{p.env}</span>
          </div>
        ))}
      </div>
    </Card>
  </div>
);

// ═══════════════════════════════════════════════════════════════════════════
// APP BACKGROUND — Semantic Field Animation (80 particles, gold↔purple)
// ═══════════════════════════════════════════════════════════════════════════

const AppBackground = () => {
  const canvasRef = useRef(null);
  const mouseRef = useRef({ x: -1000, y: -1000 });
  const frameRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let animId;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const PARTICLE_COUNT = 250;
    const particles = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        radius: Math.random() * 2.0 + 0.5,
        baseOpacity: Math.random() * 0.35 + 0.1,
        pulsePhase: Math.random() * Math.PI * 2,
        colorPhase: Math.random() * Math.PI * 2,
        colorSpeed: 0.002 + Math.random() * 0.008,
      });
    }

    const connections = [];
    const MOUSE_RADIUS = 160;
    const CONNECT_DIST = 110;

    const lerp = (a, b, t) => a + (b - a) * t;
    const goldR = 194, goldG = 160, goldB = 90;
    const purpR = 150, purpG = 80, purpB = 210;

    let globalPhase = Math.random() * Math.PI * 2;

    const animate = () => {
      frameRef.current++;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const mx = mouseRef.current.x;
      const my = mouseRef.current.y;

      globalPhase += 0.001;

      for (const p of particles) {
        // Move
        p.x += p.vx;
        p.y += p.vy;
        p.pulsePhase += 0.006;
        p.colorPhase += p.colorSpeed;

        // Wrap
        if (p.x < 0) p.x += canvas.width;
        if (p.x > canvas.width) p.x -= canvas.width;
        if (p.y < 0) p.y += canvas.height;
        if (p.y > canvas.height) p.y -= canvas.height;

        // Very gentle mouse push (not attraction — just brightness boost)
        const dmx = mx - p.x;
        const dmy = my - p.y;
        const distMouse = Math.sqrt(dmx * dmx + dmy * dmy);

        // Subtle drift — no strong attraction that clusters them
        if (distMouse < MOUSE_RADIUS && distMouse > 30) {
          p.vx += (dmx / distMouse) * 0.002;
          p.vy += (dmy / distMouse) * 0.002;
        }

        // Speed limit and damping
        const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
        if (speed > 0.5) {
          p.vx *= 0.5 / speed;
          p.vy *= 0.5 / speed;
        }
        p.vx *= 0.999;
        p.vy *= 0.999;

        // Per-particle color: own phase + global drift
        const t = Math.sin(p.colorPhase + globalPhase) * 0.5 + 0.5;
        const cR = lerp(goldR, purpR, t);
        const cG = lerp(goldG, purpG, t);
        const cB = lerp(goldB, purpB, t);

        // Pulse + mouse proximity boost
        const pulse = Math.sin(p.pulsePhase) * 0.12 + 0.88;
        const mouseBrightness = distMouse < MOUSE_RADIUS ? 1 + (1 - distMouse / MOUSE_RADIUS) * 0.8 : 1;
        const alpha = p.baseOpacity * pulse * mouseBrightness;
        const r = p.radius * (distMouse < MOUSE_RADIUS ? 1 + (1 - distMouse / MOUSE_RADIUS) * 0.5 : 1);

        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${cR|0}, ${cG|0}, ${cB|0}, ${Math.min(alpha, 0.7)})`;
        ctx.fill();

        // Glow near mouse
        if (distMouse < MOUSE_RADIUS * 0.7) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, r * 2.5, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${cR|0}, ${cG|0}, ${cB|0}, ${alpha * 0.06})`;
          ctx.fill();
        }
      }

      // Global avg color for connections
      const gt = Math.sin(globalPhase * 1.3) * 0.5 + 0.5;
      const gcR = lerp(goldR, purpR, gt);
      const gcG = lerp(goldG, purpG, gt);
      const gcB = lerp(goldB, purpB, gt);

      // Mouse-proximity connections
      for (let i = 0; i < particles.length; i++) {
        const a = particles[i];
        const da = Math.sqrt((mx - a.x) ** 2 + (my - a.y) ** 2);
        if (da > MOUSE_RADIUS) continue;
        for (let j = i + 1; j < particles.length; j++) {
          const b = particles[j];
          const db = Math.sqrt((mx - b.x) ** 2 + (my - b.y) ** 2);
          if (db > MOUSE_RADIUS) continue;
          const dist = Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);
          if (dist < CONNECT_DIST) {
            const strength = (1 - dist / CONNECT_DIST) * (1 - da / MOUSE_RADIUS) * (1 - db / MOUSE_RADIUS);
            connections.push({
              x1: a.x, y1: a.y, x2: b.x, y2: b.y,
              opacity: strength * 0.4,
              decay: 0.004 + Math.random() * 0.005,
            });
          }
        }
      }

      // Draw and decay trails
      for (let i = connections.length - 1; i >= 0; i--) {
        const c = connections[i];
        c.opacity -= c.decay;
        if (c.opacity <= 0) { connections.splice(i, 1); continue; }
        ctx.beginPath();
        ctx.moveTo(c.x1, c.y1);
        ctx.lineTo(c.x2, c.y2);
        ctx.strokeStyle = `rgba(${gcR|0}, ${gcG|0}, ${gcB|0}, ${c.opacity})`;
        ctx.lineWidth = c.opacity * 1.5;
        ctx.stroke();
      }

      // Ambient connections (skip-sample for performance with 250)
      if (frameRef.current % 6 === 0) {
        for (let i = 0; i < particles.length; i += 3) {
          for (let j = i + 1; j < particles.length; j += 3) {
            const a = particles[i], b = particles[j];
            const dx = a.x - b.x, dy = a.y - b.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 55) {
              const alpha = (1 - dist / 55) * 0.025;
              ctx.beginPath();
              ctx.moveTo(a.x, a.y);
              ctx.lineTo(b.x, b.y);
              ctx.strokeStyle = `rgba(${gcR * 0.6 |0}, ${gcG * 0.6 |0}, ${gcB * 0.6 |0}, ${alpha})`;
              ctx.lineWidth = 0.4;
              ctx.stroke();
            }
          }
        }
      }

      animId = requestAnimationFrame(animate);
    };

    animate();

    const handleMouse = (e) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };
    window.addEventListener("mousemove", handleMouse);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", handleMouse);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed", top: 0, left: 0,
        width: "100%", height: "100%",
        pointerEvents: "none", zIndex: 0,
      }}
    />
  );
};

// ═══════════════════════════════════════════════════════════════════════════
// FOOTER
// ═══════════════════════════════════════════════════════════════════════════

const Footer = () => (
  <footer style={{
    padding: "16px 0",
    marginTop: 40,
    borderTop: `1px solid ${COLORS.border}`,
    textAlign: "center",
  }}>
    <span style={{
      fontFamily: FONTS.mono,
      fontSize: 10,
      color: COLORS.textDim,
      letterSpacing: "0.06em",
    }}>
      Inspired by{" "}
      <a
        href="https://github.com/petronushowcore-mx/ECR-VP"
        target="_blank"
        rel="noopener noreferrer"
        style={{ color: COLORS.goldMuted, textDecoration: "none", borderBottom: `1px dotted ${COLORS.borderGold}` }}
      >
        Navigational Cybernetics 2.5
      </a>
      {" "}(
      <a
        href="https://www.linkedin.com/in/max-barzenkov-b03441131"
        target="_blank"
        rel="noopener noreferrer"
        style={{ color: "#A78BFA", textDecoration: "none", borderBottom: `1px dotted #7C3AED` }}
      >
        MxBv
      </a>
      )
    </span>
  </footer>
);

// ═══════════════════════════════════════════════════════════════════════════
// LICENSE GATE
// ═══════════════════════════════════════════════════════════════════════════

const LICENSE_STORAGE_KEY = "ecr-vp-license";

// Animated semantic field background
const SemanticField = () => {
  const canvasRef = useRef(null);
  const mouseRef = useRef({ x: -1000, y: -1000 });
  const particlesRef = useRef([]);
  const connectionsRef = useRef([]);
  const frameRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let animId;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    // Init particles
    const PARTICLE_COUNT = 60;
    const particles = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        radius: Math.random() * 1.5 + 0.5,
        opacity: Math.random() * 0.4 + 0.1,
        pulsePhase: Math.random() * Math.PI * 2,
      });
    }
    particlesRef.current = particles;

    // Connection trails: { x1, y1, x2, y2, opacity, decay }
    const connections = [];
    connectionsRef.current = connections;

    const MOUSE_RADIUS = 200;
    const CONNECT_DIST = 140;

    const animate = () => {
      frameRef.current++;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const mx = mouseRef.current.x;
      const my = mouseRef.current.y;

      // Update particles
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        p.pulsePhase += 0.01;

        // Wrap around
        if (p.x < -20) p.x = canvas.width + 20;
        if (p.x > canvas.width + 20) p.x = -20;
        if (p.y < -20) p.y = canvas.height + 20;
        if (p.y > canvas.height + 20) p.y = -20;

        // Mouse attraction (subtle)
        const dmx = mx - p.x;
        const dmy = my - p.y;
        const distMouse = Math.sqrt(dmx * dmx + dmy * dmy);
        if (distMouse < MOUSE_RADIUS && distMouse > 10) {
          p.vx += (dmx / distMouse) * 0.008;
          p.vy += (dmy / distMouse) * 0.008;
        }

        // Dampen velocity
        p.vx *= 0.998;
        p.vy *= 0.998;

        // Draw particle
        const pulse = Math.sin(p.pulsePhase) * 0.15 + 0.85;
        const nearMouse = distMouse < MOUSE_RADIUS ? 1 + (1 - distMouse / MOUSE_RADIUS) * 2 : 1;
        const alpha = p.opacity * pulse * nearMouse;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius * nearMouse, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(184, 150, 90, ${Math.min(alpha, 0.8)})`;
        ctx.fill();

        // Glow for nearby particles
        if (nearMouse > 1.3) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.radius * nearMouse * 3, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(217, 119, 6, ${alpha * 0.1})`;
          ctx.fill();
        }
      }

      // Find new connections near mouse
      for (let i = 0; i < particles.length; i++) {
        const a = particles[i];
        const da = Math.sqrt((mx - a.x) ** 2 + (my - a.y) ** 2);
        if (da > MOUSE_RADIUS) continue;

        for (let j = i + 1; j < particles.length; j++) {
          const b = particles[j];
          const db = Math.sqrt((mx - b.x) ** 2 + (my - b.y) ** 2);
          if (db > MOUSE_RADIUS) continue;

          const dist = Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);
          if (dist < CONNECT_DIST) {
            const strength = (1 - dist / CONNECT_DIST) * (1 - da / MOUSE_RADIUS) * (1 - db / MOUSE_RADIUS);
            connections.push({
              x1: a.x, y1: a.y, x2: b.x, y2: b.y,
              opacity: strength * 0.6,
              decay: 0.003 + Math.random() * 0.004,
            });
          }
        }
      }

      // Draw and decay connections (trails)
      for (let i = connections.length - 1; i >= 0; i--) {
        const c = connections[i];
        c.opacity -= c.decay;
        if (c.opacity <= 0) {
          connections.splice(i, 1);
          continue;
        }

        ctx.beginPath();
        ctx.moveTo(c.x1, c.y1);
        ctx.lineTo(c.x2, c.y2);
        ctx.strokeStyle = `rgba(184, 150, 90, ${c.opacity})`;
        ctx.lineWidth = c.opacity * 1.5;
        ctx.stroke();
      }

      // Ambient connections between close particles (very subtle)
      if (frameRef.current % 3 === 0) {
        for (let i = 0; i < particles.length; i++) {
          for (let j = i + 1; j < particles.length; j++) {
            const a = particles[i], b = particles[j];
            const dist = Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);
            if (dist < 80) {
              const alpha = (1 - dist / 80) * 0.04;
              ctx.beginPath();
              ctx.moveTo(a.x, a.y);
              ctx.lineTo(b.x, b.y);
              ctx.strokeStyle = `rgba(107, 90, 62, ${alpha})`;
              ctx.lineWidth = 0.5;
              ctx.stroke();
            }
          }
        }
      }

      animId = requestAnimationFrame(animate);
    };

    animate();

    const handleMouse = (e) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };
    window.addEventListener("mousemove", handleMouse);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", handleMouse);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed", top: 0, left: 0,
        width: "100%", height: "100%",
        pointerEvents: "none", zIndex: 0,
      }}
    />
  );
};

const LicenseGate = ({ onUnlock }) => {
  const [key, setKey] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);

  // Check saved license on mount
  useEffect(() => {
    const saved = localStorage.getItem(LICENSE_STORAGE_KEY);
    if (saved) {
      validateKey(saved, true);
    } else {
      setChecking(false);
    }
  }, []);

  const validateKey = async (licenseKey, silent = false) => {
    if (!silent) setLoading(true);
    setError(null);
    try {
      const result = await api.validateLicense(licenseKey);
      if (result.valid) {
        localStorage.setItem(LICENSE_STORAGE_KEY, licenseKey);
        onUnlock({
          key: licenseKey,
          customerName: result.customer_name || "",
          expiresAt: result.expires_at || null,
          status: result.status || "active",
        });
      } else {
        localStorage.removeItem(LICENSE_STORAGE_KEY);
        if (!silent) setError(result.error || "Invalid or expired license key");
        setChecking(false);
      }
    } catch (e) {
      // If backend is down, allow offline grace
      const saved = localStorage.getItem(LICENSE_STORAGE_KEY);
      if (saved && silent) {
        onUnlock({ key: saved, customerName: "", expiresAt: null, status: "offline" });
      } else {
        if (!silent) setError("Cannot reach license server. Check backend connection.");
        setChecking(false);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = () => {
    const trimmed = key.trim();
    if (!trimmed) return;
    validateKey(trimmed);
  };

  // Show nothing while checking saved license
  if (checking) return (
    <div style={{
      minHeight: "100vh", background: COLORS.bg,
      display: "flex", alignItems: "center", justifyContent: "center",
    }}>
      <Spinner />
    </div>
  );

  return (
    <div style={{
      minHeight: "100vh", background: COLORS.bg,
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: 20, position: "relative", overflow: "hidden",
    }}>
      <SemanticField />
      <div style={{ width: "100%", maxWidth: 460, position: "relative", zIndex: 1 }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{
            fontFamily: FONTS.mono, fontSize: 28, fontWeight: 700,
            color: COLORS.gold, letterSpacing: "0.08em",
          }}>
            ECR-VP
          </div>
          <div style={{
            fontFamily: FONTS.mono, fontSize: 10,
            color: COLORS.textDim, letterSpacing: "0.2em",
            marginTop: 6, textTransform: "uppercase",
          }}>
            Verification Protocol Shell
          </div>
          <div style={{
            height: 2, width: 48, margin: "16px auto 0",
            background: `linear-gradient(90deg, transparent, ${COLORS.amber}, ${COLORS.gold}, ${COLORS.amber}, transparent)`,
            borderRadius: 1,
          }} />
        </div>

        {/* License Card */}
        <div style={{
          background: COLORS.bgCard,
          border: `1px solid ${COLORS.borderGold}`,
          borderRadius: 8,
          padding: "32px 28px",
          boxShadow: "0 0 40px rgba(184,150,90,0.04)",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 20 }}>
            <Icon type="lock" size={16} color={COLORS.gold} />
            <span style={{
              fontFamily: FONTS.mono, fontSize: 11, fontWeight: 600,
              color: COLORS.gold, letterSpacing: "0.1em", textTransform: "uppercase",
            }}>
              License Activation
            </span>
          </div>

          <p style={{
            fontFamily: FONTS.body, fontSize: 13, color: COLORS.textMuted,
            lineHeight: 1.7, margin: "0 0 20px",
          }}>
            Enter your license key to access ECR-VP. Keys are issued with your subscription
            at <a href="https://petronus.lemonsqueezy.com" target="_blank" rel="noopener noreferrer"
              style={{ color: COLORS.gold, textDecoration: "none", borderBottom: `1px dotted ${COLORS.borderGold}` }}
            >petronus.lemonsqueezy.com</a>
          </p>

          <a
            href="https://petronus.lemonsqueezy.com/checkout/buy/16bb2267-434c-4ab0-a820-3f8e0b42d1d0"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
              padding: "10px 14px", borderRadius: 4, marginBottom: 20,
              background: "rgba(217,119,6,0.06)", border: `1px solid rgba(217,119,6,0.15)`,
              textDecoration: "none", cursor: "pointer", transition: "all 0.15s",
            }}
          >
            <Icon type="zap" size={12} color={COLORS.amber} />
            <span style={{ fontFamily: FONTS.mono, fontSize: 11, color: COLORS.amber }}>
              4 PLN/week (~0.90 EUR) &middot; BYOK model &middot; Cancel anytime
            </span>
          </a>

          <label style={{
            fontFamily: FONTS.mono, fontSize: 9, color: COLORS.textDim,
            letterSpacing: "0.1em", textTransform: "uppercase", display: "block", marginBottom: 6,
          }}>
            License Key
          </label>
          <input
            type="text"
            value={key}
            onChange={e => setKey(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSubmit()}
            placeholder="XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
            autoFocus
            style={{
              width: "100%", padding: "10px 14px", borderRadius: 4, boxSizing: "border-box",
              background: COLORS.bg, border: `1px solid ${COLORS.border}`,
              color: COLORS.text, fontFamily: FONTS.mono, fontSize: 13, outline: "none",
              letterSpacing: "0.02em",
            }}
          />

          {error && (
            <div style={{
              marginTop: 12, padding: "8px 12px", borderRadius: 4,
              background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.15)",
              fontFamily: FONTS.mono, fontSize: 11, color: COLORS.red,
            }}>
              {error}
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={loading || !key.trim()}
            style={{
              width: "100%", marginTop: 16, padding: "10px 18px",
              borderRadius: 4, border: "none",
              background: loading || !key.trim() ? COLORS.bgPanel : COLORS.amberDark,
              color: loading || !key.trim() ? COLORS.textDim : "#000",
              fontFamily: FONTS.mono, fontSize: 12, fontWeight: 600,
              letterSpacing: "0.06em", cursor: loading || !key.trim() ? "not-allowed" : "pointer",
              transition: "all 0.15s",
              opacity: loading || !key.trim() ? 0.5 : 1,
            }}
          >
            {loading ? "Validating..." : "Activate License"}
          </button>
        </div>

        {/* Footer */}
        <div style={{ textAlign: "center", marginTop: 24 }}>
          <span style={{
            fontFamily: FONTS.mono, fontSize: 9, color: COLORS.textDim, letterSpacing: "0.06em",
          }}>
            Inspired by{" "}
            <a href="https://github.com/petronushowcore-mx/ECR-VP" target="_blank" rel="noopener noreferrer"
              style={{ color: COLORS.goldMuted, textDecoration: "none" }}>
              Navigational Cybernetics 2.5
            </a>
            {" "}|{" "}
            <a href="https://www.linkedin.com/in/max-barzenkov-b03441131" target="_blank" rel="noopener noreferrer"
              style={{ color: "#A78BFA", textDecoration: "none" }}>
              MxBv
            </a>
          </span>
        </div>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════
// APP ROOT
// ═══════════════════════════════════════════════════════════════════════════

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [license, setLicense] = useState(null);

  const handleLogout = () => {
    localStorage.removeItem(LICENSE_STORAGE_KEY);
    setLicense(null);
  };

  // License gate
  if (!license) {
    return (
      <>
        <style>{`
          @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
          *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
          body { background: ${COLORS.bg}; color: ${COLORS.text}; font-family: ${FONTS.body}; -webkit-font-smoothing: antialiased; }
          @keyframes spin { to { transform: rotate(360deg); } }
        `}</style>
        <LicenseGate onUnlock={setLicense} />
      </>
    );
  }

  const renderPage = () => {
    switch (page) {
      case "dashboard": return <DashboardPage onNavigate={setPage} />;
      case "corpus": return <CorpusPage />;
      case "sessions": return <SessionsPage />;
      case "results": return <ResultsPage />;
      case "synthesis": return <SynthesisPage />;
      case "install": return <InstallPage />;
      case "guide": return <GuidePage />;
      default: return <DashboardPage onNavigate={setPage} />;
    }
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
        
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
          background: ${COLORS.bg};
          color: ${COLORS.text};
          font-family: ${FONTS.body};
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }

        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: ${COLORS.bg}; }
        ::-webkit-scrollbar-thumb { background: ${COLORS.border}; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: ${COLORS.borderGold}; }

        ::selection { background: rgba(217,119,6,0.25); color: ${COLORS.text}; }

        input:focus, textarea:focus, select:focus {
          border-color: ${COLORS.borderGold} !important;
          box-shadow: 0 0 0 1px ${COLORS.borderGold};
        }

        textarea { font-family: ${FONTS.body}; }
        select { cursor: pointer; }
        @keyframes exportPulse { 0%,100% { opacity: 0.3; } 50% { opacity: 0.8; } }
        
        /* Noise texture overlay */
        #ecr-vp-root::before {
          content: '';
          position: fixed;
          top: 0; left: 0; right: 0; bottom: 0;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.015'/%3E%3C/svg%3E");
          pointer-events: none;
          z-index: 9999;
          opacity: 0.4;
        }
      `}</style>

      <div id="ecr-vp-root" style={{ display: "flex", minHeight: "100vh" }}>
        <AppBackground />
        <Sidebar active={page} onNavigate={setPage} license={license} onLogout={handleLogout} />
        <main style={{
          marginLeft: 220, flex: 1,
          padding: "32px 40px",
          maxWidth: 1100,
          position: "relative", zIndex: 1,
        }}>
          {renderPage()}
          <Footer />
        </main>
      </div>
    </>
  );
}
