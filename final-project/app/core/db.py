"""SQLite engine + session helpers (SQLModel)."""
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import DB_PATH

ENGINE = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},  # FastAPI touches the db from threads
)


def init_db() -> None:
    import app.core.models  # noqa: F401 - registers tables on SQLModel.metadata
    SQLModel.metadata.create_all(ENGINE)


def get_session() -> Session:
    return Session(ENGINE)
