"""
ECR-VP xAI (Grok) Provider
===========================
Grok API is OpenAI-compatible.
Base URL: https://api.x.ai/v1
API Key env var: XAI_API_KEY

Models: grok-4, grok-4-fast, grok-3, grok-3-mini
"""

import os
import httpx
from typing import Any, Dict, List, Optional


class XAIProvider:
    """xAI / Grok API provider (OpenAI-compatible)."""

    PROVIDER_NAME = "xai"
    BASE_URL = "https://api.x.ai/v1"

    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def complete(
        self,
        messages: List[Dict[str, Any]],
        model: str = "grok-4-fast",
        max_tokens: int = 16384,
        temperature: float = 0.3,
        **kwargs,
    ) -> Dict[str, Any]:
        """Send completion request to Grok API."""
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

        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        # Extract response text
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
        }

    async def complete_with_corpus(
        self,
        system_prompt: str,
        corpus_text: str,
        reference_prompt: str,
        model: str = "grok-4-fast",
        max_tokens: int = 16384,
    ) -> Dict[str, Any]:
        """
        ECR-VP protocol: send corpus as a single large prompt.
        Grok supports up to 2M token context (grok-4-fast) or 256K (grok-4).
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
        )
