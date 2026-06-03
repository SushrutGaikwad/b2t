import shutil
import tempfile
from pathlib import Path

from b2t.state import PipelineState


def copy_input(state: PipelineState) -> dict:
    """Copy the read-only input into a fresh working directory."""
    work_dir = Path(tempfile.mkdtemp(prefix="b2t_")) / "deck"
    shutil.copytree(state.input_dir, work_dir)
    return {"work_dir": work_dir}
