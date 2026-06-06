from b2t import config


def test_reference_deck_exists():
    assert config.REFERENCE_DECK.exists()


def test_default_typst_name():
    assert config.DEFAULT_TYPST_NAME == "main.typ"


def test_build_extensions_cover_beamer_outputs():
    for ext in (".aux", ".log", ".nav", ".snm", ".toc", ".vrb", ".synctex.gz"):
        assert ext in config.BUILD_FILE_EXTENSIONS


def test_open_models_default_is_first_and_frontier():
    assert config.DEFAULT_MODEL == config.OPEN_MODELS[0].id
    assert config.OPEN_MODELS[0].strength == "frontier"


def test_open_models_ids_unique_and_namespaced():
    ids = [m.id for m in config.OPEN_MODELS]
    assert len(ids) == len(set(ids))
    assert all("/" in mid for mid in ids)


def test_open_models_have_metadata():
    for m in config.OPEN_MODELS:
        assert m.complexity and m.strength and m.reasoning


def test_open_models_include_strongest_per_family():
    ids = {m.id for m in config.OPEN_MODELS}
    for flagship in (
        "qwen/qwen3.5-397b-a17b",
        "mistralai/mistral-large-2512",
        "meta-llama/llama-4-maverick",
        "google/gemma-4-31b-it",
    ):
        assert flagship in ids


def test_model_label_composition():
    assert (
        config.OPEN_MODELS[0].label
        == "gpt-oss-120b - frontier, high reasoning, 120B MoE"
    )


def test_model_label_renders_none_as_no_reasoning():
    llama = next(
        m for m in config.OPEN_MODELS
        if m.id == "meta-llama/llama-3.3-70b-instruct"
    )
    assert llama.label == "llama-3.3-70b-instruct - strong, no reasoning, 70B dense"
