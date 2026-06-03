from functools import partial

from langgraph.graph import END, START, StateGraph

from b2t.llm import ConverterLLM
from b2t.nodes.clean_build import clean_build
from b2t.nodes.compile import compile_node
from b2t.nodes.convert import convert_node
from b2t.nodes.copy_input import copy_input
from b2t.nodes.detect_main import detect_main
from b2t.nodes.flatten import flatten_node
from b2t.nodes.strip_overlays import strip_overlays_node
from b2t.nodes.write_output import write_output
from b2t.state import PipelineState


def build_graph(llm: ConverterLLM):
    """Build and compile the linear v0 conversion graph."""
    graph = StateGraph(PipelineState)

    graph.add_node("copy_input", copy_input)
    graph.add_node("clean_build", clean_build)
    graph.add_node("detect_main", detect_main)
    graph.add_node("flatten", flatten_node)
    graph.add_node("strip_overlays", strip_overlays_node)
    graph.add_node("convert", partial(convert_node, llm=llm))
    graph.add_node("write_output", write_output)
    graph.add_node("compile", compile_node)

    graph.add_edge(START, "copy_input")
    graph.add_edge("copy_input", "clean_build")
    graph.add_edge("clean_build", "detect_main")
    graph.add_edge("detect_main", "flatten")
    graph.add_edge("flatten", "strip_overlays")
    graph.add_edge("strip_overlays", "convert")
    graph.add_edge("convert", "write_output")
    graph.add_edge("write_output", "compile")
    graph.add_edge("compile", END)

    return graph.compile()
