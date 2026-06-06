from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from b2t.graph import build_graph
from b2t.llm import ConverterLLM, OpenRouterConverter


def convert_deck(
    input_dir: str | Path,
    output_dir: str | Path,
    llm: ConverterLLM | None = None,
) -> dict:
    """Convert a Beamer deck directory into a compiled Typst Touying deck."""
    load_dotenv()
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
