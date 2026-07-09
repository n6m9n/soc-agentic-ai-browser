"""Assignment 5 — FastAPI backend server.

Endpoints:
  POST   /command            -> {task_id}          (kicks off the agent in the background)
  GET    /status/{task_id}   -> task progress
  GET    /user/profile       -> stored user memory
  POST   /user/profile       -> update user memory
  WS     /ws/{task_id}       -> live step-by-step updates

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload
    open http://127.0.0.1:8000/docs   (Swagger UI to test every endpoint)
"""
import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import agent_runner
from database import ENGINE, init_db
from hub import TaskHub
from models import CommandIn, CommandOut, ProfileIn, TaskStatus, UserProfile
from sqlmodel import Session

hub = TaskHub()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    hub.register_loop(asyncio.get_running_loop())
    yield


app = FastAPI(title="AI Browser Agent API", version="1.0", lifespan=lifespan)

# CORS so the React UI (different port) can call the API + open WebSockets.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Command / task endpoints -------------------------------------------------
@app.post("/command", response_model=CommandOut)
async def post_command(body: CommandIn) -> CommandOut:
    """Accept a natural-language command, return a task_id immediately, and run
    the agent in the background (streaming progress over /ws/{task_id})."""
    task_id = uuid.uuid4().hex[:12]
    hub.create_task(task_id, body.command)
    asyncio.create_task(agent_runner.run_command(task_id, body.command, hub))
    return CommandOut(task_id=task_id, status="pending")


@app.get("/status/{task_id}", response_model=TaskStatus)
async def get_status(task_id: str) -> TaskStatus:
    task = hub.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


# --- User profile (memory) endpoints -----------------------------------------
@app.get("/user/profile", response_model=UserProfile)
async def get_profile() -> UserProfile:
    with Session(ENGINE) as session:
        profile = session.get(UserProfile, 1)
        return profile or UserProfile(id=1)


@app.post("/user/profile", response_model=UserProfile)
async def set_profile(body: ProfileIn) -> UserProfile:
    with Session(ENGINE) as session:
        profile = session.get(UserProfile, 1) or UserProfile(id=1)
        for key, value in body.model_dump().items():
            setattr(profile, key, value)
        profile.id = 1
        session.add(profile)
        session.commit()
        session.refresh(profile)
        return profile


# --- Live updates -------------------------------------------------------------
@app.websocket("/ws/{task_id}")
async def ws_updates(websocket: WebSocket, task_id: str) -> None:
    await websocket.accept()
    queue = hub.subscribe(task_id)
    try:
        # Replay any steps that happened before this client connected.
        task = hub.get(task_id)
        if task:
            for step in task.steps:
                await websocket.send_json(
                    {"task_id": task_id, "message": step.message, "status": task.status}
                )
            # If it already finished before this client connected, stop here
            # rather than blocking forever on queue.get().
            if task.status in ("completed", "failed"):
                return
        # Then stream new steps live until the task ends.
        while True:
            payload = await queue.get()
            await websocket.send_json(payload)
            if payload.get("status") in ("completed", "failed"):
                break
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(task_id, queue)


@app.get("/")
async def root() -> dict:
    return {"service": "AI Browser Agent API", "docs": "/docs"}
