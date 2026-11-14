"""Deterministic submissions and OKF dossiers; no narrative-model rewriting."""

import json
import re
from pathlib import Path

from . import store
from ._vendor.okf.bundle.document import OKFDocument
from ._vendor.okf.viewer.generator import generate_visualization
from .okf import index as okf_index
from .okf import render


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n")


def jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in rows)
    )


def check_bundle(root, withheld=frozenset()):
    """Check every page's type and links. Returns counts, or raises with the faults.

    `withheld` are paths, relative to the root, that a bundle limited to some
    sources leaves out on purpose; a link to one of them is counted, not a fault.
    """
    root = Path(root)
    errors = []
    count = held = 0
    for path in root.rglob("*.md"):
        text = path.read_text()
        if path.name not in ("index.md", "log.md"):
            doc = OKFDocument.parse(text)
            if not doc.frontmatter.get("type"):
                errors.append(f"Missing type: {path}")
            count += 1
        for target in re.findall(r"\]\(([^)\s]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            dest = (path.parent / target.split("#")[0]).resolve()
            if not dest.is_relative_to(root.resolve()):
                errors.append(f"Broken or escaping link: {path} -> {target}")
            elif dest.relative_to(root.resolve()).as_posix() in withheld:
                held += 1
            elif not dest.exists():
                errors.append(f"Broken or escaping link: {path} -> {target}")
    if errors:
        raise ValueError("\n".join(errors))
    counts = {"concepts": count, "broken_links": 0}
    return {**counts, "withheld_links": held} if withheld else counts


def okf_export(result, sources, root, generated_at=None, ontology=None):
    """Write a batch's dossiers as an OKF folder, with the shared renderer.

    `generated_at` stamps every page; pass the batch's time for a reproducible
    export. `ontology` is `(hash, document)` when concept pages are wanted.
    """
    root = Path(root)
    stamp = generated_at or store.now()
    observations = {o["id"]: o for o in result["observations"]}
    files = {
        render.source_path(source["id"]): render.render_source(source, stamp)
        for source in sources
    }
    concepts = []
    if ontology:
        ontology_hash, definitions = ontology
        for name, concept in definitions["concepts"].items():
            files[render.concept_path(concept["scope"], name)] = render.render_concept(
                concept, ontology_hash, stamp
            )
            concepts.append((concept["scope"], name, concept["definition"]))
    for profile in result["profiles"]:
        claims = sorted(i for i in render.cited_ids(profile) if i in observations)
        for oid in claims:
            files[render.evidence_path(oid)] = render.render_evidence(
                observations[oid], stamp
            )
        files[render.entity_path(profile["canonical_entity_key"])] = (
            render.render_entity(
                profile, [(oid, observations[oid]["field"]) for oid in claims], stamp
            )
        )
    files.update(
        okf_index.pages(
            okf_index.build(
                [okf_index.summary(profile) for profile in result["profiles"]],
                [(source["id"], source["metadata"]["title"]) for source in sources],
                concepts,
            )
        )
    )
    for path, body in files.items():
        target = root / path.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
    checked = check_bundle(root)
    stats = generate_visualization(
        root, root / "viewer.html", bundle_name="Link Lens: evidence dossiers"
    )
    viewer = store.blob(
        (root / "viewer.html").read_bytes(), "text/html", "okf-viewer.html"
    )
    return {**stats, **checked, "viewer_artifact": viewer}


def export(output: Path, batch_id=None, experiment_id=None):
    if batch_id:
        selected = store.require("batches", batch_id)
        if selected.get("enhancement_job_id"):
            from .enhancement import validate_output

            validate_output(output)
    output.mkdir(parents=True, exist_ok=True)
    from .measurements import summary

    write_json(output / "measurement-summary.json", summary(experiment_id))
    from .pricing import collect, estimate

    ledger = collect(experiment_id)
    write_json(output / "cost-usage.json", ledger)
    write_json(output / "cost-summary.json", estimate(ledger))
    discovery = store.current_discovery(experiment_id)
    if discovery:
        jsonl(output / "shortlist.jsonl", discovery["shortlist"])
        write_json(
            output / "discovery-audit.json",
            {k: v for k, v in discovery.items() if k not in ("ranked", "shortlist")},
        )
    runs = (
        store.listing("runs")
        if batch_id is None
        else [
            store.require("runs", r)
            for r in store.require("batches", batch_id)["run_ids"]
        ]
    )
    if experiment_id:
        runs = [
            r for r in runs if r.get("experiment_id", "terra-baseline") == experiment_id
        ]
    from .ontology import resolve
    from .budget import summary as budget_summary

    if experiment_id:
        write_json(output / "budget.json", budget_summary(experiment_id))
    for ontology_hash in sorted(
        {r["ontology_hash"] for r in runs if r.get("ontology_hash")}
    ):
        write_json(
            output / "ontologies" / (ontology_hash + ".json"), resolve(ontology_hash)
        )
    selected_run_ids = {r["id"] for r in runs}
    from .ontology import proposals

    for proposal in proposals():
        if selected_run_ids.intersection(proposal.get("run_ids", [])):
            write_json(
                output / "ontology-proposals" / (proposal["id"] + ".json"),
                {**proposal, **store.read_json(proposal["proposal_artifact"])},
            )
    for run in runs:
        folder = output / "onboarding" / run["source_slug"] / run["id"]
        write_json(folder / "run.json", run)
        write_json(folder / "events.json", store.listing("events", owner=run["id"]))
        if run.get("extraction_artifact"):
            extraction = store.read_json(run["extraction_artifact"])
            jsonl(folder / "observations.jsonl", extraction["observations"])
            write_json(
                folder / "extraction-diagnostics.json",
                {k: v for k, v in extraction.items() if k != "observations"},
            )
        write_json(
            folder / "approvals.json", store.listing("approvals", owner=run["id"])
        )
        for mapping in store.listing("mappings", owner=run["id"]):
            write_json(folder / f"mapping-v{mapping['version']}.json", mapping)
        if run.get("review_artifact"):
            (folder / "review.md").write_bytes(
                store.blob_path(run["review_artifact"]).read_bytes()
            )
    chosen = {}
    for run in runs:
        if run["status"] in {"waiting_for_human", "completed"} and run.get(
            "mapping_id"
        ):
            chosen[run["source_slug"]] = run
    for slug, run in chosen.items():
        mapping = store.require("mappings", run["mapping_id"])
        write_json(
            output / "mappings" / f"{slug}.json",
            {
                **mapping,
                "approval_status": run["status"],
                "snapshot_id": run["snapshot_id"],
            },
        )
    coverage = []
    for slug, run in chosen.items():
        config = store.require("mappings", run["mapping_id"])["config"]
        coverage.append(
            {
                "source": slug,
                "run_id": run["id"],
                "approval_status": run["status"],
                "ontology_hash": config.get("ontology_hash"),
                "mapped_source_fields": sorted(
                    {s for f in config["fields"] for s in f["source_fields"]}
                ),
                "targets": sorted({f["canonical_field"] for f in config["fields"]}),
                "unmapped_fields": config["unmapped_fields"],
                "emitted_observations": None,
                "profiles_receiving_evidence": None,
            }
        )
    report = {
        "runs": len(runs),
        "approved": sum(r["status"] == "completed" for r in runs),
    }
    if batch_id:
        batch = store.require("batches", batch_id)
        result = store.read_json(batch["result_artifact"])
        if "enhancement_policy" in result:
            from .enhancement import export_enhancement

            export_enhancement(result, output)
        for key in ["observations", "links", "unlinked", "profiles"]:
            jsonl(output / f"{key}.jsonl", result[key])
        write_json(output / "source-removal.json", result["source_impact"])
        write_json(output / "selection.json", result["selection"])
        sources = [store.require("sources", r["source_id"]) for r in runs]
        # Stamped with the batch's own time, so the same batch exports the same pages.
        report["okf"] = okf_export(
            result, sources, output / "okf", generated_at=batch.get("created_at")
        )
        for row in coverage:
            sid = store.require("runs", row["run_id"])["source_id"]
            row["emitted_observations"] = sum(
                o["source_id"] == sid for o in result["observations"]
            )

            def has_claim(value):
                if isinstance(value, dict):
                    if "raw_locator" in value and value.get("source_id") == sid:
                        return True
                    return any(has_claim(v) for v in value.values())
                return isinstance(value, list) and any(has_claim(v) for v in value)

            row["profiles_receiving_evidence"] = sum(
                has_claim(p) for p in result["profiles"]
            )
    write_json(
        output / "ontology-coverage.json",
        {
            "basis": "Mapped columns are not correctness measurements; absent extraction/profile counts remain unknown",
            "sources": coverage,
        },
    )
    write_json(output / "export-manifest.json", report)
    return report
