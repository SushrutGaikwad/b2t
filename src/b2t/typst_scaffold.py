"""Deterministic assembly of the Typst Touying deck from converted frames."""

import re
from datetime import date

from b2t.state import DeckMeta, FrameUnit

_MONTHS = {
    name: i
    for i, name in enumerate(
        [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
        ],
        start=1,
    )
}


def _typst_datetime(year: int, month: int, day: int) -> str | None:
    """Return a Typst datetime(...) for a real calendar date, else None.

    Guards against shape-valid but out-of-range dates (month 13, Feb 31) so the
    scaffold never emits Typst that fails to compile.
    """
    try:
        date(year, month, day)
    except ValueError:
        return None
    return f"datetime(year: {year}, month: {month}, day: {day})"


def render_date(date_raw: str | None) -> str:
    """Return a Typst date expression for a raw beamer \\date argument.

    Tries YYYY-MM-DD, 'Month DD, YYYY', and 'Month YYYY' (day defaults to 1),
    validating each as a real calendar date. Anything else (including \\today,
    free text, or an out-of-range date) falls back to datetime.today(), keeping
    the original text in a trailing comment.
    """
    if date_raw:
        text = date_raw.strip()
        iso = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
        if iso:
            expr = _typst_datetime(*(int(g) for g in iso.groups()))
            if expr:
                return expr
        mdy = re.fullmatch(r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", text)
        if mdy and mdy.group(1).lower() in _MONTHS:
            expr = _typst_datetime(
                int(mdy.group(3)), _MONTHS[mdy.group(1).lower()], int(mdy.group(2))
            )
            if expr:
                return expr
        my = re.fullmatch(r"([A-Za-z]+)\s+(\d{4})", text)
        if my and my.group(1).lower() in _MONTHS:
            return (
                f"datetime(year: {int(my.group(2))}, "
                f"month: {_MONTHS[my.group(1).lower()]}, day: 1)"
            )
        return f"datetime.today()  // original date: {text}"
    return "datetime.today()"


_HEADER_TEMPLATE = '''#import "@preview/touying:0.7.4": *
#import themes.university: *

#import "@preview/theorion:0.6.0": *
#import cosmos.fancy: *
#show: show-theorion

// Generic Beamer-style block
#let block-frame(
  title,
  body,
  border: blue.darken(30%),
  fill: blue.lighten(95%),
  symbol: none,
) = fancy-box(
  get-border-color: loc => border,
  get-body-color: loc => fill,
  get-symbol: loc => symbol,
  full-title: title,
  body,
)

#show: university-theme.with(
  align: horizon,
  aspect-ratio: "__ASPECT__",
  config-common(frozen-counters: (theorem-counter,), slide-level: 2),
  config-info(
    title: [__TITLE__],
    subtitle: [__SUBTITLE__],
    author: [__AUTHOR__],
    date: __DATE__,
    institution: [__INSTITUTION__],
  ),
)

// Comment out the following for heading numbering (like Beamer section numbers)
// #import "@preview/numbly:0.1.0": numbly
// #set heading(numbering: numbly("{1}.", default: "1.1"))

// Fonts (using New Computer Modern to avoid the Fira font warning)
#set text(
  // font: "New Computer Modern",  // comment out for default font
  weight: "light",
  size: 20pt,
  lang: "en",
  region: "US"
)

#title-slide()
'''

_OUTLINE = '''
= Outline <touying:hidden>

== Outline <touying:hidden>

#components.adaptive-columns(outline(title: none, indent: 1em))
'''


def build_header(meta: DeckMeta | None, aspect_ratio: str) -> str:
    """Build the deck header (imports, theme, config-info, title slide).

    Absent metadata fields fall back to the reference deck's placeholders, and
    the date is rendered by render_date.
    """
    m = meta or DeckMeta()
    return (
        _HEADER_TEMPLATE
        .replace("__ASPECT__", aspect_ratio)
        .replace("__TITLE__", m.title or "Main Title of the Presentation")
        .replace("__SUBTITLE__", m.subtitle or "Subtitle of the Presentation")
        .replace("__AUTHOR__", m.author or "Author's Name")
        .replace("__DATE__", render_date(m.date_raw))
        .replace("__INSTITUTION__", m.institute or "Institute's Name")
    )


def _bibliography_block(bib_name: str) -> str:
    """Return the References section and bibliography call.

    No closing slide is added. A thank-you slide appears only when the source
    deck has its own, converted as a normal frame.
    """
    return (
        "\n= References\n\n"
        "== References <touying:hidden>\n\n"
        f'#bibliography("{bib_name}", title: none, style: "apa")\n'
    )


def _hide_frame_title(typ: str) -> str:
    """Append <touying:hidden> to the first level-2 (==) heading line.

    Used for appendix frames, whose slide titles stay out of the table of
    contents. A higher-level (===) heading and an already-hidden title are left
    untouched, and a body with no == heading is returned unchanged.
    """
    lines = typ.split("\n")
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("==") and not stripped.startswith("==="):
            if "<touying:hidden>" not in line:
                lines[i] = line.rstrip() + " <touying:hidden>"
            return "\n".join(lines)
    return typ


def _section_heading(section: str, hidden: bool) -> str:
    """Return a = Section heading, hidden from the outline when hidden is True."""
    return f"= {section} <touying:hidden>" if hidden else f"= {section}"


def _body(pairs: list[tuple[FrameUnit, str]]) -> str:
    """Interleave = Section headings (on change) with converted frame bodies.

    A heading that came from a starred \\section* is hidden from the outline.
    """
    parts: list[str] = []
    prev_section: str | None = None
    for unit, typ in pairs:
        if unit.section is not None and unit.section != prev_section:
            parts.append(_section_heading(unit.section, unit.section_starred))
        prev_section = unit.section
        parts.append(typ.strip())
    return "\n\n".join(parts)


def _appendix_block(pairs: list[tuple[FrameUnit, str]]) -> str:
    """Render the appendix: #show: appendix then hidden-heading backup frames.

    Appendix section headings and frame titles are hidden from the outline. A
    single = Appendix wrapper is synthesized when the source gives no section.
    """
    parts: list[str] = ["#show: appendix"]
    prev_section: str | None = None
    emitted_section = False
    for unit, typ in pairs:
        if unit.section is not None and unit.section != prev_section:
            parts.append(_section_heading(unit.section, True))
            emitted_section = True
        elif unit.section is None and not emitted_section:
            # Synthesize one wrapper only when the appendix has no section of
            # its own; a real section heading above also sets emitted_section.
            parts.append("= Appendix <touying:hidden>")
            emitted_section = True
        prev_section = unit.section
        parts.append(_hide_frame_title(typ.strip()))
    return "\n" + "\n\n".join(parts) + "\n"


def assemble(
    meta: DeckMeta | None,
    aspect_ratio: str,
    has_toc: bool,
    frames: list[FrameUnit],
    converted: list[str],
    bib_name: str | None,
) -> str:
    """Assemble the full Typst deck from the scaffold and converted frames.

    Frames after \\appendix render after the bibliography, introduced by
    #show: appendix, with their section and frame headings hidden from the
    table of contents.
    """
    pairs = list(zip(frames, converted))
    body_pairs = [p for p in pairs if not p[0].is_appendix]
    appendix_pairs = [p for p in pairs if p[0].is_appendix]
    out = build_header(meta, aspect_ratio)
    if has_toc:
        out += _OUTLINE
    out += "\n" + _body(body_pairs) + "\n"
    if bib_name:
        out += _bibliography_block(bib_name)
    if appendix_pairs:
        out += _appendix_block(appendix_pairs)
    return out
