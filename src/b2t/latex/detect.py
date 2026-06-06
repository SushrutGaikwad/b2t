from pathlib import Path


def _is_main(text: str) -> bool:
    """Return True if the LaTeX source declares a beamer document."""
    return (
        r"\documentclass" in text
        and "beamer" in text
        and r"\begin{document}" in text
    )


def find_main_tex(directory: Path) -> Path:
    """Return the one .tex file declaring a beamer document.

    Args:
        directory: Deck directory to search recursively for .tex files.

    Returns:
        Path to the single main .tex file.

    Raises:
        ValueError: If zero or more than one candidate is found; the pipeline
            must fail loudly rather than guess.
    """
    candidates = [
        p
        for p in directory.rglob("*.tex")
        if _is_main(p.read_text(encoding="utf-8"))
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"expected exactly one beamer main .tex, found {len(candidates)}"
        )
    return candidates[0]
