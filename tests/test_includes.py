import pytest
from pathlib import Path

from b2t.latex.includes import parse_includes, detect_bib_file


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


DECK1 = Path(__file__).parent / "fixtures" / "sample_decks" / "deck1"
DECK2 = Path(__file__).parent / "fixtures" / "sample_decks" / "deck2"


def test_detect_bib_file_found():
    text = (DECK2 / "main.tex").read_text(encoding="utf-8")
    bib = detect_bib_file(text, DECK2)
    assert bib is not None
    assert bib.name == "references.bib"
    assert bib.exists()


def test_detect_bib_file_absent():
    text = (DECK1 / "main.tex").read_text(encoding="utf-8")
    assert detect_bib_file(text, DECK1) is None


def test_detect_bib_file_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        detect_bib_file(r"\addbibresource{nope.bib}", tmp_path)
