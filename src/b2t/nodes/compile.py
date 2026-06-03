from b2t.state import PipelineState
from b2t.typst_runner import compile_typst


def compile_node(state: PipelineState) -> dict:
    result = compile_typst(state.typst_path)
    return {
        "compiled": result.ok,
        "pdf_path": result.pdf_path,
        "compile_error": result.error,
    }
