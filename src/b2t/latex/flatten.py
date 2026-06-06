import re
from pathlib import Path

_INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")


def flatten(main_tex: Path) -> str:
    """Expand \\input/\\include recursively into one LaTeX string.

    Args:
        main_tex: Path to the main .tex file; includes are resolved relative
            to its directory.

    Returns:
        The complete LaTeX source with every include replaced by its content.

    Raises:
        FileNotFoundError: If an included file is missing; content is never
            guessed.
    """
    deck_dir = main_tex.parent

    def expand(tex: Path) -> str:
        """Return the file's text with its includes expanded recursively."""
        text = tex.read_text(encoding="utf-8")

        def repl(match: re.Match) -> str:
            child = deck_dir / match.group(1)
            if child.suffix != ".tex":
                child = child.with_suffix(".tex")
            if not child.exists():
                raise FileNotFoundError(f"included file not found: {child}")
            return expand(child)

        return _INPUT_RE.sub(repl, text)

    return expand(main_tex)
