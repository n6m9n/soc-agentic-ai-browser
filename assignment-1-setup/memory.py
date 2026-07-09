"""Assignment 1 — async "memory" layer.

Reads a JSON file of user info (name, email, phone, address) and prints it
nicely. This module is the seed of the user-profile/memory layer that the final
browser agent (Assignment 4) will query for autofill data.

Run:  python memory.py            # uses ./user_info.json
      python memory.py other.json
"""
import asyncio
import json
import sys
from pathlib import Path


async def load_user_info(path: Path) -> dict:
    """Asynchronously read and parse the user-info JSON file.

    File I/O is blocking, so it's pushed to a thread via asyncio.to_thread to
    keep the event loop free — the same pattern the agent will use later when
    reading the profile alongside live browser calls.
    """
    raw = await asyncio.to_thread(path.read_text, encoding="utf-8")
    return json.loads(raw)


def format_user_info(info: dict) -> str:
    """Render the profile as an aligned, human-readable block."""
    lines = ["", "=" * 44, "  USER MEMORY", "=" * 44]
    for key, value in info.items():
        label = key.replace("_", " ").title()
        if isinstance(value, dict):
            lines.append(f"  {label}:")
            for sub_key, sub_value in value.items():
                sub_label = sub_key.replace("_", " ").title()
                lines.append(f"      {sub_label:<10} {sub_value}")
        else:
            lines.append(f"  {label:<14} {value}")
    lines.append("=" * 44)
    return "\n".join(lines)


async def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "user_info.json"
    if not path.exists():
        sys.exit(f"error: file not found: {path}")
    info = await load_user_info(path)
    print(format_user_info(info))


if __name__ == "__main__":
    asyncio.run(main())
