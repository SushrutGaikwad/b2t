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


class SaveRequest(BaseModel):
    source: str


class SaveResult(BaseModel):
    ok: bool
    error: str | None


class ModelsView(BaseModel):
    models: list[str]
    default: str


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
