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
