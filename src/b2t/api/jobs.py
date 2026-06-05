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
