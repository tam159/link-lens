"""Retrospective list-price estimates; never overwrite historical billing receipts."""

import json
from decimal import Decimal
from pathlib import Path


def rates():
    return json.loads(Path(__file__).with_name("pricing_rates.json").read_text())


def price_usage(usage, rate):
    if (
        not usage
        or usage.get("input_tokens") is None
        or usage.get("output_tokens") is None
    ):
        return None
    details = usage.get("input_token_details") or {}
    if details.get("cache_read") is None or details.get("cache_creation") is None:
        return None  # Unknown cache split is not zero cache use.
    read, write = details["cache_read"], details["cache_creation"]
    ordinary = usage["input_tokens"] - read - write
    counts = {
        "input": ordinary,
        "cache_read": read,
        "cache_write": write,
        "output": usage["output_tokens"],
    }
    if any(
        not isinstance(v, int) or isinstance(v, bool) or v < 0 for v in counts.values()
    ):
        raise ValueError("Invalid or overlapping token categories")
    return float(
        sum(Decimal(n) * Decimal(str(rate[k])) for k, n in counts.items())
        / Decimal(1_000_000)
    )


def estimate(rows, snapshot=None):
    snapshot = snapshot or rates()
    calls = []
    for row in rows:
        usage = row.get("usage")
        # This report deliberately prices only the measured short-context workload.
        # Longer calls require selecting the documented threshold before extending it.
        eligible = (
            usage
            and isinstance(usage.get("input_tokens"), int)
            and usage["input_tokens"]
            <= (32000 if row["model"].startswith("typesafe/") else 20278)
        )
        model_rates = snapshot["models"].get(row["model"])
        cost = (
            price_usage(usage, model_rates["standard"]["short"])
            if eligible and model_rates
            else None
        )
        calls.append({**row, "estimated_standard_list_cost_usd": cost})
    known = [c for c in calls if c["estimated_standard_list_cost_usd"] is not None]
    subtotal = float(
        sum(Decimal(str(c["estimated_standard_list_cost_usd"])) for c in known)
    )
    by_run = []
    for rid in sorted({r["run_id"] for r in calls}):
        group = [c for c in calls if c["run_id"] == rid]
        priced = [c for c in group if c["estimated_standard_list_cost_usd"] is not None]
        by_run.append(
            {
                "run_id": rid,
                "source": group[0]["source"],
                "calls": len(group),
                "priced_calls": len(priced),
                "unpriced_calls": len(group) - len(priced),
                "measured_subtotal_usd": float(
                    sum(
                        Decimal(str(c["estimated_standard_list_cost_usd"]))
                        for c in priced
                    )
                ),
            }
        )
    return {
        "pricing_snapshot": snapshot,
        "basis": "OpenAI Standard short-context prices approximate Azure deployment costs; Jev uses published OpenRouter flat input pricing. No regional uplift.",
        "calls": len(calls),
        "priced_calls": len(known),
        "unpriced_calls": len(calls) - len(known),
        "measured_subtotal_usd": subtotal,
        "complete_estimated_total_usd": subtotal if len(known) == len(calls) else None,
        "budget_target_usd": 10,
        "measured_subtotal_within_budget": subtotal <= 10,
        "budget_compliance": "Assessed on priced calls only; unpriced calls are excluded.",
        "per_record_llm_calls": 0,
        "per_record_llm_cost_usd": 0,
        "per_run": by_run,
        "call_details": calls,
    }


def collect(experiment_id=None):
    from . import store

    rows = []
    for e in store.listing("events", kind="model_usage"):
        run = store.require("runs", e["run_id"])
        if (
            experiment_id
            and run.get("experiment_id", "terra-baseline") != experiment_id
        ):
            continue
        raw = (
            store.read_json(e["response_artifact"])
            if e.get("response_artifact")
            else {}
        )
        rows.append(
            {
                "event_id": e["id"],
                "run_id": e["run_id"],
                "source": run["source_slug"],
                "stage": e.get("stage"),
                "model": e["model"],
                "usage": raw.get("usage_metadata"),
                "response_artifact": e.get("response_artifact"),
                "reported_model": raw.get("response_metadata", {}).get("model_name"),
                "reported_service_tier": raw.get("response_metadata", {}).get(
                    "service_tier"
                ),
            }
        )
    for e in store.listing("events", kind="triage_usage"):
        if experiment_id and e.get("experiment_id") != experiment_id:
            continue
        usage = None
        if e.get("input_tokens") is not None and e.get("output_tokens") is not None:
            usage = {
                "input_tokens": e["input_tokens"],
                "output_tokens": e["output_tokens"],
                "input_token_details": {"cache_read": 0, "cache_creation": 0},
            }
        rows.append(
            {
                "event_id": e["id"],
                "run_id": e["run_id"],
                "source": "catalogue triage",
                "stage": "triage",
                "model": e["model"],
                "usage": usage,
                "response_artifact": e.get("response_artifact"),
                "reported_cost_usd": e.get("calculated_cost_usd"),
            }
        )
    return rows
