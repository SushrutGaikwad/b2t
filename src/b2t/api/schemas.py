from pathlib import Path

from pydantic import BaseModel

from b2t.api.jobs import JobRecord


class NodeRunView(BaseModel):
    """What an LLM node used on a run: the model and prompt version."""

    model: str
    prompt_version: str


class JobCreated(BaseModel):
    """Response to a job submission: the new job's id and initial status."""

    job_id: str
    status: str


class JobView(BaseModel):
    """A job's public state, as polled by the UI.

    Mirrors JobRecord but exposes names instead of paths, and has_pdf as a
    live filesystem check.
    """

    id: str
    status: str
    current_node: str | None
    error: str | None
    main_tex: str | None
    included_tex: list[str]
    images: list[str]
    has_typst: bool
    has_pdf: bool
    llm_runs: dict[str, NodeRunView] = {}


class SaveRequest(BaseModel):
    """Body for save-and-compile: the edited Typst source to write."""

    source: str


class SaveResult(BaseModel):
    """Outcome of save-and-compile: ok plus the compiler error, if any."""

    ok: bool
    error: str | None


class ModelOption(BaseModel):
    """One dropdown entry: the OpenRouter model id and its display label."""

    id: str
    label: str


class ModelsView(BaseModel):
    """The model catalog as dropdown options plus the default model id."""

    models: list[ModelOption]
    default: str


class GraphView(BaseModel):
    """The pipeline topology as a mermaid flowchart definition."""

    mermaid: str


class VersionOption(BaseModel):
    """One prompt-version dropdown entry."""

    id: str
    label: str


class LLMNodeView(BaseModel):
    """An LLM node with its available prompt versions and default."""

    node: str
    versions: list[VersionOption]
    default_version: str


class LLMNodesView(BaseModel):
    """All LLM nodes, for building per-node UI controls."""

    nodes: list[LLMNodeView]


def to_view(job: JobRecord) -> JobView:
    """Project a JobRecord onto the public JobView.

    Args:
        job: The internal job record.

    Returns:
        A JobView with file names instead of paths and has_pdf checked
        against the filesystem.
    """
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
        llm_runs={
            node: NodeRunView(**run) for node, run in job.llm_runs.items()
        },
    )
