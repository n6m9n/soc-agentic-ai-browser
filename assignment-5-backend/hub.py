"""In-memory task registry + pub/sub so WebSocket clients get live updates.

One TaskHub instance holds every task's status/steps and a set of asyncio
queues (one per connected WebSocket) it fans each new step out to.
"""
import asyncio
from typing import Optional

from models import StatusStep, TaskStatus


class TaskHub:
    def __init__(self) -> None:
        self.tasks: dict[str, TaskStatus] = {}
        self.subscribers: dict[str, list[asyncio.Queue]] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def register_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Remember the app's event loop so worker threads can publish safely."""
        self._loop = loop

    def create_task(self, task_id: str, command: str) -> TaskStatus:
        task = TaskStatus(task_id=task_id, command=command, status="pending")
        self.tasks[task_id] = task
        return task

    def get(self, task_id: str) -> Optional[TaskStatus]:
        return self.tasks.get(task_id)

    def subscribe(self, task_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self.subscribers.setdefault(task_id, []).append(queue)
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue) -> None:
        subs = self.subscribers.get(task_id, [])
        if queue in subs:
            subs.remove(queue)

    async def publish(self, task_id: str, message: str,
                      status: Optional[str] = None, result: Optional[str] = None) -> None:
        """Record a step on the task and push it to every subscriber."""
        task = self.tasks.get(task_id)
        if task is not None:
            task.steps.append(StatusStep(message=message))
            if status:
                task.status = status
            if result is not None:
                task.result = result
        payload = {
            "task_id": task_id,
            "message": message,
            "status": task.status if task else (status or "unknown"),
        }
        for queue in list(self.subscribers.get(task_id, [])):
            await queue.put(payload)

    def publish_threadsafe(self, task_id: str, message: str,
                           status: Optional[str] = None, result: Optional[str] = None) -> None:
        """Publish from a worker thread (used by the real browser agent)."""
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self.publish(task_id, message, status, result), self._loop
        )
