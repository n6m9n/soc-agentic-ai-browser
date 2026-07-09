"""Module 3 — Page/Content Summarisation.

Extract content (HTML page, any URL, or PDF link) and produce structured output
(TL;DR · key points · action items · tags · sentiment). Also a JD analyser and a
multi-page comparison. The LLM is injectable so the parsing is unit-testable.
"""
from typing import Optional

from app.core.schemas import JDAnalysis, Summary


# --- content extraction (pure / testable) ------------------------------------
def extract_text_from_html(html: str) -> str:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines)


def _pdf_bytes_to_text(data: bytes) -> str:
    import io

    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def fetch_content(url: str, timeout: float = 20.0) -> str:
    """Fetch a URL's readable text. Handles HTML and PDF links."""
    import httpx
    resp = httpx.get(url, timeout=timeout, follow_redirects=True,
                     headers={"User-Agent": "Mozilla/5.0 (AI-Browser-Assistant)"})
    resp.raise_for_status()
    ctype = resp.headers.get("content-type", "").lower()
    if url.lower().endswith(".pdf") or "application/pdf" in ctype:
        return _pdf_bytes_to_text(resp.content)
    return extract_text_from_html(resp.text)


# --- summarisation ------------------------------------------------------------
def _chat(llm):
    if llm is not None:
        return llm
    from app.core.llm import get_chat
    return get_chat(temperature=0)


def _clip(text: str, limit: int = 12000) -> str:
    return text[:limit]


def summarize_text(text: str, llm=None) -> Summary:
    structured = _chat(llm).with_structured_output(Summary)
    prompt = (
        "Summarise the content below. Provide a 3-sentence TL;DR, exactly 5 key "
        "points, any action items, 3-6 topic tags, and overall sentiment "
        "(positive/neutral/negative).\n\nCONTENT:\n" + _clip(text)
    )
    return structured.invoke(prompt)


def analyze_jd(text: str, llm=None) -> JDAnalysis:
    structured = _chat(llm).with_structured_output(JDAnalysis)
    prompt = (
        "Analyse this job description. List the required skills, the nice-to-haves, "
        "and what an applicant should highlight in their application.\n\nJD:\n"
        + _clip(text)
    )
    return structured.invoke(prompt)


def compare_pages(labeled_texts: dict[str, str], llm=None) -> str:
    joined = "\n\n".join(f"### {label}\n{_clip(t, 4000)}" for label, t in labeled_texts.items())
    prompt = (
        "Compare the following pages and return a concise markdown comparison table "
        "highlighting the key differences.\n\n" + joined
    )
    return _chat(llm).invoke(prompt).content


def summarize_url(url: str, llm=None) -> Summary:
    return summarize_text(fetch_content(url), llm=llm)
