"""Map a beamer documentclass aspectratio to a Touying aspect-ratio string."""

import re

# Beamer's documented aspectratio codes mapped to Touying "W-H" strings.
# Touying 0.7.3 accepts any "W-H" with positive numbers (see utils.typ
# page-args-from-aspect-ratio); "4-3" and "16-9" use built-in paper sizes,
# every other ratio gets explicit width/height.
_RATIOS = {
    "43": "4-3",
    "169": "16-9",
    "1610": "16-10",
    "149": "14-9",
    "141": "141-100",
    "54": "5-4",
    "32": "3-2",
}

_ASPECT_RE = re.compile(r"aspectratio\s*=\s*(\d+)")

DEFAULT_ASPECT_RATIO = "4-3"


def aspect_ratio(main_tex: str) -> str:
    """Return the Touying aspect-ratio for a beamer main file's documentclass.

    Beamer defaults to 4:3 when no aspectratio option is given, so a missing
    or unrecognized code maps to "4-3".

    Args:
        main_tex: The main .tex source text.

    Returns:
        A Touying aspect-ratio string, e.g. "4-3", "16-9", or "16-10".
    """
    match = _ASPECT_RE.search(main_tex)
    if match is None:
        return DEFAULT_ASPECT_RATIO
    return _RATIOS.get(match.group(1), DEFAULT_ASPECT_RATIO)
