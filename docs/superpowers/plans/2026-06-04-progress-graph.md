# LangGraph Progress Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat list of stage rectangles with a rendered Mermaid diagram of the real LangGraph pipeline, highlighting done and current nodes as the job runs.

**Architecture:** A new `GET /api/graph` serves the live graph's Mermaid string (`build_graph(...).get_graph().draw_mermaid()`). The page loads Mermaid 11 as an ES module from a CDN (an inline module sets `window.mermaid` and fires a `mermaid-ready` event), renders the diagram once into a `#graph` container, builds a node-name to SVG-element map, and toggles `done`/`active` classes as `current_node` advances. The conversion pipeline is untouched (read only via `get_graph()`).

**Tech Stack:** Python 3.12, uv, FastAPI, pydantic v2, pytest with FastAPI `TestClient`. Frontend: vanilla JS plus Mermaid 11 (ESM from jsDelivr, verified URL below). No build step.

---

## Conventions for this plan

- Work happens on the current branch `feat/testing-frontend`.
- All commands run from the repo root `d:\projects\b2t` with `uv run ...`. Never use `pip` or `python` directly.
- Every commit message appends the trailer line (after a blank line):
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- No emojis. No em or en dashes in code or docs.
- Do NOT modify the pipeline (`graph.py`, `nodes/`, `state.py`, `latex/`, `typst_runner.py`, `llm.py`) or `jobs.py`. `graph.py` is used only via its existing public `build_graph` and the compiled graph's `get_graph()`.

## Verified CDN URL (Mermaid 11.12.0)

`https://cdn.jsdelivr.net/npm/mermaid@11.12.0/dist/mermaid.esm.min.mjs` was confirmed to be a real ES module with a default export. It is imported, not loaded via a classic `<script>` tag (the cdnjs UMD build for v11 does not cleanly expose `window.mermaid`). No Subresource Integrity is added (consistent with the editor's documented v0 CDN deferral).

## File structure

```
src/b2t/api/schemas.py          # modify: add GraphView
src/b2t/api/app.py              # modify: add GET /api/graph + build_graph import
src/b2t/api/static/index.html   # modify: <ul id="nodes"> -> <div id="graph">; add mermaid module
src/b2t/api/static/app.js       # modify: replace renderNodes with loadGraph + highlightGraph
src/b2t/api/static/style.css    # modify: graph node highlight styles
tests/test_api_app.py           # modify: add /api/graph test and graph-markup test
```

For reference, `app.py` currently imports `from b2t.llm import ConverterLLM, FakeConverter, OpenAIConverter` (so `FakeConverter` is available) but does NOT import `build_graph`. The current `app.js` has a `NODES` array, a `renderNodes(currentNode, status)` function, and a `poll` function that calls `renderNodes(job.current_node, job.status)`. The current `index.html` status section is:

```html
    <section class="status">
      <span id="badge" class="badge">idle</span>
      <ul id="nodes"></ul>
    </section>
```

and the scripts at the end of body are:

```html
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/mode/simple.min.js"></script>
  <script src="/app.js"></script>
```

---

### Task 1: /api/graph endpoint

**Files:**
- Modify: `src/b2t/api/schemas.py`
- Modify: `src/b2t/api/app.py`
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_api_app.py`:

```python
def test_graph_endpoint_returns_mermaid():
    body = _client().get("/api/graph").json()
    assert "graph" in body["mermaid"].lower()
    for name in ("copy_input", "convert", "compile"):
        assert name in body["mermaid"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_app.py::test_graph_endpoint_returns_mermaid -q`
Expected: FAIL (the `/api/graph` route does not exist yet, so the JSON has no `mermaid` key / the route 404s).

- [ ] **Step 3: Add the schema**

In `src/b2t/api/schemas.py`, add this model after the `ModelsView` class (before `def to_view`):

```python
class GraphView(BaseModel):
    mermaid: str
```

- [ ] **Step 4: Add the endpoint and import in app.py**

In `src/b2t/api/app.py`, add this import with the other `b2t` imports (for example just below `from b2t.api.jobs import EXECUTOR, JobStore, run_job`):

```python
from b2t.graph import build_graph
```

Add `GraphView` to the schemas import so it reads:

```python
from b2t.api.schemas import (
    GraphView,
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
    @app.get("/api/graph", response_model=GraphView)
    def get_graph():
        mermaid = build_graph(FakeConverter()).get_graph().draw_mermaid()
        return GraphView(mermaid=mermaid)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_api_app.py -q`
Expected: PASS (the new test plus all existing ones; typst-dependent tests skip when the binary is absent).

- [ ] **Step 6: Commit**

```bash
git add src/b2t/api/schemas.py src/b2t/api/app.py tests/test_api_app.py
git commit -m "feat: serve the langgraph topology as mermaid"
```

---

### Task 2: Render and highlight the graph (frontend)

Replace the rectangle list with a Mermaid-rendered graph that highlights progress. If Mermaid fails to load, a single text line is the fallback.

**Files:**
- Modify: `src/b2t/api/static/index.html`
- Modify: `src/b2t/api/static/app.js`
- Modify: `src/b2t/api/static/style.css`
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_api_app.py`:

```python
def test_index_has_graph_container():
    text = _client().get("/").text
    assert '<div id="graph"' in text
    assert "mermaid" in text.lower()
    assert '<ul id="nodes"' not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_app.py::test_index_has_graph_container -q`
Expected: FAIL (the page still has `<ul id="nodes">` and no `<div id="graph">` or mermaid reference).

- [ ] **Step 3: Update index.html**

In `src/b2t/api/static/index.html`, replace this line:

```html
      <ul id="nodes"></ul>
```

with:

```html
      <div id="graph"></div>
```

Then replace this scripts block:

```html
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/mode/simple.min.js"></script>
  <script src="/app.js"></script>
```

with:

```html
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/mode/simple.min.js"></script>
  <script type="module">
    import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.12.0/dist/mermaid.esm.min.mjs";
    window.mermaid = mermaid;
    document.dispatchEvent(new Event("mermaid-ready"));
  </script>
  <script src="/app.js"></script>
```

Note: the module script is deferred, so it runs after the classic `app.js` has executed and registered its `mermaid-ready` listener. If the import fails (offline), the event never fires and the app uses its text fallback.

- [ ] **Step 4: Add the graph state variable in app.js**

In `src/b2t/api/static/app.js`, find this line near the top:

```javascript
let editor = null;
```

and add a new line immediately after it:

```javascript
let graphNodes = null;
```

- [ ] **Step 5: Replace renderNodes with loadGraph and highlightGraph**

In `src/b2t/api/static/app.js`, replace this entire function:

```javascript
function renderNodes(currentNode, status) {
  const list = $("nodes");
  list.innerHTML = "";
  const idx = NODES.indexOf(currentNode);
  const allDone = status === "succeeded";
  NODES.forEach((name, i) => {
    const li = document.createElement("li");
    li.textContent = name;
    if (allDone || (idx >= 0 && i < idx)) li.classList.add("done");
    else if (idx === i) li.classList.add(status === "running" ? "active" : "done");
    list.appendChild(li);
  });
}
```

with:

```javascript
async function loadGraph() {
  let def;
  try {
    def = (await (await fetch("/api/graph")).json()).mermaid;
  } catch (e) {
    return;  // leave graphNodes null; highlightGraph uses the text fallback
  }
  if (!window.mermaid) return;
  try {
    window.mermaid.initialize({ startOnLoad: false, securityLevel: "loose", theme: "dark" });
    const { svg } = await window.mermaid.render("pipelineGraph", def);
    $("graph").innerHTML = svg;
    const map = {};
    $("graph").querySelectorAll("g.node").forEach((g) => {
      map[g.textContent.trim()] = g;
    });
    graphNodes = map;
  } catch (e) {
    graphNodes = null;
  }
}

function highlightGraph(currentNode, status) {
  if (!graphNodes) {
    $("graph").textContent = currentNode ? `Stage: ${currentNode} (${status})` : "";
    return;
  }
  const idx = NODES.indexOf(currentNode);
  const allDone = status === "succeeded";
  NODES.forEach((name, i) => {
    const g = graphNodes[name];
    if (!g) return;
    g.classList.remove("done", "active");
    if (allDone || (idx >= 0 && i < idx)) g.classList.add("done");
    else if (idx === i) g.classList.add(status === "running" ? "active" : "done");
  });
}
```

- [ ] **Step 6: Call highlightGraph from poll and load the graph on ready**

In `src/b2t/api/static/app.js`, in the `poll` function, replace this line:

```javascript
  renderNodes(job.current_node, job.status);
```

with:

```javascript
  highlightGraph(job.current_node, job.status);
```

Then add this line as the very last line of the file:

```javascript
document.addEventListener("mermaid-ready", loadGraph);
```

- [ ] **Step 7: Add graph styles to style.css**

Append to `src/b2t/api/static/style.css`:

```css
#graph { margin-top: 0.8rem; text-align: center; min-height: 1.2rem; }
#graph svg { max-width: 100%; height: auto; }
#graph .node.done rect, #graph .node.done polygon, #graph .node.done path { fill: #bfe9c6 !important; }
#graph .node.active rect, #graph .node.active polygon, #graph .node.active path { fill: #ffe9b3 !important; }
```

- [ ] **Step 8: Run the test to verify it passes**

Run: `uv run pytest tests/test_api_app.py::test_index_has_graph_container -q`
Expected: PASS.

- [ ] **Step 9: Run the full suite**

Run: `uv run pytest -q`
Expected: all tests pass (typst-dependent tests skip when the binary is absent).

- [ ] **Step 10: Manual smoke check (browser)**

A true visual check is a human step, but the implementer should confirm the server serves the page and the graph endpoint:

```bash
uv run python -c "from fastapi.testclient import TestClient; from b2t.api.app import app; c = TestClient(app); print(c.get('/').status_code); print('graph TD' in c.get('/api/graph').json()['mermaid'] or 'graph' in c.get('/api/graph').json()['mermaid'].lower())"
```

Expected: prints `200`, then `True`. Then, if a browser is available, run `uv run uvicorn b2t.api.app:app --reload`, open http://127.0.0.1:8000, click "Use sample deck" (fake converter ticked), and confirm the pipeline renders as a graph whose nodes light up as the run progresses. If the nodes render but do not get colored, confirm the rendered node groups carry `class="node"` and that their label text matches the node names (the basis of the `graphNodes` map); adjust the selector if the installed Mermaid differs. The text fallback should appear if Mermaid is blocked.

- [ ] **Step 11: Commit**

```bash
git add src/b2t/api/static/index.html src/b2t/api/static/app.js src/b2t/api/static/style.css tests/test_api_app.py
git commit -m "feat: show pipeline progress on the langgraph graph"
```

---

## Self-review

**Spec coverage** (each spec section maps to a task):
- Show the real graph instead of a list -> Task 1 (`/api/graph` from `get_graph().draw_mermaid()`), Task 2 (render into `#graph`).
- Highlight done/current nodes as `current_node` advances -> Task 2 (`highlightGraph`).
- Source the graph from the compiled LangGraph -> Task 1 (`build_graph(...).get_graph().draw_mermaid()`).
- Mermaid from a CDN, render once + toggle classes -> Task 2 (ESM import, `loadGraph` renders once, `highlightGraph` toggles classes).
- Replace the rectangle list -> Task 2 (`<ul id="nodes">` removed; `renderNodes` removed).
- Text fallback if Mermaid unavailable -> Task 2 (`highlightGraph` writes `Stage: ...` when `graphNodes` is null).
- `__start__`/`__end__` present but unhighlighted -> Task 2 (they are not in `NODES`, so never marked).
- Backend test for `/api/graph`; static markup test -> Tasks 1, 2.
- Pipeline and jobs.py untouched -> no task modifies them.

**Placeholder scan:** none. The CDN URL is pinned to a verified version (11.12.0).

**Type consistency:** `GraphView(mermaid: str)` (Task 1) is returned by `get_graph` (Task 1) and read by the frontend as `.mermaid` (Task 2). `build_graph` and `FakeConverter` are both available in `app.py` after the Task 1 import addition. `highlightGraph(currentNode, status)` (Task 2) replaces `renderNodes(currentNode, status)` with the same signature and is called with the same arguments in `poll`. `graphNodes` is declared once (Step 4) and used in `loadGraph`/`highlightGraph`. The `NODES` array is unchanged and still matches the backend `PIPELINE_NODES`.

**Out-of-scope guard:** no zoom/pan, no clickable nodes, no edge animation, no graph editing. Consistent with the spec non-goals.
