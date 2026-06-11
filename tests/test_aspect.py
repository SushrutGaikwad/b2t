import pytest

from b2t.latex.aspect import aspect_ratio


def test_default_when_no_option():
    assert aspect_ratio(r"\documentclass{beamer}") == "4-3"


@pytest.mark.parametrize(
    "code,expected",
    [
        ("43", "4-3"),
        ("169", "16-9"),
        ("1610", "16-10"),
        ("149", "14-9"),
        ("141", "141-100"),
        ("54", "5-4"),
        ("32", "3-2"),
    ],
)
def test_known_codes(code, expected):
    assert aspect_ratio(rf"\documentclass[aspectratio={code}]{{beamer}}") == expected


def test_found_among_other_options():
    src = r"\documentclass[xcolor=dvipsnames,aspectratio=169,t]{beamer}"
    assert aspect_ratio(src) == "16-9"


def test_spaces_around_equals():
    assert aspect_ratio(r"\documentclass[aspectratio = 32]{beamer}") == "3-2"


def test_unknown_code_falls_back_to_default():
    assert aspect_ratio(r"\documentclass[aspectratio=999]{beamer}") == "4-3"
