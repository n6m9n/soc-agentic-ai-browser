"""Assignment 3 — exercise parse_intent() across 10 varied commands.

Setup:
    pip install -r requirements.txt
    export GOOGLE_API_KEY=AIza...      # free key: https://aistudio.google.com/apikey
    python test_commands.py
"""
import json
import os
import sys

from dotenv import load_dotenv
from google import genai

from intent_parser import parse_intent

load_dotenv()  # reads GOOGLE_API_KEY from a .env file (git-ignored)

COMMANDS = [
    "apply to this job",                                  # ambiguous -> clarify
    "close all tabs",                                     # click/navigate-ish
    "email this summary to my boss",                      # ambiguous email -> clarify
    "go to google.com and search for AI news",           # navigate
    "fill out the contact form on acme.com with my info", # fill_form
    "summarize the article currently open",               # summarize
    "click the 'Sign in' button",                         # click
    "navigate to my github notifications",                # navigate
    "book a flight",                                      # ambiguous -> clarify
    "fill the demoqa practice form and screenshot it",    # fill_form
]


def main() -> None:
    if not os.getenv("GOOGLE_API_KEY"):
        sys.exit("set GOOGLE_API_KEY first (free key: https://aistudio.google.com/apikey)")
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    for i, cmd in enumerate(COMMANDS, 1):
        result = parse_intent(cmd, client=client)
        flag = "  ❓ clarify" if result.get("needs_clarification") else ""
        print(f"\n[{i:2}] {cmd!r}{flag}")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
