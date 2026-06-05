# Typst Editor, Save-and-Compile, and Download Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the testing frontend show the generated `main.typ` in a syntax-highlighted, editable CodeMirror editor, save-and-recompile the edited source from a button, and download the result directory as a zip.

**Architecture:** Three additive changes to the existing `src/b2t/api/` package and its static assets, leaving the conversion pipeline untouched. A deterministic synchronous `POST /api/jobs/{id}/save` writes the edited Typst over the job's `main.typ` and reruns `typst_runner.compile_typst`. A `GET /api/jobs/{id}/download` zips the job's `output_dir`. The page swaps the read-only `<pre>` for a CodeMirror-enhanced `<textarea>` (loaded from a CDN, with a graceful plain-textarea fallback) and adds Save and Download buttons.

**Tech Stack:** Python 3.12, uv, FastAPI, pydantic v2, the existing `typst_runner.compile_typst`, pytest with FastAPI `TestClient`. Frontend: vanilla JS plus CodeMirror 5 from cdnjs (verified URLs below). No build step.

---

## Conventions for this plan

- Work happens on the current branch `feat/testing-frontend`.
- All commands run from the repo root `d:\projects\b2t` with `uv run ...`. Never use `pip` or `python` directly.
- Every commit message appends the trailer line (after a blank line):
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- No emojis. No em or en dashes in code or docs.
- Do NOT modify the pipeline (`graph.py`, `nodes/`, `state.py`, `latex/`, `typst_runner.py`, `llm.py`) or `jobs.py`. Changes are confined to `schemas.py`, `app.py`, and `static/`.

## Verified CDN URLs (CodeMirror 5.65.16, cdnjs)

These were confirmed to serve the real assets:
- Core CSS: `https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css`
- Theme CSS: `https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/theme/material-darker.min.css`
- Core JS: `https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js`
- Simple-mode addon JS: `https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/mode/simple.min.js`

Subresource Integrity (`integrity=...` / `crossorigin`) is intentionally NOT
added on these tags for v0. This is a localhost-only testing tool, the editor
degrades to a plain textarea if an asset fails to load, and a mismatched pinned
hash would silently disable the editor. CDN hardening (SRI on pinned versions)
belongs with the SaaS phase (roadmap item 7), alongside the other untrusted-
input hardening.

## File structure

```
src/b2t/api/schemas.py          # modify: add SaveRequest, SaveResult
src/b2t/api/app.py              # modify: add /save and /download routes + imports
src/b2t/api/static/index.html   # modify: CodeMirror assets, textarea, Save/Download buttons
src/b2t/api/static/app.js       # modify: editor init, save/download wiring
src/b2t/api/static/style.css    # modify: editor and textarea sizing
tests/test_api_app.py           # modify: add save and download tests, editor markup assertions
```

Current `app.py` registers routes in `create_app` and mounts `StaticFiles` at `/` LAST (line 98). All new routes must be added inside `create_app` BEFORE that mount.

---

### Task 1: Save-and-compile endpoint

**Files:**
- Modify: `src/b2t/api/schemas.py`
- Modify: `src/b2t/api/app.py`
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_api_app.py`:

```python
def _run_sample(client):
    job_id = client.post("/api/jobs/sample", data={"use_fake": "true"}).json()["job_id"]
    _wait_terminal(client, job_id)
    return job_id


@pytest.mark.skipif(not typst_available(), reason="typst binary not installed")
def test_save_valid_source_recompiles():
    client = _client()
    job_id = _run_sample(client)
    res = client.post(
        f"/api/jobs/{job_id}/save", json={"source": "= Edited\n\nNew body.\n"}
    )
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert "Edited" in client.get(f"/api/jobs/{job_id}/typ").text
    assert client.get(f"/api/jobs/{job_id}").json()["status"] == "succeeded"


@pytest.mark.skipif(not typst_available(), reason="typst binary not installed")
def test_save_broken_source_reports_compile_failed():
    client = _client()
    job_id = _run_sample(client)
    res = client.post(
        f"/api/jobs/{job_id}/save", json={"source": "#this_is_not_defined()\n"}
    )
    assert res.status_code == 200
    assert res.json()["ok"] is False
    assert res.json()["error"]
    assert client.get(f"/api/jobs/{job_id}").json()["status"] == "compile_failed"


def test_save_unknown_job_returns_404():
    res = _client().post("/api/jobs/does-not-exist/save", json={"source": "= x\n"})
    assert res.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_api_app.py::test_save_unknown_job_returns_404 -q`
Expected: FAIL with 404 not returned (the route does not exist yet, so FastAPI returns 405/404 for the path; the assertion path is unregistered). The clearest signal is that the `/save` route is absent.

- [ ] **Step 3: Add the schemas**

In `src/b2t/api/schemas.py`, add these two models after the existing `JobView` class (before `def to_view`):

```python
class SaveRequest(BaseModel):
    source: str


class SaveResult(BaseModel):
    ok: bool
    error: str | None
```

- [ ] **Step 4: Add the route and imports in app.py**

In `src/b2t/api/app.py`, update the schemas import line to:

```python
from b2t.api.schemas import (
    JobCreated,
    JobView,
    SaveRequest,
    SaveResult,
    to_view,
)
```

Add this import with the other `b2t` imports:

```python
from b2t.typst_runner import compile_typst
```

Then add this route inside `create_app`, immediately after the `get_pdf` route and BEFORE `app.mount(...)`:

```python
    @app.post("/api/jobs/{job_id}/save", response_model=SaveResult)
    def save_job(job_id: str, req: SaveRequest):
        job = jobs.get(job_id)
        if job is None or job.typst_path is None:
            raise HTTPException(status_code=404, detail="no typst output to save")
        Path(job.typst_path).write_text(req.source, encoding="utf-8")
        result = compile_typst(Path(job.typst_path))
        if result.ok:
            jobs.update(
                job_id, status="succeeded", pdf_path=result.pdf_path, error=None
            )
        else:
            jobs.update(
                job_id, status="compile_failed", pdf_path=None, error=result.error
            )
        return SaveResult(ok=result.ok, error=result.error)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_api_app.py -q`
Expected: PASS. `test_save_unknown_job_returns_404` always runs; the two typst-dependent tests run when `typst` is installed and skip otherwise.

- [ ] **Step 6: Commit**

```bash
git add src/b2t/api/schemas.py src/b2t/api/app.py tests/test_api_app.py
git commit -m "feat: add save-and-compile endpoint"
```

---

### Task 2: Download endpoint

**Files:**
- Modify: `src/b2t/api/app.py`
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing tests**

At the top of `tests/test_api_app.py`, add these imports next to the existing `import time`:

```python
import io
import zipfile
```

Append these tests to `tests/test_api_app.py`:

```python
@pytest.mark.skipif(not typst_available(), reason="typst binary not installed")
def test_download_returns_zip_with_typ_and_pdf():
    client = _client()
    job_id = _run_sample(client)
    res = client.get(f"/api/jobs/{job_id}/download")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    names = zipfile.ZipFile(io.BytesIO(res.content)).namelist()
    assert "main.typ" in names
    assert "main.pdf" in names
    assert "logo.png" in names


def test_download_unknown_job_returns_404():
    assert _client().get("/api/jobs/does-not-exist/download").status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_api_app.py::test_download_unknown_job_returns_404 -q`
Expected: FAIL (the `/download` route does not exist yet, so a 404 from the unregistered path is not the one our handler raises; once added, the handler returns 404 for unknown jobs).

- [ ] **Step 3: Add the zip helper and route**

In `src/b2t/api/app.py`, add this import at the top with the standard-library imports (next to `import tempfile`):

```python
import zipfile
```

Add this module-level helper after `_reconstruct`:

```python
def _zip_dir(directory: Path) -> Path:
    """Zip every file under directory into a fresh temp zip; return its path."""
    zip_path = Path(tempfile.mkdtemp(prefix="b2t_download_")) / "deck.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(directory))
    return zip_path
```

Add this route inside `create_app`, immediately after the `save_job` route and BEFORE `app.mount(...)`:

```python
    @app.get("/api/jobs/{job_id}/download")
    def download_job(job_id: str):
        job = jobs.get(job_id)
        if job is None or job.output_dir is None or not Path(job.output_dir).exists():
            raise HTTPException(status_code=404, detail="no output to download")
        zip_path = _zip_dir(Path(job.output_dir))
        return FileResponse(
            zip_path, media_type="application/zip", filename="deck.zip"
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_api_app.py -q`
Expected: PASS (the download zip test runs when `typst` is installed and skips otherwise; the 404 test always runs).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/api/app.py tests/test_api_app.py
git commit -m "feat: add result-directory download endpoint"
```

---

### Task 3: Editor, Save and Download buttons (frontend)

Replace the read-only `<pre id="typ">` with a CodeMirror-enhanced `<textarea>`, load the editor assets from the CDN, and wire the Save and Download buttons. The page degrades to a plain textarea if the CDN is unreachable.

**Files:**
- Modify: `src/b2t/api/static/index.html`
- Modify: `src/b2t/api/static/app.js`
- Modify: `src/b2t/api/static/style.css`
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_api_app.py`:

```python
def test_index_has_editor_and_buttons():
    text = _client().get("/").text
    assert 'id="typ"' in text
    assert 'id="save"' in text
    assert 'id="download"' in text
    assert "codemirror" in text.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_app.py::test_index_has_editor_and_buttons -q`
Expected: FAIL (the current `index.html` has no `id="save"`, `id="download"`, or any `codemirror` reference).

- [ ] **Step 3: Update `index.html`**

Replace the entire contents of `src/b2t/api/static/index.html` with:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>b2t testing UI</title>
  <link rel="stylesheet" href="/style.css" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/theme/material-darker.min.css" />
</head>
<body>
  <main id="app">
    <h1>b2t: Beamer to Touying</h1>

    <section class="submit">
      <label>
        Deck folder:
        <input type="file" id="folder" webkitdirectory directory multiple />
      </label>
      <div class="options">
        <label><input type="checkbox" id="use-fake" /> use fake converter (offline)</label>
        <label>model override: <input type="text" id="model" placeholder="(default)" /></label>
      </div>
      <div class="actions">
        <button id="run">Convert folder</button>
        <button id="run-sample" type="button">Use sample deck</button>
      </div>
    </section>

    <section class="status">
      <span id="badge" class="badge">idle</span>
      <ul id="nodes"></ul>
    </section>

    <section class="output">
      <h2>Generated main.typ</h2>
      <textarea id="typ"></textarea>
      <div class="actions">
        <button id="save" type="button" disabled>Save and compile</button>
        <button id="download" type="button" disabled>Download</button>
      </div>
      <h2>Compiled PDF</h2>
      <iframe id="pdf" title="compiled pdf"></iframe>
      <h2>Compile error</h2>
      <pre id="error">(none)</pre>
    </section>
  </main>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/mode/simple.min.js"></script>
  <script src="/app.js"></script>
</body>
</html>
```

- [ ] **Step 4: Replace `app.js`**

Replace the entire contents of `src/b2t/api/static/app.js` with:

```javascript
const NODES = [
  "copy_input", "clean_build", "detect_main", "flatten",
  "strip_overlays", "convert", "write_output", "compile",
];
const TERMINAL = ["succeeded", "compile_failed", "failed"];

const $ = (id) => document.getElementById(id);

let currentJobId = null;
let editor = null;

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
}

async function poll(id) {
  const res = await fetch(`/api/jobs/${id}`);
  const job = await res.json();
  setBadge(job.status);
  renderNodes(job.current_node, job.status);
  if (TERMINAL.includes(job.status)) finish(id, job);
  else setTimeout(() => poll(id), 1000);
}

function commonFields(fd) {
  fd.append("use_fake", $("use-fake").checked ? "true" : "false");
  fd.append("model", $("model").value);
  return fd;
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
```

- [ ] **Step 5: Append editor styling to `style.css`**

Append to `src/b2t/api/static/style.css`:

```css
#typ { width: 100%; min-height: 200px; box-sizing: border-box; }
.CodeMirror { height: 340px; border: 1px solid #e3dbe8; border-radius: 6px; }
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `uv run pytest tests/test_api_app.py::test_index_has_editor_and_buttons -q`
Expected: PASS.

- [ ] **Step 7: Run the full suite**

Run: `uv run pytest -q`
Expected: all tests pass (typst-dependent save/download tests skip when the binary is absent).

- [ ] **Step 8: Manual smoke check of the editor**

Run the server and confirm the editor renders with highlighting and the buttons work:

```bash
uv run uvicorn b2t.api.app:app --reload
```

Open http://127.0.0.1:8000, click "Use sample deck" with "use fake converter" ticked, and confirm: the generated source appears in a highlighted editor, editing then "Save and compile" updates the PDF (or shows an error), and "Download" downloads `deck.zip`. Stop the server when done. If the editor does not appear highlighted, confirm the four CDN URLs in `index.html` load in the browser devtools network tab.

- [ ] **Step 9: Commit**

```bash
git add src/b2t/api/static/index.html src/b2t/api/static/app.js src/b2t/api/static/style.css tests/test_api_app.py
git commit -m "feat: add highlighted editor with save and download"
```

---

## Self-review

**Spec coverage** (each spec section maps to a task):
- Editor with Typst highlighting (CodeMirror 5 + simple-mode, fromTextArea) -> Task 3.
- Editable in place -> Task 3 (textarea + CodeMirror).
- Save edited source and recompile -> Task 1 (`/save`).
- Download result directory as zip -> Task 2 (`/download`).
- Deterministic, reuse `compile_typst` -> Task 1 (no LLM, no graph).
- Save writes in place over `output_dir/main.typ` -> Task 1.
- Save request body JSON `{"source"}` -> Task 1 (`SaveRequest`).
- Save is the only writer; bundle self-consistent -> Tasks 1 and 2 (download zips whatever save produced).
- Error handling: unknown job 404 (save and download), no typst output 404 (save), no output_dir 404 (download), compile failure as `ok=false` -> Tasks 1, 2 (tests cover each).
- Graceful textarea fallback if CDN fails -> Task 3 (`if (window.CodeMirror)` guard, `getSource`/`setSource`).
- Testing with TestClient, typst-guarded -> Tasks 1, 2, 3.
- Pipeline and jobs.py untouched -> no task modifies them.

**Placeholder scan:** none. Every code step contains complete code. CDN URLs are pinned to a verified version (5.65.16).

**Type consistency:** `SaveRequest(source)` and `SaveResult(ok, error)` defined in Task 1 are imported and used in the same task's route and read by the Task 1 tests (`res.json()["ok"]`, `["error"]`). The `/save` route uses `job.typst_path` and `JobStore.update(status, pdf_path, error)`, all existing fields/methods. The `/download` route uses `job.output_dir` (an existing `JobRecord` field) and `_zip_dir`. The frontend `save` handler posts `{"source": ...}` matching `SaveRequest`; `download` navigates to the `/download` route. `refreshPdf` and `getSource`/`setSource` are defined before use. Node list and status set unchanged from the existing app.

**Out-of-scope guard:** no autosave, no multi-file editing, no diff, no LLM in save. Consistent with the spec non-goals.
