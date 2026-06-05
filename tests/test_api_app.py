import io
import time
import zipfile
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from b2t.api.app import _safe_target, create_app
from b2t.typst_runner import typst_available

SAMPLE_DECK = Path(__file__).parent / "fixtures" / "sample_deck"
TERMINAL = {"succeeded", "compile_failed", "failed"}


def test_safe_target_allows_nested_paths(tmp_path):
    root = (tmp_path / "deck").resolve()
    assert _safe_target(root, "sub/main.tex") == root / "sub" / "main.tex"


def test_safe_target_rejects_parent_escape(tmp_path):
    root = (tmp_path / "deck").resolve()
    with pytest.raises(HTTPException):
        _safe_target(root, "../evil.txt")


def test_safe_target_rejects_sibling_prefix_escape(tmp_path):
    # root is .../deck; a sibling .../deck_evil shares the string prefix but is
    # outside root. The old startswith check let this through; is_relative_to does not.
    root = (tmp_path / "deck").resolve()
    with pytest.raises(HTTPException):
        _safe_target(root, "../deck_evil/x.txt")


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


def _run_sample(client):
    job_id = client.post("/api/jobs/sample", data={"use_fake": "true"}).json()["job_id"]
    _wait_terminal(client, job_id)
    return job_id


@pytest.mark.skipif(not typst_available(), reason="typst binary not installed")
def test_save_valid_source_recompiles():
    client = _client()
    job_id = _run_sample(client)
    res = client.post(
        f"/api/jobs/{job_id}/save", json={"source": "= Edited\n\nNew body.\n"}
    )
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert "Edited" in client.get(f"/api/jobs/{job_id}/typ").text
    assert client.get(f"/api/jobs/{job_id}").json()["status"] == "succeeded"


@pytest.mark.skipif(not typst_available(), reason="typst binary not installed")
def test_save_broken_source_reports_compile_failed():
    client = _client()
    job_id = _run_sample(client)
    res = client.post(
        f"/api/jobs/{job_id}/save", json={"source": "#this_is_not_defined()\n"}
    )
    assert res.status_code == 200
    assert res.json()["ok"] is False
    assert res.json()["error"]
    assert client.get(f"/api/jobs/{job_id}").json()["status"] == "compile_failed"


def test_save_unknown_job_returns_404():
    res = _client().post("/api/jobs/does-not-exist/save", json={"source": "= x\n"})
    assert res.status_code == 404


@pytest.mark.skipif(not typst_available(), reason="typst binary not installed")
def test_download_returns_zip_with_typ_and_pdf():
    client = _client()
    job_id = _run_sample(client)
    res = client.get(f"/api/jobs/{job_id}/download")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    names = zipfile.ZipFile(io.BytesIO(res.content)).namelist()
    assert "main.typ" in names
    assert "main.pdf" in names
    assert "logo.png" in names


def test_download_unknown_job_returns_404():
    assert _client().get("/api/jobs/does-not-exist/download").status_code == 404


def test_index_has_editor_and_buttons():
    text = _client().get("/").text
    assert 'id="typ"' in text
    assert 'id="save"' in text
    assert 'id="download"' in text
    assert "codemirror" in text.lower()
