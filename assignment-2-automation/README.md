# Assignment 2 — Browser Automation Scripts

Three async Playwright scripts that become the agent's building blocks. Each is
wrapped in `async` functions and handles at least two error conditions
(element-not-found and timeout).

## Setup
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium      # one-time browser download
```

## Scripts
| Script | What it does | Output |
|--------|--------------|--------|
| `navigator.py` | Opens Hacker News, extracts the top 5 article titles | `top_articles.json` |
| `form_filler.py` | Fills every field on demoqa practice form from `form_data.json`, screenshots before submit | `form_before_submit.png` |
| `tab_manager.py` | Opens 5 tabs in parallel, captures each title, closes all but the first | stdout |

```bash
python navigator.py
python form_filler.py
python tab_manager.py
```

## Error handling (≥2 per script)
| Script | Condition 1 | Condition 2 |
|--------|-------------|-------------|
| navigator | `TimeoutError` loading page/list | selector matches 0 elements |
| form_filler | `TimeoutError` loading form | a mapped field is absent → skip with warning |
| tab_manager | per-tab `TimeoutError` → `"<timeout>"` | per-tab exception isolated via `asyncio.gather` |

All three import `TimeoutError as PlaywrightTimeoutError` so a slow network
degrades gracefully instead of crashing the batch.
