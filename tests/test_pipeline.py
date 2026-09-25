from link_lens import store
from link_lens.pipeline import assemble
from link_lens.ingestion import new_run
from link_lens.contracts import content_hash
from link_lens.extraction import valid_abn
from link_lens.readers import record, partition
from link_lens.exports import export
import pytest
from link_lens.pipeline import select_cohort


def test_baseline_cohort_is_not_displaced_by_new_entities():
    entities = [{"id": x} for x in ["a-new", "b-new", "y-old", "z-old"]]
    baseline = [{"id": "y-old"}, {"id": "z-old"}]
    assert select_cohort(entities, 2, baseline) == baseline
    assert select_cohort(entities, 2) == entities[:2]
    with pytest.raises(ValueError, match="baseline entities"):
        select_cohort(entities[:-1], 2, baseline)


def test_fifty_profiles_require_exact_approved_configs(tmp_path, spec, snapshot):
    # Synthetic fixture mappings and approvals exist only in isolated test SQLite.
    ids = []
    number = 10000000000
    while len(ids) < 50:
        if valid_abn(str(number)):
            ids.append(str(number))
        number += 1
    runs = []
    for source in ["source-a", "source-b", "source-c"]:
        snap = {**snapshot, "id": source + "-snapshot", "source_id": source}
        store.put(
            "sources",
            source,
            {
                "id": source,
                "portal": "https://data.gov.au/data",
                "metadata": {
                    "title": "Synthetic test source",
                    "license_title": "Fixture",
                },
            },
        )
        store.put("snapshots", snap["id"], snap)
        run = new_run({"id": source, "slug": source}, snap)
        spec.ontology_hash = run["ontology_hash"]
        mapping = {
            "id": source + "-mapping",
            "config": spec.model_dump(),
            "config_hash": content_hash(spec),
            "version": 1,
        }
        store.put("mappings", mapping["id"], mapping, run["id"])
        approval = {
            "id": source + "-approval",
            "decision": "approved",
            "config_hash": content_hash(spec),
            "reviewer": "TEST FIXTURE; NOT HUMAN EVALUATION",
        }
        store.put("approvals", approval["id"], approval)
        rows = [
            record(source, "csv", i + 20, {"name": f"Synthetic Entity {i}", "abn": abn})
            for i, abn in enumerate(ids)
        ]
        run.update(
            status="completed",
            mapping_id=mapping["id"],
            approval_id=approval["id"],
            partitions_artifact=store.json_blob({"partitions": partition(rows)}),
        )
        store.put("runs", run["id"], run)
        runs.append(run["id"])
    batch = assemble(runs[:2])
    assert batch["counts"]["profiles"] == 50 and batch["counts"]["links"] == 50
    assert len(store.listing("observations")) == 200
    assert export(tmp_path / "outputs", batch["id"])["okf"]["broken_links"] == 0
    extended = assemble(runs, baseline_batch_id=batch["id"])
    import runpy
    from pathlib import Path

    compare = runpy.run_path(
        str(Path(__file__).parents[1] / "scripts/compare_source_contribution.py")
    )["compare"]
    contribution = compare(
        store.read_json(batch["result_artifact"]),
        store.read_json(extended["result_artifact"]),
        "source-c",
    )
    assert contribution["success"]
    assert contribution["existing_profiles_receiving_evidence"] == 50
    assert contribution["links_involving_new_source"] > 0
    assert not compare(
        store.read_json(batch["result_artifact"]),
        store.read_json(batch["result_artifact"]),
        "source-c",
    )["success"]
    with pytest.raises(ValueError, match="retain all original"):
        assemble(runs[1:], baseline_batch_id=batch["id"])


def test_post_approval_pool_expands_same_snapshot_without_changing_mapping(
    spec, snapshot
):
    from link_lens.pipeline import approved_result

    data = (
        "name,abn\n" + "".join(f"Example {i},51824753556\n" for i in range(20))
    ).encode()
    digest = store.blob(data)
    snapshot.update(artifact_id=digest, sha256=digest)
    store.put("snapshots", snapshot["id"], snapshot)
    config_hash = content_hash(spec)
    store.put(
        "mappings", "mapping", {"config": spec.model_dump(), "config_hash": config_hash}
    )
    store.put(
        "approvals", "approval", {"decision": "approved", "config_hash": config_hash}
    )
    pack = store.json_blob(
        {"partitions": {"discovery": [], "validation": [], "final": []}}
    )
    run = {
        "status": "completed",
        "mapping_id": "mapping",
        "approval_id": "approval",
        "snapshot_id": snapshot["id"],
        "partitions_artifact": pack,
    }
    result, rows = approved_result(run, all_pool=True, cohort_pool_size=15)
    assert len(rows) == 15 and len(result["observations"]) == 30
    assert store.read_json(pack)["partitions"]["final"] == []
    assert all(o["config_hash"] == config_hash for o in result["observations"])
