"""Deterministic splitting of a beamer deck into preamble, metadata, frames."""

import re

from b2t.state import DeckMeta, FrameUnit

_DOCUMENT = r"\begin{document}"


def split_preamble(stripped: str) -> tuple[str, str]:
    """Split the source at \\begin{document} into (preamble, body).

    Args:
        stripped: Flattened, overlay-free LaTeX source.

    Returns:
        The preamble (before \\begin{document}) and the body (after it).

    Raises:
        ValueError: If \\begin{document} is absent; the deck cannot be split.
    """
    idx = stripped.find(_DOCUMENT)
    if idx == -1:
        raise ValueError(r"no \begin{document} found")
    return stripped[:idx], stripped[idx + len(_DOCUMENT):]


def _field(name: str, preamble: str) -> str | None:
    """Return the brace argument of \\name in the preamble, or None."""
    match = re.search(rf"\\{name}\{{([^}}]*)\}}", preamble)
    return match.group(1).strip() if match else None


def parse_meta(preamble: str) -> DeckMeta:
    """Parse beamer title-block commands into DeckMeta.

    Nested braces in an argument are not handled (plain decks only); the raw
    \\date text is kept verbatim and rendered at assembly time.
    """
    return DeckMeta(
        title=_field("title", preamble),
        subtitle=_field("subtitle", preamble),
        author=_field("author", preamble),
        institute=_field("institute", preamble),
        date_raw=_field("date", preamble),
    )
