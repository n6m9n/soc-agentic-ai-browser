"""Command / task / WebSocket endpoints (ported + extended from A5)."""
import asyncio
import uuid

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from agents.runner import run_command
from app.core.runtime import hub
from app.core.schemas import CommandIn, CommandOut, ResumeIn, TaskState, TaskStatus

router = APIRouter()


@router.post("/command", response_model=CommandOut)
async def post_command(body: CommandIn) -> CommandOut:
    task_id = uuid.uuid4().hex[:12]
    hub.create_task(task_id, body.command)
    asyncio.create_task(run_command(task_id, body.command, hub))
    return CommandOut(task_id=task_id, status=TaskState.pending)


@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_status(task_id: str) -> TaskStatus:
    task = hub.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.post("/command/{task_id}/resume")
async def resume_command(task_id: str, body: ResumeIn) -> dict:
    """Answer a human-in-the-loop pause (approve/reject/edit/answer/send)."""
    ok = hub.resume(task_id, {"decision": body.decision, "payload": body.payload})
    if not ok:
        raise HTTPException(status_code=409, detail="task is not waiting for input")
    return {"resumed": True}


@router.websocket("/ws/{task_id}")
async def ws_updates(websocket: WebSocket, task_id: str) -> None:
    await websocket.accept()
    queue = hub.subscribe(task_id)
    try:
        task = hub.get(task_id)
        if task:
            for step in task.steps:
                await websocket.send_json(
                    {"task_id": task_id, "message": step.message,
                     "status": task.status.value, "prompt": task.prompt}
                )
            if task.status in (TaskState.completed, TaskState.failed):
                return
        while True:
            payload = await queue.get()
            await websocket.send_json(payload)
            if payload.get("status") in (TaskState.completed.value, TaskState.failed.value):
                break
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(task_id, queue)
