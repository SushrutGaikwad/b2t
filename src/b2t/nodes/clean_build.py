from b2t.latex.cleanup import remove_build_files
from b2t.state import PipelineState


def clean_build(state: PipelineState) -> dict:
    return {"removed_build_files": remove_build_files(state.work_dir)}
