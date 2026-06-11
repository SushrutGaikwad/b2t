from loguru import logger

from b2t.config import MATH_GUIDE, REFERENCE_DECK
from b2t.llm import LLMClient
from b2t.nodes._llm import run_prompt
from b2t.state import PipelineState
from b2t.typst_output import strip_code_fence


def convert_node(state: PipelineState, client: LLMClient) -> dict:
    """The single LLM call for this node: Beamer source to Typst Touying source.

    Args:
        state: Pipeline state carrying stripped_tex and llm_choices.
        client: LLM client (bound via functools.partial when the graph is built).

    Returns:
        State update with typst_source (any wrapping code fence removed), the
        node's provenance merged into llm_runs, and the rendered prompt merged
        into llm_rendered.
    """
    reference = REFERENCE_DECK.read_text(encoding="utf-8")
    guides = MATH_GUIDE.read_text(encoding="utf-8")
    logger.info("converting {} chars of LaTeX", len(state.stripped_tex))
    output, run, rendered = run_prompt(
        state,
        "convert",
        client,
        {
            "reference": reference,
            "guides": guides,
            "source": state.stripped_tex,
            "aspect_ratio": state.aspect_ratio,
        },
    )
    logger.info("conversion returned {} chars of Typst", len(output))
    return {
        "typst_source": strip_code_fence(output),
        "llm_runs": {**state.llm_runs, "convert": run},
        "llm_rendered": {**state.llm_rendered, "convert": rendered},
    }
