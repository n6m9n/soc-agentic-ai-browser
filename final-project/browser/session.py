"""Playwright browser session (sync) — ported from assignment-4's BrowserSession."""
from playwright.sync_api import sync_playwright


class BrowserSession:
    """Lazily-launched, single shared Chromium page."""

    def __init__(self, headless: bool = True) -> None:
        self._pw = None
        self._browser = None
        self.page = None
        self.headless = headless

    def ensure(self):
        if self.page is None:
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(headless=self.headless)
            self.page = self._browser.new_page()
        return self.page

    def goto(self, url: str, timeout: int = 25_000):
        page = self.ensure()
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        return page

    def close(self) -> None:
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._pw:
            self._pw.stop()
            self._pw = None
        self.page = None
