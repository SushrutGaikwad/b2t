import shutil
import tempfile
from pathlib import Path

from loguru import logger

from b2t.state import PipelineState


def copy_input(state: PipelineState) -> dict:
    """Copy the read-only input deck into a fresh working directory.

    Args:
        state: Pipeline state carrying input_dir.

    Returns:
        State update with work_dir, the writable copy; the original input is
        never mutated.
    """
    work_dir = Path(tempfile.mkdtemp(prefix="b2t_")) / "deck"
    shutil.copytree(state.input_dir, work_dir)
    logger.debug("copied {} -> {}", state.input_dir, work_dir)
    return {"work_dir": work_dir}
