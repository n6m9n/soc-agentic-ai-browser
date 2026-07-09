"""Helpers to turn structured data into memory records for the vector store."""
from app.core.schemas import MemoryType, UserProfile


def profile_to_texts(profile: UserProfile) -> list[tuple[str, MemoryType, dict, str]]:
    """Flatten a profile into (text, type, metadata, stable_id) tuples.

    Stable ids (e.g. "profile:email") let re-ingesting a profile UPDATE the same
    record instead of duplicating it.
    """
    fields = {
        "name": profile.name, "email": profile.email, "phone": profile.phone,
        "college": profile.college, "degree": profile.degree,
        "grad_year": profile.grad_year, "city": profile.city,
        "linkedin": profile.linkedin, "resume_path": profile.resume_path or "",
    }
    out = []
    for key, value in fields.items():
        if not value:
            continue
        text = f"The user's {key.replace('_', ' ')} is {value}."
        out.append((text, MemoryType.profile_fact, {"field": key, "value": value}, f"profile:{key}"))
    return out
