import re
from pathlib import Path

_IMAGE_CALL_RE = re.compile(r'image\(\s*"([^"]+)"')


def fix_image_paths(typst_source: str, images: list[Path]) -> str:
    """Rewrite image() paths to the actual copied filenames, with extension.

    The LLM mirrors Beamer's extensionless \\includegraphics, but Typst needs
    the real filename. Images are copied flat into the output dir, so each
    reference is normalized to its basename with the correct extension.

    Args:
        typst_source: Generated Typst source possibly using bare image stems.
        images: The deck's image files, as discovered by the include parser.

    Returns:
        The source with every known image() reference rewritten to the copied
        filename. Unknown references are left untouched.
    """
    by_stem = {image.stem: image.name for image in images}

    def repl(match: re.Match) -> str:
        """Swap one image() argument for its known filename, if any."""
        name = by_stem.get(Path(match.group(1)).stem, match.group(1))
        return f'image("{name}"'

    return _IMAGE_CALL_RE.sub(repl, typst_source)
