"""Part 1 only. Stage new results; keep the original and Parts 2–4 unchanged."""

import hashlib
import json
import shutil
from pathlib import Path

from link_lens import evaluation, exports, store
from link_lens.downloadability import POLICY, probe_dataset, select_downloadable

root = Path("outputs/part1-downloadable")
root.mkdir(exist_ok=True)
previous = store.require("batches", "discovery-jev-luna-v1")
revision_id = "discovery-jev-luna-v1-downloadable-v3"
archive = Path("experiments/jev-luna-before-download-gate")
if not archive.exists():
    archive.mkdir(parents=True)
    for name in [
        "shortlist.jsonl",
        "discovery-audit.json",
        "README.md",
        "measurement-summary.json",
        "COMPARISON.md",
        "triage-review.html",
        "triage-review.json",
        "ai-audit",
    ]:
        src = Path("outputs") / name
        if src.is_dir():
            shutil.copytree(src, archive / name)
        elif src.exists():
            shutil.copy2(src, archive / name)
    exports.write_json(archive / "discovery-batch.json", previous)
    exports.write_json(
        archive / "manifest.json",
        {
            str(p.relative_to(archive)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in archive.rglob("*")
            if p.is_file()
        },
    )
if not (root / "downstream-hashes.json").exists():
    exports.write_json(
        root / "downstream-hashes.json",
        {
            name: hashlib.sha256((Path("outputs") / name).read_bytes()).hexdigest()
            for name in [
                "observations.jsonl",
                "links.jsonl",
                "unlinked.jsonl",
                "profiles.jsonl",
                "selection.json",
                "source-removal.json",
            ]
        },
    )
cache = root / "checks"
cache.mkdir(exist_ok=True)


def check(d):
    path = cache / (d["id"] + ".json")
    if path.exists():
        cached = json.loads(path.read_text())
        if (
            cached["status"] == "available"
            or cached.get("policy_version") == POLICY["version"]
        ):
            return cached
    r = probe_dataset(d)
    r["policy_version"] = POLICY["version"]
    exports.write_json(path, r)
    print(d["title"], r["status"], len(r["attempts"]), flush=True)
    return r


datasets = {d["id"]: d for d in store.read_json(previous["catalogue_artifact"])}
shortlist, checks = select_downloadable(previous["ranked"], datasets, check=check)
audit = {
    **previous,
    "id": revision_id,
    "supersedes_discovery_id": previous["id"],
    "shortlist": shortlist,
    "download_checked_at": store.now(),
    "download_policy": POLICY,
    "download_checks_artifact": store.json_blob(checks, "download-checks.json"),
    "triage_method": previous["triage_method"]
    + "; bounded GET + reader preflight gate",
    "rerun_model_calls": 0,
    "ranking_reuse": "Same catalogue and Jev scores; no evaluation labels used",
}
store.put("batches", revision_id, audit, kind="discovery", immutable=True)
exports.write_json(root / "discovery-audit.json", audit)
exports.write_json(root / "download-checks.json", checks)
exports.jsonl(root / "shortlist.jsonl", shortlist)
exports.write_json(
    root / "triage-review.json", evaluation.worksheet("triage", revision_id)
)
print(
    json.dumps(
        {
            "revision": revision_id,
            "selected": len(shortlist),
            "checked": len(checks),
            "portfolio": [
                r["slug"]
                for r in shortlist
                if r["slug"]
                in __import__("link_lens.ingestion", fromlist=["PORTFOLIO"]).PORTFOLIO
            ],
        },
        indent=2,
    )
)
