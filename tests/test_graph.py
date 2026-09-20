"""Deliberately faulty model proposal exercises real validator -> revision -> HIL."""

from copy import deepcopy
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from link_lens import store, agent
from link_lens.contracts import SemanticReview
from link_lens.ingestion import new_run


def prepared(spec, snapshot):
    data = (
        "name,abn\n" + "".join(f"Example {i},51824753556\n" for i in range(200))
    ).encode()
    blob = store.blob(data)
    snapshot.update(
        artifact_id=blob,
        sha256=blob,
        inspection={
            "format": "csv",
            "preview": [["name", "abn"], ["Example", "51824753556"]],
        },
        dataset_notes="",
        documentation=[],
    )
    snapshot["receipt"]["partial"] = False
    source = {
        "id": "source-a",
        "slug": "fixture",
        "metadata": {"title": "Test fixture"},
    }
    store.put("sources", source["id"], source)
    store.put("snapshots", snapshot["id"], snapshot)
    return new_run(source, snapshot)


def test_revision_interrupt_resume_idempotency(monkeypatch, spec, snapshot):
    run = prepared(spec, snapshot)
    calls = []
    bad = deepcopy(spec)
    bad.fields[0].source_fields = ["nonexistent_name"]

    def fake_call(run_id, schema, prompt, stage):
        calls.append(stage)
        if stage == "inspect":
            return agent.AnalysisPlan(
                reader=spec.reader, grain_hypothesis=spec.record_grain, uncertainties=[]
            )
        if stage == "propose_mapping":
            return bad if calls.count(stage) == 1 else spec
        return SemanticReview(
            acceptable=True,
            blocking_issues=[],
            warnings=[],
            evidence_checked=["fixture headers"],
        )

    monkeypatch.setattr(agent, "call", fake_call)
    saver = InMemorySaver()
    graph = agent.build_graph(saver)
    config = {"configurable": {"thread_id": "review-test"}}
    result = graph.invoke({"run_id": run["id"]}, config)
    assert result.get("__interrupt__"), store.require("runs", run["id"]).get("error")
    current = store.require("runs", run["id"])
    assert current["version"] == 2 and current["status"] == "waiting_for_human"
    validations = store.listing("events", owner=run["id"], kind="validation")
    assert not validations[0]["report"]["passed"] and validations[1]["report"]["passed"]
    digest = store.require("mappings", current["mapping_id"])["config_hash"]
    # New graph instance with the same checkpointer models orchestration restart.
    restarted = agent.build_graph(saver)
    restarted.invoke(
        Command(resume=[{"type": "accept", "args": {"config_hash": digest}}]), config
    )
    current = store.require("runs", run["id"])
    assert current["status"] == "completed"
    count = len(store.listing("observations"))
    agent.extract_node({"run_id": run["id"]})
    assert len(store.listing("observations")) == count
    assert len(store.listing("approvals")) == 1


def test_final_failure_never_returns_to_model(monkeypatch, spec, snapshot):
    run = prepared(spec, snapshot)
    # Direct final node receives empty final partition and must stop without approval.
    store.put(
        "mappings",
        "m",
        {"id": "m", "config": spec.model_dump(), "config_hash": "hash", "version": 1},
    )
    run.update(
        mapping_id="m",
        partitions_artifact=store.json_blob(
            {"headers": ["name", "abn"], "partitions": {"final": []}}
        ),
    )
    store.put("runs", run["id"], run)
    result = agent.final_node({"run_id": run["id"]})
    assert (
        result["route"] == "end"
        and store.require("runs", run["id"])["status"] == "final_validation_failed"
    )
    assert not store.listing("approvals")


def test_structural_reader_repair_precedes_partition_freeze(
    monkeypatch, spec, snapshot
):
    run = prepared(spec, snapshot)
    data = (
        "name,abn\n" + "".join(f'"Example {i}",51824753556\n' for i in range(200))
    ).encode()
    digest = store.blob(data)
    snap = store.require("snapshots", "snapshot")
    snap.update(artifact_id=digest, sha256=digest)
    store.put("snapshots", "snapshot", snap)
    calls = []

    def fake_call(run_id, schema, prompt, stage):
        calls.append(stage)
        if stage == "inspect":
            reader = (
                spec.reader.model_copy(update={"delimiter": "\t"})
                if calls.count("inspect") == 1
                else spec.reader
            )
            return agent.AnalysisPlan(
                reader=reader, grain_hypothesis=spec.record_grain, uncertainties=[]
            )
        if stage == "propose_mapping":
            return spec
        return SemanticReview(
            acceptable=True,
            blocking_issues=[],
            warnings=[],
            evidence_checked=["fixture"],
        )

    monkeypatch.setattr(agent, "call", fake_call)
    graph = agent.build_graph(InMemorySaver())
    result = graph.invoke(
        {"run_id": run["id"]}, {"configurable": {"thread_id": "reader-repair"}}
    )
    assert result.get("__interrupt__")
    saved = store.require("runs", run["id"])
    assert saved["reader_attempts"] == 2 and saved["version"] == 1
    assert len(store.listing("events", owner=run["id"], kind="reader_validation")) == 1
    assert store.read_json(saved["partitions_artifact"])["reader"]["delimiter"] == ","


def test_critique_format_retry_is_bounded(monkeypatch, spec, snapshot):
    run = prepared(spec, snapshot)
    monkeypatch.setattr(agent, "proposal_context", lambda *args, **kwargs: "{}")

    def malformed(*args, **kwargs):
        raise ValueError("Missing warnings field")

    monkeypatch.setattr(agent, "call", malformed)
    assert agent.critique_node({"run_id": run["id"]})["route"] == "critique"
    assert agent.critique_node({"run_id": run["id"]})["route"] == "end"
    updated = store.require("runs", run["id"])
    assert updated["critique_format_attempts"] == 2
    assert updated["status"] == "failed"
    assert not store.listing("approvals")
