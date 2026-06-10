"""Prompt registry: versioned prompt files plus token rendering."""

import re

_TOKEN_RE = re.compile(r"\{\{(\w+)\}\}")


def render(template: str, values: dict[str, str]) -> str:
    """Replace each {{token}} in template with values[token].

    Only the template is scanned; injected values are inserted verbatim and are
    never re-scanned, so LaTeX/Typst braces and dollar signs are untouched.

    Args:
        template: A user-message template containing {{token}} markers.
        values: Mapping of token name to replacement text.

    Returns:
        The rendered string.

    Raises:
        KeyError: If the template contains a {{token}} not present in values
            (catches typos early).
    """

    def repl(match: re.Match) -> str:
        key = match.group(1)
        if key not in values:
            raise KeyError(f"unknown template token: {{{{{key}}}}}")
        return values[key]

    return _TOKEN_RE.sub(repl, template)
