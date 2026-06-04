from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DECK = REPO_ROOT / "files" / "reference" / "touying_reference_presentation.typ"
MATH_GUIDE = REPO_ROOT / "files" / "md" / "guides" / "math_equations_in_typst.md"

DEFAULT_TYPST_NAME = "main.typ"

DEFAULT_OPENAI_MODEL = "gpt-5.4-nano"

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
