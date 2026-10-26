# 🤖 AI Research & Workflow Automation Agent

> A production-grade, bounded stateful research agent built with **LangGraph**, **FastAPI**, and **Next.js**. Autonomously plans, searches, extracts, verifies citations, and generates structured research reports — with full observability via LangSmith.

---

## ✨ Features

- **Autonomous Research Pipeline** — LangGraph multi-node agent: plan → search → fetch → extract → verify → report
- **Citation Verification** — Two-stage: deterministic regex checks + LLM entailment scoring
- **SSRF Protection** — DNS pre-resolution blocks RFC 1918, link-local, and cloud metadata endpoints
- **Prompt Injection Defense** — Content sanitizer neutralizes injection patterns in retrieved content
- **Human-in-the-Loop Approval** — Pause graph at configurable checkpoint, resume after review
- **LangSmith Tracing** — Full graph tracing with secret redaction, latency, token, and cost metadata
- **Evaluation Suite** — 40-case benchmark, LLM judge with explicit rubrics, experiment comparison
- **Demo Mode** — Full end-to-end run with zero paid API keys (mock LLM + fixture data)
- **Dark-theme UI** — Next.js 14 + Tailwind dashboard with live SSE execution graph, report viewer, approval modal

---

## 🗂️ Project Structure

```
AI RAWA/
├── backend/
│   ├── agents/
│   │   ├── graph.py              # LangGraph StateGraph definition
│   │   ├── state.py              # ResearchAgentState TypedDict
│   │   └── nodes/                # Planner, QueryGen, ToolExecutor, Evidence, Verifier, Report, Approval
│   ├── api/
│   │   ├── routes_tasks.py       # REST + SSE task endpoints
│   │   ├── routes_evals.py       # Admin-only eval endpoints
│   │   └── routes_health.py      # /health probe
│   ├── models/
│   │   ├── schemas.py            # Pydantic v2 request/response models
│   │   └── orm.py                # SQLAlchemy async ORM (User, Task, Source, EvalRun)
│   ├── services/
│   │   ├── task_manager.py       # Background execution, SSE broadcast, approval gate
│   │   ├── auth.py               # Bearer / X-API-Key authentication
│   │   ├── llm_adapter.py        # Provider-neutral LLM adapter + MockLLM
│   │   ├── citation_verifier.py  # Two-stage citation audit
│   │   └── content_sanitizer.py  # Prompt injection defense
│   ├── tools/
│   │   ├── ssrf_guard.py         # DNS-based SSRF blocking
│   │   ├── web_search.py         # Tavily / DuckDuckGo / Mock search
│   │   ├── page_fetcher.py       # Safe HTTP fetch with redirect validation
│   │   ├── content_extractor.py  # BeautifulSoup + SHA-256 dedup chunking
│   │   ├── registry.py           # Tool allowlist + budget + concurrency limiter
│   │   └── fixtures.py           # Demo mode offline fixture data
│   ├── db/
│   │   ├── session.py            # Async DB session + init
│   │   └── checkpointer.py       # LangGraph checkpointer factory (Postgres / Memory)
│   ├── observability/
│   │   └── langsmith_tracer.py   # Trace spans, secret redaction, offline fallback
│   ├── config.py                 # Pydantic Settings with all env vars
│   └── main.py                   # FastAPI app entry point
├── frontend/
│   └── src/
│       ├── app/                  # Next.js App Router pages
│       ├── components/           # TaskForm, ExecutionGraph, ReportViewer, ApprovalModal, EvalComparison…
│       └── lib/                  # api.ts (REST+SSE client), types.ts (mirrors backend schemas)
├── evaluation/
│   ├── datasets/
│   │   ├── benchmark_cases.json  # 40 benchmark cases across 8 categories
│   │   └── calibration_set.json  # 5 human-reviewed calibration cases
│   ├── evaluators/               # research_quality, agent_behavior, performance, llm_judge
│   ├── run_offline_evals.py      # CLI runner — saves JSON/Markdown or uploads to LangSmith
│   └── compare_experiments.py    # Markdown delta comparison table
├── tests/
│   ├── conftest.py
│   ├── test_api_endpoints.py
│   └── integration/              # Real-service tests (skipped by default)
├── docs/
│   └── ARCHITECTURE.md
├── PRD.md
├── compose.yaml
├── .env.example
└── pyproject.toml
```

---

## 🚀 Quick Start

### Demo Mode (no API keys needed)

```bash
# 1. Clone
git clone https://github.com/chirag13-glitch/AI-Research-Workflow-Automation-Agent.git
cd AI-Research-Workflow-Automation-Agent

# 2. Backend
cp .env.example .env          # DEMO_MODE=true by default
pip install -e ".[dev]"
python -m uvicorn backend.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev                   # http://localhost:3000
```

Visit **http://localhost:3000** — no API keys required.

---

### Real Mode (live LLM + search)

Set these in your `.env`:

| Variable | Description |
|---|---|
| `DEMO_MODE` | Set to `false` |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `OPENAI_MODEL` | e.g. `gpt-4o-mini` |
| `TAVILY_API_KEY` | Your Tavily search key |
| `DATABASE_URL` | PostgreSQL URL (optional, SQLite by default) |
| `LANGSMITH_API_KEY` | LangSmith key (optional, for tracing) |
| `LANGSMITH_PROJECT` | Project name in LangSmith |

```bash
DEMO_MODE=false python -m uvicorn backend.main:app --reload --port 8000
```

---

## 🧪 Tests

```bash
# Unit tests
python -m pytest tests/ -v

# Offline evaluation suite (40 cases)
python evaluation/run_offline_evals.py --mode demo

# Compare two experiment runs
python evaluation/compare_experiments.py results/run_A.json results/run_B.json
```

---

## 🔌 API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health probe + mode indicator |
| `POST` | `/api/v1/research/tasks` | Create research task |
| `GET` | `/api/v1/research/tasks` | List all tasks |
| `GET` | `/api/v1/research/tasks/{id}` | Get task detail |
| `GET` | `/api/v1/research/tasks/{id}/events` | SSE live stream |
| `GET` | `/api/v1/research/tasks/{id}/report` | Get final report + citations |
| `GET` | `/api/v1/research/tasks/{id}/report/download` | Download Markdown |
| `GET` | `/api/v1/research/tasks/{id}/sources` | List sources |
| `POST` | `/api/v1/research/tasks/{id}/approve` | Approve / reject |
| `POST` | `/api/v1/research/tasks/{id}/cancel` | Cancel task |
| `GET` | `/api/v1/evals/runs` | List eval runs (admin) |
| `POST` | `/api/v1/evals/runs` | Trigger eval run (admin) |

Interactive docs: **http://localhost:8000/docs**

---

## 🏗️ Architecture

```
User → FastAPI → Auth → TaskManager
                            │
                    LangGraph StateGraph
                            │
          ┌─────────────────┼─────────────────┐
       Planner         ToolExecutor       Verifier
          │                │                  │
    QueryGenerator    WebSearch/Fetch    CitationAudit
                           │
                    ContentExtractor
                    (SSRF + Sanitizer)
                            │
                    EvidenceCollector
                            │
                    ReportGenerator → Final Markdown
```

---

## 🛡️ Security

- **SSRF Guard**: DNS pre-resolution blocks all private IP ranges and cloud metadata endpoints
- **Prompt Injection Defense**: Strips/neutralizes injection patterns before LLM context insertion  
- **Auth**: SHA-256 hashed API keys; demo default key auto-applied in DEMO_MODE
- **Admin-only endpoints**: Evaluation routes gated behind `is_admin` flag
- **No secrets in frontend**: All keys live in backend `.env`

---

## 📦 Tech Stack

| Layer | Tech |
|---|---|
| Agent Framework | LangGraph 0.2 |
| Backend | FastAPI, SQLAlchemy (async), Pydantic v2 |
| LLM | OpenAI-compatible (provider-neutral adapter) |
| Search | Tavily / DuckDuckGo / Mock |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Checkpointing | LangGraph MemorySaver / AsyncPostgresSaver |
| Observability | LangSmith |
| Frontend | Next.js 14, Tailwind CSS, TypeScript |
| Containerization | Docker + Compose |

---

## 📄 License

MIT © 2026 SLURBUILDS
