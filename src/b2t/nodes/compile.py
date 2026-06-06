from b2t.state import PipelineState
from b2t.typst_runner import compile_typst


def compile_node(state: PipelineState) -> dict:
    """Compile the written main.typ; the compiler is ground truth.

    Args:
        state: Pipeline state carrying typst_path.

    Returns:
        State update with compiled, pdf_path, and compile_error. Failures are
        recorded, not raised; v0 does not yet retry.
    """
    result = compile_typst(state.typst_path)
    return {
        "compiled": result.ok,
        "pdf_path": result.pdf_path,
        "compile_error": result.error,
    }
