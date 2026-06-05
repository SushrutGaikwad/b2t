import pytest

from b2t.latex.includes import parse_includes


def test_collects_tex_and_images_recursively(deck_copy):
    result = parse_includes(deck_copy / "main.tex")
    tex_names = {p.name for p in result.tex}
    image_names = {p.name for p in result.images}
    assert tex_names == {"intro.tex"}
    assert image_names == {"logo.png"}


def test_missing_included_tex_raises(tmp_path):
    main = tmp_path / "main.tex"
    main.write_text(r"\input{missing}", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        parse_includes(main)


def test_missing_image_raises(tmp_path):
    main = tmp_path / "main.tex"
    main.write_text(r"\includegraphics{nope}", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        parse_includes(main)
