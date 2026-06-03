from b2t.config import REFERENCE_DECK
from b2t.llm import ConverterLLM
from b2t.state import PipelineState


def convert_node(state: PipelineState, llm: ConverterLLM) -> dict:
    """The single LLM call: Beamer source to Typst Touying source."""
    reference = REFERENCE_DECK.read_text(encoding="utf-8")
    typst_source = llm.convert(state.stripped_tex, reference)
    return {"typst_source": typst_source}
