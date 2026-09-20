"""Measure new-source evidence in a completed batch; never create links or labels."""

import argparse
import json
from pathlib import Path
from link_lens import store


def source_ids(value):
    if isinstance(value, dict):
        found = {value["source_id"]} if "source_id" in value else set()
        return found.union(*(source_ids(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(source_ids(v) for v in value))
    return set()


def compare(baseline, result, source_id):
    old = {p["canonical_entity_key"]: p for p in baseline["profiles"]}
    new = {p["canonical_entity_key"]: p for p in result["profiles"]}
    receiving = sorted(k for k, p in new.items() if source_id in source_ids(p))
    existing_receiving = sorted(set(receiving) & old.keys())
    links = [
        l
        for l in result["links"]
        if source_id in [l["source_a_record"][0], l["source_b_record"][0]]
    ]
    return {
        "baseline_batch_id": baseline["batch_id"],
        "batch_id": result["batch_id"],
        "source_id": source_id,
        "total_links": len(result["links"]),
        "links_involving_new_source": len(links),
        "profiles_receiving_evidence": len(receiving),
        "existing_profiles_receiving_evidence": len(existing_receiving),
        "existing_entity_ids_receiving_evidence": existing_receiving,
        "baseline_profiles_retained": len(old.keys() & new.keys()),
        "baseline_profiles": len(old),
        "note": "Evidence includes selected claims and alternatives; this does not imply a winning value changed or independent publisher corroboration.",
        "success": bool(existing_receiving and links and old.keys() <= new.keys()),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-batch-id", required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    read = lambda key: store.read_json(store.require("batches", key)["result_artifact"])
    report = compare(read(args.baseline_batch_id), read(args.batch_id), args.source_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not report["success"]:
        raise SystemExit(
            "Demo contribution not established. Inspect config, roles, filters, identifiers, pool coverage and unlinked reasons; do not claim success."
        )
