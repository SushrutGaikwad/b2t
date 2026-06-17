from pathlib import Path

import pytest

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


SAMPLE_DECK = Path(__file__).parent / "fixtures" / "sample_decks" / "deck1"


def test_copy_input_copies_deck(tmp_path):
    state = _state(input_dir=SAMPLE_DECK, output_dir=tmp_path / "out")
    update = copy_input(state)
    work = update["work_dir"]
    assert work != SAMPLE_DECK
    assert (work / "main.tex").exists()


def test_clean_build_node(deck_copy):
    from conftest import FIXTURE_BUILD_FILES

    update = clean_build(_state(work_dir=deck_copy))
    assert {p.name for p in update["removed_build_files"]} == FIXTURE_BUILD_FILES


def test_detect_main_node(deck_copy):
    update = detect_main(_state(work_dir=deck_copy))
    assert update["main_tex"] == deck_copy / "main.tex"
    assert update["aspect_ratio"] == "4-3"


def test_flatten_node(deck_copy):
    update = flatten_node(_state(main_tex=deck_copy / "main.tex"))
    assert "Motivation" in update["flattened_tex"]
    assert {p.name for p in update["image_files"]} == {"logo.png"}
    assert {p.name for p in update["included_tex"]} == {"intro.tex"}


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


def test_write_output_fixes_image_extension(deck_copy, tmp_path):
    out = tmp_path / "out"
    state = _state(
        output_dir=out,
        typst_source='#image("logo")\n',
        image_files=[deck_copy / "logo.png"],
    )
    write_output(state)
    assert (out / "main.typ").read_text(encoding="utf-8") == '#image("logo.png")\n'


def test_split_deck_node(tmp_path):
    from b2t.nodes.split_deck import split_deck

    stripped = (
        "\\documentclass{beamer}\n\\title{T}\n\\date{June 2026}\n"
        "\\begin{document}\n"
        "\\begin{frame}\\titlepage\\end{frame}\n"
        "\\section{Intro}\n"
        "\\begin{frame}{Motivation}a\\end{frame}\n"
        "\\end{document}\n"
    )
    update = split_deck(_state(stripped_tex=stripped, work_dir=tmp_path))
    assert update["meta"].title == "T"
    assert update["has_toc"] is False
    assert update["bib_file"] is None
    assert [f.section for f in update["frames"]] == ["Intro"]
    assert r"\title" in update["preamble"]


def test_split_deck_node_raises_without_frames(tmp_path):
    from b2t.nodes.split_deck import split_deck

    stripped = "\\documentclass{beamer}\n\\begin{document}\n\\end{document}\n"
    with pytest.raises(ValueError):
        split_deck(_state(stripped_tex=stripped, work_dir=tmp_path))


def test_assemble_node_builds_typst_source():
    from b2t.nodes.assemble import assemble_node
    from b2t.state import DeckMeta, FrameUnit

    state = _state(
        meta=DeckMeta(title="T"),
        aspect_ratio="16-9",
        has_toc=False,
        frames=[FrameUnit(raw="", section="Intro")],
        converted_frames=["== Motivation\n\nbody"],
    )
    update = assemble_node(state)
    assert 'aspect-ratio: "16-9"' in update["typst_source"]
    assert "= Intro" in update["typst_source"]
    assert "== Motivation" in update["typst_source"]


def test_assemble_node_includes_bibliography_when_bib_present(tmp_path):
    from b2t.nodes.assemble import assemble_node
    from b2t.state import FrameUnit

    bib = tmp_path / "references.bib"
    bib.write_text("", encoding="utf-8")
    state = _state(
        frames=[FrameUnit(raw="", section=None)],
        converted_frames=["== X\n\nbody"],
        bib_file=bib,
    )
    update = assemble_node(state)
    assert '#bibliography("references.bib"' in update["typst_source"]


def test_convert_frame_sets_candidate_without_committing():
    from b2t.llm import FakeClient
    from b2t.nodes.convert_frame import convert_frame
    from b2t.state import FrameUnit

    state = _state(preamble="PRE", frames=[FrameUnit(raw="f0")], frame_index=0)
    update = convert_frame(state, client=FakeClient("== Title\n\nbody\n"))
    assert update["candidate"] == "== Title\n\nbody\n"
    assert "frame_index" not in update
    assert "converted_frames" not in update
    assert update["llm_runs"]["convert"].prompt_version == "v4"


def test_convert_frame_includes_feedback_when_present():
    from b2t.nodes.convert_frame import convert_frame
    from b2t.state import FrameUnit

    captured = {}

    class Recorder:
        def complete(self, system, user, model):
            captured["user"] = user
            return "== ok\n"

    state = _state(
        preamble="P", frames=[FrameUnit(raw="F")], frame_index=0, feedback="make it bold"
    )
    convert_frame(state, client=Recorder())
    assert "make it bold" in captured["user"]


def test_convert_frame_passes_preamble_and_frame_into_prompt():
    from b2t.nodes.convert_frame import convert_frame
    from b2t.state import FrameUnit, NodeChoice

    captured = {}

    class Recorder:
        def complete(self, system, user, model):
            captured["user"] = user
            return "== ok\n"

    state = _state(
        preamble="MYPREAMBLE",
        frames=[FrameUnit(raw="MYFRAME")],
        frame_index=0,
        llm_choices={"convert": NodeChoice(prompt_version="v3")},
    )
    convert_frame(state, client=Recorder())
    assert "MYPREAMBLE" in captured["user"]
    assert "MYFRAME" in captured["user"]


def test_preview_node_skips_when_hitl_disabled():
    from b2t.nodes.preview import preview_node
    from b2t.state import FrameUnit

    state = _state(hitl_enabled=False, frames=[FrameUnit(raw="")], candidate="== X\n\nb")
    assert preview_node(state) == {}


def test_preview_node_no_bibliography_without_bib(tmp_path):
    from b2t.nodes.preview import preview_node
    from b2t.state import DeckMeta, FrameUnit

    state = _state(
        output_dir=tmp_path / "out",
        hitl_enabled=True,
        meta=DeckMeta(title="T"),
        frames=[FrameUnit(raw="", section=None)],
        frame_index=0,
        converted_frames=[],
        candidate="== Slide\n\nbody",
        bib_file=None,
    )
    update = preview_node(state)
    assert update["preview_path"] == tmp_path / "out" / "preview.typ"
    text = (tmp_path / "out" / "preview.typ").read_text(encoding="utf-8")
    assert "== Slide" in text
    assert "#title-slide()" in text
    assert "#bibliography" not in text


def test_preview_node_includes_bibliography_when_bib_present(tmp_path):
    from b2t.nodes.preview import preview_node
    from b2t.state import DeckMeta, FrameUnit

    bib = tmp_path / "references.bib"
    bib.write_text("", encoding="utf-8")
    state = _state(
        output_dir=tmp_path / "out",
        hitl_enabled=True,
        meta=DeckMeta(title="T"),
        frames=[FrameUnit(raw="", section=None)],
        frame_index=0,
        converted_frames=[],
        candidate="== Slide\n\nbody",
        bib_file=bib,
    )
    preview_node(state)
    text = (tmp_path / "out" / "preview.typ").read_text(encoding="utf-8")
    # the bibliography must be present from the first preview so a frame with a
    # citation resolves instead of failing to compile
    assert '#bibliography("references.bib"' in text
    assert (tmp_path / "out" / "references.bib").exists()


def test_preview_node_citation_frame_compiles(tmp_path):
    from b2t.nodes.preview import preview_node
    from b2t.state import DeckMeta, FrameUnit
    from b2t.typst_runner import typst_available

    deck2 = Path(__file__).parent / "fixtures" / "sample_decks" / "deck2"
    state = _state(
        output_dir=tmp_path / "out",
        hitl_enabled=True,
        meta=DeckMeta(title="T"),
        frames=[FrameUnit(raw="", section="Intro")],
        frame_index=0,
        converted_frames=[],
        candidate="== Citations\n\nSee @hawking1975particle and @einstein1935can.",
        bib_file=deck2 / "references.bib",
    )
    update = preview_node(state)
    if typst_available():
        assert update["preview_error"] is None
        assert update["preview_pdf"] is not None


def test_preview_node_normalizes_image_paths_and_copies_images(tmp_path):
    from b2t.nodes.preview import preview_node
    from b2t.state import DeckMeta, FrameUnit

    img = tmp_path / "logo.png"
    img.write_bytes(b"not-a-real-png")
    state = _state(
        output_dir=tmp_path / "out",
        hitl_enabled=True,
        meta=DeckMeta(title="T"),
        frames=[FrameUnit(raw="", section=None)],
        frame_index=0,
        converted_frames=[],
        candidate='#figure(image("logo", width: 30%))',
        image_files=[img],
    )
    preview_node(state)
    text = (tmp_path / "out" / "preview.typ").read_text(encoding="utf-8")
    assert 'image("logo.png"' in text  # extensionless ref normalized for the preview
    assert (tmp_path / "out" / "logo.png").exists()  # image copied next to preview.typ


def test_review_node_auto_approves_when_hitl_disabled():
    from b2t.nodes.review import review_node
    from b2t.state import FrameUnit

    state = _state(
        hitl_enabled=False,
        frames=[FrameUnit(raw=""), FrameUnit(raw="")],
        frame_index=0,
        converted_frames=[],
        candidate="== X\n\nbody",
    )
    update = review_node(state)
    assert update["converted_frames"] == ["== X\n\nbody"]
    assert update["frame_index"] == 1
    assert update["candidate"] is None
    assert update["feedback"] is None
