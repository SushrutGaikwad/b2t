"""Deterministic assembly of the Typst Touying deck from converted frames."""

import re

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


def render_date(date_raw: str | None) -> str:
    """Return a Typst date expression for a raw beamer \\date argument.

    Tries YYYY-MM-DD, 'Month DD, YYYY', and 'Month YYYY' (day defaults to 1).
    Anything else (including \\today or free text) falls back to
    datetime.today(), keeping the original text in a trailing comment.
    """
    if date_raw:
        text = date_raw.strip()
        iso = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
        if iso:
            y, m, d = (int(g) for g in iso.groups())
            return f"datetime(year: {y}, month: {m}, day: {d})"
        mdy = re.fullmatch(r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", text)
        if mdy and mdy.group(1).lower() in _MONTHS:
            return (
                f"datetime(year: {int(mdy.group(3))}, "
                f"month: {_MONTHS[mdy.group(1).lower()]}, day: {int(mdy.group(2))})"
            )
        my = re.fullmatch(r"([A-Za-z]+)\s+(\d{4})", text)
        if my and my.group(1).lower() in _MONTHS:
            return (
                f"datetime(year: {int(my.group(2))}, "
                f"month: {_MONTHS[my.group(1).lower()]}, day: 1)"
            )
        return f"datetime.today()  // original date: {text}"
    return "datetime.today()"


_HEADER_TEMPLATE = '''#import "@preview/touying:0.7.3": *
#import themes.university: *

#import "@preview/theorion:0.6.0": *
#import cosmos.fancy: *
#show: show-theorion

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
    """Return the References section, bibliography call, and thank-you slide."""
    return (
        "\n= References\n\n"
        "== References <touying:hidden>\n\n"
        f'#bibliography("{bib_name}", title: none, style: "apa")\n\n'
        "#slide(config: (\n"
        "  page: (header: none, footer: none),\n"
        "))[\n"
        "  #set align(center + horizon)\n"
        "  #text(size: 2.5em)[Thank you!]\n"
        "]\n"
    )


def _body(frames: list[FrameUnit], converted: list[str]) -> str:
    """Interleave = Section headings (on change) with converted frame bodies."""
    parts: list[str] = []
    prev_section: str | None = None
    for unit, typ in zip(frames, converted):
        if unit.section is not None and unit.section != prev_section:
            parts.append(f"= {unit.section}")
        prev_section = unit.section
        parts.append(typ.strip())
    return "\n\n".join(parts)


def assemble(
    meta: DeckMeta | None,
    aspect_ratio: str,
    has_toc: bool,
    frames: list[FrameUnit],
    converted: list[str],
    bib_name: str | None,
) -> str:
    """Assemble the full Typst deck from the scaffold and converted frames."""
    out = build_header(meta, aspect_ratio)
    if has_toc:
        out += _OUTLINE
    out += "\n" + _body(frames, converted) + "\n"
    if bib_name:
        out += _bibliography_block(bib_name)
    return out
