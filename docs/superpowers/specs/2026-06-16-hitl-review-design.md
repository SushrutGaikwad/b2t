# Per-Frame Human-in-the-Loop Review - Design

Date: 2026-06-16
Status: proposed

## 1. Motivation

The per-frame conversion increment converts one Beamer frame per LLM call in a
LangGraph cycle, but every frame is accepted automatically. Roadmap item 4 is
human review: a professor should be able to inspect each converted frame,
approve it, or send it back with feedback for regeneration, before the deck is
finalized. The per-frame cycle was built specifically as the seam this increment
interrupts on.

This increment adds per-frame review to the pipeline and the testing UI, while
leaving the library entry point (`convert_deck`) and the whole offline/test path
behaving exactly as they do today.

## 2. Scope

In scope:

- A dual-mode pipeline: an `hitl_enabled` flag turns per-frame review on; off by
  default so the library path and existing tests are unchanged.
- A graph restructure of the per-frame loop into `convert -> preview -> review`,
  with the frame commit/advance moved out of `convert` into `review`.
- A LangGraph `interrupt()` in the `review` node, an in-memory checkpointer, and
  a thread id per job.
- A deck-so-far preview compiled per frame (header + approved frames + the
  candidate). The preview includes the bibliography and thank-you when the deck
  has a `.bib`, and copies the images and `.bib`, so a frame that references an
  image or a citation compiles during review. (This revises the initial
  "no bibliography in previews" idea, which broke citation frames.)
- `run_job` split into an initial run and a `resume_job`, plus three API
  endpoints to fetch the review payload, fetch the preview PDF, and submit a
  decision.
- A testing-UI review panel: frame i of n, the candidate Typst, the preview PDF,
  a feedback box, and Approve / Regenerate buttons.
- A feedback-aware prompt version `convert/v4`, made the default.

Out of scope (later increments):

- Durable, cross-restart persistence of a paused review (a SaaS concern; this
  increment uses the in-memory checkpointer, so a review survives only while the
  dev server process runs).
- Direct per-frame Typst editing and reject-and-skip (the whole-deck editor
  still lets a reviewer hand-fix the final deck).
- Any change to the linear progress-strip rendering for the cyclic loop; the
  review is surfaced through the new panel and the `awaiting_review` status
  instead.

## 3. Decisions already made (with rationale)

| Decision | Choice | Why |
| --- | --- | --- |
| Reviewer actions | Approve, or Regenerate with optional feedback | Smallest genuinely useful set; reuses the existing convert node and the final whole-deck editor covers hand-fixes |
| Preview | The compiled deck-so-far (header + approved + candidate) | The reviewer sees the new frame in real context; reuses `assemble` + `compile_typst` directly |
| Persistence | Built-in `InMemorySaver`, no new dependency | Fits the testing harness; a review survives as long as the server runs. Durable persistence is a SaaS-increment concern |
| Dual-mode | One graph gated by `hitl_enabled` (default False) | Keeps `convert_deck` and every existing test unchanged; avoids two graph variants |
| Commit/advance location | In `review`, not `convert` | `convert` must be able to regenerate the same frame without duplicating it; only an approval commits and advances |
| Preview bibliography | Excluded from previews; added only in the final `assemble` | Mid-review previews are about frame content; the trailing bibliography/thank-you would be noise on every frame |

## 4. Architecture overview

```
copy_input -> ... -> strip_overlays -> split_deck
   -> convert   [LLM] produce candidate for frames[frame_index]
   -> preview   assemble header + approved + candidate, compile (HITL only)
   -> review    auto-approve (off) | interrupt() then approve/regenerate (on)
        |
   review --(frame_index < len(frames))--> convert
   review --(frames done)--> assemble -> write_output -> compile -> END
```

The conditional edge after `review` is the existing `frame_index < len(frames)`
test: regenerate leaves the index unchanged (re-do current frame), approve
advances it. Both regenerate and approve-but-more route back to `convert`;
approve-on-the-last-frame routes to `assemble`.

## 5. State model (`src/b2t/state.py`)

`PipelineState` gains:

```python
    hitl_enabled: bool = False         # the UI sets this True to enable review
    candidate: str | None = None       # current unapproved frame Typst
    feedback: str | None = None        # reviewer feedback for the next regenerate
    preview_path: Path | None = None   # the written preview.typ
    preview_pdf: Path | None = None    # the compiled preview PDF, if it compiled
    preview_error: str | None = None   # preview compile error, if any
```

`converted_frames` and `frame_index` keep their meaning but are now written by
`review` on approve, not by `convert`.

## 6. Components

### 6.1 `convert` node (`nodes/convert_frame.py`)

`convert_frame` produces a candidate for `frames[frame_index]` and no longer
commits or advances. It calls `run_prompt(state, "convert", client, {reference,
guides, preamble, feedback, frame})`, where `feedback` is `""` on a first attempt
or a framed block built from `state.feedback` on a regenerate. Returns
`{"candidate": strip_code_fence(output), "llm_runs": ..., "llm_rendered": ...}`.

### 6.2 `preview` node (`nodes/preview.py` + `typst_scaffold`/`typst_runner`)

If `state.hitl_enabled` is `False`, returns `{}` (no preview work). Otherwise:

1. Builds `converted = state.converted_frames + [state.candidate]` and
   `frames = state.frames[: state.frame_index + 1]`.
2. Calls `assemble(meta, aspect_ratio, has_toc, frames, converted, bib_name)`
   where `bib_name` is the detected `.bib` filename or `None`, then
   `fix_image_paths` on the result.
3. Copies the images and the `.bib` into `output_dir`, writes
   `output_dir/preview.typ`, and runs `compile_typst` on it, so a frame that
   references an image or a citation resolves during review.
4. Returns `preview_path`, `preview_pdf` (or `None`), and `preview_error`.

### 6.3 `review` node (`nodes/review.py`)

- `hitl_enabled` is `False`: auto-approve. Returns `{"converted_frames":
  [*state.converted_frames, state.candidate], "frame_index": state.frame_index +
  1, "candidate": None, "feedback": None}`.
- `hitl_enabled` is `True`: `decision = interrupt({...review payload...})`. The
  payload carries `frame_index`, `total`, the `candidate`, and whether the
  preview compiled plus any error. On resume:
  - `decision["action"] == "approve"`: same commit/advance as above.
  - `decision["action"] == "regenerate"`: returns `{"feedback":
    decision.get("feedback"), "candidate": None}` (index unchanged).

The `review` node holds no expensive work before `interrupt()`, so re-execution
on resume is cheap; the preview compile lives in the prior `preview` node so it
is checkpointed and never recompiled on resume.

### 6.4 Graph (`graph.py`)

`build_graph(client, checkpointer=None)` registers `convert` (the per-frame
function), `preview`, and `review`; wires `split_deck -> convert -> preview ->
review`, a conditional edge `review -> {convert, assemble}` on the existing
`_more_frames`, and compiles with `graph.compile(checkpointer=checkpointer)`.
With `checkpointer=None` (library, tests) and `hitl_enabled=False`, the graph
runs straight through exactly as today.

### 6.5 Prompt `convert/v4`

`v4` adds a `{{feedback}}` token before the frame; `v1`/`v2`/`v3` stay for
history. `defaults.json` points `convert` at `v4`. The node always supplies
`feedback` (empty string on the first attempt), so v4 renders in both modes.

### 6.6 Jobs and resume (`api/jobs.py`)

A module-level `CHECKPOINTER = InMemorySaver()` is shared across jobs; each job
uses `thread_id = job_id`. The `JobRecord` gains `hitl`, `use_fake`, `choices`
(so a resume rebuilds the same client), `review` (the current interrupt payload),
and the `awaiting_review` status.

- The initial run streams the seed with `config={"configurable": {"thread_id":
  job_id}}` until the stream surfaces an `__interrupt__` (pause) or the graph
  ends. A shared helper drives the stream and records node deltas as today.
- On pause: status `awaiting_review`, the interrupt payload stored on the record.
- `resume_job(store, job_id, action, feedback, make_client)`: streams
  `Command(resume={"action": action, "feedback": feedback})` on the same thread
  until the next interrupt or the end.

### 6.7 API (`api/app.py`) and UI (`api/static/`)

- `POST /api/jobs` and `/api/jobs/sample` accept a `hitl` form flag; when set,
  the job seeds `hitl_enabled=True` and the graph is built with `CHECKPOINTER`.
- `GET /api/jobs/{id}/review` -> `{frame_index, total, candidate, preview_ok,
  preview_error}` (404 when not awaiting review).
- `GET /api/jobs/{id}/preview.pdf` -> the deck-so-far preview PDF (404 if absent).
- `POST /api/jobs/{id}/review` `{action, feedback}` -> validates the job is
  `awaiting_review` and the action, then submits the resume to the executor;
  400 otherwise.
- UI: a review panel shown when status is `awaiting_review` (frame i of n, the
  candidate Typst, the preview PDF, a feedback textbox, Approve / Regenerate).
  The decision is posted and polling resumes.

## 7. Data flow (one HITL run)

1. `split_deck` produces frames; `convert` makes a candidate for frame 0.
2. `preview` assembles header + candidate and compiles `preview.pdf`.
3. `review` interrupts; the job goes `awaiting_review` with the payload.
4. The reviewer approves -> `resume_job` commits the frame, advances, and the
   edge routes back to `convert` for frame 1; or regenerates with feedback ->
   `convert` re-runs frame 0 with the feedback, then `preview` and `review` again.
5. After the last frame is approved, `assemble` builds the full deck (with the
   bibliography and thank-you), `write_output` writes it, `compile` finalizes.

## 8. Error handling

- A failed preview compile is recorded in `preview_error` and shown to the
  reviewer; it does not block approve or regenerate.
- `POST /review` on a job that is not `awaiting_review`, or with an unknown
  action, returns HTTP 400.
- A regenerate whose LLM call raises propagates to the existing failure boundary
  (status `failed`).
- The library path (`hitl_enabled=False`, no checkpointer) never calls
  `interrupt()`, so it cannot pause and needs no checkpointer.

## 9. Testing

- `nodes`: `convert` sets `candidate` (does not append/advance); `preview`
  assembles and compiles a partial deck and returns `{}` when `hitl_enabled` is
  False; `review` auto-approves (off) and, with a stubbed resume value, commits
  on approve and stores feedback on regenerate.
- Graph straight-through (`hitl_enabled=False`, no checkpointer): deck1/deck2
  assemble and compile exactly as today (the existing tests stay green).
- Graph HITL: with `CHECKPOINTER` and `hitl_enabled=True` under a `FakeClient`,
  the stream pauses at the first `__interrupt__`; resuming with `approve`
  advances; resuming with `regenerate` re-runs `convert` and the regenerate
  feedback reaches the prompt (asserted via a recording client).
- API: a HITL job reaches `awaiting_review`; the review payload, the preview PDF,
  approve, and regenerate-with-feedback endpoints behave; a non-HITL job is
  unaffected.
- `prompts`: `convert/v4` loads and renders with the feedback token; the default
  is `v4`.

## 10. Known limitations / deferred

- A paused review lives in process memory; restarting the dev server drops it.
  Durable persistence is the SaaS increment.
- The linear progress strip does not render the review cycle; the review panel
  and `awaiting_review` status stand in for it.
- No direct per-frame Typst editing and no reject-and-skip this increment.
- `v1`/`v2`/`v3` remain in the registry for history but are not runnable through
  the feedback-aware per-frame node.
