import copy

import pytest

from link_lens import store
from link_lens.enhancement_contracts import (
    EnhancementPolicy,
    IdentityJudgment,
    EquivalenceJudgment,
    ConflictAnnotation,
)
from link_lens.enhancement_models import Inference, PendingInference
from link_lens.semantic_resolution import (
    records_from,
    retrieve,
    gate,
    cluster,
    comparison,
    frequencies,
)
from link_lens.reconciliation import reconcile_profiles


POLICY = EnhancementPolicy(retrieval="fuzzy")


def data(count=3, identifiers=None, address=True):
    obs, candidates = [], []
    for i in range(count):
        sid = chr(97 + i)
        candidates.append(
            {
                "source_id": sid,
                "source_record_id": sid,
                "subject_role": "legal_entity",
                "label": "Acme Ltd",
                "raw_locator": {"row": 1},
            }
        )
        fields = {"entity.legal_name": "Acme Ltd"}
        if address:
            fields["address.full"] = "1 Example Road"
        if identifiers and identifiers[i]:
            fields["entity.abn"] = identifiers[i]
        for field, value in fields.items():
            obs.append(
                {
                    "id": sid + field,
                    "source_id": sid,
                    "source_record_id": sid,
                    "field": field,
                    "value": value,
                    "raw_value": value,
                    "subject_role": "legal_entity",
                    "address_role": "registered",
                    "source_kind": "company_register",
                    "observed_at": "2025-01-01T00:00:00Z",
                    "observed_at_basis": "source record statement field",
                    "confidence": {"field_confidence": 0.9},
                    "raw_locator": {"row": 1},
                }
            )
    return obs, candidates


def judgment(**kwargs):
    return IdentityJudgment(
        choice="same_entity",
        probabilities={
            "same_entity": 0.995,
            "related_distinct": 0.002,
            "different": 0.002,
            "insufficient_evidence": 0.001,
        },
        names_compatible=0.995,
        corroborated=0.995,
        ownership_clear=0.995,
        **kwargs,
    )


def decisions(records, pairs=None):
    comps = retrieve(records)
    return [
        gate(c, records, judgment(), POLICY)
        for c in comps
        if pairs is None or (c.left[0] + c.right[0]) in pairs
    ]


def test_unanchored_complete_links_and_stable_id_on_addition():
    obs, candidates = data(2)
    records = records_from(obs, candidates)
    first = cluster(records, decisions(records))
    assert len(first["entities"]) == 1
    assert first["entities"][0]["identifiers"] == {}
    obs, candidates = data(3)
    records = records_from(obs, candidates)
    second = cluster(records, decisions(records), first["entities"])
    assert second["entities"][0]["id"] == first["entities"][0]["id"]
    assert len(second["entities"][0]["records"]) == 3
    assert all(l["human_review_status"] == "unreviewed" for l in second["links"])


def test_transitive_bridge_is_deferred_not_partitioned():
    records = records_from(*data())
    result = cluster(records, decisions(records, {"ab", "bc"}))
    assert result["entities"] == []
    assert len(result["unlinked"]) == 3
    assert result["cluster_decisions"][0]["status"] == "deferred"


def test_name_only_and_service_location_cannot_corroborate():
    for address in (False, True):
        obs, candidates = data(2, address=address)
        for o in obs:
            o["address_role"] = "service_location"
        records = records_from(obs, candidates)
        assert decisions(records)[0].status == "deferred"


def test_identifier_conflicts_and_ownership_block_model():
    records = records_from(*data(2, ["51824753556", "53004085616"]))
    assert decisions(records)[0].status == "blocked"
    records = records_from(*data(2))
    records[("a", "a")]["subject_role"] = "reporting_group"
    assert decisions(records)[0].status == "blocked"
    records[("a", "a")]["subject_role"] = "legal_entity"
    comp = retrieve(records)[0]
    j = judgment().model_copy(update={"ownership_clear": 0.5})
    assert gate(comp, records, j, POLICY).status == "deferred"


def test_attachment_needs_direct_anchor_support():
    records = records_from(*data(4, ["51824753556", "51824753556", None, None]))
    result = cluster(records, decisions(records, {"bc", "cd"}))
    assert len(result["entities"]) == 1
    assert len(result["entities"][0]["records"]) == 2
    assert result["cluster_decisions"][0]["status"] == "deferred"
    result = cluster(records, decisions(records, {"bc", "bd"}))
    assert len(result["entities"][0]["records"]) == 4


def test_two_existing_anchors_never_merge():
    records = records_from(*data(4, ["51824753556"] * 2 + ["53004085616"] * 2))
    # Artificial eligible edge tests whole-cluster enforcement even with bad input.
    ds = decisions(records)
    ds = [d.model_copy(update={"status": "eligible"}) for d in ds]
    result = cluster(records, ds)
    assert len(result["entities"]) == 2
    assert result["cluster_decisions"][0]["status"] == "deferred"


def test_candidate_union_and_frequency_evidence_hash():
    records = records_from(*data(3))
    vectors = {r: [1.0, 0.0] for r in records}
    comps = retrieve(records, vectors, top_k=1)
    assert len(comps) == 3
    assert set(comps[0].methods) == {"embedding", "fuzzy"}
    assert comps[0].features["repeated_value_flags"]["addresses"]
    reduced = {r: value for r, value in records.items() if r[0] != "c"}
    newer = comparison(comps[0].left, comps[0].right, reduced, frequencies(reduced))
    assert newer.evidence_hash != comps[0].evidence_hash


class FakeInference:
    cache_only = False

    def __init__(self, *args, **kwargs):
        pass

    def parallel(self, fn, items):
        return list(map(fn, items))

    def identity(self, evidence):
        return judgment(), "identity-artifact"

    def equivalent(self, evidence):
        return EquivalenceJudgment(equivalent=0.995), "equivalence-artifact"

    def explain(self, observations):
        return ConflictAnnotation(
            outcome="insufficient_evidence",
            explanation="Conflicting source claims.",
            observation_ids=[o["id"] for o in observations],
        ), "annotation-artifact"


def test_profile_equivalence_preserves_raw_values_and_addresses():
    obs, candidates = data(2)
    next(o for o in obs if o["id"] == "bentity.legal_name")["value"] = "ACME LIMITED"
    records = records_from(obs, candidates)
    linked = cluster(records, decisions(records))
    before = copy.deepcopy(obs)
    profile = reconcile_profiles(obs, linked["entities"], FakeInference(), POLICY)[0]
    value = profile["fields"]["entity.legal_name"]
    assert value["status"] == "selected"
    assert {p["value"] for p in value["provenance"]} == {"Acme Ltd", "ACME LIMITED"}
    assert len(profile["addresses"]) == 2
    assert obs == before
    assert profile["status"] == "provisional_profile_from_semantic_links"


def test_equivalence_bridge_does_not_collapse_three_values():
    obs, candidates = data(3)
    for o in obs:
        if o["field"] == "entity.legal_name":
            o["value"] = o["source_id"]
    records = records_from(obs, candidates)
    linked = cluster(records, decisions(records))

    class Bridge(FakeInference):
        def equivalent(self, evidence):
            pair = {evidence["left"][0]["value"], evidence["right"][0]["value"]}
            return EquivalenceJudgment(
                equivalent=0.1 if pair == {"a", "c"} else 0.995
            ), "eq"

    p = reconcile_profiles(obs, linked["entities"], Bridge(), POLICY)[0]
    assert p["fields"]["entity.legal_name"]["status"] == "unresolved"
    assert not p["reconciliation"]["equivalence_groups"]
    assert p["reconciliation"]["conflicts"][0]["outcome"] == "insufficient_evidence"


def test_model_cache_usage_and_unknown_failures():
    calls = []
    engine = Inference("job", "test", POLICY, budget=0.01, retries=2)

    def perform():
        calls.append(1)
        return {
            "usage": {"input_tokens": 100, "output_tokens": 0, "cost": 0.0000042},
            "result": 7,
        }

    args = (
        "resolution",
        POLICY.decision_model,
        {"evidence": "a"},
        perform,
        lambda r: r["result"],
    )
    assert engine._request(*args)[0] == 7
    assert engine._request(*args)[0] == 7
    assert len(calls) == 1
    engine.cache_only = True
    with pytest.raises(PendingInference):
        engine._request(
            "resolution",
            POLICY.decision_model,
            {"evidence": "changed"},
            perform,
            lambda r: r,
        )
    engine.cache_only = False

    def fail():
        raise TimeoutError("not logged")

    with pytest.raises(PendingInference):
        engine._request(
            "resolution", POLICY.decision_model, {"evidence": "b"}, fail, lambda r: r
        )
    events = store.listing("events", owner="job")
    assert len(events) == 4
    assert sum(e["status"] == "error" for e in events) == 3
    assert all(e["budget_charge_usd"] > 0 for e in events)
    from link_lens.pricing import collect, estimate

    report = estimate(collect("test"))
    assert report["per_record_llm_calls"] == 4
    assert report["unpriced_calls"] == 3
    assert report["per_record_llm_cost_usd"] is None


def test_budget_reservation_survives_restart_and_concurrency():
    engine = Inference("job", "test", POLICY, budget=0.0002, retries=0)

    def fail(_):
        try:
            engine._request(
                "resolution",
                POLICY.decision_model,
                {"x": _},
                lambda: (_ for _ in ()).throw(TimeoutError()),
                lambda r: r,
            )
        except PendingInference:
            return "pending"

    assert engine.parallel(fail, range(8)) == ["pending"] * 8
    spent = sum(e["budget_charge_usd"] for e in store.listing("events", owner="job"))
    assert 0 < spent <= 0.0002
    count = len(store.listing("events", owner="job"))
    engine = Inference("job", "test", POLICY, budget=0.0002, retries=0)
    fail(20)
    assert len(store.listing("events", owner="job")) == count


def test_bad_explanation_citations_rejected(monkeypatch):
    engine = Inference("job", "test", POLICY)

    def request(stage, name, payload, perform, validate, **kwargs):
        return validate(
            {
                "annotation": {
                    "outcome": "inference",
                    "explanation": "Maybe a rename",
                    "observation_ids": ["invented"],
                }
            }
        ), "artifact"

    monkeypatch.setattr(engine, "_request", request)
    with pytest.raises(ValueError, match="Unknown observation"):
        engine.explain(data(2)[0])


def test_enhance_frozen_batch_keeps_baseline_and_exports(tmp_path):
    from link_lens.enhancement import enhance

    obs, candidates = data(3)
    result = {
        "batch_id": "baseline",
        "run_ids": ["r"],
        "observations": obs,
        "candidates": candidates,
        "entities": [],
        "links": [],
        "unlinked": [],
        "profiles": [],
        "selection": [{"run_id": "r", "record_ids": ["a", "b", "c"]}],
        "source_impact": [],
    }
    artifact = store.json_blob(result, "baseline.json")
    store.put(
        "batches",
        "baseline",
        {
            "id": "baseline",
            "experiment_id": "test",
            "run_ids": ["r"],
            "result_artifact": artifact,
        },
        kind="pipeline",
        immutable=True,
    )
    batch = enhance(
        "baseline", POLICY, tmp_path / "out", inference_factory=FakeInference
    )
    saved = store.read_json(batch["result_artifact"])
    assert len(saved["entities"]) == 1
    assert saved["selection"] == result["selection"]
    assert saved["comparison"]["semantic_precision"] is None
    assert store.read_json(artifact) == result
    assert (tmp_path / "out" / "candidate_decisions.jsonl").exists()
    assert (tmp_path / "out" / "cost-summary.json").exists()


def test_human_evaluation_unknowns_and_leakage():
    from link_lens.enhancement_evaluation import worksheet, evaluate

    obs, candidates = data(3)
    records = records_from(obs, candidates)
    ds = decisions(records)
    linked = cluster(records, ds)
    result = {
        **linked,
        "batch_id": "b",
        "candidates": candidates,
        "observations": obs,
        "selection": [],
        "enhancement_policy": POLICY.model_dump(),
        "candidate_decisions": [d.model_dump(mode="json") for d in ds],
    }
    packet = worksheet(result)
    split = packet["items"][0]["split"]
    assert (
        evaluate(result, packet, split)["variants"]["hybrid_jev"]["semantic_precision"]
        is None
    )
    for item in packet["items"]:
        item.update(
            label="same",
            reviewer="human",
            reviewed_at="2026-09-24",
            evidence_notes="Reviewed source evidence",
        )
    assert (
        evaluate(result, packet, split)["variants"]["hybrid_jev"]["semantic_precision"]
        == 1
    )
    packet["items"][0]["split"] = "development" if split == "heldout" else "heldout"
    with pytest.raises(ValueError, match="leakage"):
        evaluate(result, packet, split)


def test_frozen_reconstruction_checks_observation_equality(monkeypatch):
    from link_lens.enhancement import frozen_candidates
    from link_lens import enhancement

    obs, candidates = data(2)
    result = {"selection": [{"run_id": "r", "record_ids": ["a"]}], "observations": obs}
    store.put("runs", "r", {"mapping_id": "m", "snapshot_id": "s"})
    store.put("mappings", "m", {"config": {}})
    store.put("snapshots", "s", {})
    monkeypatch.setattr(
        enhancement, "approved_result", lambda *a, **kw: ({}, [{"record_id": "a"}])
    )
    monkeypatch.setattr(enhancement.MappingSpec, "model_validate", lambda _: None)
    monkeypatch.setattr(
        enhancement,
        "extract",
        lambda *args: {"observations": obs, "candidates": candidates},
    )
    assert frozen_candidates(result) == candidates
    monkeypatch.setattr(
        enhancement,
        "extract",
        lambda *args: {"observations": obs[:1], "candidates": candidates},
    )
    with pytest.raises(ValueError, match="differ"):
        frozen_candidates(result)


def test_submission_output_rejected_before_read_or_inference():
    from link_lens.enhancement import enhance, validate_output

    with pytest.raises(ValueError, match="experimental directory"):
        enhance("missing", output="outputs")
    for dest in ("experiments", "experiments/terra-baseline", "outputs/onboarding"):
        with pytest.raises(ValueError):
            validate_output(dest)


def test_real_adapter_mock_http_and_embedding_validation(monkeypatch):
    from link_lens import enhancement_models

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_BASE", "https://example.invalid/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("LINK_LENS_EMBEDDING_API_BASE", raising=False)
    monkeypatch.delenv("LINK_LENS_EMBEDDING_API_KEY", raising=False)
    requests = []

    class Response:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            if "questions" in self.payload:
                return {
                    "model": "typesafe/jev-1.13-test",
                    "answers": {
                        "identity": {
                            "choice": judgment().choice,
                            "probabilities": judgment().probabilities,
                        },
                        **{
                            key: {"noul": 0.995}
                            for key in (
                                "names_compatible",
                                "corroborated",
                                "ownership_clear",
                            )
                        },
                    },
                    "usage": {"input_tokens": 10, "output_tokens": 0},
                }
            return {
                "data": [{"embedding": [3.0, 4.0]}],
                "usage": {"prompt_tokens": 10, "total_tokens": 10},
            }

    def post(url, **kwargs):
        requests.append((url, kwargs["json"]))
        return Response(kwargs["json"])

    monkeypatch.setattr(enhancement_models.httpx, "post", post)
    policy = EnhancementPolicy(dimensions=2)
    engine = Inference("job", "test", policy)
    assert engine.identity({"a": "b"})[0].choice == "same_entity"
    assert engine.embed({"name": "Acme"})[0] == [0.6, 0.8]
    assert requests[0][1]["questions"]["identity"]["type"] == "choice"
    assert requests[1][0].endswith("/v1/embeddings")
    assert len(store.listing("events", owner="job")) == 2
    invalid = Inference("invalid", "test", EnhancementPolicy(dimensions=3), retries=0)
    with pytest.raises(PendingInference):
        invalid.embed({"name": "Acme"})
    assert store.listing("events", owner="invalid")[0]["status"] == "error"


def test_cache_only_source_impact_reports_unknown_changed_evidence():
    from link_lens.enhancement import resolve_hybrid, source_impact

    obs, candidates = data(3)

    class Cache(FakeInference):
        def identity(self, evidence):
            if self.cache_only:
                raise PendingInference("Changed evidence")
            return super().identity(evidence)

    inference = Cache()
    linked = resolve_hybrid(obs, candidates, inference, POLICY)
    profiles = reconcile_profiles(obs, linked["entities"], inference, POLICY)
    reports = source_impact(
        obs, candidates, linked, profiles, inference, POLICY, [], "test"
    )
    assert all(r["status"] == "incomplete" for r in reports)
    assert all(r["profiles_with_changed_membership_support"] is None for r in reports)
    assert not inference.cache_only


def test_cli_enhancement_help_and_human_workflow(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from link_lens.cli import app
    from link_lens import enhancement

    runner = CliRunner()
    assert runner.invoke(app, ["enhance", "--help"]).exit_code == 0
    assert runner.invoke(app, ["enhance-worksheet", "--help"]).exit_code == 0
    assert runner.invoke(app, ["enhance-evaluate", "--help"]).exit_code == 0
    result = {**data_result(), "batch_id": "baseline"}
    store.put(
        "batches",
        "baseline",
        {
            "id": "baseline",
            "experiment_id": "test",
            "run_ids": [],
            "result_artifact": store.json_blob(result),
        },
    )
    original = enhancement.enhance
    monkeypatch.setattr(
        enhancement,
        "enhance",
        lambda *args, **kwargs: original(
            *args, **kwargs, inference_factory=FakeInference
        ),
    )
    response = runner.invoke(
        app,
        [
            "enhance",
            "--batch-id",
            "baseline",
            "--retrieval",
            "fuzzy",
            "--output",
            str(tmp_path / "out"),
        ],
    )
    assert response.exit_code == 0, response.output
    batch = store.listing("batches", kind="enhancement")[0]
    response = runner.invoke(
        app,
        [
            "enhance-worksheet",
            "--batch-id",
            batch["id"],
            "--output",
            str(tmp_path / "review"),
        ],
    )
    assert response.exit_code == 0, response.output
    response = runner.invoke(
        app,
        [
            "enhance-evaluate",
            "--batch-id",
            batch["id"],
            "--labels",
            str(tmp_path / "review" / "worksheet.json"),
            "--output",
            str(tmp_path / "report.json"),
        ],
    )
    assert response.exit_code == 0, response.output


def data_result():
    obs, candidates = data(3)
    return {
        "run_ids": [],
        "observations": obs,
        "candidates": candidates,
        "entities": [],
        "links": [],
        "unlinked": [],
        "profiles": [],
        "selection": [],
        "source_impact": [],
    }


def test_provisional_id_survives_later_exact_identifiers():
    records = records_from(*data(2))
    first = cluster(records, decisions(records))
    old_id = first["entities"][0]["id"]
    identified = records_from(*data(2, ["51824753556", "51824753556"]))
    second = cluster(identified, [], first["entities"])
    assert second["entities"][0]["id"] == old_id
    assert second["links"][0]["canonical_entity_key"] == old_id


def test_new_exact_evidence_cannot_merge_two_provisional_ids():
    records = records_from(*data(4))
    first = cluster(records, decisions(records, {"ab", "cd"}))
    assert len(first["entities"]) == 2
    identified = records_from(*data(4, ["51824753556"] * 4))
    second = cluster(identified, [], first["entities"])
    assert not second["entities"]
    assert second["cluster_decisions"][0]["status"] == "deferred"


def test_sparse_names_reach_model_but_remain_review_candidates():
    from link_lens.enhancement import resolve_hybrid

    obs, candidates = data(2, address=False)

    class Count(FakeInference):
        calls = 0

        def identity(self, evidence):
            self.calls += 1
            return super().identity(evidence)

    inference = Count()
    result = resolve_hybrid(obs, candidates, inference, POLICY)
    assert inference.calls == 1
    assert not result["links"]
    assert result["candidate_decisions"][0]["judgment"]["choice"] == "same_entity"
    assert result["review_candidates"][0]["labels"] == [["Acme Ltd"], ["Acme Ltd"]]
    assert result["review_candidates"][0]["human_review_status"] == "unreviewed"


def location_data(service=False):
    obs, candidates = data(2, address=service)
    for c in candidates:
        c["label"] = "Northbridge Community Care"
    for o in obs:
        if o["field"] == "entity.legal_name":
            o["value"] = "Northbridge Community Care"
        o["address_role"] = (
            "service_location" if service and o["source_id"] == "a" else "business"
        )
    for sid in ("a", "b"):
        base = next(o for o in obs if o["source_id"] == sid)
        for field, value in [
            ("address.postcode", "2000"),
            ("address.locality", "Sydney"),
            ("address.state", "NSW"),
        ]:
            obs.append({**base, "id": sid + field, "field": field, "value": value})
    return obs, candidates


def test_alternative_location_evidence_and_service_roles():
    for service in (False, True):
        obs, candidates = location_data(service)
        records = records_from(obs, candidates)
        comp = retrieve(records)[0]
        route = (
            "service_name_full_address_postcode"
            if service
            else "distinctive_name_and_location"
        )
        assert route in comp.features["admission_routes"]
        assert gate(comp, records, judgment(), POLICY).status == "eligible"
        # A high same-entity score cannot override a low ownership assessment.
        uncertain = judgment().model_copy(update={"ownership_clear": 0.4})
        assert gate(comp, records, uncertain, POLICY).status == "deferred"
        next(o for o in obs if o["id"] == "baddress.postcode")["value"] = "3000"
        records = records_from(obs, candidates)
        assert route not in retrieve(records)[0].features["admission_routes"]
        assert (
            gate(retrieve(records)[0], records, judgment(), POLICY).status == "deferred"
        )


def test_postcode_only_and_generic_name_are_not_alternative_identity():
    obs, candidates = location_data()
    obs = [o for o in obs if o["field"] != "address.locality"]
    records = records_from(obs, candidates)
    assert not retrieve(records)[0].features["admission_routes"]
    obs, candidates = location_data()
    for c in candidates:
        c["label"] = "Australian Financial Services"
    for o in obs:
        if o["field"] == "entity.legal_name":
            o["value"] = "Australian Financial Services"
    records = records_from(obs, candidates)
    assert not retrieve(records)[0].features["admission_routes"]


def test_cached_v1_embeddings_are_reused_by_v2_batcher(monkeypatch):
    from link_lens.contracts import content_hash
    from link_lens.semantic_resolution import evidence_text
    from link_lens import enhancement_models

    monkeypatch.setenv("OPENAI_API_BASE", "https://example.invalid/v1")
    monkeypatch.delenv("LINK_LENS_EMBEDDING_API_BASE", raising=False)
    policy = EnhancementPolicy(dimensions=2)
    engine = Inference("cache-job", "test", policy)
    evidence = evidence_text(next(iter(records_from(*data(2)).values())))
    assert evidence["serialization_version"] == "hybrid-evidence-1"
    endpoint, payload = engine.embedding_request(evidence)
    key = "enhance-cache-" + content_hash(
        {
            "version": "hybrid-evidence-1",
            "model": policy.embedding_model,
            "endpoint": endpoint,
            "stage": "embedding",
            "payload": payload,
        }
    )
    artifact = store.json_blob({"data": [{"embedding": [3.0, 4.0]}]})
    store.put(
        "batches",
        key,
        {"id": key, "response_artifact": artifact},
        kind="enhancement_cache",
    )
    monkeypatch.setattr(
        enhancement_models.httpx,
        "post",
        lambda *a, **kw: pytest.fail("Cache reuse must not make paid requests"),
    )
    assert engine.embed_many([(("a", "a"), evidence)])[0][1] == [0.6, 0.8]
    assert not store.listing("events", owner="cache-job")
    assert engine.stats["cache_hits"] == 1


def test_embedding_batch_indices_dedup_and_single_accounting(monkeypatch):
    from link_lens import enhancement_models

    monkeypatch.setenv("OPENAI_API_BASE", "https://example.invalid/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("LINK_LENS_EMBEDDING_API_BASE", raising=False)
    requests = []

    class Response:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return {
                "data": [
                    {"index": i, "embedding": [float(i + 1), 1.0]}
                    for i in reversed(range(len(self.payload["input"])))
                ],
                "usage": {"prompt_tokens": 20, "total_tokens": 20},
            }

    def post(url, **kw):
        requests.append(kw["json"])
        assert isinstance(kw["json"]["input"], list)
        return Response(kw["json"])

    monkeypatch.setattr(enhancement_models.httpx, "post", post)
    engine = Inference("batch-job", "test", EnhancementPolicy(dimensions=2))
    items = [
        (("a", "a"), {"name": "one"}),
        (("b", "b"), {"name": "two"}),
        (("c", "c"), {"name": "one"}),
    ]
    results = engine.embed_many(items)
    assert len(requests) == 1
    assert len(requests[0]["input"]) == 2
    assert results[0][1] == results[2][1]
    assert results[0][1] != results[1][1]
    events = store.listing("events", owner="batch-job")
    assert len(events) == 1 and events[0]["input_tokens"] == 20
    assert events[0]["estimated_cost_usd"] == pytest.approx(0.0000004)
    # Batch-created slices can be reused individually, without duplicate usage receipts.
    assert engine.embed({"name": "one"})[0] == results[0][1]
    fresh = Inference("next-job", "test", EnhancementPolicy(dimensions=2))
    assert fresh.embed_many(items) == results
    assert len(requests) == 1
    assert not store.listing("events", owner="next-job")


def test_new_pair_limit_does_not_count_cache_hits():
    engine = Inference("limit-job", "test", POLICY)
    engine.max_pairs = 1
    response = {"usage": {"input_tokens": 10, "output_tokens": 0}, "answer": "yes"}
    fn = lambda: response
    parse = lambda raw: raw["answer"]
    assert (
        engine._request("resolution", POLICY.decision_model, {"pair": 1}, fn, parse)[0]
        == "yes"
    )
    assert (
        engine._request("resolution", POLICY.decision_model, {"pair": 1}, fn, parse)[0]
        == "yes"
    )
    with pytest.raises(PendingInference, match="New-pair limit"):
        engine._request("resolution", POLICY.decision_model, {"pair": 2}, fn, parse)
    assert len(store.listing("events", owner="limit-job")) == 1


def test_preflight_only_warns_without_instantiating_inference():
    from link_lens.enhancement import enhance

    result = data_result()
    store.put(
        "batches",
        "b",
        {
            "id": "b",
            "experiment_id": "test",
            "run_ids": [],
            "result_artifact": store.json_blob(result),
        },
    )
    # Remove full addresses to reproduce the live sparse-field failure.
    result["observations"] = [
        o for o in result["observations"] if o["field"] != "address.full"
    ]
    store.put(
        "batches",
        "b",
        {
            "id": "b",
            "experiment_id": "test",
            "run_ids": [],
            "result_artifact": store.json_blob(result),
        },
    )

    def prohibited(*args, **kw):
        pytest.fail("Preflight cannot instantiate inference")

    report = enhance("b", preflight_only=True, inference_factory=prohibited)
    assert report["model_calls"] == 0
    assert report["preflight"]["warnings"]
    assert report["preflight"]["assessable_lexical_pairs"] == 3


def test_progress_is_stderr_and_does_not_corrupt_json(capsys):
    from link_lens.enhancement_progress import Progress

    progress = Progress(interval=0)
    progress("embedding", completed=5, total=10)
    print('{"ok": true}')
    result = capsys.readouterr()
    assert "embedding" in result.err and "completed=5" in result.err
    assert result.out.strip() == '{"ok": true}'
