from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DECK = REPO_ROOT / "files" / "reference" / "touying_reference_presentation.typ"
MATH_GUIDE = REPO_ROOT / "files" / "md" / "guides" / "math_equations_in_typst.md"

DEFAULT_TYPST_NAME = "main.typ"

DEFAULT_OPENAI_MODEL = "gpt-5.4-nano"

OPENAI_MODELS = (
    "gpt-5.4-nano",
    "gpt-5.4-mini",
    "gpt-5.4",
    "gpt-5.4-pro",
    "gpt-5.5",
)

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
