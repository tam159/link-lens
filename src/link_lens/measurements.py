"""Reports only measured values; separates missing observations from zero usage."""

from . import evaluation, store
from .pricing import collect, estimate


def summary(experiment_id=None):
    cost_estimate = estimate(collect(experiment_id))
    events = store.listing("events")
    selected_runs = [
        r
        for r in store.listing("runs")
        if not experiment_id
        or r.get("experiment_id", "terra-baseline") == experiment_id
    ]
    ids = {r["id"] for r in selected_runs}
    receipts = [
        e
        for e in events
        if (e["kind"] == "model_usage" and e["run_id"] in ids)
        or (
            e["kind"] in {"triage_usage", "enhancement_usage"}
            and (not experiment_id or e.get("experiment_id") == experiment_id)
        )
    ]
    runs = []
    for run in selected_runs:
        calls = [e for e in receipts if e["run_id"] == run["id"]]
        nodes = [
            e
            for e in events
            if e["run_id"] == run["id"] and e["kind"] == "node_execution"
        ]
        runs.append(
            {
                "run_id": run["id"],
                "source": run["source_slug"],
                "status": run["status"],
                "mapping_attempts": run["version"],
                "model_calls": len(calls),
                "input_tokens": sum(e["input_tokens"] or 0 for e in calls),
                "output_tokens": sum(e["output_tokens"] or 0 for e in calls),
                "calls_with_unknown_usage": sum(
                    e["input_tokens"] is None for e in calls
                ),
                "calculated_cost_usd": sum(e["calculated_cost_usd"] for e in calls)
                if calls and all(e["calculated_cost_usd"] is not None for e in calls)
                else None,
                "measured_model_wall_seconds": sum(e["wall_seconds"] for e in calls),
                "python_calls": run["python_calls"],
                "active_seconds": run["active_seconds"],
                "active_seconds_basis": run.get(
                    "timing_basis",
                    "Model calls plus sandbox only; lower bound excluding other node overhead.",
                ),
                "instrumented_graph_steps": len(nodes) if nodes else None,
                "trace_url": run.get("trace_url"),
                "supersedes_run_id": run.get("supersedes_run_id"),
                "failure": run.get("error"),
            }
        )
    discovery = store.current_discovery(experiment_id)
    batches = [
        b
        for b in store.listing("batches", kind="pipeline")
        if not experiment_id or set(b["run_ids"]).issubset(ids)
    ]
    batch_ids = {b["id"] for b in batches} | ({discovery["id"]} if discovery else set())
    worksheets = [
        w
        for w in store.listing("evaluations", kind="worksheet")
        if not experiment_id or w.get("batch_id") in batch_ids
    ]
    return {
        "published_rate_estimate": {
            k: v for k, v in cost_estimate.items() if k != "call_details"
        },
        "generated_at": store.now(),
        "experiment_id": experiment_id,
        "catalogue_records": discovery["unique_records"] if discovery else None,
        "shortlist_rows": len(discovery["shortlist"]) if discovery else None,
        "runs": runs,
        "total_model_calls_including_failures": len(receipts),
        "total_measured_input_tokens": sum(e["input_tokens"] or 0 for e in receipts),
        "total_measured_output_tokens": sum(e["output_tokens"] or 0 for e in receipts),
        "total_calculated_cost_usd": sum(e["calculated_cost_usd"] for e in receipts)
        if receipts and all(e["calculated_cost_usd"] is not None for e in receipts)
        else None,
        "billing_note": "See published_rate_estimate for agreed Azure estimates and Jev list pricing. Failed calls with missing usage remain unpriced.",
        "per_record_llm_calls": cost_estimate["per_record_llm_calls"],
        "human_evaluations": [evaluation.report(w["id"]) for w in worksheets],
        "ai_assisted_evaluations": [evaluation.ai_report(w["id"]) for w in worksheets],
        "ai_full_shortlist_evaluations": [
            evaluation.ai_report(w["id"])
            for w in store.listing("evaluations", kind="ai_census")
            if not experiment_id or w.get("batch_id") in batch_ids
        ],
        "ai_all_link_evaluations": [
            evaluation.ai_report(w["id"])
            for w in store.listing("evaluations", kind="ai_link_census")
            if not experiment_id or w.get("batch_id") in batch_ids
        ],
        "pipeline_batches": batches,
    }
