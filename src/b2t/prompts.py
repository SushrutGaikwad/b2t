"""Prompt registry: versioned prompt files plus token rendering."""

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from b2t.config import PROMPTS_DIR

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


@dataclass
class PromptVersion:
    """One versioned prompt for a node.

    Attributes:
        node: The LLM node this prompt belongs to (e.g. "convert").
        version: The version id (the .toml filename stem, e.g. "v1").
        system: The system instruction.
        user_template: The user-message template with {{tokens}}.
        description: Optional human label for the version dropdown.
    """

    node: str
    version: str
    system: str
    user_template: str
    description: str = ""


def _defaults(base: Path) -> dict:
    """Return the parsed defaults.json mapping node -> default version."""
    return json.loads((base / "defaults.json").read_text(encoding="utf-8"))


def list_nodes(base: Path = PROMPTS_DIR) -> list[str]:
    """Return node names: subdirectories holding at least one *.toml version."""
    return sorted(
        p.name for p in base.iterdir() if p.is_dir() and any(p.glob("*.toml"))
    )


def list_versions(node: str, base: Path = PROMPTS_DIR) -> list[str]:
    """Return the sorted version ids (.toml stems) for a node."""
    return sorted(p.stem for p in (base / node).glob("*.toml"))


def default_version(node: str, base: Path = PROMPTS_DIR) -> str:
    """Return the default version id for a node.

    Raises:
        KeyError: If the node is absent from defaults.json (fail loud).
    """
    return _defaults(base)[node]


def load(node: str, version: str, base: Path = PROMPTS_DIR) -> PromptVersion:
    """Parse one version file into a PromptVersion.

    Raises:
        FileNotFoundError: If the version file is missing.
        KeyError: If `system` or `user_template` is absent from the file.
    """
    data = tomllib.loads(
        (base / node / f"{version}.toml").read_text(encoding="utf-8")
    )
    return PromptVersion(
        node=node,
        version=version,
        system=data["system"],
        user_template=data["user_template"],
        description=data.get("description", ""),
    )
