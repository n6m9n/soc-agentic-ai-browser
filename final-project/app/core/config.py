"""Central configuration + paths. Loads .env once."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]  # final-project/
load_dotenv(BASE_DIR / ".env")

# --- LLM / embeddings ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
EMBED_MODEL = os.getenv("EMBED_MODEL", "models/gemini-embedding-001")

# --- Data locations (all git-ignored) ---
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "app.db"
CHECKPOINT_PATH = DATA_DIR / "checkpoints.sqlite"
CHROMA_DIR = DATA_DIR / "chroma"

# --- Google OAuth (Phase 4+) ---
GOOGLE_CREDENTIALS = BASE_DIR / os.getenv("GOOGLE_CREDENTIALS", "credentials.json")
OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
]
OAUTH_REDIRECT_URI = os.getenv(
    "OAUTH_REDIRECT_URI", "http://127.0.0.1:8000/auth/google/callback"
)


def has_google_oauth() -> bool:
    return GOOGLE_CREDENTIALS.exists()


def has_llm() -> bool:
    return bool(GOOGLE_API_KEY)
