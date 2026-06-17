from pathlib import Path

from pydantic import BaseModel, Field


class NodeChoice(BaseModel):
    """A per-node UI selection. None means use the default."""

    model: str | None = None
    prompt_version: str | None = None


class NodeRun(BaseModel):
    """What an LLM node actually used, recorded for provenance."""

    model: str
    prompt_version: str


class RenderedPrompt(BaseModel):
    """The exact system and user message an LLM node sent, for preview."""

    system: str
    user: str


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


class PipelineState(BaseModel):
    """Single state object threaded through the conversion graph.

    Each node receives the current state and returns a partial update dict;
    LangGraph merges updates into the next state. Fields are grouped by the
    stage that produces them.
    """

    # inputs (seeded by app.py)
    input_dir: Path
    output_dir: Path

    # working copy (copy_input)
    work_dir: Path | None = None

    # deterministic discoveries (clean_build, detect_main, flatten,
    # strip_overlays)
    removed_build_files: list[Path] = Field(default_factory=list)
    main_tex: Path | None = None
    aspect_ratio: str = "4-3"
    included_tex: list[Path] = Field(default_factory=list)
    image_files: list[Path] = Field(default_factory=list)
    flattened_tex: str | None = None
    stripped_tex: str | None = None

    # deck structure (split_deck)
    preamble: str | None = None
    meta: DeckMeta | None = None
    has_toc: bool = False
    bib_file: Path | None = None
    frames: list[FrameUnit] = Field(default_factory=list)

    # per-frame conversion (the convert cycle)
    frame_index: int = 0
    converted_frames: list[str] = Field(default_factory=list)

    # human-in-the-loop review
    hitl_enabled: bool = False
    candidate: str | None = None
    feedback: str | None = None
    preview_path: Path | None = None
    preview_pdf: Path | None = None
    preview_error: str | None = None

    # per-node model + prompt-version selection (seeded at start) and the
    # provenance of what actually ran
    llm_choices: dict[str, NodeChoice] = Field(default_factory=dict)
    llm_runs: dict[str, NodeRun] = Field(default_factory=dict)
    # the exact rendered prompt each LLM node sent (large; never enters JobView)
    llm_rendered: dict[str, RenderedPrompt] = Field(default_factory=dict)

    # conversion (the one LLM step) and the written output
    typst_source: str | None = None
    typst_path: Path | None = None

    # compile (ground truth)
    compiled: bool = False
    pdf_path: Path | None = None
    compile_error: str | None = None
