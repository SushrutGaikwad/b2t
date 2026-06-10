# Prompt Versioning and Per-Node LLM Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every LLM node versioned prompts stored as repo TOML files, and let the testing UI pick a model and a prompt version per node before running any Beamer deck.

**Architecture:** Generalize the single task-specific converter into a generic `LLMClient.complete(system, user, model)` seam. A filesystem prompt registry loads versioned `prompts/<node>/<version>.toml` files. A per-node selection (`llm_choices`) flows through `PipelineState`; a shared `run_prompt` helper resolves the selection, renders the chosen template, calls the client, and records provenance (`llm_runs`). The convert node is migrated onto this; the API and UI expose per-node model and version pickers.

**Tech Stack:** Python 3.12, LangGraph, Pydantic v2, FastAPI, stdlib `tomllib` and `json`, loguru, pytest. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-06-10-prompt-versioning-design.md`

---

## File Structure

New files:

- `src/b2t/prompts.py` - the prompt registry: `render()`, `PromptVersion`, `list_nodes()`, `list_versions()`, `default_version()`, `load()`.
- `src/b2t/nodes/_llm.py` - the shared `run_prompt()` helper every LLM node calls.
- `prompts/defaults.json` - per-node default version: `{ "convert": "v1" }`.
- `prompts/convert/v1.toml` - the migrated convert prompt (system + user_template).
- `tests/test_prompts.py` - registry and rendering tests.
- `tests/test_llm_node.py` - `run_prompt` helper tests.

Modified files:

- `src/b2t/config.py` - add `PROMPTS_DIR`.
- `src/b2t/state.py` - add `NodeChoice`, `NodeRun`, and the `llm_choices` / `llm_runs` fields.
- `src/b2t/llm.py` - replace `ConverterLLM`/`FakeConverter`/`OpenRouterConverter` with `LLMClient`/`FakeClient`/`OpenRouterClient`; method becomes `complete(system, user, model)`; remove `_INSTRUCTIONS`.
- `src/b2t/nodes/convert.py` - call `run_prompt`; take `client` instead of `llm`.
- `src/b2t/graph.py` - `build_graph(client)`; bind `client` into the convert node.
- `src/b2t/app.py` - `convert_deck(..., client=None, llm_choices=None)`.
- `src/b2t/api/jobs.py` - `run_job` takes a client factory plus a `choices` dict; `JobRecord` gains `llm_runs`.
- `src/b2t/api/schemas.py` - `JobView.llm_runs`; new `NodeRunView`, `VersionOption`, `LLMNodeView`, `LLMNodesView`.
- `src/b2t/api/app.py` - `_make_client`; `/api/llm-nodes`; per-node `choices` field with validation.
- `src/b2t/api/static/index.html`, `app.js`, `style.css` - per-node model and version pickers; provenance display.
- Tests: `test_llm.py`, `test_nodes.py`, `test_graph.py`, `test_state.py`, `test_api_jobs.py`, `test_api_schemas.py`, `test_api_app.py`.

---

## Task 1: Template rendering

The renderer replaces `{{token}}` markers and refuses unknown ones. It must never touch LaTeX/Typst braces or `$`, and must not re-scan injected values.

**Files:**
- Create: `src/b2t/prompts.py`
- Test: `tests/test_prompts.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_prompts.py`:

```python
import pytest

from b2t.prompts import render


def test_render_replaces_known_tokens():
    assert render("a {{x}} b {{y}}", {"x": "1", "y": "2"}) == "a 1 b 2"


def test_render_preserves_latex_and_typst_syntax():
    template = "Keep $E=mc^2$ and \\frac{a}{b}, then {{source}}."
    assert render(template, {"source": "X"}) == "Keep $E=mc^2$ and \\frac{a}{b}, then X."


def test_render_raises_on_unknown_token():
    with pytest.raises(KeyError, match="typo"):
        render("hello {{typo}}", {"source": "X"})


def test_render_does_not_rescan_injected_values():
    # an injected value that itself looks like a token is left as-is
    assert render("{{source}}", {"source": "{{reference}}"}) == "{{reference}}"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_prompts.py -v`
Expected: FAIL (ModuleNotFoundError: no module named `b2t.prompts`).

- [ ] **Step 3: Write the minimal implementation**

Create `src/b2t/prompts.py`:

```python
"""Prompt registry: versioned prompt files plus token rendering."""

import re

_TOKEN_RE = re.compile(r"\{\{(\w+)\}\}")


def render(template: str, values: dict[str, str]) -> str:
    """Replace each {{token}} in template with values[token].

    Only the template is scanned; injected values are inserted verbatim and are
    never re-scanned, so LaTeX/Typst braces and dollar signs are untouched.

    Args:
        template: A user-message template containing {{token}} markers.
        values: Mapping of token name to replacement text.

    Returns:
        The rendered string.

    Raises:
        KeyError: If the template contains a {{token}} not present in values
            (catches typos early).
    """

    def repl(match: re.Match) -> str:
        key = match.group(1)
        if key not in values:
            raise KeyError(f"unknown template token: {{{{{key}}}}}")
        return values[key]

    return _TOKEN_RE.sub(repl, template)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_prompts.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/prompts.py tests/test_prompts.py
git commit -m "feat: add prompt template renderer"
```

---

## Task 2: Prompt registry loader

Discover nodes and versions from disk, resolve the default from `defaults.json`, and load a version as a `PromptVersion`. All functions take an optional `base` so tests use a fixture directory.

**Files:**
- Modify: `src/b2t/config.py` (add `PROMPTS_DIR`)
- Modify: `src/b2t/prompts.py`
- Test: `tests/test_prompts.py`

- [ ] **Step 1: Add `PROMPTS_DIR` to config**

In `src/b2t/config.py`, below the existing `MATH_GUIDE` line, add:

```python
PROMPTS_DIR = REPO_ROOT / "prompts"
```

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_prompts.py`:

```python
import json
from pathlib import Path

from b2t.prompts import PromptVersion, default_version, list_nodes, list_versions, load


def _make_registry(base: Path) -> None:
    (base / "convert").mkdir(parents=True)
    (base / "convert" / "v1.toml").write_text(
        'description = "first"\n'
        "system = '''Sys one'''\n"
        "user_template = '''U {{source}}'''\n",
        encoding="utf-8",
    )
    (base / "convert" / "v2.toml").write_text(
        "system = '''Sys two'''\n"
        "user_template = '''U2 {{source}}'''\n",
        encoding="utf-8",
    )
    (base / "defaults.json").write_text(json.dumps({"convert": "v1"}), encoding="utf-8")


def test_list_nodes_and_versions(tmp_path):
    _make_registry(tmp_path)
    assert list_nodes(base=tmp_path) == ["convert"]
    assert list_versions("convert", base=tmp_path) == ["v1", "v2"]


def test_default_version(tmp_path):
    _make_registry(tmp_path)
    assert default_version("convert", base=tmp_path) == "v1"


def test_load_returns_prompt_version(tmp_path):
    _make_registry(tmp_path)
    pv = load("convert", "v1", base=tmp_path)
    assert isinstance(pv, PromptVersion)
    assert pv.system == "Sys one"
    assert pv.user_template == "U {{source}}"
    assert pv.description == "first"


def test_load_missing_description_defaults_empty(tmp_path):
    _make_registry(tmp_path)
    assert load("convert", "v2", base=tmp_path).description == ""


def test_load_missing_version_raises(tmp_path):
    _make_registry(tmp_path)
    with pytest.raises(FileNotFoundError):
        load("convert", "v9", base=tmp_path)


def test_default_version_unknown_node_raises(tmp_path):
    _make_registry(tmp_path)
    with pytest.raises(KeyError):
        default_version("nope", base=tmp_path)
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_prompts.py -v`
Expected: FAIL (ImportError: cannot import name `PromptVersion`).

- [ ] **Step 4: Write the minimal implementation**

In `src/b2t/prompts.py`, update the imports at the top and append the registry code:

```python
"""Prompt registry: versioned prompt files plus token rendering."""

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from b2t.config import PROMPTS_DIR

_TOKEN_RE = re.compile(r"\{\{(\w+)\}\}")
```

(Keep the existing `render` function as-is, then add below it:)

```python
@dataclass
class PromptVersion:
    """One versioned prompt for a node.

    Attributes:
        node: The LLM node this prompt belongs to (e.g. "convert").
        version: The version id (the .toml filename stem, e.g. "v1").
        system: The system instruction.
        user_template: The user-message template with {{tokens}}.
        description: Optional human label for the version dropdown.
    """

    node: str
    version: str
    system: str
    user_template: str
    description: str = ""


def _defaults(base: Path) -> dict:
    """Return the parsed defaults.json mapping node -> default version."""
    return json.loads((base / "defaults.json").read_text(encoding="utf-8"))


def list_nodes(base: Path = PROMPTS_DIR) -> list[str]:
    """Return node names: subdirectories holding at least one *.toml version."""
    return sorted(
        p.name for p in base.iterdir() if p.is_dir() and any(p.glob("*.toml"))
    )


def list_versions(node: str, base: Path = PROMPTS_DIR) -> list[str]:
    """Return the sorted version ids (.toml stems) for a node."""
    return sorted(p.stem for p in (base / node).glob("*.toml"))


def default_version(node: str, base: Path = PROMPTS_DIR) -> str:
    """Return the default version id for a node.

    Raises:
        KeyError: If the node is absent from defaults.json (fail loud).
    """
    return _defaults(base)[node]


def load(node: str, version: str, base: Path = PROMPTS_DIR) -> PromptVersion:
    """Parse one version file into a PromptVersion.

    Raises:
        FileNotFoundError: If the version file is missing.
        KeyError: If `system` or `user_template` is absent from the file.
    """
    data = tomllib.loads(
        (base / node / f"{version}.toml").read_text(encoding="utf-8")
    )
    return PromptVersion(
        node=node,
        version=version,
        system=data["system"],
        user_template=data["user_template"],
        description=data.get("description", ""),
    )
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_prompts.py -v`
Expected: PASS (10 passed).

- [ ] **Step 6: Commit**

```bash
git add src/b2t/config.py src/b2t/prompts.py tests/test_prompts.py
git commit -m "feat: add filesystem prompt registry loader"
```

---

## Task 3: Migrate the existing convert prompt to the registry

Move today's hard-coded prompt into `prompts/convert/v1.toml` and point `defaults.json` at it. The text is identical, so default runs behave the same.

**Files:**
- Create: `prompts/defaults.json`
- Create: `prompts/convert/v1.toml`
- Test: `tests/test_prompts.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_prompts.py`:

```python
from b2t import prompts as P


def test_real_convert_v1_is_default_and_loadable():
    assert P.default_version("convert") == "v1"
    pv = P.load("convert", "v1")
    assert "Typst Touying" in pv.system
    assert "Never use overlays" in pv.system
    for token in ("{{reference}}", "{{guides}}", "{{source}}"):
        assert token in pv.user_template
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_prompts.py::test_real_convert_v1_is_default_and_loadable -v`
Expected: FAIL (FileNotFoundError: no `prompts/defaults.json`).

- [ ] **Step 3: Create the prompt files**

Create `prompts/defaults.json`:

```json
{
  "convert": "v1"
}
```

Create `prompts/convert/v1.toml` (note: `system` is one line so it matches the
current `_INSTRUCTIONS` text verbatim; literal `'''` strings need no escaping):

```toml
description = "initial convert prompt, migrated from llm._INSTRUCTIONS"

system = '''You convert LaTeX Beamer source into a Typst Touying presentation using the university theme. Use the provided reference presentation as the canonical structure and preamble. Follow the provided guides, especially for writing math equations in Typst syntax. Output only Typst source, with no commentary. Never use overlays or pause functionality.'''

user_template = '''
Reference Touying presentation:

{{reference}}

Guides:

{{guides}}

Convert this Beamer source to a Typst Touying deck:

{{source}}
'''
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_prompts.py::test_real_convert_v1_is_default_and_loadable -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add prompts/defaults.json prompts/convert/v1.toml tests/test_prompts.py
git commit -m "feat: migrate convert prompt into the registry as v1"
```

---

## Task 4: Add per-node selection and provenance to state

Two small Pydantic submodels and two new fields. They default empty, so nothing else breaks yet.

**Files:**
- Modify: `src/b2t/state.py`
- Test: `tests/test_state.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_state.py`:

```python
def test_llm_choices_and_runs_default_empty():
    state = PipelineState(input_dir=Path("in"), output_dir=Path("out"))
    assert state.llm_choices == {}
    assert state.llm_runs == {}


def test_llm_choices_coerce_nested_dicts():
    state = PipelineState(
        input_dir=Path("in"),
        output_dir=Path("out"),
        llm_choices={"convert": {"model": "m", "prompt_version": "v2"}},
    )
    assert state.llm_choices["convert"].model == "m"
    assert state.llm_choices["convert"].prompt_version == "v2"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_state.py -v`
Expected: FAIL (AttributeError / ValidationError: no `llm_choices`).

- [ ] **Step 3: Write the minimal implementation**

In `src/b2t/state.py`, add the two submodels above `class PipelineState` and the two fields inside it. The top of the file becomes:

```python
from pathlib import Path

from pydantic import BaseModel, Field


class NodeChoice(BaseModel):
    """A per-node UI selection. None means use the default."""

    model: str | None = None
    prompt_version: str | None = None


class NodeRun(BaseModel):
    """What an LLM node actually used, recorded for provenance."""

    model: str
    prompt_version: str
```

Then inside `PipelineState`, after the `stripped_tex` field and before the
conversion section, add:

```python
    # per-node model + prompt-version selection (seeded at start) and the
    # provenance of what actually ran
    llm_choices: dict[str, NodeChoice] = Field(default_factory=dict)
    llm_runs: dict[str, NodeRun] = Field(default_factory=dict)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_state.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/state.py tests/test_state.py
git commit -m "feat: add llm_choices and llm_runs to pipeline state"
```

---

## Task 5: Cut over to the generic LLM client and prompt-driven convert node

This is one atomic change: renaming the converter seam to `complete(system, user, model)` breaks every importer, so `llm.py`, the convert node, the graph, the app, the API, and all their tests change together. Make every edit, then run the whole suite once. The API keeps its existing global `model` field for now (translated into `llm_choices`); per-node selection arrives in Task 8.

**Files:**
- Create: `src/b2t/nodes/_llm.py`
- Modify: `src/b2t/llm.py`, `src/b2t/nodes/convert.py`, `src/b2t/graph.py`, `src/b2t/app.py`, `src/b2t/api/jobs.py`, `src/b2t/api/app.py`
- Test: `tests/test_llm.py`, `tests/test_llm_node.py` (new), `tests/test_nodes.py`, `tests/test_graph.py`, `tests/test_api_jobs.py`, `tests/test_api_app.py`

- [ ] **Step 1: Rewrite `tests/test_llm.py` for the new seam**

Replace the entire contents of `tests/test_llm.py` with:

```python
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
```

- [ ] **Step 2: Rewrite `src/b2t/llm.py`**

Replace the entire contents of `src/b2t/llm.py` with:

```python
import os
from typing import Protocol, runtime_checkable

from loguru import logger
from openai import OpenAI

from b2t.config import OPENROUTER_BASE_URL


@runtime_checkable
class LLMClient(Protocol):
    """Interface every model client implements; keeps LLM calls mockable."""

    def complete(self, system: str, user: str, model: str) -> str:
        """Run one completion.

        Args:
            system: The system instruction.
            user: The fully rendered user message.
            model: The model id to call.

        Returns:
            The model's text output.
        """
        ...


class FakeClient:
    """Deterministic client for tests and offline runs; never touches the network."""

    def __init__(self, output: str = "= Placeholder\n") -> None:
        """Store the canned output to return from every complete call."""
        self._output = output

    def complete(self, system: str, user: str, model: str) -> str:
        """Return the canned output, ignoring all inputs."""
        return self._output


class OpenRouterClient:
    """Open-source models via OpenRouter's OpenAI-compatible Chat Completions API.

    B2T_BASE_URL can point the same code at any OpenAI-compatible endpoint,
    e.g. a campus vLLM server. The model is chosen per call.
    """

    def __init__(self) -> None:
        """Create the client.

        Raises:
            KeyError: If OPENROUTER_API_KEY is not set in the environment.
        """
        self._client = OpenAI(
            base_url=os.getenv("B2T_BASE_URL", OPENROUTER_BASE_URL),
            api_key=os.environ["OPENROUTER_API_KEY"],
        )

    def complete(self, system: str, user: str, model: str) -> str:
        """Send one Chat Completions request.

        Args:
            system: The system instruction.
            user: The fully rendered user message.
            model: The model id to call.

        Returns:
            The model's text output. Network and provider errors propagate to
            the caller's failure boundary.
        """
        logger.info("calling {} via chat completions", model)
        response = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content
```

- [ ] **Step 3: Write the `run_prompt` helper tests**

Create `tests/test_llm_node.py`:

```python
from pathlib import Path

from b2t.config import DEFAULT_MODEL
from b2t.llm import FakeClient
from b2t.nodes._llm import run_prompt
from b2t.state import NodeChoice, NodeRun, PipelineState


def _state(**kwargs) -> PipelineState:
    base = {"input_dir": Path("in"), "output_dir": Path("out")}
    base.update(kwargs)
    return PipelineState(**base)


_VALUES = {"reference": "R", "guides": "G", "source": "SRC"}


def test_run_prompt_uses_defaults_and_returns_run(monkeypatch):
    monkeypatch.delenv("B2T_MODEL", raising=False)
    out, run = run_prompt(_state(), "convert", FakeClient("OUT"), _VALUES)
    assert out == "OUT"
    assert run == NodeRun(model=DEFAULT_MODEL, prompt_version="v1")


def test_run_prompt_honors_choice_model_and_renders_user(monkeypatch):
    monkeypatch.delenv("B2T_MODEL", raising=False)
    state = _state(llm_choices={"convert": NodeChoice(model="x/y", prompt_version="v1")})
    captured = {}

    class Spy:
        def complete(self, system, user, model):
            captured["model"] = model
            captured["user"] = user
            return "OK"

    out, run = run_prompt(state, "convert", Spy(), _VALUES)
    assert captured["model"] == "x/y"
    assert "SRC" in captured["user"]
    assert run.model == "x/y"
    assert run.prompt_version == "v1"


def test_run_prompt_falls_back_to_b2t_model_env(monkeypatch):
    monkeypatch.setenv("B2T_MODEL", "env/model")
    _, run = run_prompt(_state(), "convert", FakeClient("OUT"), _VALUES)
    assert run.model == "env/model"
```

- [ ] **Step 4: Write the `run_prompt` helper**

Create `src/b2t/nodes/_llm.py`:

```python
"""Shared helper that every LLM node uses to run its prompt."""

import os

from b2t import prompts
from b2t.config import DEFAULT_MODEL
from b2t.llm import LLMClient
from b2t.state import NodeChoice, NodeRun, PipelineState


def run_prompt(
    state: PipelineState,
    node_name: str,
    client: LLMClient,
    values: dict[str, str],
) -> tuple[str, NodeRun]:
    """Resolve the node's selection, render its prompt, and call the client.

    Args:
        state: Pipeline state carrying llm_choices.
        node_name: The graph node name, also the prompt registry key.
        client: The LLM client to call.
        values: Token values for the user-message template.

    Returns:
        The model output and a NodeRun recording the model and version used.
        The model falls back to B2T_MODEL then DEFAULT_MODEL; the version falls
        back to the registry default.
    """
    choice = state.llm_choices.get(node_name) or NodeChoice()
    model = choice.model or os.getenv("B2T_MODEL") or DEFAULT_MODEL
    version = choice.prompt_version or prompts.default_version(node_name)
    pv = prompts.load(node_name, version)
    user = prompts.render(pv.user_template, values)
    output = client.complete(pv.system, user, model)
    return output, NodeRun(model=model, prompt_version=version)
```

- [ ] **Step 5: Rewrite `src/b2t/nodes/convert.py`**

Replace the entire contents with:

```python
from loguru import logger

from b2t.config import MATH_GUIDE, REFERENCE_DECK
from b2t.llm import LLMClient
from b2t.nodes._llm import run_prompt
from b2t.state import PipelineState
from b2t.typst_output import strip_code_fence


def convert_node(state: PipelineState, client: LLMClient) -> dict:
    """The single LLM call for this node: Beamer source to Typst Touying source.

    Args:
        state: Pipeline state carrying stripped_tex and llm_choices.
        client: LLM client (bound via functools.partial when the graph is built).

    Returns:
        State update with typst_source (any wrapping code fence removed) and the
        node's provenance merged into llm_runs.
    """
    reference = REFERENCE_DECK.read_text(encoding="utf-8")
    guides = MATH_GUIDE.read_text(encoding="utf-8")
    logger.info("converting {} chars of LaTeX", len(state.stripped_tex))
    output, run = run_prompt(
        state,
        "convert",
        client,
        {"reference": reference, "guides": guides, "source": state.stripped_tex},
    )
    logger.info("conversion returned {} chars of Typst", len(output))
    return {
        "typst_source": strip_code_fence(output),
        "llm_runs": {**state.llm_runs, "convert": run},
    }
```

- [ ] **Step 6: Update the convert tests in `tests/test_nodes.py`**

Replace the three convert tests at the bottom of `tests/test_nodes.py` (currently
`test_convert_node_uses_injected_llm`, `test_convert_node_strips_wrapping_code_fence`,
`test_convert_node_passes_math_guide`) with:

```python
def test_convert_node_uses_injected_client():
    from b2t.llm import FakeClient
    from b2t.nodes.convert import convert_node

    state = _state(stripped_tex="\\section{X}")
    update = convert_node(state, client=FakeClient("= Converted\n"))
    assert update["typst_source"] == "= Converted\n"


def test_convert_node_strips_wrapping_code_fence():
    from b2t.llm import FakeClient
    from b2t.nodes.convert import convert_node

    state = _state(stripped_tex="\\section{X}")
    update = convert_node(state, client=FakeClient("```typst\n= Converted\n```"))
    assert update["typst_source"] == "= Converted\n"


def test_convert_node_passes_math_guide_in_user_message():
    from b2t.nodes.convert import convert_node

    captured = {}

    class Recorder:
        def complete(self, system, user, model):
            captured["user"] = user
            return "= ok\n"

    convert_node(_state(stripped_tex="x"), client=Recorder())
    assert "Writing Math Equations in Typst" in captured["user"]


def test_convert_node_records_provenance():
    from b2t.llm import FakeClient
    from b2t.nodes.convert import convert_node

    update = convert_node(_state(stripped_tex="x"), client=FakeClient("= ok\n"))
    assert update["llm_runs"]["convert"].prompt_version == "v1"
```

- [ ] **Step 7: Update `src/b2t/graph.py`**

In `src/b2t/graph.py`, change the import line `from b2t.llm import ConverterLLM`
to `from b2t.llm import LLMClient`, and update the function signature and the
convert node registration:

```python
def build_graph(llm: LLMClient):
```

becomes

```python
def build_graph(client: LLMClient):
```

and

```python
    graph.add_node("convert", partial(convert_node, llm=llm))
```

becomes

```python
    graph.add_node("convert", partial(convert_node, client=client))
```

(Update the docstring's `Args:` line to mention `client` instead of `llm`.)

- [ ] **Step 8: Update `tests/test_graph.py`**

In `tests/test_graph.py`, change `from b2t.llm import FakeConverter` to
`from b2t.llm import FakeClient`, and the line
`graph = build_graph(FakeConverter(VALID_TYPST))` to
`graph = build_graph(FakeClient(VALID_TYPST))`.

- [ ] **Step 9: Update `src/b2t/app.py`**

In `src/b2t/app.py`, change the import
`from b2t.llm import ConverterLLM, OpenRouterConverter` to
`from b2t.llm import LLMClient, OpenRouterClient`, then replace the function with:

```python
def convert_deck(
    input_dir: str | Path,
    output_dir: str | Path,
    client: LLMClient | None = None,
    llm_choices: dict | None = None,
) -> dict:
    """Convert a Beamer deck directory into a compiled Typst Touying deck.

    Args:
        input_dir: Directory holding the compiled Beamer deck (read-only).
        output_dir: Directory to write main.typ, images, and the PDF into.
        client: LLM client to use; defaults to OpenRouterClient.
        llm_choices: Optional per-node {model, prompt_version} selection.

    Returns:
        The final pipeline state as a dict.
    """
    load_dotenv()
    setup_logging()
    client = client or OpenRouterClient()
    graph = build_graph(client)
    logger.info("converting {} -> {}", input_dir, output_dir)
    result = graph.invoke(
        {
            "input_dir": Path(input_dir),
            "output_dir": Path(output_dir),
            "llm_choices": llm_choices or {},
        }
    )
    if result.get("compiled"):
        logger.info("compiled {}", result.get("pdf_path"))
    else:
        logger.error("compile failed: {}", result.get("compile_error"))
    return result
```

- [ ] **Step 10: Update `src/b2t/api/jobs.py`**

In `src/b2t/api/jobs.py`:

Change `from b2t.llm import ConverterLLM` to `from b2t.llm import LLMClient`.

Replace the `run_job` signature and seed lines. The signature becomes:

```python
def run_job(
    store: JobStore,
    job_id: str,
    input_dir: Path,
    output_dir: Path,
    make_client: Callable[[], LLMClient],
    choices: dict | None = None,
) -> None:
```

Inside the function, change the seed dict from:

```python
    seed = {"input_dir": input_dir, "output_dir": output_dir}
```

to:

```python
    seed = {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "llm_choices": choices or {},
    }
```

and change `graph = build_graph(make_converter())` to
`graph = build_graph(make_client())`. (Update the docstring's `make_converter`
mention to `make_client`.)

- [ ] **Step 11: Update `tests/test_api_jobs.py`**

In `tests/test_api_jobs.py`:

Change `from b2t.llm import FakeConverter` to `from b2t.llm import FakeClient`.

In `test_run_job_reaches_terminal` and `test_run_job_records_deterministic_failure`,
change the `FakeConverter("= Hi\n")` factory call to `FakeClient("= Hi\n")`.

Replace `test_current_node_tracks_the_running_node` with the client-based spy:

```python
def test_current_node_tracks_the_running_node(tmp_path):
    # current_node must name the node that is RUNNING, not the last finished one.
    store = JobStore()
    job = store.create(input_dir=SAMPLE_DECK, output_dir=tmp_path / "out")
    captured = {}

    class SpyClient:
        def complete(self, system, user, model):
            captured["during_convert"] = store.get(job.id).current_node
            return "= Hi\n"

    run_job(store, job.id, SAMPLE_DECK, tmp_path / "out", lambda: SpyClient())
    assert captured["during_convert"] == "convert"
```

- [ ] **Step 12: Update `src/b2t/api/app.py`**

In `src/b2t/api/app.py`:

Change the import `from b2t.llm import ConverterLLM, FakeConverter, OpenRouterConverter`
to `from b2t.llm import FakeClient, LLMClient, OpenRouterClient`.

Replace `_make_converter` with:

```python
def _make_client(use_fake: bool) -> LLMClient:
    """Pick the client for a job.

    Args:
        use_fake: True for the offline FakeClient (no network).

    Returns:
        An LLMClient ready for the pipeline.
    """
    if use_fake:
        return FakeClient(FAKE_TYPST)
    return OpenRouterClient()
```

In `create_job`, change the executor submission to build per-node choices from
the existing `model` field and pass them through:

```python
        EXECUTOR.submit(
            run_job, jobs, job.id, root, output_dir,
            lambda: _make_client(use_fake),
            {"convert": {"model": model}} if model else {},
        )
```

In `create_sample_job`, do the same:

```python
        EXECUTOR.submit(
            run_job, jobs, job.id, SAMPLE_DECK, output_dir,
            lambda: _make_client(use_fake),
            {"convert": {"model": model}} if model else {},
        )
```

- [ ] **Step 13: Update `tests/test_api_app.py`**

In `tests/test_api_app.py`, replace `test_make_converter_picks_fake_or_openrouter`
with:

```python
def test_make_client_picks_fake_or_openrouter(monkeypatch):
    from b2t.api.app import _make_client
    from b2t.llm import FakeClient, OpenRouterClient

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    assert isinstance(_make_client(True), FakeClient)
    assert isinstance(_make_client(False), OpenRouterClient)
```

- [ ] **Step 14: Run the whole suite**

Run: `uv run pytest -q`
Expected: PASS (all tests green; integration tests run if `typst` is installed, otherwise skip).

- [ ] **Step 15: Commit**

```bash
git add src/b2t/llm.py src/b2t/nodes/_llm.py src/b2t/nodes/convert.py \
  src/b2t/graph.py src/b2t/app.py src/b2t/api/jobs.py src/b2t/api/app.py \
  tests/test_llm.py tests/test_llm_node.py tests/test_nodes.py \
  tests/test_graph.py tests/test_api_jobs.py tests/test_api_app.py
git commit -m "refactor: generic LLM client seam with prompt-driven convert node"
```

---

## Task 6: Record provenance on the job

Surface "what model and version ran" through the job record and the job view.

**Files:**
- Modify: `src/b2t/api/jobs.py`, `src/b2t/api/schemas.py`
- Test: `tests/test_api_schemas.py`, `tests/test_api_jobs.py`

- [ ] **Step 1: Write the failing tests**

In `tests/test_api_schemas.py`, append:

```python
def test_to_view_maps_llm_runs():
    rec = JobRecord(
        id="abc",
        status="succeeded",
        llm_runs={"convert": {"model": "m/x", "prompt_version": "v1"}},
    )
    view = to_view(rec)
    assert view.llm_runs["convert"].model == "m/x"
    assert view.llm_runs["convert"].prompt_version == "v1"
```

In `tests/test_api_jobs.py`, append:

```python
def test_run_job_records_llm_runs(tmp_path):
    from b2t.config import DEFAULT_MODEL

    store = JobStore()
    out = tmp_path / "out"
    job = store.create(input_dir=SAMPLE_DECK, output_dir=out)
    run_job(store, job.id, SAMPLE_DECK, out, lambda: FakeClient("= Hi\n"))
    rec = store.get(job.id)
    assert rec.llm_runs["convert"] == {
        "model": DEFAULT_MODEL,
        "prompt_version": "v1",
    }
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_api_schemas.py tests/test_api_jobs.py -q`
Expected: FAIL (`JobRecord` has no `llm_runs`; `JobView` has no `llm_runs`).

- [ ] **Step 3: Add `llm_runs` to the job record and populate it**

In `src/b2t/api/jobs.py`, add a field to `JobRecord` after `pdf_path`:

```python
    llm_runs: dict[str, dict] = field(default_factory=dict)
```

In `run_job`, after the existing `store.update(job_id, main_tex=..., ...)` block
that records the summary, add the provenance conversion. Change that block to
include `llm_runs`:

```python
    runs = state.get("llm_runs", {})
    store.update(
        job_id,
        main_tex=main_tex.name if main_tex else None,
        included_tex=[p.name for p in state.get("included_tex", [])],
        images=[p.name for p in state.get("image_files", [])],
        has_typst=state.get("typst_source") is not None,
        typst_path=state.get("typst_path"),
        llm_runs={
            node: {"model": run.model, "prompt_version": run.prompt_version}
            for node, run in runs.items()
        },
    )
```

- [ ] **Step 4: Add the view model**

In `src/b2t/api/schemas.py`, add `NodeRunView` near the top (after the imports):

```python
class NodeRunView(BaseModel):
    """What an LLM node used on a run: the model and prompt version."""

    model: str
    prompt_version: str
```

Add `llm_runs` to `JobView` (after `has_pdf`):

```python
    llm_runs: dict[str, NodeRunView] = {}
```

In `to_view`, add the mapping inside the returned `JobView(...)`:

```python
        llm_runs={
            node: NodeRunView(**run) for node, run in job.llm_runs.items()
        },
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_api_schemas.py tests/test_api_jobs.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/b2t/api/jobs.py src/b2t/api/schemas.py \
  tests/test_api_schemas.py tests/test_api_jobs.py
git commit -m "feat: record per-node llm provenance on the job"
```

---

## Task 7: Serve the LLM-node catalog

A new endpoint lists each LLM node with its prompt versions and default, so the
UI can build per-node version dropdowns.

**Files:**
- Modify: `src/b2t/api/schemas.py`, `src/b2t/api/app.py`
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing test**

In `tests/test_api_app.py`, append:

```python
def test_llm_nodes_endpoint_lists_convert_with_versions():
    body = _client().get("/api/llm-nodes").json()
    convert = next(n for n in body["nodes"] if n["node"] == "convert")
    assert convert["default_version"] == "v1"
    assert "v1" in [v["id"] for v in convert["versions"]]
    assert all(v["label"] for v in convert["versions"])
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_api_app.py::test_llm_nodes_endpoint_lists_convert_with_versions -v`
Expected: FAIL (404, route not defined).

- [ ] **Step 3: Add the schemas**

In `src/b2t/api/schemas.py`, append:

```python
class VersionOption(BaseModel):
    """One prompt-version dropdown entry."""

    id: str
    label: str


class LLMNodeView(BaseModel):
    """An LLM node with its available prompt versions and default."""

    node: str
    versions: list[VersionOption]
    default_version: str


class LLMNodesView(BaseModel):
    """All LLM nodes, for building per-node UI controls."""

    nodes: list[LLMNodeView]
```

- [ ] **Step 4: Add the endpoint**

In `src/b2t/api/app.py`, add the import `from b2t import prompts` near the other
`b2t` imports, add `LLMNodeView, LLMNodesView, VersionOption` to the
`from b2t.api.schemas import (...)` block, and register the route next to
`get_models`:

```python
    @app.get("/api/llm-nodes", response_model=LLMNodesView)
    def get_llm_nodes():
        """Return each LLM node with its prompt versions and default version."""
        nodes = []
        for node in prompts.list_nodes():
            versions = [
                VersionOption(id=v, label=prompts.load(node, v).description or v)
                for v in prompts.list_versions(node)
            ]
            nodes.append(
                LLMNodeView(
                    node=node,
                    versions=versions,
                    default_version=prompts.default_version(node),
                )
            )
        return LLMNodesView(nodes=nodes)
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `uv run pytest tests/test_api_app.py::test_llm_nodes_endpoint_lists_convert_with_versions -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/b2t/api/schemas.py src/b2t/api/app.py tests/test_api_app.py
git commit -m "feat: add /api/llm-nodes catalog endpoint"
```

---

## Task 8: Per-node selection in the API and UI

Replace the single global model field with a validated per-node `choices` payload,
and render per-node model and version pickers in the browser, plus the provenance
of the last run.

**Files:**
- Modify: `src/b2t/api/app.py`
- Modify: `src/b2t/api/static/index.html`, `src/b2t/api/static/app.js`, `src/b2t/api/static/style.css`
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing tests**

In `tests/test_api_app.py`, append:

```python
def test_choices_validation_rejects_unknown_node():
    client = _client()
    res = client.post(
        "/api/jobs/sample",
        data={"use_fake": "true", "choices": '{"nope": {"prompt_version": "v1"}}'},
    )
    assert res.status_code == 400


def test_choices_validation_rejects_unknown_version():
    client = _client()
    res = client.post(
        "/api/jobs/sample",
        data={"use_fake": "true", "choices": '{"convert": {"prompt_version": "v999"}}'},
    )
    assert res.status_code == 400


def test_sample_job_with_valid_choices_runs_and_reports_provenance():
    client = _client()
    res = client.post(
        "/api/jobs/sample",
        data={"use_fake": "true", "choices": '{"convert": {"prompt_version": "v1"}}'},
    )
    assert res.status_code == 200
    body = _wait_terminal(client, res.json()["job_id"])
    assert body["llm_runs"]["convert"]["prompt_version"] == "v1"


def test_index_has_llm_nodes_container():
    text = _client().get("/").text
    assert '<div id="llm-nodes"' in text
    assert '<select id="model"' not in text
```

Also delete the now-obsolete `test_index_has_model_select` test from this file.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_api_app.py -q`
Expected: FAIL (no `choices` validation; index still has `#model`).

- [ ] **Step 3: Add choices parsing and validation to the API**

In `src/b2t/api/app.py`, add `import json` at the top if not present, and add this
helper next to `_make_client`:

```python
def _parse_choices(raw: str) -> dict:
    """Parse and validate the per-node choices JSON from a form field.

    Args:
        raw: JSON like {"convert": {"model": "...", "prompt_version": "v1"}};
            empty string means no overrides.

    Returns:
        The validated choices dict (empty if raw is empty).

    Raises:
        HTTPException: 400 if the JSON is invalid, names an unknown node, or
            names an unknown prompt version. Unknown models are allowed through.
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="choices is not valid JSON")
    valid_nodes = set(prompts.list_nodes())
    for node, sel in data.items():
        if node not in valid_nodes:
            raise HTTPException(status_code=400, detail=f"unknown LLM node: {node}")
        version = sel.get("prompt_version")
        if version and version not in prompts.list_versions(node):
            raise HTTPException(
                status_code=400, detail=f"unknown version {version} for node {node}"
            )
    return data
```

Replace the `model: str = Form("")` parameter with `choices: str = Form("")` in
both handlers, and parse it at the very top of each handler body (so an invalid
payload raises 400 before any temp dir or job is created), then pass the parsed
result to the executor.

`create_job` becomes (showing the changed lines in context):

```python
    @app.post("/api/jobs", response_model=JobCreated)
    async def create_job(
        files: list[UploadFile] = File([]),
        use_fake: bool = Form(False),
        choices: str = Form(""),
    ):
        """Reconstruct an uploaded deck folder and start a conversion job."""
        if not files:
            raise HTTPException(status_code=400, detail="no files submitted")
        parsed = _parse_choices(choices)
        root = Path(tempfile.mkdtemp(prefix="b2t_upload_"))
        _reconstruct(files, root)
        output_dir = root.parent / (root.name + "_out")
        job = jobs.create(input_dir=root, output_dir=output_dir)
        logger.info("job {} created for upload ({} files)", job.id, len(files))
        EXECUTOR.submit(
            run_job, jobs, job.id, root, output_dir,
            lambda: _make_client(use_fake),
            parsed,
        )
        return JobCreated(job_id=job.id, status=job.status)
```

`create_sample_job` becomes:

```python
    @app.post("/api/jobs/sample", response_model=JobCreated)
    async def create_sample_job(use_fake: bool = Form(False), choices: str = Form("")):
        """Start a conversion job on the bundled sample deck."""
        parsed = _parse_choices(choices)
        output_dir = Path(tempfile.mkdtemp(prefix="b2t_sample_")) / "out"
        job = jobs.create(input_dir=SAMPLE_DECK, output_dir=output_dir)
        logger.info("job {} created for the sample deck", job.id)
        EXECUTOR.submit(
            run_job, jobs, job.id, SAMPLE_DECK, output_dir,
            lambda: _make_client(use_fake),
            parsed,
        )
        return JobCreated(job_id=job.id, status=job.status)
```

- [ ] **Step 4: Update the HTML**

In `src/b2t/api/static/index.html`, replace this block:

```html
      <div class="options">
        <label><input type="checkbox" id="use-fake" /> use fake converter (offline)</label>
        <label>model: <select id="model"></select></label>
      </div>
```

with:

```html
      <div class="options">
        <label><input type="checkbox" id="use-fake" /> use fake converter (offline)</label>
      </div>
      <div id="llm-nodes"></div>
```

And in the output section, add a provenance line after the status badge block.
Inside `<section class="status">`, after the `<div id="graph"></div>` line, add:

```html
      <div id="provenance"></div>
```

- [ ] **Step 5: Update the JavaScript**

In `src/b2t/api/static/app.js`:

Remove the `loadModels()` function and its call at the bottom of the file.

Add these functions (near the other loaders):

```javascript
let llmNodes = [];

async function loadLLMNodes() {
  const container = $("llm-nodes");
  container.innerHTML = "";
  let models = [];
  try {
    models = (await (await fetch("/api/models")).json()).models;
    llmNodes = (await (await fetch("/api/llm-nodes")).json()).nodes;
  } catch (e) {
    return; // leave empty; submitting with no choices keeps server defaults
  }
  for (const node of llmNodes) {
    const row = document.createElement("div");
    row.className = "llm-node";
    const modelSel = document.createElement("select");
    modelSel.dataset.node = node.node;
    modelSel.className = "model-select";
    for (const m of models) {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.textContent = m.label;
      modelSel.appendChild(opt);
    }
    const verSel = document.createElement("select");
    verSel.dataset.node = node.node;
    verSel.className = "version-select";
    for (const v of node.versions) {
      const opt = document.createElement("option");
      opt.value = v.id;
      opt.textContent = v.label;
      opt.selected = v.id === node.default_version;
      verSel.appendChild(opt);
    }
    row.append(`${node.node}: model `, modelSel, " version ", verSel);
    container.appendChild(row);
  }
}

function collectChoices() {
  const choices = {};
  for (const sel of document.querySelectorAll(".model-select")) {
    choices[sel.dataset.node] = { model: sel.value };
  }
  for (const sel of document.querySelectorAll(".version-select")) {
    (choices[sel.dataset.node] ||= {}).prompt_version = sel.value;
  }
  return choices;
}
```

Replace `commonFields` with:

```javascript
function commonFields(fd) {
  fd.append("use_fake", $("use-fake").checked ? "true" : "false");
  fd.append("choices", JSON.stringify(collectChoices()));
  return fd;
}
```

In `finish(id, job)`, after setting the error text, add a provenance render:

```javascript
  const prov = job.llm_runs || {};
  $("provenance").textContent = Object.keys(prov).length
    ? "Ran: " + Object.entries(prov)
        .map(([n, r]) => `${n} (${r.model}, ${r.prompt_version})`)
        .join("; ")
    : "";
```

At the bottom of the file, replace the `loadModels();` call with:

```javascript
loadLLMNodes();
```

- [ ] **Step 6: Add minimal styling**

In `src/b2t/api/static/style.css`, append:

```css
.llm-node { margin-top: 0.5rem; display: flex; gap: 0.4rem; align-items: center; flex-wrap: wrap; }
#provenance { margin-top: 0.5rem; font-size: 0.85rem; color: #555; }
```

- [ ] **Step 7: Run the suite**

Run: `uv run pytest -q`
Expected: PASS (all tests green).

- [ ] **Step 8: Manual verification in the browser**

Run: `uv run uvicorn b2t.api.app:app`
Then open `http://127.0.0.1:8000` and confirm:
- A `convert: model [...] version [...]` row appears under the checkbox.
- Tick "use fake converter (offline)" and click "Use sample deck".
- After it finishes, the provenance line reads `Ran: convert (..., v1)`.
- The generated `main.typ`, the PDF (if typst is installed), and any error show as before.

- [ ] **Step 9: Commit**

```bash
git add src/b2t/api/app.py src/b2t/api/static/index.html \
  src/b2t/api/static/app.js src/b2t/api/static/style.css tests/test_api_app.py
git commit -m "feat: per-node model and prompt-version selection in the UI"
```

---

## Final verification

- [ ] **Run the entire suite**

Run: `uv run pytest -q`
Expected: all tests pass (integration tests run if `typst` is installed).

- [ ] **Confirm a default run is unchanged**

Run: `uv run python -c "from b2t.app import convert_deck; convert_deck('tests/fixtures/sample_deck', 'out')"`
Expected: with no `OPENROUTER_API_KEY`, it logs a failed job cleanly (the client raises inside the run). With a key set, it converts as before, since `convert/v1` is the migrated prompt.

---

## Notes for the implementer

- Keep `_parse_choices` validation lenient on the model id (OpenRouter accepts
  models outside the curated catalog), strict on node and version.
- The graph is linear, so each LLM node returning `{"llm_runs": {**state.llm_runs, name: run}}` is safe (no concurrent writers). If a future graph branches, switch `llm_runs` to a LangGraph reducer.
- New LLM nodes follow the convert node exactly: add `prompts/<node>/v1.toml`, an entry in `defaults.json`, a thin node that calls `run_prompt(state, "<node>", client, values)`, wire it into `build_graph`, and the UI picks it up automatically from `/api/llm-nodes`.
