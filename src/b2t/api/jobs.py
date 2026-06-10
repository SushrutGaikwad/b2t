import threading
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger

from b2t.api.state_view import NodeDelta, serialize_values
from b2t.graph import build_graph
from b2t.llm import LLMClient

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
    """One conversion job's mutable record, as shown to the UI.

    Attributes:
        id: Opaque job identifier (uuid hex).
        status: queued | running | succeeded | compile_failed | failed.
        current_node: Name of the pipeline node currently running, if any.
        error: Failure or compile error text, if any.
        input_dir: Directory the deck was read from.
        output_dir: Directory main.typ, images, and the PDF are written to.
        main_tex: Detected main file name, once known.
        included_tex: Names of included .tex files, once known.
        images: Names of referenced images, once known.
        has_typst: True once Typst source has been generated.
        typst_path: Path to the written main.typ, once written.
        pdf_path: Path to the compiled PDF, on success.
        seed_state: JSON-safe pipeline seed (input/output dirs, choices).
        node_deltas: Per-node JSON-safe deltas captured as each node finished.
    """

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
    llm_runs: dict[str, dict] = field(default_factory=dict)
    llm_rendered: dict[str, dict] = field(default_factory=dict)
    seed_state: dict = field(default_factory=dict)
    node_deltas: list[NodeDelta] = field(default_factory=list)


class JobStore:
    """Thread-safe in-memory job registry shared by handlers and workers."""

    def __init__(self) -> None:
        """Create an empty registry guarded by a lock."""
        self._jobs: dict[str, JobRecord] = {}
        self._lock = threading.Lock()

    def create(self, **kwargs) -> JobRecord:
        """Create and register a new job.

        Args:
            **kwargs: Initial JobRecord fields (e.g. input_dir, output_dir).

        Returns:
            The new JobRecord with a fresh id.
        """
        job = JobRecord(id=uuid.uuid4().hex, **kwargs)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> JobRecord | None:
        """Return the job with this id, or None if unknown."""
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **changes) -> None:
        """Apply field changes to an existing job.

        Args:
            job_id: Id of a job that must already exist.
            **changes: JobRecord fields to overwrite.
        """
        with self._lock:
            job = self._jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)

    def append_delta(self, job_id: str, delta: NodeDelta) -> None:
        """Append one captured node delta to the job's snapshot trail."""
        with self._lock:
            self._jobs[job_id].node_deltas.append(delta)


def run_job(
    store: JobStore,
    job_id: str,
    input_dir: Path,
    output_dir: Path,
    make_client: Callable[[], LLMClient],
    choices: dict | None = None,
) -> None:
    """Run the conversion graph, updating the job record as each node runs.

    current_node is driven by debug "task" events, which fire when a node is
    about to run, so the record names the node that is actually running (not the
    last one that finished). Final state is accumulated from the "updates".

    The client is constructed inside the failure boundary so a missing API
    key records the job as failed instead of crashing the request handler.

    Args:
        store: Registry holding the job's record.
        job_id: Id of the record to drive.
        input_dir: Deck directory to convert (treated as read-only).
        output_dir: Directory for main.typ, images, and the PDF.
        make_client: Zero-arg factory producing the LLMClient.
        choices: Optional per-node {model, prompt_version} selection.

    Returns:
        None. The outcome lands on the job record: succeeded, compile_failed
        (with the compiler's error), or failed (with the exception text).
    """
    seed = {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "llm_choices": choices or {},
    }
    state = dict(seed)
    store.update(job_id, status="running", seed_state=serialize_values(seed))
    logger.info("job {} running: {} -> {}", job_id, input_dir, output_dir)
    try:
        graph = build_graph(make_client())
        for mode, chunk in graph.stream(seed, stream_mode=["updates", "debug"]):
            if mode == "debug":
                if chunk.get("type") == "task":
                    node = chunk["payload"]["name"]
                    logger.debug("job {} at node {}", job_id, node)
                    store.update(job_id, current_node=node)
            else:
                for node_name, update in chunk.items():
                    state.update(update)
                    store.append_delta(
                        job_id,
                        NodeDelta(node_name, list(update), serialize_values(update)),
                    )
    except Exception as exc:
        logger.error("job {} failed: {}", job_id, exc)
        store.update(job_id, status="failed", error=str(exc))
        return

    main_tex = state.get("main_tex")
    runs = state.get("llm_runs", {})
    rendered = state.get("llm_rendered", {})
    store.update(
        job_id,
        main_tex=main_tex.name if main_tex else None,
        included_tex=[p.name for p in state.get("included_tex", [])],
        images=[p.name for p in state.get("image_files", [])],
        has_typst=state.get("typst_source") is not None,
        typst_path=state.get("typst_path"),
        llm_runs={
            node: {"model": run.model, "prompt_version": run.prompt_version}
            for node, run in runs.items()
        },
        llm_rendered={
            node: {"system": r.system, "user": r.user}
            for node, r in rendered.items()
        },
    )
    if state.get("compiled"):
        logger.info("job {} succeeded", job_id)
        store.update(job_id, status="succeeded", pdf_path=state.get("pdf_path"))
    else:
        logger.warning("job {} compile failed", job_id)
        store.update(
            job_id, status="compile_failed", error=state.get("compile_error")
        )
