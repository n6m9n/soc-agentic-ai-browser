# Assignment 1 — Environment Setup + Python Warmup

Sets up the working environment and proves Python readiness before the agent work begins.

## What's here
| File | Purpose |
|------|---------|
| `memory.py` | Async script that reads a JSON user profile and prints it nicely — the seed of the agent's **memory layer** |
| `user_info.json` | Sample profile (name, email, phone, address) |
| `selectors.md` | 3 input + 2 button + 1 dropdown CSS selectors found in Chrome DevTools |
| `screenshots/` | DevTools screenshots of the selectors |
| `requirements.txt` | Only `requests` is installed for now (per the brief) |
| `hackerrank.md` | Days 0–5 progress tracker |

## 1. Create the venv (Python 3.10+) in `ai-browser-agent/`
The brief asks for a venv in a folder called `ai-browser-agent`. From this folder:
```bash
python3 -m venv ai-browser-agent
source ai-browser-agent/bin/activate     # Windows: ai-browser-agent\Scripts\activate
python --version                          # confirm 3.10+
pip install -r requirements.txt           # installs requests only
```

## 2. Run the async memory script
```bash
python memory.py
```
Expected output: an aligned block printing the name, email, phone, and nested address.

## 3. DevTools selectors
See `selectors.md` — selectors target `https://demoqa.com/automation-practice-form`
so they're reused directly by Assignment 2's form filler.

