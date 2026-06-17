from loguru import logger

from b2t.config import MATH_GUIDE, REFERENCE_DECK
from b2t.llm import LLMClient
from b2t.nodes._llm import run_prompt
from b2t.state import PipelineState
from b2t.typst_output import strip_code_fence


def convert_frame(state: PipelineState, client: LLMClient) -> dict:
    """Convert one beamer frame to Typst; registered in the graph as `convert`.

    Translates frames[frame_index] into a == heading plus body, appends it to
    converted_frames, and advances frame_index. A conditional edge loops back
    until every frame is converted.

    Args:
        state: Pipeline state carrying preamble, frames, frame_index.
        client: LLM client (bound via functools.partial when the graph is built).

    Returns:
        State update with the grown converted_frames, the next frame_index, and
        merged provenance under the `convert` key.
    """
    frame = state.frames[state.frame_index]
    reference = REFERENCE_DECK.read_text(encoding="utf-8")
    guides = MATH_GUIDE.read_text(encoding="utf-8")
    logger.info("converting frame {}/{}", state.frame_index + 1, len(state.frames))
    output, run, rendered = run_prompt(
        state,
        "convert",
        client,
        {
            "reference": reference,
            "guides": guides,
            "preamble": state.preamble or "",
            "frame": frame.raw,
        },
    )
    return {
        "converted_frames": [*state.converted_frames, strip_code_fence(output)],
        "frame_index": state.frame_index + 1,
        "llm_runs": {**state.llm_runs, "convert": run},
        "llm_rendered": {**state.llm_rendered, "convert": rendered},
    }
