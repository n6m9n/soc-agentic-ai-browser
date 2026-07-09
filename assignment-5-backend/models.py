"""Assignment 5 — data models.

Two layers:
  * UserProfile        — SQLModel table, persisted in SQLite (the agent's memory).
  * The BaseModel API   — request/response contracts for the endpoints.

These mirror the pure Pydantic data contracts in
assignment-6-ui/contracts.py (Task / AgentAction / UserProfile).
"""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- SQLite persistence -------------------------------------------------------
class UserProfile(SQLModel, table=True):
    """Single-user profile the agent reads at runtime (name/email/… + resume)."""
    id: Optional[int] = Field(default=1, primary_key=True)
    name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    resume_text: str = ""


# --- API request/response contracts ------------------------------------------
class CommandIn(BaseModel):
    command: str


class CommandOut(BaseModel):
    task_id: str
    status: str


class StatusStep(BaseModel):
    ts: str = Field(default_factory=_now_iso)
    message: str


class TaskStatus(BaseModel):
    task_id: str
    command: str
    status: str = "pending"  # pending | running | completed | failed
    steps: list[StatusStep] = Field(default_factory=list)
    result: Optional[str] = None


class ProfileIn(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    resume_text: str = ""
