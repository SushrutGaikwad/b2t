from pathlib import Path

from pydantic import BaseModel, Field


class PipelineState(BaseModel):
    """Single state object threaded through the conversion graph."""

    # inputs (seeded by app.py)
    input_dir: Path
    output_dir: Path

    # working copy
    work_dir: Path | None = None

    # deterministic discoveries
    removed_build_files: list[Path] = Field(default_factory=list)
    main_tex: Path | None = None
    included_tex: list[Path] = Field(default_factory=list)
    image_files: list[Path] = Field(default_factory=list)
    flattened_tex: str | None = None
    stripped_tex: str | None = None

    # conversion (the one LLM step)
    typst_source: str | None = None
    typst_path: Path | None = None

    # compile (ground truth)
    compiled: bool = False
    pdf_path: Path | None = None
    compile_error: str | None = None
