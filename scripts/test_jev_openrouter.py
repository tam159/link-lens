"""Live, paid smoke test: uv run --no-sync python scripts/test_jev_openrouter.py.

Uses the existing LangChain Core and HTTPX dependencies. Sends synthetic data only.
Jev uses OpenRouter's Decisions API, not chat completions.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import dotenv_values
from langchain_core.runnables import RunnableLambda

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.13"


def classify(state: str) -> dict:
    key = dotenv_values(ROOT / ".env").get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("Missing OPENROUTER_API_KEY in .env")
    response = httpx.post(
        ENDPOINT,
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": MODEL,
            "state": state,
            "questions": {
                "relevant": {
                    "type": "noul",
                    "instructions": "Does this dataset contain identifiable organisations rather than aggregate statistics?",
                }
            },
        },
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    probability = result["answers"]["relevant"]["noul"]
    if not 0 <= probability <= 1:
        raise ValueError("Invalid decision probability")
    return result


def main() -> None:
    # Keep this connectivity experiment outside the assignment's trace/cost ledger.
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    decision = RunnableLambda(classify, name="jev_openrouter_decision")
    cases = {
        "organisation_records": "Dataset containing one record per company, with columns ABN and company name.",
        "aggregate_statistics": "Dataset containing monthly totals of vehicle registrations by year and region. No names or identifiers for businesses or organisations.",
    }
    results = []
    for name, state in cases.items():
        started = time.monotonic()
        result = decision.invoke(state)
        results.append({"case": name, "state": state, "elapsed_seconds": round(time.monotonic() - started, 3), "response": result})
    report = {
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "integration": "LangChain RunnableLambda with HTTPX; custom Decisions API adapter",
        "endpoint": ENDPOINT,
        "requested_model": MODEL,
        "results": results,
        "limitation": "Connectivity and synthetic examples only; not an accuracy evaluation or production integration.",
    }
    target = ROOT / "outputs" / "experiments" / "jev-openrouter.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
