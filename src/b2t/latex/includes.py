import re
from dataclasses import dataclass, field
from pathlib import Path

_INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")
_GRAPHIC_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".pdf", ".eps", ".gif")


@dataclass
class Includes:
    tex: list[Path] = field(default_factory=list)
    images: list[Path] = field(default_factory=list)


def _resolve_tex(target: str, deck_dir: Path) -> Path:
    path = deck_dir / target
    if path.suffix != ".tex":
        path = path.with_suffix(".tex")
    return path


def _resolve_image(target: str, deck_dir: Path) -> Path:
    candidate = deck_dir / target
    if candidate.suffix and candidate.exists():
        return candidate
    stem = Path(target).name
    for ext in _IMAGE_EXTS:
        for match in deck_dir.rglob(f"{stem}{ext}"):
            return match
    raise FileNotFoundError(rf"image not found for \includegraphics{{{target}}}")


def parse_includes(main_tex: Path) -> Includes:
    """Walk \\input/\\include recursively, collecting tex and image targets."""
    deck_dir = main_tex.parent
    result = Includes()
    seen: set[Path] = set()

    def walk(tex: Path) -> None:
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
