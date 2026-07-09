# Assignment 6 — UI Prototype + Architecture Document

The face of the product plus the design plan and data contracts.

## Contents
| Path | Deliverable |
|------|-------------|
| `ui/` | React (Vite) app: command bar, live activity log, profile settings |
| `architecture.md` | 1-page architecture doc + diagram (UI → FastAPI → AgentExecutor → [LLM, Browser, Memory] → External APIs) |
| `contracts.py` | Pydantic data contracts: `UserProfile`, `Task`, `AgentAction` |
| `tests/` | 5 pytest tests for the intent parser (one per action type), LLM mocked |

## 1. React UI
```bash
cd ui
npm install
npm run dev          # http://localhost:5173
```
It talks to the Assignment 5 backend at `http://127.0.0.1:8000` (override with
`VITE_API_BASE`). Start that server first (`uvicorn main:app --reload`).

- **Command bar** → `POST /command`, gets a `task_id`.
- **Activity log** → opens `WS /ws/{task_id}` and renders each agent step live.
- **Profile page** → `GET`/`POST /user/profile` (the agent's memory).

Build check: `npm run build` (verified — 35 modules, clean production build).

## 2. Architecture document
See [`architecture.md`](architecture.md) — one page with a Mermaid diagram (and
an ASCII fallback), the request lifecycle, component table, data contracts, and
failure modes.

## 3. Pydantic data contracts
`contracts.py` defines `UserProfile`, `Task`, and `AgentAction` — the shared data
shapes for Weeks 7–10. Run it directly to see sample JSON:
```bash
python contracts.py
```

## 4. Intent-parser tests
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r tests/requirements.txt
pytest tests/          # 10 passed (navigate, fill_form, email, summarize, click + contract checks)
```
The Gemini client is **mocked** (a fake client returning canned JSON), so tests
are fast, deterministic, and spend zero tokens — and each parsed result is
validated against the `AgentAction` contract.
