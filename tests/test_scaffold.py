from b2t.typst_scaffold import render_date


def test_render_date_iso():
    assert render_date("2026-05-10") == "datetime(year: 2026, month: 5, day: 10)"


def test_render_date_month_day_year():
    assert render_date("May 10, 2026") == "datetime(year: 2026, month: 5, day: 10)"


def test_render_date_month_year_defaults_day_one():
    assert render_date("June 2026") == "datetime(year: 2026, month: 6, day: 1)"


def test_render_date_unparseable_falls_back_with_comment():
    out = render_date(r"\today")
    assert out.startswith("datetime.today()")
    assert "today" in out


def test_render_date_none_is_today():
    assert render_date(None) == "datetime.today()"


def test_render_date_invalid_month_falls_back():
    out = render_date("2026-13-01")
    assert out.startswith("datetime.today()")
    assert "2026-13-01" in out


def test_render_date_invalid_day_falls_back():
    out = render_date("February 31, 2026")
    assert out.startswith("datetime.today()")
    assert "February 31, 2026" in out


from b2t.state import DeckMeta, FrameUnit
from b2t.typst_scaffold import assemble, build_header


def test_build_header_fills_meta_and_aspect():
    header = build_header(DeckMeta(title="My Talk", author="Jane"), "16-9")
    assert 'aspect-ratio: "16-9"' in header
    assert "title: [My Talk]" in header
    assert "author: [Jane]" in header
    assert "#title-slide()" in header


def test_build_header_uses_placeholders_when_meta_empty():
    header = build_header(None, "4-3")
    assert "title: [Main Title of the Presentation]" in header
    assert 'aspect-ratio: "4-3"' in header


def test_assemble_inserts_each_section_once_no_toc_no_bib():
    frames = [FrameUnit(raw="", section="Intro"), FrameUnit(raw="", section="Intro")]
    converted = ["== Motivation\n\nA", "== Goals\n\nB"]
    out = assemble(DeckMeta(title="T"), "4-3", False, frames, converted, None)
    assert out.count("= Intro") == 1
    assert "== Motivation" in out and "== Goals" in out
    assert "Outline" not in out
    assert "#bibliography" not in out


def test_assemble_with_toc_and_bibliography():
    frames = [FrameUnit(raw="", section=None)]
    converted = ["== X\n\nbody"]
    out = assemble(DeckMeta(), "4-3", True, frames, converted, "references.bib")
    assert "= Outline <touying:hidden>" in out
    assert "#components.adaptive-columns(outline(title: none, indent: 1em))" in out
    assert '#bibliography("references.bib", title: none, style: "apa")' in out
    assert "Thank you!" in out
