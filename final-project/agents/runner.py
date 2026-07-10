"""Command runner — plan a command, then execute it across modules.

With a Gemini key: parse the command into a Plan (Module 5) and run it through
the orchestrator (routing to cRAG memory + feature modules, streaming steps and
pausing for human-in-the-loop). Without a key: a simulated fallback so the
command → status → WebSocket loop is still demonstrable.
"""
import asyncio

from app.core.config import has_llm
from app.core.db import ENGINE
from app.core.hub import TaskHub
from app.core.models import TaskHistory
from app.core.schemas import TaskState
from sqlmodel import Session


async def run_command(task_id: str, command: str, hub: TaskHub) -> None:
    await hub.publish(task_id, f"Received command: {command!r}", status=TaskState.running)
    try:
        if has_llm():
            await _run_real(task_id, command, hub)
        else:
            await _run_simulated(task_id, command, hub)
    except Exception as exc:  # noqa: BLE001
        from app.core.llm import QUOTA_MESSAGE, is_quota_error
        msg = QUOTA_MESSAGE if is_quota_error(exc) else f"Error: {exc}"
        await hub.publish(task_id, f"⚠ {msg}", status=TaskState.failed)
    _record_history(hub.get(task_id))


async def _run_real(task_id: str, command: str, hub: TaskHub) -> None:
    from agents.orchestrator import build_context, execute_plan
    from agents.planner import plan_command

    plan = await asyncio.to_thread(plan_command, command)  # LLM call off the loop
    await hub.publish(task_id, f"🗺️ Planned {len(plan.steps)} step(s): "
                               + " → ".join(f"{s.module}.{s.action}" for s in plan.steps))
    ctx = build_context(hub, task_id)
    ctx["command"] = command
    await execute_plan(task_id, plan, hub, ctx=ctx)


async def _run_simulated(task_id: str, command: str, hub: TaskHub) -> None:
    for step in ["🧠 Parsing intent...", "🗺️ Planning...",
                 "⚙️ (set GOOGLE_API_KEY to run real modules)"]:
        await asyncio.sleep(0.3)
        await hub.publish(task_id, step)
    await hub.publish(task_id, "✅ Done.", status=TaskState.completed,
                      result=f"Simulated: {command}")


def _record_history(task) -> None:
    if task is None:
        return
    with Session(ENGINE) as session:
        session.add(TaskHistory(task_id=task.task_id, command=task.command,
                                status=task.status.value, result=task.result or ""))
        session.commit()
