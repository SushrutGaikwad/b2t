# Typst Editor and Recompile Design

Date: 2026-06-04
Status: Approved (design), pending implementation plan

## Overview

Extend the testing frontend so the generated `main.typ` is shown in a
syntax-highlighted code editor that the user can edit in place, with a
Recompile button that rebuilds the PDF from the edited source. The recompile is
purely deterministic (write the edited Typst, run the `typst` compiler, surface
errors or the new PDF); no LLM and no LangGraph are involved. This tightens the
fix loop when a conversion produces Typst that needs a small manual correction,
and is a natural precursor to the automated compile-fix loop on the roadmap.

It builds on the existing FastAPI testing frontend (`src/b2t/api/`).

## Goals

- Show `main.typ` with Typst syntax highlighting (IDE-like colors).
- Let the user edit the Typst directly in the page.
- Recompile the edited source on demand and show the new PDF or compile error.
- Keep it deterministic: reuse the existing `typst_runner.compile_typst`.

## Non-goals

- No autosave, no download button, no multi-file editing, no diff against the
  original conversion.
- No LLM involvement in recompile.
- No change to the existing conversion pipeline (`graph.py`, `nodes/`,
  `state.py`, `latex/`, `typst_runner.py`, `llm.py`).
- No frontend build toolchain (no npm, no bundler).

## Approved decisions

1. Editor: CodeMirror 5 loaded from a CDN (core JS, a theme CSS, and the
   simple-mode addon), with a small hand-written Typst mode via
   `CodeMirror.defineSimpleMode`. Chosen over CodeMirror 6 because the single-
   file CDN drop-in keeps the no-build setup and avoids needing a separate
   Typst language package. A real Typst highlighting mode is not shipped by the
   common editors, so we define a minimal one ourselves.
2. Recompile is a deterministic, synchronous endpoint. A bare `typst` compile
   is fast, so blocking on it is simpler than another async job and needs no
   polling.
3. Recompile writes in place: it overwrites the job's `output_dir/main.typ`, so
   images already copied alongside still resolve and the edited buffer becomes
   the working copy. Re-running the original conversion regenerates from the LLM.
4. Request body is JSON `{"source": "<edited typst>"}`.

## Architecture

All changes are additive within `src/b2t/api/` plus the static assets. New
surface:

- `schemas.py`: a `RecompileRequest` model (`source: str`) and a
  `RecompileResult` model (`ok: bool`, `error: str | None`).
- `app.py`: one new route `POST /api/jobs/{job_id}/recompile`.
- `static/index.html`: load CodeMirror assets from the CDN; add a Recompile
  button.
- `static/app.js`: initialize the editor with the custom Typst mode, populate it
  on job completion, and wire the Recompile button.
- `static/style.css`: minor styling for the editor and button.

The recompile handler does not touch `jobs.py` internals beyond the existing
`JobStore.get` and `JobStore.update`. It does not import the graph or any LLM.

## Recompile endpoint

`POST /api/jobs/{job_id}/recompile`, JSON body `{"source": "..."}`.

Behavior:

1. `job = store.get(job_id)`; return 404 if the job is unknown.
2. Return 404 if the job has no `typst_path` yet (nothing has been generated to
   recompile).
3. Write `source` to the job's existing `main.typ` path (`job.typst_path`,
   which lives in `output_dir` alongside the copied images), UTF-8.
4. Run `compile_typst(job.typst_path)`.
5. Update the job record: on success `status="succeeded"`,
   `pdf_path=result.pdf_path`, `error=None`; on failure
   `status="compile_failed"`, `pdf_path=None`, `error=result.error`.
6. Return `RecompileResult(ok=result.ok, error=result.error)`.

The response is intentionally small; the page reloads the PDF via the existing
`GET /api/jobs/{id}/pdf` (cache-busted) and reads the error from the result.

## Frontend behavior

- The editor host is a `<textarea id="typ">` that CodeMirror enhances via
  `CodeMirror.fromTextArea`, using the custom Typst simple-mode and a dark theme
  to match the existing panes. If the CDN assets fail to load, the plain
  textarea remains a usable editor, so recompile still works offline.
- When a job reaches a terminal state with Typst output, the editor is filled
  from `GET /api/jobs/{id}/typ` (replacing the old read-only `<pre>`).
- The Recompile button is enabled once the editor holds content and a current
  job id is known. Clicking it:
  1. Shows a brief "compiling" status.
  2. `POST`s `{"source": <editor content>}` to the recompile route.
  3. On the result, refreshes the PDF iframe (with a cache-busting query) and
     sets the error pane from `error` (or clears it on success).
- The Typst simple-mode highlights: line comments `//...`, block comments
  `/* ... */`, double-quoted strings, inline math `$...$`, headings (a line
  starting with one or more `=`), and `#`-prefixed code including the keywords
  `let`, `set`, `show`, `import`, `include`, plus function-call names.

## Error handling

- Unknown job id: 404.
- Job with no generated Typst yet: 404 (nothing to recompile).
- A compile failure is a normal result (`ok=false`, `error` set, job
  `compile_failed`), not an HTTP error.
- If the CDN editor assets fail to load (offline), the underlying `<textarea>`
  remains an editable fallback (a free consequence of `fromTextArea`), so
  recompile is never hard-blocked on the CDN at runtime.

## Testing approach

- API tests (`TestClient`, offline via the existing `FakeConverter` sample
  flow):
  - Run the sample job to terminal, then `POST /recompile` with valid Typst:
    expect `ok` true and, when `typst` is available, the job status
    `succeeded` with a fresh PDF.
  - `POST /recompile` with deliberately broken Typst: expect `ok` false and a
    non-empty `error`, job status `compile_failed`. (Guarded by
    `typst_available()` since it needs the binary to produce an error.)
  - `POST /recompile` on an unknown job id: 404.
- Static wiring: keep the existing light check that the page serves and includes
  the expected elements (now including the editor host and the Recompile
  button), consistent with the current static-page test style.
- Existing tests remain untouched and green.

## Future seams

- The same recompile endpoint and editor are the manual version of the
  roadmap's automated compile-fix loop; an LLM fix step can later post to the
  same path.
- A download or save-as control and multi-file editing are deferred.
