from functools import partial

from langgraph.graph import END, START, StateGraph

from b2t.llm import LLMClient
from b2t.nodes.assemble import assemble_node
from b2t.nodes.clean_build import clean_build
from b2t.nodes.compile import compile_node
from b2t.nodes.convert_frame import convert_frame
from b2t.nodes.copy_input import copy_input
from b2t.nodes.detect_main import detect_main
from b2t.nodes.flatten import flatten_node
from b2t.nodes.split_deck import split_deck
from b2t.nodes.strip_overlays import strip_overlays_node
from b2t.nodes.write_output import write_output
from b2t.state import PipelineState


def _more_frames(state: PipelineState) -> str:
    """Loop back to convert while frames remain, else move on to assemble."""
    return "convert" if state.frame_index < len(state.frames) else "assemble"


def build_graph(client: LLMClient):
    """Build and compile the per-frame conversion graph.

    Args:
        client: LLM client bound into the convert node; every other node is
            deterministic.

    Returns:
        A compiled LangGraph runnable: copy_input -> clean_build -> detect_main
        -> flatten -> strip_overlays -> split_deck -> convert (self-loop over
        frames) -> assemble -> write_output -> compile.
    """
    graph = StateGraph(PipelineState)

    graph.add_node("copy_input", copy_input)
    graph.add_node("clean_build", clean_build)
    graph.add_node("detect_main", detect_main)
    graph.add_node("flatten", flatten_node)
    graph.add_node("strip_overlays", strip_overlays_node)
    graph.add_node("split_deck", split_deck)
    graph.add_node("convert", partial(convert_frame, client=client))
    graph.add_node("assemble", assemble_node)
    graph.add_node("write_output", write_output)
    graph.add_node("compile", compile_node)

    graph.add_edge(START, "copy_input")
    graph.add_edge("copy_input", "clean_build")
    graph.add_edge("clean_build", "detect_main")
    graph.add_edge("detect_main", "flatten")
    graph.add_edge("flatten", "strip_overlays")
    graph.add_edge("strip_overlays", "split_deck")
    graph.add_edge("split_deck", "convert")
    graph.add_conditional_edges(
        "convert", _more_frames, {"convert": "convert", "assemble": "assemble"}
    )
    graph.add_edge("assemble", "write_output")
    graph.add_edge("write_output", "compile")
    graph.add_edge("compile", END)

    return graph.compile()
