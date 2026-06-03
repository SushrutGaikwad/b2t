import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CompileResult:
    ok: bool
    pdf_path: Path | None
    error: str | None


def typst_available() -> bool:
    return shutil.which("typst") is not None


def compile_typst(typ_path: Path) -> CompileResult:
    """Run `typst compile <typ_path>`. Record errors; do not raise on failure."""
    pdf_path = typ_path.with_suffix(".pdf")
    proc = subprocess.run(
        ["typst", "compile", str(typ_path)],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return CompileResult(ok=True, pdf_path=pdf_path, error=None)
    return CompileResult(ok=False, pdf_path=None, error=proc.stderr.strip())
