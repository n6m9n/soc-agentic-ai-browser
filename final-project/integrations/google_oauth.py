"""Google OAuth 2.0 (web flow) for Gmail + Calendar.

The token is stored in the OAuthToken SQLite row (git-ignored db). To set up:
Google Cloud Console → enable Gmail API + Calendar API → create an OAuth client
(Web application) with redirect URI http://127.0.0.1:8000/auth/google/callback →
download the client secret as final-project/credentials.json → add yourself as a
Test user. See README.
"""
import os
from typing import Optional

# Local dev over http:// — allow the token exchange on an insecure (non-https)
# localhost redirect, and don't fail when Google returns extra scopes (e.g. openid).
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

from app.core.config import GOOGLE_CREDENTIALS, OAUTH_REDIRECT_URI, OAUTH_SCOPES
from app.core.db import ENGINE
from app.core.models import OAuthToken
from sqlmodel import Session, select


# PKCE: the code_verifier created at /login must be reused at /callback. Single
# local process, single user, so a module global is sufficient.
_PENDING: dict[str, str] = {}


def _flow():
    from google_auth_oauthlib.flow import Flow
    return Flow.from_client_secrets_file(
        str(GOOGLE_CREDENTIALS), scopes=OAUTH_SCOPES, redirect_uri=OAUTH_REDIRECT_URI,
        autogenerate_code_verifier=True,
    )


def authorization_url() -> str:
    flow = _flow()
    url, _state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )
    _PENDING["code_verifier"] = flow.code_verifier  # remember for the callback
    return url


def exchange_code(code: str) -> None:
    """Exchange the callback code for tokens and persist them."""
    flow = _flow()
    flow.code_verifier = _PENDING.get("code_verifier")  # PKCE round-trip
    flow.fetch_token(code=code)
    _save_token(flow.credentials.to_json())


def _save_token(token_json: str) -> None:
    with Session(ENGINE) as session:
        row = session.exec(select(OAuthToken).where(OAuthToken.provider == "google")).first()
        row = row or OAuthToken(provider="google")
        row.token_json = token_json
        session.add(row)
        session.commit()


def get_credentials() -> Optional["object"]:
    """Load stored credentials, refreshing if expired. None if not connected."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    with Session(ENGINE) as session:
        row = session.exec(select(OAuthToken).where(OAuthToken.provider == "google")).first()
    if row is None or not row.token_json:
        return None
    creds = Credentials.from_authorized_user_info(_json_loads(row.token_json), OAUTH_SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_token(creds.to_json())
    return creds


def is_connected() -> bool:
    return get_credentials() is not None


def _json_loads(s: str) -> dict:
    import json
    return json.loads(s)
