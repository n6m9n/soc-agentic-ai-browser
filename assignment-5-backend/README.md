# Assignment 5 — Backend API Server (FastAPI)

The server the React UI talks to: receives commands, runs the agent in the
background, streams live status over WebSocket, and stores user profiles in SQLite.

## Setup & run
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Then open **http://127.0.0.1:8000/docs** — the auto-generated Swagger UI where you
can exercise every endpoint.

## Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/command` | Accepts `{ "command": "..." }`, returns `{ task_id }` immediately; runs the agent in the background |
| GET | `/status/{task_id}` | Task progress: status + ordered steps + result |
| GET | `/user/profile` | Read the stored user memory |
| POST | `/user/profile` | Create/update user memory (name, email, phone, address, resume_text) |
| WS | `/ws/{task_id}` | Live step-by-step updates as the agent works |

## Storage (SQLite + SQLModel)
`UserProfile` is persisted in `app.db` (name, email, phone, address, resume_text).
`models.py` defines the SQLModel table + the Pydantic request/response contracts.

## The agent as a background task
`POST /command` schedules `agent_runner.run_command(...)` on the event loop and
returns a `task_id` right away. Each step is published to the **TaskHub**, which
records it (for `/status`) and fans it out to every `/ws/{task_id}` subscriber.

Two modes:
- **default (simulated)** — streams realistic steps with small delays. Runs with
  no LLM key, no browser, zero tokens — so the whole loop is demonstrable and
  testable immediately.
- **real agent** — set `USE_REAL_AGENT=true` to lazily import and stream the
  **Week 4 LangChain agent**. Requires the Week 4 deps, `GOOGLE_API_KEY`, and
  `playwright install chromium`:
  ```bash
  pip install langchain langchain-google-genai langgraph playwright
  playwright install chromium
  USE_REAL_AGENT=true uvicorn main:app
  ```

## Tests
```bash
pytest            # 4 tests: profile round-trip, command+status, 404, WebSocket stream
```
Uses the simulated agent, so tests are fast and need no key.

## Try it from the terminal
```bash
curl -X POST localhost:8000/command -H 'content-type: application/json' \
     -d '{"command":"go to google.com and search for AI news"}'
# -> {"task_id":"...","status":"pending"}
curl localhost:8000/status/<task_id>
```
