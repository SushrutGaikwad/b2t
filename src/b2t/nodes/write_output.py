import shutil

from loguru import logger

from b2t.config import DEFAULT_TYPST_NAME
from b2t.state import PipelineState
from b2t.typst_images import fix_image_paths


def write_output(state: PipelineState) -> dict:
    """Write the Typst source and copy referenced images into output_dir.

    Images are copied flat, so image() references are normalized to the copied
    filenames (with extension) to match.

    Args:
        state: Pipeline state carrying output_dir, typst_source, image_files.

    Returns:
        State update with typst_path (the written main.typ) and the
        normalized typst_source.
    """
    state.output_dir.mkdir(parents=True, exist_ok=True)
    typst_source = fix_image_paths(state.typst_source, state.image_files)
    typst_path = state.output_dir / DEFAULT_TYPST_NAME
    typst_path.write_text(typst_source, encoding="utf-8")
    for image in state.image_files:
        shutil.copy2(image, state.output_dir / image.name)
    logger.debug("wrote {} and {} images", typst_path, len(state.image_files))
    return {"typst_path": typst_path, "typst_source": typst_source}
