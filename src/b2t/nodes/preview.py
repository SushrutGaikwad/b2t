import shutil

from loguru import logger

from b2t.state import PipelineState
from b2t.typst_images import fix_image_paths
from b2t.typst_runner import compile_typst
from b2t.typst_scaffold import assemble


def preview_node(state: PipelineState) -> dict:
    """Compile a preview of the deck so far, for human review (HITL only).

    Assembles the header, already-approved frames, and the current candidate
    (no bibliography or thank-you slide) and compiles it. Image references are
    normalized and the image files copied alongside preview.typ, the same as the
    final write_output, so a frame referencing an image compiles during review
    (write_output only runs after the whole loop). A no-op when review is
    disabled, so the library and offline paths skip the extra compile.

    Returns:
        State update with preview_path, preview_pdf, and preview_error; an empty
        dict when hitl_enabled is False.
    """
    if not state.hitl_enabled:
        return {}
    converted = [*state.converted_frames, state.candidate]
    frames = state.frames[: state.frame_index + 1]
    source = assemble(
        state.meta, state.aspect_ratio, state.has_toc, frames, converted, None
    )
    source = fix_image_paths(source, state.image_files)
    state.output_dir.mkdir(parents=True, exist_ok=True)
    for image in state.image_files:
        shutil.copy2(image, state.output_dir / image.name)
    preview_path = state.output_dir / "preview.typ"
    preview_path.write_text(source, encoding="utf-8")
    result = compile_typst(preview_path)
    logger.debug("preview frame {} ok={}", state.frame_index + 1, result.ok)
    return {
        "preview_path": preview_path,
        "preview_pdf": result.pdf_path,
        "preview_error": result.error,
    }
