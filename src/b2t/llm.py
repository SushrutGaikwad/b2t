import os
from typing import Protocol, runtime_checkable

from loguru import logger
from openai import OpenAI

from b2t.config import OPENROUTER_BASE_URL


@runtime_checkable
class LLMClient(Protocol):
    """Interface every model client implements; keeps LLM calls mockable."""

    def complete(self, system: str, user: str, model: str) -> str:
        """Run one completion.

        Args:
            system: The system instruction.
            user: The fully rendered user message.
            model: The model id to call.

        Returns:
            The model's text output.
        """
        ...


class FakeClient:
    """Deterministic client for tests and offline runs; never touches the network."""

    def __init__(self, output: str = "= Placeholder\n") -> None:
        """Store the canned output to return from every complete call."""
        self._output = output

    def complete(self, system: str, user: str, model: str) -> str:
        """Return the canned output, ignoring all inputs."""
        return self._output


class OpenRouterClient:
    """Open-source models via OpenRouter's OpenAI-compatible Chat Completions API.

    B2T_BASE_URL can point the same code at any OpenAI-compatible endpoint,
    e.g. a campus vLLM server. The model is chosen per call.
    """

    def __init__(self) -> None:
        """Create the client.

        Raises:
            KeyError: If OPENROUTER_API_KEY is not set in the environment.
        """
        self._client = OpenAI(
            base_url=os.getenv("B2T_BASE_URL", OPENROUTER_BASE_URL),
            api_key=os.environ["OPENROUTER_API_KEY"],
        )

    def complete(self, system: str, user: str, model: str) -> str:
        """Send one Chat Completions request.

        Args:
            system: The system instruction.
            user: The fully rendered user message.
            model: The model id to call.

        Returns:
            The model's text output. Network and provider errors propagate to
            the caller's failure boundary.
        """
        logger.info("calling {} via chat completions", model)
        response = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content
