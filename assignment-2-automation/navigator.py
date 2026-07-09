"""Assignment 2 — Script 1: Navigator.

Opens a news site (Hacker News), extracts the titles of the top 5 articles, and
saves them to a JSON file.

Error conditions handled:
  1. TimeoutError      — page/selector never loads within the timeout.
  2. Element not found — the title selector matches nothing (site markup changed).

Run:  python navigator.py
"""
import asyncio
import json
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeoutError, async_playwright

NEWS_URL = "https://news.ycombinator.com/"
TITLE_SELECTOR = "span.titleline > a"
OUTPUT_FILE = Path(__file__).parent / "top_articles.json"
TOP_N = 5


async def extract_top_titles() -> list[str]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(NEWS_URL, wait_until="domcontentloaded", timeout=20_000)
            # Error condition 1: timeout waiting for the article list.
            await page.wait_for_selector(TITLE_SELECTOR, timeout=10_000)
        except PlaywrightTimeoutError:
            await browser.close()
            raise RuntimeError(f"timed out loading {NEWS_URL} or its article list")

        links = page.locator(TITLE_SELECTOR)
        count = await links.count()
        # Error condition 2: selector matched nothing — markup likely changed.
        if count == 0:
            await browser.close()
            raise RuntimeError(f"no articles found with selector {TITLE_SELECTOR!r}")

        titles = []
        for i in range(min(TOP_N, count)):
            titles.append((await links.nth(i).inner_text()).strip())
        await browser.close()
        return titles


async def main() -> None:
    try:
        titles = await extract_top_titles()
    except RuntimeError as exc:
        print(f"[navigator] failed: {exc}")
        return

    payload = {"source": NEWS_URL, "count": len(titles), "titles": titles}
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[navigator] saved {len(titles)} titles -> {OUTPUT_FILE.name}")
    for i, title in enumerate(titles, 1):
        print(f"  {i}. {title}")


if __name__ == "__main__":
    asyncio.run(main())
