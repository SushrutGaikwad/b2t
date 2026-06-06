from loguru import logger

from b2t.latex.overlays import strip_overlays
from b2t.state import PipelineState


def strip_overlays_node(state: PipelineState) -> dict:
    """Remove beamer overlay constructs from the flattened source.

    Args:
        state: Pipeline state carrying flattened_tex.

    Returns:
        State update with stripped_tex, free of overlay commands and specs.
    """
    stripped = strip_overlays(state.flattened_tex)
    logger.debug("stripped overlays ({} chars)", len(stripped))
    return {"stripped_tex": stripped}
