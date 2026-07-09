"""Assignment 4 (bonus) — file-based user profile store.

A tiny query layer over user_profile.json so the agent can look up the user's
name, email, resume path, etc. This is the Assignment-1 "memory layer" grown up.
"""
import json
from pathlib import Path

PROFILE_FILE = Path(__file__).parent / "user_profile.json"


class ProfileStore:
    def __init__(self, path: Path = PROFILE_FILE):
        self.path = path
        self._data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def get(self, field: str) -> str:
        """Return one profile field, or a clear 'not found' message."""
        value = self._data.get(field)
        if value is None:
            available = ", ".join(self._data) or "(empty profile)"
            return f"'{field}' not in profile. Available fields: {available}"
        return str(value)

    def all(self) -> dict:
        return dict(self._data)


if __name__ == "__main__":
    store = ProfileStore()
    print("Profile fields:", store.all())
    print("email ->", store.get("email"))
    print("resume_path ->", store.get("resume_path"))
    print("missing ->", store.get("nope"))
