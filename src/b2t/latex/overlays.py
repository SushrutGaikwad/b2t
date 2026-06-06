import re

_OVERLAY_CMDS = r"only|uncover|visible|onslide"

# \cmd<spec>{body} -> body  (non-nested body)
_UNWRAP_RE = re.compile(rf"\\(?:{_OVERLAY_CMDS})<[^>]*>\{{([^{{}}]*)\}}")
# \cmd<spec> with no body (switch form)
_SWITCH_RE = re.compile(rf"\\(?:{_OVERLAY_CMDS})<[^>]*>")
# \pause
_PAUSE_RE = re.compile(r"\\pause\b")
# leftover specs attached to other commands, e.g. \item<1->
_SPEC_RE = re.compile(r"<[0-9][^>]*>")


def strip_overlays(text: str) -> str:
    """Remove beamer overlay constructs, keeping the content they wrap.

    Args:
        text: Flattened LaTeX source.

    Returns:
        The source with \\pause, \\only/\\uncover/\\visible/\\onslide, and
        <...> overlay specs removed; wrapped content is preserved. The output
        deck never uses overlays.
    """
    text = _UNWRAP_RE.sub(r"\1", text)
    text = _SWITCH_RE.sub("", text)
    text = _PAUSE_RE.sub("", text)
    text = _SPEC_RE.sub("", text)
    return text
