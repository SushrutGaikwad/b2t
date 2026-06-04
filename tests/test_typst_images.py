from pathlib import Path

from b2t.typst_images import fix_image_paths


def test_adds_extension_to_bare_image_reference():
    src = '#figure(image("logo", width: 30%))\n'
    out = fix_image_paths(src, [Path("/deck/logo.png")])
    assert '#figure(image("logo.png", width: 30%))\n' == out


def test_leaves_correct_reference_unchanged():
    src = '#image("logo.png")'
    out = fix_image_paths(src, [Path("/deck/logo.png")])
    assert out == '#image("logo.png")'


def test_normalizes_subdir_reference_to_flat_filename():
    src = '#image("figures/logo")'
    out = fix_image_paths(src, [Path("/deck/figures/logo.png")])
    assert out == '#image("logo.png")'


def test_unknown_image_is_left_alone():
    src = '#image("other.png")'
    out = fix_image_paths(src, [Path("/deck/logo.png")])
    assert out == '#image("other.png")'
