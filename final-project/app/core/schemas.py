"""Pydantic domain + API contracts (mirrors assignment-6-ui/contracts.py, extended).

These are the shared data shapes for the whole app. SQLModel *tables* live in
models.py; these are the request/response and in-memory domain models.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- Enums --------------------------------------------------------------------
class ActionType(str, Enum):
    navigate = "navigate"
    fill_form = "fill_form"
    email = "email"
    summarize = "summarize"
    calendar = "calendar"
    click = "click"


class TaskState(str, Enum):
    pending = "pending"
    running = "running"
    needs_input = "needs_input"   # paused for human-in-the-loop (preview/confirm/ask)
    completed = "completed"
    failed = "failed"


class MemoryType(str, Enum):
    profile_fact = "profile_fact"
    sop = "sop"
    summary = "summary"
    contact = "contact"
    group = "group"
    history = "history"
    note = "note"


# --- Task / streaming ---------------------------------------------------------
class StatusStep(BaseModel):
    ts: str = Field(default_factory=_now_iso)
    message: str


class TaskStatus(BaseModel):
    task_id: str
    command: str
    status: TaskState = TaskState.pending
    steps: list[StatusStep] = Field(default_factory=list)
    result: Optional[str] = None
    # Set when status == needs_input; the UI renders this (ask / preview / confirm).
    prompt: Optional[dict[str, Any]] = None


class CommandIn(BaseModel):
    command: str


class CommandOut(BaseModel):
    task_id: str
    status: TaskState


class ResumeIn(BaseModel):
    """Human-in-the-loop response to a needs_input pause."""
    decision: str  # "approve" | "reject" | "edit" | "answer" | "send"
    payload: dict[str, Any] = Field(default_factory=dict)


# --- Domain models ------------------------------------------------------------
class UserProfile(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    college: str = ""
    degree: str = ""
    grad_year: str = ""
    city: str = ""
    resume_path: Optional[str] = None
    linkedin: str = ""


class MemoryRecord(BaseModel):
    id: str
    type: MemoryType
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=_now_iso)


class MemoryQueryIn(BaseModel):
    query: str
    type: Optional[MemoryType] = None
    k: int = 4


class AgentAction(BaseModel):
    action: ActionType
    target_url: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    steps: list[str] = Field(default_factory=list)
    needs_clarification: bool = False
    clarifying_question: str = ""


class FormField(BaseModel):
    label: str
    selector: str
    kind: str            # text | email | select | checkbox | radio | file | textarea | date
    options: list[str] = Field(default_factory=list)
    in_iframe: bool = False


class FieldPreview(BaseModel):
    field: str
    selector: str
    value: str
    source: str          # "memory" | "generated" | "asked"
    needs_user: bool = False


class EmailDraft(BaseModel):
    to: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    subject: str = ""
    body: str = ""
    attachments: list[str] = Field(default_factory=list)
    thread_id: Optional[str] = None


class Summary(BaseModel):
    tldr: str = ""
    key_points: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    sentiment: str = ""


class JDAnalysis(BaseModel):
    required_skills: list[str] = Field(default_factory=list)
    nice_to_haves: list[str] = Field(default_factory=list)
    highlight: list[str] = Field(default_factory=list)


class PlanStep(BaseModel):
    module: str            # form | email | summarize | calendar | memory
    action: str            # short verb, e.g. "fill", "send", "summarize", "add_event"
    args: dict[str, Any] = Field(default_factory=dict)


class Plan(BaseModel):
    steps: list[PlanStep] = Field(default_factory=list)
