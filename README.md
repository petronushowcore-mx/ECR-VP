# ECR-VP вЂ” Epistemic Coherence Review & Verification Protocol

**Execution Shell v0.2.0**

A local application for running the ECR-VP protocol: non-causal verification of structural coherence, boundary clarity, and engineering realizability of complex architectural document corpora.

ECR-VP treats independent LLM interpreters as isolated, non-causal observers. Each receives the same sealed corpus and produces a structured report. Interpreters never see each other's outputs, never receive feedback, and are never tuned toward any expected result. Final synthesis is always performed by a human.

---

## Quick Start

### Prerequisites
- **Python 3.10+** вЂ” [python.org](https://python.org)
- **Node.js 18+** вЂ” [nodejs.org](https://nodejs.org)

### Installation

`
git clone https://github.com/petronushowcore-mx/ECR-VP.git
cd ECR-VP
`

**Backend:**
`
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
`

**Configure API keys:**
`
cp .env.example backend/.env
# Edit backend/.env and add your API keys
`

**Start (Windows):**
`
start.bat
`

**Or manually:**
`
cd backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload --port 8000
# In another terminal:
cd frontend
npm install
npm run dev
`

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

- **Identity fixation** вЂ” corpus is SHA-256 sealed before analysis
- **Interpreter isolation** вЂ” no cross-contamination between models
- **Strict mode separation** вЂ” Rc, Ri, DET, Ra, Failure, Novelty, Verdict, Maturity
- **No numerical scoring** вЂ” qualitative axes only
- **Human synthesis is mandatory** вЂ” coherence map is human-generated
- **Immutable artifacts** вЂ” interpreter outputs cannot be edited

---

## License

Protocol specification: **CC BY-NC-ND 4.0**

Inspired by [Navigational Cybernetics 2.5](https://github.com/petronushowcore-mx/ECR-VP) | [MxBv](https://www.linkedin.com/in/max-barzenkov-b03441131)
