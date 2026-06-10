"""Shared helper that every LLM node uses to run its prompt."""

import os

from b2t import prompts
from b2t.config import DEFAULT_MODEL
from b2t.llm import LLMClient
from b2t.state import NodeChoice, NodeRun, PipelineState


def run_prompt(
    state: PipelineState,
    node_name: str,
    client: LLMClient,
    values: dict[str, str],
) -> tuple[str, NodeRun]:
    """Resolve the node's selection, render its prompt, and call the client.

    Args:
        state: Pipeline state carrying llm_choices.
        node_name: The graph node name, also the prompt registry key.
        client: The LLM client to call.
        values: Token values for the user-message template.

    Returns:
        The model output and a NodeRun recording the model and version used.
        The model falls back to B2T_MODEL then DEFAULT_MODEL; the version falls
        back to the registry default.
    """
    choice = state.llm_choices.get(node_name) or NodeChoice()
    model = choice.model or os.getenv("B2T_MODEL") or DEFAULT_MODEL
    version = choice.prompt_version or prompts.default_version(node_name)
    pv = prompts.load(node_name, version)
    user = prompts.render(pv.user_template, values)
    output = client.complete(pv.system, user, model)
    return output, NodeRun(model=model, prompt_version=version)
