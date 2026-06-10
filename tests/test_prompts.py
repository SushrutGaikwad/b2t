import pytest

from b2t.prompts import render


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
