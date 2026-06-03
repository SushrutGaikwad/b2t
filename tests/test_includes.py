from b2t.latex.includes import parse_includes


def test_collects_tex_and_images_recursively(deck_copy):
    result = parse_includes(deck_copy / "main.tex")
    tex_names = {p.name for p in result.tex}
    image_names = {p.name for p in result.images}
    assert tex_names == {"intro.tex", "diagram.tex"}
    assert image_names == {"logo.png"}
