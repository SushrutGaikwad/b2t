import sys
from pathlib import Path

from loguru import logger

from b2t.config import REPO_ROOT

DEFAULT_LOG_DIR = REPO_ROOT / "logs"


def setup_logging(log_dir: Path = DEFAULT_LOG_DIR) -> None:
    """Route loguru output to stderr (INFO) and a rotating file (DEBUG).

    Args:
        log_dir: Directory for the log file; created by loguru if missing.

    Returns:
        None. Replaces all existing sinks, so calling it again is safe.

    The file sink rotates at 10 MB and keeps 10 days of history. It writes
    through a queue (enqueue=True) so the job worker threads never block or
    interleave, and tracebacks omit variable values (diagnose=False) so
    secrets like API keys cannot leak into the logs.
    """
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(
        log_dir / "b2t.log",
        level="DEBUG",
        rotation="10 MB",
        retention="10 days",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )
