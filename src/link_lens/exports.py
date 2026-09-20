"""Deterministic submissions and OKF dossiers; no narrative-model rewriting."""

import html
import json
import re
from pathlib import Path

import yaml

from . import store
from ._vendor.okf.bundle.document import OKFDocument
from ._vendor.okf.viewer.generator import generate_visualization


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n")


def jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in rows)
    )


def document(path, frontmatter, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
        + "---\n\n"
        + body
        + "\n"
    )


def check_bundle(root):
    errors = []
    count = 0
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
            if not dest.is_relative_to(root.resolve()) or not dest.exists():
                errors.append(f"Broken or escaping link: {path} -> {target}")
    if errors:
        raise ValueError("\n".join(errors))
    return {"concepts": count, "broken_links": 0}


def okf_export(result, sources, root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    stamp = store.now()
    generated = {"by": "process:link-lens-exporter-1", "at": stamp}
    source_index = []
    entity_index = []
    for source in sources:
        sid = source["id"]
        meta = source["metadata"]
        title = meta["title"]
        source_index.append(
            f"* [{html.escape(title)}]({sid}.md) - publisher metadata and licence."
        )
        document(
            root / "sources" / f"{sid}.md",
            {
                "type": "Public Data Source",
                "title": title,
                "description": "Publisher, source role and licence.",
                "generated": generated,
                "resource": source["portal"] + "/dataset/" + sid,
                "tags": ["source"],
            },
            f"# Publisher\n\n{html.escape((meta.get('organization') or {}).get('title', 'unknown'))}\n\nLicence: {html.escape(meta.get('license_title') or 'unknown')}.\n\n[Catalogue record]({source['portal']}/dataset/{sid})",
        )
    observations = {o["id"]: o for o in result["observations"]}
    for profile in result["profiles"]:
        eid = profile["canonical_entity_key"]
        name = profile["fields"].get("entity.legal_name", {}).get("value", eid)
        entity_index.append(
            f"* [{html.escape(name)}]({eid}.md) - profile with claim-level evidence and alternatives."
        )
        claims = []

        def walk(value):
            if isinstance(value, dict):
                if "id" in value and value["id"] in observations:
                    claims.append(value["id"])  # noqa: B023 -- walk executes synchronously within this profile
                for v in value.values():
                    walk(v)
            elif isinstance(value, list):
                for v in value:
                    walk(v)

        walk(profile)
        links = []
        for oid in sorted(set(claims)):
            obs = observations[oid]
            document(
                root / "evidence" / f"{oid}.md",
                {
                    "type": "Field Observation",
                    "title": obs["field"] + ": " + obs["value"],
                    "description": "A source claim, not independent proof of identity.",
                    "generated": generated,
                    "tags": ["evidence"],
                    "sources": [{"resource": f"../sources/{obs['source_id']}.md"}],
                },
                "[Source](../sources/"
                + obs["source_id"]
                + ".md)\n\n```json\n"
                + json.dumps(obs, indent=2, ensure_ascii=False)
                + "\n```",
            )
            links.append(
                f"* [{obs['field']}](../evidence/{oid}.md) - source value and exact raw locator."
            )
        # JSON is the exact profile serialization, so no loss of alternatives or confidence dimensions.
        document(
            root / "entities" / f"{eid}.md",
            {
                "type": "Business Profile",
                "title": name,
                "description": "Versioned profile assembled from proposed identifier links.",
                "tags": ["entity", "proposed-identity"],
                "generated": generated,
                "status": "draft",
                "profile_version": profile["profile_version"],
                "sources": [
                    {"resource": f"../sources/{sid}.md"}
                    for sid in sorted({r[0] for r in profile["source_records"]})
                ],
            },
            "# Profile\n\nRule scores are uncalibrated. Review of a mapping does not verify every identity link.\n\n```json\n"
            + json.dumps(profile, indent=2, ensure_ascii=False)
            + "\n```\n\n# Evidence\n\n"
            + "\n".join(links),
        )
    for folder, lines in [("sources", source_index), ("entities", entity_index)]:
        (root / folder).mkdir(exist_ok=True)
        (root / folder / "index.md").write_text(
            "# " + folder.title() + "\n\n" + "\n".join(lines) + "\n"
        )
    (root / "index.md").write_text(
        '---\nokf_version: "0.2"\n---\n\n# Link Lens\n\n* [Entities](entities/index.md) - generated profiles and evidence.\n* [Sources](sources/index.md) - publisher metadata.\n\nThe document graph represents evidence links; it is not proof of business identity.\n'
    )
    checked = check_bundle(root)
    stats = generate_visualization(
        root, root / "viewer.html", bundle_name="Link Lens: evidence dossiers"
    )
    viewer = store.blob(
        (root / "viewer.html").read_bytes(), "text/html", "okf-viewer.html"
    )
    return {**stats, **checked, "viewer_artifact": viewer}


def export(output: Path, batch_id=None, experiment_id=None):
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
    report = {
        "runs": len(runs),
        "approved": sum(r["status"] == "completed" for r in runs),
    }
    if batch_id:
        batch = store.require("batches", batch_id)
        result = store.read_json(batch["result_artifact"])
        for key in ["observations", "links", "unlinked", "profiles"]:
            jsonl(output / f"{key}.jsonl", result[key])
        write_json(output / "source-removal.json", result["source_impact"])
        write_json(output / "selection.json", result["selection"])
        sources = [store.require("sources", r["source_id"]) for r in runs]
        report["okf"] = okf_export(result, sources, output / "okf")
    write_json(output / "export-manifest.json", report)
    return report
