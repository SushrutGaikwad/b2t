from b2t.api.jobs import JobRecord
from b2t.api.schemas import JobView, to_view


def test_to_view_maps_fields():
    rec = JobRecord(
        id="abc",
        status="succeeded",
        current_node="compile",
        main_tex="main.tex",
        included_tex=["intro.tex"],
        images=["logo.png"],
        has_typst=True,
    )
    view = to_view(rec)
    assert view.id == "abc"
    assert view.status == "succeeded"
    assert view.current_node == "compile"
    assert view.included_tex == ["intro.tex"]
    assert view.images == ["logo.png"]
    assert view.has_typst is True
    assert view.has_pdf is False  # pdf_path is None


def test_to_view_has_pdf_false_for_missing_file(tmp_path):
    rec = JobRecord(id="x", status="succeeded", pdf_path=tmp_path / "nope.pdf")
    assert to_view(rec).has_pdf is False


def test_to_view_maps_llm_runs():
    rec = JobRecord(
        id="abc",
        status="succeeded",
        llm_runs={"convert": {"model": "m/x", "prompt_version": "v1"}},
    )
    view = to_view(rec)
    assert view.llm_runs["convert"].model == "m/x"
    assert view.llm_runs["convert"].prompt_version == "v1"


def test_job_view_excludes_rendered_prompt():
    # Rendered prompts are large; they must stay out of the per-second polled
    # JobView and be served only by the dedicated lazy prompt endpoint.
    assert "llm_rendered" not in JobView.model_fields
