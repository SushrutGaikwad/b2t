from b2t.latex.overlays import strip_overlays
from b2t.state import PipelineState


def strip_overlays_node(state: PipelineState) -> dict:
    return {"stripped_tex": strip_overlays(state.flattened_tex)}
