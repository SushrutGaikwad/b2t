from typing import Protocol, runtime_checkable

from openai import OpenAI

_INSTRUCTIONS = (
    "You convert LaTeX Beamer source into a Typst Touying presentation using the "
    "university theme. Use the provided reference presentation as the canonical "
    "structure and preamble. Output only Typst source, with no commentary. Never "
    "use overlays or pause functionality."
)


@runtime_checkable
class ConverterLLM(Protocol):
    def convert(self, latex_source: str, reference: str) -> str: ...


class FakeConverter:
    """Deterministic converter for tests; never touches the network."""

    def __init__(self, output: str = "= Placeholder\n") -> None:
        self._output = output

    def convert(self, latex_source: str, reference: str) -> str:
        return self._output


class OpenAIConverter:
    """Real converter backed by the OpenAI Responses API."""

    def __init__(self, model: str = "gpt-4o") -> None:
        self._client = OpenAI()
        self._model = model

    def convert(self, latex_source: str, reference: str) -> str:
        user = (
            f"Reference Touying presentation:\n\n{reference}\n\n"
            f"Convert this Beamer source to a Typst Touying deck:\n\n{latex_source}"
        )
        response = self._client.responses.create(
            model=self._model,
            instructions=_INSTRUCTIONS,
            input=user,
        )
        return response.output_text
