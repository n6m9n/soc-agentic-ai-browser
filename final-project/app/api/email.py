"""Email endpoints (Module 2)."""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import has_llm
from app.core.db import ENGINE
from app.core.models import Contact, Group
from app.core.schemas import EmailDraft
from sqlmodel import Session, select

router = APIRouter()


class DraftIn(BaseModel):
    intent: str
    recipients: Optional[list[str]] = None
    target: Optional[str] = None   # a contact/group name to resolve
    context: str = ""


class SendIn(BaseModel):
    draft: EmailDraft


def _require(llm=True, google=True):
    if llm and not has_llm():
        raise HTTPException(status_code=400, detail="GOOGLE_API_KEY not set (see .env)")
    if google:
        from integrations.google_oauth import get_credentials
        creds = get_credentials()
        if creds is None:
            raise HTTPException(status_code=401, detail="Google not connected — visit /auth/google/login")
        return creds
    return None


def _contacts_and_groups() -> tuple[dict, dict]:
    with Session(ENGINE) as session:
        contacts = {c.name: c.email for c in session.exec(select(Contact)).all()}
        groups = {g.name: [m.strip() for m in g.members.split(",") if m.strip()]
                  for g in session.exec(select(Group)).all()}
    return contacts, groups


@router.post("/email/draft", response_model=EmailDraft)
async def email_draft(body: DraftIn) -> EmailDraft:
    _require(llm=True, google=False)
    from modules.email_assistant import draft_email, resolve_recipients
    recipients = body.recipients or []
    if body.target:
        contacts, groups = _contacts_and_groups()
        recipients = recipients + resolve_recipients(body.target, contacts, groups)
    try:
        return draft_email(body.intent, recipients or None, context=body.context)
    except Exception as exc:  # noqa: BLE001
        from app.core.llm import raise_if_quota
        raise_if_quota(exc)
        raise


@router.post("/email/send")
async def email_send(body: SendIn) -> dict:
    creds = _require(llm=False, google=True)
    from integrations.gmail_client import build_service, send_message
    d = body.draft
    if not d.to:
        raise HTTPException(status_code=422, detail="draft has no recipients")
    res = send_message(build_service(creds), d.to, d.subject, d.body,
                       d.cc, d.attachments, d.thread_id)
    return {"status": "sent", "id": res.get("id"), "to": d.to}


@router.get("/email/unread")
async def email_unread(max_results: int = 10) -> list[dict]:
    creds = _require(llm=False, google=True)
    from integrations.gmail_client import build_service
    from modules.email_assistant import inbox_digest
    return inbox_digest(build_service(creds), max_results)
