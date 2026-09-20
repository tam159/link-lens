import pytest
import json
from typer.testing import CliRunner
from link_lens.cli import app
from link_lens import store, evaluation
from link_lens.agent import record_approval, extract_node
from link_lens.ingestion import new_run
from link_lens.contracts import content_hash


def test_approval_exact_hash_and_idempotent():
    run = {"id": "run"}
    mapping = {"id": "mapping", "config_hash": "abc"}
    with pytest.raises(ValueError):
        record_approval(
            run, mapping, [{"type": "accept", "args": {"config_hash": "wrong"}}]
        )
    response = [
        {
            "type": "accept",
            "args": {"config_hash": "abc", "untrusted_edited_config": "ignored"},
        }
    ]
    assert record_approval(run, mapping, response) == record_approval(
        run, mapping, response
    )
    assert len(store.listing("approvals")) == 1
    with pytest.raises(ValueError):
        record_approval(run, mapping, [{"type": "edit", "args": {}}])


def test_reject_prevents_extraction(spec, snapshot):
    store.put("sources", "source-a", {"id": "source-a"})
    store.put("snapshots", "snapshot", snapshot)
    run = new_run({"id": "source-a", "slug": "example"}, snapshot)
    mapping = {
        "id": "mapping",
        "config_hash": content_hash(spec),
        "config": spec.model_dump(),
    }
    store.put("mappings", "mapping", mapping)
    approval = record_approval(run, mapping, [{"type": "ignore"}])
    run.update(mapping_id="mapping", approval_id=approval["id"])
    store.put("runs", run["id"], run)
    extract_node({"run_id": run["id"]})
    assert store.require("runs", run["id"])["status"] == "failed"
    assert not store.listing("observations")


def test_unknown_labels_are_never_correct():
    store.put(
        "batches",
        "discovery",
        {"shortlist": [{"dataset_id": str(i)} for i in range(50)]},
    )
    sheet = evaluation.worksheet("triage")
    assert sheet == evaluation.worksheet("triage")
    report = evaluation.report(sheet["id"])
    assert report["unresolved"] == 20 and report["precision_on_resolved"] is None
    labels = [
        {
            "item_id": sheet["items"][0]["item_id"],
            "verdict": "yes",
            "reviewer": "Human",
            "evidence": "Opened raw CSV and saw named business entities.",
        },
        {
            "item_id": sheet["items"][1]["item_id"],
            "verdict": "unsure",
            "reviewer": "Human",
            "evidence": "Could not download the resource.",
        },
    ]
    report = evaluation.import_labels(sheet["id"], labels)
    assert report["correct_or_relevant"] == 1 and report["unresolved"] == 19
    assert report["confirmed_fraction_of_full_sample"] == 0.05


def test_blob_registry_rejects_path_traversal():
    with pytest.raises(KeyError):
        store.blob_path("../../.env")
    digest = store.blob(b"public")
    assert store.blob_path(digest).read_bytes() == b"public"


def test_blanket_yes_without_review_does_not_claim_perfect_precision():
    store.put(
        "batches",
        "discovery",
        {"shortlist": [{"dataset_id": str(i)} for i in range(50)]},
    )
    sheet = evaluation.worksheet("triage")
    labels = [
        {
            "item_id": i["item_id"],
            "verdict": "yes",
            "reviewer": "Human",
            "evidence": "I think it's correct",
        }
        for i in sheet["items"]
    ]
    result = evaluation.import_labels(
        sheet["id"],
        labels,
        reviewed=False,
        review_note="User disclosed selecting Yes without reviewing evidence.",
    )
    assert result["submitted_responses"] == result["unreviewed_responses"] == 20
    assert result["unresolved"] == 20 and result["reviewed_resolved"] == 0
    assert result["precision_on_resolved"] is None
    assert result["false_positive_rate_on_resolved"] is None
    saved = store.listing("evaluations", owner=sheet["id"], kind="human_label")
    assert all(label["verdict"] == "yes" and not label["reviewed"] for label in saved)
    # A later actual review can resolve an item; its original event is retained.
    revised = evaluation.import_labels(
        sheet["id"],
        [
            {
                **labels[0],
                "verdict": "no",
                "evidence": "Opened resource: aggregate counts only.",
            }
        ],
    )
    assert revised["unresolved"] == 19 and revised["unreviewed_responses"] == 19
    assert revised["precision_on_resolved"] == 0
    assert len(store.listing("events", owner=sheet["id"], kind="human_label")) == 21


def test_ai_audit_cannot_replace_human_ground_truth(tmp_path):
    store.put(
        "batches",
        "discovery",
        {"shortlist": [{"dataset_id": str(i)} for i in range(50)]},
    )
    sheet = evaluation.worksheet("triage")
    rows = [
        {
            "item_id": i["item_id"],
            "verdict": "yes",
            "reviewer": "AI assistant",
            "evidence": "Observed named organisation in the original raw sample.",
            "evidence_refs": {"row": 2},
        }
        for i in sheet["items"]
    ]
    rows[-1]["verdict"] = "unsure"
    path = tmp_path / "audit.json"
    path.write_text(
        json.dumps({"id": sheet["id"], "review_type": "ai_assisted", "items": rows})
    )
    cli = CliRunner()
    assert cli.invoke(app, ["import-labels", str(path)]).exit_code != 0
    assert not store.listing("evaluations", kind="human_label")
    imported = cli.invoke(app, ["import-ai-audit", str(path)])
    assert imported.exit_code == 0, imported.output
    audit = evaluation.ai_report(sheet["id"])
    assert audit["supported"] == 19 and audit["unresolved"] == 1
    assert audit["human_requirement_satisfied"] is False
    human = evaluation.report(sheet["id"])
    assert human["precision_on_resolved"] is None and human["unresolved"] == 20
    # Reimport may append audit history but cannot duplicate current item labels.
    assert cli.invoke(app, ["import-ai-audit", str(path)]).exit_code == 0
    assert len(store.listing("evaluations", kind="ai_label")) == 20
