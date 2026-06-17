from pathlib import Path

from b2t.state import DeckMeta, FrameUnit, PipelineState


def test_defaults():
    state = PipelineState(input_dir=Path("in"), output_dir=Path("out"))
    assert state.work_dir is None
    assert state.removed_build_files == []
    assert state.included_tex == []
    assert state.image_files == []
    assert state.flattened_tex is None
    assert state.compiled is False
    assert state.compile_error is None


def test_hitl_fields_default():
    s = PipelineState(input_dir=Path("in"), output_dir=Path("out"))
    assert s.hitl_enabled is False
    assert s.candidate is None
    assert s.feedback is None
    assert s.preview_path is None
    assert s.preview_pdf is None
    assert s.preview_error is None


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


def test_per_frame_fields_default():
    state = PipelineState(input_dir=Path("in"), output_dir=Path("out"))
    assert state.preamble is None
    assert state.meta is None
    assert state.has_toc is False
    assert state.bib_file is None
    assert state.frames == []
    assert state.frame_index == 0
    assert state.converted_frames == []


def test_deck_meta_and_frame_unit_construct():
    meta = DeckMeta(title="T", author="A")
    assert meta.subtitle is None
    assert meta.date_raw is None
    unit = FrameUnit(raw=r"\begin{frame}x\end{frame}", section="Intro")
    assert unit.section == "Intro"
    assert FrameUnit(raw="y").section is None
