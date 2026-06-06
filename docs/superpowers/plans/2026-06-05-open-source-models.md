# Open-Source Models via OpenRouter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the proprietary OpenAI models with an open-source model catalog served through OpenRouter, with complexity/strength/reasoning shown in the frontend dropdown.

**Architecture:** Minimal in-place swap behind the existing `ConverterLLM` Protocol: a `ModelInfo` catalog in `config.py`, a new `OpenRouterConverter` in `llm.py` using Chat Completions against OpenRouter's OpenAI-compatible endpoint, a richer `/api/models` payload (`{id, label}`), and a matching dropdown. Each task is additive and keeps the suite green; the old OpenAI converter and constants are deleted last.

**Tech Stack:** Python 3.12 via uv, Pydantic v2, `openai` SDK (pointed at OpenRouter), FastAPI, vanilla JS frontend, pytest.

**Spec:** `docs/superpowers/specs/2026-06-05-open-source-models-design.md`

**Conventions:** Run everything with `uv run ...`. Never `python ...` directly. All tests are offline (no network); LLM calls are stubbed.

---

### Task 1: Model catalog in config.py

`config.py` currently exposes `DEFAULT_OPENAI_MODEL` and `OPENAI_MODELS` (plain strings). Add the new catalog alongside them (old constants are removed in Task 5, after all consumers migrate).

**Files:**
- Modify: `src/b2t/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_config.py`:

```python
def test_open_models_default_is_first_and_frontier():
    assert config.DEFAULT_MODEL == config.OPEN_MODELS[0].id
    assert config.OPEN_MODELS[0].strength == "frontier"


def test_open_models_ids_unique_and_namespaced():
    ids = [m.id for m in config.OPEN_MODELS]
    assert len(ids) == len(set(ids))
    assert all("/" in mid for mid in ids)


def test_open_models_have_metadata():
    for m in config.OPEN_MODELS:
        assert m.complexity and m.strength and m.reasoning


def test_model_label_composition():
    assert (
        config.OPEN_MODELS[0].label
        == "gpt-oss-120b - frontier, high reasoning, 120B MoE"
    )


def test_model_label_renders_none_as_no_reasoning():
    llama = next(
        m for m in config.OPEN_MODELS
        if m.id == "meta-llama/llama-3.3-70b-instruct"
    )
    assert llama.label == "llama-3.3-70b-instruct - strong, no reasoning, 70B dense"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_config.py -v`
Expected: the five new tests FAIL with `AttributeError: module 'b2t.config' has no attribute ...`; the four existing tests PASS.

- [ ] **Step 3: Implement the catalog**

In `src/b2t/config.py`, add at the top:

```python
from pydantic import BaseModel
```

Then add after `DEFAULT_OPENAI_MODEL` / `OPENAI_MODELS` (leave those untouched for now):

```python
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class ModelInfo(BaseModel):
    """One open-source model in the conversion catalog."""

    id: str
    complexity: str
    strength: str
    reasoning: str

    @property
    def label(self) -> str:
        """Dropdown label: '<short-name> - <strength>, <reasoning> reasoning, <complexity>'."""
        short = self.id.split("/", 1)[1]
        reasoning = "no" if self.reasoning == "none" else self.reasoning
        return f"{short} - {self.strength}, {reasoning} reasoning, {self.complexity}"


# Open-source families US universities most commonly self-host, strongest
# first. IDs verified against the live OpenRouter API on 2026-06-05.
OPEN_MODELS = (
    ModelInfo(id="openai/gpt-oss-120b", complexity="120B MoE", strength="frontier", reasoning="high"),
    ModelInfo(id="qwen/qwen3-32b", complexity="32B dense", strength="strong", reasoning="hybrid"),
    ModelInfo(id="meta-llama/llama-3.3-70b-instruct", complexity="70B dense", strength="strong", reasoning="none"),
    ModelInfo(id="meta-llama/llama-4-scout", complexity="109B MoE", strength="strong", reasoning="none"),
    ModelInfo(id="google/gemma-4-26b-a4b-it", complexity="26B MoE", strength="capable", reasoning="none"),
    ModelInfo(id="mistralai/mistral-small-2603", complexity="24B dense", strength="capable", reasoning="none"),
    ModelInfo(id="openai/gpt-oss-20b", complexity="21B MoE", strength="capable", reasoning="medium"),
    ModelInfo(id="meta-llama/llama-3.1-8b-instruct", complexity="8B dense", strength="basic", reasoning="none"),
)

DEFAULT_MODEL = OPEN_MODELS[0].id
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_config.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/config.py tests/test_config.py
git commit -m "feat: add open-source model catalog with metadata labels"
```

---

### Task 2: OpenRouterConverter in llm.py

Add `OpenRouterConverter` next to the existing `OpenAIConverter` (which is deleted in Task 5). It uses Chat Completions — the dialect OpenRouter and campus vLLM/Ollama endpoints all speak — instead of the OpenAI-only Responses API.

**Files:**
- Modify: `src/b2t/llm.py`
- Test: `tests/test_llm.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_llm.py` (new imports at the top):

```python
from types import SimpleNamespace

import pytest

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_llm.py -v`
Expected: new tests FAIL with `ImportError: cannot import name 'OpenRouterConverter'`; the two existing tests PASS (if collection fails entirely from the import error, that counts as the failing state).

- [ ] **Step 3: Implement OpenRouterConverter**

In `src/b2t/llm.py`, change the config import line to:

```python
from b2t.config import DEFAULT_MODEL, DEFAULT_OPENAI_MODEL, OPENROUTER_BASE_URL
```

Add after `FakeConverter` (leave `OpenAIConverter` untouched for now):

```python
class OpenRouterConverter:
    """Open-source models via OpenRouter's OpenAI-compatible Chat Completions API.

    B2T_BASE_URL can point the same code at any OpenAI-compatible endpoint,
    e.g. a campus vLLM server.
    """

    def __init__(self, model: str | None = None) -> None:
        self._client = OpenAI(
            base_url=os.getenv("B2T_BASE_URL", OPENROUTER_BASE_URL),
            api_key=os.environ["OPENROUTER_API_KEY"],
        )
        self._model = model or os.getenv("B2T_MODEL", DEFAULT_MODEL)

    def convert(self, latex_source: str, reference: str, guides: str = "") -> str:
        parts = [f"Reference Touying presentation:\n\n{reference}"]
        if guides:
            parts.append(f"Guides:\n\n{guides}")
        parts.append(f"Convert this Beamer source to a Typst Touying deck:\n\n{latex_source}")
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _INSTRUCTIONS},
                {"role": "user", "content": "\n\n".join(parts)},
            ],
        )
        return response.choices[0].message.content
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_llm.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/llm.py tests/test_llm.py
git commit -m "feat: add openrouter converter using chat completions"
```

---

### Task 3: /api/models serves the catalog with labels; dropdown shows them

The endpoint payload changes from `models: list[str]` to `models: list[{id, label}]`. The frontend change ships in the same task so the dropdown never breaks against the new shape.

**Files:**
- Modify: `src/b2t/api/schemas.py`
- Modify: `src/b2t/api/app.py:149-151` (`get_models`) and its config import
- Modify: `src/b2t/api/static/app.js:128-143` (`loadModels`)
- Test: `tests/test_api_app.py:188-194`

- [ ] **Step 1: Replace the models-endpoint test**

In `tests/test_api_app.py`, replace `test_models_endpoint_lists_config_models` (lines 188-194) with:

```python
def test_models_endpoint_lists_open_models_with_labels():
    from b2t.config import DEFAULT_MODEL, OPEN_MODELS

    body = _client().get("/api/models").json()
    assert body["default"] == DEFAULT_MODEL
    assert [m["id"] for m in body["models"]] == [m.id for m in OPEN_MODELS]
    assert [m["label"] for m in body["models"]] == [m.label for m in OPEN_MODELS]
    assert body["default"] in {m["id"] for m in body["models"]}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_app.py::test_models_endpoint_lists_open_models_with_labels -v`
Expected: FAIL (current payload is a list of strings, so `m["id"]` raises `TypeError: string indices must be integers`).

- [ ] **Step 3: Update schemas**

In `src/b2t/api/schemas.py`, replace `ModelsView` with:

```python
class ModelOption(BaseModel):
    id: str
    label: str


class ModelsView(BaseModel):
    models: list[ModelOption]
    default: str
```

- [ ] **Step 4: Update the endpoint**

In `src/b2t/api/app.py`, change the config import to:

```python
from b2t.config import DEFAULT_MODEL, OPEN_MODELS, REPO_ROOT
```

Add `ModelOption` to the `b2t.api.schemas` import list, then replace the `get_models` body:

```python
    @app.get("/api/models", response_model=ModelsView)
    def get_models():
        return ModelsView(
            models=[ModelOption(id=m.id, label=m.label) for m in OPEN_MODELS],
            default=DEFAULT_MODEL,
        )
```

- [ ] **Step 5: Update the dropdown builder**

In `src/b2t/api/static/app.js`, in `loadModels()`, replace the option-building loop:

```js
    for (const m of data.models) {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.textContent = m.id === data.default ? `${m.label} (default)` : m.label;
      sel.appendChild(opt);
    }
```

- [ ] **Step 6: Run the full suite**

Run: `uv run pytest -q`
Expected: all PASS (the new endpoint test, plus everything else still green).

- [ ] **Step 7: Commit**

```bash
git add src/b2t/api/schemas.py src/b2t/api/app.py src/b2t/api/static/app.js tests/test_api_app.py
git commit -m "feat: serve model catalog with metadata labels in the dropdown"
```

---

### Task 4: Switch the converter consumers to OpenRouter

`convert_deck` and the API's `_make_converter` construct `OpenRouterConverter` instead of `OpenAIConverter`.

**Files:**
- Modify: `src/b2t/app.py:7,17`
- Modify: `src/b2t/api/app.py:23,33-36` (`_make_converter` and the llm import)
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_api_app.py`:

```python
def test_make_converter_picks_fake_or_openrouter(monkeypatch):
    from b2t.api.app import _make_converter
    from b2t.llm import FakeConverter, OpenRouterConverter

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    assert isinstance(_make_converter(True, ""), FakeConverter)
    real = _make_converter(False, "qwen/qwen3-32b")
    assert isinstance(real, OpenRouterConverter)
    assert real._model == "qwen/qwen3-32b"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_app.py::test_make_converter_picks_fake_or_openrouter -v`
Expected: FAIL. Either `AssertionError` (an `OpenAIConverter` came back, not an
`OpenRouterConverter`) or `openai.OpenAIError` about a missing OpenAI api key,
depending on whether a `.env` with `OPENAI_API_KEY` was loaded. Both prove the
old converter is still wired in.

- [ ] **Step 3: Switch both consumers**

In `src/b2t/api/app.py`, change the llm import to:

```python
from b2t.llm import ConverterLLM, FakeConverter, OpenRouterConverter
```

and `_make_converter` to:

```python
def _make_converter(use_fake: bool, model: str) -> ConverterLLM:
    if use_fake:
        return FakeConverter(FAKE_TYPST)
    return OpenRouterConverter(model=model or None)
```

In `src/b2t/app.py`, change the llm import to:

```python
from b2t.llm import ConverterLLM, OpenRouterConverter
```

and the converter line in `convert_deck` to:

```python
    converter = llm or OpenRouterConverter()
```

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q`
Expected: all PASS. (Pipeline tests pass `FakeConverter` explicitly, so nothing constructs the real converter without the env var.)

- [ ] **Step 5: Commit**

```bash
git add src/b2t/app.py src/b2t/api/app.py tests/test_api_app.py
git commit -m "feat: convert decks with openrouter instead of openai"
```

---

### Task 5: Remove the OpenAI converter and constants; update README

All consumers are migrated; delete the dead code and fix the docs.

**Files:**
- Modify: `src/b2t/llm.py` (delete `OpenAIConverter`)
- Modify: `src/b2t/config.py` (delete `DEFAULT_OPENAI_MODEL`, `OPENAI_MODELS`)
- Modify: `tests/test_config.py` (delete the old models test)
- Modify: `README.md:76-78,90-96,126-127`

- [ ] **Step 1: Delete the old test**

In `tests/test_config.py`, delete `test_openai_models_includes_default_first` (lines 17-19).

- [ ] **Step 2: Delete the dead code**

- In `src/b2t/llm.py`: delete the whole `OpenAIConverter` class and remove `DEFAULT_OPENAI_MODEL` from the config import (keep `DEFAULT_MODEL` and `OPENROUTER_BASE_URL`).
- In `src/b2t/config.py`: delete `DEFAULT_OPENAI_MODEL = "gpt-5.4-nano"` and the whole `OPENAI_MODELS` tuple.

- [ ] **Step 3: Verify nothing references the deleted names**

Run: `grep -rn "OpenAIConverter\|OPENAI_MODELS\|DEFAULT_OPENAI_MODEL\|OPENAI_MODEL" src tests README.md`
Expected: no matches (README is fixed next; if it matches now, that is the next step's work — only src and tests must be clean here).

- [ ] **Step 4: Update README**

In `README.md`:

Replace the requirements bullet (lines 76-78) with:

```markdown
- An OpenRouter API key, for real conversions. The pipeline runs offline with
  the fake converter (tests and the UI checkbox), but actual Beamer to Typst
  translation calls open-source models via OpenRouter.
```

Replace the `.env` block and the model-override line (lines 90-96) with:

````markdown
Create a `.env` file in the repo root:

```
OPENROUTER_API_KEY=sk-or-...
```

Optionally add `B2T_MODEL=...` to override the default model
(`openai/gpt-oss-120b`), or `B2T_BASE_URL=...` to point at any
OpenAI-compatible endpoint (for example a campus vLLM server).
````

In the testing-UI section (lines 126-127), change "without calling OpenAI" to "without calling OpenRouter".

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -q`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/b2t/llm.py src/b2t/config.py tests/test_config.py README.md
git commit -m "refactor: drop the openai converter and model list"
```

---

### Task 6: End-to-end verification

- [ ] **Step 1: Full suite**

Run: `uv run pytest -q`
Expected: all PASS (63 before this work; more now).

- [ ] **Step 2: Offline UI smoke test**

Run: `uv run uvicorn b2t.api.app:app` then open http://127.0.0.1:8000.
Expected: the model dropdown lists eight labelled entries, e.g.
`gpt-oss-120b - frontier, high reasoning, 120B MoE (default)`; "Use sample deck" with "use fake converter" ticked completes as before.

- [ ] **Step 3: One real conversion (uses the OpenRouter key; costs a fraction of a cent)**

Run: `uv run python -c "from b2t.app import convert_deck; convert_deck('tests/fixtures/sample_deck', 'out_or')"`
Expected: log line `compiled out_or\main.pdf` (or a compile error recorded in state, which v0 does not retry — that is existing behavior, not a regression).
