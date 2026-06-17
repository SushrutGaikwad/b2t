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


def test_parse_meta_handles_optional_short_argument():
    meta = parse_meta("\\title[Short]{The Long Title}\n\\author[JD]{Jane Doe}")
    assert meta.title == "The Long Title"
    assert meta.author == "Jane Doe"


from b2t.latex.split import split_frames

BODY = r"""
\begin{frame}\titlepage\end{frame}
\section{Introduction}
\begin{frame}{Motivation}One\end{frame}
\begin{frame}{Goals}Two\end{frame}
\section{Methods}
\begin{frame}{Approach}Three\end{frame}
"""


def test_split_frames_tags_sections_and_excludes_titlepage():
    frames, has_toc = split_frames(BODY)
    assert has_toc is False
    assert len(frames) == 3
    assert [f.section for f in frames] == ["Introduction", "Introduction", "Methods"]
    assert all(r"\titlepage" not in f.raw for f in frames)
    assert frames[0].raw == r"\begin{frame}{Motivation}One\end{frame}"


def test_split_frames_detects_toc_and_excludes_it():
    body = r"\begin{frame}\tableofcontents\end{frame}\begin{frame}{X}a\end{frame}"
    frames, has_toc = split_frames(body)
    assert has_toc is True
    assert len(frames) == 1
    assert frames[0].section is None


def test_split_frames_excludes_printbibliography_frame():
    body = r"\begin{frame}{Body}a\end{frame}" \
           r"\begin{frame}[allowframebreaks]{References}\printbibliography\end{frame}"
    frames, has_toc = split_frames(body)
    assert len(frames) == 1
    assert frames[0].raw == r"\begin{frame}{Body}a\end{frame}"


def test_split_frames_unmatched_begin_raises():
    with pytest.raises(ValueError):
        split_frames(r"\begin{frame}{X}a")


def test_split_frames_frame_shorthand_raises():
    # \frame{...} shorthand must fail loud, not silently drop its content
    with pytest.raises(ValueError):
        split_frames(r"\frame{Hello}\begin{frame}{X}a\end{frame}")


def test_split_frames_frametitle_is_not_shorthand():
    # \frametitle{...} inside a normal frame must not trip the shorthand guard
    frames, _ = split_frames(r"\begin{frame}\frametitle{T}body\end{frame}")
    assert len(frames) == 1


def test_split_frames_empty_section_is_none():
    frames, _ = split_frames(r"\section{}\begin{frame}{X}a\end{frame}")
    assert frames[0].section is None
