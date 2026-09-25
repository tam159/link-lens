"""Candidate retrieval and constrained cluster assembly over immutable evidence."""

import copy
import re
import uuid
from collections import Counter, defaultdict
from itertools import combinations
from urllib.parse import urlsplit

import numpy as np
from rapidfuzz import fuzz, process

from .contracts import content_hash
from .enhancement_contracts import (
    CandidateComparison,
    ClusterDecision,
    PairDecision,
    VERSION,
    EMBEDDING_VERSION,
)
from .resolution import ELIGIBLE, resolve


def normalize(value):
    return " ".join(re.findall(r"\w+", str(value).casefold()))


def name_key(value):
    return re.sub(
        r"\b(pty|proprietary|limited|ltd|incorporated|inc)\b", "", normalize(value)
    ).strip()


def domain(value):
    try:
        host = urlsplit(value if "://" in value else "https://" + value).hostname or ""
        return host.lower().removeprefix("www.")
    except ValueError:
        return ""


def records_from(observations, candidates):
    records = {
        tuple(c[k] for k in ("source_id", "source_record_id")): {
            **c,
            "observations": [],
        }
        for c in candidates
    }
    for obs in observations:
        ref = (obs["source_id"], obs["source_record_id"])
        if ref in records:
            records[ref]["observations"].append(obs)
    for r in records.values():
        r["observations"].sort(key=lambda o: o["id"])
        r["names"] = sorted(
            {
                str(o["value"])
                for o in r["observations"]
                if o["field"] in {"entity.legal_name", "entity.trading_name"}
            }
            | ({str(r["label"])} if r.get("label") else set())
        )
        r["domains"] = sorted(
            {
                domain(o["value"])
                for o in r["observations"]
                if o["field"] == "entity.website"
            }
            - {""}
        )
        r["addresses"] = [
            {
                "value": o["value"],
                "role": o.get("address_role", "unknown"),
                "id": o["id"],
            }
            for o in r["observations"]
            if o["field"] == "address.full"
        ]
        r["identifiers"] = {
            scheme: sorted(
                {o["value"] for o in r["observations"] if o["field"] == scheme}
            )
            for scheme in ("entity.abn", "entity.acn")
        }
    return records


def evidence_text(record):
    # Label is explicitly not promoted to a legal-name observation.
    return {
        **(
            {
                "ontology_hashes": sorted(
                    {
                        o["ontology_hash"]
                        for o in record["observations"]
                        if o.get("ontology_hash")
                    }
                )
            }
            if any(o.get("ontology_hash") for o in record["observations"])
            else {}
        ),
        "serialization_version": EMBEDDING_VERSION,
        "subject_role": record["subject_role"],
        "source_label": record.get("label"),
        "fields": [
            {k: o.get(k) for k in ("field", "value", "address_role")}
            for o in record["observations"]
            if o["field"]
            in {
                "entity.legal_name",
                "entity.trading_name",
                "entity.website",
                "address.full",
                "address.locality",
                "address.state",
                "address.postcode",
            }
        ],
    }


def frequencies(records):
    result = {}
    for key, values in [
        ("names", lambda r: [name_key(n) for n in r["names"]]),
        ("domains", lambda r: r["domains"]),
        ("addresses", lambda r: [normalize(a["value"]) for a in r["addresses"]]),
    ]:
        result[key] = Counter(v for r in records.values() for v in set(values(r)) if v)
    return result


def field_values(record, field):
    return {
        normalize(o["value"])
        for o in record["observations"]
        if o["field"] == field and normalize(o["value"])
    }


def distinctive(name):
    generic = {
        "australia",
        "australian",
        "services",
        "service",
        "group",
        "company",
        "co",
        "financial",
        "holdings",
        "investments",
        "the",
        "and",
    }
    words = set(name.split()) - generic
    return len(words) >= 2 or any(len(w) >= 8 for w in words)


def evidence_routes(left, right):
    """Potential bilateral support, still subject to model and cluster gates."""
    exact_names = {name_key(n) for n in left["names"]} & {
        name_key(n) for n in right["names"]
    } - {""}
    unique_name = any(distinctive(n) for n in exact_names)
    postcode = bool(
        field_values(left, "address.postcode") & field_values(right, "address.postcode")
    )
    locality = bool(
        field_values(left, "address.locality") & field_values(right, "address.locality")
    )
    state = bool(
        field_values(left, "address.state") & field_values(right, "address.state")
    )
    location_conflict = any(
        field_values(left, f)
        and field_values(right, f)
        and not (field_values(left, f) & field_values(right, f))
        for f in (
            "address.country",
            "address.state",
            "address.postcode",
            "address.locality",
        )
    )
    roles = [
        {
            o.get("address_role", "unknown")
            for o in r["observations"]
            if o["field"].startswith("address.")
        }
        for r in (left, right)
    ]
    nonservice = all(v and v <= {"registered", "business"} for v in roles)
    service = any("service_location" in v for v in roles)
    exact_address = any(
        normalize(a["value"]) == normalize(b["value"])
        for a in left["addresses"]
        for b in right["addresses"]
        if normalize(a["value"])
    )
    routes = []
    if set(left["domains"]) & set(right["domains"]):
        routes.append("entity_domain")
    if any(
        a["role"] == b["role"] and a["role"] in {"registered", "business"}
        for a in left["addresses"]
        for b in right["addresses"]
    ):
        routes.append("compatible_full_address")
    if (
        unique_name
        and postcode
        and locality
        and state
        and nonservice
        and not location_conflict
    ):
        routes.append("distinctive_name_and_location")
    if (
        unique_name
        and exact_address
        and postcode
        and service
        and not location_conflict
        and all(
            v and v <= {"registered", "business", "service_location"} for v in roles
        )
    ):
        routes.append("service_name_full_address_postcode")
    # Alias evidence must be explicitly co-stated by a source, not invented by a model.
    explicit_alias = any(
        field_values(r, "entity.legal_name") and field_values(r, "entity.trading_name")
        for r in (left, right)
    )
    if (
        explicit_alias
        and unique_name
        and postcode
        and locality
        and state
        and nonservice
        and not location_conflict
    ):
        routes.append("explicit_alias_and_location")
    return {
        "admission_routes": routes,
        "exact_name": bool(exact_names),
        "distinctive_exact_name": unique_name,
        "matching_postcode": postcode,
        "matching_locality": locality,
        "matching_state": state,
        "location_conflict": location_conflict,
        "service_location_present": service,
        "name_only_is_review_evidence": True,
    }


def comparison(a, b, records, freq, methods=None, scores=None):
    a, b = sorted((a, b))
    left, right = records[a], records[b]
    domains = sorted(set(left["domains"]) & set(right["domains"]))
    address_pairs = [
        (x, y)
        for x in left["addresses"]
        for y in right["addresses"]
        if x["role"] == y["role"] and x["role"] in {"registered", "business"}
    ]
    values = {
        "domains": left["domains"] + right["domains"],
        "names": [name_key(n) for n in left["names"] + right["names"]],
        "addresses": [
            normalize(x["value"]) for x in left["addresses"] + right["addresses"]
        ],
    }
    features = {
        "shared_domains": domains,
        "compatible_full_address_available": bool(address_pairs),
        "exact_full_address": any(
            normalize(x["value"]) == normalize(y["value"]) for x, y in address_pairs
        ),
        "weak_location_is_not_corroboration": True,
        "value_frequencies": {
            k: {v: freq[k][v] for v in sorted(set(vs)) if v} for k, vs in values.items()
        },
    }
    features.update(evidence_routes(left, right))
    features["repeated_value_flags"] = {
        k: any(n > 2 for n in values.values())
        for k, values in features["value_frequencies"].items()
    }
    evidence = {"left": left, "right": right, "features": features}
    return CandidateComparison(
        id=content_hash([a, b]),
        left=a,
        right=b,
        methods=methods or [],
        scores=scores or {},
        evidence_hash=content_hash(evidence),
        features=features,
    )


def retrieve(
    records,
    vectors=None,
    top_k=20,
    fuzzy_floor=0.0,
    embedding_floor=-1.0,
    progress=None,
):
    """Bounded-memory cosine search plus lexical retrieval, per other source."""
    vectors = vectors or {}
    refs = sorted(records)
    by_source = defaultdict(list)
    for ref in refs:
        by_source[ref[0]].append(ref)
    pairs = {}
    freq = frequencies(records)
    for source, targets in sorted(by_source.items()):
        vrefs = [r for r in targets if r in vectors]
        matrix = np.asarray([vectors[r] for r in vrefs], dtype=np.float32)
        aliases = [
            (name_key(name), ref)
            for ref in targets
            for name in records[ref]["names"]
            if name_key(name)
        ]
        alias_names = [name for name, _ in aliases]
        if progress:
            progress(
                "retrieval",
                source=source,
                sources=len(by_source),
                message="Scanning cross-source names and vectors",
            )
        for ref in refs:
            if ref[0] == source or not records[ref]["names"]:
                continue
            lexical_scores = {}
            for name in records[ref]["names"]:
                key = name_key(name)
                if not key:
                    continue
                # All alias scores are computed in native code; then reduce to records.
                for _, score, index in process.extract(
                    key,
                    alias_names,
                    scorer=fuzz.ratio,
                    limit=None,
                    score_cutoff=max(1, fuzzy_floor * 100),
                ):
                    other = aliases[index][1]
                    lexical_scores[other] = max(
                        lexical_scores.get(other, 0), score / 100
                    )
            rankings = {
                "fuzzy": sorted(
                    ((score, other) for other, score in lexical_scores.items()),
                    key=lambda x: (-x[0], x[1]),
                )[:top_k]
            }
            if ref in vectors and vrefs:
                scores = matrix @ np.asarray(vectors[ref], dtype=np.float32)
                rankings["embedding"] = sorted(
                    (
                        (float(score), ref)
                        for score, ref in zip(scores, vrefs)
                        if score >= embedding_floor
                    ),
                    key=lambda x: (-x[0], x[1]),
                )[:top_k]
            for method, ranked in rankings.items():
                for score, other in ranked:
                    pair = tuple(sorted((ref, other)))
                    item = pairs.setdefault(pair, {"methods": set(), "scores": {}})
                    item["methods"].add(method)
                    item["scores"][method] = score
    return [
        comparison(a, b, records, freq, sorted(v["methods"]), v["scores"])
        for (a, b), v in sorted(pairs.items())
    ]


def hard_block(left, right):
    if left["subject_role"] not in ELIGIBLE or right["subject_role"] not in ELIGIBLE:
        return "Ineligible or ambiguous subject ownership"
    for scheme in ("entity.abn", "entity.acn"):
        if (
            len(set(left["identifiers"][scheme]) | set(right["identifiers"][scheme]))
            > 1
        ):
            return "Conflicting validated identifiers"
    return None


def gate(comp, records, judgment, policy, artifact=None):
    reason = hard_block(records[comp.left], records[comp.right])
    if reason:
        return PairDecision(comparison=comp, status="blocked", reason=reason)
    features = comp.features
    supported = bool(features.get("admission_routes"))
    other = max(v for k, v in judgment.probabilities.items() if k != "same_entity")
    passed = (
        supported
        and judgment.choice == "same_entity"
        and judgment.probabilities["same_entity"] >= policy.threshold
        and judgment.probabilities["same_entity"] - other >= policy.margin
        and min(
            judgment.names_compatible, judgment.corroborated, judgment.ownership_clear
        )
        >= policy.threshold
    )
    return PairDecision(
        comparison=comp,
        status="eligible" if passed else "deferred",
        reason="Identity and independent corroboration gates passed"
        if passed
        else (
            "Review candidate: no independent bilateral evidence route"
            if not supported
            else "Insufficient identity, corroboration, or ownership evidence"
        ),
        judgment=judgment,
        response_artifact=artifact,
    )


def components(nodes, edges):
    neighbors = defaultdict(set)
    for a, b in edges:
        neighbors[a].add(b)
        neighbors[b].add(a)
    remaining = set(nodes)
    while remaining:
        todo = [min(remaining)]
        group = set()
        while todo:
            ref = todo.pop()
            if ref in group:
                continue
            group.add(ref)
            todo.extend(neighbors[ref] - group)
        remaining -= group
        yield sorted(group)


def cluster(records, decisions, existing_entities=None, namespace="default"):
    observations = [o for r in records.values() for o in r["observations"]]
    candidates = [
        {
            k: r[k]
            for k in (
                "source_id",
                "source_record_id",
                "subject_role",
                "label",
                "raw_locator",
            )
        }
        for r in records.values()
    ]
    exact = resolve(observations, candidates, existing_entities)
    # Resolve explicit prior membership before adopting newly discovered identifiers.
    prior_members = defaultdict(set)
    existing_ids = {e["id"] for e in existing_entities or []}
    for e in existing_entities or []:
        for ref in e.get("records", []):
            prior_members[tuple(ref)].add(e["id"])
    entities = []
    preblocked = set()
    prior_reviews = []
    for original in exact["entities"]:
        entity = copy.deepcopy(original)
        refs = [tuple(r) for r in entity["records"]]
        priors = set().union(*(prior_members[r] for r in refs))
        if entity["id"] in existing_ids:
            priors.add(entity["id"])
        if len(priors) > 1:
            preblocked.update(refs)
            prior_reviews.append(
                ClusterDecision(
                    records=refs,
                    status="deferred",
                    reason="Exact evidence would join existing entity IDs; explicit review required",
                )
            )
            continue
        if priors:
            entity["id"] = entity["canonical_entity_key"] = next(iter(priors))
        entities.append(entity)
    membership = {tuple(r): e["id"] for e in entities for r in e["records"]}
    exact["links"] = [
        {**link, "canonical_entity_key": membership[tuple(link["source_a_record"])]}
        for link in exact["links"]
        if tuple(link["source_a_record"]) in membership
    ]
    for link in exact["links"]:
        if link["canonical_entity_key"] != next(
            (
                e["id"]
                for e in exact["entities"]
                if link["source_a_record"] in e["records"]
            ),
            None,
        ):
            link["id"] = content_hash({k: v for k, v in link.items() if k != "id"})
    blocked = {
        (u["source_id"], u["source_record_id"])
        for u in exact["unlinked"]
        if "conflict" in u["reason"].lower()
        or "ownership" in u["reason"].lower()
        or "multiple existing" in u["reason"]
    }
    blocked |= preblocked
    eligible = {
        tuple(sorted((d.comparison.left, d.comparison.right))): d
        for d in decisions
        if d.status == "eligible"
        and d.comparison.left not in blocked
        and d.comparison.right not in blocked
    }
    # Connect exact members as anchors, but never let semantic chains join anchors.
    edges = list(eligible)
    for e in entities:
        refs = [tuple(r) for r in e["records"]]
        edges.extend((refs[0], r) for r in refs[1:])
    cluster_decisions = list(prior_reviews)
    semantic_links = []
    for group in components(records, edges):
        added = [r for r in group if r not in membership]
        if len({r[0] for r in group}) < 2:
            continue
        anchors = {membership[r] for r in group if r in membership}
        if not added and len(anchors) < 2:
            continue
        priors = set().union(*(prior_members[r] for r in group)) | anchors
        reason = None
        if len(priors) > 1:
            reason = "Would join multiple existing entity IDs; explicit membership review required"
        elif any(hard_block(records[a], records[b]) for a, b in combinations(group, 2)):
            reason = "Cluster has identifier or ownership conflicts"
        elif anchors:
            original = [r for r in group if r in membership]
            if any(
                not any(tuple(sorted((r, a))) in eligible for a in original)
                for r in added
            ):
                reason = "No direct support from an original identifier cluster record"
        elif any(
            tuple(sorted((a, b))) not in eligible
            for a, b in combinations(group, 2)
            if a[0] != b[0]
        ):
            reason = "Incomplete cross-source pairwise consistency; no transitive merge"
        pair_ids = [
            d.comparison.id for p, d in eligible.items() if set(p).issubset(group)
        ]
        if reason:
            cluster_decisions.append(
                ClusterDecision(
                    records=group, status="deferred", reason=reason, pair_ids=pair_ids
                )
            )
            continue
        eid = (
            next(iter(priors))
            if priors
            else str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    "link-lens:semantic:" + namespace + ":" + content_hash(group),
                )
            )
        )
        entity = next((e for e in entities if e["id"] == eid), None)
        if entity is None:
            entity = {
                "id": eid,
                "canonical_entity_key": eid,
                "identifiers": {},
                "records": [],
                "identity_rule_version": VERSION,
                "status": "provisional_semantic_cluster",
            }
            entities.append(entity)
        entity["records"] = [list(r) for r in group]
        entity["identifiers"] = {
            k: sorted({v for r in group for v in records[r]["identifiers"][k]})
            for k in ("entity.abn", "entity.acn")
            if any(records[r]["identifiers"][k] for r in group)
        }
        entity["identity_rule_version"] = VERSION
        entity["status"] = "provisional_semantic_cluster"
        for r in group:
            membership[r] = eid
        cluster_decisions.append(
            ClusterDecision(
                records=group,
                status="admitted",
                reason="Consistent, corroborated semantic membership",
                entity_id=eid,
                pair_ids=pair_ids,
            )
        )
        for pair, d in eligible.items():
            if set(pair).issubset(group) and any(r in added for r in pair):
                link = {
                    "source_a_record": list(pair[0]),
                    "source_b_record": list(pair[1]),
                    "canonical_entity_key": eid,
                    "confidence": d.judgment.probabilities["same_entity"],
                    "confidence_kind": "uncalibrated model score",
                    "rule_version": VERSION,
                    "status": "proposed_unreviewed",
                    "human_review_status": "unreviewed",
                    "evidence_kind": "semantic_model",
                    "evidence": d.model_dump(mode="json"),
                }
                link["id"] = content_hash(link)
                semantic_links.append(link)
    links = [
        {
            **link,
            "evidence_kind": "exact_identifier",
            "human_review_status": "unreviewed",
        }
        for link in exact["links"]
    ] + semantic_links
    unlinked = []
    reasons = {
        r: d.reason
        for d in cluster_decisions
        if d.status == "deferred"
        for r in d.records
    }
    for ref, r in sorted(records.items()):
        if ref not in membership:
            unlinked.append(
                {
                    **{
                        k: r[k]
                        for k in (
                            "source_id",
                            "source_record_id",
                            "label",
                            "raw_locator",
                        )
                    },
                    "reason": reasons.get(
                        ref,
                        "No admitted counterpart; inspect candidate decisions including pending work",
                    ),
                }
            )
    return {
        "entities": entities,
        "links": links,
        "membership": membership,
        "unlinked": unlinked,
        "cluster_decisions": [d.model_dump(mode="json") for d in cluster_decisions],
    }
