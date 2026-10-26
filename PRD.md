# Product Requirements Document (PRD)
## AI Research & Workflow Automation Agent (SLURBUILDS AI VAULT - Project 03)

### 1. Objective
A bounded, stateful autonomous research agent that accepts a research topic, autonomously plans, searches the web, fetches pages, collects and deduplicates evidence, validates sources, synthesizes a structured Markdown report with real citations, and deterministically verifies every claim against source excerpts. Supports human approval for ambiguous tasks and runs 100% offline in demo mode.

### 2. Core Functional Requirements
- **Planning**: Generates structured Pydantic-validated `ResearchPlan` (objectives, subquestions, seed queries, constraints, sections).
- **Allowlisted Tool Execution**: Read-only tools (`web_search`, `fetch_web_page`, `extract_html_text`, `extract_metadata`, `deduplicate_evidence`). Enforces SSRF guard (blocks private IPs, localhost, link-local metadata), timeouts (8-10s), payload limits (2MB), bounded retries (<=2), and total call budgets (<=15).
- **Content Sanitization**: Strips prompt-injection vectors (scripts, hidden elements, system override instructions) and encloses fetched content in passive data delimiters.
- **Evidence & Citation Grounding**: Every citation `[^src-X]` must map to a registered source and be supported by exact/fuzzy excerpt matches verified deterministically and via LLM judge. Hallucinations are barred; uncertainties are explicitly declared.
- **Human Approval (HITL)**: Workflow pauses into `AWAITING_APPROVAL` with durable checkpoints on ambiguity or user request; resumes upon authorized `/approve`.
- **Live Observability & Streaming**: Live task status via Server-Sent Events (SSE). Full tracing with LangSmith (nodes, latencies, tokens, errors).
- **100% Offline Demo Mode**: Zero external keys needed; uses deterministic mock LLM and saved web fixtures.

### 3. Non-Functional & Security Requirements
- **Security**: SSRF protection, strict URL validation, prompt-injection defense, constant-time API key auth, user ownership checks, admin-only eval endpoints.
- **Reliability**: Postgres checkpointer for crash recovery; network timeouts and individual web failures never crash the task.
- **Simplicity**: Deterministic Python preferred over LLM calls; no Redis/ARQ; SQLite/Postgres interchangeable.

### 4. API Endpoints
- `POST /api/v1/research/tasks` | `GET /api/v1/research/tasks/{id}` | `GET /api/v1/research/tasks/{id}/events` (SSE)
- `GET /api/v1/research/tasks/{id}/sources` | `GET /api/v1/research/tasks/{id}/report`
- `POST /api/v1/research/tasks/{id}/approve` | `POST /api/v1/research/tasks/{id}/cancel`
- `POST /api/v1/evaluations/runs` | `GET /api/v1/evaluations/runs/{id}` | `GET /api/v1/evaluations/compare`
- `GET /health`
