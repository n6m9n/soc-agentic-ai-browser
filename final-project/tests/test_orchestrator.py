"""Phase 6 — planner + orchestrator. LLM mocked; handlers faked to verify
sequencing, proactive follow-ups, and cross-module context chaining.
"""
import asyncio

from agents.orchestrator import execute_plan
from agents.planner import plan_command
from app.core.schemas import Plan, PlanStep, TaskState


class FakeHub:
    def __init__(self):
        self.msgs = []

    async def publish(self, task_id, message, status=None, result=None, prompt=None):
        self.msgs.append({"message": message, "status": status, "prompt": prompt})

    def get(self, task_id):
        return None


async def _approve(prompt):
    return {"decision": "approve"}


def test_plan_command_mocked():
    plan = Plan(steps=[PlanStep(module="summarize", action="summarize", args={"url": "u"}),
                       PlanStep(module="email", action="send", args={"target": "mentor"})])

    class _Structured:
        def invoke(self, prompt): return plan

    class FakeLLM:
        def with_structured_output(self, schema): return _Structured()

    out = plan_command("summarise u and email mentor", llm=FakeLLM())
    assert [s.module for s in out.steps] == ["summarize", "email"]


def test_executor_runs_steps_in_order_and_completes():
    calls = []

    async def h_sum(step, tid, hub, ctx): calls.append("summarize"); return {}
    async def h_email(step, tid, hub, ctx): calls.append("email"); return {"status": "sent"}

    plan = Plan(steps=[PlanStep(module="summarize", action="s"),
                       PlanStep(module="email", action="e")])
    hub = FakeHub()
    asyncio.run(execute_plan("t", plan, hub,
                             handlers={"summarize": h_sum, "email": h_email},
                             ctx={"pause": _approve}))
    assert calls == ["summarize", "email"]
    assert any(m["status"] == TaskState.completed for m in hub.msgs)


def test_proactive_deadline_to_calendar():
    scheduled = []

    async def h_form(step, tid, hub, ctx):
        return {"status": "submitted",
                "proactive": {"module": "calendar", "action": "add",
                              "question": "Add the deadline to your calendar?",
                              "args": {"title": "Hackathon deadline"}}}

    async def h_cal(step, tid, hub, ctx):
        scheduled.append(step.args); return {"status": "created"}

    plan = Plan(steps=[PlanStep(module="form", action="fill", args={"url": "x"})])
    asyncio.run(execute_plan("t", plan, FakeHub(),
                             handlers={"form": h_form, "calendar": h_cal},
                             ctx={"pause": _approve}))
    assert scheduled and scheduled[0]["title"] == "Hackathon deadline"


def test_proactive_declined_when_user_rejects():
    scheduled = []

    async def h_form(step, tid, hub, ctx):
        return {"proactive": {"module": "calendar", "question": "?", "args": {}}}

    async def h_cal(step, tid, hub, ctx):
        scheduled.append(1); return {}

    async def reject(prompt):
        return {"decision": "reject"}

    plan = Plan(steps=[PlanStep(module="form", action="fill", args={})])
    asyncio.run(execute_plan("t", plan, FakeHub(),
                             handlers={"form": h_form, "calendar": h_cal},
                             ctx={"pause": reject}))
    assert scheduled == []


def test_summary_to_email_context_chaining():
    seen = {}

    class _S:
        tldr = "The TL;DR."

    async def h_sum(step, tid, hub, ctx): ctx["last_summary"] = _S(); return {}
    async def h_email(step, tid, hub, ctx):
        seen["ctx"] = ctx.get("last_summary"); return {"status": "sent"}

    plan = Plan(steps=[PlanStep(module="summarize", action="s"),
                       PlanStep(module="email", action="e")])
    asyncio.run(execute_plan("t", plan, FakeHub(),
                             handlers={"summarize": h_sum, "email": h_email},
                             ctx={"pause": _approve}))
    assert seen["ctx"].tldr == "The TL;DR."
