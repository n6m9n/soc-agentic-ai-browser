"""ChromaDB vector store wrapped with Gemini embeddings.

Heavy imports (chromadb / langchain) are deferred to __init__ so this module can
be imported in unit tests that inject a fake store instead.
"""
import uuid
from functools import lru_cache
from typing import Optional

from app.core.config import CHROMA_DIR
from app.core.schemas import MemoryType


class MemoryStore:
    def __init__(self, embeddings=None, persist_directory=None, collection_name="memory"):
        from langchain_chroma import Chroma
        if embeddings is None:
            from app.core.llm import get_embeddings
            embeddings = get_embeddings()
        self.vs = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(persist_directory or CHROMA_DIR),
        )

    def add(self, text: str, mtype: MemoryType, metadata: Optional[dict] = None,
            id: Optional[str] = None) -> str:
        rid = id or uuid.uuid4().hex
        md = {"type": mtype.value, **(metadata or {})}
        self.vs.add_texts([text], metadatas=[md], ids=[rid])
        return rid

    def query(self, query: str, k: int = 4, mtype: Optional[MemoryType] = None) -> list[dict]:
        flt = {"type": mtype.value} if mtype else None
        pairs = self.vs.similarity_search_with_relevance_scores(query, k=k, filter=flt)
        return [{"text": d.page_content, "metadata": d.metadata, "score": s} for d, s in pairs]

    def all(self, mtype: Optional[MemoryType] = None) -> list[dict]:
        where = {"type": mtype.value} if mtype else None
        got = self.vs.get(where=where)
        return [
            {"text": t, "metadata": m}
            for t, m in zip(got.get("documents", []), got.get("metadatas", []))
        ]


@lru_cache(maxsize=1)
def get_store() -> MemoryStore:
    """Process-wide singleton (real Chroma + Gemini embeddings)."""
    return MemoryStore()
