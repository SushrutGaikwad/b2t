# State Inspector Readability and Show/Hide - Design

Date: 2026-06-10
Status: proposed

## 1. Motivation

The per-node state inspector (see `2026-06-10-state-inspector-design.md`) works, but
two things hurt its usefulness in practice:

- The snapshot is rendered as a field-by-field DOM list with a preview/expand toggle
  per long string. It is hard to read: no real formatting, no syntax highlighting,
  and source-heavy values are awkward.
- Clicking a node shows its snapshot but there is no way to hide it again. The panel
  just stays open.

This change makes the snapshot render as one read-only, wrapping,
syntax-highlighted JSON text box, and makes the panel toggle open and closed. It is
a frontend-only refinement of the existing feature. No backend changes: the
`GET /api/jobs/{id}/state/{node}` endpoint and the `state_nodes` poll field already
return exactly what is needed.

## 2. Scope

In scope:

- Render the snapshot as pretty-printed JSON in a read-only CodeMirror instance with
  line wrapping and JSON syntax highlighting, reusing the CodeMirror already loaded
  for the Typst editor.
- A `changed: ...` line above the JSON (the per-node changed fields), kept from the
  current behavior since per-key highlighting inside the JSON blob is out of scope.
- Show/hide: clicking an inspectable node toggles its panel (click again to hide),
  a `hide` button in the panel header closes it, and clicking a different node
  switches to that node.
- A graceful fallback to a plain wrapping text block if CodeMirror failed to load.

Out of scope:

- Any backend change. The endpoint and `state_nodes` are untouched.
- Per-key highlighting of changed fields inside the JSON (the `changed:` line covers
  this).
- Editing the snapshot. The viewer is read-only.
- Truncation/preview of long values. The JSON viewer is scrollable and wraps, so the
  full value is shown and the box simply scrolls.

## 3. Decisions already made (with rationale)

| Decision | Choice | Why |
| --- | --- | --- |
| Render format | One read-only JSON text box (CodeMirror), with a `changed:` line above | User selection; a real text box with wrapping and highlighting reads far better than the field-by-field DOM |
| Highlighting mechanism | Reuse CodeMirror with its real `javascript`/`json` mode (one extra CDN script) | Best key/string/number highlighting for the least code; matches the existing Typst editor look |
| Show/hide | Click toggles open/close, plus a `hide` button; clicking another node switches | User selection |
| Long values | Shown in full inside a scrollable, wrapping, height-capped box | The viewer scrolls, so no preview/expand is needed; simpler than the old per-string toggle |
| Viewer lifecycle | One read-only CodeMirror instance, created lazily and reused (`setValue` + `refresh`) | CodeMirror is costly to recreate per click and needs `refresh()` after being unhidden |
| Fallback | Plain wrapping text block when `window.CodeMirror` is absent | Matches the existing `getSource`/`setSource` resilience; the feature still works offline of the CDN |

Alternatives considered and rejected: a JSON `simple-mode` defined via the
already-loaded `simple.min.js` addon (avoids a CDN script but gives coarser
highlighting that cannot cleanly separate keys from string values); and a plain
`<pre>` with hand-rolled regex JSON highlighting (reimplements what CodeMirror
already does well, more code to maintain).

## 4. Components (frontend only)

### 4.1 `src/b2t/api/static/index.html`

- Add the CodeMirror `javascript` mode script next to the existing CodeMirror
  scripts:
  `https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/javascript/javascript.min.js`.
- Mark the inspector container hidden by default:
  `<div id="state-inspector" hidden></div>` (it currently has no `hidden`
  attribute).

### 4.2 `src/b2t/api/static/app.js`

Remove the old rendering path: `renderInspector`, `renderValue`, `renderString`,
and the `STATE_PREVIEW` constant.

Add:

- Module state: `let inspectedNode = null;` (the node whose snapshot is shown, or
  null) and `let stateViewer = null;` (the lazy read-only CodeMirror instance).
- `ensureInspector()` - builds the panel shell once into `#state-inspector`: a
  header (`#inspector-title` span plus a `hide` button wired to `hideInspector`), a
  `#inspector-changed` line, and a `#inspector-viewer` div. On first build, if
  `window.CodeMirror` is present, create the read-only JSON CodeMirror in the viewer
  div with `{ mode: { name: "javascript", json: true }, theme: "material-darker",
  lineWrapping: true, readOnly: true }` and store it in `stateViewer`.
- `setViewer(text)` - if `stateViewer` exists, `setValue(text)` then `refresh()`
  (refresh is required because the panel was hidden); otherwise set the viewer div's
  `textContent` (the wrapping fallback).
- `selectNode(node)` - clear `selected` on all strip boxes, add it to `node`'s box.
- `hideInspector()` - set the panel `hidden`, clear `inspectedNode`, clear the
  `selected` outline on all boxes.
- `inspectNode(node)` (rewritten):
  - guard: `if (!currentJobId || !stateNodes.includes(node)) return;`
  - toggle: if `inspectedNode === node` and the panel is visible, `hideInspector()`
    and return.
  - otherwise `ensureInspector()`, `selectNode(node)`, set `inspectedNode = node`,
    unhide the panel, set the title to `State after: <node>` and the changed line to
    `loading...`, then `fetch(/api/jobs/{currentJobId}/state/{node})`. On success set
    the changed line to `changed: <fields>` (or `(nothing)`) and
    `setViewer(JSON.stringify(data.state, null, 2))`. On failure set the changed line
    to `(failed to load state)` and clear the viewer.

Keep, unchanged: the click wiring added in `loadGraph` (`box.addEventListener(
"click", () => inspectNode(n.name))`), `markInspectable`, and the `poll` updates
(`stateNodes = job.state_nodes || []; markInspectable()`). In `start`, replace the
current inline clearing with `hideInspector(); stateNodes = []; markInspectable();`.

### 4.3 `src/b2t/api/static/style.css`

- Remove the now-unused rules: `#state-inspector:empty`, `.state-field`,
  `.state-field.is-changed`, `.state-key`, `.state-string`,
  `.state-object, .state-subfield`, `.state-meta`, `button.expand`.
- Keep: `#state-inspector { margin-top: 0.8rem; }`, `#graph .node.inspectable`,
  `#graph .node.selected`, `.inspector-title`, `.inspector-changed`.
- Add: `.inspector-header` (flex row, title left, hide button right);
  `.inspector-hide` (small purple button); `#inspector-viewer` (the fallback:
  `white-space: pre-wrap; word-break: break-word;`); and
  `#state-inspector .CodeMirror { height: auto; max-height: 360px; border: 1px
  solid #e3dbe8; border-radius: 6px; }` so the inspector editor scrolls within a
  capped height instead of using the editor's fixed 340px.

## 5. Data flow (unchanged backend)

```mermaid
sequenceDiagram
    participant UI
    participant CM as CodeMirror (read-only json)
    participant API as /api/jobs/{id}/state/{node}

    Note over UI: click an inspectable node
    alt same node already open
        UI->>UI: hideInspector()
    else open or switch
        UI->>API: GET state/{node}
        API-->>UI: { node, changed, state }
        UI->>CM: setValue(JSON.stringify(state, null, 2)); refresh()
        UI->>UI: show panel, set "changed: ..." line, mark node selected
    end
    Note over UI: hide button -> hideInspector(); new run -> hideInspector()
```

## 6. Error handling

- Fetch failure sets the changed line to `(failed to load state)` and clears the
  viewer; the panel stays usable.
- If CodeMirror is unavailable, `setViewer` falls back to plain wrapping text, so the
  snapshot is still readable.
- The toggle and selection logic guards on `graphNodes` and `currentJobId`, so clicks
  before a run or before the strip is built are no-ops (unchanged from today).

## 7. Testing

The JS and CSS are not unit-tested, so automated coverage is limited to the served
HTML:

- Keep `test_index_has_state_inspector_container` (the `hidden` attribute does not
  change the `'<div id="state-inspector"'` substring it asserts).
- Add `test_index_loads_codemirror_json_mode` asserting the served HTML references
  the CodeMirror javascript mode (e.g. `'mode/javascript' in text`), guarding the
  highlighting dependency.

Everything else is manual browser verification: click a node to open the highlighted
JSON, click the same node again to hide, use the `hide` button, switch between nodes,
and confirm a long value (for example `flattened_tex` or `llm_rendered`) wraps and
scrolls within the capped-height box.

## 8. Risk

Low. Frontend-only, additive to one CDN script. The backend, the endpoint, and the
poll payload are untouched. The one external dependency added is a CodeMirror mode
from the same pinned CDN version already in use; the fallback covers its absence.
