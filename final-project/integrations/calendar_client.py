"""Google Calendar API wrapper — list events, create (incl. recurrence +
attendees), and free/busy queries. RFC3339 formatting lives here; the scheduling
logic (free slots, conflicts) is pure and lives in modules/calendar_intel.py.
"""
from datetime import datetime


def build_service(creds):
    from googleapiclient.discovery import build
    return build("calendar", "v3", credentials=creds)


def _rfc3339(dt: datetime) -> str:
    return dt.isoformat()


def list_events(service, time_min: datetime, time_max: datetime,
                calendar_id: str = "primary") -> list[dict]:
    resp = service.events().list(
        calendarId=calendar_id, timeMin=_rfc3339(time_min), timeMax=_rfc3339(time_max),
        singleEvents=True, orderBy="startTime",
    ).execute()
    return resp.get("items", [])


def freebusy(service, time_min: datetime, time_max: datetime,
             calendar_id: str = "primary") -> list[tuple[str, str]]:
    resp = service.freebusy().query(body={
        "timeMin": _rfc3339(time_min), "timeMax": _rfc3339(time_max),
        "items": [{"id": calendar_id}],
    }).execute()
    busy = resp["calendars"][calendar_id]["busy"]
    return [(b["start"], b["end"]) for b in busy]


def insert_event(service, event_body: dict, calendar_id: str = "primary",
                 send_updates: str = "all") -> dict:
    return service.events().insert(
        calendarId=calendar_id, body=event_body, sendUpdates=send_updates
    ).execute()
