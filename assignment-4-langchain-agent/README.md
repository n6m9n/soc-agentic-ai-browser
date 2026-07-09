# Assignment 4 — LangChain Agent with Playwright Tools

Integrates the browser automation (Assignment 2) and intent parsing
(Assignment 3) into a real agent that drives Chromium via LangChain tools, on
**Google Gemini** (free tier).

## Setup
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
export GOOGLE_API_KEY=AIza...     # free key: https://aistudio.google.com/apikey
python agent.py
```

## The 3 tools (+ bonus)
| Tool | Signature | Action |
|------|-----------|--------|
| `navigate_to` | `(url)` | open URL, return page title |
| `click_element` | `(selector)` | click first match of CSS selector |
| `type_text` | `(selector, text)` | type into the matched input |
| `get_profile` *(bonus)* | `(field)` | query `user_profile.json` for name/email/resume_path/… |

All four are real `@tool` functions sharing one lazily-launched Playwright page;
each handles timeouts gracefully and returns a string the agent can reason over.
The agent is built with `ChatGoogleGenerativeAI` (Gemini), which supports
tool/function calling so `create_agent` can plan and invoke them.

## Conversation memory
Built on LangChain 1.x `create_agent` (a LangGraph agent). Passing an
`InMemorySaver` checkpointer and reusing the same `thread_id` across `invoke`
calls makes the agent remember prior turns automatically — that's why the demo's
4th turn, *"Which site did you visit first?"*, is answered correctly from
earlier turns.

## The full loop
`agent.py`'s `main()` runs: **user command → agent reasoning → tool execution →
result → next step**, across four turns that exercise navigation, the profile
store, a second navigation, and memory recall.

## Bonus — file-based profile store
`profile_store.py` (`ProfileStore`) reads `user_profile.json` and is exposed to
the agent through `get_profile`. Test it standalone:
```bash
python profile_store.py
```
