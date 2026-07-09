"""Google OAuth endpoints (Phase 4)."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.config import has_google_oauth

router = APIRouter()


@router.get("/auth/google/login")
async def google_login():
    if not has_google_oauth():
        raise HTTPException(status_code=400,
                            detail="credentials.json missing — see README for Google Cloud setup")
    from integrations.google_oauth import authorization_url
    return RedirectResponse(authorization_url())


@router.get("/auth/google/callback")
async def google_callback(code: str = "", error: str = ""):
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="missing authorization code")
    from integrations.google_oauth import exchange_code
    try:
        exchange_code(code)
    except Exception as exc:  # noqa: BLE001 - show a readable reason instead of a 500
        return HTMLResponse(
            f"<h3>❌ Could not complete Google sign-in</h3><pre>{type(exc).__name__}: {exc}</pre>"
            "<p>Fix the issue, then retry <a href='/auth/google/login'>/auth/google/login</a>.</p>",
            status_code=400,
        )
    return HTMLResponse(
        "<h3>✅ Google connected. You can close this tab and return to the app.</h3>"
    )


@router.get("/auth/google/status")
async def google_status() -> dict:
    from integrations.google_oauth import is_connected
    return {"credentials_present": has_google_oauth(),
            "connected": has_google_oauth() and is_connected()}
