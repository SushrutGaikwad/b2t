# Testing Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a thin FastAPI backend plus a static browser page that runs the existing b2t pipeline as an async job, so a deck folder can be converted and inspected (generated `main.typ`, compiled PDF, compile errors) from the browser.

**Architecture:** A new `src/b2t/api/` package wraps the existing compiled LangGraph graph without changing it. A request starts a background job (a `ThreadPoolExecutor` task) that runs `graph.stream(..., stream_mode="updates")`, updating an in-memory `JobStore` per node. The browser picks a folder with `<input webkitdirectory>`, posts its loose files (no zip), and polls a JSON status endpoint. A converter is selected per request (`FakeConverter` offline or `OpenAIConverter`).

**Tech Stack:** Python 3.12, uv, FastAPI, uvicorn, python-multipart, pydantic v2, LangGraph (existing), pytest, FastAPI `TestClient` (httpx). Vanilla HTML/JS/CSS, no build step.

---

## Conventions for this plan

- Work happens on the current branch `feat/testing-frontend`.
- All commands run from the repo root `d:\projects\b2t` with `uv run ...`. Never use `pip` or `python` directly. Never use `uvicorn` without `uv run`.
- Every commit message appends the trailer line:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
  Commit steps show the summary only; append the trailer when committing.
- No emojis. No em or en dashes in code or docs.
- The existing pipeline (`graph.py`, `nodes/`, `state.py`, `latex/`, `typst_runner.py`, `llm.py`) is NOT modified by this plan.

## File structure

Created or modified by this plan:

```
pyproject.toml                    # modified: add fastapi, uvicorn, python-multipart, dev httpx
src/b2t/api/__init__.py           # package marker
src/b2t/api/jobs.py               # JobRecord, JobStore, run_job, EXECUTOR, PIPELINE_NODES
src/b2t/api/schemas.py            # JobCreated, JobView, to_view
src/b2t/api/app.py                # create_app(): routes + static mount; module-level app
src/b2t/api/static/index.html     # the single page
src/b2t/api/static/app.js         # submit + poll + render
src/b2t/api/static/style.css      # minimal styling
tests/test_api_jobs.py            # JobStore + run_job (offline)
tests/test_api_schemas.py         # to_view mapping
tests/test_api_app.py             # endpoints via TestClient (offline, FakeConverter)
README.md                         # modified: add "Run the testing UI" section
```

Reused as-is: `tests/fixtures/sample_deck/` and `tests/conftest.py` (`SAMPLE_DECK`).

---

### Task 1: Dependencies and package skeleton

**Files:**
- Modify: `pyproject.toml`
- Create: `src/b2t/api/__init__.py`

- [ ] **Step 1: Add runtime and dev dependencies with uv**

Run (quote the bracketed extra so the shell does not glob it):

```bash
uv add fastapi "uvicorn[standard]" python-multipart
uv add --dev httpx
```

Expected: `pyproject.toml` `dependencies` now also lists `fastapi`, `uvicorn[standard]`, `python-multipart`; the dev group lists `httpx` (alongside `pytest`); `uv.lock` updates.

- [ ] **Step 2: Create the api package marker**

Create `src/b2t/api/__init__.py`:

```python
"""b2t testing frontend: FastAPI app over the existing conversion pipeline."""
```

- [ ] **Step 3: Verify imports resolve**

Run:

```bash
uv run python -c "import b2t.api, fastapi, uvicorn, multipart, httpx; print('ok')"
```

Expected: prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock src/b2t/api/__init__.py
git commit -m "chore: add api deps and package skeleton"
```

---

### Task 2: Job record and store

The in-memory, thread-safe registry of jobs. No graph yet.

**Files:**
- Create: `src/b2t/api/jobs.py`
- Test: `tests/test_api_jobs.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_api_jobs.py`:

```python
from b2t.api.jobs import JobStore, PIPELINE_NODES


def test_create_and_get():
    store = JobStore()
    job = store.create(status="queued")
    assert store.get(job.id) is job
    assert store.get("missing") is None


def test_update_mutates_record():
    store = JobStore()
    job = store.create()
    store.update(job.id, status="running", current_node="flatten")
    rec = store.get(job.id)
    assert rec.status == "running"
    assert rec.current_node == "flatten"


def test_pipeline_nodes_are_the_eight_in_order():
    assert PIPELINE_NODES == (
        "copy_input",
        "clean_build",
        "detect_main",
        "flatten",
        "strip_overlays",
        "convert",
        "write_output",
        "compile",
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_jobs.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'b2t.api.jobs'`.

- [ ] **Step 3: Write the implementation (store only)**

Create `src/b2t/api/jobs.py`:

```python
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

PIPELINE_NODES = (
    "copy_input",
    "clean_build",
    "detect_main",
    "flatten",
    "strip_overlays",
    "convert",
    "write_output",
    "compile",
)

EXECUTOR = ThreadPoolExecutor(max_workers=2)


@dataclass
class JobRecord:
    id: str
    status: str = "queued"
    current_node: str | None = None
    error: str | None = None
    input_dir: Path | None = None
    output_dir: Path | None = None
    main_tex: str | None = None
    included_tex: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    has_typst: bool = False
    typst_path: Path | None = None
    pdf_path: Path | None = None


class JobStore:
    """Thread-safe in-memory job registry."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = threading.Lock()

    def create(self, **kwargs) -> JobRecord:
        job = JobRecord(id=uuid.uuid4().hex, **kwargs)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **changes) -> None:
        with self._lock:
            job = self._jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_api_jobs.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/api/jobs.py tests/test_api_jobs.py
git commit -m "feat: add in-memory job store"
```

---

### Task 3: Background runner

`run_job` runs the existing graph and records progress and the terminal outcome. It is a plain blocking function (the executor calls it on a worker thread); the test calls it directly, offline, with a `FakeConverter`.

**Files:**
- Modify: `src/b2t/api/jobs.py`
- Test: add to `tests/test_api_jobs.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_api_jobs.py`:

```python
from b2t.api.jobs import run_job
from b2t.llm import FakeConverter
from b2t.typst_runner import typst_available
from tests.conftest import SAMPLE_DECK


def test_run_job_reaches_terminal(tmp_path):
    store = JobStore()
    out = tmp_path / "out"
    job = store.create(input_dir=SAMPLE_DECK, output_dir=out)
    run_job(store, job.id, SAMPLE_DECK, out, FakeConverter("= Hi\n"))
    rec = store.get(job.id)
    assert rec.status in {"succeeded", "compile_failed", "failed"}
    assert rec.main_tex == "main.tex"
    assert rec.images == ["logo.png"]
    assert rec.has_typst is True
    assert rec.typst_path is not None
    if typst_available():
        assert rec.status == "succeeded"
        assert rec.pdf_path is not None


def test_run_job_records_deterministic_failure(tmp_path):
    deck = tmp_path / "deck"
    deck.mkdir()
    (deck / "notes.tex").write_text("just notes", encoding="utf-8")
    store = JobStore()
    job = store.create(input_dir=deck, output_dir=tmp_path / "out")
    run_job(store, job.id, deck, tmp_path / "out", FakeConverter("= Hi\n"))
    rec = store.get(job.id)
    assert rec.status == "failed"
    assert "beamer main" in rec.error
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_jobs.py::test_run_job_reaches_terminal -q`
Expected: FAIL with `ImportError: cannot import name 'run_job'`.

- [ ] **Step 3: Write the implementation**

Add to the top imports of `src/b2t/api/jobs.py` (below the existing `from pathlib import Path`):

```python
from b2t.graph import build_graph
from b2t.llm import ConverterLLM
```

Append to `src/b2t/api/jobs.py`:

```python
def run_job(
    store: JobStore,
    job_id: str,
    input_dir: Path,
    output_dir: Path,
    converter: ConverterLLM,
) -> None:
    """Run the conversion graph, updating the job record as each node completes."""
    graph = build_graph(converter)
    seed = {"input_dir": input_dir, "output_dir": output_dir}
    state = dict(seed)
    store.update(job_id, status="running")
    try:
        for chunk in graph.stream(seed, stream_mode="updates"):
            for node, update in chunk.items():
                state.update(update)
                store.update(job_id, current_node=node)
    except Exception as exc:
        store.update(job_id, status="failed", error=str(exc))
        return

    main_tex = state.get("main_tex")
    store.update(
        job_id,
        main_tex=main_tex.name if main_tex else None,
        included_tex=[p.name for p in state.get("included_tex", [])],
        images=[p.name for p in state.get("image_files", [])],
        has_typst=state.get("typst_source") is not None,
        typst_path=state.get("typst_path"),
    )
    if state.get("compiled"):
        store.update(job_id, status="succeeded", pdf_path=state.get("pdf_path"))
    else:
        store.update(
            job_id, status="compile_failed", error=state.get("compile_error")
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_api_jobs.py -q`
Expected: PASS (5 passed). If the `typst` binary is absent, `test_run_job_reaches_terminal` still passes because the `succeeded`/`pdf_path` assertions are guarded.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/api/jobs.py tests/test_api_jobs.py
git commit -m "feat: add background job runner over the graph"
```

---

### Task 4: Response schemas

Pydantic models for the JSON API plus a mapper from `JobRecord`.

**Files:**
- Create: `src/b2t/api/schemas.py`
- Test: `tests/test_api_schemas.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_api_schemas.py`:

```python
from b2t.api.jobs import JobRecord
from b2t.api.schemas import to_view


def test_to_view_maps_fields():
    rec = JobRecord(
        id="abc",
        status="succeeded",
        current_node="compile",
        main_tex="main.tex",
        included_tex=["intro.tex"],
        images=["logo.png"],
        has_typst=True,
    )
    view = to_view(rec)
    assert view.id == "abc"
    assert view.status == "succeeded"
    assert view.current_node == "compile"
    assert view.included_tex == ["intro.tex"]
    assert view.images == ["logo.png"]
    assert view.has_typst is True
    assert view.has_pdf is False  # pdf_path is None


def test_to_view_has_pdf_false_for_missing_file(tmp_path):
    rec = JobRecord(id="x", status="succeeded", pdf_path=tmp_path / "nope.pdf")
    assert to_view(rec).has_pdf is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_schemas.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'b2t.api.schemas'`.

- [ ] **Step 3: Write the implementation**

Create `src/b2t/api/schemas.py`:

```python
from pathlib import Path

from pydantic import BaseModel

from b2t.api.jobs import JobRecord


class JobCreated(BaseModel):
    job_id: str
    status: str


class JobView(BaseModel):
    id: str
    status: str
    current_node: str | None
    error: str | None
    main_tex: str | None
    included_tex: list[str]
    images: list[str]
    has_typst: bool
    has_pdf: bool


def to_view(job: JobRecord) -> JobView:
    has_pdf = job.pdf_path is not None and Path(job.pdf_path).exists()
    return JobView(
        id=job.id,
        status=job.status,
        current_node=job.current_node,
        error=job.error,
        main_tex=job.main_tex,
        included_tex=job.included_tex,
        images=job.images,
        has_typst=job.has_typst,
        has_pdf=has_pdf,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_api_schemas.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/api/schemas.py tests/test_api_schemas.py
git commit -m "feat: add api response schemas"
```

---

### Task 5: Static frontend page

The single page: a folder picker, a sample button, a fake-converter toggle and model field, an eight-node checklist, and panes for the Typst source, the PDF, and errors. No test of its own; serving is verified in Task 6.

**Files:**
- Create: `src/b2t/api/static/index.html`
- Create: `src/b2t/api/static/style.css`
- Create: `src/b2t/api/static/app.js`

- [ ] **Step 1: Create `src/b2t/api/static/index.html`**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>b2t testing UI</title>
  <link rel="stylesheet" href="/style.css" />
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
      <pre id="typ">(nothing yet)</pre>
      <h2>Compiled PDF</h2>
      <iframe id="pdf" title="compiled pdf"></iframe>
      <h2>Compile error</h2>
      <pre id="error">(none)</pre>
    </section>
  </main>
  <script src="/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create `src/b2t/api/static/style.css`**

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
#nodes { list-style: none; padding: 0; margin: 0.8rem 0 0; display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.3rem; }
#nodes li { padding: 0.25rem 0.5rem; border-radius: 4px; background: #f3eef6; font-size: 0.9rem; }
#nodes li.done { background: #bfe9c6; }
#nodes li.active { background: #ffe9b3; }
pre { background: #1e1e26; color: #eee; padding: 0.8rem; border-radius: 6px; overflow: auto; max-height: 320px; }
iframe { width: 100%; height: 480px; border: 1px solid #e3dbe8; border-radius: 6px; background: #fff; }
```

- [ ] **Step 3: Create `src/b2t/api/static/app.js`**

```javascript
const NODES = [
  "copy_input", "clean_build", "detect_main", "flatten",
  "strip_overlays", "convert", "write_output", "compile",
];
const TERMINAL = ["succeeded", "compile_failed", "failed"];

const $ = (id) => document.getElementById(id);

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

async function finish(id, job) {
  setBusy(false);
  const typ = await fetch(`/api/jobs/${id}/typ`);
  $("typ").textContent = typ.ok ? await typ.text() : "(no typst output)";
  $("pdf").src = job.has_pdf ? `/api/jobs/${id}/pdf` : "about:blank";
  $("error").textContent = job.error || "(none)";
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
  $("typ").textContent = "(running)";
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
```

- [ ] **Step 4: Commit**

```bash
git add src/b2t/api/static
git commit -m "feat: add static testing UI page"
```

---

### Task 6: FastAPI app and endpoints

The app factory: the five routes, converter selection, upload reconstruction with a path-traversal guard, and the static mount. Tested end to end with `TestClient` and the `FakeConverter`, fully offline.

**Files:**
- Create: `src/b2t/api/app.py`
- Test: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_api_app.py`:

```python
import time

from fastapi.testclient import TestClient

from b2t.api.app import create_app
from b2t.typst_runner import typst_available
from tests.conftest import SAMPLE_DECK

TERMINAL = {"succeeded", "compile_failed", "failed"}


def _client():
    return TestClient(create_app())


def _wait_terminal(client, job_id, timeout=30.0):
    deadline = time.monotonic() + timeout
    body = None
    while time.monotonic() < deadline:
        body = client.get(f"/api/jobs/{job_id}").json()
        if body["status"] in TERMINAL:
            return body
        time.sleep(0.1)
    raise AssertionError(f"job did not finish: {body}")


def _sample_files():
    files = []
    for path in sorted(SAMPLE_DECK.rglob("*")):
        if path.is_file():
            rel = "sample_deck/" + str(path.relative_to(SAMPLE_DECK)).replace("\\", "/")
            files.append(("files", (rel, path.read_bytes(), "application/octet-stream")))
    return files


def test_unknown_job_returns_404():
    assert _client().get("/api/jobs/does-not-exist").status_code == 404


def test_sample_job_runs_and_exposes_typ():
    client = _client()
    res = client.post("/api/jobs/sample", data={"use_fake": "true"})
    assert res.status_code == 200
    job_id = res.json()["job_id"]
    body = _wait_terminal(client, job_id)
    assert body["status"] in TERMINAL
    assert body["main_tex"] == "main.tex"
    typ = client.get(f"/api/jobs/{job_id}/typ")
    assert typ.status_code == 200
    assert "Sample" in typ.text
    if typst_available():
        assert body["status"] == "succeeded"
        assert body["has_pdf"] is True
        assert client.get(f"/api/jobs/{job_id}/pdf").status_code == 200


def test_folder_upload_reconstructs_and_runs():
    client = _client()
    res = client.post("/api/jobs", data={"use_fake": "true"}, files=_sample_files())
    assert res.status_code == 200
    body = _wait_terminal(client, res.json()["job_id"])
    assert body["status"] in TERMINAL
    assert body["images"] == ["logo.png"]
    assert "intro.tex" in body["included_tex"]


def test_broken_deck_reports_failed():
    client = _client()
    files = [("files", ("deck/notes.tex", b"just notes", "text/plain"))]
    res = client.post("/api/jobs", data={"use_fake": "true"}, files=files)
    body = _wait_terminal(client, res.json()["job_id"])
    assert body["status"] == "failed"
    assert "beamer main" in body["error"]


def test_empty_upload_is_rejected():
    # no files part: rejected without creating a job (400 from our guard, or
    # 422 if FastAPI rejects the missing multipart first)
    code = _client().post("/api/jobs", data={"use_fake": "true"}).status_code
    assert code in (400, 422)


def test_serves_index_at_root():
    res = _client().get("/")
    assert res.status_code == 200
    assert 'id="app"' in res.text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_api_app.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'b2t.api.app'`.

- [ ] **Step 3: Write the implementation**

Create `src/b2t/api/app.py`:

```python
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from b2t.api.jobs import EXECUTOR, JobStore, run_job
from b2t.api.schemas import JobCreated, JobView, to_view
from b2t.config import REPO_ROOT
from b2t.llm import ConverterLLM, FakeConverter, OpenAIConverter

SAMPLE_DECK = REPO_ROOT / "tests" / "fixtures" / "sample_deck"
STATIC_DIR = Path(__file__).parent / "static"
FAKE_TYPST = (
    "#set page(width: 16cm, height: 9cm)\n"
    "= Sample\n\nGenerated by the fake converter.\n"
)


def _make_converter(use_fake: bool, model: str) -> ConverterLLM:
    if use_fake:
        return FakeConverter(FAKE_TYPST)
    return OpenAIConverter(model=model or None)


def _reconstruct(files: list[UploadFile], root: Path) -> None:
    """Write each uploaded file under root at its relative path. Reject escapes."""
    root = root.resolve()
    for upload in files:
        rel = upload.filename or ""
        target = (root / rel).resolve()
        if not str(target).startswith(str(root)):
            raise HTTPException(status_code=400, detail="invalid path in upload")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(upload.file.read())


def create_app(store: JobStore | None = None) -> FastAPI:
    load_dotenv()
    app = FastAPI(title="b2t testing UI")
    jobs = store or JobStore()

    @app.post("/api/jobs", response_model=JobCreated)
    async def create_job(
        files: list[UploadFile] = File([]),
        use_fake: bool = Form(False),
        model: str = Form(""),
    ):
        if not files:
            raise HTTPException(status_code=400, detail="no files submitted")
        root = Path(tempfile.mkdtemp(prefix="b2t_upload_"))
        _reconstruct(files, root)
        output_dir = root.parent / (root.name + "_out")
        job = jobs.create(input_dir=root, output_dir=output_dir)
        EXECUTOR.submit(
            run_job, jobs, job.id, root, output_dir, _make_converter(use_fake, model)
        )
        return JobCreated(job_id=job.id, status=job.status)

    @app.post("/api/jobs/sample", response_model=JobCreated)
    async def create_sample_job(use_fake: bool = Form(False), model: str = Form("")):
        output_dir = Path(tempfile.mkdtemp(prefix="b2t_sample_")) / "out"
        job = jobs.create(input_dir=SAMPLE_DECK, output_dir=output_dir)
        EXECUTOR.submit(
            run_job, jobs, job.id, SAMPLE_DECK, output_dir,
            _make_converter(use_fake, model),
        )
        return JobCreated(job_id=job.id, status=job.status)

    @app.get("/api/jobs/{job_id}", response_model=JobView)
    def get_job(job_id: str):
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="unknown job")
        return to_view(job)

    @app.get("/api/jobs/{job_id}/typ")
    def get_typ(job_id: str):
        job = jobs.get(job_id)
        if job is None or job.typst_path is None:
            raise HTTPException(status_code=404, detail="no typst output")
        return PlainTextResponse(Path(job.typst_path).read_text(encoding="utf-8"))

    @app.get("/api/jobs/{job_id}/pdf")
    def get_pdf(job_id: str):
        job = jobs.get(job_id)
        if job is None or job.pdf_path is None or not Path(job.pdf_path).exists():
            raise HTTPException(status_code=404, detail="no pdf output")
        return FileResponse(Path(job.pdf_path), media_type="application/pdf")

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


app = create_app()
```

Note: `_reconstruct` uses `upload.file.read()` (the synchronous file object) so it works whether or not the handler awaits. The static mount is added last so the `/api/...` routes match first.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_api_app.py -q`
Expected: PASS (6 passed). With `typst` installed the sample job reaches `succeeded` and the pdf assertions run; without it, the guarded assertions are skipped and the rest still pass.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -q`
Expected: all tests pass (the existing 34 plus the new api tests).

- [ ] **Step 6: Commit**

```bash
git add src/b2t/api/app.py tests/test_api_app.py
git commit -m "feat: add fastapi app and endpoints"
```

---

### Task 7: README usage section

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a "Run the testing UI" section**

Append to `README.md` (after the existing "Run (v0)" section):

```markdown
## Run the testing UI

A thin browser UI for converting a deck folder and inspecting the result.

```bash
uv run uvicorn b2t.api.app:app --reload
```

Open http://127.0.0.1:8000. Click "Use sample deck" for a one-click run, or
pick a deck folder with the folder chooser. Tick "use fake converter (offline)"
to exercise the pipeline without calling OpenAI. The page shows per-node
progress, the generated `main.typ`, the compiled PDF, and any compile error.

A real conversion needs `OPENAI_API_KEY` in `.env` and the `typst` CLI on PATH.
```

- [ ] **Step 2: Verify the server boots**

Run (start, confirm it serves, then stop):

```bash
uv run python -c "from fastapi.testclient import TestClient; from b2t.api.app import app; print(TestClient(app).get('/').status_code)"
```

Expected: prints `200`.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document the testing UI"
```

---

## Self-review

**Spec coverage** (each spec section maps to a task):
- FastAPI backend plus thin static frontend -> Tasks 1, 5, 6.
- Async job model (POST returns job_id, page polls) -> Tasks 3, 6 (endpoints), 5 (poll in app.js).
- Folder picker via webkitdirectory, loose files reassembled server-side -> Task 5 (`index.html` input, `app.js` FormData with `webkitRelativePath`), Task 6 (`_reconstruct`).
- Sample-deck convenience endpoint -> Task 6 (`/api/jobs/sample`).
- Per-node progress via `graph.stream` -> Task 3 (`run_job`), Task 5 (node checklist).
- Converter selectable (real or fake) reusing ConverterLLM -> Task 6 (`_make_converter`).
- In-memory thread-safe job store -> Task 2.
- Job model and status enum (queued/running/succeeded/compile_failed/failed) -> Tasks 2, 3.
- API surface (POST /api/jobs, POST /api/jobs/sample, GET /api/jobs/{id}, /typ, /pdf) -> Task 6.
- JobView with has_pdf and small state view -> Task 4.
- Error handling: deterministic failure -> failed; bad upload -> 400; unknown id -> 404; compile failure -> compile_failed -> Tasks 3, 6 (tests cover all four).
- Testing with TestClient and FakeConverter, typst-guarded assertions -> Tasks 3, 6.
- Pipeline untouched -> no task modifies `graph.py`, `nodes/`, `state.py`, `latex/`.

**Placeholder scan:** none. Every code step contains complete code. The only
free value is the OpenAI model, taken from the `model` form field or the
existing `OPENAI_MODEL` default.

**Type consistency:** `JobStore.create/get/update` and `JobRecord` fields are
used identically in `run_job` (Task 3), `to_view` (Task 4), and the endpoints
(Task 6). `run_job(store, job_id, input_dir, output_dir, converter)` is called
with that exact signature by `EXECUTOR.submit` in both POST handlers. `PIPELINE_NODES`
(Task 2) matches the `NODES` array in `app.js` (Task 5) and the verified stream
order. `JobCreated(job_id, status)` and `JobView` fields match what the tests in
Task 6 read (`job_id`, `status`, `main_tex`, `images`, `included_tex`, `has_pdf`).
The graph reads `image_files` from state; `run_job` maps it to the record field
`images`, which `to_view` exposes as `images`.

**Out-of-scope guard:** no auth, no database, no persistence across restarts, no
HITL pause/resume, no real sandboxing. The in-memory store and status enum leave
room for those later, consistent with the spec's non-goals.
