import json
from unittest.mock import Mock

import pytest

from link_lens import store, triage
from link_lens.pricing import collect, estimate, rates


def test_decision_cached_with_receipt_and_experiment_isolation(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only")
    response = Mock()
    response.json.return_value = {
        "model": "typesafe/jev-1.13-test",
        "answers": {"relevant": {"type": "noul", "noul": 0.91}},
        "usage": {"input_tokens": 1000, "output_tokens": 22, "cost": 0.000042},
        "id": "request-1",
    }
    post = Mock(return_value=response)
    monkeypatch.setattr(triage.httpx, "post", post)
    dataset = {"id": "d1", "title": "Company register", "resources": []}
    first = triage.classify_dataset(dataset, "discovery-jev-luna-v1")
    assert first == triage.classify_dataset(dataset, "discovery-jev-luna-v1")
    assert post.call_count == 1
    assert len(store.listing("events", kind="triage_usage")) == 1
    assert collect("terra-baseline") == []
    report = estimate(collect("jev-luna-v1"))
    assert report["complete_estimated_total_usd"] == 0.000042
    assert "test-only" not in json.dumps(store.listing("events"))
    assert rates()["models"]["typesafe/jev-1.13"]["standard"]["short"]["output"] == 0
    dataset["notes"] = "Changed metadata"
    triage.classify_dataset(dataset, "discovery-jev-luna-v1")
    assert post.call_count == 2


def test_bad_response_records_failure_without_cached_decision(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only")
    response = Mock()
    response.json.return_value = {"answers": {"relevant": {"noul": 4}}}
    monkeypatch.setattr(triage.httpx, "post", Mock(return_value=response))
    with pytest.raises(ValueError):
        triage.classify_dataset({"id": "d", "title": "Bad"}, "discovery-test")
    assert not store.listing("batches", kind="triage_decision")
    assert store.listing("events", kind="triage_usage")[0]["status"] == "error"
