"""Assignment 2 — Script 2: Form Filler.

Goes to demoqa.com/automation-practice-form, fills every field from a JSON file,
and screenshots the page before submitting.

Error conditions handled:
  1. TimeoutError      — the form never loads within the timeout.
  2. Element not found — a JSON key maps to a field that isn't on the page;
                         it is skipped with a warning instead of crashing.

Run:  python form_filler.py
"""
import asyncio
import json
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeoutError, async_playwright

FORM_URL = "https://demoqa.com/automation-practice-form"
DATA_FILE = Path(__file__).parent / "form_data.json"
SCREENSHOT = Path(__file__).parent / "form_before_submit.png"

# Maps JSON keys to the selectors / handling strategy for each field.
TEXT_FIELDS = {
    "firstName": "#firstName",
    "lastName": "#lastName",
    "userEmail": "#userEmail",
    "userNumber": "#userNumber",
    "currentAddress": "#currentAddress",
}


async def fill_form(data: dict) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(FORM_URL, wait_until="domcontentloaded", timeout=25_000)
            await page.wait_for_selector("#firstName", timeout=10_000)
        except PlaywrightTimeoutError:
            await browser.close()
            raise RuntimeError(f"timed out loading {FORM_URL}")

        # Plain text inputs.
        for key, selector in TEXT_FIELDS.items():
            value = data.get(key)
            if value is None:
                continue
            field = page.locator(selector)
            # Error condition 2: field absent on the page.
            if await field.count() == 0:
                print(f"[form_filler] warning: field {selector!r} not found, skipping")
                continue
            await field.fill(str(value))

        # Gender radio (label click avoids the input being intercepted).
        if data.get("gender"):
            label = page.locator(f"label:has-text('{data['gender']}')").first
            if await label.count():
                await label.click()

        # Date of Birth (react-datepicker): open it, pick month/year, click the day.
        dob = data.get("dob")
        if dob:
            try:
                await page.click("#dateOfBirthInput")
                await page.select_option(".react-datepicker__month-select", label=dob["month"])
                await page.select_option(".react-datepicker__year-select", label=str(dob["year"]))
                day = str(dob["day"]).zfill(3)  # react-datepicker uses 3-digit day classes (e.g. day--015)
                await page.click(
                    f".react-datepicker__day--{day}"
                    ":not(.react-datepicker__day--outside-month)"
                )
            except PlaywrightTimeoutError:
                print("[form_filler] warning: date picker did not respond")

        # Subjects auto-complete.
        if data.get("subjects"):
            subj = page.locator("#subjectsInput")
            if await subj.count():
                await subj.fill(str(data["subjects"]))
                try:
                    await page.wait_for_selector(".subjects-auto-complete__option", timeout=5_000)
                except PlaywrightTimeoutError:
                    print("[form_filler] warning: subject suggestion slow; committing anyway")
                # Press Enter regardless — react-select commits the top match.
                await subj.press("Enter")

        await page.screenshot(path=str(SCREENSHOT), full_page=True)
        print(f"[form_filler] screenshot saved -> {SCREENSHOT.name} (not submitted)")
        # NOTE: deliberately not clicking #submit — the brief asks to screenshot
        # *before* submitting so the filled-but-unsent state is captured.
        await browser.close()


async def main() -> None:
    if not DATA_FILE.exists():
        print(f"[form_filler] failed: {DATA_FILE} missing")
        return
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    try:
        await fill_form(data)
    except RuntimeError as exc:
        print(f"[form_filler] failed: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
