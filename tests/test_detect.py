import pytest

from b2t.latex.detect import find_main_tex


def test_finds_the_beamer_main(deck_copy):
    assert find_main_tex(deck_copy) == deck_copy / "main.tex"


def test_raises_when_no_main(tmp_path):
    (tmp_path / "notes.tex").write_text("just notes", encoding="utf-8")
    with pytest.raises(ValueError):
        find_main_tex(tmp_path)
