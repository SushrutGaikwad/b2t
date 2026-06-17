from loguru import logger

from b2t.config import MATH_GUIDE, REFERENCE_DECK
from b2t.llm import LLMClient
from b2t.nodes._llm import run_prompt
from b2t.state import PipelineState
from b2t.typst_output import strip_code_fence


def _feedback_block(feedback: str | None) -> str:
    """Frame reviewer feedback for the prompt, or empty when there is none."""
    if not feedback:
        return ""
    return (
        "\nThe reviewer reviewed a previous attempt at this frame and asked for "
        f"these changes; address them:\n{feedback}\n"
    )


def convert_frame(state: PipelineState, client: LLMClient) -> dict:
    """Produce a candidate Typst conversion for the current frame.

    Does not commit or advance; the review node does that on approval. Uses
    state.feedback to steer a regeneration. Registered in the graph as `convert`.

    Args:
        state: Pipeline state carrying preamble, frames, frame_index, feedback.
        client: LLM client (bound via functools.partial when the graph is built).

    Returns:
        State update with candidate plus merged provenance under the `convert`
        key.
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
            "feedback": _feedback_block(state.feedback),
            "frame": frame.raw,
        },
    )
    return {
        "candidate": strip_code_fence(output),
        "llm_runs": {**state.llm_runs, "convert": run},
        "llm_rendered": {**state.llm_rendered, "convert": rendered},
    }
