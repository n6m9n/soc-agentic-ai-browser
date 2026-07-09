"""SQLModel tables (structured persistence). Semantic memory lives in ChromaDB."""
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Profile(SQLModel, table=True):
    """Single-user structured profile (fast, exact lookups)."""
    id: Optional[int] = Field(default=1, primary_key=True)
    name: str = ""
    email: str = ""
    phone: str = ""
    college: str = ""
    degree: str = ""
    grad_year: str = ""
    city: str = ""
    resume_path: str = ""
    linkedin: str = ""


class Contact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str


class Group(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    members: str = ""  # comma-separated emails (kept simple for the MVP)


class TaskHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(index=True)
    command: str
    status: str
    result: str = ""
    created_at: datetime = Field(default_factory=_now)


class OAuthToken(SQLModel, table=True):
    """Google OAuth token JSON (Phase 4+). One row per provider."""
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str = Field(default="google", index=True)
    token_json: str = ""
    created_at: datetime = Field(default_factory=_now)
