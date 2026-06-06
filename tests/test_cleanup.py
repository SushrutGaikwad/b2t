from conftest import FIXTURE_BUILD_FILES

from b2t.latex.cleanup import list_build_files, remove_build_files


def test_lists_only_build_files(deck_copy):
    names = {p.name for p in list_build_files(deck_copy)}
    assert names == FIXTURE_BUILD_FILES


def test_remove_deletes_build_files_and_keeps_sources(deck_copy):
    removed = remove_build_files(deck_copy)
    assert {p.name for p in removed} == FIXTURE_BUILD_FILES
    assert not (deck_copy / "main.aux").exists()
    assert (deck_copy / "main.tex").exists()
    assert (deck_copy / "intro.tex").exists()
    assert (deck_copy / "logo.png").exists()
    # the compiled deck is input content, not a build file to delete
    assert (deck_copy / "main.pdf").exists()
