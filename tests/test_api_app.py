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


@pytest.mark.skipif(not typst_available(), reason="typst binary not installed")
def test_download_excludes_stale_pdf_after_failed_save():
    client = _client()
    job_id = _run_sample(client)  # sample compiles, so main.pdf exists
    res = client.post(f"/api/jobs/{job_id}/save", json={"source": "#nope_undefined()\n"})
    assert res.json()["ok"] is False
    names = zipfile.ZipFile(
        io.BytesIO(client.get(f"/api/jobs/{job_id}/download").content)
    ).namelist()
    assert "main.typ" in names
    assert "main.pdf" not in names


def test_index_has_editor_and_buttons():
    text = _client().get("/").text
    assert 'id="typ"' in text
    assert 'id="save"' in text
    assert 'id="download"' in text
    assert "codemirror" in text.lower()


def test_models_endpoint_lists_open_models_with_labels():
    from b2t.config import DEFAULT_MODEL, OPEN_MODELS

    body = _client().get("/api/models").json()
    assert body["default"] == DEFAULT_MODEL
    assert [m["id"] for m in body["models"]] == [m.id for m in OPEN_MODELS]
    assert [m["label"] for m in body["models"]] == [m.label for m in OPEN_MODELS]
    assert body["default"] in {m["id"] for m in body["models"]}


def test_graph_endpoint_returns_structured_topology():
    body = _client().get("/api/graph").json()
    names = [n["name"] for n in body["nodes"]]
    assert "copy_input" in names and "convert" in names and "compile" in names
    assert "__start__" not in names and "__end__" not in names
    convert = next(n for n in body["nodes"] if n["name"] == "convert")
    assert convert["is_llm"] is True
    copy = next(n for n in body["nodes"] if n["name"] == "copy_input")
    assert copy["is_llm"] is False
    assert body["edges"]


def test_index_has_graph_container():
    text = _client().get("/").text
    assert '<div id="graph"' in text
    assert "mermaid" not in text.lower()


def test_make_client_picks_fake_or_openrouter(monkeypatch):
    from b2t.api.app import _make_client
    from b2t.llm import FakeClient, OpenRouterClient

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    assert isinstance(_make_client(True), FakeClient)
    assert isinstance(_make_client(False), OpenRouterClient)


def test_real_job_without_key_records_failed(monkeypatch):
    client = _client()  # create_app loads .env, so clear the key afterwards
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    res = client.post("/api/jobs/sample", data={"use_fake": "false"})
    assert res.status_code == 200
    body = _wait_terminal(client, res.json()["job_id"])
    assert body["status"] == "failed"
    assert "OPENROUTER_API_KEY" in body["error"]


def test_llm_nodes_endpoint_lists_convert_with_versions():
    body = _client().get("/api/llm-nodes").json()
    convert = next(n for n in body["nodes"] if n["node"] == "convert")
    assert convert["default_version"] == "v1"
    assert "v1" in [v["id"] for v in convert["versions"]]
    assert all(v["label"] for v in convert["versions"])


def test_choices_validation_rejects_unknown_node():
    client = _client()
    res = client.post(
        "/api/jobs/sample",
        data={"use_fake": "true", "choices": '{"nope": {"prompt_version": "v1"}}'},
    )
    assert res.status_code == 400


def test_choices_validation_rejects_unknown_version():
    client = _client()
    res = client.post(
        "/api/jobs/sample",
        data={"use_fake": "true", "choices": '{"convert": {"prompt_version": "v999"}}'},
    )
    assert res.status_code == 400


def test_choices_validation_on_upload_rejects_unknown_node():
    client = _client()
    res = client.post(
        "/api/jobs",
        data={"use_fake": "true", "choices": '{"nope": {"prompt_version": "v1"}}'},
        files=_sample_files(),
    )
    assert res.status_code == 400


def test_sample_job_with_valid_choices_runs_and_reports_provenance():
    client = _client()
    res = client.post(
        "/api/jobs/sample",
        data={"use_fake": "true", "choices": '{"convert": {"prompt_version": "v1"}}'},
    )
    assert res.status_code == 200
    body = _wait_terminal(client, res.json()["job_id"])
    assert body["llm_runs"]["convert"]["prompt_version"] == "v1"


def test_index_has_llm_nodes_container():
    text = _client().get("/").text
    assert '<div id="llm-nodes"' in text
    assert '<select id="model"' not in text


def test_prompt_content_endpoint_returns_template():
    body = _client().get("/api/prompts/convert/v1").json()
    assert body["node"] == "convert"
    assert body["version"] == "v1"
    assert "You convert LaTeX Beamer" in body["system"]
    assert "{{source}}" in body["user_template"]


def test_prompt_content_unknown_node_returns_404():
    assert _client().get("/api/prompts/nope/v1").status_code == 404


def test_prompt_content_unknown_version_returns_404():
    assert _client().get("/api/prompts/convert/v999").status_code == 404


def test_rendered_prompt_available_after_run():
    client = _client()
    job_id = _run_sample(client)
    body = client.get(f"/api/jobs/{job_id}/prompt/convert").json()
    assert body["prompt_version"] == "v1"
    assert "You convert LaTeX Beamer" in body["system"]
    assert "Reference Touying presentation" in body["user"]


def test_rendered_prompt_unknown_job_returns_404():
    assert _client().get("/api/jobs/does-not-exist/prompt/convert").status_code == 404


def test_rendered_prompt_unknown_node_after_run_returns_404():
    client = _client()
    job_id = _run_sample(client)
    assert client.get(f"/api/jobs/{job_id}/prompt/nope").status_code == 404


def test_node_state_available_after_run():
    client = _client()
    job_id = _run_sample(client)
    body = client.get(f"/api/jobs/{job_id}/state/convert").json()
    assert body["node"] == "convert"
    assert "typst_source" in body["changed"]
    assert "stripped_tex" in body["state"]
    assert "typst_source" in body["state"]


def test_jobview_lists_state_nodes_after_run():
    client = _client()
    job_id = _run_sample(client)
    body = client.get(f"/api/jobs/{job_id}").json()
    assert "convert" in body["state_nodes"]
    assert "copy_input" in body["state_nodes"]


def test_node_state_unknown_job_returns_404():
    assert _client().get("/api/jobs/does-not-exist/state/convert").status_code == 404


def test_node_state_unknown_node_returns_404():
    client = _client()
    job_id = _run_sample(client)
    assert client.get(f"/api/jobs/{job_id}/state/nope").status_code == 404


def test_index_has_state_inspector_container():
    text = _client().get("/").text
    assert '<div id="state-inspector"' in text


def test_index_loads_codemirror_json_mode():
    # CodeMirror 5 has no separate json mode; the javascript mode covers JSON
    # (used with json: true), so the inspector loads mode/javascript.
    text = _client().get("/").text
    assert "mode/javascript" in text
