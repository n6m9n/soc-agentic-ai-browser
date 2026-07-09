"""Shared Gemini chat + embeddings factories (with retry for free-tier limits)."""
from app.core.config import EMBED_MODEL, GEMINI_MODEL, GOOGLE_API_KEY

QUOTA_MESSAGE = (
    "Gemini free-tier quota is exhausted for this model right now. It resets daily "
    "(midnight Pacific) — or switch GEMINI_MODEL in .env (e.g. gemini-2.5-flash-lite) "
    "and restart the server."
)


def is_quota_error(exc: Exception) -> bool:
    s = str(exc).lower()
    return "resource_exhausted" in s or "429" in s or "quota" in s


def raise_if_quota(exc: Exception) -> None:
    """Turn a Gemini quota error into a clean HTTP 429 (else do nothing)."""
    if is_quota_error(exc):
        from fastapi import HTTPException
        raise HTTPException(status_code=429, detail=QUOTA_MESSAGE)


def get_chat(temperature: float = 0):
    from langchain_google_genai import ChatGoogleGenerativeAI
    # max_retries backs off on transient 429/503 (free tier is ~5 req/min).
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL, temperature=temperature,
        google_api_key=GOOGLE_API_KEY, max_retries=5,
    )


def get_embeddings():
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    return GoogleGenerativeAIEmbeddings(model=EMBED_MODEL, google_api_key=GOOGLE_API_KEY)
