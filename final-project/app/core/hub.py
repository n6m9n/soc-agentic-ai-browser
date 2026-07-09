"""In-memory task registry + pub/sub for live WebSocket updates (ported from A5).

Extended with human-in-the-loop support: a task can enter `needs_input` with a
`prompt` (ask / preview / confirm) that the UI renders, then resume.
"""
import asyncio
from typing import Any, Optional

from app.core.schemas import StatusStep, TaskState, TaskStatus


class TaskHub:
    def __init__(self) -> None:
        self.tasks: dict[str, TaskStatus] = {}
        self.subscribers: dict[str, list[asyncio.Queue]] = {}
        # Set when a task pauses for human input; resolved by /resume.
        self.resume_events: dict[str, asyncio.Event] = {}
        self.resume_payloads: dict[str, dict[str, Any]] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def register_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def create_task(self, task_id: str, command: str) -> TaskStatus:
        task = TaskStatus(task_id=task_id, command=command, status=TaskState.pending)
        self.tasks[task_id] = task
        return task

    def get(self, task_id: str) -> Optional[TaskStatus]:
        return self.tasks.get(task_id)

    # --- pub/sub --------------------------------------------------------------
    def subscribe(self, task_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self.subscribers.setdefault(task_id, []).append(queue)
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue) -> None:
        subs = self.subscribers.get(task_id, [])
        if queue in subs:
            subs.remove(queue)

    async def publish(self, task_id: str, message: str,
                      status: Optional[TaskState] = None,
                      result: Optional[str] = None,
                      prompt: Optional[dict] = None) -> None:
        task = self.tasks.get(task_id)
        if task is not None:
            task.steps.append(StatusStep(message=message))
            if status:
                task.status = status
            if result is not None:
                task.result = result
            task.prompt = prompt  # only set on needs_input
        payload = {
            "task_id": task_id,
            "message": message,
            "status": (task.status if task else status or TaskState.running).value,
            "prompt": prompt,
        }
        for queue in list(self.subscribers.get(task_id, [])):
            await queue.put(payload)

    def publish_threadsafe(self, task_id: str, message: str, **kwargs) -> None:
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.publish(task_id, message, **kwargs), self._loop)

    # --- human-in-the-loop ----------------------------------------------------
    async def wait_for_resume(self, task_id: str) -> dict[str, Any]:
        """Await a /resume call for this task; returns the decision payload."""
        event = self.resume_events.setdefault(task_id, asyncio.Event())
        event.clear()
        await event.wait()
        return self.resume_payloads.pop(task_id, {})

    def resume(self, task_id: str, payload: dict[str, Any]) -> bool:
        event = self.resume_events.get(task_id)
        if event is None:
            return False
        self.resume_payloads[task_id] = payload
        event.set()
        return True
