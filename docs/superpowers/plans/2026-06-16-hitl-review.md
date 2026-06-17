# Per-Frame Human-in-the-Loop Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a reviewer approve or regenerate (with feedback) each converted frame, pausing the LangGraph pipeline per frame, driven from the testing UI, while the library path and existing tests behave exactly as before.

**Architecture:** The per-frame loop becomes `convert -> preview -> review`. `convert` produces a candidate (no commit), `preview` compiles the deck-so-far (HITL only), and `review` either auto-approves (HITL off) or pauses on a LangGraph `interrupt()` and resumes on the reviewer's decision. An in-memory checkpointer plus a per-job thread id makes pause/resume work; `run_job` is split into an initial run and a `resume_job`.

**Tech Stack:** Python 3.12, LangGraph 1.2.4 (`interrupt`, `Command`, `InMemorySaver`), Pydantic v2, FastAPI, pytest, vanilla JS.

## Global Constraints

- Use `uv` for everything: `uv run pytest`, `uv run python`. Never call `python`/`pip` directly.
- No new third-party dependencies (the checkpointer is the built-in `InMemorySaver`).
- The generated deck must never use overlays/pause.
- The LLM node stays registered in the graph under the name `convert`.
- Deterministic vs LLM boundary preserved; nodes stay thin, helpers do the work.
- No emojis. No em or en dashes in code or prose.
- `hitl_enabled` defaults `False`, so `convert_deck` and every existing test path is unchanged.
- End each commit message with: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- Gate commits on a real test run: `if uv run pytest -q; then git commit ...; fi` (piping pytest into `tail` masks its exit code).

---

### Task 1: HITL state fields

**Files:**
- Modify: `src/b2t/state.py`
- Test: `tests/test_state.py`

**Interfaces:**
- Produces: `PipelineState` fields `hitl_enabled: bool`, `candidate: str | None`, `feedback: str | None`, `preview_path: Path | None`, `preview_pdf: Path | None`, `preview_error: str | None`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_state.py`:

```python
def test_hitl_fields_default():
    s = PipelineState(input_dir=Path("in"), output_dir=Path("out"))
    assert s.hitl_enabled is False
    assert s.candidate is None
    assert s.feedback is None
    assert s.preview_path is None
    assert s.preview_pdf is None
    assert s.preview_error is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_state.py::test_hitl_fields_default -v`
Expected: FAIL with `AttributeError`/validation error on `hitl_enabled`.

- [ ] **Step 3: Write minimal implementation**

In `src/b2t/state.py`, add to `PipelineState` after the `converted_frames` field:

```python
    # human-in-the-loop review
    hitl_enabled: bool = False
    candidate: str | None = None
    feedback: str | None = None
    preview_path: Path | None = None
    preview_pdf: Path | None = None
    preview_error: str | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_state.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/state.py tests/test_state.py
git commit -m "feat: add HITL review state fields"
```

---

### Task 2: Feedback-aware prompt convert/v4

**Files:**
- Create: `prompts/convert/v4.toml`
- Test: `tests/test_prompts.py`

**Interfaces:**
- Produces: prompt `convert/v4` with tokens `{{reference}}`, `{{guides}}`, `{{preamble}}`, `{{feedback}}`, `{{frame}}`. Default stays `v3` in this task.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_prompts.py`:

```python
def test_real_convert_v4_is_feedback_aware():
    pv = P.load("convert", "v4")
    for token in ("{{reference}}", "{{guides}}", "{{preamble}}", "{{feedback}}", "{{frame}}"):
        assert token in pv.user_template
    assert pv.user_template.rstrip().endswith("{{frame}}")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_prompts.py::test_real_convert_v4_is_feedback_aware -v`
Expected: FAIL with `FileNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

Create `prompts/convert/v4.toml` (literal `'''` strings; do not escape backslashes):

```toml
# v4 is feedback-aware: it adds an optional {{feedback}} block so a reviewer's
# regenerate request can steer the next attempt. The convert node supplies an
# empty string when there is no feedback. v1/v2/v3 are kept for history.
description = "v4 - per-frame, feedback-aware"

system = '''You convert a single LaTeX Beamer frame into Typst Touying source for a presentation using the university theme. Output only the Typst for this one frame: a level-2 heading (==) carrying the frame title, followed by the converted body. Do not emit any imports, theme setup, title slide, outline, or preamble; those are generated separately. Use the provided reference presentation for body syntax and the guides for math. Map citation commands (\cite, \citep, \citet, \textcite, \parencite) to Typst @key references. Output only Typst source, with no commentary. Never use overlays or pause functionality.'''

user_template = '''
Reference Touying presentation (for body syntax and conventions):

{{reference}}

Guides:

{{guides}}

The Beamer preamble (context only, for custom macros; do not translate it):

{{preamble}}
{{feedback}}
Convert this single Beamer frame to Typst Touying source (a == heading plus body):

{{frame}}'''
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_prompts.py -v`
Expected: PASS (v4 test passes; the existing "default is v3" test still passes because the default is unchanged).

- [ ] **Step 5: Commit**

```bash
git add prompts/convert/v4.toml tests/test_prompts.py
git commit -m "feat: add feedback-aware convert/v4 prompt"
```

---

### Task 3: preview node

**Files:**
- Create: `src/b2t/nodes/preview.py`
- Test: `tests/test_nodes.py`

**Interfaces:**
- Consumes: `typst_scaffold.assemble`, `typst_runner.compile_typst`.
- Produces: `preview_node(state: PipelineState) -> dict` returning `preview_path`, `preview_pdf`, `preview_error` (or `{}` when `hitl_enabled` is False).

- [ ] **Step 1: Write the failing test**

Add to `tests/test_nodes.py`:

```python
def test_preview_node_skips_when_hitl_disabled():
    from b2t.nodes.preview import preview_node
    from b2t.state import FrameUnit

    state = _state(hitl_enabled=False, frames=[FrameUnit(raw="")], candidate="== X\n\nb")
    assert preview_node(state) == {}


def test_preview_node_assembles_without_bibliography(tmp_path):
    from b2t.nodes.preview import preview_node
    from b2t.state import DeckMeta, FrameUnit

    state = _state(
        output_dir=tmp_path / "out",
        hitl_enabled=True,
        meta=DeckMeta(title="T"),
        frames=[FrameUnit(raw="", section=None)],
        frame_index=0,
        converted_frames=[],
        candidate="== Slide\n\nbody",
        bib_file=tmp_path / "references.bib",
    )
    update = preview_node(state)
    assert update["preview_path"] == tmp_path / "out" / "preview.typ"
    text = (tmp_path / "out" / "preview.typ").read_text(encoding="utf-8")
    assert "== Slide" in text
    assert "#title-slide()" in text
    assert "#bibliography" not in text  # previews never show the bibliography
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_nodes.py::test_preview_node_skips_when_hitl_disabled -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'b2t.nodes.preview'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/b2t/nodes/preview.py`:

```python
from loguru import logger

from b2t.state import PipelineState
from b2t.typst_runner import compile_typst
from b2t.typst_scaffold import assemble


def preview_node(state: PipelineState) -> dict:
    """Compile a preview of the deck so far, for human review (HITL only).

    Assembles the header, already-approved frames, and the current candidate
    (no bibliography or thank-you slide) and compiles it. A no-op when review is
    disabled, so the library and offline paths skip the extra compile.

    Returns:
        State update with preview_path, preview_pdf, and preview_error; an empty
        dict when hitl_enabled is False.
    """
    if not state.hitl_enabled:
        return {}
    converted = [*state.converted_frames, state.candidate]
    frames = state.frames[: state.frame_index + 1]
    source = assemble(
        state.meta, state.aspect_ratio, state.has_toc, frames, converted, None
    )
    state.output_dir.mkdir(parents=True, exist_ok=True)
    preview_path = state.output_dir / "preview.typ"
    preview_path.write_text(source, encoding="utf-8")
    result = compile_typst(preview_path)
    logger.debug("preview frame {} ok={}", state.frame_index + 1, result.ok)
    return {
        "preview_path": preview_path,
        "preview_pdf": result.pdf_path,
        "preview_error": result.error,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_nodes.py -k preview -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/nodes/preview.py tests/test_nodes.py
git commit -m "feat: add preview node that compiles the deck so far"
```

---

### Task 4: review node

**Files:**
- Create: `src/b2t/nodes/review.py`
- Test: `tests/test_nodes.py`

**Interfaces:**
- Consumes: `langgraph.types.interrupt`.
- Produces: `review_node(state: PipelineState) -> dict`. Off-HITL: commits the candidate and advances. On-HITL: `interrupt(payload)` then approve (commit/advance) or regenerate (store feedback, index unchanged).

- [ ] **Step 1: Write the failing test**

Add to `tests/test_nodes.py`:

```python
def test_review_node_auto_approves_when_hitl_disabled():
    from b2t.nodes.review import review_node
    from b2t.state import FrameUnit

    state = _state(
        hitl_enabled=False,
        frames=[FrameUnit(raw=""), FrameUnit(raw="")],
        frame_index=0,
        converted_frames=[],
        candidate="== X\n\nbody",
    )
    update = review_node(state)
    assert update["converted_frames"] == ["== X\n\nbody"]
    assert update["frame_index"] == 1
    assert update["candidate"] is None
    assert update["feedback"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_nodes.py::test_review_node_auto_approves_when_hitl_disabled -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'b2t.nodes.review'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/b2t/nodes/review.py`:

```python
from langgraph.types import interrupt
from loguru import logger

from b2t.state import PipelineState


def _approve(state: PipelineState) -> dict:
    """Commit the candidate frame and advance to the next."""
    return {
        "converted_frames": [*state.converted_frames, state.candidate],
        "frame_index": state.frame_index + 1,
        "candidate": None,
        "feedback": None,
    }


def review_node(state: PipelineState) -> dict:
    """Approve or regenerate the candidate frame.

    Without HITL, auto-approves. With HITL, pauses on an interrupt carrying the
    review payload and resumes on the reviewer's decision: approve commits and
    advances; regenerate stores feedback and leaves the frame in place so the
    convert node re-runs it.
    """
    if not state.hitl_enabled:
        return _approve(state)
    decision = interrupt(
        {
            "frame_index": state.frame_index,
            "total": len(state.frames),
            "candidate": state.candidate,
            "preview_ok": state.preview_pdf is not None and state.preview_error is None,
            "preview_error": state.preview_error,
        }
    )
    if decision.get("action") == "approve":
        return _approve(state)
    logger.debug("regenerate frame {}", state.frame_index + 1)
    return {"feedback": decision.get("feedback"), "candidate": None}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_nodes.py::test_review_node_auto_approves_when_hitl_disabled -v`
Expected: PASS. (The interrupt path is exercised by the graph test in Task 5.)

- [ ] **Step 5: Commit**

```bash
git add src/b2t/nodes/review.py tests/test_nodes.py
git commit -m "feat: add review node (auto-approve or interrupt)"
```

---

### Task 5: Wire the review loop (atomic switch)

Refactors `convert` to produce a candidate, rewires the graph into `convert -> preview -> review`, adds the optional checkpointer, flips the default prompt to v4, guards `run_job` against `None` updates, and updates every test the switch breaks.

**Files:**
- Modify: `src/b2t/nodes/convert_frame.py`
- Modify: `src/b2t/graph.py`
- Modify: `prompts/defaults.json`
- Modify: `src/b2t/api/jobs.py` (only the `None`-update guard here)
- Modify/Test: `tests/test_nodes.py`, `tests/test_graph.py`, `tests/test_prompts.py`, `tests/test_llm_node.py`, `tests/test_api_app.py`, `tests/test_api_jobs.py`

**Interfaces:**
- Consumes: `preview_node`, `review_node` (Tasks 3-4).
- Produces: `build_graph(client, checkpointer=None)`; `convert_frame` returns `{"candidate", "llm_runs", "llm_rendered"}`; the graph is `... split_deck -> convert -> preview -> review -> {convert | assemble} -> ...`.

- [ ] **Step 1: Write/adjust the failing tests**

In `tests/test_nodes.py`, replace `test_convert_frame_appends_and_advances` with:

```python
def test_convert_frame_sets_candidate_without_committing():
    from b2t.llm import FakeClient
    from b2t.nodes.convert_frame import convert_frame
    from b2t.state import FrameUnit

    state = _state(preamble="PRE", frames=[FrameUnit(raw="f0")], frame_index=0)
    update = convert_frame(state, client=FakeClient("== Title\n\nbody\n"))
    assert update["candidate"] == "== Title\n\nbody\n"
    assert "frame_index" not in update
    assert "converted_frames" not in update
    assert update["llm_runs"]["convert"].prompt_version == "v4"


def test_convert_frame_includes_feedback_when_present():
    from b2t.nodes.convert_frame import convert_frame
    from b2t.state import FrameUnit

    captured = {}

    class Recorder:
        def complete(self, system, user, model):
            captured["user"] = user
            return "== ok\n"

    state = _state(
        preamble="P", frames=[FrameUnit(raw="F")], frame_index=0, feedback="make it bold"
    )
    convert_frame(state, client=Recorder())
    assert "make it bold" in captured["user"]
```

In `tests/test_graph.py`, append HITL tests (keep the existing two straight-through tests unchanged):

```python
def test_hitl_graph_pauses_then_approves_all(tmp_path):
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import Command

    graph = build_graph(FakeClient(FRAME_BODY), checkpointer=InMemorySaver())
    cfg = {"configurable": {"thread_id": "t1"}}
    seed = {"input_dir": DECK1, "output_dir": tmp_path / "out", "hitl_enabled": True}
    chunks = list(graph.stream(seed, config=cfg, stream_mode=["updates"]))
    interrupts = [
        chunk["__interrupt__"][0].value for mode, chunk in chunks if "__interrupt__" in chunk
    ]
    assert interrupts and interrupts[0]["frame_index"] == 0
    assert interrupts[0]["total"] == 4
    for _ in range(4):
        list(graph.stream(Command(resume={"action": "approve"}), config=cfg, stream_mode=["updates"]))
    final = graph.get_state(cfg).values
    assert final["typst_source"].count("== Slide") == 4


def test_hitl_graph_regenerate_reconverts_with_feedback(tmp_path):
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import Command

    calls = []

    class Recorder:
        def complete(self, system, user, model):
            calls.append(user)
            return FRAME_BODY

    graph = build_graph(Recorder(), checkpointer=InMemorySaver())
    cfg = {"configurable": {"thread_id": "t2"}}
    seed = {"input_dir": DECK1, "output_dir": tmp_path / "out", "hitl_enabled": True}
    list(graph.stream(seed, config=cfg, stream_mode=["updates"]))
    n_before = len(calls)
    list(graph.stream(
        Command(resume={"action": "regenerate", "feedback": "make it bold"}),
        config=cfg, stream_mode=["updates"],
    ))
    assert len(calls) == n_before + 1          # convert re-ran the same frame
    assert "make it bold" in calls[-1]         # feedback reached the prompt
```

In `tests/test_prompts.py`, replace `test_real_convert_default_is_v3` with:

```python
def test_real_convert_default_is_v4():
    assert P.default_version("convert") == "v4"


def test_real_convert_v3_still_loadable():
    pv = P.load("convert", "v3")
    assert "{{frame}}" in pv.user_template
    assert "{{feedback}}" not in pv.user_template
```

In `tests/test_llm_node.py`: add `"feedback": "FB"` to `_VALUES`, and update `test_run_prompt_uses_defaults_and_returns_run` to expect v4:

```python
_VALUES = {
    "reference": "R",
    "guides": "G",
    "source": "SRC",
    "aspect_ratio": "4-3",
    "preamble": "PRE",
    "feedback": "FB",
    "frame": "FRAMEBODY",
}
```

```python
    assert run == NodeRun(model=DEFAULT_MODEL, prompt_version="v4")
    assert "FRAMEBODY" in rendered.user
```

In `tests/test_api_app.py`:
- `test_llm_nodes_endpoint_lists_convert_with_versions`: change `== "v3"` to `== "v4"`.
- `test_rendered_prompt_available_after_run`: change `== "v3"` to `== "v4"`.
- Replace the body of `test_node_state_available_after_run` with:

```python
def test_node_state_available_after_run():
    client = _client()
    job_id = _run_sample(client)
    body = client.get(f"/api/jobs/{job_id}/state/convert").json()
    assert "candidate" in body["changed"]
    review = client.get(f"/api/jobs/{job_id}/state/review").json()
    assert "converted_frames" in review["changed"]
    asm = client.get(f"/api/jobs/{job_id}/state/assemble").json()
    assert "typst_source" in asm["changed"]
```

In `tests/test_api_jobs.py`:
- Rename `test_pipeline_nodes_are_the_ten_in_order` to `..._twelve...` and set the tuple to the 12 nodes:

```python
    assert PIPELINE_NODES == (
        "copy_input",
        "clean_build",
        "detect_main",
        "flatten",
        "strip_overlays",
        "split_deck",
        "convert",
        "preview",
        "review",
        "assemble",
        "write_output",
        "compile",
    )
```

- In `test_run_job_records_llm_runs`, change `"prompt_version": "v3"` to `"v4"`.
- In `test_run_job_captures_node_deltas`, change the convert-delta assertion and add the review delta:

```python
    convert = next(d for d in rec.node_deltas if d.node == "convert")
    assert "candidate" in convert.changed
    review = next(d for d in rec.node_deltas if d.node == "review")
    assert "converted_frames" in review.changed
```

(The distinct-nodes `seen == list(PIPELINE_NODES)` block stays; `preview` appears with an empty `changed`.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_graph.py -v`
Expected: FAIL (graph still has the old `convert (cycle)` wiring; `preview`/`review` not wired; default still v3).

- [ ] **Step 3: Make the implementation changes**

(a) `src/b2t/nodes/convert_frame.py` - replace the file:

```python
from loguru import logger

from b2t.config import MATH_GUIDE, REFERENCE_DECK
from b2t.llm import LLMClient
from b2t.nodes._llm import run_prompt
from b2t.state import PipelineState
from b2t.typst_output import strip_code_fence


def _feedback_block(feedback: str | None) -> str:
    """Frame reviewer feedback for the prompt, or empty when there is none."""
    if not feedback:
        return ""
    return (
        "\nThe reviewer reviewed a previous attempt at this frame and asked for "
        f"these changes; address them:\n{feedback}\n"
    )


def convert_frame(state: PipelineState, client: LLMClient) -> dict:
    """Produce a candidate Typst conversion for the current frame.

    Does not commit or advance; the review node does that on approval. Uses
    state.feedback to steer a regeneration. Registered in the graph as `convert`.

    Returns:
        State update with candidate plus merged provenance under the `convert`
        key.
    """
    frame = state.frames[state.frame_index]
    reference = REFERENCE_DECK.read_text(encoding="utf-8")
    guides = MATH_GUIDE.read_text(encoding="utf-8")
    logger.info("converting frame {}/{}", state.frame_index + 1, len(state.frames))
    output, run, rendered = run_prompt(
        state,
        "convert",
        client,
        {
            "reference": reference,
            "guides": guides,
            "preamble": state.preamble or "",
            "feedback": _feedback_block(state.feedback),
            "frame": frame.raw,
        },
    )
    return {
        "candidate": strip_code_fence(output),
        "llm_runs": {**state.llm_runs, "convert": run},
        "llm_rendered": {**state.llm_rendered, "convert": rendered},
    }
```

(b) `src/b2t/graph.py` - replace the file:

```python
from functools import partial

from langgraph.graph import END, START, StateGraph

from b2t.llm import LLMClient
from b2t.nodes.assemble import assemble_node
from b2t.nodes.clean_build import clean_build
from b2t.nodes.compile import compile_node
from b2t.nodes.convert_frame import convert_frame
from b2t.nodes.copy_input import copy_input
from b2t.nodes.detect_main import detect_main
from b2t.nodes.flatten import flatten_node
from b2t.nodes.preview import preview_node
from b2t.nodes.review import review_node
from b2t.nodes.split_deck import split_deck
from b2t.nodes.strip_overlays import strip_overlays_node
from b2t.nodes.write_output import write_output
from b2t.state import PipelineState


def _more_frames(state: PipelineState) -> str:
    """Loop back to convert while frames remain, else move on to assemble."""
    return "convert" if state.frame_index < len(state.frames) else "assemble"


def build_graph(client: LLMClient, checkpointer=None):
    """Build and compile the per-frame conversion graph with optional review.

    Args:
        client: LLM client bound into the convert node.
        checkpointer: Optional LangGraph checkpointer; required for HITL pause
            and resume. Omit it (None) for the straight-through library path.

    Returns:
        A compiled LangGraph runnable: ... -> split_deck -> convert -> preview ->
        review (self-loop over frames) -> assemble -> write_output -> compile.
    """
    graph = StateGraph(PipelineState)

    graph.add_node("copy_input", copy_input)
    graph.add_node("clean_build", clean_build)
    graph.add_node("detect_main", detect_main)
    graph.add_node("flatten", flatten_node)
    graph.add_node("strip_overlays", strip_overlays_node)
    graph.add_node("split_deck", split_deck)
    graph.add_node("convert", partial(convert_frame, client=client))
    graph.add_node("preview", preview_node)
    graph.add_node("review", review_node)
    graph.add_node("assemble", assemble_node)
    graph.add_node("write_output", write_output)
    graph.add_node("compile", compile_node)

    graph.add_edge(START, "copy_input")
    graph.add_edge("copy_input", "clean_build")
    graph.add_edge("clean_build", "detect_main")
    graph.add_edge("detect_main", "flatten")
    graph.add_edge("flatten", "strip_overlays")
    graph.add_edge("strip_overlays", "split_deck")
    graph.add_edge("split_deck", "convert")
    graph.add_edge("convert", "preview")
    graph.add_edge("preview", "review")
    graph.add_conditional_edges(
        "review", _more_frames, {"convert": "convert", "assemble": "assemble"}
    )
    graph.add_edge("assemble", "write_output")
    graph.add_edge("write_output", "compile")
    graph.add_edge("compile", END)

    return graph.compile(checkpointer=checkpointer)
```

(c) `prompts/defaults.json`:

```json
{
  "convert": "v4"
}
```

(d) `src/b2t/api/jobs.py` - guard the delta loop against `None` updates (a node returning `{}` streams as `None`). Change the `else` branch of the stream loop in `run_job`:

```python
            else:
                for node_name, update in chunk.items():
                    update = update or {}
                    state.update(update)
                    store.append_delta(
                        job_id,
                        NodeDelta(node_name, list(update), serialize_values(update)),
                    )
```

- [ ] **Step 4: Run the full suite to verify it passes**

Run: `uv run pytest -q`
Expected: PASS. (Straight-through deck1/deck2 still assemble and compile; HITL graph tests pause and resume.)

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: wire convert -> preview -> review loop with optional checkpointer"
```

---

### Task 6: Checkpointer, run/resume split (jobs layer)

**Files:**
- Modify: `src/b2t/api/jobs.py`
- Test: `tests/test_api_jobs.py`

**Interfaces:**
- Produces: module-level `CHECKPOINTER = InMemorySaver()`; `JobRecord` fields `hitl: bool`, `use_fake: bool`, `choices: dict`, `review: dict | None`; `run_job(store, job_id, input_dir, output_dir, make_client, choices=None, hitl=False)`; `resume_job(store, job_id, action, feedback, make_client)`. Both pause to status `awaiting_review` (storing the interrupt payload in `review`) or finalize.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_api_jobs.py`:

```python
def test_run_job_hitl_pauses_awaiting_review(tmp_path):
    from b2t.api.jobs import run_job

    store = JobStore()
    out = tmp_path / "out"
    job = store.create(input_dir=SAMPLE_DECK, output_dir=out)
    run_job(store, job.id, SAMPLE_DECK, out, lambda: FakeClient("== S\n\nb\n"), hitl=True)
    rec = store.get(job.id)
    assert rec.status == "awaiting_review"
    assert rec.review["frame_index"] == 0
    assert rec.review["total"] == 4


def test_resume_job_approve_advances_then_finishes(tmp_path):
    from b2t.api.jobs import resume_job, run_job

    store = JobStore()
    out = tmp_path / "out"
    job = store.create(input_dir=SAMPLE_DECK, output_dir=out)
    run_job(store, job.id, SAMPLE_DECK, out, lambda: FakeClient("== S\n\nb\n"), hitl=True)
    for _ in range(4):
        resume_job(store, job.id, "approve", None, lambda: FakeClient("== S\n\nb\n"))
    rec = store.get(job.id)
    assert rec.status in {"succeeded", "compile_failed"}
    assert rec.has_typst is True


def test_resume_job_regenerate_stays_on_same_frame(tmp_path):
    from b2t.api.jobs import resume_job, run_job

    store = JobStore()
    out = tmp_path / "out"
    job = store.create(input_dir=SAMPLE_DECK, output_dir=out)
    run_job(store, job.id, SAMPLE_DECK, out, lambda: FakeClient("== S\n\nb\n"), hitl=True)
    resume_job(store, job.id, "regenerate", "use bullets", lambda: FakeClient("== S\n\nb\n"))
    rec = store.get(job.id)
    assert rec.status == "awaiting_review"
    assert rec.review["frame_index"] == 0  # still the first frame
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_jobs.py::test_run_job_hitl_pauses_awaiting_review -v`
Expected: FAIL (`run_job` has no `hitl` parameter / no pause handling).

- [ ] **Step 3: Write the implementation**

In `src/b2t/api/jobs.py`, add imports near the top:

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
```

Add the shared checkpointer after `EXECUTOR`:

```python
CHECKPOINTER = InMemorySaver()
```

Add `hitl`, `use_fake`, `choices`, and `review` to `JobRecord` (after the existing fields):

```python
    hitl: bool = False
    use_fake: bool = False
    choices: dict = field(default_factory=dict)
    review: dict | None = None
```

Replace `run_job` with a drive helper, a finalizer, and the run/resume entry points:

```python
def _drive(store, job_id, graph, stream_input, config, state) -> tuple[bool, dict | None]:
    """Stream until an interrupt or the end. Returns (paused, review_payload).

    Records current_node from debug task events and node deltas from updates.
    """
    paused = False
    payload = None
    for mode, chunk in graph.stream(stream_input, config=config, stream_mode=["updates", "debug"]):
        if mode == "debug":
            if chunk.get("type") == "task":
                store.update(job_id, current_node=chunk["payload"]["name"])
            continue
        if "__interrupt__" in chunk:
            payload = chunk["__interrupt__"][0].value
            paused = True
            continue
        for node_name, update in chunk.items():
            update = update or {}
            state.update(update)
            store.append_delta(
                job_id, NodeDelta(node_name, list(update), serialize_values(update))
            )
    return paused, payload


def _finalize(store, job_id, final: dict) -> None:
    """Project the final pipeline state onto the job record and set status."""
    main_tex = final.get("main_tex")
    runs = final.get("llm_runs", {})
    rendered = final.get("llm_rendered", {})
    store.update(
        job_id,
        main_tex=main_tex.name if main_tex else None,
        included_tex=[p.name for p in final.get("included_tex", [])],
        images=[p.name for p in final.get("image_files", [])],
        has_typst=final.get("typst_source") is not None,
        typst_path=final.get("typst_path"),
        review=None,
        llm_runs={
            node: {"model": run.model, "prompt_version": run.prompt_version}
            for node, run in runs.items()
        },
        llm_rendered={
            node: {"system": r.system, "user": r.user} for node, r in rendered.items()
        },
    )
    if final.get("compiled"):
        logger.info("job {} succeeded", job_id)
        store.update(job_id, status="succeeded", pdf_path=final.get("pdf_path"))
    else:
        logger.warning("job {} compile failed", job_id)
        store.update(job_id, status="compile_failed", error=final.get("compile_error"))


def _config(job_id: str) -> dict:
    return {"configurable": {"thread_id": job_id}}


def run_job(store, job_id, input_dir, output_dir, make_client, choices=None, hitl=False):
    """Run the conversion graph, pausing for review when hitl is True.

    On a review pause the job becomes awaiting_review with the interrupt payload
    in `review`; otherwise it finalizes from the checkpointed state.
    """
    seed = {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "llm_choices": choices or {},
        "hitl_enabled": hitl,
    }
    state = dict(seed)
    store.update(job_id, status="running", seed_state=serialize_values(seed))
    logger.info("job {} running: {} -> {} (hitl={})", job_id, input_dir, output_dir, hitl)
    config = _config(job_id)
    try:
        graph = build_graph(make_client(), checkpointer=CHECKPOINTER)
        paused, payload = _drive(store, job_id, graph, seed, config, state)
        if paused:
            store.update(job_id, status="awaiting_review", review=payload)
            return
        _finalize(store, job_id, graph.get_state(config).values)
    except Exception as exc:
        logger.error("job {} failed: {}", job_id, exc)
        store.update(job_id, status="failed", error=str(exc))


def resume_job(store, job_id, action, feedback, make_client):
    """Resume a paused review with the reviewer's decision, then pause or finish."""
    store.update(job_id, status="running")
    config = _config(job_id)
    state: dict = {}
    try:
        graph = build_graph(make_client(), checkpointer=CHECKPOINTER)
        resume = {"action": action, "feedback": feedback}
        paused, payload = _drive(store, job_id, graph, Command(resume=resume), config, state)
        if paused:
            store.update(job_id, status="awaiting_review", review=payload)
            return
        _finalize(store, job_id, graph.get_state(config).values)
    except Exception as exc:
        logger.error("job {} resume failed: {}", job_id, exc)
        store.update(job_id, status="failed", error=str(exc))
```

Note: the existing call sites in `src/b2t/api/app.py` keep working because `hitl` defaults to `False`; Task 7 passes it through.

- [ ] **Step 4: Run the suite to verify it passes**

Run: `uv run pytest tests/test_api_jobs.py -q && uv run pytest -q`
Expected: PASS (the new HITL job tests plus all existing tests).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/api/jobs.py tests/test_api_jobs.py
git commit -m "feat: run/resume split with an in-memory checkpointer for review"
```

---

### Task 7: Review API endpoints

**Files:**
- Modify: `src/b2t/api/schemas.py`
- Modify: `src/b2t/api/app.py`
- Test: `tests/test_api_app.py`

**Interfaces:**
- Consumes: `resume_job`, `JobRecord.review`, `JobRecord.use_fake` (Task 6).
- Produces: `POST /api/jobs` / `/sample` accept a `hitl` form flag; `GET /api/jobs/{id}/review`; `GET /api/jobs/{id}/preview.pdf`; `POST /api/jobs/{id}/review`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_api_app.py`:

```python
def _start_hitl(client, deck="deck1"):
    res = client.post(
        "/api/jobs/sample", data={"use_fake": "true", "hitl": "true", "deck": deck}
    )
    assert res.status_code == 200
    job_id = res.json()["job_id"]
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        body = client.get(f"/api/jobs/{job_id}").json()
        if body["status"] == "awaiting_review":
            return job_id
        time.sleep(0.1)
    raise AssertionError(f"job never awaited review: {body}")


def test_hitl_review_payload_and_approve_flow():
    client = _client()
    job_id = _start_hitl(client)
    review = client.get(f"/api/jobs/{job_id}/review").json()
    assert review["frame_index"] == 0
    assert review["total"] == 4
    assert "==" in review["candidate"]
    # approve the first frame; the job leaves awaiting_review
    res = client.post(f"/api/jobs/{job_id}/review", json={"action": "approve"})
    assert res.status_code == 200


def test_hitl_review_rejects_bad_action():
    client = _client()
    job_id = _start_hitl(client)
    res = client.post(f"/api/jobs/{job_id}/review", json={"action": "nope"})
    assert res.status_code == 400


def test_review_on_non_awaiting_job_returns_400():
    client = _client()
    job_id = _run_sample(client)  # non-HITL, terminal
    res = client.post(f"/api/jobs/{job_id}/review", json={"action": "approve"})
    assert res.status_code == 400


def test_review_endpoint_404_when_not_awaiting():
    client = _client()
    job_id = _run_sample(client)
    assert client.get(f"/api/jobs/{job_id}/review").status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_app.py::test_hitl_review_payload_and_approve_flow -v`
Expected: FAIL (no `hitl` handling / no `/review` endpoint).

- [ ] **Step 3: Write the implementation**

In `src/b2t/api/schemas.py`, add:

```python
class ReviewView(BaseModel):
    """The current frame awaiting review."""

    frame_index: int
    total: int
    candidate: str
    preview_ok: bool
    preview_error: str | None = None


class ReviewDecision(BaseModel):
    """A reviewer's decision: approve, or regenerate with optional feedback."""

    action: str
    feedback: str | None = None
```

In `src/b2t/api/app.py`:

Add to the imports from `b2t.api.jobs`: `resume_job`. Add to the imports from `b2t.api.schemas`: `ReviewView`, `ReviewDecision`.

In `create_job`, accept and store the flag and client params:

```python
    @app.post("/api/jobs", response_model=JobCreated)
    async def create_job(
        files: list[UploadFile] = File([]),
        use_fake: bool = Form(False),
        choices: str = Form(""),
        hitl: bool = Form(False),
    ):
        if not files:
            raise HTTPException(status_code=400, detail="no files submitted")
        parsed = _parse_choices(choices)
        root = Path(tempfile.mkdtemp(prefix="b2t_upload_"))
        _reconstruct(files, root)
        output_dir = root.parent / (root.name + "_out")
        job = jobs.create(
            input_dir=root, output_dir=output_dir, hitl=hitl,
            use_fake=use_fake, choices=parsed,
        )
        EXECUTOR.submit(
            run_job, jobs, job.id, root, output_dir,
            lambda: _make_client(use_fake), parsed, hitl,
        )
        return JobCreated(job_id=job.id, status=job.status)
```

Apply the same three changes to `create_sample_job` (add `hitl: bool = Form(False)`, pass `hitl=hitl, use_fake=use_fake, choices=parsed` to `jobs.create`, and pass `parsed, hitl` to `run_job`).

Add the three endpoints (after `get_node_state`):

```python
    @app.get("/api/jobs/{job_id}/review", response_model=ReviewView)
    def get_review(job_id: str):
        """Return the frame currently awaiting review. 404 if none."""
        job = jobs.get(job_id)
        if job is None or job.status != "awaiting_review" or job.review is None:
            raise HTTPException(status_code=404, detail="no frame awaiting review")
        return ReviewView(**job.review)

    @app.get("/api/jobs/{job_id}/preview.pdf")
    def get_preview(job_id: str):
        """Return the deck-so-far preview PDF. 404 if not produced."""
        job = jobs.get(job_id)
        if job is None or job.output_dir is None:
            raise HTTPException(status_code=404, detail="no preview")
        pdf = Path(job.output_dir) / "preview.pdf"
        if not pdf.exists():
            raise HTTPException(status_code=404, detail="no preview")
        return FileResponse(pdf, media_type="application/pdf")

    @app.post("/api/jobs/{job_id}/review", response_model=JobCreated)
    def submit_review(job_id: str, decision: ReviewDecision):
        """Resume a paused review with the reviewer's decision."""
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="unknown job")
        if job.status != "awaiting_review":
            raise HTTPException(status_code=400, detail="job is not awaiting review")
        if decision.action not in {"approve", "regenerate"}:
            raise HTTPException(status_code=400, detail="invalid action")
        jobs.update(job_id, status="running")
        EXECUTOR.submit(
            resume_job, jobs, job_id, decision.action, decision.feedback,
            lambda: _make_client(job.use_fake),
        )
        return JobCreated(job_id=job_id, status="running")
```

- [ ] **Step 4: Run the suite to verify it passes**

Run: `uv run pytest tests/test_api_app.py -q && uv run pytest -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/api/schemas.py src/b2t/api/app.py tests/test_api_app.py
git commit -m "feat: review API endpoints (payload, preview pdf, decision)"
```

---

### Task 8: Review panel in the testing UI

**Files:**
- Modify: `src/b2t/api/static/index.html`
- Modify: `src/b2t/api/static/app.js`
- Modify: `src/b2t/api/static/style.css`
- Test: `tests/test_api_app.py`

**Interfaces:**
- Consumes: `GET /api/jobs/{id}/review`, `GET /api/jobs/{id}/preview.pdf`, `POST /api/jobs/{id}/review` (Task 7).
- Produces: a `hitl` submit checkbox and a `#review` panel.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_api_app.py`:

```python
def test_index_has_review_panel_and_hitl_toggle():
    text = _client().get("/").text
    assert 'id="review"' in text
    assert 'id="hitl"' in text
    assert 'id="review-approve"' in text
    assert 'id="review-regenerate"' in text
    assert 'id="review-feedback"' in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_app.py::test_index_has_review_panel_and_hitl_toggle -v`
Expected: FAIL (no such elements yet).

- [ ] **Step 3: Write the implementation**

In `src/b2t/api/static/index.html`, add the HITL toggle next to the existing "use fake converter" checkbox (in the submit panel):

```html
<label><input type="checkbox" id="hitl" /> review each frame</label>
```

And add the review panel (place it just before the output section):

```html
<div id="review" hidden>
  <h2>Review frame <span id="review-counter"></span></h2>
  <p id="review-status"></p>
  <div class="review-body">
    <textarea id="review-candidate" readonly rows="14"></textarea>
    <iframe id="review-preview" title="frame preview"></iframe>
  </div>
  <textarea id="review-feedback" placeholder="feedback for regeneration (optional)" rows="3"></textarea>
  <div class="review-actions">
    <button id="review-approve">Approve</button>
    <button id="review-regenerate">Regenerate</button>
  </div>
</div>
```

In `src/b2t/api/static/app.js`:

1. When submitting a job, include the HITL flag in the form data:

```javascript
form.append("hitl", document.getElementById("hitl").checked);
```

(Add this line wherever the existing submit builds its `FormData`, alongside the `use_fake` field, for both the folder-upload and sample-deck submit paths.)

2. In the status poll handler, when `job.status === "awaiting_review"`, render the review panel; otherwise hide it:

```javascript
const reviewPanel = document.getElementById("review");

async function renderReview(jobId) {
  const r = await fetch(`/api/jobs/${jobId}/review`);
  if (!r.ok) { reviewPanel.hidden = true; return; }
  const review = await r.json();
  document.getElementById("review-counter").textContent =
    `${review.frame_index + 1} of ${review.total}`;
  document.getElementById("review-candidate").value = review.candidate;
  document.getElementById("review-status").textContent = review.preview_ok
    ? "" : `preview did not compile: ${review.preview_error || ""}`;
  const frame = document.getElementById("review-preview");
  frame.src = review.preview_ok ? `/api/jobs/${jobId}/preview.pdf?ts=${Date.now()}` : "";
  reviewPanel.hidden = false;
}

async function submitReview(jobId, action) {
  const feedback = document.getElementById("review-feedback").value;
  await fetch(`/api/jobs/${jobId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, feedback: feedback || null }),
  });
  document.getElementById("review-feedback").value = "";
  reviewPanel.hidden = true;
}
```

Wire the buttons once, using the current job id tracked by the page:

```javascript
document.getElementById("review-approve").onclick = () => submitReview(currentJobId, "approve");
document.getElementById("review-regenerate").onclick = () => submitReview(currentJobId, "regenerate");
```

In the existing poll loop, call `renderReview(currentJobId)` when the status is `awaiting_review`, and set `reviewPanel.hidden = true` for any other status, so the panel appears and disappears as the run pauses and resumes.

In `src/b2t/api/static/style.css`, add minimal layout:

```css
#review { border: 1px solid #cc3399; border-radius: 6px; padding: 1rem; margin: 1rem 0; }
#review .review-body { display: flex; gap: 1rem; }
#review .review-body textarea, #review .review-body iframe { flex: 1; min-height: 18rem; }
#review .review-actions { margin-top: 0.5rem; display: flex; gap: 0.5rem; }
```

- [ ] **Step 4: Run the test and verify it passes**

Run: `uv run pytest tests/test_api_app.py::test_index_has_review_panel_and_hitl_toggle -v && uv run pytest -q`
Expected: PASS.

- [ ] **Step 5: Manual smoke check (optional but recommended)**

Run: `uv run uvicorn b2t.api.app:app` then open http://127.0.0.1:8000, tick "review each frame" and "use fake converter", pick deck1, "Use sample deck". Confirm the review panel shows frame 1 of 4 with the candidate and a preview, and that Approve advances and Regenerate re-pauses.

- [ ] **Step 6: Commit**

```bash
git add src/b2t/api/static/index.html src/b2t/api/static/app.js src/b2t/api/static/style.css tests/test_api_app.py
git commit -m "feat: per-frame review panel in the testing UI"
```

---

### Task 9: Update docs

**Files:**
- Modify: `README.md`
- Modify: `CODEBASE_GUIDE.md`

**Interfaces:**
- None (documentation only).

- [ ] **Step 1: Update the README**

In `README.md`: update the flowchart and node list to insert `preview` and `review` between `convert` and `assemble`, and add a short "Review each frame" note to the testing-UI section describing the `hitl` toggle, the per-frame approve/regenerate panel, and that a paused review lives in memory until the server stops.

- [ ] **Step 2: Update CODEBASE_GUIDE**

In `CODEBASE_GUIDE.md`: bump the node count from ten to twelve, add `preview` and `review` to the file tree, the graph mermaid, the node table, and a 9.x section each; note the `hitl_enabled` flag, the shared `InMemorySaver`, and the `run_job`/`resume_job` split with the `awaiting_review` status and the three review endpoints. Update `defaults.json` references to `convert/v4`.

- [ ] **Step 3: Verify the suite is unaffected**

Run: `uv run pytest -q`
Expected: PASS (docs do not change tests).

- [ ] **Step 4: Commit**

```bash
git add README.md CODEBASE_GUIDE.md
git commit -m "docs: describe per-frame review (preview/review nodes, HITL flow)"
```

---

## Self-Review

**1. Spec coverage:**
- `hitl_enabled` dual-mode: Tasks 1, 4, 5.
- `convert -> preview -> review` restructure, commit/advance in `review`: Tasks 3, 4, 5.
- `interrupt()` + in-memory checkpointer + thread id: Tasks 4, 6.
- Deck-so-far preview without bibliography: Task 3.
- `run_job` split + `resume_job` + 3 endpoints: Tasks 6, 7.
- Review panel + hitl toggle: Task 8.
- Feedback-aware `convert/v4` default: Tasks 2, 5.
- Error handling (preview failure non-fatal, 400 on bad/absent review, failed on LLM error): Tasks 4 (payload carries preview_error), 7 (400 paths), 6 (failure boundary).
- Known limitations (in-memory only, linear progress strip, no direct edit/skip, v1-v3 history): carried in docs (Task 9); no code owed.

**2. Placeholder scan:** No "TBD"/"TODO"/"handle edge cases"; every code and test step is concrete. Task 8's JS is given as concrete functions plus exact wiring instructions; Task 9 is doc prose with exact targets.

**3. Type consistency:** `convert_frame` returns `candidate` (Task 5), consumed by `preview` and `review` (Tasks 3, 4). `review_node` writes `converted_frames`/`frame_index` consumed by `_more_frames` and `assemble`. `run_job(..., hitl=False)` and `resume_job(store, job_id, action, feedback, make_client)` (Task 6) match their call sites in Task 7. `ReviewView(frame_index, total, candidate, preview_ok, preview_error)` matches the `review` node's interrupt payload keys (Task 4) and the `get_review` projection (Task 7). `build_graph(client, checkpointer=None)` (Task 5) matches its callers in Task 6 and `app.convert_deck` (unchanged, omits the checkpointer).
