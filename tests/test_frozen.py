from link_lens import store
from link_lens.frozen import freeze, thaw


def test_frozen_roundtrip_preserves_pending_decisions(tmp_path):
    artifact = store.blob(b"public source evidence", "text/plain", "evidence.txt")
    store.put(
        "runs",
        "test-run",
        {"id": "test-run", "status": "waiting_for_human", "artifact": artifact},
    )
    archive = tmp_path / "frozen.zip"
    freeze(archive)
    assert thaw(archive)["restored"] == 2
    assert store.require("runs", "test-run")["status"] == "waiting_for_human"
    assert not store.listing("approvals")
