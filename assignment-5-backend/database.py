"""SQLite engine + session helpers (SQLModel)."""
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

DB_PATH = Path(__file__).parent / "app.db"
ENGINE = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},  # FastAPI touches the db from threads
)


def init_db() -> None:
    """Create tables if they don't exist. Imports models for side effects."""
    import models  # noqa: F401 - registers UserProfile on SQLModel.metadata
    SQLModel.metadata.create_all(ENGINE)


def get_session() -> Session:
    return Session(ENGINE)
