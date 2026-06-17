import pytest

from b2t.latex.split import parse_meta, split_preamble

PREAMBLE = r"""\documentclass{beamer}
\title{A Minimal Sample Deck}
\subtitle{For Testing}
\author{Jane Doe}
\institute{Department of Examples}
\date{June 2026}
"""

DOC = PREAMBLE + r"""\begin{document}
\begin{frame}\titlepage\end{frame}
\section{Introduction}
\begin{frame}{Motivation}Body one\end{frame}
\end{document}"""


def test_split_preamble_divides_at_begin_document():
    pre, body = split_preamble(DOC)
    assert r"\title{A Minimal Sample Deck}" in pre
    assert r"\begin{document}" not in pre
    assert r"\begin{frame}{Motivation}" in body
    assert r"\title{" not in body


def test_split_preamble_missing_document_raises():
    with pytest.raises(ValueError):
        split_preamble(r"\documentclass{beamer}")


def test_parse_meta_reads_all_fields():
    meta = parse_meta(PREAMBLE)
    assert meta.title == "A Minimal Sample Deck"
    assert meta.subtitle == "For Testing"
    assert meta.author == "Jane Doe"
    assert meta.institute == "Department of Examples"
    assert meta.date_raw == "June 2026"


def test_parse_meta_missing_fields_are_none():
    meta = parse_meta(r"\documentclass{beamer}")
    assert meta.title is None
    assert meta.author is None
