from pathlib import Path

from b2t.state import PipelineState


def test_defaults():
    state = PipelineState(input_dir=Path("in"), output_dir=Path("out"))
    assert state.work_dir is None
    assert state.removed_build_files == []
    assert state.included_tex == []
    assert state.image_files == []
    assert state.flattened_tex is None
    assert state.compiled is False
    assert state.compile_error is None


def test_partial_update_roundtrip():
    state = PipelineState(input_dir=Path("in"), output_dir=Path("out"))
    updated = state.model_copy(update={"main_tex": Path("in/main.tex")})
    assert updated.main_tex == Path("in/main.tex")


def test_llm_choices_and_runs_default_empty():
    state = PipelineState(input_dir=Path("in"), output_dir=Path("out"))
    assert state.llm_choices == {}
    assert state.llm_runs == {}


def test_llm_choices_coerce_nested_dicts():
    state = PipelineState(
        input_dir=Path("in"),
        output_dir=Path("out"),
        llm_choices={"convert": {"model": "m", "prompt_version": "v2"}},
    )
    assert state.llm_choices["convert"].model == "m"
    assert state.llm_choices["convert"].prompt_version == "v2"


def test_llm_runs_coerce_nested_dicts():
    state = PipelineState(
        input_dir=Path("in"),
        output_dir=Path("out"),
        llm_runs={"convert": {"model": "m", "prompt_version": "v1"}},
    )
    assert state.llm_runs["convert"].model == "m"
    assert state.llm_runs["convert"].prompt_version == "v1"


def test_llm_rendered_defaults_empty():
    state = PipelineState(input_dir=Path("in"), output_dir=Path("out"))
    assert state.llm_rendered == {}


def test_llm_rendered_coerces_nested_dicts():
    state = PipelineState(
        input_dir=Path("in"),
        output_dir=Path("out"),
        llm_rendered={"convert": {"system": "S", "user": "U"}},
    )
    assert state.llm_rendered["convert"].system == "S"
    assert state.llm_rendered["convert"].user == "U"
