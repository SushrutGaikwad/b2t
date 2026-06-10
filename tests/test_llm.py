from types import SimpleNamespace

import pytest

from b2t.config import DEFAULT_MODEL, OPENROUTER_BASE_URL
from b2t.llm import FakeClient, LLMClient, OpenRouterClient


def test_fake_client_returns_canned_output():
    assert FakeClient("= Typst\n").complete("sys", "user", "model") == "= Typst\n"


def test_fake_client_satisfies_protocol():
    assert isinstance(FakeClient(), LLMClient)


class _StubClient:
    """Captures constructor kwargs and chat.completions.create calls."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content="= Deck\n")
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


@pytest.fixture
def stub_client(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("B2T_BASE_URL", raising=False)
    monkeypatch.setattr("b2t.llm.OpenAI", _StubClient)


def test_openrouter_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr("b2t.llm.OpenAI", _StubClient)
    with pytest.raises(KeyError, match="OPENROUTER_API_KEY"):
        OpenRouterClient()


def test_openrouter_complete_sends_system_user_and_model(stub_client):
    client = OpenRouterClient()
    out = client.complete("SYS", "USER", "some/model")
    assert out == "= Deck\n"
    (call,) = client._client.calls
    assert call["model"] == "some/model"
    system, user = call["messages"]
    assert system == {"role": "system", "content": "SYS"}
    assert user == {"role": "user", "content": "USER"}


def test_openrouter_base_url_default_and_override(stub_client, monkeypatch):
    assert OpenRouterClient()._client.kwargs["base_url"] == OPENROUTER_BASE_URL
    monkeypatch.setenv("B2T_BASE_URL", "http://cluster.example/v1")
    assert OpenRouterClient()._client.kwargs["base_url"] == "http://cluster.example/v1"


def test_openrouter_satisfies_protocol(stub_client):
    assert isinstance(OpenRouterClient(), LLMClient)
