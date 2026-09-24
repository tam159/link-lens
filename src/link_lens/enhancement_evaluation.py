"""Human-only, entity-separated development/test worksheets and bounded metrics."""

import math
import random
from itertools import combinations
from .contracts import content_hash
from .enhancement_contracts import PairDecision
from .semantic_resolution import records_from, cluster
from .resolution import resolve


def worksheet(result, sample_size=200, seed=159):
    if sample_size < 1:
        raise ValueError("sample_size must be positive")
    refs = sorted((c["source_id"], c["source_record_id"]) for c in result["candidates"])
    groups = {tuple(r): e["id"] for e in result["entities"] for r in e["records"]}
    groups.update({r: groups.get(r, content_hash(r)) for r in refs})
    split = {
        r: (
            "heldout"
            if int(content_hash([seed, groups[r]])[:8], 16) % 2
            else "development"
        )
        for r in refs
    }
    decisions = {
        tuple(
            sorted((tuple(d["comparison"]["left"]), tuple(d["comparison"]["right"])))
        ): d
        for d in result["candidate_decisions"]
    }
    records = records_from(result["observations"], result["candidates"])
    pools = {"retrieved": [], "outside_candidates": []}
    excluded = 0
    # Reservoir sampling avoids materialising the cross-product of source records.
    seen = {k: 0 for k in pools}
    rng = random.Random(seed)
    for a, b in combinations(refs, 2):
        if a[0] == b[0]:
            continue
        if split[a] != split[b]:
            excluded += 1
            continue
        stratum = "retrieved" if (a, b) in decisions else "outside_candidates"
        seen[stratum] += 1
        index = (
            len(pools[stratum])
            if len(pools[stratum]) < sample_size
            else rng.randrange(seen[stratum])
        )
        if index >= sample_size:
            continue
        item = {
            "pair_id": content_hash([a, b]),
            "left": list(a),
            "right": list(b),
            "split": split[a],
            "stratum": stratum,
            "label": None,
            "reviewer": None,
            "reviewed_at": None,
            "evidence_notes": None,
            "left_entity_group": groups[a],
            "right_entity_group": groups[b],
        }
        if index == len(pools[stratum]):
            pools[stratum].append(item)
        else:
            pools[stratum][index] = item
    # Keep hard positives with masked identifiers available as a separate challenge set,
    # never misrepresent these identifier-derived controls as human ground truth.
    controls = []
    exact = resolve(result["observations"], result["candidates"])
    for link in exact["links"][:sample_size]:
        pair = [tuple(link[k]) for k in ("source_a_record", "source_b_record")]
        if split[pair[0]] != split[pair[1]]:
            continue
        controls.append(
            {
                "split": split[pair[0]],
                "basis": "identifier-derived positive control, not human label",
                "records": [
                    {
                        **records[r],
                        "identifiers": {"entity.abn": [], "entity.acn": []},
                        "observations": [
                            o
                            for o in records[r]["observations"]
                            if o["field"] not in {"entity.abn", "entity.acn"}
                        ],
                    }
                    for r in pair
                ],
                "label": None,
            }
        )
    # Add bounded challenge examples for each available failure mode, not labels.
    challenges = {
        k: []
        for k in (
            "missing_identifiers",
            "similar_names",
            "shared_values",
            "brands_branches",
            "ownership_conflicts",
        )
    }
    for (a, b), decision in sorted(decisions.items()):
        if split[a] != split[b]:
            continue
        features = decision["comparison"]["features"]
        flags = []
        if any(not any(records[r]["identifiers"].values()) for r in (a, b)):
            flags.append("missing_identifiers")
        if decision["comparison"]["scores"].get("fuzzy", 0) >= 0.8:
            flags.append("similar_names")
        if any(features.get("repeated_value_flags", {}).values()):
            flags.append("shared_values")
        judgment = decision.get("judgment") or {}
        if judgment.get("choice") == "related_distinct" or any(
            records[r]["subject_role"] != "legal_entity" for r in (a, b)
        ):
            flags.append("brands_branches")
        if decision["status"] == "blocked" or judgment.get("ownership_clear", 1) < 0.98:
            flags.append("ownership_conflicts")
        item = {
            "pair_id": content_hash([a, b]),
            "left": list(a),
            "right": list(b),
            "split": split[a],
            "stratum": "retrieved",
            "scenarios": flags,
            "label": None,
            "reviewer": None,
            "reviewed_at": None,
            "evidence_notes": None,
            "left_entity_group": groups[a],
            "right_entity_group": groups[b],
        }
        for flag in flags:
            if len(challenges[flag]) < min(20, sample_size):
                challenges[flag].append(item)
    chosen = {i["pair_id"]: i for i in pools["retrieved"] + pools["outside_candidates"]}
    for items_for_case in challenges.values():
        chosen.update({i["pair_id"]: i for i in items_for_case})
    items = sorted(
        chosen.values(),
        key=lambda x: (x["split"], x["pair_id"]),
    )
    return {
        "batch_id": result["batch_id"],
        "selection_hash": content_hash(result["selection"]),
        "policy_hash": content_hash(result["enhancement_policy"]),
        "seed": seed,
        "status": "human_labels_pending",
        "population_counts": seen,
        "cross_split_pairs_excluded": excluded,
        "split_basis": "Exact/provisional cluster grouping, with unlinked records grouped individually; reviewer must correct entity groups and reject cross-split identity leakage.",
        "items": items,
        "pair_manifest": [i["pair_id"] for i in items],
        "challenge_counts": {k: len(v) for k, v in challenges.items()},
        "masked_identifier_controls": controls,
        "review_scenarios": [
            "missing identifiers",
            "similar names with different owners",
            "shared addresses or domains",
            "brands and branches",
            "ownership conflicts",
            "missed candidates",
        ],
        "records": [records[r] for r in refs],
    }


def wilson(success, count):
    if not count:
        return None
    z = 1.96
    p = success / count
    center = (p + z * z / (2 * count)) / (1 + z * z / count)
    half = (
        z
        * math.sqrt(p * (1 - p) / count + z * z / (4 * count * count))
        / (1 + z * z / count)
    )
    return [max(0, center - half), min(1, center + half)]


def evaluate(result, packet, split="heldout"):
    if split not in {"development", "heldout"}:
        raise ValueError("Unknown evaluation split")
    if (
        packet["batch_id"] != result["batch_id"]
        or packet["selection_hash"] != content_hash(result["selection"])
        or packet["policy_hash"] != content_hash(result["enhancement_policy"])
    ):
        raise ValueError("Evaluation belongs to different evidence or policy")
    refs = {(c["source_id"], c["source_record_id"]) for c in result["candidates"]}
    if set(packet.get("pair_manifest", [])) != {i["pair_id"] for i in packet["items"]}:
        raise ValueError(
            "Evaluate the combined worksheet; both split manifests are required"
        )
    group_splits, record_splits, seen_pairs = {}, {}, set()
    record_groups = {}
    for item in packet["items"]:
        pair = tuple(sorted((tuple(item["left"]), tuple(item["right"]))))
        if (
            item["pair_id"] != content_hash(pair)
            or pair[0][0] == pair[1][0]
            or item["split"] not in {"development", "heldout"}
        ):
            raise ValueError("Invalid pair identity or split")
        if item["pair_id"] in seen_pairs:
            raise ValueError("Duplicate evaluation pair")
        seen_pairs.add(item["pair_id"])
        for side in ("left", "right"):
            ref = tuple(item[side])
            if ref not in refs:
                raise ValueError("Unknown source record")
            group = item[side + "_entity_group"]
            if not isinstance(group, str) or not group.strip():
                raise ValueError("Human entity group must be a nonempty string")
            if ref in record_groups and record_groups[ref] != group:
                raise ValueError("One record has inconsistent human entity groups")
            record_groups[ref] = group
            for key, assignment in [(ref, record_splits), (group, group_splits)]:
                if key in assignment and assignment[key] != item["split"]:
                    raise ValueError(
                        "Entity/record leakage across development and heldout"
                    )
                assignment[key] = item["split"]
        if (
            item.get("label") == "same"
            and item["left_entity_group"] != item["right_entity_group"]
        ):
            raise ValueError(
                "Human same-entity labels require a common entity group before evaluation"
            )
        if item.get("label") not in {None, "same", "different", "unknown"}:
            raise ValueError("Use human labels same, different, unknown, or null")
        if item.get("label") is not None and not all(
            item.get(k) for k in ("reviewer", "reviewed_at", "evidence_notes")
        ):
            raise ValueError(
                "Human labels require reviewer, timestamp and evidence notes"
            )
    labelled = [
        i
        for i in packet["items"]
        if i["split"] == split and i.get("label") in {"same", "different"}
    ]
    records = records_from(result["observations"], result["candidates"])
    decisions = [PairDecision.model_validate(d) for d in result["candidate_decisions"]]
    variants = {"exact": resolve(result["observations"], result["candidates"])}
    for name, ds in [
        ("fuzzy_jev", [d for d in decisions if "fuzzy" in d.comparison.methods]),
        ("hybrid_jev", decisions),
    ]:
        variants[name] = cluster(
            records, ds, namespace=result.get("enhancement_namespace", "evaluation")
        )
    if "variant_memberships" in result:
        variants = {
            name: {
                "membership": {
                    tuple(item["record"]): item["entity_id"] for item in memberships
                }
            }
            for name, memberships in result["variant_memberships"].items()
        }
    reports = {}
    for name, value in variants.items():
        membership = value["membership"]
        correct = predicted = positives = retrieved_positive = contaminated = (
            additional
        ) = 0
        retrieval_pairs = {
            tuple(sorted((d.comparison.left, d.comparison.right)))
            for d in decisions
            if name == "hybrid_jev"
            or (name == "fuzzy_jev" and "fuzzy" in d.comparison.methods)
        }
        semantic_correct = semantic_predicted = 0
        touched_clusters, contaminated_clusters = set(), set()
        for item in labelled:
            a, b = tuple(item["left"]), tuple(item["right"])
            yes = membership.get(a) is not None and membership.get(a) == membership.get(
                b
            )
            positive = item["label"] == "same"
            baseline = variants["exact"]["membership"]
            exact_yes = baseline.get(a) is not None and baseline.get(a) == baseline.get(
                b
            )
            predicted += yes
            correct += yes and positive
            positives += positive
            retrieved_positive += positive and tuple(sorted((a, b))) in retrieval_pairs
            contaminated += yes and not positive
            if yes:
                touched_clusters.add(membership[a])
                if not positive:
                    contaminated_clusters.add(membership[a])
            additional += yes and positive and not exact_yes
            semantic_predicted += yes and not exact_yes
            semantic_correct += yes and not exact_yes and positive
        reports[name] = {
            "human_labelled_pairs": len(labelled),
            "predicted_pairs": predicted,
            "precision": correct / predicted if predicted else None,
            "precision_95pct_wilson": wilson(correct, predicted),
            "benchmark_recall": correct / positives if positives else None,
            "retrieval_recall_on_labelled_benchmark": retrieved_positive / positives
            if positives and name != "exact"
            else None,
            "additional_correct_links": additional,
            "contaminating_labelled_pairs": contaminated,
            "clusters_with_labelled_pairs": len(touched_clusters),
            "clusters_with_observed_contamination": len(contaminated_clusters),
            "observed_cluster_contamination_fraction": len(contaminated_clusters)
            / len(touched_clusters)
            if touched_clusters
            else None,
            "semantic_predicted_pairs": semantic_predicted,
            "semantic_precision": semantic_correct / semantic_predicted
            if semantic_predicted
            else None,
            "semantic_precision_95pct_wilson": wilson(
                semantic_correct, semantic_predicted
            ),
        }
    primary_variant = "hybrid_jev" if "hybrid_jev" in reports else "fuzzy_jev"
    score = reports[primary_variant]["semantic_precision"]
    return {
        "batch_id": result["batch_id"],
        "policy_hash": packet["policy_hash"],
        "split": split,
        "variants": reports,
        "primary_variant": primary_variant,
        "meets_observed_precision_target": score >= 0.99 if score is not None else None,
        "status": "experimental",
        "note": "Stratified labelled benchmark metrics, not population precision/recall. Unknown/unreviewed labels excluded. Observed 99% alone does not establish sufficient evidence for promotion.",
    }
