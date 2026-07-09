"""Phase 2 — Form Filling tests against a local HTML fixture (real headless
Chromium, offline). Covers: detect, cRAG-backed plan (memory vs ask), fill+submit,
and write-back of newly-provided values.
"""
import tempfile
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from app.core.schemas import UserProfile
from browser.form_detect import detect_fields
from browser.session import BrowserSession
from modules.form_filling import FormFiller

FIXTURE = (Path(__file__).parent / "fixtures" / "form.html").resolve().as_uri()


@pytest.fixture()
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        pg = browser.new_page()
        pg.goto(FIXTURE)
        yield pg
        browser.close()


class FakeCrag:
    """Deterministic cRAG: knows 'bio', everything else is missing."""
    def __init__(self):
        self.learned = {}

    def resolve(self, query):
        from memory.crag import CragResult
        if "bio" in query.lower():
            return CragResult(status="found", value="Builder of AI agents.", source="memory")
        return CragResult(status="needs_user", question=f"need {query}")

    def learn(self, query, value, mtype=None):
        self.learned[query] = value
        return "id"


def test_detects_all_visible_fields(page):
    fields = detect_fields(page)
    kinds = {f.selector: f.kind for f in fields}
    assert "#firstName" in kinds and kinds["#firstName"] == "text"
    assert kinds["#email"] == "email"
    assert kinds["#country"] == "select"
    assert kinds["#bio"] == "textarea"
    assert kinds["#resume"] == "file"
    assert kinds["#subscribe"] == "checkbox"
    # radio group collapses to one field with both options
    gender = next(f for f in fields if f.kind == "radio")
    assert set(gender.options) == {"Male", "Female"}
    # hidden csrf field is excluded
    assert all("csrf" not in f.selector for f in fields)


def test_plan_sources_memory_vs_ask(page):
    profile = UserProfile(name="Anselm", email="a@b.com", phone="555-0142")
    filler = FormFiller(profile=profile, crag=FakeCrag())
    fields, previews = filler.plan(page)
    by = {p.selector: p for p in previews}
    assert by["#email"].source == "memory" and by["#email"].value == "a@b.com"
    assert by["#firstName"].value == "Anselm"
    assert by["#bio"].source == "memory" and "Builder" in by["#bio"].value
    # country isn't in profile or cRAG -> ask
    assert by["#country"].needs_user is True


def test_fill_and_submit(page):
    profile = UserProfile(name="Anselm", email="a@b.com", phone="555-0142")
    filler = FormFiller(profile=profile, crag=FakeCrag())
    fields, _ = filler.plan(page)

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(b"%PDF-1.4 resume"); tmp.close()
    values = {
        "#firstName": "Anselm", "#email": "a@b.com", "#phone": "555-0142",
        'input[name="gender"]': "Male", "#country": "India",
        "#bio": "Builder of AI agents.", "#subscribe": "yes", "#resume": tmp.name,
    }
    filler.apply(page, fields, values)

    assert page.locator("#firstName").input_value() == "Anselm"
    assert page.locator("#email").input_value() == "a@b.com"
    assert page.locator('input[name="gender"]:checked').get_attribute("value") == "Male"
    assert page.locator("#country").input_value() == "India"
    assert page.locator("#subscribe").is_checked()
    assert page.locator("#resume").evaluate("el => el.files.length") == 1

    assert filler.submit(page) is True
    assert page.locator("#status").text_content() == "submitted"


def test_learn_new_values_writes_back(page):
    crag = FakeCrag()
    filler = FormFiller(profile=UserProfile(), crag=crag)
    _, previews = filler.plan(page)
    # user supplies the missing country in the preview
    saved = filler.learn_new_values(previews, {"#country": "India"})
    assert saved == 1
    assert crag.learned.get("Country") == "India"


def test_run_form_fill_loop_with_pause():
    """Full async loop: plan -> pause(approve) -> fill -> submit."""
    import asyncio

    from modules.form_filling import run_form_fill

    profile = UserProfile(name="Anselm", email="a@b.com", phone="555-0142")
    filler = FormFiller(profile=profile, crag=FakeCrag())

    captured = {}

    async def pause(prompt):
        captured["prompt"] = prompt
        return {"decision": "approve",
                "payload": {"values": {"#firstName": "Anselm", "#email": "a@b.com",
                                       "#country": "USA"}}}

    result = asyncio.run(run_form_fill(FIXTURE, pause, filler=filler))

    assert result["status"] == "submitted"
    assert "#firstName" in result["filled"]
    assert captured["prompt"]["type"] == "preview"
    assert any(p["field"] for p in captured["prompt"]["previews"])
