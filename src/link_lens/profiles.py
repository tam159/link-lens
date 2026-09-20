from collections import defaultdict
from .contracts import content_hash
from .resolution import resolve

POLICY_VERSION = "field-authority-1"
AUTHORITY = {
    "entity.legal_name": {
        "company_register": 100,
        "charity_register": 90,
        "tax_disclosure": 80,
        "licence_register": 70,
    },
    "entity.trading_name": {"business_name_register": 100},
    "entity.date_registered": {"company_register": 100},
    "entity.entity_type": {"company_register": 100},
    "entity.status": {"company_register": 100},
}


def rank(obs):
    authority = AUTHORITY.get(obs["field"], {}).get(obs["source_kind"], 50)
    # Source publication proxies are lower temporal evidence than record statements.
    # Do not break semantic ties using model confidence or alphabetic publisher IDs.
    temporal = 2 if obs["observed_at_basis"] == "source record statement field" else 1
    return authority, temporal, obs["observed_at"]


def claim(obs):
    return {
        k: obs[k]
        for k in [
            "id",
            "source_id",
            "source_record_id",
            "value",
            "observed_at",
            "observed_at_basis",
            "confidence",
            "raw_locator",
        ]
    }


def field_result(observations, multiple=False):
    variants = defaultdict(list)
    for o in observations:
        variants[o["value"]].append(o)
    options = []
    for value, claims in variants.items():
        strongest = max(claims, key=rank)
        options.append(
            {
                "value": value,
                "confidence": strongest["confidence"],
                "provenance": [claim(o) for o in claims],
                "authority_rank": rank(strongest),
            }
        )
    options.sort(key=lambda x: (x["authority_rank"], x["value"]), reverse=True)
    if multiple:
        return {
            "status": "multiple_values",
            "values": options,
            "decision": "Trading names are multi-valued; no winner is forced.",
        }
    best = options[0]
    tied = [o for o in options if o["authority_rank"] == best["authority_rank"]]
    if len(tied) > 1:
        return {
            "status": "unresolved",
            "alternatives": options,
            "decision": "Equally authoritative and equally dated conflicting claims; no selected value.",
        }
    return {
        "status": "selected",
        "value": best["value"],
        "confidence": best["confidence"],
        "provenance": best["provenance"],
        "alternatives": options[1:],
        "decision": "Field-specific publisher role, then statement-vs-publication evidence, then most recent timestamp.",
        "temporal_caveat": "Publication time does not prove when this field changed.",
    }


def assemble_profiles(observations, entities):
    by_record = defaultdict(list)
    for o in observations:
        by_record[(o["source_id"], o["source_record_id"])].append(o)
    profiles = []
    for entity in entities:
        fields = defaultdict(list)
        addresses = []
        for ref in entity["records"]:
            claims = by_record[tuple(ref)]
            address = {}
            for o in claims:
                if o["field"].startswith("address."):
                    address[o["field"]] = field_result([o])
                else:
                    fields[o["field"]].append(o)
            if address:
                first = next(o for o in claims if o["field"].startswith("address."))
                addresses.append(
                    {
                        "role": first["address_role"],
                        "source_id": ref[0],
                        "source_record_id": ref[1],
                        "fields": address,
                        "decision": "Keep source address fields together; no inferred headquarters address.",
                    }
                )
        profile = {
            "canonical_entity_key": entity["id"],
            "status": "profile_from_proposed_links",
            "policy_version": POLICY_VERSION,
            "fields": {
                field: field_result(claims, field == "entity.trading_name")
                for field, claims in sorted(fields.items())
            },
            "source_records": entity["records"],
            "uncertainties": [
                "Identity links are rule proposals; manual precision is measured separately.",
                "Confidence components are uncalibrated.",
            ],
        }
        if addresses:
            profile["addresses"] = addresses
        profile["profile_version"] = content_hash(profile)
        profiles.append(profile)
    return profiles


def values_only(profile):
    return {
        "fields": {
            k: (
                {"value": v["value"]}
                if "value" in v
                else {
                    "values": [
                        x["value"] for x in v.get("values", v.get("alternatives", []))
                    ],
                    "status": v["status"],
                }
            )
            for k, v in profile["fields"].items()
        },
        "addresses": [
            {
                "role": a["role"],
                "values": {k: v.get("value") for k, v in a["fields"].items()},
            }
            for a in profile.get("addresses", [])
        ],
    }


def impact(observations, candidates, entities, profiles):
    reports = []
    baseline = {p["canonical_entity_key"]: p for p in profiles}
    for source in sorted({o["source_id"] for o in observations}):
        remaining = [o for o in observations if o["source_id"] != source]
        fixed = assemble_profiles(remaining, entities)
        rerun = resolve(remaining, [c for c in candidates if c["source_id"] != source])
        no_support = 0
        membership_changes = 0
        for entity in entities:
            refs = [tuple(r) for r in entity["records"] if r[0] != source]
            new_ids = {rerun["membership"].get(ref) for ref in refs}
            if not any(x is not None for x in new_ids):
                no_support += 1
            if len(new_ids) > 1 or None in new_ids:
                membership_changes += 1
        reports.append(
            {
                "removed_source_id": source,
                "profiles_with_value_changes": sum(
                    values_only(p) != values_only(baseline[p["canonical_entity_key"]])
                    for p in fixed
                ),
                "profiles_with_provenance_changes": sum(
                    p["fields"] != baseline[p["canonical_entity_key"]]["fields"]
                    or p.get("addresses")
                    != baseline[p["canonical_entity_key"]].get("addresses")
                    for p in fixed
                ),
                "profiles_without_remaining_cross_source_support": no_support,
                "profiles_with_changed_membership_support": membership_changes,
                "scope": "Values recomputed with original memberships; identity support separately re-resolved without removed source.",
            }
        )
    return reports
