from pathlib import Path

from b2t.graph import build_graph
from b2t.llm import FakeClient
from b2t.typst_runner import typst_available

DECK1 = Path(__file__).parent / "fixtures" / "sample_decks" / "deck1"
DECK2 = Path(__file__).parent / "fixtures" / "sample_decks" / "deck2"

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
