"""Collect evidence only; this script makes no evaluation verdicts."""

import json
from pathlib import Path
from link_lens import store
from link_lens.readers import read_records
from link_lens.contracts import MappingSpec

root = Path("outputs/ai-audit")
root.mkdir(exist_ok=True)
packet = json.loads(Path("outputs/link-review.json").read_text())
batch = store.require("batches", packet["batch_id"])
result = store.read_json(batch["result_artifact"])
raw = {}
sources = {}
for rid in batch["run_ids"]:
    r = store.require("runs", rid)
    snap = store.require("snapshots", r["snapshot_id"])
    spec = MappingSpec.model_validate(
        store.require("mappings", r["mapping_id"])["config"]
    )
    _, rows = read_records(
        store.blob_path(snap["artifact_id"]),
        spec.reader,
        snap["sha256"],
        snap["receipt"].get("partial", False),
        25000,
    )
    sources[r["source_id"]] = {
        "slug": r["source_slug"],
        "snapshot": snap["sha256"],
        "url": snap["receipt"]["url"],
        "role": spec.subject_role,
        "filters": [f.model_dump() for f in spec.filters],
    }
    for row in rows:
        raw[(r["source_id"], row["record_id"])] = row
links = []
for n, e in enumerate(result["links"], 1):
    records = []
    for side in ["source_a_record", "source_b_record"]:
        ref = tuple(e[side])
        records.append({"source": sources[ref[0]], **raw[ref]})
    links.append({"number": n, "item_id": e["id"], "link": e, "raw_records": records})
(root / "link-evidence.json").write_text(json.dumps(links, indent=2))
print("Collected", len(links), "raw link pairs (full batch, not just worksheet)")
