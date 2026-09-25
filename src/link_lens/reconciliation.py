"""Evidence-preserving model-assisted equivalence and conflict annotations."""

from collections import defaultdict
from itertools import combinations

from .contracts import content_hash
from .enhancement_contracts import ReconciliationDecision, VERSION
from .enhancement_models import PendingInference
from .profiles import assemble_profiles, claim, field_result, rank
from .semantic_resolution import components

EQUIVALENCE_FIELDS = {
    "entity.legal_name",
    "entity.trading_name",
    "entity.website",
    "address.full",
}


def reconcile_profiles(observations, entities, inference, policy):
    profiles = assemble_profiles(observations, entities)
    by_record = defaultdict(list)
    for o in observations:
        by_record[(o["source_id"], o["source_record_id"])].append(o)
    for index, (profile, entity) in enumerate(zip(profiles, entities)):
        if getattr(inference, "progress", None):
            inference.progress("profiles", completed=index, total=len(profiles))
        semantic = entity.get("identity_rule_version") == VERSION
        profile["identity_basis"] = (
            "includes_semantic_model_links" if semantic else "exact_identifier"
        )
        if semantic:
            profile["status"] = "provisional_profile_from_semantic_links"
            profile["uncertainties"][0] = (
                "Identity includes unreviewed model proposals; model scores are uncalibrated."
            )
        if not policy.reconcile:
            profile["profile_version"] = content_hash(
                {k: v for k, v in profile.items() if k != "profile_version"}
            )
            continue
        groups = defaultdict(list)
        for ref in entity["records"]:
            for o in by_record[tuple(ref)]:
                if o.get("group_id"):
                    continue  # Scoped bundles remain intact; never reconcile across subjects/periods.
                groups[
                    (
                        o["field"],
                        o.get("address_role", "unknown")
                        if o["field"].startswith("address.")
                        else "entity",
                    )
                ].append(o)
        decisions = []
        equivalences = []
        annotations = []
        for (field, role), obs in sorted(groups.items()):
            variants = defaultdict(list)
            for o in obs:
                variants[o["value"]].append(o)
            if len(variants) < 2:
                continue
            edges = set()
            if field in EQUIVALENCE_FIELDS:
                for a, b in combinations(sorted(variants), 2):
                    support = variants[a] + variants[b]
                    evidence = {
                        "field": field,
                        "role": role,
                        "left": variants[a],
                        "right": variants[b],
                    }
                    try:
                        result, artifact = inference.equivalent(evidence)
                        passed = result.equivalent >= policy.threshold
                        decision = ReconciliationDecision(
                            field=field,
                            observation_ids=[o["id"] for o in support],
                            status="equivalent" if passed else "distinct",
                            score=result.equivalent,
                            response_artifact=artifact,
                        )
                        if passed:
                            edges.add((a, b))
                    except PendingInference:
                        decision = ReconciliationDecision(
                            field=field,
                            observation_ids=[o["id"] for o in support],
                            status="pending",
                        )
                    decisions.append(decision.model_dump(mode="json"))
            remap = {}
            for group in components(variants, edges):
                if len(group) < 2 or any(
                    tuple(sorted((a, b))) not in edges
                    for a, b in combinations(group, 2)
                ):
                    continue
                originals = [o for v in group for o in variants[v]]
                # Representative is a source value, never model-authored text.
                representative = max(originals, key=lambda o: (rank(o), o["value"]))[
                    "value"
                ]
                equivalences.append(
                    {
                        "field": field,
                        "role": role,
                        "values": group,
                        "representative": representative,
                        "observations": [claim(o) for o in originals],
                        "derivation_level": "L3",
                        "decision": "Pairwise model equivalence; representative selected by evidence policy.",
                    }
                )
                remap.update({value: representative for value in group})
            if remap and not field.startswith("address."):
                projected = [
                    {**o, "value": remap.get(o["value"], o["value"])} for o in obs
                ]
                result = field_result(projected, field == "entity.trading_name")
                originals = {o["id"]: o for o in obs}

                def restore(value):
                    if isinstance(value, dict):
                        if "id" in value and value["id"] in originals:
                            value.update(claim(originals[value["id"]]))
                        else:
                            for v in value.values():
                                restore(v)
                    elif isinstance(value, list):
                        for v in value:
                            restore(v)

                restore(result)
                result["equivalence_basis"] = (
                    "Model-inferred equivalence; all source values retained in provenance and equivalence groups."
                )
                profile["fields"][field] = result
            # Address groups annotate equivalence only; never combine or replace bundles.
            unresolved = profile["fields"].get(field, {}).get("status") == "unresolved"
            if field.startswith("address."):
                unresolved = len({remap.get(v, v) for v in variants}) > 1
            if unresolved:
                try:
                    annotation, artifact = inference.explain(obs)
                    annotations.append(
                        {
                            "field": field,
                            "role": role,
                            **annotation.model_dump(),
                            "response_artifact": artifact,
                            "derivation_level": "L3",
                        }
                    )
                except PendingInference:
                    annotations.append(
                        {
                            "field": field,
                            "role": role,
                            "outcome": "insufficient_evidence",
                            "status": "pending",
                            "explanation": "No validated model annotation available.",
                            "observation_ids": [o["id"] for o in obs],
                        }
                    )
        profile["reconciliation"] = {
            "version": VERSION,
            "decisions": decisions,
            "equivalence_groups": equivalences,
            "conflicts": annotations,
        }
        profile["policy_version"] += "+" + VERSION
        profile["profile_version"] = content_hash(
            {k: v for k, v in profile.items() if k != "profile_version"}
        )
    return profiles
