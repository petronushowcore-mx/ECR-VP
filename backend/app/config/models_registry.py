"""
ECR-VP Model Registry — February 2026
======================================
Complete catalog of all supported AI models across all providers.
Each provider has 2-8 models sorted by capability (expensive → cheap).

Usage:
    from app.config.models_registry import PROVIDERS, get_all_models, get_provider_models

Integration:
    1. Backend: import this and use as source of truth for available models
    2. Frontend: expose via GET /api/models endpoint
    3. Session creation: validate model_id against this registry
"""

from typing import Any, Dict, List, Optional


# ─── Model Definition ────────────────────────────────────────────

def _m(
    model_id: str,
    name: str,
    context_k: int,
    input_price: float,
    output_price: float,
    tier: str = "standard",
    notes: str = "",
) -> Dict[str, Any]:
    """Helper to create a model entry."""
    return {
        "model_id": model_id,
        "name": name,
        "context_window": context_k * 1024,
        "context_k": context_k,
        "price_per_1m_input": input_price,
        "price_per_1m_output": output_price,
        "tier": tier,  # "flagship" | "standard" | "fast" | "mini" | "local"
        "notes": notes,
    }


# ─── Provider Definitions ────────────────────────────────────────

PROVIDERS: Dict[str, Dict[str, Any]] = {

    # ═══════════════════════════════════════════════════════════════
    # ANTHROPIC (Claude)
    # API: https://api.anthropic.com/v1/messages
    # Key: ANTHROPIC_API_KEY
    # ═══════════════════════════════════════════════════════════════
    "anthropic": {
        "display_name": "Anthropic",
        "api_base": "https://api.anthropic.com/v1",
        "env_key": "ANTHROPIC_API_KEY",
        "api_format": "anthropic",  # native Anthropic format
        "models": [
            _m("claude-opus-4-6", "Claude Opus 4.6",
               200, 5.00, 25.00, "flagship",
               "Most intelligent. Best for deep analysis"),
            _m("claude-opus-4-5-20250514", "Claude Opus 4.5",
               200, 5.00, 25.00, "flagship",
               "Previous flagship. Deep reasoning"),
            _m("claude-sonnet-4-5-20250929", "Claude Sonnet 4.5",
               200, 3.00, 15.00, "standard",
               "Best balance of quality and cost. Recommended default"),
            _m("claude-haiku-4-5-20251001", "Claude Haiku 4.5",
               200, 0.80, 4.00, "fast",
               "Fast and cheap. Good for quick checks"),
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # OPENAI (GPT)
    # API: https://api.openai.com/v1/chat/completions
    # Key: OPENAI_API_KEY
    # ═══════════════════════════════════════════════════════════════
    "openai": {
        "display_name": "OpenAI",
        "api_base": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
        "api_format": "openai",
        "models": [
            _m("gpt-5.2", "GPT-5.2",
               128, 1.75, 14.00, "flagship",
               "Latest flagship. Best reasoning + coding. Feb 2026"),
            _m("gpt-5.1", "GPT-5.1",
               128, 1.25, 10.00, "standard",
               "Previous flagship. Strong all-round"),
            _m("gpt-5", "GPT-5",
               128, 1.25, 10.00, "standard",
               "First GPT-5 release. Aug 2025"),
            _m("gpt-5-mini", "GPT-5 Mini",
               128, 0.25, 1.00, "fast",
               "Lightweight. High throughput. Very affordable"),
            _m("o3", "o3",
               200, 2.00, 8.00, "standard",
               "Reasoning model. Good for complex analysis"),
            _m("o4-mini", "o4-mini",
               200, 1.10, 4.40, "fast",
               "Fast reasoning. Best on AIME math benchmarks"),
            _m("gpt-4.1", "GPT-4.1",
               128, 2.00, 8.00, "standard",
               "Previous gen. Still excellent quality"),
            _m("gpt-4o", "GPT-4o",
               128, 2.50, 10.00, "standard",
               "Legacy flagship. Multimodal. Mature & stable"),
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # GOOGLE (Gemini)
    # API: https://generativelanguage.googleapis.com/v1beta
    # Key: GOOGLE_API_KEY
    # ═══════════════════════════════════════════════════════════════
    "google": {
        "display_name": "Google",
        "api_base": "https://generativelanguage.googleapis.com/v1beta",
        "env_key": "GOOGLE_API_KEY",
        "api_format": "google",
        "models": [
            _m("gemini-3-pro-preview", "Gemini 3 Pro (Preview)",
               1000, 2.00, 12.00, "flagship",
               "Latest frontier. 1M context. Preview pricing"),
            _m("gemini-2.5-pro", "Gemini 2.5 Pro",
               1000, 1.25, 10.00, "flagship",
               "Best for coding + long context. 1M tokens"),
            _m("gemini-3-flash-preview", "Gemini 3 Flash (Preview)",
               1000, 0.50, 3.00, "standard",
               "Fast frontier model. Great balance"),
            _m("gemini-2.5-flash", "Gemini 2.5 Flash",
               1000, 0.15, 0.60, "fast",
               "Workhorse. Excellent cost-performance"),
            _m("gemini-2.5-flash-lite", "Gemini 2.5 Flash-Lite",
               1000, 0.10, 0.40, "mini",
               "Most affordable. High throughput"),
            _m("gemini-2.0-flash", "Gemini 2.0 Flash",
               1000, 0.10, 0.40, "fast",
               "Legacy fast model. Stable. Deprecates Mar 2026"),
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # XAI (Grok)
    # API: https://api.x.ai/v1 (OpenAI-compatible)
    # Key: XAI_API_KEY
    # ═══════════════════════════════════════════════════════════════
    "xai": {
        "display_name": "xAI (Grok)",
        "api_base": "https://api.x.ai/v1",
        "env_key": "XAI_API_KEY",
        "api_format": "openai",
        "models": [
            _m("grok-4", "Grok 4",
               256, 3.00, 15.00, "flagship",
               "Most capable. Deep reasoning. 256K context"),
            _m("grok-4-fast", "Grok 4 Fast",
               2000, 0.20, 0.50, "fast",
               "2M context! Cheapest flagship-class model"),
            _m("grok-3", "Grok 3",
               131, 3.00, 15.00, "standard",
               "Previous gen. Solid quality"),
            _m("grok-3-mini", "Grok 3 Mini",
               131, 0.30, 0.50, "mini",
               "Lightweight. Very affordable"),
            _m("grok-code-fast-1", "Grok Code Fast",
               2000, 0.20, 0.50, "fast",
               "Optimized for code analysis"),
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # DEEPSEEK
    # API: https://api.deepseek.com (OpenAI-compatible)
    # Key: DEEPSEEK_API_KEY
    # ═══════════════════════════════════════════════════════════════
    "deepseek": {
        "display_name": "DeepSeek",
        "api_base": "https://api.deepseek.com",
        "env_key": "DEEPSEEK_API_KEY",
        "api_format": "openai",
        "models": [
            _m("deepseek-reasoner", "DeepSeek R1 (V3.2 Reasoner)",
               128, 0.55, 2.19, "flagship",
               "Best reasoning. o1-class at 95% less cost"),
            _m("deepseek-chat", "DeepSeek V3.2 (Chat)",
               128, 0.14, 0.28, "standard",
               "GPT-4 class. Incredibly cheap"),
            _m("deepseek-r1-0528", "DeepSeek R1 (May 2025)",
               128, 0.40, 1.75, "standard",
               "Earlier R1 snapshot. Reasoning model"),
            _m("deepseek-v3.1", "DeepSeek V3.1",
               128, 0.15, 0.75, "fast",
               "Previous general model. Good value"),
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # PERPLEXITY (Sonar)
    # API: https://api.perplexity.ai (OpenAI-compatible)
    # Key: PERPLEXITY_API_KEY
    # Note: Web search grounding included. Disable for corpus analysis.
    # ═══════════════════════════════════════════════════════════════
    "perplexity": {
        "display_name": "Perplexity",
        "api_base": "https://api.perplexity.ai",
        "env_key": "PERPLEXITY_API_KEY",
        "api_format": "openai",
        "models": [
            _m("sonar-deep-research", "Sonar Deep Research",
               128, 2.00, 8.00, "flagship",
               "Multi-step research. Reasoning + search"),
            _m("sonar-reasoning-pro", "Sonar Reasoning Pro",
               128, 3.00, 15.00, "flagship",
               "Deep analytical reasoning"),
            _m("sonar-pro", "Sonar Pro",
               200, 3.00, 15.00, "standard",
               "Advanced search + analysis. Larger context"),
            _m("sonar", "Sonar",
               128, 1.00, 1.00, "fast",
               "Fast search. Most affordable Perplexity model"),
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # MISTRAL
    # API: https://api.mistral.ai/v1 (OpenAI-compatible)
    # Key: MISTRAL_API_KEY
    # ═══════════════════════════════════════════════════════════════
    "mistral": {
        "display_name": "Mistral",
        "api_base": "https://api.mistral.ai/v1",
        "env_key": "MISTRAL_API_KEY",
        "api_format": "openai",
        "models": [
            _m("mistral-large-latest", "Mistral Large",
               128, 2.00, 6.00, "flagship",
               "Most capable Mistral model"),
            _m("mistral-medium-latest", "Mistral Medium",
               128, 0.70, 2.80, "standard",
               "Good balance of quality and cost"),
            _m("mistral-small-latest", "Mistral Small",
               128, 0.10, 0.30, "fast",
               "Fast and efficient"),
            _m("codestral-latest", "Codestral",
               256, 0.30, 0.90, "standard",
               "Optimized for code. 256K context"),
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # OLLAMA (Local)
    # API: http://localhost:11434/api (Ollama native)
    # Key: None (local)
    # ═══════════════════════════════════════════════════════════════
    "ollama": {
        "display_name": "Ollama (Local)",
        "api_base": "http://localhost:11434",
        "env_key": None,
        "api_format": "ollama",
        "models": [
            _m("llama3.3:70b", "Llama 3.3 70B",
               128, 0.0, 0.0, "flagship",
               "Largest local. Needs 48GB+ VRAM"),
            _m("qwen3:72b", "Qwen 3 72B",
               128, 0.0, 0.0, "flagship",
               "Strong reasoning. Needs 48GB+ VRAM"),
            _m("llama3.1:8b", "Llama 3.1 8B",
               128, 0.0, 0.0, "fast",
               "Fast local model. 8GB VRAM"),
            _m("qwen2.5:14b", "Qwen 2.5 14B",
               128, 0.0, 0.0, "standard",
               "Good quality. 16GB VRAM"),
            _m("mistral:7b", "Mistral 7B",
               32, 0.0, 0.0, "fast",
               "Compact. 8GB VRAM"),
            _m("gemma2:9b", "Gemma 2 9B",
               8, 0.0, 0.0, "fast",
               "Google's open model. 8GB VRAM"),
            _m("deepseek-r1:8b", "DeepSeek R1 8B (distilled)",
               128, 0.0, 0.0, "fast",
               "Distilled reasoning. 8GB VRAM"),
            _m("deepseek-r1:70b", "DeepSeek R1 70B (distilled)",
               128, 0.0, 0.0, "flagship",
               "Best local reasoning. 48GB+ VRAM"),
        ],
    },
}


# ─── Helper Functions ────────────────────────────────────────────

def get_all_providers() -> List[Dict[str, Any]]:
    """Return list of all providers with their models."""
    result = []
    for key, provider in PROVIDERS.items():
        result.append({
            "provider_id": key,
            "display_name": provider["display_name"],
            "env_key": provider.get("env_key"),
            "model_count": len(provider["models"]),
            "models": provider["models"],
        })
    return result


def get_provider_models(provider_id: str) -> List[Dict[str, Any]]:
    """Return models for a specific provider."""
    provider = PROVIDERS.get(provider_id)
    if not provider:
        return []
    return provider["models"]


def get_all_models() -> List[Dict[str, Any]]:
    """Flat list of all models across all providers."""
    result = []
    for key, provider in PROVIDERS.items():
        for model in provider["models"]:
            result.append({
                **model,
                "provider_id": key,
                "provider_name": provider["display_name"],
            })
    return result


def validate_model(provider_id: str, model_id: str) -> bool:
    """Check if a model_id is valid for a given provider."""
    models = get_provider_models(provider_id)
    return any(m["model_id"] == model_id for m in models)


def get_model_info(provider_id: str, model_id: str) -> Optional[Dict[str, Any]]:
    """Get full model info."""
    models = get_provider_models(provider_id)
    for m in models:
        if m["model_id"] == model_id:
            return {**m, "provider_id": provider_id}
    return None


def estimate_cost(provider_id: str, model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD for a given token count."""
    info = get_model_info(provider_id, model_id)
    if not info:
        return 0.0
    cost = (
        (input_tokens / 1_000_000) * info["price_per_1m_input"]
        + (output_tokens / 1_000_000) * info["price_per_1m_output"]
    )
    return round(cost, 4)


# ─── API Endpoint Data ───────────────────────────────────────────

def get_models_for_api() -> Dict[str, Any]:
    """
    Return data structured for the frontend API.
    Use in: GET /api/models
    """
    return {
        "providers": [
            {
                "id": key,
                "name": provider["display_name"],
                "requires_key": provider.get("env_key") is not None,
                "env_key": provider.get("env_key"),
                "models": [
                    {
                        "id": m["model_id"],
                        "name": m["name"],
                        "context": m["context_k"],
                        "tier": m["tier"],
                        "price_input": m["price_per_1m_input"],
                        "price_output": m["price_per_1m_output"],
                        "notes": m["notes"],
                    }
                    for m in provider["models"]
                ],
            }
            for key, provider in PROVIDERS.items()
        ],
        "total_providers": len(PROVIDERS),
        "total_models": sum(len(p["models"]) for p in PROVIDERS.values()),
    }


# ─── Quick Reference (for console) ──────────────────────────────

if __name__ == "__main__":
    print("ECR-VP Model Registry — February 2026")
    print("=" * 60)
    total = 0
    for key, provider in PROVIDERS.items():
        n = len(provider["models"])
        total += n
        print(f"\n{provider['display_name']} ({n} models):")
        for m in provider["models"]:
            price = f"${m['price_per_1m_input']}/{m['price_per_1m_output']}"
            if m["price_per_1m_input"] == 0:
                price = "FREE (local)"
            ctx = f"{m['context_k']}K"
            print(f"  [{m['tier']:8s}] {m['model_id']:35s} {ctx:>6s}  {price:>12s}")
    print(f"\nTotal: {len(PROVIDERS)} providers, {total} models")
