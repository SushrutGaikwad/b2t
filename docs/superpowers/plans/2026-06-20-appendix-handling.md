# Appendix Handling and `<touying:hidden>` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render Beamer `\appendix` frames as a Touying appendix (`#show: appendix`) after the references slide, with appendix and starred-section headings hidden from the table of contents via `<touying:hidden>`.

**Architecture:** Two new facts (`is_appendix`, `section_starred`) are tagged onto each `FrameUnit` by the deterministic splitter (`latex/split.py`). The deterministic assembler (`typst_scaffold.py`) partitions frames into body vs appendix, emits the references block first, then `#show: appendix` and the appendix frames, hiding their headings. The convert/preview/review cycle, the prompts, and the graph wiring are untouched; `preview` inherits the new behavior because it already calls `assemble`.

**Tech Stack:** Python 3.12, Pydantic v2, pytest, loguru. Typst CLI is ground truth for compilation.

## Global Constraints

- Use `uv` for everything: `uv run pytest`. Never call `python`/`pip` directly.
- No new third-party dependencies.
- No LaTeX toolchain, ever. Input decks are read-only; never mutate the input dir.
- The generated deck must never use overlays or pause functionality.
- Deterministic logic lives in `latex/` and module-level helpers (network-free, tested directly); `nodes/` stay thin. No LLM is involved in this plan; all hiding is deterministic from `\appendix` and `\section*`.
- No emojis anywhere. No em or en dashes in prose. Prefer clear docstrings, sparse inline comments.
- End each commit message with the trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- Keep all non-integration tests offline via `FakeClient`. Typst integration assertions stay guarded by `typst_available()`.

---

### Task 1: Tag FrameUnit with appendix and starred-section facts

**Files:**
- Modify: `src/b2t/state.py`
- Test: `tests/test_state.py`

**Interfaces:**
- Produces: `FrameUnit` gains `is_appendix: bool = False` and `section_starred: bool = False`, used by `latex/split.py` (Task 2) and `typst_scaffold.py` (Task 3).

- [ ] **Step 1: Write the failing test**

Add to `tests/test_state.py` (it already imports `FrameUnit`):

```python
def test_frame_unit_appendix_and_starred_default_false():
    unit = FrameUnit(raw="x")
    assert unit.is_appendix is False
    assert unit.section_starred is False


def test_frame_unit_appendix_and_starred_settable():
    unit = FrameUnit(raw="y", is_appendix=True, section_starred=True)
    assert unit.is_appendix is True
    assert unit.section_starred is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_state.py::test_frame_unit_appendix_and_starred_default_false -v`
Expected: FAIL with `TypeError` / unexpected keyword `is_appendix` (the field does not exist yet). The default test fails on the missing attribute.

- [ ] **Step 3: Write minimal implementation**

In `src/b2t/state.py`, replace the `FrameUnit` class with:

```python
class FrameUnit(BaseModel):
    """One beamer frame plus the section it falls under.

    Attributes:
        raw: The whole \\begin{frame}...\\end{frame} source.
        section: The \\section this frame belongs to, or None if before any.
        is_appendix: Whether the frame appears after \\appendix (backup material
            rendered after the references, kept out of the table of contents).
        section_starred: Whether the enclosing section was \\section* (Beamer
            keeps starred sections out of the table of contents).
    """

    raw: str
    section: str | None = None
    is_appendix: bool = False
    section_starred: bool = False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_state.py -v`
Expected: PASS (all state tests).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/state.py tests/test_state.py
git commit -m "feat: tag FrameUnit with is_appendix and section_starred"
```

---

### Task 2: Detect `\appendix` and starred sections in the splitter

**Files:**
- Modify: `src/b2t/latex/split.py`
- Test: `tests/test_split.py`

**Interfaces:**
- Consumes: `FrameUnit` fields from Task 1.
- Produces: `split_frames(body)` keeps its `-> (list[FrameUnit], bool)` signature, but now tags every frame after `\appendix` with `is_appendix=True` (resetting the carried section to `None`), and sets `section_starred` from a `\section*`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_split.py` (it already imports `split_frames` and `pytest`):

```python
APPENDIX_BODY = r"""
\section{Methods}
\begin{frame}{Approach}One\end{frame}
\appendix
\begin{frame}{Backup}two\end{frame}
\begin{frame}{More Backup}three\end{frame}
"""


def test_split_frames_tags_appendix_frames():
    frames, _ = split_frames(APPENDIX_BODY)
    assert [f.is_appendix for f in frames] == [False, True, True]


def test_appendix_resets_the_carried_section():
    frames, _ = split_frames(APPENDIX_BODY)
    assert frames[0].section == "Methods"
    assert frames[1].section is None
    assert frames[2].section is None


def test_section_after_appendix_is_kept_and_tagged_appendix():
    frames, _ = split_frames(r"\appendix\section{Extra}\begin{frame}{X}a\end{frame}")
    assert frames[0].is_appendix is True
    assert frames[0].section == "Extra"


def test_starred_section_sets_section_starred():
    frames, _ = split_frames(r"\section*{Hidden}\begin{frame}{X}a\end{frame}")
    assert frames[0].section == "Hidden"
    assert frames[0].section_starred is True


def test_plain_section_is_not_starred():
    frames, _ = split_frames(r"\section{Shown}\begin{frame}{X}a\end{frame}")
    assert frames[0].section_starred is False


def test_appendix_requires_a_word_boundary():
    # a longer command starting with "appendix" must not trigger the split
    frames, _ = split_frames(r"\appendixfoo\begin{frame}{X}a\end{frame}")
    assert frames[0].is_appendix is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_split.py::test_split_frames_tags_appendix_frames -v`
Expected: FAIL with `AssertionError` (every frame currently reports `is_appendix=False`).

- [ ] **Step 3: Write minimal implementation**

In `src/b2t/latex/split.py`, replace `_TOKEN_RE` with one that captures the section star and matches `\appendix`:

```python
_TOKEN_RE = re.compile(
    r"\\section(?P<star>\*)?\{(?P<section>[^}]*)\}"
    r"|\\begin\{frame\}(?P<frame>.*?)\\end\{frame\}"
    r"|(?P<appendix>\\appendix)\b",
    re.DOTALL,
)
```

Then replace the body of `split_frames` (the part from `frames: list[FrameUnit] = []` through `return frames, has_toc`, leaving the `_FRAME_SHORTHAND_RE` guard above it untouched) with:

```python
    frames: list[FrameUnit] = []
    has_toc = False
    current_section: str | None = None
    section_starred = False
    in_appendix = False
    matched = 0
    for match in _TOKEN_RE.finditer(body):
        if match.group("appendix") is not None:
            in_appendix = True
            current_section = None
            section_starred = False
            continue
        if match.group("section") is not None:
            current_section = match.group("section").strip() or None
            section_starred = match.group("star") is not None
            continue
        matched += 1
        inner = match.group("frame")
        if r"\tableofcontents" in inner:
            has_toc = True
            continue
        if any(marker in inner for marker in _SCAFFOLD_FRAME_MARKERS):
            continue
        frames.append(
            FrameUnit(
                raw=match.group(0),
                section=current_section,
                is_appendix=in_appendix,
                section_starred=section_starred,
            )
        )
    if matched != body.count(r"\begin{frame}"):
        raise ValueError(r"unmatched \begin{frame} in document body")
    return frames, has_toc
```

Also extend the `split_frames` docstring's behavior line. Change:

```python
    Walks the body in order, tracking the current \\section. The title-slide,
    table-of-contents, and bibliography frames are excluded because the scaffold
    renders them; the table-of-contents frame sets has_toc.
```

to:

```python
    Walks the body in order, tracking the current \\section (and whether it was
    starred) and whether \\appendix has been seen. Every frame after \\appendix
    is tagged is_appendix with the carried section reset to None. The title-slide,
    table-of-contents, and bibliography frames are excluded because the scaffold
    renders them; the table-of-contents frame sets has_toc.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_split.py -v`
Expected: PASS (the new tests and every existing split test).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/latex/split.py tests/test_split.py
git commit -m "feat: detect appendix region and starred sections in the splitter"
```

---

### Task 3: Render the appendix and hide headings in the assembler

**Files:**
- Modify: `src/b2t/typst_scaffold.py`
- Test: `tests/test_scaffold.py`

**Interfaces:**
- Consumes: `FrameUnit.is_appendix`/`section_starred` (Task 1).
- Produces: `_hide_frame_title(typ: str) -> str` (hides the first `==` heading); a hidden-aware `_body`; a new `_appendix_block`; `assemble(...)` keeps its signature `assemble(meta, aspect_ratio, has_toc, frames, converted, bib_name)` but now partitions appendix frames and renders them after the bibliography.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_scaffold.py` (it already imports `assemble`, `build_header`, `DeckMeta`, `FrameUnit`). Add this import near the top with the other `typst_scaffold` imports:

```python
from b2t.typst_scaffold import _hide_frame_title
```

Then add the tests:

```python
def test_hide_frame_title_appends_label():
    assert _hide_frame_title("== Backup\n\nbody") == "== Backup <touying:hidden>\n\nbody"


def test_hide_frame_title_is_idempotent():
    once = _hide_frame_title("== Backup\n\nbody")
    assert _hide_frame_title(once) == once


def test_hide_frame_title_ignores_level_three_heading():
    assert "<touying:hidden>" not in _hide_frame_title("=== Sub\n\nbody")


def test_hide_frame_title_no_heading_returns_unchanged():
    assert _hide_frame_title("just body\nmore") == "just body\nmore"


def test_assemble_hides_starred_section_heading():
    frames = [FrameUnit(raw="", section="Secret", section_starred=True)]
    out = assemble(DeckMeta(), "4-3", False, frames, ["== S\n\nb"], None)
    assert "= Secret <touying:hidden>" in out


def test_assemble_plain_section_heading_is_not_hidden():
    frames = [FrameUnit(raw="", section="Open")]
    out = assemble(DeckMeta(), "4-3", False, frames, ["== S\n\nb"], None)
    assert "= Open" in out
    assert "= Open <touying:hidden>" not in out


def test_assemble_appendix_after_bibliography_with_synthesized_section():
    frames = [
        FrameUnit(raw="", section="Intro"),
        FrameUnit(raw="", section=None, is_appendix=True),
    ]
    converted = ["== Motivation\n\nA", "== Backup\n\nB"]
    out = assemble(DeckMeta(title="T"), "4-3", False, frames, converted, "references.bib")
    assert "#show: appendix" in out
    assert out.index("#bibliography") < out.index("#show: appendix")
    assert "= Appendix <touying:hidden>" in out
    assert "== Backup <touying:hidden>" in out


def test_assemble_appendix_without_bibliography():
    frames = [
        FrameUnit(raw="", section="Intro"),
        FrameUnit(raw="", section=None, is_appendix=True),
    ]
    out = assemble(DeckMeta(), "4-3", False, frames, ["== M\n\nA", "== B\n\nb"], None)
    assert "#show: appendix" in out
    assert "#bibliography" not in out
    assert "= Appendix <touying:hidden>" in out


def test_assemble_appendix_uses_source_section_when_present():
    frames = [
        FrameUnit(raw="", section="Intro"),
        FrameUnit(raw="", section="Extra Material", is_appendix=True),
    ]
    out = assemble(DeckMeta(), "4-3", False, frames, ["== M\n\nA", "== B\n\nb"], None)
    assert "= Extra Material <touying:hidden>" in out
    assert "= Appendix <touying:hidden>" not in out


def test_assemble_no_appendix_emits_no_show_rule():
    frames = [FrameUnit(raw="", section="Intro")]
    out = assemble(DeckMeta(), "4-3", False, frames, ["== S\n\nb"], None)
    assert "#show: appendix" not in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_scaffold.py::test_hide_frame_title_appends_label -v`
Expected: FAIL with `ImportError: cannot import name '_hide_frame_title'`.

- [ ] **Step 3: Write minimal implementation**

In `src/b2t/typst_scaffold.py`, replace the existing `_body` function and the existing `assemble` function with the following, and add the three new helpers (`_hide_frame_title`, `_section_heading`, `_appendix_block`). The `build_header`, `_OUTLINE`, `_HEADER_TEMPLATE`, `render_date`, and `_bibliography_block` definitions are unchanged.

```python
def _hide_frame_title(typ: str) -> str:
    """Append <touying:hidden> to the first level-2 (==) heading line.

    Used for appendix frames, whose slide titles stay out of the table of
    contents. A higher-level (===) heading and an already-hidden title are left
    untouched, and a body with no == heading is returned unchanged.
    """
    lines = typ.split("\n")
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("==") and not stripped.startswith("==="):
            if "<touying:hidden>" not in line:
                lines[i] = line.rstrip() + " <touying:hidden>"
            return "\n".join(lines)
    return typ


def _section_heading(section: str, hidden: bool) -> str:
    """Return a = Section heading, hidden from the outline when hidden is True."""
    return f"= {section} <touying:hidden>" if hidden else f"= {section}"


def _body(pairs: list[tuple[FrameUnit, str]]) -> str:
    """Interleave = Section headings (on change) with converted frame bodies.

    A heading that came from a starred \\section* is hidden from the outline.
    """
    parts: list[str] = []
    prev_section: str | None = None
    for unit, typ in pairs:
        if unit.section is not None and unit.section != prev_section:
            parts.append(_section_heading(unit.section, unit.section_starred))
        prev_section = unit.section
        parts.append(typ.strip())
    return "\n\n".join(parts)


def _appendix_block(pairs: list[tuple[FrameUnit, str]]) -> str:
    """Render the appendix: #show: appendix then hidden-heading backup frames.

    Appendix section headings and frame titles are hidden from the outline. A
    single = Appendix wrapper is synthesized when the source gives no section.
    """
    parts: list[str] = ["#show: appendix"]
    prev_section: str | None = None
    emitted_section = False
    for unit, typ in pairs:
        if unit.section is not None and unit.section != prev_section:
            parts.append(_section_heading(unit.section, True))
            emitted_section = True
        elif unit.section is None and not emitted_section:
            parts.append("= Appendix <touying:hidden>")
            emitted_section = True
        prev_section = unit.section
        parts.append(_hide_frame_title(typ.strip()))
    return "\n" + "\n\n".join(parts) + "\n"


def assemble(
    meta: DeckMeta | None,
    aspect_ratio: str,
    has_toc: bool,
    frames: list[FrameUnit],
    converted: list[str],
    bib_name: str | None,
) -> str:
    """Assemble the full Typst deck from the scaffold and converted frames.

    Frames after \\appendix render after the bibliography, introduced by
    #show: appendix, with their section and frame headings hidden from the
    table of contents.
    """
    pairs = list(zip(frames, converted))
    body_pairs = [p for p in pairs if not p[0].is_appendix]
    appendix_pairs = [p for p in pairs if p[0].is_appendix]
    out = build_header(meta, aspect_ratio)
    if has_toc:
        out += _OUTLINE
    out += "\n" + _body(body_pairs) + "\n"
    if bib_name:
        out += _bibliography_block(bib_name)
    if appendix_pairs:
        out += _appendix_block(appendix_pairs)
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_scaffold.py -v`
Expected: PASS (the new tests and every existing scaffold test, including the no-appendix `test_assemble_inserts_each_section_once_no_toc_no_bib` and `test_assemble_with_toc_and_bibliography`, which are unaffected because those frames default to `is_appendix=False`).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/typst_scaffold.py tests/test_scaffold.py
git commit -m "feat: render appendix after the bibliography with hidden headings"
```

---

### Task 4: End-to-end appendix rendering on deck3

**Files:**
- Modify: `tests/test_graph.py`

**Interfaces:**
- Consumes: the full pipeline (Tasks 1-3) and the existing `deck3` fixture (a deck with `\appendix`, a backup frame, and a bibliography).

- [ ] **Step 1: Write the failing test**

In `tests/test_graph.py`, add a `DECK3` constant next to `DECK1`/`DECK2`:

```python
DECK3 = Path(__file__).parent / "fixtures" / "sample_decks" / "deck3"
```

Then add this test:

```python
def test_pipeline_renders_appendix_after_bibliography(tmp_path):
    out = tmp_path / "out"
    graph = build_graph(FakeClient(FRAME_BODY))
    result = dict(graph.invoke({"input_dir": DECK3, "output_dir": out}))
    typ = (out / "main.typ").read_text(encoding="utf-8")
    # the backup frame is now an appendix, rendered after the bibliography
    assert "#show: appendix" in typ
    assert typ.index("#bibliography") < typ.index("#show: appendix")
    assert "= Appendix <touying:hidden>" in typ
    # exactly one frame title is hidden: the single appendix (backup) frame
    assert typ.count("== Slide <touying:hidden>") == 1
    assert (out / "references.bib").exists()
    if typst_available():
        assert result["compiled"] is True
        assert Path(result["pdf_path"]).exists()
```

- [ ] **Step 2: Run test to verify it fails**

If implementing strictly task-by-task this passes already (Tasks 1-3 are done before this task). To confirm the test exercises the new path, temporarily check it against the pre-feature behavior is not required; just run it.

Run: `uv run pytest tests/test_graph.py::test_pipeline_renders_appendix_after_bibliography -v`
Expected: PASS once Tasks 1-3 are in. (Before Task 3 it would FAIL: no `#show: appendix` is emitted.)

- [ ] **Step 3: Run the full graph suite**

Run: `uv run pytest tests/test_graph.py -v`
Expected: PASS (deck1, deck2, deck3, and the two HITL tests). The deck1/deck2 tests are unaffected: neither deck has an `\appendix`, so no `#show: appendix` is emitted and their assertions hold.

- [ ] **Step 4: Run the whole suite**

Run: `uv run pytest -q`
Expected: PASS. If `typst` is installed, deck3 compiles with the appendix; the first compile fetches the Touying/theorion packages from `@preview`, so a network connection is needed on first run.

- [ ] **Step 5: Commit**

```bash
git add tests/test_graph.py
git commit -m "test: end-to-end appendix rendering on deck3"
```

---

### Task 5: Update docs (README and CODEBASE_GUIDE)

**Files:**
- Modify: `README.md`
- Modify: `CODEBASE_GUIDE.md`

**Interfaces:**
- None (documentation only).

- [ ] **Step 1: Update the README node descriptions**

In `README.md`, in the numbered "Nodes" list, append to the `split_deck` (node 6) description:

```
Frames after \appendix are tagged as appendix material and a starred \section*
is flagged, so the assembler can keep their headings out of the outline.
```

And append to the `assemble` (node 10) description:

```
Appendix frames are rendered after the bibliography, introduced by
#show: appendix, with their section and frame headings labelled
<touying:hidden> so they stay out of the table of contents; a = Appendix
wrapper is synthesized when the source appendix has no section of its own.
```

- [ ] **Step 2: Update the CODEBASE_GUIDE node descriptions**

In `CODEBASE_GUIDE.md`, in section 9.6 (`split_deck`), add a sentence noting that frames after `\appendix` are tagged `is_appendix` (with the carried section reset) and a starred `\section*` sets `section_starred`. In section 9.10 (`assemble`), add a sentence noting that appendix frames are emitted after the bibliography via `#show: appendix`, with `<touying:hidden>` on their `=` and `==` headings and a synthesized `= Appendix` wrapper when the source gives no section. If section 11 documents `typst_scaffold.py` helpers, add `_hide_frame_title` and `_appendix_block` to that list.

- [ ] **Step 3: Verify nothing else broke**

Run: `uv run pytest -q`
Expected: PASS (docs do not affect tests). Manually confirm the README node names still match `src/b2t/nodes/`.

- [ ] **Step 4: Commit**

```bash
git add README.md CODEBASE_GUIDE.md
git commit -m "docs: describe appendix rendering and touying:hidden headings"
```

---

## Self-Review

**1. Spec coverage:**
- Detect `\appendix` region and tag frames: Task 2.
- Render appendix after references via `#show: appendix`: Task 3 (`_appendix_block`, `assemble`).
- Thank-you before the appendix (decision 2): Task 3 keeps the existing `_bibliography_block` (which ends with the thank-you slide) ahead of the appendix block.
- Hide appendix `=` and `==` headings; synthesize `= Appendix` when no section (decision 3): Task 3 (`_appendix_block`, `_hide_frame_title`).
- Hide starred `\section*` body headings (the other deterministic signal): Tasks 2 (`section_starred`) and 3 (`_section_heading` in `_body`).
- Deterministic only, no LLM (decision 1): no prompt or node changes; all hiding is in `split.py`/`typst_scaffold.py`.
- Unchanged convert/preview/review cycle and graph: confirmed (no edits to those files); `preview` reuses `assemble`.
- deck3 as the end-to-end fixture: Task 4.
- Error handling / no new failure modes (spec section 8): no `\appendix` leaves output identical (Task 3 `assemble` only adds a block when `appendix_pairs` is non-empty); empty appendix yields no block; `_hide_frame_title` returns unchanged when there is no `==` heading (tested in Task 3).

**2. Placeholder scan:** No "TBD"/"TODO"/"handle edge cases". Every code and test step carries concrete content. The doc task (Task 5) gives exact sentences to add and the exact sections to add them to.

**3. Type consistency:** `FrameUnit.is_appendix`/`section_starred` are defined in Task 1 and consumed identically in `split.py` (Task 2) and `typst_scaffold.py` (Task 3). `assemble(meta, aspect_ratio, has_toc, frames, converted, bib_name)` keeps the signature its callers (`assemble_node`, `preview_node`) already use, so no caller changes. `_body` changes from `(frames, converted)` to `(pairs)` but is private and called only inside `assemble`. `_hide_frame_title`, `_section_heading`, and `_appendix_block` are introduced and consumed within Task 3. `split_frames` keeps its `-> (list[FrameUnit], bool)` return type, so `split_deck` is unaffected.
