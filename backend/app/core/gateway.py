"""
ECR-VP Interpreter Gateway

Abstract interface for all LLM providers.
Each interpreter is treated as an opaque black box.
The gateway ensures identical input and captures immutable output.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..models.schema import InterpreterConfig, InterpreterResponse


@dataclass
class FilePayload:
    """A file to be sent to an interpreter."""
    filename: str
    content: bytes
    mime_type: str
    canonical_order: int


@dataclass 
class MessagePayload:
    """A message to be sent to an interpreter, with optional file attachments."""
    text: str
    files: list[FilePayload] | None = None


class InterpreterProvider(ABC):
    """
    Abstract base for all LLM provider integrations.
    
    Contract:
    - create_session() opens a clean, isolated session
    - send_message() transmits content WITHOUT receiving feedback
    - get_full_response() retrieves the complete interpreter output
    - Each session is independent — no state leakage between sessions
    """
    
    def __init__(self, config: InterpreterConfig):
        self.config = config
    
    @abstractmethod
    async def create_session(self) -> str:
        """
        Create a new clean session.
        Returns a session identifier (provider-specific).
        Must guarantee: no context from previous sessions.
        """
        ...
    
    @abstractmethod
    async def send_message(
        self, 
        session_id: str, 
        message: MessagePayload
    ) -> None:
        """
        Send a message (with optional files) to the interpreter.
        This is a one-way transmission — no response is expected yet.
        Used for sequential corpus loading.
        """
        ...
    
    @abstractmethod
    async def send_and_receive(
        self,
        session_id: str,
        message: MessagePayload
    ) -> InterpreterResponse:
        """
        Send the final message (completion phrase) and receive full response.
        The response is captured as an immutable artifact.
        """
        ...
    
    @abstractmethod
    async def close_session(self, session_id: str) -> None:
        """Close the session. No further interaction allowed."""
        ...
    
    @abstractmethod
    def supports_file_upload(self) -> bool:
        """Whether this provider accepts file attachments natively."""
        ...
    
    @abstractmethod
    def max_context_tokens(self) -> int:
        """Maximum context window for this provider/model combination."""
        ...

    # ── Utility Methods ──────────────────────────────────────────────
    
    @staticmethod
    def hash_prompt(prompt: str) -> str:
        """SHA-256 of the exact prompt text, for audit trail."""
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


class ProviderRegistry:
    """
    Registry of available interpreter providers.
    Used by the Session Orchestrator to instantiate providers by name.
    """
    
    _providers: dict[str, type[InterpreterProvider]] = {}
    
    @classmethod
    def register(cls, name: str, provider_class: type[InterpreterProvider]) -> None:
        cls._providers[name] = provider_class
    
    @classmethod
    def get(cls, name: str) -> type[InterpreterProvider]:
        if name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unknown provider '{name}'. Available: {available}"
            )
        return cls._providers[name]
    
    @classmethod
    def list_available(cls) -> list[str]:
        return list(cls._providers.keys())
    
    @classmethod
    def create(cls, config: InterpreterConfig) -> InterpreterProvider:
        """Create a provider instance from config."""
        provider_class = cls.get(config.provider)
        return provider_class(config)
