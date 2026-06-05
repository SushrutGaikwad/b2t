# b2t Testing Frontend Design

Date: 2026-06-04
Status: Approved (design), pending implementation plan

## Overview

A thin web frontend, backed by FastAPI, for exercising the b2t conversion
pipeline through a browser. It wraps the existing LangGraph graph without
modifying it. The goal is a fast feedback loop for testing conversions (upload a
deck, watch the pipeline run node by node, inspect the generated Typst source,
the compiled PDF, and any compile error) and a foundation flexible enough to
grow into later roadmap features, especially human-in-the-loop review and the
eventual SaaS wrapper.

## Goals

- Submit a Beamer deck and run the existing pipeline end to end from a browser.
- Show per-node progress as the deck moves through the graph.
- Display the generated `main.typ`, the compiled PDF, and compile errors.
- Run offline against the `FakeConverter` so the plumbing can be tested without
  API cost.
- Keep the API shaped so HITL pause/resume and richer status slot in later
  without a rewrite.

## Non-goals (frontend v0)

- Authentication, accounts, multi-user.
- A database or any persistence across server restarts.
- Real upload sandboxing or hardening of untrusted archives (roadmap item 7).
- HITL pause/resume (the job model leaves room for it but does not implement it).
- A frontend build toolchain (no npm, no bundler, no SPA framework).
- Any change to the conversion pipeline itself.

## Approved decisions

1. FastAPI backend plus a thin static frontend (vanilla HTML, JS, CSS, no build
   step). Chosen over a Python-native UI (Streamlit/Gradio) and over a full SPA,
   because it matches the eventual SaaS and HITL architecture without much extra
   cost now.
2. Async job model. POST starts a background run and returns a `job_id`; the
   page polls for status. Chosen over a synchronous endpoint so per-node
   progress and a future HITL pause have a place to live.
3. Input is a directory chosen with a browser folder picker
   (`<input type="file" webkitdirectory>`). The folder's loose files are sent as
   multipart (no zip) and reassembled into a temp directory server-side, plus a
   convenience endpoint to run the bundled sample deck with no upload.
4. The pipeline runs unchanged. The runner uses `graph.stream(...)` for
   progress; nodes are not modified.
5. The converter is selectable per request (real `OpenAIConverter` or offline
   `FakeConverter`), reusing the existing `ConverterLLM` interface.
6. In-memory job store for v0. This is the seam where a persistent
   checkpointer or store arrives with HITL.

## Architecture

A new `src/b2t/api/` package sits on top of the existing pipeline. It does not
alter node internals; it only calls `build_graph` and streams the compiled
graph. The pipeline (`graph.py`, `nodes/`, `state.py`, `latex/`) is untouched.

```
src/b2t/api/
  __init__.py
  app.py        # FastAPI app: route registration, static mount, app factory
  jobs.py       # JobRecord, JobStore (in-memory), run_job background runner
  schemas.py    # Pydantic request/response models
  static/
    index.html
    app.js
    style.css
```

New dependencies via `uv add`: `fastapi`, `uvicorn[standard]`,
`python-multipart`.

Launch: `uv run uvicorn b2t.api.app:app --reload`.

## Job model

A `JobRecord` holds:

- `id`: str
- `status`: `queued` | `running` | `succeeded` | `compile_failed` | `failed`
- `current_node`: str | None (last completed node)
- `work_dir`, `output_dir`: Path
- `result`: a serialized view of the terminal `PipelineState` (selected fields)
- `error`: str | None (deterministic failure message or compile error text)

Status semantics:

- `queued`: created, background run not yet started.
- `running`: graph is streaming; `current_node` names the last completed node.
- `succeeded`: compile produced a PDF (`state.compiled` is True).
- `compile_failed`: pipeline finished but `typst` compile failed; the compile
  error text is recorded in `error`.
- `failed`: a deterministic node raised (no main `.tex`, missing include, and
  similar); `error` holds the message.

The `JobStore` is an in-memory dict keyed by `id` with lock-guarded access,
since the background runner writes from a worker thread while request handlers
read.

## Execution flow

1. `POST /api/jobs` receives the picked folder's files as multipart, each
   carrying its relative path (`webkitRelativePath`). The handler rebuilds the
   directory tree under a fresh temp directory (the deck root), creating
   subdirectories as needed so `\input` and `\includegraphics` targets resolve,
   creates a `JobRecord` (`queued`), schedules the background run, and returns
   `{job_id, status}`.
2. The background runner builds the graph with the chosen converter, then
   iterates `graph.stream({input_dir, output_dir})`. After each yielded step it
   sets `current_node` and `status=running`. A deterministic raise is caught and
   recorded as `failed`. On normal completion it inspects the final state:
   `compiled` True means `succeeded`, otherwise `compile_failed` with the error.
3. The page polls `GET /api/jobs/{id}` until a terminal status, then loads the
   `typ` and (if present) `pdf` endpoints.

Running a blocking graph under async FastAPI: the pipeline blocks on a
subprocess (`typst`) and on the network (LLM), so the runner executes
`graph.stream` in a worker thread (for example via `anyio`
`run_in_threadpool` or a `ThreadPoolExecutor`) and never blocks the event loop.

The converter choice and model override come from the POST form fields
(`use_fake` checkbox, optional `model`). The sample endpoint uses the same
runner against the bundled fixture path.

## API surface

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/api/jobs` | Upload the picked folder's files (multipart, `webkitdirectory`); start a run; return `{job_id, status}` |
| POST | `/api/jobs/sample` | Run the bundled `tests/fixtures/sample_deck` with no upload |
| GET | `/api/jobs/{id}` | Poll status, `current_node`, error, and a small state view |
| GET | `/api/jobs/{id}/typ` | The generated `main.typ` text |
| GET | `/api/jobs/{id}/pdf` | The compiled PDF (for inline embed) when present |

`POST /api/jobs` request fields (multipart form):

- `files`: the folder's files, each part's filename carrying its relative path
  (for example `sample_deck/main.tex`, `sample_deck/img/logo.png`)
- `use_fake`: bool (default false)
- `model`: optional string, overrides `OPENAI_MODEL` when the real converter is
  used

`GET /api/jobs/{id}` response (`JobView`): `id`, `status`, `current_node`,
`error`, `has_pdf`, plus a small state view (`main_tex` name, `included_tex`
names, image names, whether `typst_source` is present).

## Frontend page

A single `index.html` with three regions, driven by `app.js` using `fetch` and
a roughly one-second poll:

1. Submit: a folder input (`<input type="file" webkitdirectory>`) with a Browse
   button, a "use sample deck" button, a "use fake converter (offline)"
   checkbox, and an optional model field.
2. Status: a fixed checklist of the eight nodes (`copy_input`, `clean_build`,
   `detect_main`, `flatten`, `strip_overlays`, `convert`, `write_output`,
   `compile`) that fill in as `current_node` advances, plus an overall status
   badge.
3. Output: a pane showing `main.typ` text, an embedded PDF viewer of the `pdf`
   endpoint when `has_pdf`, and a compile-error pane shown when status is
   `compile_failed`.

The node list is static in the page (the v0 graph is linear and fixed), so the
frontend needs no graph-introspection endpoint.

## Error handling

- Deterministic pipeline errors (`ValueError`, `FileNotFoundError` from detect
  and flatten) are caught by the runner and surfaced as `status=failed` with the
  message. They never crash the server.
- Compile failure is a normal terminal outcome (`compile_failed`), not an
  exception.
- Bad uploads (no files submitted) return 400 from the POST handler. A folder
  with no Beamer main `.tex` is a deterministic pipeline failure surfaced as
  `status=failed`, not a 400.
- Unknown job id returns 404.

## Testing approach

- API tests use FastAPI `TestClient` and the `FakeConverter` path, fully
  offline:
  - `POST /api/jobs/sample` (or a multipart post of the fixture deck's files)
    reaches a terminal status and exposes `main.typ`.
  - Unknown job id returns 404.
  - A deliberately broken deck reaches `status=failed` with a message.
- typst-dependent assertions (status reaching `succeeded`, the `pdf` endpoint
  serving a file) are guarded the same way as the existing `integration` marker,
  so the suite passes without the `typst` binary.
- Existing pipeline tests are untouched.

## Future seams (informative, not built now)

- HITL: the job store and status enum are where an `awaiting_review` state and a
  resume endpoint attach; the in-memory store swaps for the LangGraph
  checkpointer.
- Streaming: polling can later be replaced by SSE or websockets without changing
  the job model.
- SaaS: the folder upload path and temp-directory isolation are the starting
  points for roadmap item 7 hardening.
