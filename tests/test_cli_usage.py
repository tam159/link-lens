import json

import pytest
from typer.testing import CliRunner

from link_lens import store
from link_lens.cli import app
from link_lens.pricing import collect, estimate
from link_lens.settings import settings


@pytest.mark.parametrize("explicit", [False, True])
def test_usage_matches_export_estimate_for_selected_experiment(monkeypatch, explicit):
    monkeypatch.setenv("LINK_LENS_EXPERIMENT_ID", "other" if explicit else "current")
    settings.cache_clear()
    for experiment in ("current", "other"):
        store.put(
            "runs",
            experiment,
            {
                "id": experiment,
                "experiment_id": experiment,
                "source_slug": "source",
            },
        )
        # An attempt with unknown usage must not become a zero-cost call.
        store.put(
            "events",
            experiment,
            {
                "id": experiment,
                "run_id": experiment,
                "kind": "model_usage",
                "model": "gpt-5.6-luna",
            },
            kind="model_usage",
        )
        store.put(
            "events",
            experiment + "-triage",
            {
                "id": experiment + "-triage",
                "run_id": "discovery-" + experiment,
                "experiment_id": experiment,
                "kind": "triage_usage",
                "model": "typesafe/jev-1.13",
                "input_tokens": 1000,
                "output_tokens": 22,
            },
            kind="triage_usage",
        )

    args = ["usage"] + (["--experiment-id", "current"] if explicit else [])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    expected = estimate(collect("current"))
    assert report == {
        "experiment_id": "current",
        **{
            k: v
            for k, v in expected.items()
            if k not in {"pricing_snapshot", "call_details"}
        },
    }
    assert report["calls"] == 2
    assert report["priced_calls"] == 1
    assert report["unpriced_calls"] == 1
    assert report["measured_subtotal_usd"] == pytest.approx(0.000042)
    assert report["complete_estimated_total_usd"] is None
