import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from b2t.graph import build_graph
from b2t.llm import ConverterLLM

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


def run_job(
    store: JobStore,
    job_id: str,
    input_dir: Path,
    output_dir: Path,
    converter: ConverterLLM,
) -> None:
    """Run the conversion graph, updating the job record as each node completes."""
    graph = build_graph(converter)
    seed = {"input_dir": input_dir, "output_dir": output_dir}
    state = dict(seed)
    store.update(job_id, status="running")
    try:
        for chunk in graph.stream(seed, stream_mode="updates"):
            for node, update in chunk.items():
                state.update(update)
                store.update(job_id, current_node=node)
    except Exception as exc:
        store.update(job_id, status="failed", error=str(exc))
        return

    main_tex = state.get("main_tex")
    store.update(
        job_id,
        main_tex=main_tex.name if main_tex else None,
        included_tex=[p.name for p in state.get("included_tex", [])],
        images=[p.name for p in state.get("image_files", [])],
        has_typst=state.get("typst_source") is not None,
        typst_path=state.get("typst_path"),
    )
    if state.get("compiled"):
        store.update(job_id, status="succeeded", pdf_path=state.get("pdf_path"))
    else:
        store.update(
            job_id, status="compile_failed", error=state.get("compile_error")
        )
