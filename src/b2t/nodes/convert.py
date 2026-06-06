from loguru import logger

from b2t.config import MATH_GUIDE, REFERENCE_DECK
from b2t.llm import ConverterLLM
from b2t.state import PipelineState
from b2t.typst_output import strip_code_fence


def convert_node(state: PipelineState, llm: ConverterLLM) -> dict:
    """The single LLM call: Beamer source to Typst Touying source.

    Args:
        state: Pipeline state carrying stripped_tex.
        llm: Converter used for the translation (bound via functools.partial
            when the graph is built).

    Returns:
        State update with typst_source, with any wrapping code fence removed.
    """
    reference = REFERENCE_DECK.read_text(encoding="utf-8")
    guides = MATH_GUIDE.read_text(encoding="utf-8")
    logger.info("converting {} chars of LaTeX", len(state.stripped_tex))
    typst_source = llm.convert(state.stripped_tex, reference, guides)
    logger.info("conversion returned {} chars of Typst", len(typst_source))
    return {"typst_source": strip_code_fence(typst_source)}
