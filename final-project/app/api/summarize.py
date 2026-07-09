"""Summarisation endpoints (Module 3)."""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import has_llm
from app.core.schemas import JDAnalysis, MemoryType, Summary

router = APIRouter()


class SummarizeIn(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None
    save: bool = True


class CompareIn(BaseModel):
    urls: dict[str, str]  # label -> url


def _require_llm():
    if not has_llm():
        raise HTTPException(status_code=400, detail="GOOGLE_API_KEY not set (see .env)")


def _content(body: SummarizeIn) -> str:
    from modules.summarizer import fetch_content
    if body.text:
        return body.text
    if body.url:
        try:
            return fetch_content(body.url)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"could not fetch {body.url}: {exc}")
    raise HTTPException(status_code=422, detail="provide 'url' or 'text'")


@router.post("/summarize", response_model=Summary)
async def summarize(body: SummarizeIn) -> Summary:
    _require_llm()
    from modules.summarizer import summarize_text
    try:
        result = summarize_text(_content(body))
    except Exception as exc:  # noqa: BLE001
        from app.core.llm import raise_if_quota
        raise_if_quota(exc)
        raise
    if body.save:
        try:
            from memory.store import get_store
            get_store().add(result.tldr, MemoryType.summary,
                            metadata={"source": body.url or "text", "tags": ",".join(result.tags)})
        except Exception:  # noqa: BLE001 - saving is best-effort
            pass
    return result


@router.post("/summarize/jd", response_model=JDAnalysis)
async def summarize_jd(body: SummarizeIn) -> JDAnalysis:
    _require_llm()
    from modules.summarizer import analyze_jd
    try:
        return analyze_jd(_content(body))
    except Exception as exc:  # noqa: BLE001
        from app.core.llm import raise_if_quota
        raise_if_quota(exc)
        raise


@router.post("/summarize/compare")
async def summarize_compare(body: CompareIn) -> dict:
    _require_llm()
    from modules.summarizer import compare_pages, fetch_content
    texts = {}
    for label, url in body.urls.items():
        try:
            texts[label] = fetch_content(url)
        except Exception as exc:  # noqa: BLE001
            texts[label] = f"(could not fetch: {exc})"
    return {"comparison": compare_pages(texts)}
