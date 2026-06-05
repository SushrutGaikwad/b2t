import time
from pathlib import Path

from fastapi.testclient import TestClient

from b2t.api.app import create_app
from b2t.typst_runner import typst_available

SAMPLE_DECK = Path(__file__).parent / "fixtures" / "sample_deck"
TERMINAL = {"succeeded", "compile_failed", "failed"}


def _client():
    return TestClient(create_app())


def _wait_terminal(client, job_id, timeout=30.0):
    deadline = time.monotonic() + timeout
    body = None
    while time.monotonic() < deadline:
        body = client.get(f"/api/jobs/{job_id}").json()
        if body["status"] in TERMINAL:
            return body
        time.sleep(0.1)
    raise AssertionError(f"job did not finish: {body}")


def _sample_files():
    files = []
    for path in sorted(SAMPLE_DECK.rglob("*")):
        if path.is_file():
            rel = "sample_deck/" + str(path.relative_to(SAMPLE_DECK)).replace("\\", "/")
            files.append(("files", (rel, path.read_bytes(), "application/octet-stream")))
    return files


def test_unknown_job_returns_404():
    assert _client().get("/api/jobs/does-not-exist").status_code == 404


def test_sample_job_runs_and_exposes_typ():
    client = _client()
    res = client.post("/api/jobs/sample", data={"use_fake": "true"})
    assert res.status_code == 200
    job_id = res.json()["job_id"]
    body = _wait_terminal(client, job_id)
    assert body["status"] in TERMINAL
    assert body["main_tex"] == "main.tex"
    typ = client.get(f"/api/jobs/{job_id}/typ")
    assert typ.status_code == 200
    assert "Sample" in typ.text
    if typst_available():
        assert body["status"] == "succeeded"
        assert body["has_pdf"] is True
        assert client.get(f"/api/jobs/{job_id}/pdf").status_code == 200


def test_folder_upload_reconstructs_and_runs():
    client = _client()
    res = client.post("/api/jobs", data={"use_fake": "true"}, files=_sample_files())
    assert res.status_code == 200
    body = _wait_terminal(client, res.json()["job_id"])
    assert body["status"] in TERMINAL
    assert body["images"] == ["logo.png"]
    assert "intro.tex" in body["included_tex"]


def test_broken_deck_reports_failed():
    client = _client()
    files = [("files", ("deck/notes.tex", b"just notes", "text/plain"))]
    res = client.post("/api/jobs", data={"use_fake": "true"}, files=files)
    body = _wait_terminal(client, res.json()["job_id"])
    assert body["status"] == "failed"
    assert "beamer main" in body["error"]


def test_empty_upload_is_rejected():
    # no files part: rejected without creating a job (400 from our guard, or
    # 422 if FastAPI rejects the missing multipart first)
    code = _client().post("/api/jobs", data={"use_fake": "true"}).status_code
    assert code in (400, 422)


def test_serves_index_at_root():
    res = _client().get("/")
    assert res.status_code == 200
    assert 'id="app"' in res.text
