"""Explicit bounded replacement attempts for exhausted user-requested revisions.

Preserves history, frozen partitions and consumed final-slice cursor. No approvals.
"""

import json
from langgraph_sdk import get_sync_client
from link_lens import store, ingestion
from link_lens.settings import settings


def recover(old_id):
    old = store.require("runs", old_id)
    previous = [
        r for r in store.listing("runs") if r.get("supersedes_run_id") == old_id
    ]
    if previous:
        return previous[-1]
    if old["status"] not in {"needs_review", "budget_exhausted"}:
        raise ValueError("Only exhausted revision attempts can be replaced")
    approvals = store.listing("approvals", owner=old_id)
    if not approvals or approvals[-1]["decision"] != "revision_requested":
        raise ValueError("An actual user revision request is required")
    run = ingestion.new_run(
        store.require("sources", old["source_id"]),
        store.require("snapshots", old["snapshot_id"]),
    )
    for field in [
        "analysis_artifact",
        "partitions_artifact",
        "partition_counts",
        "mapping_id",
        "critique",
    ]:
        if field in old:
            run[field] = old[field]
    # Never reset to a previously examined slice, including earlier attempts on these bytes.
    run["final_cursor"] = max(
        r.get("final_cursor", 0)
        for r in store.listing("runs")
        if r["snapshot_id"] == old["snapshot_id"]
    )
    run.update(
        supersedes_run_id=old_id,
        retry_reason="User-requested revision exhausted prior attempt; explicit new bounded attempt, frozen partitions and consumed final cursor retained",
        carried_feedback=approvals[-1]["feedback"],
    )
    client = get_sync_client(url=settings().api_url)
    thread = client.threads.create(
        metadata={
            "application": "link-lens",
            "onboarding_run_id": run["id"],
            "source": run["source_slug"],
        }
    )
    run["thread_id"] = thread["thread_id"]
    store.put("runs", run["id"], run, run["source_id"], "onboarding")
    feedback = (
        approvals[-1]["feedback"]
        + "\nApply this feedback only where supported by THIS source. If a named column or concept is absent, do not invent it or add fake unmapped columns. A deliberately partial config is allowed. Correct actionable semantic critique by omitting unsupported claims. Do not infer legal ownership from a site label. Preserve the supplied reader."
    )
    client.runs.create(
        thread["thread_id"],
        "onboard",
        input={"run_id": run["id"], "feedback": feedback},
        config={"recursion_limit": 40},
    )
    return run


if __name__ == "__main__":
    import sys

    for rid in sys.argv[1:]:
        r = recover(rid)
        print(
            json.dumps(
                {k: r[k] for k in ["id", "source_slug", "thread_id", "final_cursor"]}
            ),
            flush=True,
        )
