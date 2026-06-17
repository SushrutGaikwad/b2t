import re
from dataclasses import dataclass, field
from pathlib import Path

_INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")
_GRAPHIC_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".pdf", ".eps", ".gif")
_BIB_RE = re.compile(r"\\(?:addbibresource|bibliography)\{([^}]+)\}")


@dataclass
class Includes:
    """Files referenced by a deck.

    Attributes:
        tex: Included .tex files, in discovery order.
        images: Image files referenced by \\includegraphics, deduplicated.
    """

    tex: list[Path] = field(default_factory=list)
    images: list[Path] = field(default_factory=list)


def _resolve_tex(target: str, deck_dir: Path) -> Path:
    """Resolve an \\input/\\include target to a .tex path under deck_dir.

    Args:
        target: The raw brace argument, with or without the .tex suffix.
        deck_dir: Directory of the main .tex file.

    Returns:
        The target path with a .tex suffix (existence is checked by callers).
    """
    path = deck_dir / target
    if path.suffix != ".tex":
        path = path.with_suffix(".tex")
    return path


def _resolve_image(target: str, deck_dir: Path) -> Path:
    """Resolve an \\includegraphics target to an existing image file.

    Args:
        target: The raw brace argument; LaTeX allows omitting the extension.
        deck_dir: Directory searched recursively for extension candidates.

    Returns:
        Path to the existing image file.

    Raises:
        FileNotFoundError: If no file matches any known image extension.
    """
    candidate = deck_dir / target
    if candidate.suffix and candidate.exists():
        return candidate
    stem = Path(target).name
    for ext in _IMAGE_EXTS:
        for match in deck_dir.rglob(f"{stem}{ext}"):
            return match
    raise FileNotFoundError(rf"image not found for \includegraphics{{{target}}}")


def parse_includes(main_tex: Path) -> Includes:
    """Walk \\input/\\include recursively, collecting tex and image targets.

    Args:
        main_tex: Path to the main .tex file.

    Returns:
        An Includes with every reachable .tex include and referenced image.

    Raises:
        FileNotFoundError: If an included .tex or referenced image is missing;
            content is never guessed.
    """
    deck_dir = main_tex.parent
    result = Includes()
    seen: set[Path] = set()

    def walk(tex: Path) -> None:
        """Scan one .tex file for includes and recurse into new ones."""
        text = tex.read_text(encoding="utf-8")
        for raw in _INPUT_RE.findall(text):
            child = _resolve_tex(raw, deck_dir)
            if child in seen:
                continue
            seen.add(child)
            if not child.exists():
                raise FileNotFoundError(f"included file not found: {child}")
            result.tex.append(child)
            walk(child)
        for raw in _GRAPHIC_RE.findall(text):
            image = _resolve_image(raw, deck_dir)
            if image not in result.images:
                result.images.append(image)

    walk(main_tex)
    return result


def detect_bib_file(text: str, deck_dir: Path) -> Path | None:
    """Resolve a \\addbibresource/\\bibliography target to an existing .bib file.

    Args:
        text: LaTeX source to scan (preamble or whole deck).
        deck_dir: Directory the target is resolved against.

    Returns:
        The existing .bib path, or None if the deck declares no bibliography.

    Raises:
        FileNotFoundError: If a bibliography is declared but the file is missing.
    """
    match = _BIB_RE.search(text)
    if match is None:
        return None
    path = deck_dir / match.group(1)
    if path.suffix != ".bib":
        path = path.with_suffix(".bib")
    if not path.exists():
        raise FileNotFoundError(f"bibliography not found: {path}")
    return path
