ECR-VP — Verification Protocol Shell
Independent structural verification of document corpora through parallel LLM interpretation.

What is ECR-VP?
ECR-VP is a protocol execution engine that submits your document corpus to multiple AI interpreters simultaneously — each working in complete isolation, under identical conditions, following a fixed analytical protocol.
No interpreter sees the output of another. No prompt is adapted per model. Every response is captured as an immutable, hash-verified artifact.
The result: a structural map of your work — not through one opinion, but through independent convergence or divergence across interpreters.

Who is it for?
Researchers and theorists preparing grant applications, whitepapers, or academic submissions who need to know — before reviewers do — where their corpus is structurally weak, where claims exceed evidence, and where an outsider loses the thread.
System architects building novel frameworks who need independent verification that their architecture is readable, realizable, and internally consistent — without relying on a single reviewer's bias.
Patent authors who need to understand how their claims read to multiple independent analytical systems before filing.
Anyone producing a serious document corpus who wants honest, protocol-bound structural feedback — not flattery, not stylistic preferences, not optimization advice.

What does the protocol actually do?
Each interpreter independently executes eight analytical modes in fixed order:
ModePurposeRcClassify the architecture — what class of system it is, what problems it addresses, how it differs from known approachesRiExtract invariants and prohibitions explicitly fixed by the corpus — what must exist, what is forbiddenDeclarative Epistemic TypologyClassify the corpus by epistemic layers — which are present, partially present, or absentRaAssess engineering realizability — what can be built today, what needs domain-specific specification, what is declared but non-operationalFailureIdentify failure modes — where the architecture could break, where metric gaming could emerge, where definitions driftNovelty & PositioningIdentify what is genuinely non-trivial at the architectural level and whyVerdictConcise engineering verdict on coherence, readability, realizability, and gapsProject MaturityOperational readiness snapshot — what exists, what can be piloted, what is blocking deployment
Every interpreter receives the same corpus, the same prompt, in the same order. The protocol is a fixed artifact — any modification is a protocol violation.

What makes this different from "just asking ChatGPT"?
Isolation. Each interpreter works in a clean session with zero context from other runs. There is no cross-contamination.
Immutability. Every response is captured exactly as received — timestamped, hashed, stored. No post-hoc editing, no cherry-picking.
Integrity. The entire session — corpus, passport, responses, Merkle tree — is exportable as a cryptographically verifiable bundle.
Protocol discipline. Interpreters don't freestyle. They follow prescribed modes in fixed order. You see not just what they think, but whether they can follow structure — and where they deviate.
Convergence analysis. When three or five interpreters independently identify the same structural gap, that's not an opinion. That's a signal.

How it works

Upload your corpus — PDFs, markdown, text files. Any document set.
Create a Corpus Passport — a locked, hash-verified manifest of your files in canonical order.
Select interpreters — local models via Ollama, or cloud APIs (Anthropic, OpenAI, and others via your own API keys).
Execute — the protocol runs all interpreters in parallel under identical conditions.
Review results — each interpreter's output displayed as an immutable artifact with mode detection.
Export — download the full verification bundle as a ZIP with Merkle tree proof.


Pricing
$1/week — bring your own API keys (BYOK).
You pay for the protocol shell. You pay your LLM providers directly for inference. ECR-VP never touches your API keys server-side — they stay in your local environment.
For local models via Ollama — no API costs at all. Run the full protocol on your own hardware.

What you get

Protocol execution engine with full session management
Corpus Passport with SHA-256 integrity verification and Canon Lock
Parallel or sequential interpreter execution
Immutable artifact storage with timestamps and hash chains
Mode detection — automatic identification of protocol compliance per interpreter
Merkle tree verification for every session
Export as a self-contained, cryptographically verifiable ZIP bundle
Works with local models (Ollama) and cloud APIs


What you don't get

ECR-VP does not interpret results for you.
ECR-VP does not rank interpreters or pick a "winner."
ECR-VP does not optimize prompts per model.
ECR-VP does not provide recommendations or strategy advice.

The protocol is a verification instrument — not an optimization tool. It shows you the structural landscape. You decide what to do with it.

Built on
Navigational Cybernetics 2.5 — an architectural theory of long-horizon adaptive systems.
The protocol itself is a structural artifact of that theory: verification through independent observation, not consensus; immutability over convenience; admissibility over optimization.

Copyright © 2026 Maksim Barziankou (MxBv). Licensed under CC BY-NC-ND 4.0.

---

## Quick Start

### Prerequisites
- **Python 3.10+** - [python.org](https://python.org)
- **Node.js 18+** - [nodejs.org](https://nodejs.org)

### Installation

```
git clone https://github.com/petronushowcore-mx/ECR-VP.git
cd ECR-VP
```

**Backend:**
```
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

**Configure API keys:**
```
cp .env.example backend/.env
# Edit backend/.env and add your API keys
```

**Start (Windows):**
```
start.bat
```

**Or manually:**
```
cd backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload --port 8000
# In another terminal:
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**

---

## Supported Providers

| Provider | Models | Pricing (150K/10K tokens) |
|----------|--------|--------------------------|
| **Anthropic** | Claude Opus 4.5, Sonnet 4.5, Haiku 4.5 | 0.60 - 0.90 |
| **OpenAI** | GPT-5.2, GPT-5, o3, o4-mini | 0.04 - 0.40 |
| **Google** | Gemini 3 Pro, 2.5 Pro/Flash | 0.02 - 0.32 |
| **xAI** | Grok 4, Grok 4 Fast (2M context) | 0.04 - 0.60 |
| **DeepSeek** | R1 V3.2, V3.2 Chat | 0.02 - 0.10 |
| **Perplexity** | Sonar Deep Research, Sonar Pro | 0.16 - 0.45 |
| **Mistral** | Large, Medium, Small, Codestral | 0.02 - 0.36 |
| **Ollama** | LLaMA 3.3, Qwen 3, DeepSeek R1 | **Free (local)** |

---

## Protocol Invariants

- **Identity fixation** - corpus is SHA-256 sealed before analysis
- **Interpreter isolation** - no cross-contamination between models
- **Strict mode separation** - Rc, Ri, DET, Ra, Failure, Novelty, Verdict, Maturity
- **No numerical scoring** - qualitative axes only
- **Human synthesis is mandatory** - coherence map is human-generated
- **Immutable artifacts** - interpreter outputs cannot be edited

---

## License

Protocol specification: **CC BY-NC-ND 4.0**

Inspired by [Navigational Cybernetics 2.5](https://github.com/petronushowcore-mx/ECR-VP) | [MxBv](https://www.linkedin.com/in/max-barzenkov-b03441131)
