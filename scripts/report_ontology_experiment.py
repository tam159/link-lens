"""Compare preserved exports without inference, labels, or submission mutations."""

import argparse
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

from link_lens.ontology import digest, legacy
from link_lens.profiles import values_only


def read(path):
    return json.loads(path.read_text())


def rows(path):
    stream = path.open() if path.exists() else gzip.open(str(path) + ".gz", "rt")
    with stream:
        return [json.loads(line) for line in stream if line.strip()]


def references(value):
    if isinstance(value, dict):
        if "raw_locator" in value and "id" in value:
            yield value["id"]
        for child in value.values():
            yield from references(child)
    elif isinstance(value, list):
        for child in value:
            yield from references(child)


def report(root, submission):
    if root.resolve() == submission.resolve():
        raise ValueError("Choose a separate experimental output directory")
    manifest = read(root / "manifest.json")
    ontology_hash = manifest["ontology_hash"]
    document = read(root / "baseline/ontologies" / f"{ontology_hash}.json")
    assert digest(document) == ontology_hash
    new = set(document["concepts"]) - set(legacy()["concepts"])
    coverage = {
        name: {
            "new_concept": name in new,
            "scope": concept["scope"],
            "type": concept["type"],
            "mapped_sources": [],
        }
        for name, concept in document["concepts"].items()
    }
    for source in read(root / "baseline/ontology-coverage.json")["sources"]:
        for target in source["targets"]:
            coverage[target]["mapped_sources"].append(source["source"])
    variants = {}
    checks = {}
    profile_values = {}
    for name, directory in [
        ("preserved_submission", submission),
        ("baseline", root / "baseline"),
        ("enhanced", root / "enhanced"),
    ]:
        observations = rows(directory / "observations.jsonl")
        profiles = rows(directory / "profiles.jsonl")
        profile_values[name] = {
            p["canonical_entity_key"]: values_only(p) for p in profiles
        }
        ids = {o["id"]: o for o in observations}
        emitted = Counter(o["field"] for o in observations)
        contributed = Counter()
        by_source = Counter()
        cited = set()
        for profile in profiles:
            refs = set(references(profile))
            assert refs <= ids.keys(), "Profile contains unknown observation IDs"
            cited.update(refs)
            contributed.update({ids[key]["field"] for key in refs})
            by_source.update({ids[key]["source_id"] for key in refs})
        variants[name] = {
            "observations": len(observations),
            "unique_observation_ids": len(ids),
            "repeated_identical_observations": len(observations) - len(ids),
            "links": len(rows(directory / "links.jsonl")),
            "profiles": len(profiles),
            "unlinked_records": len(rows(directory / "unlinked.jsonl")),
            "emitted_concepts": len(emitted),
            "concepts_contributing_to_profiles": len(contributed),
            "sources_contributing_to_profiles": sum(v > 0 for v in by_source.values()),
            "sources": [
                {
                    "source": source["slug"],
                    "observations": sum(
                        o["source_id"] == source["source_id"] for o in observations
                    ),
                    "profiles_receiving_evidence": by_source[source["source_id"]],
                }
                for source in manifest["sources"]
            ],
        }
        if name == "preserved_submission":
            continue
        assert all(o.get("ontology_hash") == ontology_hash for o in observations)
        assert all(ids[o["id"]] == o for o in observations), (
            "Conflicting observation IDs"
        )
        groups = defaultdict(set)
        for obs in observations:
            if obs.get("group_id"):
                groups[obs["group_id"]].add(
                    (obs["source_id"], obs["source_record_id"], obs["scope"])
                )
        assert all(len(subjects) == 1 for subjects in groups.values())
        for field, item in coverage.items():
            item[name] = {
                "observations": emitted[field],
                "profiles_receiving_evidence": contributed[field],
                "cited_observations": sum(ids[key]["field"] == field for key in cited),
            }
        variants[name]["new_concepts_emitted"] = len(new & emitted.keys())
        variants[name]["new_concepts_contributing_to_profiles"] = len(
            new & contributed.keys()
        )
        checks[name] = {
            "observation_ids_have_identical_content": True,
            "all_observations_pinned_to_ontology": True,
            "profile_observation_references_resolve": True,
            "groups_have_single_source_record_and_scope": True,
            "observation_groups": len(groups),
            "okf": read(directory / "export-manifest.json")["okf"],
        }
        assert checks[name]["okf"]["broken_links"] == 0
    assert variants["baseline"]["observations"] == variants["enhanced"]["observations"]
    assert read(root / "baseline/selection.json") == read(
        root / "enhanced/selection.json"
    )
    changed = sum(
        value != profile_values["enhanced"][key]
        for key, value in profile_values["baseline"].items()
        if key in profile_values["enhanced"]
    )
    assert (
        read(root / "enhanced/comparison.json")["existing_profiles_with_value_changes"]
        == changed
    )
    result = {
        "experiment_id": manifest["experiment_id"],
        "ontology_hash": ontology_hash,
        "accepted_new_concepts": len(new),
        "mapped_new_concepts": sum(bool(coverage[n]["mapped_sources"]) for n in new),
        "existing_profiles_with_value_changes_after_enhancement": changed,
        "variants": variants,
        "comparison_limits": [
            "Preserved submission comparison changes model, ontology, mappings, cohort and four snapshots; it is not a causal ontology benchmark.",
            "Baseline versus enhanced uses the same approved mappings, observations and selected records.",
            "Contribution includes source evidence retained as alternatives; it is not human-verified accuracy or population recall.",
        ],
    }
    for filename, value in [
        ("comparison.json", result),
        ("concept-coverage.json", coverage),
        ("verification.json", checks),
    ]:
        (root / filename).write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument(
        "--submission",
        type=Path,
        default=Path("experiments/jev-luna-v1-submission/outputs"),
    )
    args = parser.parse_args()
    report(args.root, args.submission)
