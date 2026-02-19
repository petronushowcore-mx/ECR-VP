"""
DeepSeek provider for ECR-VP Interpreter Gateway.
Uses OpenAI-compatible API.
"""

from __future__ import annotations

import json
from typing import Optional

from ..core.gateway import (
    FilePayload,
    InterpreterProvider,
    MessagePayload,
    ProviderRegistry,
)
from ..models.schema import InterpreterConfig, InterpreterResponse


class DeepSeekProvider(InterpreterProvider):
    """
    Provider for DeepSeek models via OpenAI-compatible API.
    """

    BASE_URL = "https://api.deepseek.com/v1"

    def __init__(self, config: InterpreterConfig):
        if not config.api_key_env:
            config.api_key_env = "DEEPSEEK_API_KEY"
        super().__init__(config)
        self._sessions: dict[str, list[dict]] = {}

    async def create_session(self) -> str:
        import uuid
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = []
        return session_id

    async def send_message(self, session_id: str, message: MessagePayload) -> None:
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")

        content_parts = []

        if message.files:
            for f in message.files:
                # DeepSeek doesn't support file uploads natively
                # Extract text from files
                text = self._extract_file_text(f)
                if text:
                    content_parts.append(text)

        content_parts.append(message.text)
        full_content = "\n\n".join(content_parts)

        self._sessions[session_id].append({
            "role": "user",
            "content": full_content,
        })

    async def send_and_receive(
        self, session_id: str, message: MessagePayload
    ) -> InterpreterResponse:
        import httpx
        import os

        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")

        await self.send_message(session_id, message)
        messages = self._prepare_messages(session_id)

        api_key = os.environ.get(self.config.api_key_env, "")
        if not api_key:
            raise ValueError(f"API key not found: {self.config.api_key_env}")

        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]
        raw_text = choice["message"]["content"]
        usage = data.get("usage", {})

        return InterpreterResponse(
            raw_text=raw_text,
            token_count_input=usage.get("prompt_tokens"),
            token_count_output=usage.get("completion_tokens"),
            model_used=data.get("model", self.config.model),
            provider="deepseek",
        )

    async def close_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def supports_file_upload(self) -> bool:
        return False

    def max_context_tokens(self) -> int:
        if "r1" in self.config.model.lower():
            return 128_000
        return 64_000

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

    @staticmethod
    def _extract_file_text(f: FilePayload) -> str | None:
        """Extract text from file payload."""
        if f.filename.lower().endswith(".pdf"):
            try:
                import pdfplumber
                import io
                with pdfplumber.open(io.BytesIO(f.content)) as pdf:
                    pages = []
                    for i, page in enumerate(pdf.pages):
                        text = page.extract_text()
                        if text:
                            pages.append(f"[Page {i+1}]\n{text}")
                    if pages:
                        return f"--- File: {f.filename} ---\n" + "\n\n".join(pages) + f"\n--- End: {f.filename} ---"
            except Exception:
                pass
        if f.filename.lower().endswith(".docx"):
            try:
                from docx import Document
                import io
                doc = Document(io.BytesIO(f.content))
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                if paragraphs:
                    return f"--- File: {f.filename} ---\n" + "\n".join(paragraphs) + f"\n--- End: {f.filename} ---"
            except Exception:
                pass
        try:
            return f"--- File: {f.filename} ---\n{f.content.decode('utf-8')}\n--- End: {f.filename} ---"
        except UnicodeDecodeError:
            return f"[Binary file: {f.filename}, could not extract text]"


ProviderRegistry.register("deepseek", DeepSeekProvider)
