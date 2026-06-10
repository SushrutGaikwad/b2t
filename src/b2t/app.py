from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from b2t.graph import build_graph
from b2t.llm import LLMClient, OpenRouterClient
from b2t.log import setup_logging


def convert_deck(
    input_dir: str | Path,
    output_dir: str | Path,
    client: LLMClient | None = None,
    llm_choices: dict | None = None,
) -> dict:
    """Convert a Beamer deck directory into a compiled Typst Touying deck.

    Args:
        input_dir: Directory holding the compiled Beamer deck (read-only).
        output_dir: Directory to write main.typ, images, and the PDF into.
        client: LLM client to use; defaults to OpenRouterClient.
        llm_choices: Optional per-node {model, prompt_version} selection.

    Returns:
        The final pipeline state as a dict.
    """
    load_dotenv()
    setup_logging()
    client = client or OpenRouterClient()
    graph = build_graph(client)
    logger.info("converting {} -> {}", input_dir, output_dir)
    result = graph.invoke(
        {
            "input_dir": Path(input_dir),
            "output_dir": Path(output_dir),
            "llm_choices": llm_choices or {},
        }
    )
    if result.get("compiled"):
        logger.info("compiled {}", result.get("pdf_path"))
    else:
        logger.error("compile failed: {}", result.get("compile_error"))
    return result
