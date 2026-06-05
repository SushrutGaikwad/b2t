from b2t.api.jobs import JobRecord
from b2t.api.schemas import to_view


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
