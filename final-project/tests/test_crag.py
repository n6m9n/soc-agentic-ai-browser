"""Phase 1 — Corrective-RAG tests. No network: a fake store + deterministic
grader/generator. Covers the three behaviours that make cRAG "personal":

  1. hit         — a stored fact is retrieved and returned.
  2. miss->ask   — a missing fact triggers the corrective needs_user branch.
  3. write-back  — after learn(), the same query now hits.
"""
from memory.crag import CorrectiveRAG, build_crag_graph
from app.core.schemas import MemoryType


class FakeStore:
    """In-memory stand-in for the Chroma-backed MemoryStore."""
    def __init__(self):
        self.records: list[dict] = []

    def add(self, text, mtype, metadata=None, id=None):
        self.records.append({"text": text, "metadata": {**(metadata or {}),
                             "type": mtype.value}})
        return id or f"id{len(self.records)}"

    def query(self, query, k=4, mtype=None):
        # naive keyword match on the query token(s)
        q = query.lower()
        hits = [r for r in self.records if any(w in r["text"].lower() for w in q.split())]
        return [{"text": r["text"], "metadata": r["metadata"], "score": 0.9} for r in hits[:k]]


# Deterministic grader/generator (no LLM): relevant if any doc came back.
def grader(query, docs):
    return "correct" if docs else "incorrect"


def generator(query, docs):
    return docs[0]["text"]


def make_crag():
    store = FakeStore()
    store.add("The user's email is anselm@example.com.", MemoryType.profile_fact,
              {"field": "email"})
    return CorrectiveRAG(store, grader=grader, generator=generator)


def test_hit_returns_value():
    crag = make_crag()
    res = crag.resolve("email")
    assert res.status == "found"
    assert "anselm@example.com" in res.value


def test_miss_asks_user():
    crag = make_crag()
    res = crag.resolve("linkedin")
    assert res.status == "needs_user"
    assert "linkedin" in res.question.lower()


def test_write_back_then_hit():
    crag = make_crag()
    assert crag.resolve("linkedin").status == "needs_user"
    crag.learn("linkedin", "https://linkedin.com/in/anselm")
    res = crag.resolve("linkedin")
    assert res.status == "found"
    assert "linkedin.com/in/anselm" in res.value


def test_langgraph_subgraph_runs():
    crag = make_crag()
    graph = build_crag_graph(crag)
    found = graph.invoke({"query": "email", "k": 4})
    assert found["status"] == "found" and "anselm@example.com" in found["value"]
    missing = graph.invoke({"query": "passport", "k": 4})
    assert missing["status"] == "needs_user"
