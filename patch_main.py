import os

path = os.path.join('backend', 'app', 'main.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = '''@app.get("/api/providers")
async def list_providers():
    """List available LLM providers."""
    return {"providers": ProviderRegistry.list_available()}'''

new = '''@app.get("/api/providers")
async def list_providers():
    """List available LLM providers."""
    return {"providers": ProviderRegistry.list_available()}

@app.get("/api/providers/status")
async def provider_status():
    """Check which providers have API keys and which Ollama models are installed."""
    import httpx
    key_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
        "xai": "XAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "perplexity": "PERPLEXITY_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "microsoft": "AZURE_API_KEY",
    }
    result = {}
    for pid, env_var in key_map.items():
        val = os.environ.get(env_var, "")
        result[pid] = {"available": bool(val and len(val) > 5), "models": []}
    # Check Ollama
    ollama_models = []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            if resp.status_code == 200:
                for m in resp.json().get("models", []):
                    name = m["name"]
                    ollama_models.append(name)
        result["ollama"] = {"available": True, "models": ollama_models}
    except Exception:
        result["ollama"] = {"available": False, "models": []}
    return result'''

if old in content:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print("OK: provider_status endpoint added")
else:
    print("ERROR: Could not find target string")
