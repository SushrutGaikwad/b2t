from pathlib import Path

from b2t.api.jobs import JobStore, PIPELINE_NODES, run_job
from b2t.api.state_view import NodeDelta
from b2t.llm import FakeClient
from b2t.typst_runner import typst_available

SAMPLE_DECK = Path(__file__).parent / "fixtures" / "sample_deck"


def test_run_job_reaches_terminal(tmp_path):
    store = JobStore()
    out = tmp_path / "out"
    job = store.create(input_dir=SAMPLE_DECK, output_dir=out)
    run_job(store, job.id, SAMPLE_DECK, out, lambda: FakeClient("= Hi\n"))
    rec = store.get(job.id)
    assert rec.status in {"succeeded", "compile_failed", "failed"}
    assert rec.main_tex == "main.tex"
    assert rec.images == ["logo.png"]
    assert rec.has_typst is True
    assert rec.typst_path is not None
    if typst_available():
        assert rec.status == "succeeded"
        assert rec.pdf_path is not None


def test_run_job_records_deterministic_failure(tmp_path):
    deck = tmp_path / "deck"
    deck.mkdir()
    (deck / "notes.tex").write_text("just notes", encoding="utf-8")
    store = JobStore()
    job = store.create(input_dir=deck, output_dir=tmp_path / "out")
    run_job(store, job.id, deck, tmp_path / "out", lambda: FakeClient("= Hi\n"))
    rec = store.get(job.id)
    assert rec.status == "failed"
    assert "beamer main" in rec.error


def test_create_and_get():
    store = JobStore()
    job = store.create(status="queued")
    assert store.get(job.id) is job
    assert store.get("missing") is None


def test_update_mutates_record():
    store = JobStore()
    job = store.create()
    store.update(job.id, status="running", current_node="flatten")
    rec = store.get(job.id)
    assert rec.status == "running"
    assert rec.current_node == "flatten"


def test_pipeline_nodes_are_the_eight_in_order():
    assert PIPELINE_NODES == (
        "copy_input",
        "clean_build",
        "detect_main",
        "flatten",
        "strip_overlays",
        "convert",
        "write_output",
        "compile",
    )


def test_current_node_tracks_the_running_node(tmp_path):
    # current_node must name the node that is RUNNING, not the last finished one.
    store = JobStore()
    job = store.create(input_dir=SAMPLE_DECK, output_dir=tmp_path / "out")
    captured = {}

    class SpyClient:
        def complete(self, system, user, model):
            captured["during_convert"] = store.get(job.id).current_node
            return "= Hi\n"

    run_job(store, job.id, SAMPLE_DECK, tmp_path / "out", lambda: SpyClient())
    assert captured["during_convert"] == "convert"


def test_run_job_records_llm_runs(tmp_path):
    from b2t.config import DEFAULT_MODEL

    store = JobStore()
    out = tmp_path / "out"
    job = store.create(input_dir=SAMPLE_DECK, output_dir=out)
    run_job(store, job.id, SAMPLE_DECK, out, lambda: FakeClient("= Hi\n"))
    rec = store.get(job.id)
    assert rec.llm_runs["convert"] == {
        "model": DEFAULT_MODEL,
        "prompt_version": "v1",
    }


def test_run_job_records_rendered_prompt(tmp_path):
    store = JobStore()
    out = tmp_path / "out"
    job = store.create(input_dir=SAMPLE_DECK, output_dir=out)
    run_job(store, job.id, SAMPLE_DECK, out, lambda: FakeClient("= Hi\n"))
    rec = store.get(job.id)
    assert "convert" in rec.llm_rendered
    assert "Reference Touying presentation" in rec.llm_rendered["convert"]["user"]
    assert rec.llm_rendered["convert"]["system"]


def test_append_delta_accumulates_node_deltas():
    store = JobStore()
    job = store.create()
    store.append_delta(job.id, NodeDelta("copy_input", ["work_dir"], {"work_dir": "/w"}))
    store.append_delta(
        job.id, NodeDelta("detect_main", ["main_tex"], {"main_tex": "main.tex"})
    )
    rec = store.get(job.id)
    assert [d.node for d in rec.node_deltas] == ["copy_input", "detect_main"]
    assert rec.seed_state == {}
