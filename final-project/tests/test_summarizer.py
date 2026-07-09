"""Phase 3 — Summarisation tests. HTML extraction is real; the LLM is mocked."""
from app.core.schemas import JDAnalysis, Summary
from modules.summarizer import (analyze_jd, extract_text_from_html, summarize_text)


class _FakeStructured:
    def __init__(self, obj):
        self.obj = obj

    def invoke(self, prompt):
        return self.obj


class FakeLLM:
    """Mocks ChatGoogleGenerativeAI's with_structured_output / invoke surface."""
    def __init__(self, structured_obj=None, text="| a | b |"):
        self._obj = structured_obj
        self._text = text

    def with_structured_output(self, schema):
        return _FakeStructured(self._obj)

    def invoke(self, prompt):
        return type("R", (), {"content": self._text})()


def test_html_extraction_strips_scripts():
    html = """<html><head><style>.x{}</style></head><body>
      <h1>Hello</h1><script>var x=1;</script><p>World of agents</p></body></html>"""
    text = extract_text_from_html(html)
    assert "Hello" in text and "World of agents" in text
    assert "var x" not in text and ".x{}" not in text


def test_summarize_structured_output():
    summary = Summary(tldr="A short summary.",
                      key_points=["k1", "k2", "k3", "k4", "k5"],
                      action_items=["do x"], tags=["ai", "agents"], sentiment="positive")
    result = summarize_text("some long article text", llm=FakeLLM(summary))
    assert isinstance(result, Summary)
    assert result.tldr == "A short summary."
    assert len(result.key_points) == 5
    assert result.sentiment == "positive"


def test_jd_analysis():
    jd = JDAnalysis(required_skills=["Python", "Playwright"],
                    nice_to_haves=["LangChain"], highlight=["agent projects"])
    result = analyze_jd("We need a Python engineer...", llm=FakeLLM(jd))
    assert "Python" in result.required_skills
    assert "LangChain" in result.nice_to_haves
