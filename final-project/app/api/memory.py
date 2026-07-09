"""Memory endpoints — cRAG query, write-back, profile ingest, resume upload, history."""
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.core.config import has_llm
from app.core.db import ENGINE
from app.core.models import Profile, TaskHistory
from app.core.schemas import MemoryQueryIn, MemoryType, UserProfile
from sqlmodel import Session, select

router = APIRouter()


def _require_llm():
    if not has_llm():
        raise HTTPException(status_code=400, detail="GOOGLE_API_KEY not set (see .env)")


@router.post("/memory/query")
async def memory_query(body: MemoryQueryIn) -> dict:
    """Run the Corrective-RAG loop: returns a found value or a needs_user prompt."""
    _require_llm()
    from memory.crag import get_crag
    try:
        result = get_crag().resolve(body.query, k=body.k)
    except Exception as exc:  # noqa: BLE001
        from app.core.llm import raise_if_quota
        raise_if_quota(exc)
        raise
    return result.model_dump()


@router.post("/memory/learn")
async def memory_learn(query: str, value: str) -> dict:
    """Write-back a newly-provided fact so it's remembered forever."""
    _require_llm()
    from memory.crag import get_crag
    rid = get_crag().learn(query, value)
    return {"stored_id": rid, "query": query, "value": value}


@router.post("/memory/ingest-profile")
async def ingest_profile_ep() -> dict:
    """Embed the current SQLite profile into the vector memory."""
    _require_llm()
    from memory.ingest import ingest_profile
    from memory.store import get_store
    with Session(ENGINE) as session:
        row = session.get(Profile, 1)
    if row is None:
        raise HTTPException(status_code=404, detail="no profile saved yet")
    n = ingest_profile(get_store(), UserProfile(**row.model_dump(exclude={"id"})))
    return {"ingested_fields": n}


@router.post("/memory/resume")
async def upload_resume(file: UploadFile) -> dict:
    """Upload a resume PDF; parse + embed it into memory."""
    _require_llm()
    from memory.ingest import ingest_resume_pdf
    from memory.store import get_store
    suffix = Path(file.filename or "resume.pdf").suffix or ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)
    chunks = ingest_resume_pdf(get_store(), tmp_path)
    return {"chunks_stored": chunks}


@router.get("/memory/history")
async def memory_history(limit: int = 50) -> list[dict]:
    with Session(ENGINE) as session:
        rows = session.exec(
            select(TaskHistory).order_by(TaskHistory.id.desc()).limit(limit)
        ).all()
    return [r.model_dump() for r in rows]
