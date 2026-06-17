"""Deterministic assembly of the Typst Touying deck from converted frames."""

import re

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
