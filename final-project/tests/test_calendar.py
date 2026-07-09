"""Phase 5 — Calendar scheduling logic (pure) + event building + mocked service."""
from datetime import date, datetime, time, timedelta

from modules.calendar_intel import (build_event, detect_conflicts,
                                     find_free_slots, weekly_agenda)


def test_find_free_slots_around_busy():
    busy = [(datetime(2026, 7, 6, 10), datetime(2026, 7, 6, 11)),
            (datetime(2026, 7, 6, 13), datetime(2026, 7, 6, 14))]
    slots = find_free_slots(busy, datetime(2026, 7, 6, 9), datetime(2026, 7, 6, 18),
                            timedelta(hours=2))
    hhmm = [(s.strftime("%H:%M"), e.strftime("%H:%M")) for s, e in slots]
    # 9-10 is only 1h (< 2h, excluded); 11-13 and 14-18 qualify
    assert ("11:00", "13:00") in hhmm
    assert ("14:00", "18:00") in hhmm
    assert ("09:00", "10:00") not in hhmm


def test_free_slots_respect_working_hours():
    slots = find_free_slots([], datetime(2026, 7, 6, 0), datetime(2026, 7, 6, 23, 59),
                            timedelta(hours=1), day_start=time(9), day_end=time(17))
    assert slots == [(datetime(2026, 7, 6, 9), datetime(2026, 7, 6, 17))]


def test_detect_conflicts():
    events = [(datetime(2026, 7, 6, 10), datetime(2026, 7, 6, 11), "A"),
              (datetime(2026, 7, 6, 10, 30), datetime(2026, 7, 6, 11, 30), "B"),
              (datetime(2026, 7, 6, 12), datetime(2026, 7, 6, 13), "C")]
    assert detect_conflicts(events) == [("A", "B")]


def test_build_recurring_event_with_rrule():
    body = build_event("DSA practice", datetime(2026, 7, 6, 20), datetime(2026, 7, 6, 21),
                       freq="DAILY", count=14, reminders_minutes=10)
    assert body["summary"] == "DSA practice"
    assert body["recurrence"] == ["RRULE:FREQ=DAILY;COUNT=14"]
    assert body["reminders"]["overrides"][0]["minutes"] == 10


def test_build_event_with_attendees_and_until():
    body = build_event("Team sync", datetime(2026, 7, 6, 9), datetime(2026, 7, 6, 10),
                       freq="WEEKLY", until=date(2026, 8, 1),
                       attendees=["a@x.com", "b@x.com"], location="Zoom")
    assert body["attendees"] == [{"email": "a@x.com"}, {"email": "b@x.com"}]
    assert "UNTIL=20260801T000000Z" in body["recurrence"][0]
    assert body["location"] == "Zoom"


def test_weekly_agenda_formatting():
    events = [{"summary": "Standup", "start": {"dateTime": "2026-07-06T14:00:00"}}]
    lines = weekly_agenda(events)
    assert lines == ["2026-07-06T14:00:00 — Standup"]
