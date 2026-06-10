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
    included_tex: list[Path] = Field(default_factory=list)
    image_files: list[Path] = Field(default_factory=list)
    flattened_tex: str | None = None
    stripped_tex: str | None = None

    # per-node model + prompt-version selection (seeded at start) and the
    # provenance of what actually ran
    llm_choices: dict[str, NodeChoice] = Field(default_factory=dict)
    llm_runs: dict[str, NodeRun] = Field(default_factory=dict)

    # conversion (the one LLM step) and the written output
    typst_source: str | None = None
    typst_path: Path | None = None

    # compile (ground truth)
    compiled: bool = False
    pdf_path: Path | None = None
    compile_error: str | None = None
