from pathlib import Path


def _is_main(text: str) -> bool:
    return (
        r"\documentclass" in text
        and "beamer" in text
        and r"\begin{document}" in text
    )


def find_main_tex(directory: Path) -> Path:
    """Return the one .tex declaring a beamer document. Fail loudly otherwise."""
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
