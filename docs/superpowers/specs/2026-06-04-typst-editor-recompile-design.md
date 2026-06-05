# Typst Editor, Save-and-Compile, and Download Design

Date: 2026-06-04
Status: Approved (design), pending implementation plan

## Overview

Extend the testing frontend so the generated `main.typ` is shown in a
syntax-highlighted code editor that the user can edit in place. A "Save and
compile" action writes the edited source to disk and rebuilds the PDF, and a
"Download" action zips the result directory (the `.typ`, its PDF, and the
images) for the user to take away. The save-and-compile is purely deterministic
(write the edited Typst, run the `typst` compiler, surface errors or the new
PDF); no LLM and no LangGraph are involved. This tightens the fix loop when a
conversion produces Typst that needs a small manual correction, and is a natural
precursor to the automated compile-fix loop on the roadmap.

It builds on the existing FastAPI testing frontend (`src/b2t/api/`).

## Goals

- Show `main.typ` with Typst syntax highlighting (IDE-like colors).
- Let the user edit the Typst directly in the page.
- Save the edited source and recompile it on demand, showing the new PDF or
  compile error.
- Download the result directory (`.typ`, its PDF, and images) as a zip.
- Keep it deterministic: reuse the existing `typst_runner.compile_typst`.

## Non-goals

- No autosave, no multi-file editing, no diff against the original conversion.
- No LLM involvement in save-and-compile.
- No change to the existing conversion pipeline (`graph.py`, `nodes/`,
  `state.py`, `latex/`, `typst_runner.py`, `llm.py`).
- No frontend build toolchain (no npm, no bundler).

## Approved decisions

1. Editor: CodeMirror 5 loaded from a CDN (core JS, a theme CSS, and the
   simple-mode addon), enhancing a `<textarea>` via `CodeMirror.fromTextArea`,
   with a small hand-written Typst mode via `CodeMirror.defineSimpleMode`.
   Chosen over CodeMirror 6 because the single-file CDN drop-in keeps the
   no-build setup and avoids needing a separate Typst language package. A real
   Typst highlighting mode is not shipped by the common editors, so we define a
   minimal one ourselves.
2. Save-and-compile is a deterministic, synchronous endpoint. A bare `typst`
   compile is fast, so blocking on it is simpler than another async job and
   needs no polling. Download is likewise synchronous.
3. Save writes in place: it overwrites the job's `output_dir/main.typ`, so the
   images already copied alongside still resolve and the edited buffer becomes
   the working copy. Re-running the original conversion regenerates from the LLM.
4. Save request body is JSON `{"source": "<edited typst>"}`.
5. Save and download are two actions, not three. "Save and compile" writes the
   edited source and recompiles it in one operation, keeping the directory's
   `.typ` and PDF consistent. "Download" zips that saved `output_dir`. Saving
   without compiling is not offered, so the bundle is always self-consistent.

## Architecture

All changes are additive within `src/b2t/api/` plus the static assets. New
surface:

- `schemas.py`: a `SaveRequest` model (`source: str`) and a `SaveResult` model
  (`ok: bool`, `error: str | None`).
- `app.py`: two new routes: `POST /api/jobs/{job_id}/save` (write edited source
  and compile) and `GET /api/jobs/{job_id}/download` (zip the result directory).
- `static/index.html`: load CodeMirror assets from the CDN; replace the
  read-only `<pre>` with an editor textarea; add "Save and compile" and
  "Download" buttons.
- `static/app.js`: initialize the editor with the custom Typst mode, populate it
  on job completion, and wire the Save and Download buttons.
- `static/style.css`: minor styling for the editor and buttons.

The save handler does not touch `jobs.py` internals beyond the existing
`JobStore.get` and `JobStore.update`. It does not import the graph or any LLM.

## Save-and-compile endpoint

`POST /api/jobs/{job_id}/save`, JSON body `{"source": "..."}`. Writes the edited
source to disk and compiles it in one step.

Behavior:

1. `job = store.get(job_id)`; return 404 if the job is unknown.
2. Return 404 if the job has no `typst_path` yet (nothing has been generated to
   save).
3. Write `source` to the job's existing `main.typ` path (`job.typst_path`,
   which lives in `output_dir` alongside the copied images), UTF-8.
4. Run `compile_typst(job.typst_path)`.
5. Update the job record: on success `status="succeeded"`,
   `pdf_path=result.pdf_path`, `error=None`; on failure
   `status="compile_failed"`, `pdf_path=None`, `error=result.error`.
6. Return `SaveResult(ok=result.ok, error=result.error)`.

The response is intentionally small; the page reloads the PDF via the existing
`GET /api/jobs/{id}/pdf` (cache-busted) and reads the error from the result.

## Download endpoint

`GET /api/jobs/{job_id}/download`. Returns the result directory as a zip
attachment.

Behavior:

1. `job = store.get(job_id)`; return 404 if the job is unknown or its
   `output_dir` does not exist on disk yet.
2. Zip the contents of `output_dir` (the current `main.typ`, `main.pdf` when a
   compile has succeeded, and the copied images) into a temp zip file.
3. Serve it with `FileResponse(..., media_type="application/zip",
   filename="deck.zip")` so the browser downloads it.

The download reflects whatever is currently on disk. Because "Save and compile"
is the only writer and it writes the source and the PDF together, the saved
directory is internally consistent.

## Frontend behavior

- The editor host is a `<textarea id="typ">` that CodeMirror enhances via
  `CodeMirror.fromTextArea`, using the custom Typst simple-mode and a dark theme
  to match the existing panes. If the CDN assets fail to load, the plain
  textarea remains a usable editor, so save and download still work offline.
- When a job reaches a terminal state with Typst output, the editor is filled
  from `GET /api/jobs/{id}/typ`.
- The "Save and compile" button is enabled once the editor holds content and a
  current job id is known. Clicking it:
  1. Shows a brief "saving" status.
  2. `POST`s `{"source": <editor content>}` to the save route.
  3. On the result, refreshes the PDF iframe (with a cache-busting query) and
     sets the error pane from `error` (or clears it on success).
- The "Download" button is enabled once a job has output. Clicking it points the
  browser at `GET /api/jobs/{id}/download` to download the zip of the saved
  directory.
- The Typst simple-mode highlights: line comments `//...`, block comments
  `/* ... */`, double-quoted strings, inline math `$...$`, headings (a line
  starting with one or more `=`), and `#`-prefixed code including the keywords
  `let`, `set`, `show`, `import`, `include`, plus function-call names.

## Error handling

- Unknown job id: 404 (save and download).
- Job with no generated Typst yet: 404 on save (nothing to save).
- Job with no `output_dir` on disk yet: 404 on download (nothing to zip).
- A compile failure is a normal save result (`ok=false`, `error` set, job
  `compile_failed`), not an HTTP error.
- If the CDN editor assets fail to load (offline), the underlying `<textarea>`
  remains an editable fallback (a free consequence of `fromTextArea`), so save
  and download are never hard-blocked on the CDN at runtime.

## Testing approach

- API tests (`TestClient`, offline via the existing `FakeConverter` sample
  flow):
  - Run the sample job to terminal, then `POST /save` with valid Typst: expect
    `ok` true and, when `typst` is available, the job status `succeeded` with a
    fresh PDF.
  - `POST /save` with deliberately broken Typst: expect `ok` false and a
    non-empty `error`, job status `compile_failed`. (Guarded by
    `typst_available()` since it needs the binary to produce an error.)
  - `POST /save` on an unknown job id: 404.
  - After a successful sample run, `GET /download` returns a zip (200,
    `application/zip`) whose entries include `main.typ` (and `main.pdf` when
    `typst` is available, plus `logo.png`); `GET /download` on an unknown job
    id: 404.
- Static wiring: keep the existing light check that the page serves and includes
  the expected elements (now including the editor textarea and the Save and
  Download buttons), consistent with the current static-page test style.
- Existing tests remain untouched and green.

## Future seams

- The same save-and-compile endpoint and editor are the manual version of the
  roadmap's automated compile-fix loop; an LLM fix step can later post to the
  same path.
- Multi-file editing and diffing against the original conversion are deferred.
