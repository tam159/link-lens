"""Enhance a frozen approved batch without changing its sampling or baseline."""

import copy
import time
from collections import Counter
from pathlib import Path

from . import store
from .contracts import MappingSpec, content_hash
from .enhancement_contracts import EnhancementPolicy, PairDecision
from .enhancement_models import Inference, PendingInference
from .extraction import extract
from .pipeline import approved_result
from .profiles import values_only
from .reconciliation import reconcile_profiles
from .semantic_resolution import (
    cluster,
    evidence_text,
    gate,
    hard_block,
    records_from,
    retrieve,
)
from .settings import settings


def frozen_candidates(result):
    if "candidates" in result:
        return result["candidates"]
    candidates, reconstructed = [], []
    for selected in result["selection"]:
        run = store.require("runs", selected["run_id"])
        _, rows = approved_result(
            run, all_pool=True, cohort_pool_size=result.get("cohort_pool_limit")
        )
        ids = set(selected["record_ids"])
        rows = [r for r in rows if r["record_id"] in ids]
        if {r["record_id"] for r in rows} != ids:
            raise ValueError("Frozen selected records missing from approved snapshot")
        mapping = store.require("mappings", run["mapping_id"])
        snapshot = store.require("snapshots", run["snapshot_id"])
        restored = extract(
            MappingSpec.model_validate(mapping["config"]), rows, snapshot
        )
        candidates.extend(restored["candidates"])
        reconstructed.extend(restored["observations"])
    if {o["id"]: o for o in reconstructed} != {
        o["id"]: o for o in result["observations"]
    }:
        raise ValueError(
            "Reconstructed observations differ from frozen batch; do not enhance changed evidence"
        )
    return candidates


def evaluate_pairs(records, comparisons, inference, policy):
    def judge(comp):
        reason = hard_block(records[comp.left], records[comp.right])
        if reason:
            return PairDecision(comparison=comp, status="blocked", reason=reason)
        if any(
            set(records[comp.left]["identifiers"][scheme])
            & set(records[comp.right]["identifiers"][scheme])
            for scheme in ("entity.abn", "entity.acn")
        ):
            return PairDecision(
                comparison=comp,
                status="deferred",
                reason="Exact identifier evidence handled by baseline resolver; no model assessment needed",
            )
        try:
            judgment, artifact = inference.identity(
                {
                    "left": records[comp.left],
                    "right": records[comp.right],
                    "features": comp.features,
                }
            )
            return gate(comp, records, judgment, policy, artifact)
        except PendingInference as exc:
            return PairDecision(comparison=comp, status="pending", reason=str(exc))

    # Potential corroborated routes first, then exact names, then retrieval rank.
    ordered = sorted(
        comparisons,
        key=lambda c: (
            not bool(c.features.get("admission_routes")),
            not c.features.get("exact_name", False),
            -max(c.scores.values(), default=0),
            c.id,
        ),
    )
    inference.current_stage = "identity-assessment"
    return inference.parallel(judge, ordered)


def resolve_hybrid(
    observations, candidates, inference, policy, existing=None, namespace="default"
):
    records = records_from(observations, candidates)
    pending = []
    vectors = {}
    if policy.retrieval == "hybrid":
        named = [
            (ref, evidence_text(record))
            for ref, record in sorted(records.items())
            if record["names"]
        ]
        for ref, record in records.items():
            if not record["names"]:
                pending.append(
                    {
                        "record": list(ref),
                        "stage": "embedding",
                        "reason": "No subject name available",
                        "status": "unavailable",
                    }
                )
        if hasattr(inference, "embed_many"):
            embedded = inference.embed_many(named)
        else:

            def embed(item):
                ref, evidence = item
                try:
                    vector, _ = inference.embed(evidence)
                    return ref, vector, None
                except PendingInference as exc:
                    return ref, None, str(exc)

            embedded = inference.parallel(embed, named)
        for ref, vector, reason in embedded:
            if vector is None:
                pending.append(
                    {
                        "record": list(ref),
                        "stage": "embedding",
                        "reason": reason,
                        "status": "pending",
                    }
                )
            else:
                vectors[ref] = vector
    progress = getattr(inference, "progress", None)
    comparisons = retrieve(
        records,
        vectors,
        policy.top_k,
        policy.fuzzy_floor,
        policy.embedding_floor,
        progress,
    )
    if progress:
        progress("retrieval", candidate_pairs=len(comparisons), force=True)
    decisions = evaluate_pairs(records, comparisons, inference, policy)
    if progress:
        progress(
            "clustering",
            assessed=sum(d.judgment is not None for d in decisions),
            pending=sum(d.status == "pending" for d in decisions),
            force=True,
        )
    linked = cluster(records, decisions, existing, namespace)
    reviews = [
        {
            **d.model_dump(mode="json"),
            "review_kind": "relationship"
            if d.judgment.choice == "related_distinct"
            else "identity",
            "human_review_status": "unreviewed",
            "labels": [
                records[d.comparison.left]["names"],
                records[d.comparison.right]["names"],
            ],
            "subject_roles": [
                records[d.comparison.left]["subject_role"],
                records[d.comparison.right]["subject_role"],
            ],
        }
        for d in decisions
        if d.status == "deferred"
        and d.judgment is not None
        and d.judgment.choice != "different"
        and max(d.judgment.names_compatible, d.comparison.scores.get("fuzzy", 0))
        >= 0.85
    ]
    return {
        **linked,
        "candidate_decisions": [d.model_dump(mode="json") for d in decisions],
        "pending_inference": pending,
        "review_candidates": reviews,
        "retrieval_coverage": {
            "records": len(records),
            "embedded_records": len(vectors),
            "candidate_pairs": len(comparisons),
            "records_with_candidates": len(
                {ref for c in comparisons for ref in (c.left, c.right)}
            ),
            "decision_statuses": dict(Counter(d.status for d in decisions)),
            "model_assessed_pairs": sum(d.judgment is not None for d in decisions),
            "review_candidates": len(reviews),
            "note": "Retrieval coverage is not recall; audit outside candidates.",
        },
    }


def source_impact(
    observations, candidates, linked, profiles, inference, policy, existing, namespace
):
    reports = []
    old_cache_only = inference.cache_only
    inference.cache_only = True
    try:
        for source in sorted({c["source_id"] for c in candidates}):
            if getattr(inference, "progress", None):
                inference.progress(
                    "source-impact",
                    removed_source=source,
                    message="Cache-only counterfactual; changed judgments stay pending",
                    force=True,
                )
            remaining = [o for o in observations if o["source_id"] != source]
            filtered = [c for c in candidates if c["source_id"] != source]
            rerun = resolve_hybrid(
                remaining, filtered, inference, policy, existing, namespace
            )
            # Fixed memberships show field effects separately from membership effects.
            fixed = reconcile_profiles(remaining, linked["entities"], inference, policy)
            pending_pairs = sum(
                d["status"] == "pending" for d in rerun["candidate_decisions"]
            )
            pending_reconciliation = sum(
                d["status"] == "pending"
                for p in fixed
                for d in p.get("reconciliation", {}).get("decisions", [])
            ) + sum(
                d.get("status") == "pending"
                for p in fixed
                for d in p.get("reconciliation", {}).get("conflicts", [])
            )
            incomplete = bool(
                pending_pairs
                or any(
                    p.get("status") != "unavailable" for p in rerun["pending_inference"]
                )
            )
            support_changes = 0
            for entity in linked["entities"]:
                refs = [tuple(r) for r in entity["records"] if r[0] != source]
                new = {rerun["membership"].get(r) for r in refs}
                support_changes += not refs or None in new or len(new) != 1
            reports.append(
                {
                    "removed_source_id": source,
                    "resolution_policy": policy.model_dump(),
                    "scope": "Fixed-membership profiles and hybrid re-resolution; cache-only, changed inputs are pending, not negative decisions.",
                    "status": "incomplete"
                    if incomplete or pending_reconciliation
                    else "complete",
                    "pending_pairs": pending_pairs,
                    "pending_embeddings": len(rerun["pending_inference"]),
                    "pending_reconciliation": pending_reconciliation,
                    "profiles_with_changed_membership_support": None
                    if incomplete
                    else support_changes,
                    "profiles_with_value_changes": None
                    if pending_reconciliation
                    else sum(
                        values_only(a) != values_only(b)
                        for a, b in zip(profiles, fixed)
                    ),
                }
            )
    finally:
        inference.cache_only = old_cache_only
    return reports


def feasibility(observations, candidates, policy):
    records = records_from(observations, candidates)
    fields = {}
    for ref, r in records.items():
        group = fields.setdefault(
            ref[0],
            {
                "records": 0,
                "named_records": 0,
                "fields": Counter(),
                "address_roles": Counter(),
            },
        )
        group["records"] += 1
        group["named_records"] += bool(r["names"])
        group["fields"].update({o["field"] for o in r["observations"]})
        group["address_roles"].update(
            {
                o.get("address_role", "unknown")
                for o in r["observations"]
                if o["field"].startswith("address.")
            }
        )
    candidates_for_review = retrieve(
        records, top_k=policy.top_k, fuzzy_floor=policy.fuzzy_floor
    )
    allowed = [
        c
        for c in candidates_for_review
        if not hard_block(records[c.left], records[c.right])
    ]
    routes = Counter(route for c in allowed for route in c.features["admission_routes"])
    return {
        "records": len(records),
        "sources": fields,
        "lexical_candidate_pairs": len(candidates_for_review),
        "assessable_lexical_pairs": len(allowed),
        "potential_admission_routes": dict(routes),
        "warnings": (
            []
            if routes
            else [
                "No automatic-admission evidence combination found among lexical candidates. Model review may be useful, but more links are not guaranteed."
            ]
        ),
        "scope": "Read-only lexical feasibility scan before embeddings; potential routes are not verified matches and semantic retrieval may find additional candidates.",
    }


def enhance(
    batch_id,
    policy=None,
    output=None,
    budget=None,
    inference_factory=Inference,
    max_pairs=None,
    preflight_only=False,
    progress=None,
):
    cfg = settings()
    if output is not None:
        validate_output(output)
    policy = policy or EnhancementPolicy(
        embedding_model=cfg.embedding_model,
        decision_model=cfg.resolution_model,
        explanation_model=cfg.model,
    )
    if progress:
        progress(
            "loading",
            batch_id=batch_id,
            message="Reading frozen evidence and reconstructing approved candidates",
            force=True,
        )
    parent = store.require("batches", batch_id)
    original = store.read_json(parent["result_artifact"])
    # Stable job ownership preserves cumulative spend and successful caches on retry.
    job_id = (
        "enhance-"
        + content_hash(
            {
                "parent_artifact": parent["result_artifact"],
                "policy": policy.model_dump(),
            }
        )[:48]
    )
    experiment = parent.get("experiment_id") or store.require(
        "runs", parent["run_ids"][0]
    ).get("experiment_id", cfg.experiment_id)
    start = time.monotonic()
    candidates = frozen_candidates(original)
    if progress:
        progress(
            "preflight",
            message="Checking available fields and lexical evidence routes",
            force=True,
        )
    preflight = feasibility(original["observations"], candidates, policy)
    if progress:
        progress(
            "preflight",
            assessable_pairs=preflight["assessable_lexical_pairs"],
            routes=preflight["potential_admission_routes"],
            warnings=preflight["warnings"],
            force=True,
        )
    if preflight_only:
        return {
            "baseline_batch_id": batch_id,
            "policy": policy.model_dump(),
            "preflight": preflight,
            "model_calls": 0,
        }
    namespace = original.get("enhancement_namespace", batch_id)
    inference = inference_factory(
        job_id,
        experiment,
        policy,
        cfg.enhancement_max_cost_usd if budget is None else budget,
        cfg.enhancement_workers,
        cfg.enhancement_retries,
    )
    inference.progress = progress
    inference.max_pairs = cfg.enhancement_max_pairs if max_pairs is None else max_pairs
    if inference.max_pairs < 0:
        raise ValueError("max_pairs cannot be negative")
    if not 1 <= cfg.embedding_batch_size <= 128:
        raise ValueError("embedding_batch_size must be between 1 and 128")
    inference.embedding_batch_size = cfg.embedding_batch_size
    existing = original["entities"]
    linked = resolve_hybrid(
        original["observations"], candidates, inference, policy, existing, namespace
    )
    if progress:
        progress("profiles", entities=len(linked["entities"]), force=True)
    profiles = reconcile_profiles(
        original["observations"], linked["entities"], inference, policy
    )
    impact = source_impact(
        original["observations"],
        candidates,
        linked,
        profiles,
        inference,
        policy,
        existing,
        namespace,
    )
    # Same decisions restricted to lexical retrieval provide an ablation with no extra calls.
    from .enhancement_contracts import PairDecision

    lexical_decisions = [
        PairDecision.model_validate(d)
        for d in linked["candidate_decisions"]
        if "fuzzy" in d["comparison"]["methods"]
    ]
    records = records_from(original["observations"], candidates)
    fuzzy = cluster(records, lexical_decisions, existing, namespace)
    from .resolution import resolve

    exact = resolve(original["observations"], candidates, existing)
    variants = [("exact", exact), ("fuzzy_jev", fuzzy)]
    if policy.retrieval == "hybrid":
        variants.append(("hybrid_jev", linked))
    original_profiles = {p["canonical_entity_key"]: p for p in original["profiles"]}
    comparison_profiles = {p["canonical_entity_key"]: p for p in profiles}
    comparison = {
        "status": "experimental_human_labels_pending",
        "selection_hash": content_hash(original["selection"]),
        "variants": {
            name: {
                "links": len(value["links"]),
                "profiles": len(value["entities"]),
                "linked_records": len(value["membership"]),
            }
            for name, value in variants
        },
        "additional_correct_links": None,
        "semantic_precision": None,
        "benchmark_recall": None,
        "cluster_contamination": None,
        "target_precision": 0.99,
        "existing_profiles_with_value_changes": sum(
            values_only(p) != values_only(comparison_profiles[eid])
            for eid, p in original_profiles.items()
            if eid in comparison_profiles
        ),
        "new_profiles": len(comparison_profiles.keys() - original_profiles.keys()),
        "removed_profiles": len(original_profiles.keys() - comparison_profiles.keys()),
        "deferred_candidate_pairs": sum(
            d["status"] == "deferred" for d in linked["candidate_decisions"]
        ),
        "pending_candidate_pairs": sum(
            d["status"] == "pending" for d in linked["candidate_decisions"]
        ),
        "population_recall": None,
        "note": "Counts are not accuracy. Same frozen selection; lexical ablation reuses identical evidence judgments. Source sampling favors identifier overlap.",
        "retrieval": linked["retrieval_coverage"],
        "review_candidates": len(linked["review_candidates"]),
        "elapsed_seconds": round(time.monotonic() - start, 3),
    }
    result = {
        **copy.deepcopy(original),
        **{k: v for k, v in linked.items() if k != "membership"},
        "candidates": candidates,
        "profiles": profiles,
        "source_impact": impact,
        "baseline_batch_id": batch_id,
        "enhancement_namespace": namespace,
        "enhancement_policy": policy.model_dump(),
        "preflight": preflight,
        "execution_limits": {
            "max_new_pairs": inference.max_pairs,
            "embedding_batch_size": inference.embedding_batch_size,
        },
        "comparison": comparison,
        "enhancement_job_id": job_id,
        "variant_memberships": {
            name: [
                {"record": list(ref), "entity_id": eid}
                for ref, eid in sorted(value["membership"].items())
            ]
            for name, value in variants
        },
    }
    # Each retry publishes an immutable revision; budget job remains stable.
    derived_id = (
        job_id
        + "-"
        + content_hash({k: v for k, v in result.items() if k != "batch_id"})[:12]
    )
    result["batch_id"] = derived_id
    if progress:
        progress(
            "saving",
            links=len(result["links"]),
            profiles=len(result["profiles"]),
            review_candidates=len(result["review_candidates"]),
            force=True,
        )
    result_id = store.json_blob(result, "enhanced-pipeline-results.json")
    for table, rows, kind, id_field in [
        ("entities", linked["entities"], "enhanced_entity", "id"),
        ("links", linked["links"], "proposed_link", "id"),
        ("profiles", profiles, "profile", "canonical_entity_key"),
    ]:
        for row in rows:
            # Batch-owned snapshots do not overwrite canonical baseline entities.
            key = content_hash([derived_id, table, row[id_field]])
            store.put(table, key, row, derived_id, kind, immutable=True)
    for ref, eid in linked["membership"].items():
        store.put(
            "memberships",
            content_hash([derived_id, ref]),
            {"batch_id": derived_id, "record": list(ref), "entity_id": eid},
            derived_id,
            "membership",
            immutable=True,
        )
    batch = {
        "id": derived_id,
        "baseline_batch_id": batch_id,
        "experiment_id": experiment,
        "enhancement_job_id": job_id,
        "result_artifact": result_id,
        "run_ids": parent["run_ids"],
        "created_at": store.now(),
        "counts": {
            k: len(result[k]) for k in ("observations", "links", "unlinked", "profiles")
        },
        "evaluation_status": "experimental_human_labels_pending",
        "policy": policy.model_dump(),
    }
    store.put("batches", derived_id, batch, kind="enhancement", immutable=True)
    if output is not None:
        export_enhancement(result, Path(output))
    if progress:
        progress(
            "complete",
            batch_id=derived_id,
            counts=batch["counts"],
            review_candidates=len(result["review_candidates"]),
            pending_pairs=comparison["pending_candidate_pairs"],
            force=True,
        )
    return batch


def validate_output(output):
    path = Path(output).resolve()
    submission = Path("outputs").resolve()
    local = submission / "local-run"
    if (
        path == submission
        or (path.is_relative_to(submission) and not path.is_relative_to(local))
        or path == Path("experiments").resolve()
        or path.is_relative_to(Path("experiments").resolve())
    ):
        raise ValueError(
            "Choose outputs/local-run/ or a separate experimental directory"
        )


def export_enhancement(result, output):
    from .exports import jsonl, write_json

    output = Path(output)
    validate_output(output)
    for key in (
        "observations",
        "candidates",
        "links",
        "unlinked",
        "entities",
        "profiles",
        "candidate_decisions",
        "cluster_decisions",
        "pending_inference",
        "review_candidates",
    ):
        jsonl(output / (key + ".jsonl"), result.get(key, []))
    for key, filename in [
        ("comparison", "comparison.json"),
        ("source_impact", "source-removal.json"),
        ("selection", "selection.json"),
        ("enhancement_policy", "policy.json"),
        ("preflight", "preflight.json"),
        ("variant_memberships", "variant-memberships.json"),
    ]:
        write_json(output / filename, result.get(key, {}))
    from .pricing import collect, estimate

    rows = [r for r in collect() if r["run_id"] == result["enhancement_job_id"]]
    write_json(output / "cost-summary.json", estimate(rows))
    write_json(output / "cost-usage.json", rows)
    write_json(
        output / "manifest.json",
        {
            "batch_id": result["batch_id"],
            "baseline_batch_id": result["baseline_batch_id"],
            "enhancement_job_id": result["enhancement_job_id"],
            "status": "experimental_human_labels_pending",
        },
    )
