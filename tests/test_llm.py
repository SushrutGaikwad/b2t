from types import SimpleNamespace

import pytest

from b2t.llm import ConverterLLM, FakeConverter


def test_fake_converter_returns_canned_output():
    fake = FakeConverter("= Typst\n")
    assert fake.convert(latex_source="x", reference="y") == "= Typst\n"


def test_fake_converter_satisfies_protocol():
    fake = FakeConverter()
    assert isinstance(fake, ConverterLLM)


from b2t.config import DEFAULT_MODEL, OPENROUTER_BASE_URL
from b2t.llm import _INSTRUCTIONS, OpenRouterConverter


class _StubClient:
    """Captures constructor kwargs and chat.completions.create calls."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content="= Deck\n")
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


@pytest.fixture
def stub_client(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("B2T_MODEL", raising=False)
    monkeypatch.delenv("B2T_BASE_URL", raising=False)
    monkeypatch.setattr("b2t.llm.OpenAI", _StubClient)


def test_openrouter_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr("b2t.llm.OpenAI", _StubClient)
    with pytest.raises(KeyError, match="OPENROUTER_API_KEY"):
        OpenRouterConverter()


def test_openrouter_sends_system_and_composed_user_message(stub_client):
    conv = OpenRouterConverter()
    out = conv.convert("SRC", "REF", "GUIDE")
    assert out == "= Deck\n"
    (call,) = conv._client.calls
    assert call["model"] == DEFAULT_MODEL
    system, user = call["messages"]
    assert system == {"role": "system", "content": _INSTRUCTIONS}
    assert user["role"] == "user"
    for piece in ("REF", "GUIDE", "SRC"):
        assert piece in user["content"]


def test_openrouter_model_fallback_chain(stub_client, monkeypatch):
    assert OpenRouterConverter()._model == DEFAULT_MODEL
    monkeypatch.setenv("B2T_MODEL", "env/model")
    assert OpenRouterConverter()._model == "env/model"
    assert OpenRouterConverter(model="arg/model")._model == "arg/model"


def test_openrouter_base_url_default_and_override(stub_client, monkeypatch):
    assert OpenRouterConverter()._client.kwargs["base_url"] == OPENROUTER_BASE_URL
    monkeypatch.setenv("B2T_BASE_URL", "http://cluster.example/v1")
    assert (
        OpenRouterConverter()._client.kwargs["base_url"]
        == "http://cluster.example/v1"
    )


def test_openrouter_satisfies_protocol(stub_client):
    assert isinstance(OpenRouterConverter(), ConverterLLM)
