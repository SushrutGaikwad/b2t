from pathlib import Path

from b2t.graph import build_graph
from b2t.llm import FakeClient
from b2t.typst_runner import typst_available

DECK1 = Path(__file__).parent / "fixtures" / "sample_decks" / "deck1"
DECK2 = Path(__file__).parent / "fixtures" / "sample_decks" / "deck2"
DECK3 = Path(__file__).parent / "fixtures" / "sample_decks" / "deck3"

FRAME_BODY = "== Slide\n\nbody\n"


def test_pipeline_assembles_per_frame_deck(tmp_path):
    out = tmp_path / "out"
    graph = build_graph(FakeClient(FRAME_BODY))
    result = dict(graph.invoke({"input_dir": DECK1, "output_dir": out}))
    typ = (out / "main.typ").read_text(encoding="utf-8")
    assert "#title-slide()" in typ              # deterministic header
    assert "= Introduction" in typ              # section heading inserted once
    assert typ.count("== Slide") == 4           # deck1 has four content frames
    assert (out / "logo.png").exists()
    if typst_available():
        assert result["compiled"] is True
        assert Path(result["pdf_path"]).exists()


def test_pipeline_appends_bibliography_for_bib_deck(tmp_path):
    out = tmp_path / "out"
    graph = build_graph(FakeClient(FRAME_BODY))
    result = dict(graph.invoke({"input_dir": DECK2, "output_dir": out}))
    typ = (out / "main.typ").read_text(encoding="utf-8")
    assert '#bibliography("references.bib", title: none, style: "apa")' in typ
    assert "Thank you!" in typ
    assert (out / "references.bib").exists()
    # the \printbibliography frame must not be converted as a content frame
    assert "printbibliography" not in typ


def test_hitl_graph_pauses_then_approves_all(tmp_path):
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import Command

    graph = build_graph(FakeClient(FRAME_BODY), checkpointer=InMemorySaver())
    cfg = {"configurable": {"thread_id": "t1"}}
    seed = {"input_dir": DECK1, "output_dir": tmp_path / "out", "hitl_enabled": True}
    chunks = list(graph.stream(seed, config=cfg, stream_mode=["updates"]))
    interrupts = [
        chunk["__interrupt__"][0].value for mode, chunk in chunks if "__interrupt__" in chunk
    ]
    assert interrupts and interrupts[0]["frame_index"] == 0
    assert interrupts[0]["total"] == 4
    for _ in range(4):
        list(graph.stream(Command(resume={"action": "approve"}), config=cfg, stream_mode=["updates"]))
    final = graph.get_state(cfg).values
    assert final["typst_source"].count("== Slide") == 4


def test_hitl_graph_regenerate_reconverts_with_feedback(tmp_path):
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import Command

    calls = []

    class Recorder:
        def complete(self, system, user, model):
            calls.append(user)
            return FRAME_BODY

    graph = build_graph(Recorder(), checkpointer=InMemorySaver())
    cfg = {"configurable": {"thread_id": "t2"}}
    seed = {"input_dir": DECK1, "output_dir": tmp_path / "out", "hitl_enabled": True}
    list(graph.stream(seed, config=cfg, stream_mode=["updates"]))
    n_before = len(calls)
    list(graph.stream(
        Command(resume={"action": "regenerate", "feedback": "make it bold"}),
        config=cfg, stream_mode=["updates"],
    ))
    assert len(calls) == n_before + 1          # convert re-ran the same frame
    assert "make it bold" in calls[-1]         # feedback reached the prompt


def test_pipeline_renders_appendix_after_bibliography(tmp_path):
    out = tmp_path / "out"
    graph = build_graph(FakeClient(FRAME_BODY))
    result = dict(graph.invoke({"input_dir": DECK3, "output_dir": out}))
    typ = (out / "main.typ").read_text(encoding="utf-8")
    # the backup frame is now an appendix, rendered after the bibliography
    assert "#show: appendix" in typ
    assert typ.index("#bibliography") < typ.index("#show: appendix")
    assert "= Appendix <touying:hidden>" in typ
    # exactly one frame title is hidden: the single appendix (backup) frame
    assert typ.count("== Slide <touying:hidden>") == 1
    assert (out / "references.bib").exists()
    if typst_available():
        assert result["compiled"] is True
        assert Path(result["pdf_path"]).exists()
