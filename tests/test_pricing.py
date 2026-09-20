import pytest
from link_lens.pricing import price_usage, rates, estimate

RATE = rates()["models"]["gpt-5.6-terra"]["standard"]["short"]


def test_cache_writes_replace_input_charge():
    usage = {
        "input_tokens": 1000,
        "output_tokens": 100,
        "input_token_details": {"cache_read": 300, "cache_creation": 500},
    }
    # 200 ordinary input, 300 reads, 500 writes; no double charging writes.
    assert price_usage(usage, RATE) == pytest.approx(0.00291)
    with pytest.raises(ValueError):
        price_usage({**usage, "input_tokens": 100}, RATE)


def test_missing_usage_or_cache_split_is_not_free():
    assert price_usage(None, RATE) is None
    assert price_usage({"input_tokens": 1000, "output_tokens": 100}, RATE) is None
    usage = {
        "input_tokens": 1000,
        "output_tokens": 100,
        "input_token_details": {"cache_read": 0, "cache_creation": 0},
    }
    rows = [
        {"run_id": "r", "source": "s", "model": "gpt-5.6-terra", "usage": u}
        for u in [usage, None]
    ]
    report = estimate(rows)
    assert report["measured_subtotal_usd"] == 0.0032
    assert report["unpriced_calls"] == 1
    assert report["complete_estimated_total_usd"] is None
    assert "actual_billed_cost_usd" not in report
    assert report["measured_subtotal_within_budget"] is True
    assert report["per_record_llm_cost_usd"] == 0
    rows[0]["usage"]["input_tokens"] = None
    assert estimate(rows)["unpriced_calls"] == 2


def test_rates_and_scope_do_not_invent_prices():
    r = rates()["models"]
    assert r["gpt-5.6-sol"]["standard"]["short"]["input"] == 4
    assert r["gpt-5.6-luna"]["standard"]["short"]["output"] == 1.2
    assert r["gpt-5.6-terra"]["fast"]["long"]["cache_write"] == 10
    row = {
        "run_id": "r",
        "source": "s",
        "model": "unknown",
        "usage": {
            "input_tokens": 2,
            "output_tokens": 1,
            "input_token_details": {"cache_read": 0, "cache_creation": 0},
        },
    }
    assert estimate([row])["unpriced_calls"] == 1
