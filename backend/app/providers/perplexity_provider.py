"""
ECR-VP Perplexity Provider
===========================
Perplexity Sonar API (OpenAI-compatible).
Base URL: https://api.perplexity.ai
API Key env var: PERPLEXITY_API_KEY

Models: sonar, sonar-pro, sonar-deep-research, sonar-reasoning-pro
Note: Sonar models include web search grounding by default.
"""

import os
import httpx
from typing import Any, Dict, List, Optional


class PerplexityProvider:
    """Perplexity Sonar API provider (OpenAI-compatible)."""

    PROVIDER_NAME = "perplexity"
    BASE_URL = "https://api.perplexity.ai"

    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def complete(
        self,
        messages: List[Dict[str, Any]],
        model: str = "sonar-pro",
        max_tokens: int = 16384,
        temperature: float = 0.3,
        **kwargs,
    ) -> Dict[str, Any]:
        """Send completion request to Perplexity API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Perplexity-specific: disable web search for corpus analysis
        # (we don't want web results mixed into verification)
        if kwargs.get("disable_search", True):
            payload["web_search_options"] = {"search_context_size": "none"}

        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        raw_text = ""
        if data.get("choices"):
            raw_text = data["choices"][0].get("message", {}).get("content", "")

        usage = data.get("usage", {})

        return {
            "raw_text": raw_text,
            "model": data.get("model", model),
            "usage": {
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            },
            "provider": self.PROVIDER_NAME,
            "citations": data.get("citations", []),
        }

    async def complete_with_corpus(
        self,
        system_prompt: str,
        corpus_text: str,
        reference_prompt: str,
        model: str = "sonar-pro",
        max_tokens: int = 16384,
    ) -> Dict[str, Any]:
        """
        ECR-VP protocol: send corpus as a single large prompt.
        Sonar Pro supports 200K context.
        Disable web search to keep analysis focused on corpus only.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": corpus_text},
            {"role": "user", "content": reference_prompt},
        ]

        return await self.complete(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            disable_search=True,  # Important: no web mixing
        )
