from b2t.api.jobs import JobStore, PIPELINE_NODES


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
