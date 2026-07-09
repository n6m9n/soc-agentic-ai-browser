"""Corrective RAG (cRAG) over the user's memory.

    retrieve → grade → (correct) generate | (incorrect) corrective → write-back

The *corrective* branch is what makes the assistant feel personal: when the
knowledge base can't answer, it returns a `needs_user` signal so the caller asks
the user once — and `learn()` writes the answer back so it's remembered forever.

The grader/generator default to Gemini but are injectable, so the whole loop is
unit-testable with no API calls (see tests/test_crag.py).
"""
from typing import Callable, Optional, TypedDict

from pydantic import BaseModel

from app.core.schemas import MemoryType


class CragResult(BaseModel):
    status: str            # "found" | "needs_user" | "not_found"
    value: Optional[str] = None
    source: Optional[str] = None      # "memory" | "web"
    question: Optional[str] = None
    docs: list[dict] = []


def _default_llm():
    from app.core.llm import get_chat
    return get_chat(temperature=0)


class CorrectiveRAG:
    def __init__(self, store, llm=None,
                 grader: Optional[Callable[[str, list[dict]], str]] = None,
                 generator: Optional[Callable[[str, list[dict]], str]] = None):
        self.store = store
        self._llm = llm
        self.grader = grader or self._llm_grader
        self.generator = generator or self._llm_generator

    @property
    def llm(self):
        if self._llm is None:
            self._llm = _default_llm()
        return self._llm

    # --- steps ----------------------------------------------------------------
    def retrieve(self, query: str, k: int = 4) -> list[dict]:
        return self.store.query(query, k=k)

    def grade(self, query: str, docs: list[dict]) -> str:
        """Return 'correct' if the docs sufficiently answer the query, else 'incorrect'."""
        if not docs:
            return "incorrect"
        return self.grader(query, docs)

    def resolve(self, query: str, k: int = 4, allow_ask: bool = True) -> CragResult:
        docs = self.retrieve(query, k)
        verdict = self.grade(query, docs)
        if verdict == "correct":
            return CragResult(status="found", value=self.generator(query, docs),
                              source="memory", docs=docs)
        if allow_ask:
            return CragResult(
                status="needs_user", docs=docs,
                question=f"I don't have your {query} yet — please provide it.",
            )
        return CragResult(status="not_found", docs=docs)

    def answer(self, question: str, k: int = 6) -> CragResult:
        """Open-ended Q&A over memory (RAG): retrieve relevant memory and GENERATE
        a grounded answer. Unlike resolve(), this doesn't demand an exact stored
        fact — it reasons over documents (e.g. the uploaded resume). Only asks the
        user when memory is entirely empty.
        """
        docs = self.retrieve(question, k)
        if not docs:
            return CragResult(
                status="needs_user", docs=[],
                question="I don't have anything in memory yet — add details in "
                         "Profile or upload a document, then ask again.",
            )
        context = "\n".join(f"- {d['text']}" for d in docs)
        prompt = (
            "Answer the user's question using ONLY the memory below. Be concise and "
            "specific. If the memory is not enough to answer well, say what's missing.\n\n"
            f"Question: {question}\n\nMemory:\n{context}"
        )
        text = self.llm.invoke(prompt).content.strip()
        return CragResult(status="found", value=text, source="memory", docs=docs)

    def learn(self, query: str, value: str,
              mtype: MemoryType = MemoryType.profile_fact) -> str:
        """Write-back: persist a newly-provided fact so it's remembered forever."""
        text = f"The user's {query} is {value}."
        return self.store.add(text, mtype, metadata={"field": query, "value": value})

    # --- default LLM implementations -----------------------------------------
    # grade + generate are fused into ONE call (the cRAG "knowledge refinement"
    # step) — cheaper and far friendlier to the free-tier rate limit. The result
    # is memoised so grade() and generator() don't each hit the API.
    def _llm_resolve(self, query: str, docs: list[dict]) -> tuple[str, Optional[str]]:
        context = "\n".join(f"- {d['text']}" for d in docs) or "(no memory)"
        prompt = (
            "You answer a query using ONLY the user's stored memory below.\n"
            "If the memory clearly contains the answer, reply with just the value "
            "(no preamble). If it does not, reply with exactly INSUFFICIENT.\n\n"
            f"Query: {query}\n\nMemory:\n{context}"
        )
        out = self.llm.invoke(prompt).content.strip()
        if not out or out.upper().startswith("INSUFFICIENT"):
            return "incorrect", None
        return "correct", out

    def _cached_resolve(self, query: str, docs: list[dict]) -> tuple[str, Optional[str]]:
        key = (query, tuple(d["text"] for d in docs))
        cached = getattr(self, "_cache", None)
        if cached and cached[0] == key:
            return cached[1]
        result = self._llm_resolve(query, docs)
        self._cache = (key, result)
        return result

    def _llm_grader(self, query: str, docs: list[dict]) -> str:
        return self._cached_resolve(query, docs)[0]

    def _llm_generator(self, query: str, docs: list[dict]) -> str:
        return self._cached_resolve(query, docs)[1] or ""


# --- LangGraph subgraph (for agent integration) ------------------------------
class CragState(TypedDict, total=False):
    query: str
    k: int
    docs: list
    verdict: str
    status: str
    value: Optional[str]
    source: Optional[str]
    question: Optional[str]


def build_crag_graph(crag: CorrectiveRAG):
    """Compile the cRAG loop as a LangGraph StateGraph node network."""
    from langgraph.graph import END, START, StateGraph

    def retrieve(state: CragState) -> CragState:
        return {"docs": crag.retrieve(state["query"], state.get("k", 4))}

    def grade(state: CragState) -> CragState:
        return {"verdict": crag.grade(state["query"], state["docs"])}

    def generate(state: CragState) -> CragState:
        return {"status": "found", "source": "memory",
                "value": crag.generator(state["query"], state["docs"])}

    def corrective(state: CragState) -> CragState:
        return {"status": "needs_user",
                "question": f"I don't have your {state['query']} yet — please provide it."}

    def route(state: CragState) -> str:
        return "generate" if state["verdict"] == "correct" else "corrective"

    g = StateGraph(CragState)
    g.add_node("retrieve", retrieve)
    g.add_node("grade", grade)
    g.add_node("generate", generate)
    g.add_node("corrective", corrective)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "grade")
    g.add_conditional_edges("grade", route,
                            {"generate": "generate", "corrective": "corrective"})
    g.add_edge("generate", END)
    g.add_edge("corrective", END)
    return g.compile()


def get_crag() -> CorrectiveRAG:
    from memory.store import get_store
    return CorrectiveRAG(get_store())
