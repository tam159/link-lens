import pytest
from link_lens import store, llm
from link_lens.ingestion import new_run
from link_lens.contracts import SemanticReview
from link_lens.settings import settings


def test_call_limit_stops_before_network(monkeypatch):
    run = new_run({"id": "s", "slug": "s"}, {"id": "snapshot"})
    run["model_calls"] = settings().max_model_calls
    store.put("runs", run["id"], run)
    monkeypatch.setattr(
        llm, "model", lambda: pytest.fail("Network model must not be created")
    )
    with pytest.raises(llm.BudgetExceeded, match="Model-call"):
        llm.call(run["id"], SemanticReview, "test", "test")


def test_project_spend_includes_failed_prior_run(monkeypatch):
    monkeypatch.setenv("LINK_LENS_INPUT_USD_PER_MILLION", "10")
    monkeypatch.setenv("LINK_LENS_OUTPUT_USD_PER_MILLION", "20")
    monkeypatch.setenv("LINK_LENS_MAX_COST_USD", "1")
    settings.cache_clear()
    old = new_run({"id": "s", "slug": "s"}, {"id": "snapshot"})
    old.update(input_tokens=200000, status="failed")
    store.put("runs", old["id"], old)
    run = new_run({"id": "s", "slug": "s"}, {"id": "snapshot"})
    monkeypatch.setattr(
        llm, "model", lambda: pytest.fail("Network model must not be created")
    )
    with pytest.raises(llm.BudgetExceeded, match="Project dollar"):
        llm.call(run["id"], SemanticReview, "test", "test")
