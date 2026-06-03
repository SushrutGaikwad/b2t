from pathlib import Path

from b2t.nodes.clean_build import clean_build
from b2t.nodes.copy_input import copy_input
from b2t.nodes.detect_main import detect_main
from b2t.nodes.flatten import flatten_node
from b2t.nodes.strip_overlays import strip_overlays_node
from b2t.nodes.write_output import write_output
from b2t.state import PipelineState


def _state(**kwargs) -> PipelineState:
    base = {"input_dir": Path("in"), "output_dir": Path("out")}
    base.update(kwargs)
    return PipelineState(**base)


SAMPLE_DECK = Path(__file__).parent / "fixtures" / "sample_deck"


def test_copy_input_copies_deck(tmp_path):
    state = _state(input_dir=SAMPLE_DECK, output_dir=tmp_path / "out")
    update = copy_input(state)
    work = update["work_dir"]
    assert work != SAMPLE_DECK
    assert (work / "main.tex").exists()


def test_clean_build_node(deck_copy):
    update = clean_build(_state(work_dir=deck_copy))
    assert {p.name for p in update["removed_build_files"]} == {
        "main.aux",
        "main.log",
        "main.nav",
    }


def test_detect_main_node(deck_copy):
    update = detect_main(_state(work_dir=deck_copy))
    assert update["main_tex"] == deck_copy / "main.tex"


def test_flatten_node(deck_copy):
    update = flatten_node(_state(main_tex=deck_copy / "main.tex"))
    assert "Motivation" in update["flattened_tex"]
    assert {p.name for p in update["image_files"]} == {"logo.png"}
    assert {p.name for p in update["included_tex"]} == {"intro.tex", "diagram.tex"}


def test_strip_overlays_node():
    update = strip_overlays_node(_state(flattened_tex=r"a \pause b"))
    assert update["stripped_tex"] == "a  b"


def test_write_output_node(deck_copy, tmp_path):
    out = tmp_path / "out"
    state = _state(
        output_dir=out,
        typst_source="= Hi\n",
        image_files=[deck_copy / "logo.png"],
    )
    update = write_output(state)
    assert update["typst_path"] == out / "main.typ"
    assert (out / "main.typ").read_text(encoding="utf-8") == "= Hi\n"
    assert (out / "logo.png").exists()


def test_convert_node_uses_injected_llm():
    from b2t.llm import FakeConverter
    from b2t.nodes.convert import convert_node

    state = _state(stripped_tex="\\section{X}")
    update = convert_node(state, llm=FakeConverter("= Converted\n"))
    assert update["typst_source"] == "= Converted\n"
