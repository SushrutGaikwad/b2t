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
    # core latex / pdflatex auxiliary
    ".aux",
    ".lof",
    ".log",
    ".lot",
    ".fls",
    ".out",
    ".toc",
    ".fmt",
    ".fot",
    ".cb",
    ".cb2",
    # intermediate documents
    ".dvi",
    ".xdv",
    # bibliography
    ".bbl",
    ".bcf",
    ".blg",
    ".run.xml",
    # build tools
    ".fdb_latexmk",
    ".synctex",
    ".synctex.gz",
    ".pdfsync",
    # beamer and package
    ".nav",
    ".snm",
    ".vrb",
    ".pre",
    ".soc",
    ".loa",
    ".thm",
    ".cpt",
    ".spl",
    ".lox",
    # makeindex
    ".idx",
    ".ilg",
    ".ind",
    ".ist",
    # glossaries
    ".acn",
    ".acr",
    ".glg",
    ".glo",
    ".gls",
    ".glsdefs",
    ".slg",
    ".slo",
    ".sls",
    # xindy
    ".xdy",
)
