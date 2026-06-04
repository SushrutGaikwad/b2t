import os
from typing import Protocol, runtime_checkable

from openai import OpenAI

from b2t.config import DEFAULT_OPENAI_MODEL

_INSTRUCTIONS = (
    "You convert LaTeX Beamer source into a Typst Touying presentation using the "
    "university theme. Use the provided reference presentation as the canonical "
    "structure and preamble. Follow the provided guides, especially for writing "
    "math equations in Typst syntax. Output only Typst source, with no commentary. "
    "Never use overlays or pause functionality."
)


@runtime_checkable
class ConverterLLM(Protocol):
    def convert(self, latex_source: str, reference: str, guides: str = "") -> str: ...


class FakeConverter:
    """Deterministic converter for tests; never touches the network."""

    def __init__(self, output: str = "= Placeholder\n") -> None:
        self._output = output

    def convert(self, latex_source: str, reference: str, guides: str = "") -> str:
        return self._output


class OpenAIConverter:
    """Real converter backed by the OpenAI Responses API."""

    def __init__(self, model: str | None = None) -> None:
        self._client = OpenAI()
        self._model = model or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    def convert(self, latex_source: str, reference: str, guides: str = "") -> str:
        parts = [f"Reference Touying presentation:\n\n{reference}"]
        if guides:
            parts.append(f"Guides:\n\n{guides}")
        parts.append(f"Convert this Beamer source to a Typst Touying deck:\n\n{latex_source}")
        user = "\n\n".join(parts)
        response = self._client.responses.create(
            model=self._model,
            instructions=_INSTRUCTIONS,
            input=user,
        )
        return response.output_text
