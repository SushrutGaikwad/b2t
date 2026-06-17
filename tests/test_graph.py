from pathlib import Path

from b2t.graph import build_graph
from b2t.llm import FakeClient
from b2t.typst_runner import typst_available

SAMPLE_DECK = Path(__file__).parent / "fixtures" / "sample_decks" / "deck1"

VALID_TYPST = "#set page(width: 12cm, height: 6cm)\n= Hello\n\nWorld\n"


def test_pipeline_writes_output(tmp_path):
    out = tmp_path / "out"
    graph = build_graph(FakeClient(VALID_TYPST))
    result = graph.invoke({"input_dir": SAMPLE_DECK, "output_dir": out})
    final = result if isinstance(result, dict) else dict(result)
    assert (out / "main.typ").exists()
    assert (out / "logo.png").exists()
    if typst_available():
        assert final["compiled"] is True
        assert Path(final["pdf_path"]).exists()
