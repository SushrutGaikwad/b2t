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
    """Return the brace argument of \\name in the preamble, or None.

    Tolerates Beamer's optional short form, e.g. \\title[Short]{The Long Title}.
    """
    match = re.search(rf"\\{name}(?:\[[^\]]*\])?\{{([^}}]*)\}}", preamble)
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


_TOKEN_RE = re.compile(
    r"\\section(?P<star>\*)?\{(?P<section>[^}]*)\}"
    r"|\\begin\{frame\}(?P<frame>.*?)\\end\{frame\}"
    r"|(?P<appendix>\\appendix)\b",
    re.DOTALL,
)

# Frames whose body holds one of these are rendered by the scaffold, not the LLM.
_SCAFFOLD_FRAME_MARKERS = (r"\titlepage", r"\tableofcontents", r"\printbibliography")

# The \frame{...} / \frame<...>{...} shorthand, but not \frametitle{...}.
_FRAME_SHORTHAND_RE = re.compile(r"\\frame(?=[\s<{])")


def split_frames(body: str) -> tuple[list[FrameUnit], bool]:
    """Split the document body into section-tagged frames.

    Walks the body in order, tracking the current \\section (and whether it was
    starred) and whether \\appendix has been seen. Every frame after \\appendix
    is tagged is_appendix with the carried section reset to None. The title-slide,
    table-of-contents, and bibliography frames are excluded because the scaffold
    renders them; the table-of-contents frame sets has_toc.

    Args:
        body: The text after \\begin{document}.

    Returns:
        The ordered convertible frames, and whether a \\tableofcontents frame
        was present.

    Raises:
        ValueError: If a \\begin{frame} has no matching \\end{frame}, or if the
            \\frame{...} shorthand is used (it would otherwise be silently lost).
    """
    if _FRAME_SHORTHAND_RE.search(body):
        raise ValueError(
            r"\frame{...} shorthand is not supported; use \begin{frame}...\end{frame}"
        )
    frames: list[FrameUnit] = []
    has_toc = False
    current_section: str | None = None
    section_starred = False
    in_appendix = False
    matched = 0
    for match in _TOKEN_RE.finditer(body):
        if match.group("appendix") is not None:
            in_appendix = True
            current_section = None
            section_starred = False
            continue
        if match.group("section") is not None:
            current_section = match.group("section").strip() or None
            section_starred = match.group("star") is not None
            continue
        matched += 1
        inner = match.group("frame")
        if r"\tableofcontents" in inner:
            has_toc = True
            continue
        if any(marker in inner for marker in _SCAFFOLD_FRAME_MARKERS):
            continue
        frames.append(
            FrameUnit(
                raw=match.group(0),
                section=current_section,
                is_appendix=in_appendix,
                section_starred=section_starred,
            )
        )
    if matched != body.count(r"\begin{frame}"):
        raise ValueError(r"unmatched \begin{frame} in document body")
    return frames, has_toc
