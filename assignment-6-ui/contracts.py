"""Assignment 6 — Pydantic data contracts (shared vocabulary for Weeks 7-10).

Three models the whole system agrees on:
  * UserProfile — the memory record the agent reads (name/email/resume/…).
  * AgentAction — the structured output of the intent parser (Assignment 3).
  * Task        — one user command and its live progress.

The Assignment 5 backend persists a SQLModel version of UserProfile; these are
the pure-Pydantic contracts the API and UI validate against.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    navigate = "navigate"
    fill_form = "fill_form"
    email = "email"
    summarize = "summarize"
    click = "click"


class TaskState(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class UserProfile(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    resume_text: str = ""
    resume_path: Optional[str] = None


class AgentAction(BaseModel):
    """Structured plan produced by parse_intent() (Assignment 3)."""
    action: ActionType
    target_url: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    steps: list[str] = Field(default_factory=list)
    needs_clarification: bool = False
    clarifying_question: str = ""


class Task(BaseModel):
    task_id: str
    command: str
    status: TaskState = TaskState.pending
    steps: list[str] = Field(default_factory=list)
    result: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


if __name__ == "__main__":
    # Quick self-check.
    a = AgentAction(action="navigate", target_url="https://google.com",
                    steps=["open tab", "go to url"])
    t = Task(task_id="abc123", command="go to google")
    u = UserProfile(name="Anselm", email="a@b.com")
    print(a.model_dump_json(indent=2))
    print(t.model_dump_json(indent=2))
    print(u.model_dump_json(indent=2))
