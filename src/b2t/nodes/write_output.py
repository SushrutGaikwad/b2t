import shutil

from b2t.config import DEFAULT_TYPST_NAME
from b2t.state import PipelineState


def write_output(state: PipelineState) -> dict:
    """Write the Typst source and copy referenced images into output_dir."""
    state.output_dir.mkdir(parents=True, exist_ok=True)
    typst_path = state.output_dir / DEFAULT_TYPST_NAME
    typst_path.write_text(state.typst_source, encoding="utf-8")
    for image in state.image_files:
        shutil.copy2(image, state.output_dir / image.name)
    return {"typst_path": typst_path}
