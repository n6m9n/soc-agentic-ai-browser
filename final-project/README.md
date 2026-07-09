# Agentic AI Browser Assistant (final project)

A personal AI assistant that fills forms, drafts/sends email, summarises pages,
manages your Google Calendar, chains those together, and **remembers you** via a
Corrective-RAG memory. Built on the Weeks 1–6 assignments as building blocks.

> Status: **all 6 modules + cRAG built** across Phases 0–7. 33 backend tests pass;
> the React UI builds clean. Google modules (email/calendar) need OAuth set up below.

## Modules
| # | Module | What it does | Key files |
|---|--------|--------------|-----------|
| 6 | Memory (cRAG) | retrieve→grade→correct→learn; asks once, remembers forever | `memory/` |
| 1 | Form Filling | detect fields (incl. iframes) → cRAG values → preview → submit → learn | `modules/form_filling.py`, `browser/` |
| 3 | Summarisation | page/URL/PDF → TL;DR·key points·actions·tags·sentiment; JD analyser; compare | `modules/summarizer.py` |
| 2 | Email | LLM draft → confirm-before-send; groups; inbox digest | `modules/email_assistant.py`, `integrations/gmail_client.py` |
| 4 | Calendar | free-slot finder, recurring events, conflicts, proactive prompts | `modules/calendar_intel.py`, `integrations/calendar_client.py` |
| 5 | Orchestration | decompose compound commands → run modules in sequence with HITL | `agents/planner.py`, `agents/orchestrator.py` |

## Run the UI
```bash
cd ui && npm install && npm run dev      # http://localhost:5173 (needs the API on :8000)
```
Command bar + live activity log (WebSocket), form **preview** and email **confirm**
panels for human-in-the-loop, profile/resume manager, task history, Connect-Google.

## Setup
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your free Gemini key: https://aistudio.google.com/apikey
uvicorn app.main:app --reload
# open http://127.0.0.1:8000/docs
```

## Google OAuth setup (Gmail + Calendar)
1. [Google Cloud Console](https://console.cloud.google.com/) → new project.
2. Enable **Gmail API** and **Google Calendar API**.
3. **APIs & Services → OAuth consent screen** → External → add yourself as a **Test user**.
4. **Credentials → Create credentials → OAuth client ID → Web application** →
   Authorized redirect URI: `http://127.0.0.1:8000/auth/google/callback`.
5. Download the client secret JSON as **`final-project/credentials.json`** (git-ignored).
6. Start the server, open `http://127.0.0.1:8000/auth/google/login`, approve.
   Check `GET /auth/google/status`. App stays in "testing" mode — no verification needed for personal use.

## Architecture
```
React UI ──▶ FastAPI ──▶ Orchestrator (LangGraph) ──▶ feature modules
   ▲            │              │
   └─WebSocket──┘              ├─ cRAG memory (ChromaDB + Gemini embeddings)
   live steps + HITL           ├─ browser tools (Playwright)
                               └─ Google APIs (Gmail, Calendar)
```

## Corrective-RAG memory (Module 6 — the brain)
`memory/crag.py` runs: **retrieve → grade → (correct) generate | (incorrect)
corrective → write-back**. When the knowledge base can't answer, cRAG returns a
`needs_user` signal so the assistant asks you once; `learn()` writes the answer
back to ChromaDB so it's remembered forever.

- `memory/store.py` — ChromaDB + Gemini embeddings (`models/gemini-embedding-001`)
- `memory/crag.py` — the cRAG loop (grade+generate fused into one LLM call)
- `memory/ingest.py` — profile fields + resume PDF → vector memory
- Endpoints: `POST /memory/query`, `POST /memory/learn`, `POST /memory/ingest-profile`,
  `POST /memory/resume`, `GET /memory/history`

## Endpoints (so far)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/command` | run a command (returns `task_id`); streams over WS |
| GET | `/status/{task_id}` | task progress |
| POST | `/command/{task_id}/resume` | answer a human-in-the-loop pause |
| WS | `/ws/{task_id}` | live step updates |
| GET/POST | `/user/profile` | structured profile |
| POST | `/memory/*` | cRAG memory (query/learn/ingest/resume) |

## Tests
```bash
pytest            # Phase 0 infra + Phase 1 cRAG (mocked LLM/embeddings, no key needed)
```
