"""Conservative, versioned identifier evidence. No fuzzy or LLM identity decisions."""

import uuid
from collections import defaultdict
from .contracts import content_hash

RULE_VERSION = "identifier-evidence-1"
ELIGIBLE = {
    "legal_entity",
    "business_name_holder",
    "licence_holder",
    "service_provider",
    "supplier",
}


def resolve(observations, candidates, existing_entities=None):
    known = defaultdict(set)
    for entity in existing_entities or []:
        for scheme, values in entity["identifiers"].items():
            for value in values:
                known[(scheme, value)].add(entity["id"])
    records = {}
    for candidate in candidates:
        ref = (candidate["source_id"], candidate["source_record_id"])
        records[ref] = {
            **candidate,
            "identifiers": defaultdict(set),
            "observations": [],
        }
    for obs in observations:
        ref = (obs["source_id"], obs["source_record_id"])
        if ref not in records:
            continue
        records[ref]["observations"].append(obs)
        if obs["field"] in {"entity.abn", "entity.acn"}:
            records[ref]["identifiers"][obs["field"]].add(obs["value"])
    groups = defaultdict(list)
    blocked = {}
    unlinked = []
    for ref, record in records.items():
        if record["subject_role"] not in ELIGIBLE:
            blocked[ref] = (
                "Unknown/group subject role; identity ownership not established"
            )
            continue
        if any(len(v) > 1 for v in record["identifiers"].values()):
            blocked[ref] = "Conflicting same-scheme identifiers inside one subject"
            continue
        for scheme, values in record["identifiers"].items():
            for value in values:
                groups[(scheme, value)].append(ref)
    # Reject every member of a contradictory identifier block, rather than letting
    # iteration order decide which company absorbs an ambiguous bridge record.
    for key, refs in groups.items():
        schemes = defaultdict(set)
        for ref in refs:
            for scheme, values in records[ref]["identifiers"].items():
                schemes[scheme].update(values)
        if any(len(v) > 1 for v in schemes.values()):
            for ref in refs:
                blocked[ref] = (
                    "Shared identifier block contains conflicting identifiers; manual investigation required"
                )
    parent = {ref: ref for ref in records}
    identifiers = {
        ref: {k: set(v) for k, v in r["identifiers"].items()}
        for ref, r in records.items()
    }

    def root(ref):
        while parent[ref] != ref:
            parent[ref] = parent[parent[ref]]
            ref = parent[ref]
        return ref

    for _, refs in sorted(groups.items()):
        refs = [r for r in refs if r not in blocked]
        if not refs:
            continue
        for ref in refs[1:]:
            a, b = root(refs[0]), root(ref)
            if a == b:
                continue
            combined = {
                k: identifiers[a].get(k, set()) | identifiers[b].get(k, set())
                for k in identifiers[a].keys() | identifiers[b].keys()
            }
            if any(len(v) > 1 for v in combined.values()):
                continue
            parent[b] = a
            identifiers[a] = combined
    clusters = defaultdict(list)
    for ref in records:
        if ref not in blocked:
            clusters[root(ref)].append(ref)
    links = []
    entities = []
    membership = {}
    for refs in clusters.values():
        refs = sorted(refs)
        if len({r[0] for r in refs}) < 2:
            for ref in refs:
                blocked[ref] = (
                    "No cross-source counterpart in processed sample"
                    if records[ref]["identifiers"]
                    else "No validated ABN/ACN; name-only matching disabled"
                )
            continue
        ids = identifiers[root(refs[0])]
        identity = next(
            (
                f"{scheme}:{sorted(ids[scheme])[0]}"
                for scheme in ["entity.abn", "entity.acn"]
                if ids.get(scheme)
            ),
            None,
        )
        if identity is None:
            continue
        prior = {
            eid
            for scheme, values in ids.items()
            for value in values
            for eid in known[(scheme, value)]
        }
        if len(prior) > 1:
            for ref in refs:
                blocked[ref] = (
                    "Would join multiple existing entity IDs; explicit membership review required"
                )
            continue
        entity_id = (
            next(iter(prior))
            if prior
            else str(uuid.uuid5(uuid.NAMESPACE_URL, "link-lens:" + identity))
        )
        entity = {
            "id": entity_id,
            "canonical_entity_key": entity_id,
            "identifiers": {k: sorted(v) for k, v in ids.items()},
            "records": [list(r) for r in refs],
            "identity_rule_version": RULE_VERSION,
            "status": "proposed_identity_cluster",
        }
        entities.append(entity)
        for ref in refs:
            membership[ref] = entity_id
        # Direct cross-source evidence only. Avoid materialising the quadratic
        # complete graph when many aliases/licences refer to one legal entity.
        seen_edges = set()
        for key in sorted(
            (scheme, value) for scheme, values in ids.items() for value in values
        ):
            ref_set = set(refs)
            members = [r for r in groups[key] if r in ref_set]
            by_source = defaultdict(list)
            for ref in members:
                by_source[ref[0]].append(ref)
            if len(by_source) < 2:
                continue
            anchors = [sorted(v)[0] for _, v in sorted(by_source.items())]
            for ref in members:
                anchor = next(a for a in anchors if a[0] != ref[0])
                pair = tuple(sorted([anchor, ref]))
                if pair in seen_edges:
                    continue
                seen_edges.add(pair)
                evidence = {
                    "rule": "exact_validated_identifier",
                    "identifier_type": key[0],
                    "identifier": key[1],
                    "subject_roles": [records[r]["subject_role"] for r in pair],
                    "labels": [records[r].get("label") for r in pair],
                    "raw_locators": [records[r]["raw_locator"] for r in pair],
                }
                link = {
                    "source_a_record": list(pair[0]),
                    "source_b_record": list(pair[1]),
                    "canonical_entity_key": entity_id,
                    "confidence": 0.99,
                    "confidence_kind": "uncalibrated rule score",
                    "threshold": 0.99,
                    "evidence": evidence,
                    "rule_version": RULE_VERSION,
                    "status": "proposed_unreviewed",
                }
                link["id"] = content_hash(link)
                links.append(link)
    for ref, reason in sorted(blocked.items()):
        unlinked.append(
            {
                "source_id": ref[0],
                "source_record_id": ref[1],
                "label": records[ref].get("label"),
                "reason": reason,
                "raw_locator": records[ref]["raw_locator"],
            }
        )
    return {
        "entities": entities,
        "links": links,
        "unlinked": unlinked,
        "membership": membership,
    }
