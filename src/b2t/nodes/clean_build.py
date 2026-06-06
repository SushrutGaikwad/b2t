from loguru import logger

from b2t.latex.cleanup import remove_build_files
from b2t.state import PipelineState


def clean_build(state: PipelineState) -> dict:
    """Delete LaTeX build artifacts from the working copy.

    Args:
        state: Pipeline state carrying work_dir.

    Returns:
        State update with removed_build_files, the deleted paths.
    """
    removed = remove_build_files(state.work_dir)
    logger.debug("removed {} build files", len(removed))
    return {"removed_build_files": removed}
