from pathlib import Path

from b2t.latex.overlays import strip_overlays

FIXTURE = Path(__file__).parent / "fixtures" / "overlay_snippet.tex"


def test_strips_all_overlay_constructs():
    out = strip_overlays(FIXTURE.read_text(encoding="utf-8"))
    # commands and specs are gone
    assert r"\pause" not in out
    assert r"\only" not in out
    assert r"\uncover" not in out
    assert r"\onslide" not in out
    assert "<1->" not in out
    assert "<2>" not in out
    # content is preserved
    assert "Only on slide 2." in out
    assert "Uncovered later." in out
    assert r"\item Always shown." in out
    assert "Switched on." in out
