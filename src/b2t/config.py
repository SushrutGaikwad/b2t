"""Static configuration: paths, the model catalog, and cleanup extensions."""

from pathlib import Path

from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DECK = REPO_ROOT / "files" / "reference" / "touying_reference_presentation.typ"
MATH_GUIDE = REPO_ROOT / "files" / "md" / "guides" / "math_equations_in_typst.md"

DEFAULT_TYPST_NAME = "main.typ"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class ModelInfo(BaseModel):
    """One open-source model in the conversion catalog.

    Attributes:
        id: OpenRouter model id (author/slug).
        complexity: Parameter size and architecture, e.g. "120B MoE".
        strength: Capability tier: frontier | strong | capable | basic.
        reasoning: Reasoning level: high | hybrid | medium | none.
    """

    id: str
    complexity: str
    strength: str
    reasoning: str

    @property
    def label(self) -> str:
        """Dropdown label: '<short-name> - <strength>, <reasoning> reasoning, <complexity>'."""
        short = self.id.split("/", 1)[1]
        reasoning = "no" if self.reasoning == "none" else self.reasoning
        return f"{short} - {self.strength}, {reasoning} reasoning, {self.complexity}"


# Open-source models, strongest first: the strongest open-weight flagship of
# each family, then the sizes US universities most commonly self-host. IDs
# verified against the live OpenRouter API on 2026-06-06.
OPEN_MODELS = (
    ModelInfo(id="openai/gpt-oss-120b", complexity="120B MoE", strength="frontier", reasoning="high"),
    ModelInfo(id="qwen/qwen3.5-397b-a17b", complexity="397B MoE", strength="frontier", reasoning="high"),
    ModelInfo(id="mistralai/mistral-large-2512", complexity="675B MoE", strength="frontier", reasoning="none"),
    ModelInfo(id="meta-llama/llama-4-maverick", complexity="400B MoE", strength="strong", reasoning="none"),
    ModelInfo(id="google/gemma-4-31b-it", complexity="31B dense", strength="strong", reasoning="high"),
    ModelInfo(id="qwen/qwen3-32b", complexity="32B dense", strength="strong", reasoning="hybrid"),
    ModelInfo(id="meta-llama/llama-3.3-70b-instruct", complexity="70B dense", strength="strong", reasoning="none"),
    ModelInfo(id="meta-llama/llama-4-scout", complexity="109B MoE", strength="strong", reasoning="none"),
    ModelInfo(id="google/gemma-4-26b-a4b-it", complexity="26B MoE", strength="capable", reasoning="none"),
    ModelInfo(id="mistralai/mistral-small-2603", complexity="24B dense", strength="capable", reasoning="none"),
    ModelInfo(id="openai/gpt-oss-20b", complexity="21B MoE", strength="capable", reasoning="medium"),
    ModelInfo(id="meta-llama/llama-3.1-8b-instruct", complexity="8B dense", strength="basic", reasoning="none"),
)

DEFAULT_MODEL = OPEN_MODELS[0].id

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
