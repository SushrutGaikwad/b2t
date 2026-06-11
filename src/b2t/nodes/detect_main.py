from loguru import logger

from b2t.latex.aspect import aspect_ratio
from b2t.latex.detect import find_main_tex
from b2t.state import PipelineState


def detect_main(state: PipelineState) -> dict:
    """Locate the single beamer main .tex and read its aspect ratio.

    Args:
        state: Pipeline state carrying work_dir.

    Returns:
        State update with main_tex and the Touying aspect_ratio derived from
        the documentclass aspectratio option.

    Raises:
        ValueError: Propagated from find_main_tex when the count is not one.
    """
    main_tex = find_main_tex(state.work_dir)
    ratio = aspect_ratio(main_tex.read_text(encoding="utf-8"))
    logger.debug("main tex: {}, aspect-ratio: {}", main_tex.name, ratio)
    return {"main_tex": main_tex, "aspect_ratio": ratio}
