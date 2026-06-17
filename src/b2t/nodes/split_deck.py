from loguru import logger

from b2t.latex.includes import detect_bib_file
from b2t.latex.split import parse_meta, split_frames, split_preamble
from b2t.state import PipelineState


def split_deck(state: PipelineState) -> dict:
    """Split the stripped source into preamble, metadata, frames, and flags.

    Args:
        state: Pipeline state carrying stripped_tex and work_dir.

    Returns:
        State update with preamble, meta, frames, has_toc, and bib_file.

    Raises:
        ValueError: If the deck has no convertible frames after exclusions.
    """
    preamble, body = split_preamble(state.stripped_tex)
    meta = parse_meta(preamble)
    frames, has_toc = split_frames(body)
    if not frames:
        raise ValueError("no convertible frames found in deck")
    bib_file = detect_bib_file(state.stripped_tex, state.work_dir)
    logger.debug(
        "split into {} frames, toc={}, bib={}", len(frames), has_toc, bib_file
    )
    return {
        "preamble": preamble,
        "meta": meta,
        "frames": frames,
        "has_toc": has_toc,
        "bib_file": bib_file,
    }
