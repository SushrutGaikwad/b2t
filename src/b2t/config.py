from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DECK = REPO_ROOT / "files" / "reference" / "touying_reference_presentation.typ"

DEFAULT_TYPST_NAME = "main.typ"

BUILD_FILE_EXTENSIONS = (
    ".aux",
    ".log",
    ".out",
    ".fls",
    ".fdb_latexmk",
    ".nav",
    ".snm",
    ".toc",
    ".vrb",
    ".synctex.gz",
)
