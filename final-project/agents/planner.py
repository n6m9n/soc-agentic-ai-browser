"""Multi-step planner (Module 5) — decompose a natural-language command into an
ordered Plan of module steps. Extends assignment-3's parse_intent from a single
action to a sequence that can chain modules.
"""
from app.core.schemas import Plan

PLANNER_PROMPT = """You are the planner for a browser assistant. Break the user's
command into an ordered list of steps. Each step targets ONE module:

  - form       : fill a web form.        args: {"url": "..."}
  - summarize  : summarise a page/URL/uploaded PDF. args: {"url": "..."} for a real
                 http(s) link, OR {} (empty) when the user says "this pdf/page/
                 document" — never put a non-URL phrase in "url".
  - email      : draft+send an email.    args: {"intent": "...", "target": "person-or-group"}
  - calendar   : add a calendar event.   args: {"title": "...", "start": "ISO datetime (YYYY-MM-DDTHH:MM:SS)", "end": "ISO datetime (optional)", "freq": "DAILY|WEEKLY (optional for recurring)", "count": int (optional)}
  - memory     : recall/store a fact.    args: {"query": "..."}

Only use these modules. Keep the steps minimal and in execution order.
Use the current system time provided to resolve relative dates/times like "tomorrow", "this evening", "this week", etc., into precise ISO-8601 datetimes.

Examples:

Command: summarise https://example.com/post and email it to my mentor
Steps: summarize {"url":"https://example.com/post"} -> email {"intent":"share this summary","target":"mentor"}

Command: apply to this internship at https://jobs.x.com/123, add the deadline to my calendar, and email my mentor that I applied
Steps: form {"url":"https://jobs.x.com/123"} -> calendar {"title":"Internship deadline"} -> email {"intent":"tell mentor I applied","target":"mentor"}

Command: Add a study block every evening this week
Steps: calendar {"title":"study block", "start":"2026-07-09T18:00:00", "freq":"DAILY", "count":7}

Command: schedule a sync meeting tomorrow at 3 PM
Steps: calendar {"title":"sync meeting", "start":"2026-07-10T15:00:00"}

Command: summarize this pdf
Steps: summarize {}

Command: what's my email address
Steps: memory {"query":"email"}

Now produce the Plan for the command below.
"""


def _chat(llm):
    if llm is not None:
        return llm
    from app.core.llm import get_chat
    return get_chat(temperature=0)


def plan_command(command: str, llm=None) -> Plan:
    from datetime import datetime
    now_str = datetime.now().strftime("%A, %B %d, %Y, %I:%M %p")
    prompt = f"Current system time: {now_str}\n\n{PLANNER_PROMPT}\nCommand: {command}"
    structured = _chat(llm).with_structured_output(Plan)
    return structured.invoke(prompt)
