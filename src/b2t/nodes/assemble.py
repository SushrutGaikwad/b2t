from loguru import logger

from b2t.state import PipelineState
from b2t.typst_scaffold import assemble


def assemble_node(state: PipelineState) -> dict:
    """Assemble the converted frames and scaffold into the final Typst source.

    Args:
        state: Pipeline state carrying meta, aspect_ratio, has_toc, frames,
            converted_frames, and bib_file.

    Returns:
        State update with typst_source.
    """
    bib_name = state.bib_file.name if state.bib_file else None
    source = assemble(
        state.meta,
        state.aspect_ratio,
        state.has_toc,
        state.frames,
        state.converted_frames,
        bib_name,
    )
    logger.debug("assembled {} chars of typst", len(source))
    return {"typst_source": source}
