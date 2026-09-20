import importlib.util
from pathlib import Path
from unittest.mock import Mock
import pytest
from link_lens import store
from link_lens.ingestion import new_run

spec = importlib.util.spec_from_file_location(
    "review_recovery", Path("scripts/recover_review_revisions.py")
)
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


def test_recovery_requires_revision_and_preserves_holdout_cursor(monkeypatch):
    source = {"id": "source", "slug": "fixture"}
    snapshot = {"id": "snapshot"}
    store.put("sources", "source", source)
    store.put("snapshots", "snapshot", snapshot)
    run = new_run(source, snapshot)
    run.update(
        status="budget_exhausted",
        final_cursor=100,
        partitions_artifact="frozen-partitions",
        analysis_artifact="analysis",
        mapping_id="old-config",
    )
    store.put("runs", run["id"], run)
    with pytest.raises(ValueError, match="actual user revision"):
        recovery.recover(run["id"])
    store.put(
        "approvals",
        "request",
        {
            "decision": "revision_requested",
            "feedback": "Please review supported identity semantics",
        },
        run["id"],
    )
    prior = new_run(source, snapshot)
    prior.update(status="failed", final_cursor=200)
    store.put("runs", prior["id"], prior)
    client = Mock()
    client.threads.create.return_value = {"thread_id": "new-thread"}
    monkeypatch.setattr(recovery, "get_sync_client", lambda **kwargs: client)
    result = recovery.recover(run["id"])
    assert result["final_cursor"] == 200
    assert result["partitions_artifact"] == "frozen-partitions"
    assert result["supersedes_run_id"] == run["id"]
    assert result["model_calls"] == 0
    assert recovery.recover(run["id"])["id"] == result["id"]
    assert client.runs.create.call_count == 1
    assert len(store.listing("approvals")) == 1
