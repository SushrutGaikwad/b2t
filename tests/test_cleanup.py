from b2t.latex.cleanup import list_build_files, remove_build_files


def test_lists_only_build_files(deck_copy):
    names = {p.name for p in list_build_files(deck_copy)}
    assert names == {"main.aux", "main.log", "main.nav"}


def test_remove_deletes_build_files_and_keeps_sources(deck_copy):
    removed = remove_build_files(deck_copy)
    assert {p.name for p in removed} == {"main.aux", "main.log", "main.nav"}
    assert not (deck_copy / "main.aux").exists()
    assert (deck_copy / "main.tex").exists()
    assert (deck_copy / "intro.tex").exists()
    assert (deck_copy / "logo.png").exists()
