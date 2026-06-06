from loguru import logger

from b2t.latex.detect import find_main_tex
from b2t.state import PipelineState


def detect_main(state: PipelineState) -> dict:
    """Locate the single beamer main .tex in the working copy.

    Args:
        state: Pipeline state carrying work_dir.

    Returns:
        State update with main_tex.

    Raises:
        ValueError: Propagated from find_main_tex when the count is not one.
    """
    main_tex = find_main_tex(state.work_dir)
    logger.debug("main tex: {}", main_tex.name)
    return {"main_tex": main_tex}
