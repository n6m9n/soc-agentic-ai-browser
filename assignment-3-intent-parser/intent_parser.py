"""Assignment 3 — Intent Parser Prototype.

The core "intelligence" module: convert a natural-language command into a
structured browser-action plan by calling the Google Gemini API (free tier).

Schema returned by parse_intent():
    {
      "action": "fill_form" | "navigate" | "email" | "summarize" | "click",
      "target_url": str,            # "" if not applicable
      "data": dict,                 # action-specific payload
      "steps": [str, ...],          # ordered human-readable plan
      "needs_clarification": bool,  # bonus: True for ambiguous commands
      "clarifying_question": str    # set only when needs_clarification is True
    }

Setup:
    pip install -r requirements.txt
    # get a FREE key at https://aistudio.google.com/apikey  (no credit card)
    export GOOGLE_API_KEY=AIza...
"""
import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()  # reads GOOGLE_API_KEY from a .env file (git-ignored) — never hardcode keys

# Free-tier flash model. Override with `export GEMINI_MODEL=gemini-2.0-flash` if
# 2.5-flash is busy; run `client.models.list()` to see what your account offers.
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# Few-shot system prompt. Examples cover navigate, fill_form, and email (>=3
# action types), plus one ambiguous case to demonstrate the clarify behaviour.
SYSTEM_PROMPT = """You are an intent parser for a browser-automation agent.
Convert the user's natural-language command into a single JSON object matching
this schema (every field required):
{
  "action": one of "fill_form" | "navigate" | "email" | "summarize" | "click",
  "target_url": string (use "" when no URL applies),
  "data": object (action-specific key/values; {} when none),
  "steps": array of short strings describing the ordered plan,
  "needs_clarification": boolean,
  "clarifying_question": string ("" unless needs_clarification is true)
}

If the command is ambiguous or missing a critical detail (which job? which
boss's email? which page?), set "needs_clarification" to true, put one focused
question in "clarifying_question", still choose your best-guess "action", and
leave "steps" empty.

Examples:

User: go to wikipedia.org
JSON: {"action":"navigate","target_url":"https://wikipedia.org","data":{},"steps":["Open a browser tab","Navigate to https://wikipedia.org"],"needs_clarification":false,"clarifying_question":""}

User: fill out the signup form on example.com with my name and email
JSON: {"action":"fill_form","target_url":"https://example.com","data":{"fields":["name","email"]},"steps":["Navigate to https://example.com","Locate the signup form","Fill name and email from the user profile","Stop before submitting for review"],"needs_clarification":false,"clarifying_question":""}

User: email this summary to my boss
JSON: {"action":"email","target_url":"","data":{"body_source":"current_summary"},"steps":[],"needs_clarification":true,"clarifying_question":"What is your boss's email address, and should I send it now or save a draft?"}
"""


def _extract_json(text: str) -> dict:
    """Parse the model's reply as JSON, tolerating accidental code fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    return json.loads(cleaned)


def _generate_with_retry(client, user_command, retries=4):
    """Call Gemini, retrying transient 503 'overloaded' errors with backoff."""
    delay = 2.0
    for attempt in range(retries):
        try:
            return client.models.generate_content(
                model=MODEL,
                contents=user_command,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    # Forces a valid JSON document (Gemini's JSON mode).
                    response_mime_type="application/json",
                ),
            )
        except errors.ServerError as exc:  # 503 UNAVAILABLE / overloaded
            if attempt == retries - 1:
                raise
            print(f"[intent_parser] model busy ({exc.code}); retrying in {delay:.0f}s...")
            time.sleep(delay)
            delay *= 2


def parse_intent(user_command: str, client: genai.Client | None = None) -> dict:
    """Convert a natural-language command into a structured action dict."""
    client = client or genai.Client()  # reads GOOGLE_API_KEY / GEMINI_API_KEY from env
    response = _generate_with_retry(client, user_command)
    try:
        return _extract_json(response.text)
    except (json.JSONDecodeError, IndexError, AttributeError):
        # Defensive fallback so callers always get the schema shape.
        return {
            "action": "navigate",
            "target_url": "",
            "data": {"raw_model_output": getattr(response, "text", "")},
            "steps": [],
            "needs_clarification": True,
            "clarifying_question": "I couldn't parse that command — could you rephrase it?",
        }


if __name__ == "__main__":
    import sys

    cmd = " ".join(sys.argv[1:]) or "go to google.com and search for AI news"
    if not os.getenv("GOOGLE_API_KEY"):
        sys.exit("set GOOGLE_API_KEY first (free key: https://aistudio.google.com/apikey)")
    print(json.dumps(parse_intent(cmd), indent=2))
