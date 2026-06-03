from b2t import config


def test_reference_deck_exists():
    assert config.REFERENCE_DECK.exists()


def test_default_typst_name():
    assert config.DEFAULT_TYPST_NAME == "main.typ"


def test_build_extensions_cover_beamer_outputs():
    for ext in (".aux", ".log", ".nav", ".snm", ".toc", ".vrb", ".synctex.gz"):
        assert ext in config.BUILD_FILE_EXTENSIONS
