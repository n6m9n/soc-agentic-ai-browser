"""User profile endpoints (structured SQLite record — the fast, exact memory)."""
from fastapi import APIRouter

from app.core.db import ENGINE
from app.core.models import Profile
from app.core.schemas import UserProfile
from sqlmodel import Session

router = APIRouter()


@router.get("/user/profile", response_model=UserProfile)
async def get_profile() -> UserProfile:
    with Session(ENGINE) as session:
        row = session.get(Profile, 1)
        if row is None:
            return UserProfile()
        return UserProfile(**row.model_dump(exclude={"id"}))


@router.post("/user/profile", response_model=UserProfile)
async def set_profile(body: UserProfile) -> UserProfile:
    with Session(ENGINE) as session:
        row = session.get(Profile, 1) or Profile(id=1)
        for key, value in body.model_dump().items():
            if value is not None:
                setattr(row, key, value)
        row.id = 1
        session.add(row)
        session.commit()
        session.refresh(row)
        return UserProfile(**row.model_dump(exclude={"id"}))
