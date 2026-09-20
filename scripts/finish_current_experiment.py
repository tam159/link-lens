"""Finish deterministic processing only after the user's exact mapping approvals."""

import subprocess
import sys
from pathlib import Path

from link_lens import store, evaluation, exports
from link_lens.ingestion import PORTFOLIO
from link_lens.pipeline import assemble
from link_lens.review_ui import prepare_review_page
from link_lens.settings import settings

experiment = settings().experiment_id
latest = {
    r["source_slug"]: r
    for r in store.listing("runs")
    if r.get("experiment_id") == experiment and r["source_slug"] in PORTFOLIO
}
missing = [
    slug
    for slug in PORTFOLIO
    if slug not in latest or latest[slug]["status"] != "completed"
]
if missing:
    raise SystemExit(
        "Awaiting completed, user-approved mappings: " + ", ".join(missing)
    )
ids = [latest[slug]["id"] for slug in PORTFOLIO]
previous = [b for b in store.listing("batches", kind="pipeline") if b["run_ids"] == ids]
batch = previous[-1] if previous else assemble(ids, 50, 25000)
for kind, bid, filename in [
    ("triage", "discovery-" + experiment, "triage-review"),
    ("links", batch["id"], "link-review"),
]:
    packet = evaluation.worksheet(kind, bid)
    exports.write_json(Path("outputs") / (filename + ".json"), packet)
    prepare_review_page(packet, Path("outputs") / (filename + ".html"))
subprocess.run([sys.executable, "scripts/report_current_experiment.py"], check=True)
print("New batch:", batch["id"])
print(
    "Next: inspect all proposed links and save an explicitly AI-assisted census; human worksheets remain incomplete until evidence-reviewed."
)
