# Graph-Rendered Per-Node Prompt Selection and Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Mermaid-rendered pipeline graph in the testing UI with a frontend-rendered strip whose LLM nodes carry inline model and prompt-version pickers plus a read-only prompt preview (template and as-run rendered).

**Architecture:** Backend captures each LLM node's exact rendered prompt during a run and serves it lazily; `/api/graph` returns structured topology derived from the real compiled graph; two new lazy endpoints serve template and rendered prompt content. The frontend renders the pipeline strip and per-node control cards itself, dropping Mermaid.

**Tech Stack:** Python 3.12, FastAPI, LangGraph, Pydantic, pytest (run via `uv run`); vanilla JS/CSS frontend.

Spec: `docs/superpowers/specs/2026-06-10-graph-prompt-preview-design.md`.

**Conventions:** Run everything with `uv run`. No emojis, no em or en dashes in code or commits. Conventional-commit messages. One small deviation from the spec for less churn: the LLM control cards reuse the existing `#llm-nodes` container id (moved beneath the strip) instead of a new `#llm-cards` id.

---

## File Structure

Backend:
- `src/b2t/state.py` (modify): add `RenderedPrompt` model and `llm_rendered` field.
- `src/b2t/nodes/_llm.py` (modify): `run_prompt` returns the rendered prompt too.
- `src/b2t/nodes/convert.py` (modify): merge `llm_rendered` into the node update.
- `src/b2t/api/jobs.py` (modify): `JobRecord.llm_rendered` and copy it in `run_job`.
- `src/b2t/api/schemas.py` (modify): restructure `GraphView`; add `GraphNode`, `GraphEdge`, `PromptContentView`, `RenderedPromptView`.
- `src/b2t/api/app.py` (modify): restructure `/api/graph`; add `/api/prompts/{node}/{version}` and `/api/jobs/{job_id}/prompt/{node}`.

Frontend:
- `src/b2t/api/static/index.html` (modify): remove Mermaid, move `#llm-nodes` beneath `#graph`.
- `src/b2t/api/static/app.js` (rewrite): custom strip, control cards, inline preview.
- `src/b2t/api/static/style.css` (rewrite): strip, card, and preview styles.

Tests:
- `tests/test_state.py`, `tests/test_llm_node.py`, `tests/test_nodes.py`, `tests/test_api_jobs.py`, `tests/test_api_app.py` (modify).

---

## Task 1: State carries the rendered prompt

**Files:**
- Modify: `src/b2t/state.py`
- Test: `tests/test_state.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_state.py`:

```python
def test_llm_rendered_defaults_empty():
    state = PipelineState(input_dir=Path("in"), output_dir=Path("out"))
    assert state.llm_rendered == {}


def test_llm_rendered_coerces_nested_dicts():
    state = PipelineState(
        input_dir=Path("in"),
        output_dir=Path("out"),
        llm_rendered={"convert": {"system": "S", "user": "U"}},
    )
    assert state.llm_rendered["convert"].system == "S"
    assert state.llm_rendered["convert"].user == "U"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_state.py -v`
Expected: FAIL (`PipelineState` has no field `llm_rendered`).

- [ ] **Step 3: Add the model and field**

In `src/b2t/state.py`, add a new model after `NodeRun`:

```python
class RenderedPrompt(BaseModel):
    """The exact system and user message an LLM node sent, for preview."""

    system: str
    user: str
```

In `PipelineState`, add the field right below `llm_runs`:

```python
    # the exact rendered prompt each LLM node sent (large; never enters JobView)
    llm_rendered: dict[str, RenderedPrompt] = Field(default_factory=dict)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_state.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/state.py tests/test_state.py
git commit -m "feat: add RenderedPrompt and llm_rendered to pipeline state"
```

---

## Task 2: run_prompt returns the rendered prompt

**Files:**
- Modify: `src/b2t/nodes/_llm.py`
- Test: `tests/test_llm_node.py`

- [ ] **Step 1: Update the existing tests to expect the 3-tuple**

Replace the three test functions in `tests/test_llm_node.py` with these (the import line gains `RenderedPrompt` is not needed; only unpacking changes):

```python
def test_run_prompt_uses_defaults_and_returns_run(monkeypatch):
    monkeypatch.delenv("B2T_MODEL", raising=False)
    out, run, rendered = run_prompt(_state(), "convert", FakeClient("OUT"), _VALUES)
    assert out == "OUT"
    assert run == NodeRun(model=DEFAULT_MODEL, prompt_version="v1")
    assert "SRC" in rendered.user
    assert rendered.system


def test_run_prompt_honors_choice_model_and_renders_user(monkeypatch):
    monkeypatch.delenv("B2T_MODEL", raising=False)
    state = _state(llm_choices={"convert": NodeChoice(model="x/y", prompt_version="v1")})
    captured = {}

    class Spy:
        def complete(self, system, user, model):
            captured["model"] = model
            captured["user"] = user
            return "OK"

    out, run, rendered = run_prompt(state, "convert", Spy(), _VALUES)
    assert captured["model"] == "x/y"
    assert "SRC" in captured["user"]
    assert run.model == "x/y"
    assert run.prompt_version == "v1"
    assert rendered.user == captured["user"]


def test_run_prompt_falls_back_to_b2t_model_env(monkeypatch):
    monkeypatch.setenv("B2T_MODEL", "env/model")
    _, run, _ = run_prompt(_state(), "convert", FakeClient("OUT"), _VALUES)
    assert run.model == "env/model"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_llm_node.py -v`
Expected: FAIL (`run_prompt` returns a 2-tuple, cannot unpack into 3).

- [ ] **Step 3: Update run_prompt**

In `src/b2t/nodes/_llm.py`, change the import and the function. Import line:

```python
from b2t.state import NodeChoice, NodeRun, PipelineState, RenderedPrompt
```

Change the return type and body of `run_prompt`:

```python
def run_prompt(
    state: PipelineState,
    node_name: str,
    client: LLMClient,
    values: dict[str, str],
) -> tuple[str, NodeRun, RenderedPrompt]:
    """Resolve the node's selection, render its prompt, and call the client.

    Returns:
        The model output, a NodeRun recording the model and version used, and a
        RenderedPrompt holding the exact system and user message sent.
    """
    choice = state.llm_choices.get(node_name) or NodeChoice()
    model = choice.model or os.getenv("B2T_MODEL") or DEFAULT_MODEL
    version = choice.prompt_version or prompts.default_version(node_name)
    pv = prompts.load(node_name, version)
    user = prompts.render(pv.user_template, values)
    output = client.complete(pv.system, user, model)
    run = NodeRun(model=model, prompt_version=version)
    rendered = RenderedPrompt(system=pv.system, user=user)
    return output, run, rendered
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_llm_node.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/nodes/_llm.py tests/test_llm_node.py
git commit -m "feat: run_prompt returns the rendered prompt for preview"
```

---

## Task 3: convert_node records the rendered prompt

**Files:**
- Modify: `src/b2t/nodes/convert.py`
- Test: `tests/test_nodes.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_nodes.py`:

```python
def test_convert_node_records_rendered_prompt():
    from b2t.llm import FakeClient
    from b2t.nodes.convert import convert_node

    update = convert_node(_state(stripped_tex="MYSOURCE"), client=FakeClient("= ok\n"))
    assert "MYSOURCE" in update["llm_rendered"]["convert"].user
    assert update["llm_rendered"]["convert"].system
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_nodes.py::test_convert_node_records_rendered_prompt -v`
Expected: FAIL (`KeyError: 'llm_rendered'`).

- [ ] **Step 3: Update convert_node**

In `src/b2t/nodes/convert.py`, change the unpacking and the returned dict:

```python
    output, run, rendered = run_prompt(
        state,
        "convert",
        client,
        {"reference": reference, "guides": guides, "source": state.stripped_tex},
    )
    logger.info("conversion returned {} chars of Typst", len(output))
    return {
        "typst_source": strip_code_fence(output),
        "llm_runs": {**state.llm_runs, "convert": run},
        "llm_rendered": {**state.llm_rendered, "convert": rendered},
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_nodes.py -v`
Expected: PASS (including the existing `test_convert_node_records_provenance`).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/nodes/convert.py tests/test_nodes.py
git commit -m "feat: convert node records its rendered prompt"
```

---

## Task 4: Job record carries the rendered prompt

**Files:**
- Modify: `src/b2t/api/jobs.py`
- Test: `tests/test_api_jobs.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_api_jobs.py`:

```python
def test_run_job_records_rendered_prompt(tmp_path):
    store = JobStore()
    out = tmp_path / "out"
    job = store.create(input_dir=SAMPLE_DECK, output_dir=out)
    run_job(store, job.id, SAMPLE_DECK, out, lambda: FakeClient("= Hi\n"))
    rec = store.get(job.id)
    assert "convert" in rec.llm_rendered
    assert "Reference Touying presentation" in rec.llm_rendered["convert"]["user"]
    assert rec.llm_rendered["convert"]["system"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_api_jobs.py::test_run_job_records_rendered_prompt -v`
Expected: FAIL (`JobRecord` has no attribute `llm_rendered`).

- [ ] **Step 3: Add the field and populate it**

In `src/b2t/api/jobs.py`, add to `JobRecord` (right below the existing `llm_runs` field):

```python
    llm_rendered: dict[str, dict] = field(default_factory=dict)
```

In `run_job`, after the line `runs = state.get("llm_runs", {})`, add:

```python
    rendered = state.get("llm_rendered", {})
```

Then add this keyword argument to the existing `store.update(job_id, ...)` call that sets `main_tex`, `included_tex`, `images`, `has_typst`, `typst_path`, and `llm_runs`:

```python
        llm_rendered={
            node: {"system": r.system, "user": r.user}
            for node, r in rendered.items()
        },
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_api_jobs.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/api/jobs.py tests/test_api_jobs.py
git commit -m "feat: store each node's rendered prompt on the job record"
```

---

## Task 5: Structured topology from /api/graph

**Files:**
- Modify: `src/b2t/api/schemas.py`
- Modify: `src/b2t/api/app.py`
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Replace the Mermaid graph test**

In `tests/test_api_app.py`, replace `test_graph_endpoint_returns_mermaid` with:

```python
def test_graph_endpoint_returns_structured_topology():
    body = _client().get("/api/graph").json()
    names = [n["name"] for n in body["nodes"]]
    assert "copy_input" in names and "convert" in names and "compile" in names
    assert "__start__" not in names and "__end__" not in names
    convert = next(n for n in body["nodes"] if n["name"] == "convert")
    assert convert["is_llm"] is True
    copy = next(n for n in body["nodes"] if n["name"] == "copy_input")
    assert copy["is_llm"] is False
    assert body["edges"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_api_app.py::test_graph_endpoint_returns_structured_topology -v`
Expected: FAIL (`KeyError: 'nodes'`; the endpoint still returns `{mermaid}`).

- [ ] **Step 3: Restructure the schema**

In `src/b2t/api/schemas.py`, replace the `GraphView` class with:

```python
class GraphNode(BaseModel):
    """One pipeline node: its name and whether it is an LLM node."""

    name: str
    is_llm: bool


class GraphEdge(BaseModel):
    """A directed edge between two pipeline nodes."""

    source: str
    target: str


class GraphView(BaseModel):
    """The pipeline topology: nodes (with is_llm) and directed edges."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
```

- [ ] **Step 4: Restructure the endpoint**

In `src/b2t/api/app.py`, update the schema import block to add `GraphNode` and `GraphEdge`:

```python
from b2t.api.schemas import (
    GraphEdge,
    GraphNode,
    GraphView,
    JobCreated,
    JobView,
    LLMNodeView,
    LLMNodesView,
    ModelOption,
    ModelsView,
    SaveRequest,
    SaveResult,
    VersionOption,
    to_view,
)
```

Replace the `get_graph` handler body with:

```python
    @app.get("/api/graph", response_model=GraphView)
    def get_graph():
        """Return the pipeline topology (nodes with is_llm, plus edges).

        Derived from the real compiled graph, so it cannot drift from the
        pipeline; a node is an LLM node when its name is in the prompt registry.
        """
        graph = build_graph(FakeClient()).get_graph()
        llm = set(prompts.list_nodes())
        skip = {"__start__", "__end__"}
        nodes = [
            GraphNode(name=name, is_llm=name in llm)
            for name in graph.nodes
            if name not in skip
        ]
        edges = [
            GraphEdge(source=e.source, target=e.target)
            for e in graph.edges
            if e.source not in skip and e.target not in skip
        ]
        return GraphView(nodes=nodes, edges=edges)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_api_app.py::test_graph_endpoint_returns_structured_topology -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/b2t/api/schemas.py src/b2t/api/app.py tests/test_api_app.py
git commit -m "feat: serve structured pipeline topology from /api/graph"
```

---

## Task 6: Template content endpoint

**Files:**
- Modify: `src/b2t/api/schemas.py`
- Modify: `src/b2t/api/app.py`
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_api_app.py`:

```python
def test_prompt_content_endpoint_returns_template():
    body = _client().get("/api/prompts/convert/v1").json()
    assert body["node"] == "convert"
    assert body["version"] == "v1"
    assert "You convert LaTeX Beamer" in body["system"]
    assert "{{source}}" in body["user_template"]


def test_prompt_content_unknown_node_returns_404():
    assert _client().get("/api/prompts/nope/v1").status_code == 404


def test_prompt_content_unknown_version_returns_404():
    assert _client().get("/api/prompts/convert/v999").status_code == 404
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_api_app.py -k prompt_content -v`
Expected: FAIL (route not found, 404 with a different body / the success case fails).

- [ ] **Step 3: Add the schema**

In `src/b2t/api/schemas.py`, add:

```python
class PromptContentView(BaseModel):
    """A prompt version's raw content for the template preview."""

    node: str
    version: str
    description: str
    system: str
    user_template: str
```

- [ ] **Step 4: Add the endpoint**

In `src/b2t/api/app.py`, add `PromptContentView` to the schema import block, then add this handler next to `get_llm_nodes` (inside `create_app`):

```python
    @app.get("/api/prompts/{node}/{version}", response_model=PromptContentView)
    def get_prompt_content(node: str, version: str):
        """Return a prompt version's system and user_template (read-only preview)."""
        if node not in prompts.list_nodes():
            raise HTTPException(status_code=404, detail="unknown LLM node")
        if version not in prompts.list_versions(node):
            raise HTTPException(status_code=404, detail="unknown prompt version")
        pv = prompts.load(node, version)
        return PromptContentView(
            node=node,
            version=version,
            description=pv.description,
            system=pv.system,
            user_template=pv.user_template,
        )
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_api_app.py -k prompt_content -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/b2t/api/schemas.py src/b2t/api/app.py tests/test_api_app.py
git commit -m "feat: serve prompt template content for preview"
```

---

## Task 7: Rendered prompt endpoint

**Files:**
- Modify: `src/b2t/api/schemas.py`
- Modify: `src/b2t/api/app.py`
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_api_app.py`:

```python
def test_rendered_prompt_available_after_run():
    client = _client()
    job_id = _run_sample(client)
    body = client.get(f"/api/jobs/{job_id}/prompt/convert").json()
    assert body["prompt_version"] == "v1"
    assert "You convert LaTeX Beamer" in body["system"]
    assert "Reference Touying presentation" in body["user"]


def test_rendered_prompt_unknown_job_returns_404():
    assert _client().get("/api/jobs/does-not-exist/prompt/convert").status_code == 404


def test_rendered_prompt_unknown_node_after_run_returns_404():
    client = _client()
    job_id = _run_sample(client)
    assert client.get(f"/api/jobs/{job_id}/prompt/nope").status_code == 404
```

(`_run_sample` already exists in this file and runs the sample deck with the fake client; the convert node runs before compile, so the rendered prompt exists even without the typst binary.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_api_app.py -k rendered_prompt -v`
Expected: FAIL (route not found).

- [ ] **Step 3: Add the schema**

In `src/b2t/api/schemas.py`, add:

```python
class RenderedPromptView(BaseModel):
    """The exact prompt an LLM node sent on the most recent run."""

    node: str
    model: str
    prompt_version: str
    system: str
    user: str
```

- [ ] **Step 4: Add the endpoint**

In `src/b2t/api/app.py`, add `RenderedPromptView` to the schema import block, then add this handler next to the other `/api/jobs/{job_id}/...` routes (inside `create_app`):

```python
    @app.get("/api/jobs/{job_id}/prompt/{node}", response_model=RenderedPromptView)
    def get_rendered_prompt(job_id: str, node: str):
        """Return the exact prompt a node sent on this job's run. 404 if absent."""
        job = jobs.get(job_id)
        if job is None or node not in job.llm_rendered:
            raise HTTPException(status_code=404, detail="no rendered prompt")
        rendered = job.llm_rendered[node]
        run = job.llm_runs.get(node, {})
        return RenderedPromptView(
            node=node,
            model=run.get("model", ""),
            prompt_version=run.get("prompt_version", ""),
            system=rendered["system"],
            user=rendered["user"],
        )
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_api_app.py -k rendered_prompt -v`
Expected: PASS.

- [ ] **Step 6: Run the whole backend suite**

Run: `uv run pytest -q`
Expected: PASS (integration tests skip if the typst binary is absent).

- [ ] **Step 7: Commit**

```bash
git add src/b2t/api/schemas.py src/b2t/api/app.py tests/test_api_app.py
git commit -m "feat: serve each node's as-run rendered prompt"
```

---

## Task 8: index.html drops Mermaid and moves the LLM controls

**Files:**
- Modify: `src/b2t/api/static/index.html`
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Update the index-content tests**

In `tests/test_api_app.py`, replace `test_index_has_graph_container` with:

```python
def test_index_has_graph_container():
    text = _client().get("/").text
    assert '<div id="graph"' in text
    assert "mermaid" not in text.lower()
```

(`test_index_has_llm_nodes_container` stays as-is; the `#llm-nodes` div still exists, just moved.)

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_api_app.py::test_index_has_graph_container -v`
Expected: FAIL (the page still imports Mermaid, so "mermaid" is present).

- [ ] **Step 3: Edit index.html**

In `src/b2t/api/static/index.html`, remove the `<div id="llm-nodes"></div>` line from the `submit` section.

Change the `status` section to place the LLM controls beneath the graph:

```html
    <section class="status">
      <span id="badge" class="badge">idle</span>
      <div id="graph"></div>
      <div id="llm-nodes"></div>
      <div id="provenance"></div>
    </section>
```

Remove the Mermaid module script block entirely (the `<script type="module"> ... import mermaid ... dispatchEvent(new Event("mermaid-ready")) ... </script>` block). Leave the two CodeMirror `<script>` tags and the final `<script src="/app.js"></script>` in place.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_api_app.py -k "index_has" -v`
Expected: PASS (both `test_index_has_graph_container` and `test_index_has_llm_nodes_container`).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/api/static/index.html tests/test_api_app.py
git commit -m "feat: drop mermaid and move llm controls beneath the graph"
```

---

## Task 9: app.js renders the strip, cards, and preview

**Files:**
- Rewrite: `src/b2t/api/static/app.js`

This file has no automated tests in the project; it is verified manually in Task 11. Replace the entire file with the content below.

- [ ] **Step 1: Replace app.js**

Write `src/b2t/api/static/app.js` with exactly:

```javascript
const TERMINAL = ["succeeded", "compile_failed", "failed"];
const $ = (id) => document.getElementById(id);

let currentJobId = null;
let editor = null;
let graphNodes = null;   // node name -> strip element
let nodeOrder = [];      // pipeline node order from /api/graph
let llmNodes = [];       // from /api/llm-nodes
let models = [];         // from /api/models

if (window.CodeMirror) {
  CodeMirror.defineSimpleMode("typst", {
    start: [
      { regex: /\/\/.*/, token: "comment" },
      { regex: /\/\*/, token: "comment", next: "comment" },
      { regex: /"(?:[^\\"]|\\.)*"/, token: "string" },
      { regex: /\$[^$]*\$/, token: "string-2" },
      { regex: /^\s*=+.*/, token: "header" },
      { regex: /#(?:let|set|show|import|include)\b/, token: "keyword" },
      { regex: /#[A-Za-z_][\w.-]*/, token: "variable-2" },
    ],
    comment: [
      { regex: /.*?\*\//, token: "comment", next: "start" },
      { regex: /.*/, token: "comment" },
    ],
    meta: { lineComment: "//" },
  });
  editor = CodeMirror.fromTextArea($("typ"), {
    mode: "typst",
    theme: "material-darker",
    lineNumbers: true,
    lineWrapping: true,
  });
}

function getSource() {
  return editor ? editor.getValue() : $("typ").value;
}

function setSource(text) {
  if (editor) editor.setValue(text);
  else $("typ").value = text;
}

// ----- pipeline strip (custom-rendered, replaces mermaid) -----
async function loadGraph() {
  let data;
  try {
    data = await (await fetch("/api/graph")).json();
  } catch (e) {
    return; // leave graphNodes null; highlightGraph uses the text fallback
  }
  nodeOrder = data.nodes.map((n) => n.name);
  const strip = $("graph");
  strip.innerHTML = "";
  const map = {};
  data.nodes.forEach((n, i) => {
    const box = document.createElement("div");
    box.className = "node" + (n.is_llm ? " llm" : "");
    box.dataset.node = n.name;
    box.textContent = n.name;
    strip.appendChild(box);
    map[n.name] = box;
    if (i < data.nodes.length - 1) {
      const arrow = document.createElement("span");
      arrow.className = "arrow";
      arrow.textContent = "→";
      strip.appendChild(arrow);
    }
  });
  graphNodes = map;
  highlightGraph(null, "idle");
}

function highlightGraph(currentNode, status) {
  if (!graphNodes) {
    $("graph").textContent = currentNode ? `Stage: ${currentNode} (${status})` : "";
    return;
  }
  const idx = nodeOrder.indexOf(currentNode);
  const allDone = status === "succeeded";
  nodeOrder.forEach((name, i) => {
    const g = graphNodes[name];
    if (!g) return;
    g.classList.remove("done", "active", "pending");
    if (allDone || (idx >= 0 && i < idx)) g.classList.add("done");
    else if (idx === i) g.classList.add(status === "running" ? "active" : "done");
    else g.classList.add("pending");
  });
}

// ----- LLM node cards with inline prompt preview -----
async function loadLLMNodes() {
  const container = $("llm-nodes");
  container.innerHTML = "";
  try {
    models = (await (await fetch("/api/models")).json()).models;
    llmNodes = (await (await fetch("/api/llm-nodes")).json()).nodes;
  } catch (e) {
    return; // leave empty; submitting with no choices keeps server defaults
  }
  for (const node of llmNodes) container.appendChild(buildCard(node));
}

function buildCard(node) {
  const card = document.createElement("div");
  card.className = "llm-card";

  const title = document.createElement("div");
  title.className = "llm-card-title";
  title.textContent = node.node;
  card.appendChild(title);

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

  const viewBtn = document.createElement("button");
  viewBtn.type = "button";
  viewBtn.className = "view-prompt";
  viewBtn.textContent = "view prompt";

  const controls = document.createElement("div");
  controls.className = "llm-controls";
  controls.append("model ", modelSel, " version ", verSel, viewBtn);
  card.appendChild(controls);

  const preview = buildPreview(node.node, () => verSel.value);
  card.appendChild(preview.wrap);

  viewBtn.addEventListener("click", () => {
    const open = preview.wrap.hidden;
    preview.toggle(open);
    viewBtn.textContent = open ? "hide prompt" : "view prompt";
  });
  verSel.addEventListener("change", () => preview.onVersionChange());

  return card;
}

function buildPreview(nodeName, getVersion) {
  const wrap = document.createElement("div");
  wrap.className = "prompt-preview";
  wrap.hidden = true;

  const tabs = document.createElement("div");
  tabs.className = "preview-tabs";
  const tplTab = document.createElement("button");
  tplTab.type = "button";
  tplTab.textContent = "template";
  tplTab.className = "active";
  const rndTab = document.createElement("button");
  rndTab.type = "button";
  rndTab.textContent = "rendered";
  tabs.append(tplTab, rndTab);

  const note = document.createElement("div");
  note.className = "preview-note";
  const body = document.createElement("pre");
  body.className = "preview-body";

  wrap.append(tabs, note, body);

  let view = "template";

  async function showTemplate() {
    note.textContent = "";
    body.textContent = "loading...";
    try {
      const r = await fetch(`/api/prompts/${nodeName}/${getVersion()}`);
      if (!r.ok) throw new Error();
      const d = await r.json();
      body.textContent = `# system\n${d.system}\n\n# user_template\n${d.user_template}`;
    } catch (e) {
      body.textContent = "(failed to load prompt)";
    }
  }

  async function showRendered() {
    note.textContent = "";
    body.textContent = "loading...";
    if (!currentJobId) {
      note.textContent = "run the pipeline to see the rendered prompt";
      body.textContent = "";
      return;
    }
    try {
      const r = await fetch(`/api/jobs/${currentJobId}/prompt/${nodeName}`);
      if (!r.ok) throw new Error();
      const d = await r.json();
      note.textContent = `as run: ${d.model}, ${d.prompt_version}`;
      body.textContent = `# system\n${d.system}\n\n# user\n${d.user}`;
    } catch (e) {
      note.textContent = "run the pipeline to see the rendered prompt";
      body.textContent = "";
    }
  }

  function refresh() {
    if (view === "template") showTemplate();
    else showRendered();
  }

  tplTab.addEventListener("click", () => {
    view = "template";
    tplTab.classList.add("active");
    rndTab.classList.remove("active");
    refresh();
  });
  rndTab.addEventListener("click", () => {
    view = "rendered";
    rndTab.classList.add("active");
    tplTab.classList.remove("active");
    refresh();
  });

  return {
    wrap,
    toggle: (open) => {
      wrap.hidden = !open;
      if (open) refresh();
    },
    onVersionChange: () => {
      if (!wrap.hidden && view === "template") refresh();
    },
  };
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

function commonFields(fd) {
  fd.append("use_fake", $("use-fake").checked ? "true" : "false");
  fd.append("choices", JSON.stringify(collectChoices()));
  return fd;
}

function setBadge(status) {
  const badge = $("badge");
  badge.textContent = status;
  badge.className = "badge " + status;
}

function setBusy(busy) {
  $("run").disabled = busy;
  $("run-sample").disabled = busy;
}

function refreshPdf(id, hasPdf) {
  $("pdf").src = hasPdf ? `/api/jobs/${id}/pdf?t=${Date.now()}` : "about:blank";
}

async function finish(id, job) {
  setBusy(false);
  currentJobId = id;
  const typ = await fetch(`/api/jobs/${id}/typ`);
  setSource(typ.ok ? await typ.text() : "");
  refreshPdf(id, job.has_pdf);
  $("error").textContent = job.error || "(none)";
  $("save").disabled = false;
  $("download").disabled = false;
  const prov = job.llm_runs || {};
  $("provenance").textContent = Object.keys(prov).length
    ? "Ran: " + Object.entries(prov)
        .map(([n, r]) => `${n} (${r.model}, ${r.prompt_version})`)
        .join("; ")
    : "";
}

async function poll(id) {
  const res = await fetch(`/api/jobs/${id}`);
  const job = await res.json();
  setBadge(job.status);
  highlightGraph(job.current_node, job.status);
  if (TERMINAL.includes(job.status)) finish(id, job);
  else setTimeout(() => poll(id), 1000);
}

async function start(url, fd) {
  setBusy(true);
  $("save").disabled = true;
  $("download").disabled = true;
  setSource("");
  $("error").textContent = "(none)";
  $("pdf").src = "about:blank";
  const res = await fetch(url, { method: "POST", body: fd });
  const data = await res.json();
  poll(data.job_id);
}

$("run").addEventListener("click", () => {
  const files = $("folder").files;
  if (!files.length) { alert("Pick a deck folder first."); return; }
  const fd = new FormData();
  for (const f of files) fd.append("files", f, f.webkitRelativePath);
  start("/api/jobs", commonFields(fd));
});

$("run-sample").addEventListener("click", () => {
  start("/api/jobs/sample", commonFields(new FormData()));
});

$("save").addEventListener("click", async () => {
  if (!currentJobId) return;
  $("error").textContent = "(saving...)";
  const res = await fetch(`/api/jobs/${currentJobId}/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source: getSource() }),
  });
  const data = await res.json();
  $("error").textContent = data.error || "(none)";
  refreshPdf(currentJobId, data.ok);
});

$("download").addEventListener("click", () => {
  if (!currentJobId) return;
  window.location = `/api/jobs/${currentJobId}/download`;
});

loadGraph();
loadLLMNodes();
```

- [ ] **Step 2: Sanity-check the page still serves**

Run: `uv run pytest tests/test_api_app.py -k "index_has or serves_index" -v`
Expected: PASS (the HTML structure the page depends on is intact).

- [ ] **Step 3: Commit**

```bash
git add src/b2t/api/static/app.js
git commit -m "feat: render pipeline strip, llm cards, and prompt preview in app.js"
```

---

## Task 10: style.css for the strip, cards, and preview

**Files:**
- Rewrite: `src/b2t/api/static/style.css`

- [ ] **Step 1: Replace style.css**

Write `src/b2t/api/static/style.css` with exactly:

```css
body { font-family: system-ui, sans-serif; margin: 0; background: #faf7fb; color: #222; }
#app { max-width: 900px; margin: 0 auto; padding: 1.5rem; }
h1 { font-size: 1.4rem; }
section { background: #fff; border: 1px solid #e3dbe8; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
.options, .actions { margin-top: 0.6rem; display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; }
button { padding: 0.5rem 0.9rem; border: 0; border-radius: 6px; background: #cc3399; color: #fff; cursor: pointer; }
button:disabled { opacity: 0.5; cursor: default; }
.badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 999px; background: #eee; font-size: 0.85rem; }
.badge.running { background: #ffe9b3; }
.badge.succeeded { background: #bfe9c6; }
.badge.compile_failed, .badge.failed { background: #f2b8b8; }
pre { background: #1e1e26; color: #eee; padding: 0.8rem; border-radius: 6px; overflow: auto; max-height: 320px; }
iframe { width: 100%; height: 480px; border: 1px solid #e3dbe8; border-radius: 6px; background: #fff; }
#typ { width: 100%; min-height: 200px; box-sizing: border-box; }
.CodeMirror { height: 340px; border: 1px solid #e3dbe8; border-radius: 6px; }

/* pipeline strip */
#graph { margin-top: 0.8rem; display: flex; flex-wrap: wrap; gap: 0.3rem; align-items: center; min-height: 1.2rem; }
#graph .node { padding: 0.3rem 0.6rem; border-radius: 6px; border: 1px solid #c7bfd6; background: #e6e1ef; font-size: 0.8rem; }
#graph .node.llm { border-style: dashed; border-color: #cc3399; }
#graph .node.done { background: #57c98a; border-color: #2f9e63; color: #fff; }
#graph .node.active { background: #ffb02e; border-color: #d98600; animation: b2t-pulse 1.1s ease-in-out infinite; }
#graph .node.pending { background: #e6e1ef; border-color: #c7bfd6; }
#graph .arrow { color: #b0a8bf; }
@keyframes b2t-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.65; } }

/* llm node cards */
#llm-nodes { margin-top: 0.8rem; display: flex; flex-direction: column; gap: 0.6rem; }
.llm-card { border: 1px solid #e3dbe8; border-radius: 6px; padding: 0.6rem; }
.llm-card-title { font-weight: 600; font-size: 0.9rem; margin-bottom: 0.4rem; }
.llm-controls { display: flex; gap: 0.4rem; align-items: center; flex-wrap: wrap; }
.view-prompt { background: #6b5b95; }
.prompt-preview { margin-top: 0.6rem; }
.preview-tabs { display: flex; gap: 0.3rem; margin-bottom: 0.3rem; }
.preview-tabs button { background: #eee; color: #333; padding: 0.2rem 0.6rem; font-size: 0.8rem; }
.preview-tabs button.active { background: #cc3399; color: #fff; }
.preview-note { font-size: 0.8rem; color: #555; margin-bottom: 0.3rem; }
.preview-body { max-height: 360px; }

#provenance { margin-top: 0.5rem; font-size: 0.85rem; color: #555; }
```

- [ ] **Step 2: Commit**

```bash
git add src/b2t/api/static/style.css
git commit -m "feat: style the pipeline strip, llm cards, and prompt preview"
```

---

## Task 11: Full verification

**Files:** none (verification only).

- [ ] **Step 1: Run the entire test suite**

Run: `uv run pytest -q`
Expected: all tests pass; integration tests skip if the typst binary is absent.

- [ ] **Step 2: Manual UI check**

Run: `uv run uvicorn b2t.api.app:app` (no `--reload` needed) and open http://127.0.0.1:8000.

Verify:
- The pipeline strip renders all eight nodes left to right with arrows; `convert` is visually marked as an LLM node (dashed pink border).
- A `convert` card appears beneath the strip with a model dropdown, a version dropdown (default `v1` selected), and a "view prompt" button.
- Clicking "view prompt" expands the preview. The "template" tab shows the `system` text and the `user_template` containing literal `{{reference}}`, `{{guides}}`, `{{source}}`. The "rendered" tab shows "run the pipeline to see the rendered prompt" before any run.
- Tick "use fake converter (offline)", click "Use sample deck". The strip highlights nodes amber as they run and green as they finish; the badge ends `succeeded` (or `compile_failed` if no typst binary).
- After the run, the "rendered" tab shows the filled-in prompt labelled "as run: <model>, v1", with the reference deck text and the sample source inlined.
- The generated `main.typ` loads in the editor and the provenance line reads `Ran: convert (<model>, v1)`.

- [ ] **Step 3: Stop the server.**

Press Ctrl+C in the terminal running uvicorn.

---

## Self-Review Notes

- Spec coverage: structured `/api/graph` (Task 5), template endpoint (Task 6), rendered endpoint with run-time capture (Tasks 1-4, 7), custom strip with live highlight (Task 9), LLM cards with inline template/rendered toggle (Tasks 9-10), Mermaid removal (Tasks 8-9), read-only preview (Task 9). All spec sections map to a task.
- Type consistency: `RenderedPrompt{system, user}` (Task 1) is produced by `run_prompt` (Task 2), threaded by `convert_node` (Task 3), flattened to `{system, user}` dicts on `JobRecord.llm_rendered` (Task 4), and read by the rendered endpoint (Task 7). `GraphNode`/`GraphEdge`/`GraphView`, `PromptContentView`, `RenderedPromptView` names match between schema and endpoint tasks.
- No placeholders: every code and test step shows full content.
