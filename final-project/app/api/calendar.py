"""Calendar endpoints (Module 4)."""
from datetime import datetime, time, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class FreeSlotsIn(BaseModel):
    duration_minutes: int = 60
    days: int = 7
    day_start: str = "09:00"
    day_end: str = "18:00"


class EventIn(BaseModel):
    title: str
    start: str            # ISO datetime
    end: str              # ISO datetime
    freq: Optional[str] = None      # DAILY | WEEKLY | ...
    count: Optional[int] = None
    attendees: Optional[list[str]] = None
    location: Optional[str] = None
    reminders_minutes: Optional[int] = None


def _creds():
    from integrations.google_oauth import get_credentials
    creds = get_credentials()
    if creds is None:
        raise HTTPException(status_code=401, detail="Google not connected — visit /auth/google/login")
    return creds


def _naive(dt_str: str) -> datetime:
    """Parse an RFC3339/ISO string to LOCAL wall-clock time (naive).

    Google returns busy/event times as UTC/offset; convert to local so they line
    up with datetime.now() and the local working-hours window before dropping tz.
    """
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    if dt.tzinfo is not None:
        dt = dt.astimezone()  # -> local timezone
    return dt.replace(tzinfo=None)


def _parse_hm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


@router.get("/calendar/agenda")
async def agenda(days: int = 7) -> dict:
    from integrations.calendar_client import build_service, list_events
    from modules.calendar_intel import weekly_agenda
    now = datetime.now(timezone.utc)
    events = list_events(build_service(_creds()), now, now + timedelta(days=days))
    return {"agenda": weekly_agenda(events)}


@router.post("/calendar/free-slots")
async def free_slots(body: FreeSlotsIn) -> dict:
    from integrations.calendar_client import build_service, freebusy
    from modules.calendar_intel import find_free_slots
    start = datetime.now()
    end = start + timedelta(days=body.days)
    busy_raw = freebusy(build_service(_creds()),
                        start.replace(tzinfo=timezone.utc), end.replace(tzinfo=timezone.utc))
    busy = [(_naive(s), _naive(e)) for s, e in busy_raw]
    slots = find_free_slots(busy, start, end, timedelta(minutes=body.duration_minutes),
                            _parse_hm(body.day_start), _parse_hm(body.day_end))
    return {"slots": [{"start": s.isoformat(), "end": e.isoformat()} for s, e in slots]}


@router.post("/calendar/events")
async def create_event(body: EventIn) -> dict:
    from integrations.calendar_client import build_service, insert_event, get_primary_timezone
    from modules.calendar_intel import build_event
    service = build_service(_creds())
    tz = get_primary_timezone(service)
    event_body = build_event(
        body.title, datetime.fromisoformat(body.start), datetime.fromisoformat(body.end),
        freq=body.freq, count=body.count, attendees=body.attendees,
        location=body.location, reminders_minutes=body.reminders_minutes,
        timezone=tz,
    )
    created = insert_event(service, event_body)
    return {"status": "created", "id": created.get("id"), "htmlLink": created.get("htmlLink")}


@router.get("/calendar/conflicts")
async def conflicts(days: int = 7) -> dict:
    from integrations.calendar_client import build_service, list_events
    from modules.calendar_intel import detect_conflicts
    now = datetime.now(timezone.utc)
    events = list_events(build_service(_creds()), now, now + timedelta(days=days))
    parsed = []
    for ev in events:
        s = ev.get("start", {}).get("dateTime")
        e = ev.get("end", {}).get("dateTime")
        if s and e:
            parsed.append((_naive(s), _naive(e), ev.get("summary", "(no title)")))
    return {"conflicts": detect_conflicts(parsed)}
