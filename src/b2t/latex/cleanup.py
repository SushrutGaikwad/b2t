from pathlib import Path

from b2t.config import BUILD_FILE_EXTENSIONS


def list_build_files(directory: Path) -> list[Path]:
    """Return build files under directory matching known extensions.

    Matches on full filename so double extensions like .synctex.gz are caught.

    Args:
        directory: Directory tree to scan recursively.

    Returns:
        Sorted paths of every file whose name ends in a BUILD_FILE_EXTENSIONS
        entry. Nothing is deleted.
    """
    return sorted(
        p
        for p in directory.rglob("*")
        if p.is_file() and any(p.name.endswith(ext) for ext in BUILD_FILE_EXTENSIONS)
    )


def remove_build_files(directory: Path) -> list[Path]:
    """Delete build files under directory.

    Args:
        directory: Directory tree to clean recursively.

    Returns:
        The paths that were deleted, sorted.
    """
    removed = list_build_files(directory)
    for path in removed:
        path.unlink()
    return removed
