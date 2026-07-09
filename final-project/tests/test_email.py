"""Phase 4 — Email assistant tests. Gmail service + LLM are faked (no OAuth,
no network): MIME build, recipient resolution, draft, confirm-before-send, digest.
"""
import base64

from app.core.schemas import EmailDraft
from integrations.gmail_client import build_mime, send_message
from modules.email_assistant import (draft_email, inbox_digest,
                                      resolve_recipients, run_send_email)


# --- fakes --------------------------------------------------------------------
class _Send:
    def __init__(self, store): self.store = store
    def send(self, userId, body): self.store["sent"] = body; return self
    def list(self, userId, q, maxResults): self.store["q"] = q; return _Exec(
        {"messages": [{"id": "m1"}]})
    def get(self, userId, id, format=None, metadataHeaders=None):
        return _Exec({"id": id, "threadId": "t1", "snippet": "hi there",
                      "payload": {"headers": [{"name": "From", "value": "arjun@x.com"},
                                              {"name": "Subject", "value": "Standup"}]}})
    def execute(self): return {"id": "sent1", "threadId": "t1"}


class _Exec:
    def __init__(self, val): self.val = val
    def execute(self): return self.val


class _Users:
    def __init__(self, store): self._m = _Send(store)
    def messages(self): return self._m


class FakeService:
    def __init__(self): self.store = {}
    def users(self): return _Users(self.store)


class _FakeStructured:
    def __init__(self, obj): self.obj = obj
    def invoke(self, prompt): return self.obj


class FakeLLM:
    def __init__(self, obj): self.obj = obj
    def with_structured_output(self, schema): return _FakeStructured(self.obj)


# --- tests --------------------------------------------------------------------
def test_build_mime_roundtrip():
    raw = build_mime(["a@b.com"], "Hi", "Body text", cc=["c@d.com"])
    decoded = base64.urlsafe_b64decode(raw).decode()
    assert "To: a@b.com" in decoded and "Subject: Hi" in decoded and "Body text" in decoded


def test_resolve_recipients():
    contacts = {"Arjun": "arjun@x.com"}
    groups = {"team": ["a@x.com", "b@x.com"]}
    assert resolve_recipients("arjun", contacts, groups) == ["arjun@x.com"]
    assert resolve_recipients("team", contacts, groups) == ["a@x.com", "b@x.com"]
    assert resolve_recipients("raw@z.com", contacts, groups) == ["raw@z.com"]


def test_draft_email_fills_recipients():
    draft = EmailDraft(subject="Deadline extension", body="Dear Professor, ...")
    result = draft_email("ask prof for extension", ["prof@uni.edu"], llm=FakeLLM(draft))
    assert result.subject == "Deadline extension"
    assert result.to == ["prof@uni.edu"]


def test_send_message_uses_service():
    svc = FakeService()
    res = send_message(svc, ["a@b.com"], "S", "B")
    assert res["id"] == "sent1"
    assert "raw" in svc.store["sent"]


def test_confirm_before_send_cancel_and_send():
    import asyncio
    draft = EmailDraft(to=["p@x.com"], subject="S", body="B")

    async def deny(prompt):
        assert prompt["type"] == "confirm_send"
        return {"decision": "reject"}

    async def approve(prompt):
        return {"decision": "send"}

    cancelled = asyncio.run(run_send_email("x", deny, FakeService(),
                                           ["p@x.com"], llm=FakeLLM(draft)))
    assert cancelled["status"] == "cancelled"

    sent = asyncio.run(run_send_email("x", approve, FakeService(),
                                      ["p@x.com"], llm=FakeLLM(draft)))
    assert sent["status"] == "sent"


def test_inbox_digest():
    digest = inbox_digest(FakeService(), max_results=5)
    assert digest and digest[0]["from"] == "arjun@x.com"
    assert digest[0]["subject"] == "Standup"
    assert "summary" in digest[0]
