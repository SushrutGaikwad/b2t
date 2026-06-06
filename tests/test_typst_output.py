from b2t.typst_output import strip_code_fence

DECK = "= Title\n\nSome body text.\n"


def test_strips_fence_with_typst_tag():
    assert strip_code_fence(f"```typst\n{DECK}```") == DECK


def test_strips_fence_with_typ_tag():
    assert strip_code_fence(f"```typ\n{DECK}```") == DECK


def test_strips_bare_fence():
    assert strip_code_fence(f"```\n{DECK}```") == DECK


def test_strips_fence_with_surrounding_whitespace():
    assert strip_code_fence(f"\n```typst\n{DECK}```\n\n") == DECK


def test_unfenced_source_is_unchanged():
    assert strip_code_fence(DECK) == DECK


def test_internal_raw_block_is_kept():
    source = '= Title\n\n```\nverbatim text\n```\n'
    assert strip_code_fence(source) == source


def test_opening_fence_without_closing_is_kept():
    source = "```typst\n= Title\n\nNo closing fence here.\n"
    assert strip_code_fence(source) == source
