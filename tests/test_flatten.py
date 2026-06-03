import pytest

from b2t.latex.flatten import flatten


def test_expands_inputs_into_one_source(deck_copy):
    merged = flatten(deck_copy / "main.tex")
    assert "Motivation" in merged          # from intro.tex
    assert "tikzpicture" in merged         # from diagram.tex
    assert r"\input{" not in merged        # inputs are gone


def test_missing_include_fails_loudly(tmp_path):
    main = tmp_path / "main.tex"
    main.write_text(r"\input{missing}", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        flatten(main)
