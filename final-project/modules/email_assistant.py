"""Module 2 — Email Assistant.

LLM drafts a subject+body from a one-line intent; recipients resolve from saved
contacts/groups (or cRAG); the draft is shown for **confirm-before-send** — the
agent never sends without an explicit approval.
"""
from typing import Awaitable, Callable, Optional

from app.core.schemas import EmailDraft

PauseFn = Callable[[dict], Awaitable[dict]]


def _chat(llm):
    if llm is not None:
        return llm
    from app.core.llm import get_chat
    return get_chat(temperature=0.3)


def resolve_recipients(target: str, contacts: dict[str, str],
                       groups: dict[str, list[str]]) -> list[str]:
    """Turn a name / group name / raw email into a list of email addresses."""
    if not target:
        return []
    key = target.strip().lower()
    if "@" in target:
        return [target.strip()]
    if key in {g.lower() for g in groups}:
        for name, members in groups.items():
            if name.lower() == key:
                return list(members)
    for name, email in contacts.items():
        if name.lower() == key:
            return [email]
    return []


def draft_email(intent: str, recipients: Optional[list[str]] = None,
                context: str = "", llm=None) -> EmailDraft:
    structured = _chat(llm).with_structured_output(EmailDraft)
    prompt = (
        "Write a concise, professional email for the intent below. Produce a clear "
        "subject and a well-structured body. Do not invent facts.\n\n"
        f"Intent: {intent}\n"
        f"Recipients: {recipients or '(unspecified)'}\n"
        f"Context (may be empty):\n{context}"
    )
    draft = structured.invoke(prompt)
    if recipients and not draft.to:
        draft.to = recipients
    return draft


async def run_send_email(intent: str, pause: PauseFn, service,
                         recipients: Optional[list[str]] = None,
                         context: str = "", llm=None) -> dict:
    """Draft → PAUSE for confirm/edit → send. Never sends without approval."""
    draft = draft_email(intent, recipients, context=context, llm=llm)
    decision = await pause({"type": "confirm_send", "draft": draft.model_dump()})
    if decision.get("decision") not in ("send", "approve"):
        return {"status": "cancelled", "draft": draft.model_dump()}
    edited = decision.get("payload", {}).get("draft")
    if edited:
        draft = EmailDraft(**edited)
    from integrations.gmail_client import send_message
    res = send_message(service, draft.to, draft.subject, draft.body,
                       draft.cc, draft.attachments, draft.thread_id)
    return {"status": "sent", "id": res.get("id"), "to": draft.to}


def inbox_digest(service, max_results: int = 10, llm=None) -> list[dict]:
    """Structured digest of unread mail: sender, subject, one-line summary."""
    from integrations.gmail_client import list_unread
    messages = list_unread(service, max_results)
    for m in messages:
        m["summary"] = m.get("snippet", "")[:140]
    return messages
