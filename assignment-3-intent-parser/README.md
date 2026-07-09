# Assignment 3 — Intent Parser Prototype

The agent's core intelligence: `parse_intent(user_command) -> dict` calls the
**Google Gemini API** (free tier) and returns a structured browser-action plan.

## Why Gemini
Gemini has a genuinely free API tier (no credit card) — grab a key at
**https://aistudio.google.com/apikey**. Most other providers require a paid
balance, so this keeps the whole project at zero cost.

## Setup
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GOOGLE_API_KEY=AIza...        # your free key
```

## Run
```bash
python intent_parser.py "go to google.com and search for AI news"
python test_commands.py     # runs all 10 sample commands
```

## Schema
```jsonc
{
  "action": "fill_form" | "navigate" | "email" | "summarize" | "click",
  "target_url": "https://...",       // "" when not applicable
  "data": { ... },                    // action-specific payload
  "steps": ["...", "..."],            // ordered plan
  "needs_clarification": false,       // bonus
  "clarifying_question": ""           // set when needs_clarification is true
}
```

## Design notes
- **Gemini JSON mode** — `response_mime_type="application/json"` forces the model
  to return a valid JSON document, so parsing is reliable.
- **Few-shot prompt** — the system prompt includes worked examples for
  `navigate`, `fill_form`, and `email` (≥3 action types), plus an ambiguous
  example to teach the clarify behaviour.
- **Bonus (clarifying questions)** — ambiguity is modelled *inside* the schema:
  for vague commands like "apply to this job" or "email this summary to my boss"
  the model sets `needs_clarification: true` and fills `clarifying_question`,
  leaving `steps` empty until the user answers.
- **Model name** — defaults to `gemini-2.5-flash`. If your account lists a
  different free model, run `client.models.list()` and swap `MODEL`
  (e.g. `gemini-2.0-flash`).
