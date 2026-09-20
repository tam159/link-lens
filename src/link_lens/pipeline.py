import uuid
from collections import defaultdict
from . import store
from .contracts import MappingSpec, content_hash
from .extraction import extract
from .resolution import resolve
from .profiles import assemble_profiles, impact
from .readers import read_records


def approved_result(run, all_pool=False, cohort_pool_size=None):
    if run["status"] != "completed":
        raise ValueError(
            f"{run['source_slug']} is {run['status']}; approval and extraction must complete"
        )
    mapping = store.require("mappings", run["mapping_id"])
    approval = store.require("approvals", run["approval_id"])
    if (
        approval["decision"] != "approved"
        or approval["config_hash"] != mapping["config_hash"]
    ):
        raise ValueError("Stale or missing mapping approval")
    snapshot = store.require("snapshots", run["snapshot_id"])
    pack = store.read_json(run["partitions_artifact"])
    rows = sum(pack["partitions"].values(), [])
    if cohort_pool_size is not None:
        # Post-approval deterministic processing of the same immutable snapshot.
        # This does not expose additional records to the inference agent or alter its holdout.
        _, rows = read_records(
            store.blob_path(snapshot["artifact_id"]),
            MappingSpec.model_validate(mapping["config"]).reader,
            snapshot["sha256"],
            snapshot["receipt"].get("partial", False),
            cohort_pool_size,
        )
    if not all_pool:
        rows = sorted(rows, key=lambda r: r["record_id"])[:1000]
    return extract(MappingSpec.model_validate(mapping["config"]), rows, snapshot), rows


def select_cohort(entities, minimum_profiles, baseline_entities=None):
    if baseline_entities is None:
        return sorted(entities, key=lambda e: e["id"])[:minimum_profiles]
    required_ids = {e["id"] for e in baseline_entities}
    available = {e["id"]: e for e in entities}
    missing = required_ids - available.keys()
    if missing:
        raise ValueError(
            f"{len(missing)} baseline entities cannot be resolved in the new pools; inspect conflicts or increase pool size"
        )
    return [available[key] for key in sorted(required_ids)]


def assemble(
    run_ids, minimum_profiles=50, cohort_pool_size=None, baseline_batch_id=None
):
    runs = [store.require("runs", r) for r in run_ids]
    if len({r["source_id"] for r in runs}) != len(runs):
        raise ValueError("Select at most one onboarding run per dataset")
    baseline_entities = None
    if baseline_batch_id:
        baseline = store.require("batches", baseline_batch_id)
        if not set(baseline["run_ids"]).issubset(run_ids):
            raise ValueError(
                "Baseline comparison must retain all original approved runs"
            )
        baseline_entities = store.read_json(baseline["result_artifact"])["entities"]
    combined = {"observations": [], "candidates": []}
    by_run = {}
    for run in runs:
        result, rows = approved_result(
            run, all_pool=True, cohort_pool_size=cohort_pool_size
        )
        by_run[run["id"]] = (result, rows)
        for key in combined:
            combined[key].extend(result[key])
    existing = store.listing("entities")
    feasibility = resolve(**combined, existing_entities=existing)
    cohort = select_cohort(feasibility["entities"], minimum_profiles, baseline_entities)
    if len(cohort) < minimum_profiles:
        raise ValueError(
            f"Only {len(cohort)} linked entities in sampled pools, need {minimum_profiles}. Try a larger post-approval cohort pool within the same snapshot; if more downloads are needed, onboard those new snapshots. Do not fabricate links."
        )
    required = defaultdict(set)
    for entity in cohort:
        seen = set()
        for source, record in entity["records"]:
            if source not in seen:
                required[source].add(record)
                seen.add(source)
    observations = []
    candidates = []
    issues = []
    selections = []
    for run in runs:
        _, rows = by_run[run["id"]]
        want = required[run["source_id"]]
        selected = [r for r in rows if r["record_id"] in want]
        if len(selected) > 1000:
            raise ValueError(
                "Cohort exceeds 1000 records for a source; choose smaller cohort"
            )
        selected.extend(
            sorted(
                [r for r in rows if r["record_id"] not in want],
                key=lambda r: r["record_id"],
            )[: 1000 - len(selected)]
        )
        mapping = store.require("mappings", run["mapping_id"])
        snapshot = store.require("snapshots", run["snapshot_id"])
        result = extract(
            MappingSpec.model_validate(mapping["config"]), selected, snapshot
        )
        observations.extend(result["observations"])
        candidates.extend(result["candidates"])
        issues.extend(result["issues"])
        selections.append(
            {
                "run_id": run["id"],
                "source_id": run["source_id"],
                "selected_records": len(selected),
                "cohort_records": len(want),
                "record_ids": [r["record_id"] for r in selected],
                "pool_records": len(rows),
            }
        )
    linked = resolve(observations, candidates, existing_entities=existing)
    profiles = assemble_profiles(observations, linked["entities"])
    batch_id = str(uuid.uuid4())
    result = {
        "batch_id": batch_id,
        "run_ids": run_ids,
        "cohort_pool_limit": cohort_pool_size,
        "baseline_batch_id": baseline_batch_id,
        "selection_policy": "Identifier-overlap cohort followed by deterministic hash-ranked filler; not a coverage estimate.",
        "selection": selections,
        "observations": observations,
        "links": linked["links"],
        "unlinked": linked["unlinked"],
        "entities": linked["entities"],
        "profiles": profiles,
        "issues": issues,
        "source_impact": impact(observations, candidates, linked["entities"], profiles),
    }
    result_id = store.json_blob(result, "pipeline-results.json")
    for observation in observations:
        store.put(
            "observations",
            observation["id"],
            observation,
            observation["source_id"],
            "observation",
            immutable=True,
        )
    for entity in linked["entities"]:
        store.put("entities", entity["id"], entity, kind="entity")
    for ref, entity_id in linked["membership"].items():
        key = content_hash({"batch": batch_id, "record": ref})
        store.put(
            "memberships",
            key,
            {"batch_id": batch_id, "record": list(ref), "entity_id": entity_id},
            batch_id,
            "membership",
            immutable=True,
        )
    for link in linked["links"]:
        store.put(
            "links",
            batch_id + ":" + link["id"][:64],
            link,
            batch_id,
            "proposed_link",
            immutable=True,
        )
    for profile in profiles:
        store.put(
            "profiles",
            batch_id + ":" + profile["canonical_entity_key"],
            profile,
            batch_id,
            "profile",
            immutable=True,
        )
    batch = {
        "id": batch_id,
        "baseline_batch_id": baseline_batch_id,
        "result_artifact": result_id,
        "run_ids": run_ids,
        "created_at": store.now(),
        "counts": {
            k: len(result[k]) for k in ["observations", "links", "unlinked", "profiles"]
        },
        "evaluation_status": "human_labels_pending",
    }
    store.put("batches", batch_id, batch, kind="pipeline", immutable=True)
    return batch
