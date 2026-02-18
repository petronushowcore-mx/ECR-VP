"""
OpenAI provider for ECR-VP Interpreter Gateway.
Also serves as base for OpenAI-compatible APIs (DeepSeek, Mistral, etc.)
"""

from __future__ import annotations

import base64
import os
from typing import Optional

from ..core.gateway import (
    FilePayload,
    InterpreterProvider,
    MessagePayload,
    ProviderRegistry,
)
from ..models.schema import InterpreterConfig, InterpreterResponse


class OpenAIProvider(InterpreterProvider):
    """
    Provider for OpenAI models (GPT-4o, o1, o3, etc.)
    Also usable for any OpenAI-compatible API via base_url.
    """

    MODEL_CONTEXT = {
        "gpt-4o": 128_000,
        "gpt-4o-mini": 128_000,
        "o1": 200_000,
        "o3": 200_000,
        "o3-mini": 200_000,
    }

    def __init__(self, config: InterpreterConfig):
        super().__init__(config)
        self._client = None
        self._sessions: dict[str, list[dict]] = {}

    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise RuntimeError("openai package not installed. Run: pip install openai")
            
            api_key = os.environ.get(
                self.config.api_key_env or "OPENAI_API_KEY"
            )
            if not api_key:
                raise RuntimeError(
                    f"API key not found. Set {self.config.api_key_env or 'OPENAI_API_KEY'}"
                )
            
            kwargs = {"api_key": api_key}
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    async def create_session(self) -> str:
        import uuid
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = []
        return session_id

    async def send_message(self, session_id: str, message: MessagePayload) -> None:
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
        content = self._build_content(message)
        self._sessions[session_id].append({"role": "user", "content": content})

    async def send_and_receive(
        self, session_id: str, message: MessagePayload
    ) -> InterpreterResponse:
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
        
        client = self._get_client()
        content = self._build_content(message)
        self._sessions[session_id].append({"role": "user", "content": content})
        
        messages = self._prepare_messages(session_id)
        
        response = await client.chat.completions.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=messages,
        )
        
        choice = response.choices[0]
        raw_text = choice.message.content or ""
        
        return InterpreterResponse(
            raw_text=raw_text,
            token_count_input=response.usage.prompt_tokens if response.usage else None,
            token_count_output=response.usage.completion_tokens if response.usage else None,
            model_used=response.model,
            provider=self.config.provider,
        )

    async def close_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def supports_file_upload(self) -> bool:
        return True  # GPT-4o supports images; PDFs need text extraction

    def max_context_tokens(self) -> int:
        return self.MODEL_CONTEXT.get(self.config.model, 128_000)

    def _build_content(self, message: MessagePayload) -> list[dict] | str:
        """Build OpenAI content blocks."""
        if not message.files:
            return message.text
        
        content = []
        for f in message.files:
            if f.mime_type.startswith("image/"):
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{f.mime_type};base64,{base64.b64encode(f.content).decode()}"
                    },
                })
            else:
                # OpenAI doesn't natively support PDF — extract text
                try:
                    text_content = f.content.decode("utf-8")
                except UnicodeDecodeError:
                    text_content = f"[Binary file: {f.filename}, {len(f.content)} bytes]"
                content.append({
                    "type": "text",
                    "text": f"--- File: {f.filename} ---\n{text_content}\n--- End: {f.filename} ---",
                })
        
        content.append({"type": "text", "text": message.text})
        return content

    def _prepare_messages(self, session_id: str) -> list[dict]:
        raw = self._sessions[session_id]
        messages = []
        for i, msg in enumerate(raw):
            messages.append(msg)
            if (
                i < len(raw) - 1
                and msg["role"] == "user"
                and raw[i + 1]["role"] == "user"
            ):
                messages.append({
                    "role": "assistant",
                    "content": "Acknowledged. Awaiting next corpus segment.",
                })
        return messages


# Register OpenAI
ProviderRegistry.register("openai", OpenAIProvider)


class DeepSeekProvider(OpenAIProvider):
    """DeepSeek via OpenAI-compatible API."""
    
    def __init__(self, config: InterpreterConfig):
        if not config.base_url:
            config.base_url = "https://api.deepseek.com"
        if not config.api_key_env:
            config.api_key_env = "DEEPSEEK_API_KEY"
        super().__init__(config)

    def max_context_tokens(self) -> int:
        return 64_000  # DeepSeek-V3 default


class MistralProvider(OpenAIProvider):
    """Mistral via OpenAI-compatible API."""
    
    def __init__(self, config: InterpreterConfig):
        if not config.base_url:
            config.base_url = "https://api.mistral.ai/v1"
        if not config.api_key_env:
            config.api_key_env = "MISTRAL_API_KEY"
        super().__init__(config)

    def max_context_tokens(self) -> int:
        return 128_000


# Register compatible providers
ProviderRegistry.register("deepseek", DeepSeekProvider)
ProviderRegistry.register("mistral", MistralProvider)
