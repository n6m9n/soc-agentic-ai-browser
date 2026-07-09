"""Assignment 4 — LangChain agent with Playwright tools.

Integrates the Week 2 (browser automation) and Week 3 (intent parsing) work into
a real agent that drives a browser:

  * 3 LangChain tools: navigate_to(url), click_element(selector),
    type_text(selector, text)  (+ a bonus get_profile(field) tool).
  * A tool-calling agent on Google Gemini (free tier) that plans and calls
    those tools.
  * Conversation memory so follow-up commands ("now click the first result")
    remember what just happened.

Setup:
    pip install -r requirements.txt
    playwright install chromium
    # free key (no credit card): https://aistudio.google.com/apikey
    export GOOGLE_API_KEY=AIza...
    python agent.py
"""
import os
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

from profile_store import ProfileStore

load_dotenv()  # reads GOOGLE_API_KEY from a .env file (git-ignored) — never hardcode keys

# Free-tier flash model. Override with `export GEMINI_MODEL=gemini-2.0-flash` if busy.
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
PROFILE = ProfileStore()


class BrowserSession:
    """Lazily-launched, single shared Chromium page the tools operate on."""

    def __init__(self) -> None:
        self._pw = None
        self._browser = None
        self.page = None

    def ensure(self):
        if self.page is None:
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(headless=True)
            self.page = self._browser.new_page()
        return self.page

    def close(self) -> None:
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()


BROWSER = BrowserSession()


# --- The 3 required tools (+ bonus profile tool) -----------------------------
@tool
def navigate_to(url: str) -> str:
    """Open the given URL in the browser and return the resulting page title."""
    page = BROWSER.ensure()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20_000)
        return f"Navigated to {url} — page title: {page.title()!r}"
    except PlaywrightTimeoutError:
        return f"Timeout: {url} did not load within 20s"


@tool
def click_element(selector: str) -> str:
    """Click the first element matching the CSS selector on the current page."""
    page = BROWSER.ensure()
    try:
        page.click(selector, timeout=10_000)
        return f"Clicked {selector!r}"
    except PlaywrightTimeoutError:
        return f"Could not find/click {selector!r} within 10s"


@tool
def type_text(selector: str, text: str) -> str:
    """Type text into the input element matching the CSS selector."""
    page = BROWSER.ensure()
    try:
        page.fill(selector, text, timeout=10_000)
        return f"Typed {text!r} into {selector!r}"
    except PlaywrightTimeoutError:
        return f"Could not find input {selector!r} within 10s"


@tool
def get_profile(field: str) -> str:
    """Look up a field (name, email, phone, resume_path, linkedin) from the user's profile."""
    return PROFILE.get(field)


TOOLS = [navigate_to, click_element, type_text, get_profile]


SYSTEM_PROMPT = (
    "You are a browser-automation agent. Use the tools to carry out the user's "
    "request step by step. Prefer real CSS selectors. When you need the user's "
    "name, email, or resume path, call get_profile. Report what you did concisely."
)


def build_agent():
    """Wire up the tool-calling agent with conversation memory.

    LangChain 1.x `create_agent` returns a LangGraph agent; passing an
    InMemorySaver checkpointer makes it remember prior turns automatically when
    every invoke shares the same `thread_id`.
    """
    llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0)
    return create_agent(
        model=llm,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )


def main() -> None:
    if not os.getenv("GOOGLE_API_KEY"):
        sys.exit("set GOOGLE_API_KEY first (free key: https://aistudio.google.com/apikey)")

    agent = build_agent()
    cfg = {"configurable": {"thread_id": "demo"}}  # same thread => shared memory

    # Full loop: command -> reasoning -> tool execution -> result -> next step.
    turns = [
        "Go to https://example.com and tell me the page title.",
        "What is my email address according to my profile?",
        "Now navigate to https://news.ycombinator.com and report its title.",
        "Which site did you visit first?",  # tests conversation memory
    ]
    try:
        for turn in turns:
            print(f"\n=== USER: {turn} ===")
            result = agent.invoke({"messages": [("user", turn)]}, config=cfg)
            print("AGENT:", result["messages"][-1].content)
    finally:
        BROWSER.close()


if __name__ == "__main__":
    main()
