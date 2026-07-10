"""Module 4 — Google Calendar Intelligence.

Pure scheduling logic (free-slot finding, conflict detection, recurrence event
building) — no API calls, fully unit-testable. The thin API glue lives in
integrations/calendar_client.py.
"""
from datetime import date, datetime, time, timedelta
from typing import Optional


def _merge(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    if not intervals:
        return []
    intervals = sorted(intervals)
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def find_free_slots(busy: list[tuple[datetime, datetime]],
                    window_start: datetime, window_end: datetime,
                    duration: timedelta,
                    day_start: time = time(9, 0), day_end: time = time(18, 0)
                    ) -> list[tuple[datetime, datetime]]:
    """Free gaps of at least `duration` within working hours across the window."""
    busy = _merge(busy)
    slots: list[tuple[datetime, datetime]] = []
    day = window_start.date()
    last_day = window_end.date()
    while day <= last_day:
        d_start = max(window_start, datetime.combine(day, day_start))
        d_end = min(window_end, datetime.combine(day, day_end))
        if d_start < d_end:
            cursor = d_start
            for b_start, b_end in busy:
                if b_end <= cursor or b_start >= d_end:
                    continue
                if b_start > cursor and b_start - cursor >= duration:
                    slots.append((cursor, b_start))
                cursor = max(cursor, b_end)
            if d_end - cursor >= duration:
                slots.append((cursor, d_end))
        day += timedelta(days=1)
    return slots


def detect_conflicts(events: list[tuple[datetime, datetime, str]]
                     ) -> list[tuple[str, str]]:
    """Return titles of overlapping event pairs."""
    conflicts = []
    ordered = sorted(events, key=lambda e: e[0])
    for i in range(len(ordered)):
        for j in range(i + 1, len(ordered)):
            a_start, a_end, a_title = ordered[i]
            b_start, b_end, b_title = ordered[j]
            if b_start >= a_end:
                break
            if a_start < b_end and b_start < a_end:
                conflicts.append((a_title, b_title))
    return conflicts


def build_event(title: str, start: datetime, end: datetime,
                freq: Optional[str] = None, count: Optional[int] = None,
                until: Optional[date] = None, attendees: Optional[list[str]] = None,
                location: Optional[str] = None, reminders_minutes: Optional[int] = None,
                timezone: Optional[str] = None
                ) -> dict:
    """Build a Google Calendar event body, with optional RRULE recurrence."""
    # Ensure start and end times are timezone-aware (required by Google API)
    if start.tzinfo is None:
        start = start.astimezone()
    if end.tzinfo is None:
        end = end.astimezone()

    body: dict = {
        "summary": title,
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": end.isoformat()},
    }
    if timezone:
        body["start"]["timeZone"] = timezone
        body["end"]["timeZone"] = timezone
    if location:
        body["location"] = location
    if attendees:
        body["attendees"] = [{"email": e} for e in attendees]
    if freq:
        rule = f"RRULE:FREQ={freq.upper()}"
        if count:
            rule += f";COUNT={count}"
        elif until:
            rule += f";UNTIL={until.strftime('%Y%m%dT000000Z')}"
        body["recurrence"] = [rule]
    if reminders_minutes is not None:
        body["reminders"] = {"useDefault": False,
                             "overrides": [{"method": "popup", "minutes": reminders_minutes}]}
    return body


def weekly_agenda(events: list[dict]) -> list[str]:
    """One line per event: 'Mon 14:00 — Standup'."""
    lines = []
    for ev in events:
        start = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date", "")
        title = ev.get("summary", "(no title)")
        lines.append(f"{start} — {title}")
    return lines
