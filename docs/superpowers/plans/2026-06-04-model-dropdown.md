# Model Dropdown Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the free-text "model override" box in the testing frontend with a typo-proof dropdown of OpenAI model ids, sourced from a single list in `config.py`.

**Architecture:** Two additive changes. The backend gains `OPENAI_MODELS` in `config.py`, a `ModelsView` schema, and a `GET /api/models` endpoint that serves the list plus the default. The frontend swaps the model `<input>` for a `<select>` populated on load from that endpoint, with a first `(default)` option (empty value) preserving the existing fallback chain. The conversion pipeline and the `/api/jobs` flow are untouched.

**Tech Stack:** Python 3.12, uv, FastAPI, pydantic v2, pytest with FastAPI `TestClient`. Vanilla JS, no build step.

---

## Conventions for this plan

- Work happens on the current branch `feat/testing-frontend`.
- All commands run from the repo root `d:\projects\b2t` with `uv run ...`. Never use `pip` or `python` directly.
- Every commit message appends the trailer line (after a blank line):
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- No emojis. No em or en dashes in code or docs.
- Do NOT modify the pipeline (`graph.py`, `nodes/`, `state.py`, `latex/`, `typst_runner.py`, `llm.py`) or `jobs.py`.

## File structure

```
src/b2t/config.py               # modify: add OPENAI_MODELS tuple
src/b2t/api/schemas.py          # modify: add ModelsView
src/b2t/api/app.py              # modify: add GET /api/models + imports
src/b2t/api/static/index.html   # modify: model input -> <select>
src/b2t/api/static/app.js       # modify: populate the select on load
tests/test_api_app.py           # modify: add /api/models test and select markup test
tests/test_config.py            # modify: assert OPENAI_MODELS contents
```

For reference, `src/b2t/config.py` currently ends with `DEFAULT_OPENAI_MODEL = "gpt-5.4-nano"` followed by the `BUILD_FILE_EXTENSIONS` tuple. `app.py` imports `from b2t.config import REPO_ROOT` and registers routes before mounting `StaticFiles` at `/` LAST. The current model input in `index.html` is:
`<label>model override: <input type="text" id="model" placeholder="(default)" /></label>`.

---

### Task 1: Config list, schema, and /api/models endpoint

**Files:**
- Modify: `src/b2t/config.py`
- Modify: `src/b2t/api/schemas.py`
- Modify: `src/b2t/api/app.py`
- Test: `tests/test_api_app.py`, `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_api_app.py`:

```python
def test_models_endpoint_lists_config_models():
    from b2t.config import DEFAULT_OPENAI_MODEL, OPENAI_MODELS

    body = _client().get("/api/models").json()
    assert body["models"] == list(OPENAI_MODELS)
    assert body["default"] == DEFAULT_OPENAI_MODEL
    assert body["default"] in body["models"]
```

Append to `tests/test_config.py`:

```python
def test_openai_models_includes_default_first():
    assert config.OPENAI_MODELS[0] == config.DEFAULT_OPENAI_MODEL
    assert "gpt-5.5" in config.OPENAI_MODELS
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_config.py::test_openai_models_includes_default_first -q`
Expected: FAIL with `AttributeError: module 'b2t.config' has no attribute 'OPENAI_MODELS'`.

- [ ] **Step 3: Add the config list**

In `src/b2t/config.py`, add this line immediately after `DEFAULT_OPENAI_MODEL = "gpt-5.4-nano"`:

```python
OPENAI_MODELS = (
    "gpt-5.4-nano",
    "gpt-5.4-mini",
    "gpt-5.4",
    "gpt-5.4-pro",
    "gpt-5.5",
)
```

- [ ] **Step 4: Add the schema**

In `src/b2t/api/schemas.py`, add this model after the `SaveResult` class (before `def to_view`):

```python
class ModelsView(BaseModel):
    models: list[str]
    default: str
```

- [ ] **Step 5: Add the endpoint and imports in app.py**

In `src/b2t/api/app.py`, change the config import line:

```python
from b2t.config import REPO_ROOT
```

to:

```python
from b2t.config import DEFAULT_OPENAI_MODEL, OPENAI_MODELS, REPO_ROOT
```

Add `ModelsView` to the schemas import so it reads:

```python
from b2t.api.schemas import (
    JobCreated,
    JobView,
    ModelsView,
    SaveRequest,
    SaveResult,
    to_view,
)
```

Then add this route inside `create_app`, with the other routes and BEFORE `app.mount(...)`:

```python
    @app.get("/api/models", response_model=ModelsView)
    def get_models():
        return ModelsView(models=list(OPENAI_MODELS), default=DEFAULT_OPENAI_MODEL)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_config.py tests/test_api_app.py -q`
Expected: PASS (the new tests plus all existing ones; typst-dependent tests skip when the binary is absent).

- [ ] **Step 7: Commit**

```bash
git add src/b2t/config.py src/b2t/api/schemas.py src/b2t/api/app.py tests/test_api_app.py tests/test_config.py
git commit -m "feat: serve openai model list from config"
```

---

### Task 2: Model dropdown in the frontend

**Files:**
- Modify: `src/b2t/api/static/index.html`
- Modify: `src/b2t/api/static/app.js`
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_api_app.py`:

```python
def test_index_has_model_select():
    text = _client().get("/").text
    assert '<select id="model"' in text
    assert 'type="text" id="model"' not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_app.py::test_index_has_model_select -q`
Expected: FAIL (the page still has the text input `id="model"`, not a `<select>`).

- [ ] **Step 3: Replace the model input in index.html**

In `src/b2t/api/static/index.html`, replace this line:

```html
        <label>model override: <input type="text" id="model" placeholder="(default)" /></label>
```

with:

```html
        <label>model: <select id="model"></select></label>
```

- [ ] **Step 4: Populate the select in app.js**

In `src/b2t/api/static/app.js`, add this function and its call. Place the function definition just below the `commonFields` function, and place the `loadModels();` call at the very end of the file (after the existing event-listener registrations):

```javascript
async function loadModels() {
  const sel = $("model");
  sel.innerHTML = '<option value="">(default)</option>';
  try {
    const res = await fetch("/api/models");
    const data = await res.json();
    for (const id of data.models) {
      const opt = document.createElement("option");
      opt.value = id;
      opt.textContent = id === data.default ? `${id} (default)` : id;
      sel.appendChild(opt);
    }
  } catch (e) {
    // leave only the (default) option if the list cannot be fetched
  }
}
```

Add this line as the last line of the file:

```javascript
loadModels();
```

Note: `commonFields` already does `fd.append("model", $("model").value)`, which reads the selected option's value (a model id, or `""` for the `(default)` option). No change there.

- [ ] **Step 5: Run the test to verify it passes**

Run: `uv run pytest tests/test_api_app.py::test_index_has_model_select -q`
Expected: PASS.

- [ ] **Step 6: Run the full suite**

Run: `uv run pytest -q`
Expected: all tests pass (typst-dependent tests skip when the binary is absent).

- [ ] **Step 7: Server-serves check**

Run:

```bash
uv run python -c "from fastapi.testclient import TestClient; from b2t.api.app import app; c = TestClient(app); print(c.get('/').status_code); import json; print(json.dumps(c.get('/api/models').json()))"
```

Expected: prints `200`, then a JSON object with a `models` list (5 ids) and `default` of `gpt-5.4-nano`.

- [ ] **Step 8: Commit**

```bash
git add src/b2t/api/static/index.html src/b2t/api/static/app.js tests/test_api_app.py
git commit -m "feat: replace model text box with a dropdown"
```

---

## Self-review

**Spec coverage** (each spec section maps to a task):
- Config-driven list (`OPENAI_MODELS` in config.py) -> Task 1.
- `GET /api/models` serving list + default (`ModelsView`) -> Task 1.
- Plain `<select>`, typo-proof -> Task 2.
- First `(default)` option with empty value preserving the env-var / config fallback -> Task 2 (`loadModels` seeds `<option value="">(default)</option>`).
- Submission unchanged (`commonFields` reads `$("model").value`) -> Task 2 note (no change).
- Default id labelled `<id> (default)` -> Task 2 (`loadModels`).
- Resilience if `/api/models` fails (keep the default option) -> Task 2 (the `innerHTML` seed before the fetch plus the empty catch).
- Backend test for `/api/models`; static markup test for the `<select>` -> Tasks 1, 2.
- Pipeline and jobs.py untouched -> no task modifies them.

**Placeholder scan:** none. The only free value is the model list, taken from the spec's current-models list.

**Type consistency:** `OPENAI_MODELS` (config, Task 1) is imported in `app.py` (Task 1) and asserted in tests (Tasks 1). `ModelsView(models, default)` defined in Task 1 is returned by `get_models` (Task 1) and read by the frontend `loadModels` as `data.models` / `data.default` (Task 2), matching the field names. `DEFAULT_OPENAI_MODEL` already exists in config and is now also imported into `app.py`. The select element keeps `id="model"`, so the existing `commonFields` reference is unchanged.

**Out-of-scope guard:** no pricing display, no live OpenAI catalogue fetch, no validation beyond the fixed list. Consistent with the spec non-goals.
