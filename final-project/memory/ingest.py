"""Ingest structured data + documents into the vector memory."""
from pathlib import Path

from app.core.schemas import MemoryType, UserProfile
from memory.records import profile_to_texts


def ingest_profile(store, profile: UserProfile) -> int:
    """Upsert each profile field as a semantic memory record."""
    count = 0
    for text, mtype, metadata, rid in profile_to_texts(profile):
        store.add(text, mtype, metadata=metadata, id=rid)
        count += 1
    return count


def pdf_to_text(path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def uploaded_document_text(store) -> str:
    """Concatenate the most recently uploaded PDF's chunks (in order) from memory."""
    from app.core.schemas import MemoryType
    records = store.all(MemoryType.note)
    chunks = [(r.get("metadata", {}).get("chunk", 0), r["text"])
              for r in records if r.get("metadata", {}).get("source") == "resume"]
    chunks.sort(key=lambda c: c[0])
    return "\n".join(text for _, text in chunks)


def ingest_resume_pdf(store, path: Path, chunk_size: int = 1000) -> int:
    """Parse a resume PDF and store it as chunked memory the agent can retrieve."""
    text = pdf_to_text(path)
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    stored = 0
    for i, chunk in enumerate(chunks):
        if chunk.strip():
            store.add(chunk, MemoryType.note,
                      metadata={"source": "resume", "chunk": i}, id=f"resume:{i}")
            stored += 1
    return stored
