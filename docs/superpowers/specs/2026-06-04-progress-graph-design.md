# LangGraph Progress Graph Design

Date: 2026-06-04
Status: Approved (design), pending implementation plan

## Overview

Replace the flat list of stage rectangles in the testing frontend with a
rendered diagram of the actual LangGraph pipeline, and highlight progress on
that diagram as the job runs. The graph topology is taken from the compiled
LangGraph itself (not hand-drawn), so it stays accurate as the pipeline gains
branches or loops later.

It builds on the existing FastAPI testing frontend (`src/b2t/api/`).

## Goals

- Show the real pipeline graph (nodes and edges) instead of a flat list.
- Highlight done and current nodes on that graph as `current_node` advances.
- Source the graph from the compiled LangGraph so it never drifts from reality.

## Non-goals

- No zoom, pan, clickable nodes, or edge animation.
- No graph editing.
- No change to the conversion pipeline (`graph.py` is read via its public
  `get_graph()` only) or the `/api/jobs` flow.
- No frontend build toolchain.

## Verified capability

`build_graph(FakeConverter()).get_graph().draw_mermaid()` returns a Mermaid
flowchart string of the real graph, with node ids equal to the node names
(`copy_input`, `clean_build`, `detect_main`, `flatten`, `strip_overlays`,
`convert`, `write_output`, `compile`) plus `__start__` and `__end__`. The
converter argument does not affect topology.

## Approved decisions

1. Render the real graph with Mermaid.js loaded from a CDN (a UMD `<script>`
   exposing `window.mermaid`, same pattern as CodeMirror). The Mermaid string
   comes from a new backend endpoint.
2. Render the diagram once, then toggle CSS classes on the SVG node elements as
   progress advances (no re-render per poll, so no flicker).
3. The stage rectangle list is replaced. If Mermaid is unavailable or render
   fails, a single text line (`Stage: <node> (<status>)`) is the fallback.

## Architecture

- `src/b2t/api/schemas.py`: add `GraphView` (`mermaid: str`).
- `src/b2t/api/app.py`: add `GET /api/graph` returning
  `GraphView(mermaid=build_graph(FakeConverter()).get_graph().draw_mermaid())`,
  registered with the other routes before the static mount. `build_graph` and
  `FakeConverter` are already imported in `app.py`.
- `src/b2t/api/static/index.html`: load Mermaid from the CDN; replace the
  `<ul id="nodes">` with `<div id="graph">`.
- `src/b2t/api/static/app.js`: fetch `/api/graph` on load, render it once,
  build a node-name to SVG-element map, and highlight progress by toggling
  classes; replace `renderNodes` with `highlightGraph`.
- `src/b2t/api/static/style.css`: style `#graph`, `.node.done`, `.node.active`.

## Backend endpoint

`GET /api/graph` returns `{"mermaid": "<mermaid flowchart string>"}`. The string
is produced fresh from a freshly built graph; this is a single page-load call,
so building the graph per request is acceptable and keeps the endpoint
stateless.

## Frontend behavior

- On page load, fetch `/api/graph`. If `window.mermaid` is present, call
  `mermaid.initialize({ startOnLoad: false, theme: "dark" })` and
  `mermaid.render(...)` the definition, inject the returned SVG into `#graph`,
  then build a map `name -> SVG node group element` by matching each rendered
  node group to a pipeline node name.
- Progress highlighting (`highlightGraph(currentNode, status)`): clear `done`
  and `active` classes on all mapped node elements, then mark every node before
  `current_node` in the known pipeline order as `done`, and `current_node`
  itself as `active`; when `status` is `succeeded`, mark all as `done`. Called
  from the existing `poll`/`finish` flow in place of `renderNodes`.
- The known pipeline order is the existing `NODES` array already present in
  `app.js` (it matches the backend `PIPELINE_NODES`). `__start__` and `__end__`
  are present in the diagram but are not in `NODES`, so they are simply never
  highlighted, which is the intended behavior.
- Fallback: if `window.mermaid` is absent or `mermaid.render` throws, `#graph`
  shows a single line `Stage: <currentNode> (<status>)`, updated on each poll.

## Error handling

- If `/api/graph` fails (unlikely on localhost), the page logs nothing visible
  and the fallback text line is used.
- A Mermaid render failure is caught; the fallback text line is used.

## Testing approach

- Backend: a `TestClient` test that `GET /api/graph` returns 200 and a `mermaid`
  string containing `graph` (the Mermaid keyword) and the node names
  `copy_input`, `convert`, and `compile`. Offline, no network.
- Static markup: extend the page-serves test to assert the page contains
  `<div id="graph"` and a `mermaid` script reference, and no longer contains
  `<ul id="nodes"`.
- The SVG highlighting is client-side DOM behavior, covered by a manual smoke
  check (run the sample deck and watch the graph light up), as with the editor.
- Existing tests stay green.

## Future seams

- When the pipeline gains branches or loops (HITL, compile-fix loop), the
  diagram updates automatically since it comes from the live graph. The linear
  progress logic (nodes before `current_node`) may then need revisiting, but
  that is out of scope here.
