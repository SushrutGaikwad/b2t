from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from b2t.graph import build_graph
from b2t.llm import ConverterLLM, OpenRouterConverter
from b2t.log import setup_logging


def convert_deck(
    input_dir: str | Path,
    output_dir: str | Path,
    llm: ConverterLLM | None = None,
) -> dict:
    """Convert a Beamer deck directory into a compiled Typst Touying deck.

    Args:
        input_dir: Directory holding the compiled Beamer deck (read-only).
        output_dir: Directory to write main.typ, images, and the PDF into.
        llm: Converter to use; defaults to OpenRouterConverter.

    Returns:
        The final pipeline state as a dict (typst_path, compiled, pdf_path,
        compile_error, and the intermediate discoveries).
    """
    load_dotenv()
    setup_logging()
    converter = llm or OpenRouterConverter()
    graph = build_graph(converter)
    logger.info("converting {} -> {}", input_dir, output_dir)
    result = graph.invoke(
        {"input_dir": Path(input_dir), "output_dir": Path(output_dir)}
    )
    if result.get("compiled"):
        logger.info("compiled {}", result.get("pdf_path"))
    else:
        logger.error("compile failed: {}", result.get("compile_error"))
    return result
