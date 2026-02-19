"""
Ollama provider for ECR-VP Interpreter Gateway.
Supports locally running models via Ollama REST API.
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


class OllamaProvider(InterpreterProvider):
    """
    Provider for local models via Ollama.
    Uses the /api/chat endpoint.
    """

    def __init__(self, config: InterpreterConfig):
        if not config.base_url:
            config.base_url = "http://localhost:11434"
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
        
        msg = {"role": "user", "content": message.text}
        # Ollama supports images via base64 in 'images' field
        if message.files:
            import base64
            images = []
            text_parts = []
            for f in message.files:
                if f.mime_type.startswith("image/"):
                    images.append(base64.b64encode(f.content).decode())
                else:
                    extracted = None
                    # Try PDF text extraction first
                    if f.filename.lower().endswith(".pdf"):
                        extracted = self._extract_pdf_text(f.content, f.filename)
                    # Try docx extraction
                    elif f.filename.lower().endswith(".docx"):
                        extracted = self._extract_docx_text(f.content, f.filename)
                    if extracted:
                        text_parts.append(extracted)
                    else:
                        try:
                            text_parts.append(
                                f"--- File: {f.filename} ---\n"
                                f"{f.content.decode('utf-8')}\n"
                                f"--- End: {f.filename} ---"
                            )
                        except UnicodeDecodeError:
                            text_parts.append(f"[Binary file: {f.filename}, could not extract text]")
            
            if text_parts:
                msg["content"] = "\n\n".join(text_parts) + "\n\n" + message.text
            if images:
                msg["images"] = images
        
        self._sessions[session_id].append(msg)

    async def send_and_receive(
        self, session_id: str, message: MessagePayload
    ) -> InterpreterResponse:
        import httpx
        
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
        
        # Add final message
        await self.send_message(session_id, message)
        
        # Prepare messages with interleaved acknowledgments
        messages = self._prepare_messages(session_id)
        
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                f"{self.config.base_url}/api/chat",
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
        
        raw_text = data.get("message", {}).get("content", "")
        
        return InterpreterResponse(
            raw_text=raw_text,
            token_count_input=data.get("prompt_eval_count"),
            token_count_output=data.get("eval_count"),
            model_used=self.config.model,
            provider="ollama",
        )

    async def close_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def supports_file_upload(self) -> bool:
        return False  # Limited to images; PDFs need text extraction

    def max_context_tokens(self) -> int:
        return 32_000  # Conservative default; varies by model

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
    def _extract_pdf_text(content: bytes, filename: str) -> str | None:
        """Extract text from PDF bytes using pdfplumber or PyPDF2."""
        try:
            import pdfplumber
            import io
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages = []
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        pages.append(f"[Page {i+1}]\n{text}")
                if pages:
                    return f"--- File: {filename} ---\n" + "\n\n".join(pages) + f"\n--- End: {filename} ---"
        except ImportError:
            pass
        except Exception:
            pass
        try:
            from PyPDF2 import PdfReader
            import io
            reader = PdfReader(io.BytesIO(content))
            pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    pages.append(f"[Page {i+1}]\n{text}")
            if pages:
                return f"--- File: {filename} ---\n" + "\n\n".join(pages) + f"\n--- End: {filename} ---"
        except ImportError:
            pass
        except Exception:
            pass
        return None

    @staticmethod
    def _extract_docx_text(content: bytes, filename: str) -> str | None:
        """Extract text from DOCX bytes."""
        try:
            from docx import Document
            import io
            doc = Document(io.BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            if paragraphs:
                return f"--- File: {filename} ---\n" + "\n".join(paragraphs) + f"\n--- End: {filename} ---"
        except ImportError:
            pass
        except Exception:
            pass
        return None


ProviderRegistry.register("ollama", OllamaProvider)
