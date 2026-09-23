import json
from unittest.mock import Mock

import pytest
from typer.testing import CliRunner

from link_lens import cli, store
from link_lens.ingestion import new_run
from link_lens.recovery import prepare_recovery


@pytest.fixture
def stopped():
    source = {"id": "s", "slug": "fixture"}
    snapshot = {"id": "snap"}
    store.put("sources", "s", source)
    store.put("snapshots", "snap", snapshot)
    run = new_run(source, snapshot)
    run.update(
        status="needs_review",
        version=3,
        model_calls=6,
        input_tokens=10000,
        analysis_artifact="reader",
        mapping_id="old-mapping",
        critique={"blocking_issues": ["Unsupported status"]},
        partitions_artifact=store.json_blob(
            {"partitions": {"final": list(range(300))}}
        ),
        final_cursor=100,
    )
    store.put("runs", run["id"], run)
    return run


def test_recovery_preserves_evidence_and_onboard_passes_feedback(stopped, monkeypatch):
    prior = dict(stopped, id="earlier", final_cursor=200)
    store.put("runs", "earlier", prior)
    runner = CliRunner()
    args = ["recover", stopped["id"], "--feedback", "Leave EXAD unmapped"]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 0, result.output
    new_id = json.loads(result.output)["run_id"]
    run = store.require("runs", new_id)
    assert run["supersedes_run_id"] == stopped["id"]
    assert run["final_cursor"] == 200
    for field in ("partitions_artifact", "analysis_artifact", "mapping_id", "critique"):
        assert run[field] == stopped[field]
    assert run["model_calls"] == run["version"] == run["input_tokens"] == 0
    assert store.require("runs", stopped["id"]) == stopped
    assert store.listing("approvals") == []
    assert json.loads(runner.invoke(cli.app, args).output)["run_id"] == new_id
    assert len(store.listing("runs")) == 3
    client = Mock()
    client.threads.create.return_value = {"thread_id": "replacement-thread"}
    client.runs.create.return_value = {"run_id": "server-run"}
    monkeypatch.setattr(cli, "client", lambda: client)
    result = runner.invoke(cli.app, ["onboard", new_id])
    assert result.exit_code == 0, result.output
    assert client.runs.create.call_args.kwargs["input"] == {
        "run_id": new_id,
        "feedback": "Leave EXAD unmapped",
    }


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"status": "completed"}, "Only stopped"),
        ({"status": "waiting_for_human"}, "Only stopped"),
        ({"final_validation": {"passed": False}}, "Final-test failures"),
        ({"experiment_id": "other"}, "experiment"),
        ({"model": "other"}, "model"),
        ({"final_cursor": 300}, "No unused"),
        ({"analysis_artifact": None}, "frozen reader"),
    ],
)
def test_recovery_rejects_unsafe_restarts(stopped, changes, message):
    store.put("runs", stopped["id"], {**stopped, **changes})
    with pytest.raises(ValueError, match=message):
        prepare_recovery(stopped["id"], "Correct unsupported claims")
    assert len(store.listing("runs")) == 1


def test_recovery_rejects_empty_or_changed_feedback(stopped):
    with pytest.raises(ValueError, match="non-empty"):
        prepare_recovery(stopped["id"], " ")
    prepare_recovery(stopped["id"], "Omit unsupported fields")
    with pytest.raises(ValueError, match="different feedback"):
        prepare_recovery(stopped["id"], "Different request")
