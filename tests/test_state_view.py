from pathlib import Path

import pytest

from b2t.api.state_view import (
    NodeDelta,
    fold_snapshot,
    serialize_values,
    to_jsonsafe,
)
from b2t.state import NodeRun, RenderedPrompt


def test_to_jsonsafe_path():
    assert to_jsonsafe(Path("/tmp/x")) == str(Path("/tmp/x"))


def test_to_jsonsafe_list_of_paths():
    assert to_jsonsafe([Path("a.tex"), Path("b.tex")]) == ["a.tex", "b.tex"]


def test_to_jsonsafe_tuple_becomes_list():
    assert to_jsonsafe((Path("a.tex"), Path("b.tex"))) == ["a.tex", "b.tex"]


def test_to_jsonsafe_basemodel():
    run = NodeRun(model="m/x", prompt_version="v1")
    assert to_jsonsafe(run) == {"model": "m/x", "prompt_version": "v1"}


def test_to_jsonsafe_nested_dict_of_models():
    rendered = {"convert": RenderedPrompt(system="s", user="u")}
    assert to_jsonsafe(rendered) == {"convert": {"system": "s", "user": "u"}}


def test_to_jsonsafe_passes_primitives():
    assert to_jsonsafe(True) is True
    assert to_jsonsafe(None) is None
    assert to_jsonsafe(7) == 7


def test_to_jsonsafe_stringifies_unknown():
    class Weird:
        def __str__(self):
            return "weird"

    assert to_jsonsafe(Weird()) == "weird"


def test_serialize_values():
    out = serialize_values({"main_tex": Path("main.tex"), "compiled": False})
    assert out == {"main_tex": "main.tex", "compiled": False}


def test_fold_snapshot_accumulates_to_node():
    seed = {"input_dir": "/in"}
    deltas = [
        NodeDelta("copy_input", ["work_dir"], {"work_dir": "/work"}),
        NodeDelta("detect_main", ["main_tex"], {"main_tex": "main.tex"}),
    ]
    changed, state = fold_snapshot(seed, deltas, "detect_main")
    assert changed == ["main_tex"]
    assert state == {"input_dir": "/in", "work_dir": "/work", "main_tex": "main.tex"}


def test_fold_snapshot_stops_at_requested_node():
    deltas = [NodeDelta("a", ["x"], {"x": 1}), NodeDelta("b", ["y"], {"y": 2})]
    changed, state = fold_snapshot({}, deltas, "a")
    assert changed == ["x"]
    assert state == {"x": 1}  # b's delta is not applied


def test_fold_snapshot_unknown_node_raises():
    with pytest.raises(KeyError):
        fold_snapshot({}, [NodeDelta("a", ["x"], {"x": 1})], "missing")
