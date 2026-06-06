def strip_code_fence(typst_source: str) -> str:
    """Remove a markdown code fence wrapping the entire source, if present.

    Some models wrap their whole answer in ```typst ... ```. A leading fence
    is valid Typst (it opens a raw block), so the deck compiles into a PDF of
    verbatim source; the compiler never flags it. Only a fence around the
    entire output is removed; raw blocks inside the deck are left alone.
    """
    lines = typst_source.strip().splitlines()
    if len(lines) < 2 or not lines[0].startswith("```") or lines[-1].strip() != "```":
        return typst_source
    return "\n".join(lines[1:-1]) + "\n"
