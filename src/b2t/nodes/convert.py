from b2t.config import MATH_GUIDE, REFERENCE_DECK
from b2t.llm import ConverterLLM
from b2t.state import PipelineState
from b2t.typst_output import strip_code_fence


def convert_node(state: PipelineState, llm: ConverterLLM) -> dict:
    """The single LLM call: Beamer source to Typst Touying source."""
    reference = REFERENCE_DECK.read_text(encoding="utf-8")
    guides = MATH_GUIDE.read_text(encoding="utf-8")
    typst_source = llm.convert(state.stripped_tex, reference, guides)
    return {"typst_source": strip_code_fence(typst_source)}
