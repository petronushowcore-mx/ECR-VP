"""
Anthropic (Claude) provider for ECR-VP Interpreter Gateway.
"""

from __future__ import annotations

import base64
import os
from datetime import datetime, timezone
from typing import Optional

from ..core.gateway import (
    FilePayload,
    InterpreterProvider,
    MessagePayload,
    ProviderRegistry,
)
from ..models.schema import InterpreterConfig, InterpreterResponse


class AnthropicProvider(InterpreterProvider):

    MODEL_CONTEXT = {
        "claude-opus-4-5-20250514": 200_000,
        "claude-sonnet-4-5-20250929": 200_000,
        "claude-haiku-4-5-20251001": 200_000,
    }

    def __init__(self, config: InterpreterConfig):
        super().__init__(config)
        self._client = None
        self._sessions: dict[str, list[dict]] = {}

    def _get_client(self):
        if self._client is None:
            import anthropic
            api_key = getattr(self.config, 'api_key', None) or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError("API key not found. Set ANTHROPIC_API_KEY")
            self._client = anthropic.AsyncAnthropic(api_key=api_key)
        return self._client

    async def create_session(self) -> str:
        import uuid
        sid = str(uuid.uuid4())
        self._sessions[sid] = []
        return sid

    async def send_message(self, session_id: str, message: MessagePayload) -> None:
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
        content = self._build_content(message)
        self._sessions[session_id].append({"role": "user", "content": content})

    async def send_and_receive(self, session_id: str, message: MessagePayload) -> InterpreterResponse:
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
        client = self._get_client()
        content = self._build_content(message)
        self._sessions[session_id].append({"role": "user", "content": content})
        messages = self._prepare_messages(session_id)
        response = await client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=messages,
        )
        raw_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                raw_text += block.text
        return InterpreterResponse(
            raw_text=raw_text,
            token_count_input=response.usage.input_tokens,
            token_count_output=response.usage.output_tokens,
            model_used=response.model,
            provider="anthropic",
        )

    async def close_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def supports_file_upload(self) -> bool:
        return True

    def max_context_tokens(self) -> int:
        return self.MODEL_CONTEXT.get(self.config.model, 200_000)

    def _build_content(self, message: MessagePayload) -> list[dict]:
        content = []
        if message.files:
            for f in message.files:
                if f.mime_type == "application/pdf":
                    txt = self._extract_pdf_text(f.content, f.filename)
                    content.append({"type": "text", "text": f"--- Document: {f.filename} ---\n{txt}\n--- End: {f.filename} ---"})
                elif f.mime_type.startswith("image/"):
                    content.append({"type": "image", "source": {"type": "base64", "media_type": f.mime_type, "data": base64.b64encode(f.content).decode()}})
                else:
                    try:
                        txt = f.content.decode("utf-8")
                        content.append({"type": "text", "text": f"--- File: {f.filename} ---\n{txt}\n--- End: {f.filename} ---"})
                    except UnicodeDecodeError:
                        content.append({"type": "text", "text": f"[Binary file: {f.filename}, {len(f.content)} bytes]"})
        if message.text:
            content.append({"type": "text", "text": message.text})
        return content

    @staticmethod
    def _extract_pdf_text(pdf_bytes: bytes, filename: str) -> str:
        try:
            import importlib
            fitz = importlib.import_module("fitz")
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            pages = [page.get_text() for page in doc]
            doc.close()
            text = "\n\n".join(pages)
            if text.strip():
                return text
        except Exception:
            pass
        return f"[PDF extraction failed for {filename}]"

    def _prepare_messages(self, session_id: str) -> list[dict]:
        raw = self._sessions[session_id]
        if not raw:
            return []
        messages = []
        for i, msg in enumerate(raw):
            messages.append(msg)
            if i < len(raw) - 1 and msg["role"] == "user" and raw[i + 1]["role"] == "user":
                messages.append({"role": "assistant", "content": "Acknowledged. Awaiting next corpus segment."})
        return messages


ProviderRegistry.register("anthropic", AnthropicProvider)
