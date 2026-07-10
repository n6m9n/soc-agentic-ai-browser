"""Module 5 — Cross-Module Orchestration.

Runs a Plan step-by-step, dispatching each step to a module handler, streaming
progress to the hub, and pausing for human-in-the-loop (preview/confirm) via
`ctx['pause']`. Handlers can also request a PROACTIVE follow-up (e.g. a form that
detects a deadline asks to add it to the calendar).
"""
from datetime import datetime, timedelta
from typing import Awaitable, Callable, Optional

from app.core.schemas import Plan, PlanStep, TaskState

Handler = Callable[[PlanStep, str, object, dict], Awaitable[dict]]


async def _auto_approve(prompt: dict) -> dict:
    return {"decision": "approve"}


# --- default (real) handlers --------------------------------------------------
async def _h_summarize(step, task_id, hub, ctx) -> dict:
    from modules.summarizer import summarize_text, summarize_url
    a = step.args
    url = (a.get("url") or "").strip()
    text = (a.get("text") or "").strip()

    if url.startswith("http://") or url.startswith("https://"):
        summary = summarize_url(url)
    elif len(text) > 40:
        summary = summarize_text(text)
    else:
        # No URL/text (e.g. "summarize this pdf") -> use the last uploaded document.
        from memory.ingest import uploaded_document_text
        from memory.store import get_store
        doc = uploaded_document_text(get_store())
        if not doc.strip():
            await hub.publish(task_id, "⚠ Nothing to summarize — attach a PDF (📎) or give a URL.")
            return {"status": "skipped", "reason": "no source"}
        await hub.publish(task_id, "📎 Summarizing your uploaded document…")
        summary = summarize_text(doc)

    ctx["last_summary"] = summary
    await hub.publish(task_id, f"📝 {summary.tldr}")
    return {"summary": summary.model_dump()}


async def _h_memory(step, task_id, hub, ctx) -> dict:
    # Open-ended questions ("what role fits my resume?") → RAG answer over memory,
    # not the strict form-field lookup (which would wrongly "ask the user").
    from memory.crag import get_crag
    res = get_crag().answer(step.args.get("query", ""))
    await hub.publish(task_id, f"🧠 {res.value or res.question}")
    return res.model_dump()


async def _h_form(step, task_id, hub, ctx) -> dict:
    from modules.form_filling import FormFiller, run_form_fill
    filler = ctx.get("filler") or FormFiller(profile=ctx.get("profile"), crag=ctx.get("crag"))
    res = await run_form_fill(step.args["url"], ctx["pause"], filler=filler)
    await hub.publish(task_id, f"🧾 form {res.get('status')}")
    return res


async def _h_email(step, task_id, hub, ctx) -> dict:
    service = ctx.get("gmail")
    if service is None:
        await hub.publish(task_id, "✖ email skipped: Google not connected")
        return {"status": "skipped"}
    from modules.email_assistant import resolve_recipients, run_send_email
    recipients = resolve_recipients(step.args.get("target", ""),
                                    ctx.get("contacts", {}), ctx.get("groups", {}))
    context = ""
    if ctx.get("last_summary") is not None:
        context = ctx["last_summary"].tldr
    res = await run_send_email(step.args.get("intent", ""), ctx["pause"], service,
                               recipients, context=context)
    await hub.publish(task_id, f"✉ email {res.get('status')}")
    return res


async def _h_calendar(step, task_id, hub, ctx) -> dict:
    service = ctx.get("calendar")
    if service is None:
        await hub.publish(task_id, "✖ calendar skipped: Google not connected")
        return {"status": "skipped"}
    from integrations.calendar_client import insert_event, get_primary_timezone
    from modules.calendar_intel import build_event
    from typing import Any
    
    a = step.args
    start_val = a.get("start")
    
    def is_valid_iso(s: Any) -> bool:
        if not isinstance(s, str):
            return False
        try:
            datetime.fromisoformat(s.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False

    if not start_val or not is_valid_iso(start_val):
        text_to_parse = a.get("when") or a.get("start") or ctx.get("command") or ""
        if text_to_parse:
            from pydantic import BaseModel, Field
            from typing import Optional
            from app.core.llm import get_chat

            class CalendarEventArgs(BaseModel):
                title: str = Field(description="The title of the event")
                start: str = Field(description="ISO-8601 datetime format (YYYY-MM-DDTHH:MM:SS) of the event start time")
                end: Optional[str] = Field(None, description="ISO-8601 datetime format of the event end time")
                freq: Optional[str] = Field(None, description="DAILY or WEEKLY recurrence frequency if applicable")
                count: Optional[int] = Field(None, description="Number of recurrences if applicable")

            now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            parser_prompt = (
                f"Current system time is: {now_str}\n"
                f"Analyze this scheduling instruction: '{text_to_parse}'\n"
                "Extract the event details: title, start, end, freq, count."
            )
            try:
                structured = get_chat(temperature=0).with_structured_output(CalendarEventArgs)
                parsed = structured.invoke(parser_prompt)
                a = {**a, **parsed.model_dump(exclude_none=True)}
            except Exception as e:
                await hub.publish(task_id, f"⚠ Failed to parse date/time: {e}")

    if not a.get("start") or not is_valid_iso(a["start"]):
        await hub.publish(task_id, "⚠ calendar step missing a date; skipped")
        return {"status": "skipped", "reason": "no date"}

    start = datetime.fromisoformat(a["start"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(a["end"].replace("Z", "+00:00")) if a.get("end") else start + timedelta(hours=1)
    tz = get_primary_timezone(service)
    body = build_event(a.get("title", "Event"), start, end,
                       freq=a.get("freq"), count=a.get("count"), attendees=a.get("attendees"),
                       timezone=tz)
    created = insert_event(service, body)
    await hub.publish(task_id, f"📅 calendar event created")
    return {"status": "created", "id": created.get("id")}


def default_handlers() -> dict[str, Handler]:
    return {"summarize": _h_summarize, "memory": _h_memory, "form": _h_form,
            "email": _h_email, "calendar": _h_calendar}


# --- executor -----------------------------------------------------------------
async def execute_plan(task_id: str, plan: Plan, hub,
                       handlers: Optional[dict[str, Handler]] = None,
                       ctx: Optional[dict] = None) -> list[dict]:
    handlers = handlers or default_handlers()
    ctx = ctx or {}
    ctx.setdefault("pause", _auto_approve)
    modules_in_plan = {s.module for s in plan.steps}
    results: list[dict] = []
    n = len(plan.steps)

    for i, step in enumerate(plan.steps, 1):
        await hub.publish(task_id, f"▶ Step {i}/{n}: {step.module}.{step.action}",
                          status=TaskState.running)
        handler = handlers.get(step.module)
        if handler is None:
            await hub.publish(task_id, f"⚠ no handler for {step.module!r}")
            continue
        try:
            res = await handler(step, task_id, hub, ctx) or {}
        except Exception as exc:  # noqa: BLE001 - one step's failure shouldn't sink the plan
            from app.core.llm import QUOTA_MESSAGE, is_quota_error
            msg = f"⚠ {QUOTA_MESSAGE}" if is_quota_error(exc) else f"✖ {step.module} failed: {exc}"
            await hub.publish(task_id, msg)
            res = {"error": str(exc)}
        results.append({step.module: res})

        # PROACTIVE follow-up (e.g. form found a deadline -> offer calendar)
        proactive = res.get("proactive") if isinstance(res, dict) else None
        if proactive and proactive.get("module") not in modules_in_plan:
            decision = await ctx["pause"]({"type": "confirm",
                                           "question": proactive.get("question"),
                                           "suggestion": proactive})
            if decision.get("decision") in ("approve", "yes", "send"):
                follow = handlers.get(proactive["module"])
                if follow:
                    fstep = PlanStep(module=proactive["module"],
                                     action=proactive.get("action", "auto"),
                                     args=proactive.get("args", {}))
                    await hub.publish(task_id, f"➕ Proactive: {fstep.module}.{fstep.action}")
                    await follow(fstep, task_id, hub, ctx)

    await hub.publish(task_id, "✅ All steps complete.",
                      status=TaskState.completed, result=f"Ran {n} step(s).")
    return results


def build_context(hub, task_id: str) -> dict:
    """Assemble the runtime context (pause, memory, profile, Google services)."""
    from app.core.db import ENGINE
    from app.core.models import Contact, Group, Profile
    from app.core.schemas import UserProfile
    from sqlmodel import Session, select

    async def pause(prompt: dict) -> dict:
        await hub.publish(task_id, "⏸ Waiting for your input...",
                          status=TaskState.needs_input, prompt=prompt)
        decision = await hub.wait_for_resume(task_id)
        await hub.publish(task_id, "▶ Resumed.", status=TaskState.running)
        return decision

    ctx: dict = {"pause": pause}

    with Session(ENGINE) as session:
        row = session.get(Profile, 1)
        if row:
            ctx["profile"] = UserProfile(**row.model_dump(exclude={"id"}))
        ctx["contacts"] = {c.name: c.email for c in session.exec(select(Contact)).all()}
        ctx["groups"] = {g.name: [m.strip() for m in g.members.split(",") if m.strip()]
                         for g in session.exec(select(Group)).all()}

    try:
        from memory.crag import get_crag
        ctx["crag"] = get_crag()
    except Exception:  # noqa: BLE001
        pass
    try:
        from integrations.google_oauth import get_credentials
        creds = get_credentials()
        if creds is not None:
            from integrations.calendar_client import build_service as cal_service
            from integrations.gmail_client import build_service as gmail_service
            ctx["gmail"] = gmail_service(creds)
            ctx["calendar"] = cal_service(creds)
    except Exception:  # noqa: BLE001
        pass
    return ctx
