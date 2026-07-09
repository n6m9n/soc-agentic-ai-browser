"""Assignment 2 — Script 3: Tab Manager.

Opens 5 tabs in parallel, captures each tab's title, then closes all but the
first.

Error conditions handled:
  1. TimeoutError      — a tab's navigation exceeds the timeout; that tab is
                         recorded as "<timeout>" instead of aborting the batch.
  2. Per-tab failure   — any other navigation error is caught per tab so one bad
                         URL doesn't sink the others (asyncio.gather + isolation).

Run:  python tab_manager.py
"""
import asyncio

from playwright.async_api import TimeoutError as PlaywrightTimeoutError, async_playwright

URLS = [
    "https://example.com/",
    "https://news.ycombinator.com/",
    "https://www.python.org/",
    "https://playwright.dev/",
    "https://demoqa.com/",
]


async def open_and_title(context, url: str) -> tuple[object, str]:
    """Open one tab, return (page, title). Title is a sentinel string on failure."""
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
        title = await page.title()
    except PlaywrightTimeoutError:
        title = "<timeout>"
    except Exception as exc:  # noqa: BLE001 - isolate one tab's failure from the rest
        title = f"<error: {type(exc).__name__}>"
    return page, title


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        # Open all 5 tabs in parallel.
        results = await asyncio.gather(*(open_and_title(context, u) for u in URLS))

        print("[tab_manager] captured titles:")
        for url, (_, title) in zip(URLS, results):
            print(f"  {title!r:40} <- {url}")

        pages = [page for page, _ in results]
        # Close all except the first.
        for page in pages[1:]:
            await page.close()
        print(f"[tab_manager] closed {len(pages) - 1} tabs, "
              f"{len(context.pages)} remaining (kept: {await pages[0].title()!r})")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
