from b2t.latex.detect import find_main_tex
from b2t.state import PipelineState


def detect_main(state: PipelineState) -> dict:
    return {"main_tex": find_main_tex(state.work_dir)}
