import os
import importlib
import types
import pytest

# Ensure an API key exists so ChatOpenAI constructor doesn't fail on import
os.environ.setdefault("OPENAI_API_KEY", "test-key")

# Import the module under test
from macro_mojo import ai_agent  # noqa: E402

class FakeChain:
    def __init__(self, response_text="FAKE_RESPONSE"):
        self.response_text = response_text
        self.last_invoke_kwargs = None
        self.invoke_called = 0

    def invoke(self, kwargs):
        self.invoke_called += 1
        self.last_invoke_kwargs = kwargs
        return {"text": self.response_text}

@pytest.fixture
def fake_chain(monkeypatch):
    fc = FakeChain("Mocked reply")
    monkeypatch.setattr(ai_agent, "chain", fc)
    return fc

def test_get_ai_response_uses_chain_and_returns_text(fake_chain):
    user_input = "Provide macros for a 30 y/o male 80kg 180cm maintain weight"
    result = ai_agent.get_ai_response(user_input)
    assert result == "Mocked reply"
    assert fake_chain.invoke_called == 1
    assert fake_chain.last_invoke_kwargs == {"input": user_input}

def test_get_ai_response_allows_different_text(monkeypatch):
    fc = FakeChain("Another answer")
    monkeypatch.setattr(ai_agent, "chain", fc)
    assert ai_agent.get_ai_response("Hi") == "Another answer"

def test_get_ai_response_does_not_mutate_input_dict(fake_chain):
    inp = "test question"
    ai_agent.get_ai_response(inp)
    assert "input" in fake_chain.last_invoke_kwargs
    assert list(fake_chain.last_invoke_kwargs.keys()) == ["input"]

def test_get_ai_welcome_message_contains_guidance():
    msg = ai_agent.get_ai_welcome_message()
    assert "Hello" in msg
    assert "calorie" in msg.lower()
    assert "macronutr" in msg.lower()
    assert "weight" in msg.lower()

def test_module_reimport_safe(monkeypatch):
    # Reimport after swapping chain to ensure no side effects break tests
    monkeypatch.setattr(ai_agent, "chain", FakeChain("Reimport safe"))
    importlib.reload(ai_agent)
    # After reload, chain is recreated; patch again to ensure function still works
    monkeypatch.setattr(ai_agent, "chain", FakeChain("After reload"))
    assert ai_agent.get_ai_response("x") == "After reload"
