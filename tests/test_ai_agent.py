from dotenv import load_dotenv
from macro_mojo import ai_agent
import pytest

load_dotenv()


class FakeChain:
    def __init__(self, response_text="FAKE_RESPONSE"):
        # Allows assign expected output of the chain
        self.response_text = response_text
        self.last_invoke_kwargs = None
        self.invoke_called = 0

    def invoke(self, kwargs):
        self.invoke_called += 1
        self.last_invoke_kwargs = kwargs
        return {"text": self.response_text}


"""
Create fresh FakeChain instance and patch a chain for each test
"""


@pytest.fixture
def fake_chain(monkeypatch: pytest.MonkeyPatch):
    fake_chain = FakeChain("Mocked reply")
    monkeypatch.setattr("macro_mojo.ai_agent.chain", fake_chain)
    return fake_chain


"""
Tests for function 'get_ai_response':
1. Use fake chain and return an answer
2. Check that can get a different response
"""


def test_get_ai_response_uses_chain_gets_response(fake_chain):
    user_input = """I'm 30 years old female, 150 lbs, 170 cm height, want to
                    gain muscle while maintaining weight."""
    result = ai_agent.get_ai_response(user_input)
    assert result == "Mocked reply"
    assert fake_chain.invoke_called == 1
    assert fake_chain.last_invoke_kwargs == {"input": user_input}


def test_get_ai_response_gets_another_response(monkeypatch):
    fake_chain = FakeChain(response_text="Please provide more details")
    monkeypatch.setattr("macro_mojo.ai_agent.chain", fake_chain)
    user_input = "I am 45 and want to lose weight"
    result = ai_agent.get_ai_response(user_input)
    assert result == "Please provide more details"


"""
Test welcome message
"""


def test_get_ai_welcome_message():
    message = ai_agent.get_ai_welcome_message()
    assert "Hello" in message
    assert "Weight" in message
    assert "Activity level" in message
