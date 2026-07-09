"""Assignment 6 — 5 pytest tests for the intent parser, one per action type.

The LLM API is MOCKED (a fake Gemini client), so tests are fast, deterministic,
and spend zero tokens. Each parsed result is also validated against the
AgentAction contract from contracts.py.

Run:  pip install -r requirements.txt && pytest
"""
import json
import sys
from pathlib import Path

import pytest

# Make the Assignment 3 parser and the local contracts importable.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "assignment-3-intent-parser"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts import AgentAction  # noqa: E402
from intent_parser import parse_intent  # noqa: E402


# --- Fake Gemini client -------------------------------------------------------
class _FakeResponse:
    def __init__(self, text: str):
        self.text = text


class _FakeModels:
    def __init__(self, text: str):
        self._text = text

    def generate_content(self, **kwargs):  # matches google-genai's surface
        return _FakeResponse(self._text)


class FakeClient:
    """Stands in for genai.Client(); returns canned JSON with no network call."""
    def __init__(self, payload: dict):
        self.models = _FakeModels(json.dumps(payload))


def _plan(action, **extra):
    base = {
        "action": action, "target_url": "", "data": {}, "steps": [],
        "needs_clarification": False, "clarifying_question": "",
    }
    base.update(extra)
    return base


# --- One test per action type -------------------------------------------------
def test_navigate():
    payload = _plan("navigate", target_url="https://google.com",
                    steps=["Open a tab", "Go to https://google.com"])
    result = parse_intent("go to google.com", client=FakeClient(payload))
    assert result["action"] == "navigate"
    assert result["target_url"] == "https://google.com"
    AgentAction(**result)  # conforms to the contract


def test_fill_form():
    payload = _plan("fill_form", target_url="https://acme.com",
                    data={"fields": ["name", "email"]}, steps=["Fill the form"])
    result = parse_intent("fill the acme form with my info", client=FakeClient(payload))
    assert result["action"] == "fill_form"
    assert result["data"]["fields"] == ["name", "email"]
    AgentAction(**result)


def test_email():
    payload = _plan("email", data={"to": "boss@corp.com"},
                    needs_clarification=True,
                    clarifying_question="Send now or save a draft?")
    result = parse_intent("email this summary to my boss", client=FakeClient(payload))
    assert result["action"] == "email"
    assert result["needs_clarification"] is True
    AgentAction(**result)


def test_summarize():
    payload = _plan("summarize", data={"source": "current_page"},
                    steps=["Read the page", "Produce a summary"])
    result = parse_intent("summarize this article", client=FakeClient(payload))
    assert result["action"] == "summarize"
    AgentAction(**result)


def test_click():
    payload = _plan("click", data={"selector": "#submit"}, steps=["Click #submit"])
    result = parse_intent("click the submit button", client=FakeClient(payload))
    assert result["action"] == "click"
    assert result["data"]["selector"] == "#submit"
    AgentAction(**result)


@pytest.mark.parametrize("action", ["navigate", "fill_form", "email", "summarize", "click"])
def test_all_actions_conform_to_contract(action):
    result = parse_intent(f"do a {action}", client=FakeClient(_plan(action)))
    assert AgentAction(**result).action.value == action
