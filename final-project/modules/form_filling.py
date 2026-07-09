"""Module 1 — Intelligent Form Filling.

Flow: detect fields → resolve each from memory (profile then cRAG) → build a
preview → (human approves/edits) → fill → submit → save any newly-entered values
back to memory. Missing fields surface as `needs_user` in the preview.
"""
import asyncio
from typing import Awaitable, Callable, Optional

from app.core.schemas import FieldPreview, FormField, UserProfile
from browser.fill import fill_field, submit_form
from browser.form_detect import detect_fields
from browser.session import BrowserSession

# label keyword -> profile attribute (exact, no LLM call needed)
_PROFILE_KEYWORDS = {
    "first name": "name", "full name": "name", "name": "name",
    "e-mail": "email", "email": "email",
    "phone": "phone", "mobile": "phone", "contact number": "phone",
    "college": "college", "university": "college", "school": "college",
    "degree": "degree", "graduation": "grad_year", "grad year": "grad_year",
    "city": "city", "linkedin": "linkedin",
}


class FormFiller:
    def __init__(self, profile: Optional[UserProfile] = None, crag=None):
        self.profile = profile
        self.crag = crag

    def resolve_field(self, field: FormField) -> FieldPreview:
        label = field.label.lower().strip()

        # 1) exact structured-profile hit (fast, free)
        if self.profile:
            for keyword, attr in _PROFILE_KEYWORDS.items():
                if keyword in label:
                    value = getattr(self.profile, attr, "") or ""
                    if value:
                        return FieldPreview(field=field.label, selector=field.selector,
                                            value=str(value), source="memory")

        # 2) Corrective-RAG over the vector memory
        if self.crag is not None:
            res = self.crag.resolve(field.label)
            if res.status == "found" and res.value:
                return FieldPreview(field=field.label, selector=field.selector,
                                    value=res.value, source="memory")

        # 3) nothing found -> ask the user (cRAG corrective branch)
        return FieldPreview(field=field.label, selector=field.selector,
                            value="", source="asked", needs_user=True)

    def plan(self, page) -> tuple[list[FormField], list[FieldPreview]]:
        fields = detect_fields(page)
        previews = [self.resolve_field(f) for f in fields]
        return fields, previews

    def apply(self, page, fields: list[FormField], values: dict[str, str]) -> list[str]:
        """Fill every field whose selector has a value in `values`. Returns filled selectors."""
        filled = []
        by_selector = {f.selector: f for f in fields}
        for selector, value in values.items():
            field = by_selector.get(selector)
            if field is None or value in (None, ""):
                continue
            try:
                fill_field(page, field, value)
                filled.append(selector)
            except Exception:  # noqa: BLE001 - skip a field that won't accept the value
                continue
        return filled

    def learn_new_values(self, previews: list[FieldPreview], values: dict[str, str]) -> int:
        """Write-back any values the user supplied for previously-missing fields."""
        if self.crag is None:
            return 0
        saved = 0
        by_selector = {p.selector: p for p in previews}
        for selector, value in values.items():
            p = by_selector.get(selector)
            if p is not None and p.needs_user and value:
                self.crag.learn(p.field, value)
                saved += 1
        return saved

    def submit(self, page) -> bool:
        return submit_form(page)


# Human-in-the-loop callback: given the preview prompt, returns a decision dict
# {"decision": "approve"|"reject"|"edit", "payload": {"values": {selector: value}}}.
PauseFn = Callable[[dict], Awaitable[dict]]


async def run_form_fill(url: str, pause: PauseFn,
                        filler: Optional[FormFiller] = None,
                        headless: bool = True) -> dict:
    """Open a URL, plan the fill, PAUSE for human approval, then fill + submit.

    Sync Playwright is thread-affine, so EVERY browser call (open/apply/close)
    runs on one dedicated worker thread; `pause` is awaited in between so the
    caller (the hub in Phase 6) can surface the preview to the UI and resume.
    """
    import concurrent.futures

    filler = filler or FormFiller()
    session = BrowserSession(headless=headless)
    loop = asyncio.get_running_loop()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def _plan():
        session.goto(url)
        return filler.plan(session.page)

    try:
        fields, previews = await loop.run_in_executor(executor, _plan)

        decision = await pause({"type": "preview",
                                "previews": [p.model_dump() for p in previews]})
        if decision.get("decision") == "reject":
            return {"status": "rejected",
                    "previews": [p.model_dump() for p in previews]}

        # user-edited values win; otherwise use the planned values
        values = decision.get("payload", {}).get("values") \
            or {p.selector: p.value for p in previews if p.value}

        def _apply():
            filled = filler.apply(session.page, fields, values)
            learned = filler.learn_new_values(previews, values)
            submitted = filler.submit(session.page)
            return filled, learned, submitted

        filled, learned, submitted = await loop.run_in_executor(executor, _apply)
        return {"status": "submitted" if submitted else "filled",
                "filled": filled, "learned": learned}
    finally:
        await loop.run_in_executor(executor, session.close)
        executor.shutdown(wait=True)
