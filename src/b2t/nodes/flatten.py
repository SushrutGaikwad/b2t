from loguru import logger

from b2t.latex.flatten import flatten
from b2t.latex.includes import parse_includes
from b2t.state import PipelineState


def flatten_node(state: PipelineState) -> dict:
    """Parse the include graph and expand the deck into one LaTeX string.

    Args:
        state: Pipeline state carrying main_tex.

    Returns:
        State update with included_tex, image_files, and flattened_tex.

    Raises:
        FileNotFoundError: Propagated when an include or image is missing.
    """
    includes = parse_includes(state.main_tex)
    logger.debug(
        "flattened {} includes, {} images", len(includes.tex), len(includes.images)
    )
    return {
        "included_tex": includes.tex,
        "image_files": includes.images,
        "flattened_tex": flatten(state.main_tex),
    }
