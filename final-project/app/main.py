"""Final project — FastAPI app entry point.

Run:
    pip install -r requirements.txt
    uvicorn app.main:app --reload
    open http://127.0.0.1:8000/docs
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api import auth, calendar, commands, email, memory, profile, summarize
from app.core.db import init_db
from app.core.runtime import hub


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    hub.register_loop(asyncio.get_running_loop())
    yield


app = FastAPI(title="Agentic AI Browser Assistant", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(commands.router, tags=["commands"])
app.include_router(profile.router, tags=["profile"])
app.include_router(memory.router, tags=["memory"])
app.include_router(summarize.router, tags=["summarize"])
app.include_router(auth.router, tags=["auth"])
app.include_router(email.router, tags=["email"])
app.include_router(calendar.router, tags=["calendar"])


@app.get("/", include_in_schema=False)
async def root():
    # Visiting the base URL in a browser lands on the Swagger UI.
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "ai-browser-assistant", "docs": "/docs"}
