import os
from typing import Protocol, runtime_checkable

from loguru import logger
from openai import OpenAI

from b2t.config import DEFAULT_MODEL, OPENROUTER_BASE_URL

_INSTRUCTIONS = (
    "You convert LaTeX Beamer source into a Typst Touying presentation using the "
    "university theme. Use the provided reference presentation as the canonical "
    "structure and preamble. Follow the provided guides, especially for writing "
    "math equations in Typst syntax. Output only Typst source, with no commentary. "
    "Never use overlays or pause functionality."
)


@runtime_checkable
class ConverterLLM(Protocol):
    """Interface every converter implements; keeps LLM calls mockable."""

    def convert(self, latex_source: str, reference: str, guides: str = "") -> str:
        """Translate Beamer LaTeX into Typst Touying source.

        Args:
            latex_source: Flattened, overlay-free Beamer source.
            reference: The canonical Touying reference presentation.
            guides: Optional extra guidance (e.g. the Typst math guide).

        Returns:
            Typst source for the converted deck.
        """
        ...


class FakeConverter:
    """Deterministic converter for tests and offline runs; never touches the network."""

    def __init__(self, output: str = "= Placeholder\n") -> None:
        """Store the canned Typst source to return from every convert call."""
        self._output = output

    def convert(self, latex_source: str, reference: str, guides: str = "") -> str:
        """Return the canned output, ignoring all inputs."""
        return self._output


class OpenRouterConverter:
    """Open-source models via OpenRouter's OpenAI-compatible Chat Completions API.

    B2T_BASE_URL can point the same code at any OpenAI-compatible endpoint,
    e.g. a campus vLLM server.
    """

    def __init__(self, model: str | None = None) -> None:
        """Create the client and resolve the model.

        Args:
            model: Model id to use; falls back to the B2T_MODEL env var, then
                the catalog default.

        Raises:
            KeyError: If OPENROUTER_API_KEY is not set in the environment.
        """
        self._client = OpenAI(
            base_url=os.getenv("B2T_BASE_URL", OPENROUTER_BASE_URL),
            api_key=os.environ["OPENROUTER_API_KEY"],
        )
        self._model = model or os.getenv("B2T_MODEL", DEFAULT_MODEL)

    def convert(self, latex_source: str, reference: str, guides: str = "") -> str:
        """Send one Chat Completions request translating the deck.

        Args:
            latex_source: Flattened, overlay-free Beamer source.
            reference: The canonical Touying reference presentation.
            guides: Optional extra guidance appended to the prompt.

        Returns:
            The model's Typst source. Network and provider errors propagate
            to the caller's failure boundary.
        """
        parts = [f"Reference Touying presentation:\n\n{reference}"]
        if guides:
            parts.append(f"Guides:\n\n{guides}")
        parts.append(f"Convert this Beamer source to a Typst Touying deck:\n\n{latex_source}")
        logger.info("calling {} via chat completions", self._model)
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _INSTRUCTIONS},
                {"role": "user", "content": "\n\n".join(parts)},
            ],
        )
        return response.choices[0].message.content
