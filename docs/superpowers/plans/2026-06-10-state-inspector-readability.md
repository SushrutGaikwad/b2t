# State Inspector Readability and Show/Hide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render a node's state snapshot as one read-only, wrapping, syntax-highlighted JSON text box (reusing CodeMirror), and make the inspector panel toggle open and closed with a hide button.

**Architecture:** Frontend-only change to the testing UI. Add the CodeMirror `javascript` mode script, then rewrite the inspector in `app.js` to use a reusable read-only CodeMirror JSON viewer inside a build-once panel shell that toggles via the `hidden` attribute. Swap the per-field CSS for header/viewer styling. No backend, endpoint, or schema changes.

**Tech Stack:** Plain JS, CodeMirror 5.65.16 (already loaded from CDN), CSS. Tests via pytest against the served HTML (`uv run pytest`). The JS/CSS behavior is verified manually in a browser.

Spec: `docs/superpowers/specs/2026-06-10-state-inspector-readability-design.md`.

---

## File structure

- Modify `src/b2t/api/static/index.html` - add the CodeMirror javascript mode script; mark the inspector container `hidden`.
- Modify `src/b2t/api/static/app.js` - replace the inspector rendering (the `STATE_PREVIEW` constant and `renderInspector`/`renderValue`/`renderString`) with a build-once panel shell, a reusable read-only JSON CodeMirror viewer, and a toggle/hide `inspectNode`; update `start` to call `hideInspector`.
- Modify `src/b2t/api/static/style.css` - remove the unused per-field rules; add header/hide-button/viewer styles and an inspector-specific CodeMirror height.
- Test: `tests/test_api_app.py` - assert the served HTML loads the javascript mode (the existing container test still applies).

Task 1 is the HTML dependency (with an automated test) and keeps the inspector working with the old JS. Task 2 is the JS/CSS rewrite (manual browser verification), so no intermediate commit leaves the inspector broken.

---

### Task 1: Load the CodeMirror JSON highlighting mode

**Files:**
- Modify: `src/b2t/api/static/index.html`
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_api_app.py`:

```python
def test_index_loads_codemirror_json_mode():
    text = _client().get("/").text
    assert "mode/javascript" in text
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_api_app.py::test_index_loads_codemirror_json_mode -v`
Expected: FAIL (`assert "mode/javascript" in text`).

- [ ] **Step 3: Add the mode script to `index.html`**

In `src/b2t/api/static/index.html`, the scripts at the bottom currently are:

```html
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/mode/simple.min.js"></script>
  <script src="/app.js"></script>
```

Insert the javascript mode script after the `simple.min.js` line so the block reads:

```html
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/mode/simple.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/javascript/javascript.min.js"></script>
  <script src="/app.js"></script>
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_api_app.py::test_index_loads_codemirror_json_mode tests/test_api_app.py::test_index_has_state_inspector_container -v`
Expected: PASS (both).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/api/static/index.html tests/test_api_app.py
git commit -m "feat: load the codemirror json mode for the state inspector"
```

---

### Task 2: JSON viewer with toggle and hide

**Files:**
- Modify: `src/b2t/api/static/app.js`
- Modify: `src/b2t/api/static/index.html`
- Modify: `src/b2t/api/static/style.css`
- Test: `tests/test_api_app.py` (the existing container test continues to apply; no new automated test, manual browser verification)

- [ ] **Step 1: Mark the inspector container hidden in `index.html`**

In `src/b2t/api/static/index.html`, change:

```html
      <div id="state-inspector"></div>
```

to:

```html
      <div id="state-inspector" hidden></div>
```

- [ ] **Step 2: Rewrite the inspector block in `app.js`**

In `src/b2t/api/static/app.js`, replace the entire inspector block. The current block is everything from the `// ----- per-node state inspector -----` comment down to (but NOT including) the final `loadGraph();` call, i.e. this exact text:

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

Replace ALL of that with this new block:

```javascript
// ----- per-node state inspector -----
let inspectedNode = null;   // node whose snapshot is shown, or null
let stateViewer = null;     // lazy read-only CodeMirror json viewer

function markInspectable() {
  if (!graphNodes) return;
  for (const [name, box] of Object.entries(graphNodes)) {
    box.classList.toggle("inspectable", stateNodes.includes(name));
  }
}

function selectNode(node) {
  if (!graphNodes) return;
  for (const box of Object.values(graphNodes)) box.classList.remove("selected");
  if (graphNodes[node]) graphNodes[node].classList.add("selected");
}

function ensureInspector() {
  const panel = $("state-inspector");
  if (panel.dataset.built) return;
  panel.dataset.built = "1";

  const header = document.createElement("div");
  header.className = "inspector-header";
  const title = document.createElement("span");
  title.className = "inspector-title";
  title.id = "inspector-title";
  const hide = document.createElement("button");
  hide.type = "button";
  hide.className = "inspector-hide";
  hide.textContent = "hide";
  hide.addEventListener("click", hideInspector);
  header.append(title, hide);

  const changed = document.createElement("div");
  changed.className = "inspector-changed";
  changed.id = "inspector-changed";

  const viewer = document.createElement("div");
  viewer.id = "inspector-viewer";

  panel.append(header, changed, viewer);

  if (window.CodeMirror) {
    stateViewer = CodeMirror(viewer, {
      mode: { name: "javascript", json: true },
      theme: "material-darker",
      lineWrapping: true,
      readOnly: true,
    });
  }
}

function setViewer(text) {
  if (stateViewer) {
    stateViewer.setValue(text);
    stateViewer.refresh();
  } else {
    $("inspector-viewer").textContent = text;
  }
}

function hideInspector() {
  $("state-inspector").hidden = true;
  inspectedNode = null;
  if (graphNodes) {
    for (const box of Object.values(graphNodes)) box.classList.remove("selected");
  }
}

async function inspectNode(node) {
  if (!currentJobId || !stateNodes.includes(node)) return;
  const panel = $("state-inspector");
  if (inspectedNode === node && !panel.hidden) {
    hideInspector();
    return;
  }
  ensureInspector();
  selectNode(node);
  inspectedNode = node;
  panel.hidden = false;
  $("inspector-title").textContent = `State after: ${node}`;
  $("inspector-changed").textContent = "loading...";
  setViewer("");
  try {
    const r = await fetch(`/api/jobs/${currentJobId}/state/${node}`);
    if (!r.ok) throw new Error();
    const data = await r.json();
    $("inspector-changed").textContent =
      "changed: " + (data.changed.join(", ") || "(nothing)");
    setViewer(JSON.stringify(data.state, null, 2));
  } catch (e) {
    $("inspector-changed").textContent = "(failed to load state)";
    setViewer("");
  }
}
```

- [ ] **Step 3: Update `start()` in `app.js` to hide the inspector on a new run**

In `src/b2t/api/static/app.js`, the `start` function currently contains this clearing block:

```javascript
  $("state-inspector").textContent = "";
  stateNodes = [];
  markInspectable();
  if (graphNodes) {
    for (const box of Object.values(graphNodes)) box.classList.remove("selected");
  }
```

Replace that block with:

```javascript
  hideInspector();
  stateNodes = [];
  markInspectable();
```

(`hideInspector` already hides the panel and clears the `selected` outline.)

- [ ] **Step 4: Swap the inspector CSS in `style.css`**

In `src/b2t/api/static/style.css`, replace the entire `/* state inspector */` block. The current block is exactly:

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

Replace it with:

```css
/* state inspector */
#state-inspector { margin-top: 0.8rem; }
#graph .node.inspectable { cursor: pointer; }
#graph .node.selected { outline: 2px solid #cc3399; outline-offset: 1px; }
.inspector-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem; }
.inspector-title { font-weight: 600; font-size: 0.9rem; }
.inspector-hide { background: #6b5b95; padding: 0.1rem 0.5rem; font-size: 0.75rem; }
.inspector-changed { font-size: 0.8rem; color: #cc3399; margin-bottom: 0.5rem; }
#inspector-viewer { white-space: pre-wrap; word-break: break-word; font-family: ui-monospace, monospace; font-size: 0.8rem; }
#state-inspector .CodeMirror { height: auto; max-height: 360px; }
```

- [ ] **Step 5: Run the suite (the served-HTML tests still pass)**

Run: `uv run pytest tests/test_api_app.py -q`
Expected: PASS (including `test_index_has_state_inspector_container` and `test_index_loads_codemirror_json_mode`). The `hidden` attribute does not change the `'<div id="state-inspector"'` substring.

Then the full suite: `uv run pytest -q`
Expected: PASS (integration tests run if `typst` is installed, otherwise skip).

- [ ] **Step 6: Manual browser verification**

The JS/CSS are not unit-tested; verify by hand. Start the UI:

```bash
uv run uvicorn b2t.api.app:app --reload
```

Open http://127.0.0.1:8000, tick "use fake converter (offline)", click "Use sample deck", wait for it to finish. Then:
- Click `convert`: the panel opens with `State after: convert`, a `changed: ...` line, and a dark, syntax-highlighted, pretty-printed JSON box. Confirm the JSON has colored keys/strings/numbers and that long values (for example `flattened_tex` or `llm_rendered`) wrap and the box scrolls within its capped height.
- Click `convert` again: the panel hides.
- Click `flatten`, then click the `hide` button: the panel hides and the node outline clears.
- Switch directly from one node to another (for example `strip_overlays` then `compile`): the panel updates in place.
- Start a new sample run: the inspector hides and the selection clears.

- [ ] **Step 7: Commit**

```bash
git add src/b2t/api/static/app.js src/b2t/api/static/index.html src/b2t/api/static/style.css
git commit -m "feat: show node state as a collapsible highlighted json viewer"
```

---

## Self-review notes (for the implementer)

- Task 1 only adds the script tag, so the inspector keeps working with the old JS until Task 2 lands; no intermediate commit leaves it broken.
- The panel is hidden via the `hidden` attribute, not by emptying it; the shell is built once (`panel.dataset.built`) and the read-only CodeMirror viewer is created once and reused (`setValue` + `refresh` on each show, because CodeMirror needs a refresh after being unhidden).
- Toggle logic keys off `inspectedNode`: clicking the same shown node hides; clicking another switches.
- `hideInspector`, `ensureInspector`, `selectNode`, `setViewer`, and `inspectNode` are all function declarations or used only at click time, so ordering within the file is safe.
- If the CodeMirror CDN fails, `window.CodeMirror` is falsy: the viewer falls back to a plain wrapping `#inspector-viewer` text node, and the feature still works.
- No backend, endpoint, or schema changes. `markInspectable`, the `loadGraph` click wiring, and the `poll` updates are unchanged.
```
