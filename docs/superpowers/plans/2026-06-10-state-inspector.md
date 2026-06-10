# Per-Node State Inspector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a developer click any finished node in the testing UI's pipeline strip and see the full accumulated LangGraph state after that node ran, with the fields that node changed highlighted.

**Architecture:** Capture each node's serialized delta live in `run_job`'s existing stream loop, store the deltas plus a serialized seed on the in-memory `JobRecord`, and serve a folded-on-demand snapshot from a new read-only endpoint. The browser renders the snapshot under the strip and does preview/expand of long strings client-side. No change to the graph, the nodes, or `PipelineState`.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, LangGraph (already wired); plain JS/CSS for the UI; pytest with `FakeClient` (offline). Run everything with `uv run ...`.

Spec: `docs/superpowers/specs/2026-06-10-state-inspector-design.md`.

---

## File structure

- Create `src/b2t/api/state_view.py` - JSON-safe serialization (`to_jsonsafe`, `serialize_values`), the `NodeDelta` dataclass, and `fold_snapshot`. Imports only stdlib + Pydantic, so it has no dependency on `jobs.py` (avoids an import cycle).
- Modify `src/b2t/api/jobs.py` - `JobRecord` gains `seed_state` and `node_deltas`; `JobStore` gains `append_delta`; `run_job` captures the seed once and a delta per finished node.
- Modify `src/b2t/api/schemas.py` - add `NodeStateView`; add `state_nodes` to `JobView`; populate it in `to_view`.
- Modify `src/b2t/api/app.py` - one new route `GET /api/jobs/{job_id}/state/{node}`.
- Modify `src/b2t/api/static/index.html` - add the `#state-inspector` container.
- Modify `src/b2t/api/static/app.js` - mark inspectable nodes, fetch and render a snapshot on click.
- Modify `src/b2t/api/static/style.css` - inspector and inspectable/selected-node styles.
- Tests: `tests/test_state_view.py` (new), and additions to `tests/test_api_jobs.py`, `tests/test_api_schemas.py`, `tests/test_api_app.py`.

Tasks are ordered so each builds only on earlier ones.

---

### Task 1: Serialization and folding module

**Files:**
- Create: `src/b2t/api/state_view.py`
- Test: `tests/test_state_view.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_state_view.py`:

```python
from pathlib import Path

import pytest

from b2t.api.state_view import (
    NodeDelta,
    fold_snapshot,
    serialize_values,
    to_jsonsafe,
)
from b2t.state import NodeRun, RenderedPrompt


def test_to_jsonsafe_path():
    assert to_jsonsafe(Path("/tmp/x")) == str(Path("/tmp/x"))


def test_to_jsonsafe_list_of_paths():
    assert to_jsonsafe([Path("a.tex"), Path("b.tex")]) == ["a.tex", "b.tex"]


def test_to_jsonsafe_basemodel():
    run = NodeRun(model="m/x", prompt_version="v1")
    assert to_jsonsafe(run) == {"model": "m/x", "prompt_version": "v1"}


def test_to_jsonsafe_nested_dict_of_models():
    rendered = {"convert": RenderedPrompt(system="s", user="u")}
    assert to_jsonsafe(rendered) == {"convert": {"system": "s", "user": "u"}}


def test_to_jsonsafe_passes_primitives():
    assert to_jsonsafe(True) is True
    assert to_jsonsafe(None) is None
    assert to_jsonsafe(7) == 7


def test_to_jsonsafe_stringifies_unknown():
    class Weird:
        def __str__(self):
            return "weird"

    assert to_jsonsafe(Weird()) == "weird"


def test_serialize_values():
    out = serialize_values({"main_tex": Path("main.tex"), "compiled": False})
    assert out == {"main_tex": "main.tex", "compiled": False}


def test_fold_snapshot_accumulates_to_node():
    seed = {"input_dir": "/in"}
    deltas = [
        NodeDelta("copy_input", ["work_dir"], {"work_dir": "/work"}),
        NodeDelta("detect_main", ["main_tex"], {"main_tex": "main.tex"}),
    ]
    changed, state = fold_snapshot(seed, deltas, "detect_main")
    assert changed == ["main_tex"]
    assert state == {"input_dir": "/in", "work_dir": "/work", "main_tex": "main.tex"}


def test_fold_snapshot_stops_at_requested_node():
    deltas = [NodeDelta("a", ["x"], {"x": 1}), NodeDelta("b", ["y"], {"y": 2})]
    changed, state = fold_snapshot({}, deltas, "a")
    assert changed == ["x"]
    assert state == {"x": 1}  # b's delta is not applied


def test_fold_snapshot_unknown_node_raises():
    with pytest.raises(KeyError):
        fold_snapshot({}, [NodeDelta("a", ["x"], {"x": 1})], "missing")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_state_view.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'b2t.api.state_view'`.

- [ ] **Step 3: Write the implementation**

Create `src/b2t/api/state_view.py`:

```python
"""JSON-safe serialization of pipeline state and per-node delta folding."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def to_jsonsafe(value: Any) -> Any:
    """Convert one pipeline-state value to a JSON-safe form.

    Paths become strings, Pydantic models become dicts, lists and dicts
    recurse, primitives pass through, and anything else is stringified so a
    debug view never crashes on an unexpected type.
    """
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, (list, tuple)):
        return [to_jsonsafe(v) for v in value]
    if isinstance(value, dict):
        return {k: to_jsonsafe(v) for k, v in value.items()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def serialize_values(d: dict) -> dict:
    """Apply to_jsonsafe to each value of a dict (a node delta or the seed)."""
    return {k: to_jsonsafe(v) for k, v in d.items()}


@dataclass
class NodeDelta:
    """One node's contribution to state, JSON-safe.

    Attributes:
        node: The node name.
        changed: The field names this node wrote.
        values: The JSON-safe field values this node wrote.
    """

    node: str
    changed: list[str]
    values: dict


def fold_snapshot(
    seed_state: dict, deltas: list[NodeDelta], node: str
) -> tuple[list[str], dict]:
    """Fold the seed plus deltas up to and including `node`.

    Args:
        seed_state: JSON-safe seed (input_dir, output_dir, llm_choices).
        deltas: Per-node deltas in run order.
        node: The node whose accumulated snapshot is wanted.

    Returns:
        That node's changed list and the accumulated state dict.

    Raises:
        KeyError: If no delta matches `node` (it has not run).
    """
    acc = dict(seed_state)
    for d in deltas:
        acc.update(d.values)
        if d.node == node:
            return d.changed, acc
    raise KeyError(node)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_state_view.py -v`
Expected: PASS (10 passed).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/api/state_view.py tests/test_state_view.py
git commit -m "feat: add json-safe state serializer and delta folding"
```

---

### Task 2: Job record fields and store append

**Files:**
- Modify: `src/b2t/api/jobs.py` (`JobRecord`, `JobStore`)
- Test: `tests/test_api_jobs.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_api_jobs.py` (top-level import and a new test). Add this import near the existing imports at the top of the file:

```python
from b2t.api.state_view import NodeDelta
```

Then add this test:

```python
def test_append_delta_accumulates_node_deltas():
    store = JobStore()
    job = store.create()
    store.append_delta(job.id, NodeDelta("copy_input", ["work_dir"], {"work_dir": "/w"}))
    store.append_delta(
        job.id, NodeDelta("detect_main", ["main_tex"], {"main_tex": "main.tex"})
    )
    rec = store.get(job.id)
    assert [d.node for d in rec.node_deltas] == ["copy_input", "detect_main"]
    assert rec.seed_state == {}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_api_jobs.py::test_append_delta_accumulates_node_deltas -v`
Expected: FAIL with `AttributeError: 'JobStore' object has no attribute 'append_delta'`.

- [ ] **Step 3: Write the implementation**

In `src/b2t/api/jobs.py`, add the import near the other `b2t` imports at the top:

```python
from b2t.api.state_view import NodeDelta, serialize_values
```

Add two fields at the end of `JobRecord` (after `llm_rendered`):

```python
    seed_state: dict = field(default_factory=dict)
    node_deltas: list[NodeDelta] = field(default_factory=list)
```

Add two lines to the `JobRecord` docstring's Attributes section (after the `pdf_path` line), to keep the docstring honest:

```python
        seed_state: JSON-safe pipeline seed (input/output dirs, choices).
        node_deltas: Per-node JSON-safe deltas captured as each node finished.
```

Add this method to `JobStore` (after `update`):

```python
    def append_delta(self, job_id: str, delta: NodeDelta) -> None:
        """Append one captured node delta to the job's snapshot trail."""
        with self._lock:
            self._jobs[job_id].node_deltas.append(delta)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_api_jobs.py::test_append_delta_accumulates_node_deltas -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/api/jobs.py tests/test_api_jobs.py
git commit -m "feat: store per-node deltas and seed on the job record"
```

---

### Task 3: Capture deltas live in run_job

**Files:**
- Modify: `src/b2t/api/jobs.py` (`run_job`)
- Test: `tests/test_api_jobs.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_api_jobs.py`:

```python
def test_run_job_captures_node_deltas(tmp_path):
    store = JobStore()
    out = tmp_path / "out"
    job = store.create(input_dir=SAMPLE_DECK, output_dir=out)
    run_job(store, job.id, SAMPLE_DECK, out, lambda: FakeClient("= Hi\n"))
    rec = store.get(job.id)
    assert [d.node for d in rec.node_deltas] == list(PIPELINE_NODES)
    convert = next(d for d in rec.node_deltas if d.node == "convert")
    assert "typst_source" in convert.changed
    assert "llm_runs" in convert.changed
    assert "llm_rendered" in convert.changed
    assert "input_dir" in rec.seed_state
    assert "output_dir" in rec.seed_state


def test_run_job_keeps_partial_deltas_on_failure(tmp_path):
    deck = tmp_path / "deck"
    deck.mkdir()
    (deck / "notes.tex").write_text("just notes", encoding="utf-8")
    store = JobStore()
    out = tmp_path / "out"
    job = store.create(input_dir=deck, output_dir=out)
    run_job(store, job.id, deck, out, lambda: FakeClient("= Hi\n"))
    rec = store.get(job.id)
    assert rec.status == "failed"
    # detect_main raises, so only the two nodes before it captured a delta.
    assert [d.node for d in rec.node_deltas] == ["copy_input", "clean_build"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_api_jobs.py::test_run_job_captures_node_deltas tests/test_api_jobs.py::test_run_job_keeps_partial_deltas_on_failure -v`
Expected: FAIL (`node_deltas` is empty because `run_job` does not capture yet).

- [ ] **Step 3: Write the implementation**

In `src/b2t/api/jobs.py`, change the start of the run and the `updates` branch of the stream loop. Replace this existing block:

```python
    state = dict(seed)
    store.update(job_id, status="running")
    logger.info("job {} running: {} -> {}", job_id, input_dir, output_dir)
    try:
        graph = build_graph(make_client())
        for mode, chunk in graph.stream(seed, stream_mode=["updates", "debug"]):
            if mode == "debug":
                if chunk.get("type") == "task":
                    node = chunk["payload"]["name"]
                    logger.debug("job {} at node {}", job_id, node)
                    store.update(job_id, current_node=node)
            else:
                for update in chunk.values():
                    state.update(update)
```

with:

```python
    state = dict(seed)
    store.update(job_id, status="running", seed_state=serialize_values(seed))
    logger.info("job {} running: {} -> {}", job_id, input_dir, output_dir)
    try:
        graph = build_graph(make_client())
        for mode, chunk in graph.stream(seed, stream_mode=["updates", "debug"]):
            if mode == "debug":
                if chunk.get("type") == "task":
                    node = chunk["payload"]["name"]
                    logger.debug("job {} at node {}", job_id, node)
                    store.update(job_id, current_node=node)
            else:
                for node_name, update in chunk.items():
                    state.update(update)
                    store.append_delta(
                        job_id,
                        NodeDelta(node_name, list(update), serialize_values(update)),
                    )
```

Everything after the loop (the summary copy and terminal-status logic) is unchanged.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_api_jobs.py -v`
Expected: PASS (all tests in the file, including the two new ones).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/api/jobs.py tests/test_api_jobs.py
git commit -m "feat: capture per-node state deltas live during a run"
```

---

### Task 4: Schema and JobView field

**Files:**
- Modify: `src/b2t/api/schemas.py` (`NodeStateView`, `JobView`, `to_view`)
- Test: `tests/test_api_schemas.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_api_schemas.py`:

```python
def test_node_state_view_shape():
    from b2t.api.schemas import NodeStateView

    v = NodeStateView(
        node="convert", changed=["typst_source"], state={"compiled": False}
    )
    assert v.node == "convert"
    assert v.changed == ["typst_source"]
    assert v.state["compiled"] is False


def test_to_view_includes_state_nodes():
    from b2t.api.state_view import NodeDelta

    rec = JobRecord(
        id="abc",
        status="running",
        node_deltas=[
            NodeDelta("copy_input", ["work_dir"], {"work_dir": "/w"}),
            NodeDelta("clean_build", ["removed_build_files"], {"removed_build_files": []}),
        ],
    )
    assert to_view(rec).state_nodes == ["copy_input", "clean_build"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_api_schemas.py::test_node_state_view_shape tests/test_api_schemas.py::test_to_view_includes_state_nodes -v`
Expected: FAIL (`NodeStateView` does not exist; `JobView` has no `state_nodes`).

- [ ] **Step 3: Write the implementation**

In `src/b2t/api/schemas.py`:

Add the typing import near the top (after the existing imports):

```python
from typing import Any
```

Add the new view class (place it after `RenderedPromptView`):

```python
class NodeStateView(BaseModel):
    """The accumulated pipeline state after a node ran, with its changes."""

    node: str
    changed: list[str]
    state: dict[str, Any]
```

Add one field to `JobView` (after the `llm_runs` line):

```python
    state_nodes: list[str] = []
```

In `to_view`, add the `state_nodes` argument to the `JobView(...)` construction (after the `llm_runs={...}` block):

```python
        state_nodes=[d.node for d in job.node_deltas],
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_api_schemas.py -v`
Expected: PASS (all tests in the file).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/api/schemas.py tests/test_api_schemas.py
git commit -m "feat: add NodeStateView and state_nodes to the job view"
```

---

### Task 5: State endpoint

**Files:**
- Modify: `src/b2t/api/app.py` (imports + one route)
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_api_app.py` (the file already defines `_client` and `_run_sample`):

```python
def test_node_state_available_after_run():
    client = _client()
    job_id = _run_sample(client)
    body = client.get(f"/api/jobs/{job_id}/state/convert").json()
    assert body["node"] == "convert"
    assert "typst_source" in body["changed"]
    assert "stripped_tex" in body["state"]
    assert "typst_source" in body["state"]


def test_jobview_lists_state_nodes_after_run():
    client = _client()
    job_id = _run_sample(client)
    body = client.get(f"/api/jobs/{job_id}").json()
    assert "convert" in body["state_nodes"]
    assert "copy_input" in body["state_nodes"]


def test_node_state_unknown_job_returns_404():
    assert _client().get("/api/jobs/does-not-exist/state/convert").status_code == 404


def test_node_state_unknown_node_returns_404():
    client = _client()
    job_id = _run_sample(client)
    assert client.get(f"/api/jobs/{job_id}/state/nope").status_code == 404
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_api_app.py::test_node_state_available_after_run tests/test_api_app.py::test_node_state_unknown_node_returns_404 -v`
Expected: FAIL with 404 (route not defined) on the first test, and the unknown-node test will also currently 404 for the wrong reason; both pass only once the route exists.

- [ ] **Step 3: Write the implementation**

In `src/b2t/api/app.py`:

Add `NodeStateView,` to the `from b2t.api.schemas import (...)` list (alphabetical, after `ModelsView,`):

```python
    NodeStateView,
```

Add this import after the `from b2t.api.schemas import (...)` block:

```python
from b2t.api.state_view import fold_snapshot
```

Add this route inside `create_app`, right after the `get_rendered_prompt` route:

```python
    @app.get("/api/jobs/{job_id}/state/{node}", response_model=NodeStateView)
    def get_node_state(job_id: str, node: str):
        """Return the accumulated pipeline state after `node` ran. 404 if absent."""
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="unknown job")
        try:
            changed, snapshot = fold_snapshot(job.seed_state, job.node_deltas, node)
        except KeyError:
            raise HTTPException(status_code=404, detail="node has not run")
        return NodeStateView(node=node, changed=changed, state=snapshot)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_api_app.py -v`
Expected: PASS (all tests in the file, including the four new ones).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/api/app.py tests/test_api_app.py
git commit -m "feat: serve the accumulated state after a node via /state/{node}"
```

---

### Task 6: Frontend inspector

**Files:**
- Modify: `src/b2t/api/static/index.html`
- Modify: `src/b2t/api/static/app.js`
- Modify: `src/b2t/api/static/style.css`
- Test: `tests/test_api_app.py` (the served HTML carries the container)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_api_app.py`:

```python
def test_index_has_state_inspector_container():
    text = _client().get("/").text
    assert '<div id="state-inspector"' in text
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_api_app.py::test_index_has_state_inspector_container -v`
Expected: FAIL (`assert '<div id="state-inspector"' in text`).

- [ ] **Step 3: Add the container to `index.html`**

In `src/b2t/api/static/index.html`, inside the `<section class="status">`, add the inspector container directly after the `#graph` div. Replace:

```html
      <div id="graph"></div>
      <div id="llm-nodes"></div>
```

with:

```html
      <div id="graph"></div>
      <div id="state-inspector"></div>
      <div id="llm-nodes"></div>
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_api_app.py::test_index_has_state_inspector_container -v`
Expected: PASS.

- [ ] **Step 5: Add the inspector logic to `app.js`**

In `src/b2t/api/static/app.js`:

Add a module-level variable next to the other `let` declarations near the top (after `let models = [];`):

```javascript
let stateNodes = [];     // node names that have a captured snapshot
```

In `loadGraph()`, attach a click handler when each box is created. Inside the `data.nodes.forEach((n, i) => { ... })` body, after `map[n.name] = box;`, add:

```javascript
    box.addEventListener("click", () => inspectNode(n.name));
```

Add these three functions at the end of the file, just before the final `loadGraph();` / `loadLLMNodes();` calls:

```javascript
// ----- per-node state inspector -----
const STATE_PREVIEW = 500;

function markInspectable() {
  if (!graphNodes) return;
  for (const [name, box] of Object.entries(graphNodes)) {
    box.classList.toggle("inspectable", stateNodes.includes(name));
  }
}

async function inspectNode(node) {
  if (!currentJobId || !stateNodes.includes(node)) return;
  if (graphNodes) {
    for (const box of Object.values(graphNodes)) box.classList.remove("selected");
    if (graphNodes[node]) graphNodes[node].classList.add("selected");
  }
  const panel = $("state-inspector");
  panel.textContent = "loading...";
  try {
    const r = await fetch(`/api/jobs/${currentJobId}/state/${node}`);
    if (!r.ok) throw new Error();
    renderInspector(panel, await r.json());
  } catch (e) {
    panel.textContent = "(failed to load state)";
  }
}

function renderInspector(panel, data) {
  panel.innerHTML = "";
  const title = document.createElement("div");
  title.className = "inspector-title";
  title.textContent = `State after: ${data.node}`;
  const changed = document.createElement("div");
  changed.className = "inspector-changed";
  changed.textContent = "changed: " + (data.changed.join(", ") || "(nothing)");
  panel.append(title, changed);
  for (const key of Object.keys(data.state).sort()) {
    const row = document.createElement("div");
    row.className = "state-field" + (data.changed.includes(key) ? " is-changed" : "");
    const k = document.createElement("span");
    k.className = "state-key";
    k.textContent = key + ": ";
    row.append(k, renderValue(data.state[key]));
    panel.appendChild(row);
  }
}

function renderValue(v) {
  if (typeof v === "string") return renderString(v);
  if (Array.isArray(v)) {
    const span = document.createElement("span");
    span.textContent = JSON.stringify(v);
    return span;
  }
  if (v && typeof v === "object") {
    const box = document.createElement("div");
    box.className = "state-object";
    for (const [kk, vv] of Object.entries(v)) {
      const row = document.createElement("div");
      row.className = "state-subfield";
      const k = document.createElement("span");
      k.className = "state-key";
      k.textContent = kk + ": ";
      row.append(k, renderValue(vv));
      box.appendChild(row);
    }
    return box;
  }
  const span = document.createElement("span");
  span.textContent = String(v);
  return span;
}

function renderString(s) {
  const span = document.createElement("span");
  span.className = "state-string";
  if (s.length <= STATE_PREVIEW) {
    span.textContent = s;
    return span;
  }
  const body = document.createElement("span");
  body.textContent = s.slice(0, STATE_PREVIEW);
  const meta = document.createElement("span");
  meta.className = "state-meta";
  meta.textContent = ` ... (${s.length} chars) `;
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "expand";
  btn.textContent = "expand";
  let expanded = false;
  btn.addEventListener("click", () => {
    expanded = !expanded;
    body.textContent = expanded ? s : s.slice(0, STATE_PREVIEW);
    meta.textContent = expanded ? ` (${s.length} chars) ` : ` ... (${s.length} chars) `;
    btn.textContent = expanded ? "collapse" : "expand";
  });
  span.append(body, meta, btn);
  return span;
}
```

In `poll(id)`, make the job id available during the run (so finished nodes are clickable mid-run) and refresh inspectability. Replace the body of `poll`:

```javascript
async function poll(id) {
  const res = await fetch(`/api/jobs/${id}`);
  const job = await res.json();
  setBadge(job.status);
  highlightGraph(job.current_node, job.status);
  if (TERMINAL.includes(job.status)) finish(id, job);
  else setTimeout(() => poll(id), 1000);
}
```

with:

```javascript
async function poll(id) {
  currentJobId = id;
  const res = await fetch(`/api/jobs/${id}`);
  const job = await res.json();
  setBadge(job.status);
  highlightGraph(job.current_node, job.status);
  stateNodes = job.state_nodes || [];
  markInspectable();
  if (TERMINAL.includes(job.status)) finish(id, job);
  else setTimeout(() => poll(id), 1000);
}
```

- [ ] **Step 6: Add the inspector styles to `style.css`**

Append to `src/b2t/api/static/style.css`:

```css
/* state inspector */
#state-inspector { margin-top: 0.8rem; }
#state-inspector:empty { display: none; }
#graph .node.inspectable { cursor: pointer; }
#graph .node.selected { outline: 2px solid #cc3399; outline-offset: 1px; }
.inspector-title { font-weight: 600; font-size: 0.9rem; margin-bottom: 0.3rem; }
.inspector-changed { font-size: 0.8rem; color: #cc3399; margin-bottom: 0.5rem; }
.state-field { font-family: ui-monospace, monospace; font-size: 0.8rem; padding: 0.15rem 0; border-bottom: 1px solid #efeaf3; }
.state-field.is-changed { background: #fff4fb; }
.state-key { color: #6b5b95; }
.state-string { white-space: pre-wrap; word-break: break-word; }
.state-object, .state-subfield { margin-left: 1rem; }
.state-meta { color: #888; }
button.expand { background: #6b5b95; padding: 0.05rem 0.4rem; font-size: 0.7rem; }
```

- [ ] **Step 7: Manual verification in the browser**

The JS and CSS are not unit-tested; verify by hand. Start the UI:

```bash
uv run uvicorn b2t.api.app:app --reload
```

Open http://127.0.0.1:8000, tick "use fake converter (offline)", click "Use sample deck", and wait for it to finish. Then:
- Confirm pipeline nodes show a pointer cursor (they are inspectable).
- Click `convert`: the panel shows `State after: convert`, a `changed: ...` line including `typst_source`, and fields including `stripped_tex` and `typst_source` with an `expand` toggle on the long ones.
- Click `flatten`: `changed` lists `flattened_tex`/`included_tex`/`image_files`; expanding `flattened_tex` shows the full LaTeX.
- Confirm clicking the selected node draws the pink outline and that `expand`/`collapse` toggles the full text.

- [ ] **Step 8: Run the whole suite**

Run: `uv run pytest -v`
Expected: PASS (integration tests run if the `typst` binary is installed, otherwise skip).

- [ ] **Step 9: Commit**

```bash
git add src/b2t/api/static/index.html src/b2t/api/static/app.js src/b2t/api/static/style.css tests/test_api_app.py
git commit -m "feat: click a strip node to inspect its pipeline state"
```

---

## Self-review notes (for the implementer)

- The capture point is inside the stream loop on purpose: a node that raises has no `updates` event, so only finished nodes get a delta. `test_run_job_keeps_partial_deltas_on_failure` locks this in.
- `state_nodes` is the only addition to the per-second poll; snapshot bodies are served only by `/state/{node}` on click. Do not add snapshot bodies to `JobView`.
- `fold_snapshot` raises `KeyError`, which the endpoint maps to 404; this is what `test_node_state_unknown_node_returns_404` checks.
- Field order in the inspector is sorted alphabetically (`Object.keys(...).sort()`), so the view is stable across runs.
- No new dependencies. `to_jsonsafe` relies only on the stdlib and Pydantic's `model_dump`.
```
