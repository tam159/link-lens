"""One durable, conservative API-spend ledger per experiment, including retries."""

from contextlib import nullcontext
import math
import uuid

from . import store
from .pricing import rates
from .settings import settings


class BudgetExceeded(RuntimeError):
    pass


def rate_for(model):
    entry = rates()["models"].get(model)
    if not entry:
        raise BudgetExceeded("No reservation pricing configured for " + model)
    multiplier = settings().pricing_multiplier
    if not math.isfinite(multiplier) or multiplier < 1:
        raise ValueError("Pricing multiplier must be finite and at least one")
    result = {
        key: max(t[key] for t in entry["standard"].values()) * multiplier
        for key in ("input", "cache_read", "cache_write", "output")
    }
    if settings().input_usd_per_million is not None:
        result["input"] = result["cache_write"] = settings().input_usd_per_million
    if settings().output_usd_per_million is not None:
        result["output"] = settings().output_usd_per_million
    return result


def summary(experiment_id):
    rows = store.listing("budget_reservations", owner=experiment_id)
    owners = {r["owner"] for r in rows}
    legacy_charge = 0.0
    for run in store.listing("runs"):
        if run.get("experiment_id") != experiment_id or run["id"] in owners:
            continue
        rate = rate_for(run.get("model", settings().model))
        legacy_charge += max(
            run.get("calculated_cost_usd") or 0,
            (
                run.get("input_tokens", 0) * max(rate["input"], rate["cache_write"])
                + run.get("output_tokens", 0) * rate["output"]
            )
            / 1e6,
        )
    for event in store.listing("events"):
        if (
            event.get("experiment_id") != experiment_id
            or event.get("reservation_id")
            or event.get("stage")
            not in {
                "triage",
                "embedding",
                "resolution",
                "reconciliation",
                "profile_explanation",
            }
        ):
            continue
        legacy_charge += (
            event.get("budget_charge_usd") or event.get("calculated_cost_usd") or 0
        )
    return {
        "experiment_id": experiment_id,
        "cap_usd": settings().max_cost_usd,
        "charged_usd": sum(r["charge_usd"] for r in rows) + legacy_charge,
        "attempts": len(rows),
        "unsettled_attempts": sum(r["status"] != "settled" for r in rows),
        "basis": "Conservative provider-rate estimate, not a complete invoice",
    }


def reserve(
    experiment_id, owner, stage, model, input_tokens, output_tokens, *, locked=False
):
    rate = rate_for(model)
    charge = (
        input_tokens * max(rate["input"], rate["cache_write"])
        + output_tokens * rate["output"]
    ) / 1e6
    with nullcontext() if locked else store.model_budget_lock():
        # Preserve pre-ledger attempts when an older owner starts using reservations.
        if not any(
            r["owner"] == owner
            for r in store.listing("budget_reservations", owner=experiment_id)
        ):
            previous = store.get("runs", owner)
            if previous:
                historical = max(
                    previous.get("calculated_cost_usd") or 0,
                    (
                        previous.get("input_tokens", 0)
                        * max(rate["input"], rate["cache_write"])
                        + previous.get("output_tokens", 0) * rate["output"]
                    )
                    / 1e6,
                )
                if historical:
                    entry = {
                        "id": "legacy-" + owner,
                        "experiment_id": experiment_id,
                        "owner": owner,
                        "stage": "legacy_attempts",
                        "model": model,
                        "charge_usd": historical,
                        "reservation_usd": historical,
                        "status": "historical_estimate",
                        "rate": rate,
                    }
                    store.put(
                        "budget_reservations",
                        entry["id"],
                        entry,
                        experiment_id,
                        "api_attempt",
                        immutable=True,
                    )
        if summary(experiment_id)["charged_usd"] + charge > settings().max_cost_usd:
            raise BudgetExceeded(
                "Project dollar budget exhausted (shared experiment cap); progress retained"
            )
        key = str(uuid.uuid4())
        record = {
            "id": key,
            "experiment_id": experiment_id,
            "owner": owner,
            "stage": stage,
            "model": model,
            "reservation_usd": charge,
            "charge_usd": charge,
            "status": "reserved",
            "rate": rate,
        }
        store.put("budget_reservations", key, record, experiment_id, "api_attempt")
    return key


def settle(
    key, input_tokens=None, output_tokens=None, reported_cost=None, *, locked=False
):
    with nullcontext() if locked else store.model_budget_lock():
        record = store.require("budget_reservations", key)
        valid = lambda n: isinstance(n, int) and not isinstance(n, bool) and n >= 0
        if valid(input_tokens) and valid(output_tokens):
            rate = record["rate"]
            record["charge_usd"] = (
                input_tokens * max(rate["input"], rate["cache_write"])
                + output_tokens * rate["output"]
            ) / 1e6
            record["status"] = "settled"
        if (
            isinstance(reported_cost, (int, float))
            and not isinstance(reported_cost, bool)
            and math.isfinite(reported_cost)
            and reported_cost >= 0
        ):
            record["charge_usd"] = reported_cost
            record["status"] = "settled"
        record.update(input_tokens=input_tokens, output_tokens=output_tokens)
        store.put(
            "budget_reservations", key, record, record["experiment_id"], "api_attempt"
        )


def onboarding_estimate(experiment_id=None):
    """What onboarding one more source is likely to cost, against what is left.

    The estimate is the median cost of the onboarding runs that completed, with
    the highest beside it; it is history, not a quote, and a source with a long
    or unusual file can cost more. `affordable` is false when the estimate
    would take the experiment's charges over its cap.
    """
    experiment_id = experiment_id or settings().experiment_id
    costs = sorted(
        run["calculated_cost_usd"]
        for run in store.listing("runs", kind="onboarding")
        if run.get("status") == "completed" and run.get("calculated_cost_usd")
    )
    spent = summary(experiment_id)
    remaining = max(spent["cap_usd"] - spent["charged_usd"], 0.0)
    estimate = costs[len(costs) // 2] if costs else None
    return {
        "experiment_id": experiment_id,
        "estimate_usd": estimate,
        "highest_usd": costs[-1] if costs else None,
        "basis": (
            f"median of {len(costs)} completed onboarding runs"
            if costs
            else "no completed onboarding run to estimate from"
        ),
        "cap_usd": spent["cap_usd"],
        "charged_usd": spent["charged_usd"],
        "remaining_usd": remaining,
        # With nothing to estimate from, the cap itself is the only test.
        "affordable": remaining > (estimate or 0.0),
    }
