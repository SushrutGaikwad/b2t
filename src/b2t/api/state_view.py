"""JSON-safe serialization of pipeline state and per-node delta folding."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def to_jsonsafe(value: Any) -> Any:
    """Convert one pipeline-state value to a JSON-safe form.

    Paths become strings, Pydantic models become dicts, lists and dicts
    recurse, primitives pass through, and anything else is stringified so a
    debug view never crashes on an unexpected type.
    """
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, (list, tuple)):
        return [to_jsonsafe(v) for v in value]
    if isinstance(value, dict):
        return {k: to_jsonsafe(v) for k, v in value.items()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def serialize_values(d: dict) -> dict:
    """Apply to_jsonsafe to each value of a dict (a node delta or the seed)."""
    return {k: to_jsonsafe(v) for k, v in d.items()}


@dataclass
class NodeDelta:
    """One node's contribution to state, JSON-safe.

    Attributes:
        node: The node name.
        changed: The field names this node wrote.
        values: The JSON-safe field values this node wrote.
    """

    node: str
    changed: list[str]
    values: dict


def fold_snapshot(
    seed_state: dict, deltas: list[NodeDelta], node: str
) -> tuple[list[str], dict]:
    """Fold the seed plus deltas up to and including `node`.

    Args:
        seed_state: JSON-safe seed (input_dir, output_dir, llm_choices).
        deltas: Per-node deltas in run order.
        node: The node whose accumulated snapshot is wanted.

    Returns:
        That node's changed list and the accumulated state dict.

    Raises:
        KeyError: If no delta matches `node` (it has not run).
    """
    acc = dict(seed_state)
    for d in deltas:
        acc.update(d.values)
        if d.node == node:
            return d.changed, acc
    raise KeyError(node)
