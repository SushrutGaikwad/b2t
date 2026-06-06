import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from loguru import logger


@dataclass
class CompileResult:
    """Outcome of one `typst compile` run.

    Attributes:
        ok: True if compilation succeeded.
        pdf_path: Path to the produced PDF, or None on failure.
        error: Compiler stderr (or a missing-CLI message), or None on success.
    """

    ok: bool
    pdf_path: Path | None
    error: str | None


def typst_available() -> bool:
    """Return True if the `typst` CLI is on PATH."""
    return shutil.which("typst") is not None


def compile_typst(typ_path: Path) -> CompileResult:
    """Run `typst compile` on a .typ file. Record errors; do not raise.

    Args:
        typ_path: Path to the Typst source file to compile.

    Returns:
        A CompileResult: ok with the PDF path, or not ok with the compiler's
        stderr. A missing typst CLI is reported as a clear error instead of
        an unhandled FileNotFoundError.
    """
    pdf_path = typ_path.with_suffix(".pdf")
    logger.debug("compiling {}", typ_path)
    try:
        proc = subprocess.run(
            ["typst", "compile", str(typ_path)],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        message = "typst CLI not found; install Typst 0.14+ and ensure it is on PATH"
        logger.error(message)
        return CompileResult(ok=False, pdf_path=None, error=message)
    if proc.returncode == 0:
        logger.debug("compiled {}", pdf_path)
        return CompileResult(ok=True, pdf_path=pdf_path, error=None)
    logger.warning("typst compile failed for {}", typ_path)
    return CompileResult(ok=False, pdf_path=None, error=proc.stderr.strip())
