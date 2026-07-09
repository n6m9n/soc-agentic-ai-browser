"""Set a value into a detected form control (native HTML controls + file upload).

react-select / custom widgets are a known hard case — the vision fallback
(screenshot → Gemini) is a later enhancement; this covers standard forms and
Google Forms' native controls.
"""
from app.core.schemas import FormField

_TEXTLIKE = {"text", "email", "tel", "url", "password", "search",
             "number", "textarea", "date", "datetime-local", "month", "time"}
_TRUTHY = {"1", "true", "yes", "on", "checked"}


def _context_for(page, field: FormField):
    """Return the page or the child frame that actually contains the selector."""
    if not field.in_iframe:
        return page
    for frame in page.frames:
        if frame is page.main_frame:
            continue
        try:
            if frame.locator(field.selector).count():
                return frame
        except Exception:  # noqa: BLE001
            continue
    return page


def fill_field(page, field: FormField, value: str) -> None:
    ctx = _context_for(page, field)
    sel, kind = field.selector, field.kind
    loc = ctx.locator(sel).first

    if kind in _TEXTLIKE:
        loc.fill(str(value), timeout=10_000)
    elif kind == "select":
        try:
            ctx.select_option(sel, label=str(value), timeout=10_000)
        except Exception:  # noqa: BLE001 - fall back to matching by value
            ctx.select_option(sel, value=str(value), timeout=10_000)
    elif kind == "checkbox":
        (loc.check if str(value).lower() in _TRUTHY else loc.uncheck)(timeout=10_000)
    elif kind == "radio":
        ctx.locator(f'{sel}[value="{value}"]').first.check(timeout=10_000)
    elif kind == "file":
        loc.set_input_files(str(value), timeout=10_000)
    else:
        loc.fill(str(value), timeout=10_000)


def submit_form(page, selector: str = "button[type=submit], input[type=submit], #submit") -> bool:
    loc = page.locator(selector).first
    if loc.count() == 0:
        return False
    loc.click(timeout=10_000)
    return True
