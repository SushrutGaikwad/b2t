from b2t.latex.flatten import flatten
from b2t.latex.includes import parse_includes
from b2t.state import PipelineState


def flatten_node(state: PipelineState) -> dict:
    includes = parse_includes(state.main_tex)
    return {
        "included_tex": includes.tex,
        "image_files": includes.images,
        "flattened_tex": flatten(state.main_tex),
    }
