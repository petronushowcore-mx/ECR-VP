import os

path = os.path.join('frontend', 'src', 'App.jsx')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add api function to api.js
api_path = os.path.join('frontend', 'src', 'api.js')
with open(api_path, 'r', encoding='utf-8') as f:
    api_content = f.read()

if 'providerStatus' not in api_content:
    api_content += '\n\nexport async function providerStatus() {\n  return request("/providers/status");\n}\n'
    with open(api_path, 'w', encoding='utf-8') as f:
        f.write(api_content)
    print("OK: Added providerStatus to api.js")
else:
    print("SKIP: providerStatus already in api.js")

# 2. Add providerStatus state to SessionsPage
old1 = '  const [sessionType, setSessionType] = useState("strict_verifier");\n  const [sourceSessionId, setSourceSessionId] = useState("");'
new1 = '''  const [sessionType, setSessionType] = useState("strict_verifier");
  const [sourceSessionId, setSourceSessionId] = useState("");
  const [providerStatus, setProviderStatus] = useState(null);

  useEffect(() => {
    if (showCreate) {
      api.providerStatus().then(setProviderStatus).catch(() => setProviderStatus(null));
    }
  }, [showCreate]);

  const isModelAvailable = (providerId, model) => {
    if (!providerStatus) return true; // Loading, allow all
    const ps = providerStatus[providerId];
    if (!ps) return false;
    if (providerId === "ollama") {
      if (!ps.available) return false;
      // Check if model is installed (match by base name)
      const baseModel = model.split(":")[0];
      return ps.models.some(m => m.startsWith(baseModel));
    }
    return ps.available;
  };'''

if old1 in content:
    content = content.replace(old1, new1)
    print("OK: Added providerStatus state")
else:
    print("ERROR: Could not find state insertion point")

# 3. Update the model checkbox to disable unavailable
old2 = '''                    <div
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
                        {selected && <span style={{ fontSize: 10, color: "#000", fontWeight: 700 }}'''

new2 = '''                    <div
                      key={model}
                      onClick={() => isModelAvailable(prov.id, model) && toggleProvider(prov.id, model)}
                      style={{
                        display: "flex", alignItems: "center", gap: 8,
                        padding: "5px 8px", marginBottom: 3, borderRadius: 3,
                        background: selected ? "rgba(217,119,6,0.08)" : "transparent",
                        border: `1px solid ${selected ? COLORS.amberDark : "transparent"}`,
                        cursor: isModelAvailable(prov.id, model) ? "pointer" : "not-allowed",
                        transition: "all 0.15s",
                        opacity: isModelAvailable(prov.id, model) ? 1 : 0.3,
                      }}
                    >
                      <div style={{
                        width: 14, height: 14, borderRadius: 3,
                        border: `1.5px solid ${selected ? COLORS.amber : COLORS.textDim}`,
                        background: selected ? COLORS.amber : "transparent",
                        display: "flex", alignItems: "center", justifyContent: "center",
                      }}>
                        {selected && <span style={{ fontSize: 10, color: "#000", fontWeight: 700 }}'''

if old2 in content:
    content = content.replace(old2, new2)
    print("OK: Updated model checkbox with availability check")
else:
    print("ERROR: Could not find checkbox block")

# 4. Add "no API key" / "not installed" hint after model name
old3 = '''                      <span style={{
                        fontFamily: FONTS.mono, fontSize: 10,
                        color: selected ? COLORS.text : COLORS.textMuted,
                      }}>
                        {model}
                      </span>'''

new3 = '''                      <span style={{
                        fontFamily: FONTS.mono, fontSize: 10,
                        color: selected ? COLORS.text : isModelAvailable(prov.id, model) ? COLORS.textMuted : COLORS.textDim,
                      }}>
                        {model}
                        {!isModelAvailable(prov.id, model) && (
                          <span style={{ fontSize: 9, color: COLORS.red, marginLeft: 6 }}>
                            {prov.id === "ollama" ? "not installed" : "no API key"}
                          </span>
                        )}
                      </span>'''

if old3 in content:
    content = content.replace(old3, new3)
    print("OK: Added availability hints")
else:
    print("ERROR: Could not find model name span")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("DONE: Frontend patched")
