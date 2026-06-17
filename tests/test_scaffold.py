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
