"""
ECR-VP Models Router
====================
Exposes model registry to frontend.

Add to main.py:
    from app.routers.models_router import router as models_router
    app.include_router(models_router, prefix="/api")
"""

import os
from fastapi import APIRouter
from app.config.models_registry import (
    PROVIDERS, get_models_for_api, get_provider_models, estimate_cost
)

router = APIRouter(tags=["models"])


@router.get("/models")
async def list_models():
    """
    Return all available providers and models.
    Frontend uses this to populate the New Session dialog.
    """
    data = get_models_for_api()

    # Check which providers have API keys configured
    for provider in data["providers"]:
        env_key = provider.get("env_key")
        if env_key is None:
            provider["configured"] = True  # Local (Ollama)
        else:
            provider["configured"] = bool(os.getenv(env_key, ""))

    return data


@router.get("/models/{provider_id}")
async def list_provider_models(provider_id: str):
    """Return models for a specific provider."""
    models = get_provider_models(provider_id)
    if not models:
        return {"error": f"Unknown provider: {provider_id}"}

    provider = PROVIDERS.get(provider_id, {})
    env_key = provider.get("env_key")

    return {
        "provider_id": provider_id,
        "display_name": provider.get("display_name", provider_id),
        "configured": env_key is None or bool(os.getenv(env_key, "")),
        "models": models,
    }


@router.get("/models/estimate-cost")
async def estimate_run_cost(
    provider_id: str,
    model_id: str,
    input_tokens: int = 150000,
    output_tokens: int = 10000,
):
    """Estimate cost for a verification run."""
    cost = estimate_cost(provider_id, model_id, input_tokens, output_tokens)
    return {
        "provider_id": provider_id,
        "model_id": model_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": cost,
    }
