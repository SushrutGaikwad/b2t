import json
from pathlib import Path

import pytest

from b2t import prompts as P
from b2t.prompts import (
    PromptVersion,
    default_version,
    list_nodes,
    list_versions,
    load,
    render,
)


def test_render_replaces_known_tokens():
    assert render("a {{x}} b {{y}}", {"x": "1", "y": "2"}) == "a 1 b 2"


def test_render_preserves_latex_and_typst_syntax():
    template = "Keep $E=mc^2$ and \\frac{a}{b}, then {{source}}."
    assert render(template, {"source": "X"}) == "Keep $E=mc^2$ and \\frac{a}{b}, then X."


def test_render_raises_on_unknown_token():
    with pytest.raises(KeyError, match="typo"):
        render("hello {{typo}}", {"source": "X"})


def test_render_does_not_rescan_injected_values():
    # an injected value that itself looks like a token is left as-is
    assert render("{{source}}", {"source": "{{reference}}"}) == "{{reference}}"


def _make_registry(base: Path) -> None:
    (base / "convert").mkdir(parents=True)
    (base / "convert" / "v1.toml").write_text(
        'description = "first"\n'
        "system = '''Sys one'''\n"
        "user_template = '''U {{source}}'''\n",
        encoding="utf-8",
    )
    (base / "convert" / "v2.toml").write_text(
        "system = '''Sys two'''\n"
        "user_template = '''U2 {{source}}'''\n",
        encoding="utf-8",
    )
    (base / "defaults.json").write_text(json.dumps({"convert": "v1"}), encoding="utf-8")


def test_list_nodes_and_versions(tmp_path):
    _make_registry(tmp_path)
    assert list_nodes(base=tmp_path) == ["convert"]
    assert list_versions("convert", base=tmp_path) == ["v1", "v2"]


def test_default_version(tmp_path):
    _make_registry(tmp_path)
    assert default_version("convert", base=tmp_path) == "v1"


def test_load_returns_prompt_version(tmp_path):
    _make_registry(tmp_path)
    pv = load("convert", "v1", base=tmp_path)
    assert isinstance(pv, PromptVersion)
    assert pv.system == "Sys one"
    assert pv.user_template == "U {{source}}"
    assert pv.description == "first"


def test_load_missing_description_defaults_empty(tmp_path):
    _make_registry(tmp_path)
    assert load("convert", "v2", base=tmp_path).description == ""


def test_load_missing_version_raises(tmp_path):
    _make_registry(tmp_path)
    with pytest.raises(FileNotFoundError):
        load("convert", "v9", base=tmp_path)


def test_default_version_unknown_node_raises(tmp_path):
    _make_registry(tmp_path)
    with pytest.raises(KeyError):
        default_version("nope", base=tmp_path)


def test_real_convert_v2_is_default_and_loadable():
    assert P.default_version("convert") == "v2"
    pv = P.load("convert", "v2")
    assert "Typst Touying" in pv.system
    assert "Never use overlays" in pv.system
    for token in ("{{reference}}", "{{guides}}", "{{aspect_ratio}}", "{{source}}"):
        assert token in pv.user_template
    # the user message must still end exactly at the source so it stays the
    # final, freshest context the model reads
    assert pv.user_template.endswith("{{source}}")


def test_real_convert_v1_still_loadable_without_aspect_token():
    # v1 is kept for history; it predates the aspect-ratio directive
    pv = P.load("convert", "v1")
    assert "{{aspect_ratio}}" not in pv.user_template
