"""
ECR-VP Execution Shell — Core Data Models

These models define the structural primitives of the protocol execution.
They are NOT interpretive — they describe what exists, not what it means.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ─── Enums ────────────────────────────────────────────────────────────────

class ArchitecturalStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class SessionState(str, Enum):
    PREPARING = "preparing"       # Corpus uploaded, passport not yet generated
    LOCKED = "locked"             # Canon Lock complete, passport immutable
    EXECUTING = "executing"       # Interpreter runs in progress
    AWAITING_SYNTHESIS = "awaiting_synthesis"  # All runs complete, human synthesis pending
    COMPLETED = "completed"       # Coherence map + Author's Response finalized


class RunState(str, Enum):
    PENDING = "pending"           # Queued, not yet started
    LOADING = "loading"           # Corpus being transmitted
    AWAITING_RESPONSE = "awaiting_response"  # Completion phrase sent, waiting
    COMPLETED = "completed"       # Response captured
    FAILED = "failed"             # Error during execution


class ProtocolMode(str, Enum):
    """ECR-VP protocol modes in prescribed order."""
    RC = "Rc"                           # Architecture as class
    RI = "Ri"                           # Invariants and prohibitions
    DECLARATIVE_TYPOLOGY = "Declarative Epistemic Typology"
    RA = "Ra"                           # Engineering realizability
    FAILURE = "Failure"                 # Failure modes
    NOVELTY = "Novelty and Positioning" # Structural novelty
    VERDICT = "Verdict"                 # Engineering verdict
    MATURITY = "Project Maturity Summary"  # Operational readiness

    @classmethod
    def prescribed_order(cls) -> list[ProtocolMode]:
        return [
            cls.RC, cls.RI, cls.DECLARATIVE_TYPOLOGY, cls.RA,
            cls.FAILURE, cls.NOVELTY, cls.VERDICT, cls.MATURITY
        ]


# ─── Corpus & Passport ───────────────────────────────────────────────────

class CorpusFile(BaseModel):
    """A single file in the corpus with its identity hash."""
    filename: str
    size_bytes: int
    sha256: str
    canonical_order: int
    file_path: str  # Relative path in storage


class CorpusPassport(BaseModel):
    """
    Immutable identity of a corpus for a verification session.
    Once created, MUST NOT be modified for the duration of the session.
    Ref: ECR-VP §2.5, Engineering Spec §4.
    """
    passport_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Corpus metadata
    purpose: str = Field(description="Purpose of this verification session")
    architectural_status: ArchitecturalStatus
    canon_version: str = Field(description="Version of the canonical document")
    snapshot_date: datetime = Field(description="Date of corpus snapshot")
    constraints: list[str] = Field(
        default_factory=list,
        description="Explicit constraints on scope of evaluation"
    )
    
    # File manifest
    files: list[CorpusFile]
    
    # Integrity
    is_locked: bool = False

    def lock(self) -> None:
        """Once locked, passport is immutable for the session."""
        self.is_locked = True



# ─── Interpreter & Provider ──────────────────────────────────────────────

class InterpreterConfig(BaseModel):
    """Configuration for a single interpreter instance."""
    provider: str          # e.g., "anthropic", "openai", "google", "ollama"
    model: str             # e.g., "claude-sonnet-4-5-20250929", "gpt-4o"
    display_name: str      # Human label, e.g., "Claude Sonnet 4.5"
    api_key_env: Optional[str] = None  # Environment variable name for API key
    base_url: Optional[str] = None     # For Ollama or custom endpoints
    max_tokens: int = 16384
    temperature: float = 0.0  # Deterministic by default


class InterpreterResponse(BaseModel):
    """Raw response from an interpreter — immutable once captured."""
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_text: str
    token_count_input: Optional[int] = None
    token_count_output: Optional[int] = None
    model_used: str
    provider: str
    
    # Structural analysis (non-evaluative)
    detected_modes: list[DetectedMode] = Field(default_factory=list)
    modes_in_order: Optional[bool] = None
    missing_modes: list[str] = Field(default_factory=list)


class DetectedMode(BaseModel):
    """A mode boundary detected in interpreter output."""
    mode: str
    start_position: int   # Character offset in raw_text
    end_position: int
    heading_text: str     # The actual heading found


# ─── Session & Run ───────────────────────────────────────────────────────

class InterpreterRun(BaseModel):
    """A single interpreter execution within a session."""
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    interpreter: InterpreterConfig
    state: RunState = RunState.PENDING
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Output
    response: Optional[InterpreterResponse] = None
    error: Optional[str] = None
    
    # Audit trail
    prompt_hash: Optional[str] = None       # SHA-256 of exact prompt sent
    corpus_loading_log: list[str] = Field(default_factory=list)


class VerificationSession(BaseModel):
    """
    A complete ECR-VP verification session.
    Binds a Corpus Passport to multiple interpreter runs.
    """
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    state: SessionState = SessionState.PREPARING
    
    # Fixed inputs
    passport: CorpusPassport
    reference_prompt: str  # The fixed ECR-VP prompt — must not be modified per-model
    
    # Interpreter runs
    runs: list[InterpreterRun] = Field(default_factory=list)
    
    # Synthesis (human layer)
    coherence_map: Optional[CoherenceMap] = None
    author_response: Optional[AuthorResponse] = None


# ─── Synthesis Layer (Human-Generated) ───────────────────────────────────

class CoherenceLayer(BaseModel):
    """One layer of the coherence map."""
    description: str
    entries: list[str]  # Free-text entries


class CoherenceMap(BaseModel):
    """
    The coherence map — compiled by a human, NOT automated.
    Three layers per ECR-VP §2.10.
    """
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str  # Name of human synthesizer
    
    # Layer 1: Overlapping conclusions
    overlap: CoherenceLayer = Field(
        description="Elements identified consistently by most interpreters"
    )
    # Layer 2: Unique observations per interpreter
    unique_observations: dict[str, CoherenceLayer] = Field(
        default_factory=dict,
        description="Keyed by run_id"
    )
    # Layer 3: Divergence and non-understanding
    divergence: CoherenceLayer = Field(
        description="Where corpus insufficiently fixes invariants/boundaries"
    )


class AuthorResponse(BaseModel):
    """
    Mandatory human appendix per ECR-VP §2.12.
    NOT a defense — a fixation of intent vs. transmitted structure.
    """
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author: str
    text: str  # Continuous prose, not structured
    
    # Tracking what was acknowledged
    correctly_understood: list[str] = Field(default_factory=list)
    misunderstood: list[str] = Field(default_factory=list)
    requires_clarification: list[str] = Field(default_factory=list)
