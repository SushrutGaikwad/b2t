# Per-Frame Conversion with a Deterministic Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert a Beamer deck one frame at a time through a real LangGraph cycle, and build all fixed Typst structure (header, outline, bibliography, thank-you, section headings) deterministically.

**Architecture:** A new deterministic `split_deck` node turns the stripped source into a preamble, deck metadata, structural flags, and an ordered list of frames tagged with their section. The LLM node (kept registered as `convert`) translates one frame per invocation in a self-loop driven by a conditional edge. A deterministic `assemble` node then stitches the scaffold and converted frame bodies into `main.typ`.

**Tech Stack:** Python 3.12, LangGraph, Pydantic v2, pytest, loguru. Typst CLI is ground truth for compilation.

## Global Constraints

- Use `uv` for everything: `uv run pytest`, `uv add <pkg>`. Never call `python`/`pip` directly.
- No new third-party dependencies are needed for this plan.
- No LaTeX toolchain, ever. Input decks are read-only; never mutate the input dir.
- The generated deck must never use overlays or pause functionality.
- Deterministic logic lives in `latex/` and module-level helpers (network-free, tested directly); `nodes/` are thin state-in/state-out adapters.
- The LLM node stays registered in the graph under the name `convert`. `run_prompt`, `llm_choices`, `llm_runs`, the prompt directory `prompts/convert/`, and the `/api/graph` `is_llm` flag are all keyed off that registered node name, so it must not be renamed.
- No emojis anywhere. No em or en dashes in prose. Prefer clear docstrings, sparse inline comments.
- End each commit message with the trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- Keep all non-integration tests offline via `FakeClient`. Typst integration tests stay marked/skipped when the binary is absent.

---

### Task 1: State model for per-frame conversion

**Files:**
- Modify: `src/b2t/state.py`
- Test: `tests/test_state.py`

**Interfaces:**
- Produces: `DeckMeta(title, subtitle, author, institute, date_raw: str | None = None)`; `FrameUnit(raw: str, section: str | None = None)`; new `PipelineState` fields `preamble: str | None`, `meta: DeckMeta | None`, `has_toc: bool`, `bib_file: Path | None`, `frames: list[FrameUnit]`, `frame_index: int`, `converted_frames: list[str]`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_state.py`:

```python
from b2t.state import DeckMeta, FrameUnit


def test_per_frame_fields_default():
    state = PipelineState(input_dir=Path("in"), output_dir=Path("out"))
    assert state.preamble is None
    assert state.meta is None
    assert state.has_toc is False
    assert state.bib_file is None
    assert state.frames == []
    assert state.frame_index == 0
    assert state.converted_frames == []


def test_deck_meta_and_frame_unit_construct():
    meta = DeckMeta(title="T", author="A")
    assert meta.subtitle is None
    assert meta.date_raw is None
    unit = FrameUnit(raw=r"\begin{frame}x\end{frame}", section="Intro")
    assert unit.section == "Intro"
    assert FrameUnit(raw="y").section is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_state.py::test_per_frame_fields_default -v`
Expected: FAIL with `ImportError: cannot import name 'DeckMeta'`.

- [ ] **Step 3: Write minimal implementation**

In `src/b2t/state.py`, add the two submodels after `RenderedPrompt` and the new fields inside `PipelineState`.

```python
class DeckMeta(BaseModel):
    """Title-block metadata parsed from the beamer preamble."""

    title: str | None = None
    subtitle: str | None = None
    author: str | None = None
    institute: str | None = None
    date_raw: str | None = None


class FrameUnit(BaseModel):
    """One beamer frame plus the section it falls under.

    Attributes:
        raw: The whole \\begin{frame}...\\end{frame} source.
        section: The \\section this frame belongs to, or None if before any.
    """

    raw: str
    section: str | None = None
```

Add to `PipelineState` (after the existing `stripped_tex` field):

```python
    # deck structure (split_deck)
    preamble: str | None = None
    meta: DeckMeta | None = None
    has_toc: bool = False
    bib_file: Path | None = None
    frames: list[FrameUnit] = Field(default_factory=list)

    # per-frame conversion (the convert cycle)
    frame_index: int = 0
    converted_frames: list[str] = Field(default_factory=list)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_state.py -v`
Expected: PASS (all state tests).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/state.py tests/test_state.py
git commit -m "feat: add per-frame state fields and DeckMeta/FrameUnit"
```

---

### Task 2: Bibliography detection helper

**Files:**
- Modify: `src/b2t/latex/includes.py`
- Test: `tests/test_includes.py`

**Interfaces:**
- Produces: `detect_bib_file(text: str, deck_dir: Path) -> Path | None` - resolves a `\addbibresource`/`\bibliography` target to an existing `.bib` file under `deck_dir`, returns `None` when absent, raises `FileNotFoundError` when referenced but missing.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_includes.py`:

```python
from b2t.latex.includes import detect_bib_file

DECK1 = Path(__file__).parent / "fixtures" / "sample_decks" / "deck1"
DECK2 = Path(__file__).parent / "fixtures" / "sample_decks" / "deck2"


def test_detect_bib_file_found():
    text = (DECK2 / "main.tex").read_text(encoding="utf-8")
    bib = detect_bib_file(text, DECK2)
    assert bib is not None
    assert bib.name == "references.bib"
    assert bib.exists()


def test_detect_bib_file_absent():
    text = (DECK1 / "main.tex").read_text(encoding="utf-8")
    assert detect_bib_file(text, DECK1) is None


def test_detect_bib_file_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        detect_bib_file(r"\addbibresource{nope.bib}", tmp_path)
```

Ensure `tests/test_includes.py` imports `pytest` and `Path` (add if missing).

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_includes.py::test_detect_bib_file_found -v`
Expected: FAIL with `ImportError: cannot import name 'detect_bib_file'`.

- [ ] **Step 3: Write minimal implementation**

Add to `src/b2t/latex/includes.py` (near the top-level regexes and as a new function):

```python
_BIB_RE = re.compile(r"\\(?:addbibresource|bibliography)\{([^}]+)\}")


def detect_bib_file(text: str, deck_dir: Path) -> Path | None:
    """Resolve a \\addbibresource/\\bibliography target to an existing .bib file.

    Args:
        text: LaTeX source to scan (preamble or whole deck).
        deck_dir: Directory the target is resolved against.

    Returns:
        The existing .bib path, or None if the deck declares no bibliography.

    Raises:
        FileNotFoundError: If a bibliography is declared but the file is missing.
    """
    match = _BIB_RE.search(text)
    if match is None:
        return None
    path = deck_dir / match.group(1)
    if path.suffix != ".bib":
        path = path.with_suffix(".bib")
    if not path.exists():
        raise FileNotFoundError(f"bibliography not found: {path}")
    return path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_includes.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/latex/includes.py tests/test_includes.py
git commit -m "feat: detect the deck's .bib via addbibresource/bibliography"
```

---

### Task 3: Split preamble and parse metadata

**Files:**
- Create: `src/b2t/latex/split.py`
- Test: `tests/test_split.py`

**Interfaces:**
- Produces: `split_preamble(stripped: str) -> tuple[str, str]` returns `(preamble, body)` around `\begin{document}`, raising `ValueError` if absent; `parse_meta(preamble: str) -> DeckMeta`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_split.py`:

```python
import pytest

from b2t.latex.split import parse_meta, split_preamble

PREAMBLE = r"""\documentclass{beamer}
\title{A Minimal Sample Deck}
\subtitle{For Testing}
\author{Jane Doe}
\institute{Department of Examples}
\date{June 2026}
"""

DOC = PREAMBLE + r"""\begin{document}
\begin{frame}\titlepage\end{frame}
\section{Introduction}
\begin{frame}{Motivation}Body one\end{frame}
\end{document}"""


def test_split_preamble_divides_at_begin_document():
    pre, body = split_preamble(DOC)
    assert r"\title{A Minimal Sample Deck}" in pre
    assert r"\begin{document}" not in pre
    assert r"\begin{frame}{Motivation}" in body
    assert r"\title" not in body


def test_split_preamble_missing_document_raises():
    with pytest.raises(ValueError):
        split_preamble(r"\documentclass{beamer}")


def test_parse_meta_reads_all_fields():
    meta = parse_meta(PREAMBLE)
    assert meta.title == "A Minimal Sample Deck"
    assert meta.subtitle == "For Testing"
    assert meta.author == "Jane Doe"
    assert meta.institute == "Department of Examples"
    assert meta.date_raw == "June 2026"


def test_parse_meta_missing_fields_are_none():
    meta = parse_meta(r"\documentclass{beamer}")
    assert meta.title is None
    assert meta.author is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_split.py::test_split_preamble_divides_at_begin_document -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'b2t.latex.split'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/b2t/latex/split.py`:

```python
"""Deterministic splitting of a beamer deck into preamble, metadata, frames."""

import re

from b2t.state import DeckMeta, FrameUnit

_DOCUMENT = r"\begin{document}"


def split_preamble(stripped: str) -> tuple[str, str]:
    """Split the source at \\begin{document} into (preamble, body).

    Args:
        stripped: Flattened, overlay-free LaTeX source.

    Returns:
        The preamble (before \\begin{document}) and the body (after it).

    Raises:
        ValueError: If \\begin{document} is absent; the deck cannot be split.
    """
    idx = stripped.find(_DOCUMENT)
    if idx == -1:
        raise ValueError(r"no \begin{document} found")
    return stripped[:idx], stripped[idx + len(_DOCUMENT):]


def _field(name: str, preamble: str) -> str | None:
    """Return the brace argument of \\name in the preamble, or None."""
    match = re.search(rf"\\{name}\{{([^}}]*)\}}", preamble)
    return match.group(1).strip() if match else None


def parse_meta(preamble: str) -> DeckMeta:
    """Parse beamer title-block commands into DeckMeta.

    Nested braces in an argument are not handled (plain decks only); the raw
    \\date text is kept verbatim and rendered at assembly time.
    """
    return DeckMeta(
        title=_field("title", preamble),
        subtitle=_field("subtitle", preamble),
        author=_field("author", preamble),
        institute=_field("institute", preamble),
        date_raw=_field("date", preamble),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_split.py -v`
Expected: PASS (the four tests written so far).

- [ ] **Step 5: Commit**

```bash
git add src/b2t/latex/split.py tests/test_split.py
git commit -m "feat: split beamer preamble and parse title metadata"
```

---

### Task 4: Split the body into section-tagged frames

**Files:**
- Modify: `src/b2t/latex/split.py`
- Test: `tests/test_split.py`

**Interfaces:**
- Produces: `split_frames(body: str) -> tuple[list[FrameUnit], bool]` returns frames (each tagged with the current `\section`, with `\titlepage`/`\tableofcontents`/`\printbibliography` frames excluded) and `has_toc`. Raises `ValueError` on an unmatched `\begin{frame}`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_split.py`:

```python
from b2t.latex.split import split_frames

BODY = r"""
\begin{frame}\titlepage\end{frame}
\section{Introduction}
\begin{frame}{Motivation}One\end{frame}
\begin{frame}{Goals}Two\end{frame}
\section{Methods}
\begin{frame}{Approach}Three\end{frame}
"""


def test_split_frames_tags_sections_and_excludes_titlepage():
    frames, has_toc = split_frames(BODY)
    assert has_toc is False
    assert len(frames) == 3
    assert [f.section for f in frames] == ["Introduction", "Introduction", "Methods"]
    assert all(r"\titlepage" not in f.raw for f in frames)
    assert frames[0].raw == r"\begin{frame}{Motivation}One\end{frame}"


def test_split_frames_detects_toc_and_excludes_it():
    body = r"\begin{frame}\tableofcontents\end{frame}\begin{frame}{X}a\end{frame}"
    frames, has_toc = split_frames(body)
    assert has_toc is True
    assert len(frames) == 1
    assert frames[0].section is None


def test_split_frames_excludes_printbibliography_frame():
    body = r"\begin{frame}{Body}a\end{frame}" \
           r"\begin{frame}[allowframebreaks]{References}\printbibliography\end{frame}"
    frames, has_toc = split_frames(body)
    assert len(frames) == 1
    assert frames[0].raw == r"\begin{frame}{Body}a\end{frame}"


def test_split_frames_unmatched_begin_raises():
    with pytest.raises(ValueError):
        split_frames(r"\begin{frame}{X}a")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_split.py::test_split_frames_tags_sections_and_excludes_titlepage -v`
Expected: FAIL with `ImportError: cannot import name 'split_frames'`.

- [ ] **Step 3: Write minimal implementation**

Add to `src/b2t/latex/split.py`:

```python
_TOKEN_RE = re.compile(
    r"\\section\*?\{(?P<section>[^}]*)\}"
    r"|\\begin\{frame\}(?P<frame>.*?)\\end\{frame\}",
    re.DOTALL,
)

# Frames whose body holds one of these are rendered by the scaffold, not the LLM.
_SCAFFOLD_FRAME_MARKERS = (r"\titlepage", r"\tableofcontents", r"\printbibliography")


def split_frames(body: str) -> tuple[list[FrameUnit], bool]:
    """Split the document body into section-tagged frames.

    Walks the body in order, tracking the current \\section. The title-slide,
    table-of-contents, and bibliography frames are excluded because the scaffold
    renders them; the table-of-contents frame sets has_toc.

    Args:
        body: The text after \\begin{document}.

    Returns:
        The ordered convertible frames, and whether a \\tableofcontents frame
        was present.

    Raises:
        ValueError: If a \\begin{frame} has no matching \\end{frame}.
    """
    frames: list[FrameUnit] = []
    has_toc = False
    current_section: str | None = None
    matched = 0
    for match in _TOKEN_RE.finditer(body):
        if match.group("section") is not None:
            current_section = match.group("section").strip()
            continue
        matched += 1
        inner = match.group("frame")
        if r"\tableofcontents" in inner:
            has_toc = True
            continue
        if any(marker in inner for marker in _SCAFFOLD_FRAME_MARKERS):
            continue
        frames.append(FrameUnit(raw=match.group(0), section=current_section))
    if matched != body.count(r"\begin{frame}"):
        raise ValueError(r"unmatched \begin{frame} in document body")
    return frames, has_toc
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_split.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/latex/split.py tests/test_split.py
git commit -m "feat: split body into section-tagged frames, excluding scaffold frames"
```

---

### Task 5: split_deck node

**Files:**
- Create: `src/b2t/nodes/split_deck.py`
- Test: `tests/test_nodes.py`

**Interfaces:**
- Consumes: `split_preamble`, `parse_meta`, `split_frames` (Tasks 3-4), `detect_bib_file` (Task 2).
- Produces: `split_deck(state: PipelineState) -> dict` returning `preamble`, `meta`, `frames`, `has_toc`, `bib_file`. Raises `ValueError` if no convertible frames remain.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_nodes.py`:

```python
def test_split_deck_node(tmp_path):
    from b2t.nodes.split_deck import split_deck

    stripped = (
        "\\documentclass{beamer}\n\\title{T}\n\\date{June 2026}\n"
        "\\begin{document}\n"
        "\\begin{frame}\\titlepage\\end{frame}\n"
        "\\section{Intro}\n"
        "\\begin{frame}{Motivation}a\\end{frame}\n"
        "\\end{document}\n"
    )
    update = split_deck(_state(stripped_tex=stripped, work_dir=tmp_path))
    assert update["meta"].title == "T"
    assert update["has_toc"] is False
    assert update["bib_file"] is None
    assert [f.section for f in update["frames"]] == ["Intro"]
    assert r"\title" in update["preamble"]


def test_split_deck_node_raises_without_frames(tmp_path):
    from b2t.nodes.split_deck import split_deck

    stripped = "\\documentclass{beamer}\n\\begin{document}\n\\end{document}\n"
    with pytest.raises(ValueError):
        split_deck(_state(stripped_tex=stripped, work_dir=tmp_path))
```

Ensure `tests/test_nodes.py` imports `pytest` (add `import pytest` if missing).

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_nodes.py::test_split_deck_node -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'b2t.nodes.split_deck'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/b2t/nodes/split_deck.py`:

```python
from loguru import logger

from b2t.latex.includes import detect_bib_file
from b2t.latex.split import parse_meta, split_frames, split_preamble
from b2t.state import PipelineState


def split_deck(state: PipelineState) -> dict:
    """Split the stripped source into preamble, metadata, frames, and flags.

    Args:
        state: Pipeline state carrying stripped_tex and work_dir.

    Returns:
        State update with preamble, meta, frames, has_toc, and bib_file.

    Raises:
        ValueError: If the deck has no convertible frames after exclusions.
    """
    preamble, body = split_preamble(state.stripped_tex)
    meta = parse_meta(preamble)
    frames, has_toc = split_frames(body)
    if not frames:
        raise ValueError("no convertible frames found in deck")
    bib_file = detect_bib_file(state.stripped_tex, state.work_dir)
    logger.debug(
        "split into {} frames, toc={}, bib={}", len(frames), has_toc, bib_file
    )
    return {
        "preamble": preamble,
        "meta": meta,
        "frames": frames,
        "has_toc": has_toc,
        "bib_file": bib_file,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_nodes.py::test_split_deck_node tests/test_nodes.py::test_split_deck_node_raises_without_frames -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/nodes/split_deck.py tests/test_nodes.py
git commit -m "feat: add split_deck node"
```

---

### Task 6: render_date helper

**Files:**
- Create: `src/b2t/typst_scaffold.py`
- Test: `tests/test_scaffold.py`

**Interfaces:**
- Produces: `render_date(date_raw: str | None) -> str` returning a Typst date expression: `datetime(year:, month:, day:)` for parseable dates (day defaults to 1 for month-year), else `datetime.today()` with the raw text in a trailing comment.

- [ ] **Step 1: Write the failing test**

Create `tests/test_scaffold.py`:

```python
from b2t.typst_scaffold import render_date


def test_render_date_iso():
    assert render_date("2026-05-10") == "datetime(year: 2026, month: 5, day: 10)"


def test_render_date_month_day_year():
    assert render_date("May 10, 2026") == "datetime(year: 2026, month: 5, day: 10)"


def test_render_date_month_year_defaults_day_one():
    assert render_date("June 2026") == "datetime(year: 2026, month: 6, day: 1)"


def test_render_date_unparseable_falls_back_with_comment():
    out = render_date(r"\today")
    assert out.startswith("datetime.today()")
    assert "today" in out


def test_render_date_none_is_today():
    assert render_date(None) == "datetime.today()"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_scaffold.py::test_render_date_iso -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'b2t.typst_scaffold'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/b2t/typst_scaffold.py`:

```python
"""Deterministic assembly of the Typst Touying deck from converted frames."""

import re

_MONTHS = {
    name: i
    for i, name in enumerate(
        [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
        ],
        start=1,
    )
}


def render_date(date_raw: str | None) -> str:
    """Return a Typst date expression for a raw beamer \\date argument.

    Tries YYYY-MM-DD, 'Month DD, YYYY', and 'Month YYYY' (day defaults to 1).
    Anything else (including \\today or free text) falls back to
    datetime.today(), keeping the original text in a trailing comment.
    """
    if date_raw:
        text = date_raw.strip()
        iso = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
        if iso:
            y, m, d = (int(g) for g in iso.groups())
            return f"datetime(year: {y}, month: {m}, day: {d})"
        mdy = re.fullmatch(r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", text)
        if mdy and mdy.group(1).lower() in _MONTHS:
            return (
                f"datetime(year: {int(mdy.group(3))}, "
                f"month: {_MONTHS[mdy.group(1).lower()]}, day: {int(mdy.group(2))})"
            )
        my = re.fullmatch(r"([A-Za-z]+)\s+(\d{4})", text)
        if my and my.group(1).lower() in _MONTHS:
            return (
                f"datetime(year: {int(my.group(2))}, "
                f"month: {_MONTHS[my.group(1).lower()]}, day: 1)"
            )
        return f"datetime.today()  // original date: {text}"
    return "datetime.today()"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_scaffold.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/typst_scaffold.py tests/test_scaffold.py
git commit -m "feat: render beamer date into a typst datetime expression"
```

---

### Task 7: Header, outline, bibliography, and full assembly

**Files:**
- Modify: `src/b2t/typst_scaffold.py`
- Test: `tests/test_scaffold.py`

**Interfaces:**
- Consumes: `render_date` (Task 6), `DeckMeta`/`FrameUnit` (Task 1).
- Produces: `build_header(meta: DeckMeta | None, aspect_ratio: str) -> str`; `assemble(meta, aspect_ratio: str, has_toc: bool, frames: list[FrameUnit], converted: list[str], bib_name: str | None) -> str`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_scaffold.py`:

```python
from b2t.state import DeckMeta, FrameUnit
from b2t.typst_scaffold import assemble, build_header


def test_build_header_fills_meta_and_aspect():
    header = build_header(DeckMeta(title="My Talk", author="Jane"), "16-9")
    assert 'aspect-ratio: "16-9"' in header
    assert "title: [My Talk]" in header
    assert "author: [Jane]" in header
    assert "#title-slide()" in header


def test_build_header_uses_placeholders_when_meta_empty():
    header = build_header(None, "4-3")
    assert "title: [Main Title of the Presentation]" in header
    assert 'aspect-ratio: "4-3"' in header


def test_assemble_inserts_each_section_once_no_toc_no_bib():
    frames = [FrameUnit(raw="", section="Intro"), FrameUnit(raw="", section="Intro")]
    converted = ["== Motivation\n\nA", "== Goals\n\nB"]
    out = assemble(DeckMeta(title="T"), "4-3", False, frames, converted, None)
    assert out.count("= Intro") == 1
    assert "== Motivation" in out and "== Goals" in out
    assert "Outline" not in out
    assert "#bibliography" not in out


def test_assemble_with_toc_and_bibliography():
    frames = [FrameUnit(raw="", section=None)]
    converted = ["== X\n\nbody"]
    out = assemble(DeckMeta(), "4-3", True, frames, converted, "references.bib")
    assert "= Outline <touying:hidden>" in out
    assert "#components.adaptive-columns(outline(title: none, indent: 1em))" in out
    assert '#bibliography("references.bib", title: none, style: "apa")' in out
    assert "Thank you!" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_scaffold.py::test_build_header_fills_meta_and_aspect -v`
Expected: FAIL with `ImportError: cannot import name 'build_header'`.

- [ ] **Step 3: Write minimal implementation**

Add to `src/b2t/typst_scaffold.py`. Import `DeckMeta`/`FrameUnit` at the top:

```python
from b2t.state import DeckMeta, FrameUnit
```

Then add the templates and functions:

```python
_HEADER_TEMPLATE = '''#import "@preview/touying:0.7.3": *
#import themes.university: *

#import "@preview/theorion:0.6.0": *
#import cosmos.fancy: *
#show: show-theorion

#show: university-theme.with(
  align: horizon,
  aspect-ratio: "__ASPECT__",
  config-common(frozen-counters: (theorem-counter,), slide-level: 2),
  config-info(
    title: [__TITLE__],
    subtitle: [__SUBTITLE__],
    author: [__AUTHOR__],
    date: __DATE__,
    institution: [__INSTITUTION__],
  ),
)

// Comment out the following for heading numbering (like Beamer section numbers)
// #import "@preview/numbly:0.1.0": numbly
// #set heading(numbering: numbly("{1}.", default: "1.1"))

// Fonts (using New Computer Modern to avoid the Fira font warning)
#set text(
  // font: "New Computer Modern",  // comment out for default font
  weight: "light",
  size: 20pt,
  lang: "en",
  region: "US"
)

#title-slide()
'''

_OUTLINE = '''
= Outline <touying:hidden>

== Outline <touying:hidden>

#components.adaptive-columns(outline(title: none, indent: 1em))
'''


def build_header(meta: DeckMeta | None, aspect_ratio: str) -> str:
    """Build the deck header (imports, theme, config-info, title slide).

    Absent metadata fields fall back to the reference deck's placeholders, and
    the date is rendered by render_date.
    """
    m = meta or DeckMeta()
    return (
        _HEADER_TEMPLATE
        .replace("__ASPECT__", aspect_ratio)
        .replace("__TITLE__", m.title or "Main Title of the Presentation")
        .replace("__SUBTITLE__", m.subtitle or "Subtitle of the Presentation")
        .replace("__AUTHOR__", m.author or "Author's Name")
        .replace("__DATE__", render_date(m.date_raw))
        .replace("__INSTITUTION__", m.institute or "Institute's Name")
    )


def _bibliography_block(bib_name: str) -> str:
    """Return the References section, bibliography call, and thank-you slide."""
    return (
        "\n= References\n\n"
        "== References <touying:hidden>\n\n"
        f'#bibliography("{bib_name}", title: none, style: "apa")\n\n'
        "#slide(config: (\n"
        "  page: (header: none, footer: none),\n"
        "))[\n"
        "  #set align(center + horizon)\n"
        "  #text(size: 2.5em)[Thank you!]\n"
        "]\n"
    )


def _body(frames: list[FrameUnit], converted: list[str]) -> str:
    """Interleave = Section headings (on change) with converted frame bodies."""
    parts: list[str] = []
    prev_section: str | None = None
    for unit, typ in zip(frames, converted):
        if unit.section is not None and unit.section != prev_section:
            parts.append(f"= {unit.section}")
        prev_section = unit.section
        parts.append(typ.strip())
    return "\n\n".join(parts)


def assemble(
    meta: DeckMeta | None,
    aspect_ratio: str,
    has_toc: bool,
    frames: list[FrameUnit],
    converted: list[str],
    bib_name: str | None,
) -> str:
    """Assemble the full Typst deck from the scaffold and converted frames."""
    out = build_header(meta, aspect_ratio)
    if has_toc:
        out += _OUTLINE
    out += "\n" + _body(frames, converted) + "\n"
    if bib_name:
        out += _bibliography_block(bib_name)
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_scaffold.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/typst_scaffold.py tests/test_scaffold.py
git commit -m "feat: assemble header, outline, sections, and bibliography"
```

---

### Task 8: assemble node

**Files:**
- Create: `src/b2t/nodes/assemble.py`
- Test: `tests/test_nodes.py`

**Interfaces:**
- Consumes: `assemble` (Task 7).
- Produces: `assemble_node(state: PipelineState) -> dict` returning `typst_source`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_nodes.py`:

```python
def test_assemble_node_builds_typst_source():
    from b2t.nodes.assemble import assemble_node
    from b2t.state import DeckMeta, FrameUnit

    state = _state(
        meta=DeckMeta(title="T"),
        aspect_ratio="16-9",
        has_toc=False,
        frames=[FrameUnit(raw="", section="Intro")],
        converted_frames=["== Motivation\n\nbody"],
    )
    update = assemble_node(state)
    assert 'aspect-ratio: "16-9"' in update["typst_source"]
    assert "= Intro" in update["typst_source"]
    assert "== Motivation" in update["typst_source"]


def test_assemble_node_includes_bibliography_when_bib_present(tmp_path):
    from b2t.nodes.assemble import assemble_node
    from b2t.state import FrameUnit

    bib = tmp_path / "references.bib"
    bib.write_text("", encoding="utf-8")
    state = _state(
        frames=[FrameUnit(raw="", section=None)],
        converted_frames=["== X\n\nbody"],
        bib_file=bib,
    )
    update = assemble_node(state)
    assert '#bibliography("references.bib"' in update["typst_source"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_nodes.py::test_assemble_node_builds_typst_source -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'b2t.nodes.assemble'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/b2t/nodes/assemble.py`:

```python
from loguru import logger

from b2t.state import PipelineState
from b2t.typst_scaffold import assemble


def assemble_node(state: PipelineState) -> dict:
    """Assemble the converted frames and scaffold into the final Typst source.

    Args:
        state: Pipeline state carrying meta, aspect_ratio, has_toc, frames,
            converted_frames, and bib_file.

    Returns:
        State update with typst_source.
    """
    bib_name = state.bib_file.name if state.bib_file else None
    source = assemble(
        state.meta,
        state.aspect_ratio,
        state.has_toc,
        state.frames,
        state.converted_frames,
        bib_name,
    )
    logger.debug("assembled {} chars of typst", len(source))
    return {"typst_source": source}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_nodes.py::test_assemble_node_builds_typst_source tests/test_nodes.py::test_assemble_node_includes_bibliography_when_bib_present -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/nodes/assemble.py tests/test_nodes.py
git commit -m "feat: add assemble node"
```

---

### Task 9: Add the per-frame prompt convert/v3

**Files:**
- Create: `prompts/convert/v3.toml`
- Test: `tests/test_prompts.py`

**Interfaces:**
- Produces: prompt `convert/v3` with tokens `{{reference}}`, `{{guides}}`, `{{preamble}}`, `{{frame}}`. Default stays `v2` in this task (the switch to v3 happens in Task 11).

- [ ] **Step 1: Write the failing test**

Add to `tests/test_prompts.py`:

```python
def test_real_convert_v3_is_per_frame():
    pv = P.load("convert", "v3")
    assert "single" in pv.system.lower() or "frame" in pv.system.lower()
    for token in ("{{reference}}", "{{guides}}", "{{preamble}}", "{{frame}}"):
        assert token in pv.user_template
    assert "{{source}}" not in pv.user_template
    assert pv.user_template.rstrip().endswith("{{frame}}")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_prompts.py::test_real_convert_v3_is_per_frame -v`
Expected: FAIL with `FileNotFoundError` (v3 file missing).

- [ ] **Step 3: Write minimal implementation**

Create `prompts/convert/v3.toml` (use literal `'''` strings; do not escape backslashes):

```toml
# v3 converts one beamer frame at a time. The deterministic scaffold owns the
# preamble, outline, bibliography, thank-you slide, and section (=) headings, so
# this prompt emits only a == frame-title heading and the converted body.
description = "v3 - per-frame conversion"

system = '''You convert a single LaTeX Beamer frame into Typst Touying source for a presentation using the university theme. Output only the Typst for this one frame: a level-2 heading (==) carrying the frame title, followed by the converted body. Do not emit any imports, theme setup, title slide, outline, or preamble; those are generated separately. Use the provided reference presentation for body syntax and the guides for math. Map citation commands (\cite, \citep, \citet, \textcite, \parencite) to Typst @key references. Output only Typst source, with no commentary. Never use overlays or pause functionality.'''

user_template = '''
Reference Touying presentation (for body syntax and conventions):

{{reference}}

Guides:

{{guides}}

The Beamer preamble (context only, for custom macros; do not translate it):

{{preamble}}

Convert this single Beamer frame to Typst Touying source (a == heading plus body):

{{frame}}'''
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_prompts.py -v`
Expected: PASS (v3 test passes; the existing "v2 is default" test still passes because the default is unchanged).

- [ ] **Step 5: Commit**

```bash
git add prompts/convert/v3.toml tests/test_prompts.py
git commit -m "feat: add convert/v3 per-frame prompt"
```

---

### Task 10: convert_frame node (added, not yet wired)

**Files:**
- Create: `src/b2t/nodes/convert_frame.py`
- Test: `tests/test_nodes.py`

**Interfaces:**
- Consumes: `run_prompt` (`nodes/_llm.py`), `strip_code_fence` (`typst_output.py`), prompt `convert/v3` (Task 9). Note: it resolves prompt `convert/v3` only once the default is flipped in Task 11; this task's test passes an explicit `prompt_version` via `llm_choices`.
- Produces: `convert_frame(state: PipelineState, client: LLMClient) -> dict` that converts `frames[frame_index]`, appends to `converted_frames`, increments `frame_index`, and records provenance under key `convert`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_nodes.py`:

```python
def test_convert_frame_appends_and_advances():
    from b2t.llm import FakeClient
    from b2t.nodes.convert_frame import convert_frame
    from b2t.state import FrameUnit, NodeChoice

    state = _state(
        preamble="PRE",
        frames=[FrameUnit(raw="f0"), FrameUnit(raw="f1")],
        frame_index=0,
        llm_choices={"convert": NodeChoice(prompt_version="v3")},
    )
    update = convert_frame(state, client=FakeClient("== Title\n\nbody\n"))
    assert update["frame_index"] == 1
    assert update["converted_frames"] == ["== Title\n\nbody\n"]
    assert update["llm_runs"]["convert"].prompt_version == "v3"


def test_convert_frame_passes_preamble_and_frame_into_prompt():
    from b2t.nodes.convert_frame import convert_frame
    from b2t.state import FrameUnit, NodeChoice

    captured = {}

    class Recorder:
        def complete(self, system, user, model):
            captured["user"] = user
            return "== ok\n"

    state = _state(
        preamble="MYPREAMBLE",
        frames=[FrameUnit(raw="MYFRAME")],
        frame_index=0,
        llm_choices={"convert": NodeChoice(prompt_version="v3")},
    )
    convert_frame(state, client=Recorder())
    assert "MYPREAMBLE" in captured["user"]
    assert "MYFRAME" in captured["user"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_nodes.py::test_convert_frame_appends_and_advances -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'b2t.nodes.convert_frame'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/b2t/nodes/convert_frame.py`:

```python
from loguru import logger

from b2t.config import MATH_GUIDE, REFERENCE_DECK
from b2t.llm import LLMClient
from b2t.nodes._llm import run_prompt
from b2t.state import PipelineState
from b2t.typst_output import strip_code_fence


def convert_frame(state: PipelineState, client: LLMClient) -> dict:
    """Convert one beamer frame to Typst; registered in the graph as `convert`.

    Translates frames[frame_index] into a == heading plus body, appends it to
    converted_frames, and advances frame_index. A conditional edge loops back
    until every frame is converted.

    Args:
        state: Pipeline state carrying preamble, frames, frame_index.
        client: LLM client (bound via functools.partial when the graph is built).

    Returns:
        State update with the grown converted_frames, the next frame_index, and
        merged provenance under the `convert` key.
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
            "frame": frame.raw,
        },
    )
    return {
        "converted_frames": [*state.converted_frames, strip_code_fence(output)],
        "frame_index": state.frame_index + 1,
        "llm_runs": {**state.llm_runs, "convert": run},
        "llm_rendered": {**state.llm_rendered, "convert": rendered},
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_nodes.py::test_convert_frame_appends_and_advances tests/test_nodes.py::test_convert_frame_passes_preamble_and_frame_into_prompt -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/b2t/nodes/convert_frame.py tests/test_nodes.py
git commit -m "feat: add per-frame convert_frame node"
```

---

### Task 11: Wire the per-frame cycle (atomic switch)

This is the atomic cutover. It rewires the graph, flips the default prompt to
v3, copies the `.bib` in `write_output`, updates the offline fake output and
`PIPELINE_NODES`, removes the old whole-deck `convert` node, and updates every
test the cutover breaks so the suite is green in one commit.

**Files:**
- Modify: `src/b2t/graph.py`
- Modify: `prompts/defaults.json`
- Modify: `src/b2t/nodes/write_output.py`
- Modify: `src/b2t/api/app.py` (the `FAKE_TYPST` constant)
- Modify: `src/b2t/api/jobs.py` (`PIPELINE_NODES`)
- Delete: `src/b2t/nodes/convert.py`
- Modify/Test: `tests/test_nodes.py`, `tests/test_graph.py`, `tests/test_prompts.py`, `tests/test_api_app.py`, `tests/test_api_jobs.py`

**Interfaces:**
- Consumes: `split_deck` (Task 5), `convert_frame` (Task 10), `assemble_node` (Task 8).
- Produces: a compiled graph `... -> strip_overlays -> split_deck -> convert (cycle) -> assemble -> write_output -> compile`.

- [ ] **Step 1: Write/adjust the failing tests**

In `tests/test_graph.py`, replace the whole file body with:

```python
from pathlib import Path

from b2t.graph import build_graph
from b2t.llm import FakeClient
from b2t.typst_runner import typst_available

DECK1 = Path(__file__).parent / "fixtures" / "sample_decks" / "deck1"
DECK2 = Path(__file__).parent / "fixtures" / "sample_decks" / "deck2"

FRAME_BODY = "== Slide\n\nbody\n"


def test_pipeline_assembles_per_frame_deck(tmp_path):
    out = tmp_path / "out"
    graph = build_graph(FakeClient(FRAME_BODY))
    result = dict(graph.invoke({"input_dir": DECK1, "output_dir": out}))
    typ = (out / "main.typ").read_text(encoding="utf-8")
    assert "#title-slide()" in typ              # deterministic header
    assert "= Introduction" in typ              # section heading inserted once
    assert typ.count("== Slide") == 4           # deck1 has four content frames
    assert (out / "logo.png").exists()
    if typst_available():
        assert result["compiled"] is True
        assert Path(result["pdf_path"]).exists()


def test_pipeline_appends_bibliography_for_bib_deck(tmp_path):
    out = tmp_path / "out"
    graph = build_graph(FakeClient(FRAME_BODY))
    result = dict(graph.invoke({"input_dir": DECK2, "output_dir": out}))
    typ = (out / "main.typ").read_text(encoding="utf-8")
    assert '#bibliography("references.bib", title: none, style: "apa")' in typ
    assert "Thank you!" in typ
    assert (out / "references.bib").exists()
    # the \printbibliography frame must not be converted as a content frame
    assert "printbibliography" not in typ
```

In `tests/test_nodes.py`, delete the six old `test_convert_node_*` tests (lines that `from b2t.nodes.convert import convert_node`); they are replaced by the `convert_frame` tests from Task 10.

In `tests/test_prompts.py`, replace `test_real_convert_v2_is_default_and_loadable` with:

```python
def test_real_convert_default_is_v3():
    assert P.default_version("convert") == "v3"


def test_real_convert_v2_still_loadable():
    pv = P.load("convert", "v2")
    assert "Typst Touying" in pv.system
    assert "{{aspect_ratio}}" in pv.user_template
```

In `tests/test_api_app.py`, make these edits:
- `test_llm_nodes_endpoint_lists_convert_with_versions`: change `assert convert["default_version"] == "v2"` to `== "v3"`.
- `test_rendered_prompt_available_after_run`: change `assert body["prompt_version"] == "v2"` to `== "v3"` (the `"You convert LaTeX Beamer"` / `"Reference Touying presentation"` assertions stay, both appear in v3).
- Replace `test_node_state_available_after_run` with:

```python
def test_node_state_available_after_run():
    client = _client()
    job_id = _run_sample(client)
    body = client.get(f"/api/jobs/{job_id}/state/convert").json()
    assert body["node"] == "convert"
    assert "converted_frames" in body["changed"]
    assert "frames" in body["state"]
    asm = client.get(f"/api/jobs/{job_id}/state/assemble").json()
    assert "typst_source" in asm["changed"]
```

In `tests/test_api_jobs.py`, update the `PIPELINE_NODES` expectation (line ~56) to the new tuple and relax the deltas assertion (line ~126), since `convert` now repeats per frame:

```python
    assert PIPELINE_NODES == (
        "copy_input",
        "clean_build",
        "detect_main",
        "flatten",
        "strip_overlays",
        "split_deck",
        "convert",
        "assemble",
        "write_output",
        "compile",
    )
```

```python
    # convert repeats once per frame, so compare the distinct nodes in order
    seen = []
    for d in rec.node_deltas:
        if d.node not in seen:
            seen.append(d.node)
    assert seen == list(PIPELINE_NODES)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_graph.py -v`
Expected: FAIL (graph still wires the old whole-deck `convert`; `split_deck`/`assemble`/`convert` cycle not yet present, `references.bib` not copied).

- [ ] **Step 3: Make the implementation changes**

(a) `prompts/defaults.json`:

```json
{
  "convert": "v3"
}
```

(b) `src/b2t/graph.py` - replace the file with:

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
from b2t.nodes.split_deck import split_deck
from b2t.nodes.strip_overlays import strip_overlays_node
from b2t.nodes.write_output import write_output
from b2t.state import PipelineState


def _more_frames(state: PipelineState) -> str:
    """Loop back to convert while frames remain, else move on to assemble."""
    return "convert" if state.frame_index < len(state.frames) else "assemble"


def build_graph(client: LLMClient):
    """Build and compile the per-frame conversion graph.

    Args:
        client: LLM client bound into the convert node; every other node is
            deterministic.

    Returns:
        A compiled LangGraph runnable: copy_input -> clean_build -> detect_main
        -> flatten -> strip_overlays -> split_deck -> convert (self-loop over
        frames) -> assemble -> write_output -> compile.
    """
    graph = StateGraph(PipelineState)

    graph.add_node("copy_input", copy_input)
    graph.add_node("clean_build", clean_build)
    graph.add_node("detect_main", detect_main)
    graph.add_node("flatten", flatten_node)
    graph.add_node("strip_overlays", strip_overlays_node)
    graph.add_node("split_deck", split_deck)
    graph.add_node("convert", partial(convert_frame, client=client))
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
    graph.add_conditional_edges(
        "convert", _more_frames, {"convert": "convert", "assemble": "assemble"}
    )
    graph.add_edge("assemble", "write_output")
    graph.add_edge("write_output", "compile")
    graph.add_edge("compile", END)

    return graph.compile()
```

(c) `src/b2t/nodes/write_output.py` - copy the `.bib` alongside images. After the image copy loop, before the `logger.debug`, add:

```python
    if state.bib_file:
        shutil.copy2(state.bib_file, state.output_dir / state.bib_file.name)
```

(d) `src/b2t/api/app.py` - change `FAKE_TYPST` to a per-frame body:

```python
FAKE_TYPST = "== Sample\n\nGenerated by the fake converter.\n"
```

(e) `src/b2t/api/jobs.py` - update `PIPELINE_NODES`:

```python
PIPELINE_NODES = (
    "copy_input",
    "clean_build",
    "detect_main",
    "flatten",
    "strip_overlays",
    "split_deck",
    "convert",
    "assemble",
    "write_output",
    "compile",
)
```

(f) Delete the old whole-deck node:

```bash
git rm src/b2t/nodes/convert.py
```

- [ ] **Step 4: Run the full suite to verify it passes**

Run: `uv run pytest -q`
Expected: PASS (all tests). If `typst` is installed, the deck1/deck2 integration assertions compile the assembled decks; the first compile fetches the Touying/theorion packages from `@preview`, so a network connection is required on first run.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: convert per frame through a graph cycle with a deterministic scaffold"
```

---

### Task 12: Update docs (README and CODEBASE_GUIDE)

**Files:**
- Modify: `README.md`
- Modify: `CODEBASE_GUIDE.md`

**Interfaces:**
- None (documentation only).

- [ ] **Step 1: Update the README node list**

In `README.md`, update the "Nodes" section and the mermaid flowchart so the pipeline reads `... strip_overlays -> split_deck -> convert (per frame) -> assemble -> write_output -> compile`. Add entries:
- `split_deck` (deterministic): splits the stripped source into preamble, title metadata, an ordered list of section-tagged frames, a table-of-contents flag, and the detected `.bib`; excludes the title, outline, and bibliography frames.
- `convert` (LLM): now converts one frame per invocation in a cycle, emitting a `==` frame-title heading plus the body; the scaffold owns all fixed structure.
- `assemble` (deterministic): builds the header, optional outline, section headings, converted frame bodies, and optional bibliography plus thank-you slide.

Update the `write_output` entry to note it also copies the `.bib`.

- [ ] **Step 2: Update CODEBASE_GUIDE node count**

In `CODEBASE_GUIDE.md`, update the `PIPELINE_NODES` reference (it currently says "eight nodes in order") to ten nodes and list the new `split_deck` and `assemble` nodes and the per-frame `convert` cycle.

- [ ] **Step 3: Verify docs reference real names**

Run: `uv run pytest -q`
Expected: PASS (unchanged; docs do not affect tests). Manually confirm the README node names match `src/b2t/nodes/`.

- [ ] **Step 4: Commit**

```bash
git add README.md CODEBASE_GUIDE.md
git commit -m "docs: describe the per-frame split_deck/convert/assemble pipeline"
```

---

## Self-Review

**1. Spec coverage:**
- Split into preamble + metadata + flags + frames: Tasks 3-5.
- Deterministic scaffold (header, outline, bibliography, thank-you, section headings): Tasks 6-8.
- Title metadata with date fallback: Tasks 1, 3, 6.
- `.bib` detection and copy: Tasks 2, 5, 11(c).
- Per-frame conversion as a real graph cycle: Tasks 10, 11.
- Heading ownership (LLM `==`, scaffold `=`): Tasks 7 (`_body`), 9 (prompt), 11.
- Citations mapped by the model: Task 9 prompt.
- Frame exclusions (titlepage, TOC, printbibliography): Task 4.
- Error handling (no document, no frames, missing bib, unmatched frame): Tasks 2, 3, 4, 5.
- Known limitations (UI cycle rendering, subsections, full reference per frame): carried as comments/docs; no code owed this increment.

**2. Placeholder scan:** No "TBD"/"TODO"/"handle edge cases" placeholders; every code and test step carries concrete content.

**3. Type consistency:** `DeckMeta`/`FrameUnit` fields are used identically in `state.py`, `split.py`, `typst_scaffold.py`, and the nodes. `assemble(meta, aspect_ratio, has_toc, frames, converted, bib_name)` signature matches its single caller `assemble_node`. The LLM node is `convert_frame` (function) registered as `"convert"` (graph node / prompt key) consistently across Tasks 10-11. `detect_bib_file(text, deck_dir)` matches its caller in `split_deck`. `render_date` is defined in Task 6 and consumed by `build_header` in Task 7.
