# ECR-VP Execution Shell — Architecture

## 1. System Purpose

This system is an **orchestration shell** for the ECR-VP v1.0 protocol.
It does NOT interpret, evaluate, or synthesize. It executes the protocol,
preserves invariants, and produces auditable artifacts.

### Three Inviolable Invariants

1. **Corpus Identity Fixation** — Canon Lock before any execution
2. **Interpreter Isolation** — clean sessions, identical input, no cross-contamination
3. **Observation ≠ Control** — outputs are immutable; synthesis is a separate human layer

---

## 2. Module Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                       │
│  ┌──────────┐ ┌──────────────┐ ┌─────────────────────┐  │
│  │ Corpus    │ │ Session      │ │ Synthesis           │  │
│  │ Manager   │ │ Dashboard    │ │ Workspace           │  │
│  └──────────┘ └──────────────┘ └─────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
┌────────────────────────┴────────────────────────────────┐
│                 Backend (FastAPI)                         │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Corpus      │  │ Session      │  │ Artifact       │  │
│  │ Service     │  │ Orchestrator │  │ Store          │  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬────────┘  │
│         │                │                   │           │
│  ┌──────┴──────────────────────────────────────────┐    │
│  │            Interpreter Gateway                    │    │
│  │  ┌─────────┐ ┌────────┐ ┌──────┐ ┌───────────┐  │    │
│  │  │Anthropic│ │OpenAI  │ │Google│ │Ollama/Local│  │    │
│  │  └─────────┘ └────────┘ └──────┘ └───────────┘  │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │            Storage Layer (SQLite + FS)             │    │
│  │  corpus_passports | sessions | interpreter_runs   │    │
│  │  artifacts/ (immutable files)                     │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

---

## 3. Core Modules

### 3.1 Corpus Service

**Responsibility:** Manage corpus lifecycle — upload, hash, passport generation, version lock.

- Accept file uploads (PDF, DOCX, MD, code, etc.)
- Compute SHA-256 for each file
- Generate Corpus Passport (JSON + human-readable)
- Enforce immutability: once a session starts, corpus is frozen
- Track canon version explicitly

**Passport schema:**
```json
{
  "passport_id": "uuid",
  "created_at": "ISO-8601",
  "purpose": "string",
  "architectural_status": "open | closed",
  "canon_version": "string",
  "constraints": ["string"],
  "files": [
    {
      "filename": "string",
      "size_bytes": int,
      "sha256": "string",
      "canonical_order": int
    }
  ]
}
```

### 3.2 Session Orchestrator

**Responsibility:** Create and manage verification sessions. Enforce protocol flow.

- Create session from Corpus Passport
- Launch interpreter runs in isolation
- Manage sequential loading for large corpora
- Send fixed completion phrase after final segment
- Track session state: `preparing → loading → executing → completed`
- Enforce: same passport, same prompt, same order for all interpreters

**Critical constraint:** The orchestrator MUST NOT adapt prompts per model.

### 3.3 Interpreter Gateway

**Responsibility:** Abstract interface over LLM providers. Treat all as opaque black boxes.

Supported providers (Phase 1):
- **Anthropic** (Claude) — via `anthropic` SDK
- **OpenAI** (GPT-4o, o1, o3) — via `openai` SDK
- **Google** (Gemini) — via `google-genai` SDK
- **Ollama** (local models) — via REST API
- **Mistral** — via `mistral` SDK
- **DeepSeek** — via OpenAI-compatible API

Each provider implements:
```python
class InterpreterProvider(Protocol):
    async def create_session(self) -> str
    async def send_message(self, session_id: str, content: str, files: list[File]) -> str
    async def send_files(self, session_id: str, files: list[File]) -> None
    async def get_response(self, session_id: str) -> InterpreterResponse
```

**File handling:** Different providers handle files differently (some accept PDF natively,
some need text extraction). The gateway handles conversion transparently.

### 3.4 Artifact Store

**Responsibility:** Immutable storage of all protocol outputs.

- Every interpreter response → immutable artifact with timestamp + metadata
- Artifacts linked to session + interpreter run
- No modification, no deletion during session
- Commentary/annotations stored as separate layer with references
- Historical comparison across sessions

**Storage structure:**
```
data/
  artifacts/
    {session_id}/
      passport.json
      runs/
        {run_id}/
          metadata.json      # provider, model, timestamps
          prompt.txt          # exact prompt sent
          corpus_manifest.json # what was sent, in what order
          response_raw.txt    # immutable interpreter output
          response_modes.json # parsed mode boundaries (if detectable)
```

### 3.5 Synthesis Workspace (Frontend)

**Responsibility:** UI for human synthesis — NOT automated.

- Side-by-side view of all interpreter reports
- Mode-aligned comparison (Rc vs Rc, Ri vs Ri, etc.)
- Highlighting tools for marking overlap / divergence / non-understanding
- Coherence map builder (three layers per protocol)
- Author's Response editor (clearly marked as human layer)
- Export: coherence map + author's response as immutable document

---

## 4. Protocol Flow

```
[1] Upload corpus files
        ↓
[2] Generate Corpus Passport (Canon Lock)
        ↓
[3] Create Verification Session
        ↓
[4] For each interpreter (parallel or sequential):
    [4a] Open clean session via provider API
    [4b] Send Corpus Passport
    [4c] Send corpus files (sequential if needed)
    [4d] Send completion phrase
    [4e] Capture full response as immutable artifact
        ↓
[5] All runs complete → Session moves to synthesis
        ↓
[6] Human builds coherence map in Synthesis Workspace
        ↓
[7] Human writes Author's Response
        ↓
[8] Export final verification report
```

---

## 5. Mode Detection (Structural, Not Evaluative)

The system MAY detect mode boundaries in interpreter outputs for display purposes:
- Look for mode headings (Rc, Ri, Ra, etc.)
- Flag if modes are missing or out of order
- Flag if mode mixing is detectable

This is **structural detection only** — the system does not judge content within modes.

---

## 6. Storage Migration Path

**Phase 1 (Local):**
- SQLite for metadata (passports, sessions, runs)
- Filesystem for artifacts (immutable files)

**Phase 2 (Cloud):**
- PostgreSQL for metadata
- S3-compatible storage for artifacts
- Same API, different storage backend

---

## 7. Non-Goals (per ECR-VP §12)

The system MUST NOT include:
- Numerical scoring or ratings
- Consensus or aggregation mechanisms
- Feedback loops to interpreters
- Learning from protocol outputs
- Optimization of interpreter behavior
- Automation of correctness or truth evaluation
- Any feature that collapses observation into control

---

## 8. Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Backend | Python 3.12+ / FastAPI | Best LLM SDK ecosystem, async |
| Database | SQLite (→ PostgreSQL) | Simple, local-first, easy migration |
| File storage | Local FS (→ S3) | Immutable artifacts |
| Frontend | React + TypeScript | Rich UI for synthesis workspace |
| UI framework | Tailwind + shadcn/ui | Clean, professional |
| Task queue | asyncio (→ Celery/ARQ) | Parallel interpreter runs |
| Hashing | hashlib (SHA-256) | Standard, deterministic |
