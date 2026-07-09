"""Runs a command as a background task, streaming steps to the hub.

Two modes:
  * default (simulated)  — emits realistic step-by-step updates with small delays
    so the whole command -> status -> WebSocket loop is demonstrable with no LLM
    key, no browser, and no paid tokens.
  * USE_REAL_AGENT=true  — lazily imports the Week 4 LangChain agent and streams
    its real reasoning/tool steps. Requires the Week 4 deps, a GOOGLE_API_KEY,
    and `playwright install chromium`.
"""
import asyncio
import os
import sys
from pathlib import Path

from hub import TaskHub


async def run_command(task_id: str, command: str, hub: TaskHub) -> None:
    await hub.publish(task_id, f"Received command: {command!r}", status="running")
    try:
        if os.getenv("USE_REAL_AGENT", "").lower() in ("1", "true", "yes"):
            await _run_real_agent(task_id, command, hub)
        else:
            await _run_simulated(task_id, command, hub)
    except Exception as exc:  # noqa: BLE001 - surface any failure to the client
        await hub.publish(task_id, f"Error: {exc}", status="failed")


async def _run_simulated(task_id: str, command: str, hub: TaskHub) -> None:
    steps = [
        "🧠 Parsing intent from natural-language command...",
        "🗺️  Building a structured action plan...",
        "🌐 Launching browser session...",
        f"⌨️  Executing action for: {command!r}",
        "📸 Capturing result...",
    ]
    for step in steps:
        await asyncio.sleep(0.6)  # visualises live streaming in the UI
        await hub.publish(task_id, step)
    await hub.publish(
        task_id, "✅ Task complete.",
        status="completed", result=f"Simulated completion of: {command}",
    )


async def _run_real_agent(task_id: str, command: str, hub: TaskHub) -> None:
    """Stream the actual Week 4 agent's steps (imported lazily)."""
    week4 = Path(__file__).resolve().parents[1] / "assignment-4-langchain-agent"
    sys.path.insert(0, str(week4))
    import agent as week4_agent  # noqa: E402 - lazy import, only when enabled

    agent = week4_agent.build_agent()
    cfg = {"configurable": {"thread_id": task_id}}

    def work() -> None:
        # LangGraph agents stream node-by-node updates; forward each to the hub.
        for chunk in agent.stream(
            {"messages": [("user", command)]}, config=cfg, stream_mode="updates"
        ):
            for node, update in chunk.items():
                for msg in update.get("messages", []) if isinstance(update, dict) else []:
                    text = getattr(msg, "content", "")
                    if text:
                        hub.publish_threadsafe(task_id, f"[{node}] {text}")

    await asyncio.to_thread(work)
    await hub.publish(task_id, "✅ Agent finished.", status="completed",
                      result="See streamed steps above.")
