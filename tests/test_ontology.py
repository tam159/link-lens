import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path

import pytest

from link_lens import ontology, store, budget
from link_lens.contracts import MappingSpec, content_hash, Operation
from link_lens.extraction import extract, operation
from link_lens.profiles import assemble_profiles, impact
from link_lens.settings import settings
from link_lens.ontology_workflow import (
    Proposal,
    Disposition,
    check_proposal,
    evidence_for,
)


def extension():
    parent = ontology.legacy()
    concepts = [
        ontology.Concept(
            name="contact.phone",
            definition="Telephone for the source contact record",
            type="string",
            scope="contact",
        ),
        ontology.Concept(
            name="financial.period",
            definition="Source stated reporting period",
            type="string",
            scope="financial_period",
        ),
        ontology.Concept(
            name="financial.currency",
            definition="Source documented currency code",
            type="string",
            scope="financial_period",
        ),
        ontology.Concept(
            name="financial.tax",
            definition="Tax payable for this reporting period",
            type="decimal",
            scope="financial_period",
            requires=["financial.period", "financial.currency"],
        ),
        ontology.Concept(
            name="site.latitude",
            definition="Source stated site latitude in degrees",
            type="decimal",
            scope="service_location",
            minimum="-90",
            maximum="90",
        ),
    ]
    document = {
        "version": "test",
        "parent_hash": ontology.digest(parent),
        "concepts": {
            **parent["concepts"],
            **{c.name: c.model_dump() for c in concepts},
        },
    }
    return ontology.register(document)


def scoped_spec(spec):
    data = spec.model_dump()
    data["ontology_hash"] = extension()
    for source, target, group in [
        ("phone", "contact.phone", "site_contact"),
        ("period", "financial.period", "tax_return"),
        ("currency", "financial.currency", "tax_return"),
        ("tax", "financial.tax", "tax_return"),
    ]:
        data["fields"].append(
            {
                "source_fields": [source],
                "canonical_field": target,
                "group": group,
                "transformations": [{"op": "trim"}],
                "confidence": 0.9,
                "evidence": "Explicit synthetic source column",
            }
        )
    return MappingSpec.model_validate(data)


def test_six_legacy_mapping_hashes_unchanged():
    paths = list(
        Path("experiments/jev-luna-v1-submission/outputs/mappings").glob("*.json")
    )
    assert len(paths) == 6
    for path in paths:
        data = json.loads(path.read_text())
        assert (
            content_hash(MappingSpec.model_validate(data["config"]))
            == data["config_hash"]
        )


def test_promoted_ontology_seeds_new_experiments_without_rebinding_existing():
    import yaml

    submitted = yaml.safe_load(Path("firmable_ontology.yaml").read_text())
    assert ontology.active_hash("fresh-experiment") == ontology.digest(submitted)
    legacy_hash = ontology.register(ontology.legacy())
    ontology.activate(legacy_hash, "existing-experiment")
    assert ontology.active_hash("existing-experiment") == legacy_hash
    for path in Path("outputs/mappings").glob("*.json"):
        mapping = json.loads(path.read_text())
        assert mapping["config"]["ontology_hash"] == ontology.digest(submitted)
        assert (
            content_hash(MappingSpec.model_validate(mapping["config"]))
            == mapping["config_hash"]
        )


def test_additive_immutable_ontology():
    key = extension()
    original = ontology.resolve(key)
    altered = deepcopy(original)
    altered["concepts"]["entity.legal_name"]["definition"] = (
        "Different legal meaning for this identifier"
    )
    with pytest.raises(ValueError, match="additive"):
        ontology.register(altered)
    record = store.require("ontologies", key)
    record["version"] = "tampered"
    with pytest.raises(ValueError, match="Immutable"):
        store.put("ontologies", key, record, immutable=True)


def test_registry_target_and_scope(spec):
    data = spec.model_dump()
    data["fields"][0]["canonical_field"] = "invented.value"
    with pytest.raises(ValueError, match="Unknown ontology"):
        MappingSpec.model_validate(data)
    data = scoped_spec(spec).model_dump()
    data["fields"][-1]["group"] = None
    with pytest.raises(ValueError, match="group"):
        MappingSpec.model_validate(data)


def test_scoped_finances_contacts_and_missing_values(spec, snapshot):
    spec = scoped_spec(spec)
    rows = [
        {
            "record_id": str(i),
            "locator": {"row": i},
            "values": {
                "name": "A",
                "abn": "51824753556",
                "phone": phone,
                "period": year,
                "currency": "AUD",
                "tax": tax,
            },
        }
        for i, (year, phone, tax) in enumerate(
            [
                ("2023-24", "123", "100.01"),
                ("2024-25", "456", "200.02"),
                ("", "789", "300.03"),
                ("2025-26", "987", ""),
            ]
        )
    ]
    result = extract(spec, rows, snapshot)
    taxes = [o for o in result["observations"] if o["field"] == "financial.tax"]
    assert [o["value"] for o in taxes] == ["100.01", "200.02"]
    entities = [
        {
            "id": "entity",
            "records": [[snapshot["source_id"], r["record_id"]] for r in rows],
        }
    ]
    profile = assemble_profiles(result["observations"], entities)[0]
    assert "contact.phone" not in profile["fields"]
    assert "financial.tax" not in profile["fields"]
    assert len(profile["groups"]) == 8
    assert len({o["group_id"] for o in taxes}) == 2
    assert result["issues"][0]["reason"] == "Missing required companion value"
    assert (
        impact(result["observations"], result["candidates"], entities, [profile])[0][
            "profiles_with_value_changes"
        ]
        == 1
    )


def test_types_bounds_and_categories():
    assert (
        ontology.scalar("9007199254740993.01", {"type": "decimal"})
        == "9007199254740993.01"
    )
    assert ontology.scalar("false", {"type": "boolean"}) is False
    assert ontology.scalar("3", {"type": "integer"}) == 3
    for value in ["91", "NaN", "Infinity"]:
        with pytest.raises(ValueError):
            ontology.scalar(
                value, {"type": "decimal", "minimum": "-90", "maximum": "90"}
            )
    assert operation(
        {"A": "Y", "B": "N"},
        Operation(
            op="indicator_categories",
            argument="Y",
            values={"A": "education", "B": "health"},
        ),
    ) == ["education"]
    with pytest.raises(ValueError):
        ontology.scalar("1.5", {"type": "integer"})


def test_scoped_value_comparison_survives_serialization():
    from link_lens.profiles import values_only

    profile = {
        "fields": {},
        "groups": [
            {
                "id": "licence",
                "fields": {
                    "licence.conditions": {
                        "status": "multiple_values",
                        "values": [
                            {
                                "value": "Condition A",
                                "authority_rank": (50, 1, "2026"),
                                "provenance": [{"source_id": "a"}],
                            }
                        ],
                    }
                },
            }
        ],
    }
    restored = json.loads(json.dumps(profile))
    assert values_only(profile) == values_only(restored)
    restored["groups"][0]["fields"]["licence.conditions"]["values"][0][
        "provenance"
    ] = []
    assert values_only(profile) == values_only(restored)
    restored["groups"][0]["fields"]["licence.conditions"]["values"][0]["value"] = (
        "Condition B"
    )
    assert values_only(profile) != values_only(restored)


def test_scoped_observations_never_reach_identity_model():
    from link_lens.enhancement import evaluate_pairs
    from link_lens.enhancement_contracts import CandidateComparison, EnhancementPolicy
    from link_lens.enhancement_models import PendingInference

    company = {"field": "entity.legal_name", "value": "Example", "ontology_hash": "v1"}
    scoped = {
        "field": "registration.business_name_abn",
        "value": "SCOPED-IDENTIFIER-SENTINEL",
        "ontology_hash": "v1",
        "group_id": "registration-row",
    }
    records = {
        (source, "row"): {
            "subject_role": "legal_entity",
            "identifiers": {"entity.abn": [], "entity.acn": []},
            "observations": [company, scoped],
        }
        for source in ("a", "b")
    }

    class Judge:
        calls = 0

        def parallel(self, fn, items):
            return [fn(item) for item in items]

        def identity(self, evidence):
            self.calls += 1
            assert "SCOPED-IDENTIFIER-SENTINEL" not in json.dumps(evidence)
            for side in ("left", "right"):
                assert evidence[side]["observations"] == [company]
                assert evidence[side]["ontology_hashes"] == ["v1"]
            raise PendingInference("No live inference in this test")

    judge = Judge()
    decisions = evaluate_pairs(
        records,
        [
            CandidateComparison(
                id="pair",
                left=("a", "row"),
                right=("b", "row"),
                methods=["fuzzy"],
                scores={"fuzzy": 1.0},
                evidence_hash="frozen",
                features={},
            )
        ],
        judge,
        EnhancementPolicy(),
    )
    assert judge.calls == 1 and decisions[0].status == "pending"
    assert records[("a", "row")]["observations"] == [company, scoped]


def test_evidence_excludes_heldout():
    pack = {
        "reader": {},
        "headers": ["X"],
        "partitions": {
            "discovery": [{"values": {"X": "discovery-only"}}],
            "validation": [{"secret": "validation-sentinel"}],
            "final": [{"secret": "final-sentinel"}],
        },
    }
    artifact = store.json_blob(pack)
    store.put(
        "runs",
        "r",
        {
            "partitions_artifact": artifact,
            "snapshot_id": "s",
            "source_id": "src",
            "validation": {"secret": "validation-feedback"},
        },
    )
    store.put("snapshots", "s", {"sha256": "hash"})
    store.put("sources", "src", {"metadata": {"title": "Source"}})
    serialized = json.dumps(evidence_for("r"))
    assert "discovery-only" in serialized
    assert (
        "validation-sentinel" not in serialized
        and "final-sentinel" not in serialized
        and "validation-feedback" not in serialized
    )


def test_proposal_coverage_and_evidence():
    evidence = [{"run_id": "r", "headers": ["Phone"]}]
    concept = ontology.Concept(
        name="contact.phone",
        definition="Source contact telephone number",
        type="string",
        scope="contact",
    )
    decision = Disposition(
        run_id="r",
        source_field="Phone",
        disposition="new_concept",
        target="contact.phone",
        evidence_quote="Phone",
        reason="A contact field needs its own scope",
    )
    proposal = Proposal(concepts=[concept], dispositions=[decision])
    check_proposal(proposal, evidence, ontology.legacy())
    proposal.dispositions.append(decision)
    with pytest.raises(ValueError, match="exactly once"):
        check_proposal(proposal, evidence, ontology.legacy())
    proposal.dispositions = [decision.model_copy(update={"evidence_quote": "invented"})]
    with pytest.raises(ValueError, match="Evidence quote"):
        check_proposal(proposal, evidence, ontology.legacy())


def test_global_reservations_concurrency_and_unknown_usage(monkeypatch):
    monkeypatch.setenv("LINK_LENS_MAX_COST_USD", "0.1")
    monkeypatch.delenv("LINK_LENS_INPUT_USD_PER_MILLION", raising=False)
    monkeypatch.delenv("LINK_LENS_OUTPUT_USD_PER_MILLION", raising=False)
    settings.cache_clear()

    def attempt(stage):
        try:
            return budget.reserve("experiment", stage, stage, "gpt-6-luna", 200000, 0)
        except budget.BudgetExceeded:
            return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        keys = list(pool.map(attempt, ["triage", "ontology", "onboarding", "enhance"]))
    assert sum(k is not None for k in keys) == 2
    key = next(k for k in keys if k)
    before = budget.summary("experiment")["charged_usd"]
    budget.settle(key)
    assert budget.summary("experiment")["charged_usd"] == before
    budget.settle(key, 0, 0)
    assert budget.summary("experiment")["charged_usd"] < before
    assert attempt("retry")


def test_archive_registry_roundtrip(tmp_path):
    from link_lens.frozen import freeze, thaw

    key = extension()
    ontology.activate(key, "test")
    path = tmp_path / "evidence.zip"
    freeze(path)
    for table in reversed(list(store.TABLES.values())):
        with store.engine().begin() as connection:
            connection.execute(table.delete())
    thaw(path)
    assert ontology.active_hash("test") == key
    assert ontology.resolve(key)["concepts"]["contact.phone"]["scope"] == "contact"


def test_new_ontology_invalidates_mapping_approval(spec, snapshot):
    from link_lens.pipeline import approved_result

    old = scoped_spec(spec)
    run = {
        "id": "r",
        "source_slug": "s",
        "status": "completed",
        "ontology_hash": ontology.digest(ontology.legacy()),
        "mapping_id": "m",
        "approval_id": "a",
    }
    store.put(
        "mappings", "m", {"config": old.model_dump(), "config_hash": content_hash(old)}
    )
    store.put(
        "approvals", "a", {"decision": "approved", "config_hash": content_hash(old)}
    )
    with pytest.raises(ValueError, match="Stale"):
        approved_result(run)


def test_enhancement_cannot_reconcile_scoped_periods(spec, snapshot):
    from link_lens.reconciliation import reconcile_profiles
    from link_lens.enhancement_contracts import EnhancementPolicy

    class NoCalls:
        def equivalent(self, *args):
            pytest.fail("Scoped periods must not be compared")

        def explain(self, *args):
            pytest.fail("Scoped periods must not be explained as conflicts")

    mapping = scoped_spec(spec)
    rows = [
        {
            "record_id": str(i),
            "locator": {},
            "values": {
                "name": "A",
                "abn": "51824753556",
                "phone": str(i),
                "tax": str(i),
                "period": str(2020 + i),
                "currency": "AUD",
            },
        }
        for i in range(2)
    ]
    result = extract(mapping, rows, snapshot)
    entities = [
        {"id": "e", "records": [[snapshot["source_id"], str(i)] for i in range(2)]}
    ]
    profiles = reconcile_profiles(
        result["observations"], entities, NoCalls(), EnhancementPolicy()
    )
    assert len(profiles[0]["groups"]) == 4
    assert not profiles[0]["reconciliation"]["decisions"]


def test_embedding_cache_bound_to_ontology(monkeypatch):
    from link_lens.semantic_resolution import evidence_text
    from link_lens.enhancement_models import Inference
    from link_lens.enhancement_contracts import EnhancementPolicy

    monkeypatch.setenv("OPENAI_API_BASE", "https://example.invalid/v1")
    engine = Inference("job", "test", EnhancementPolicy())

    record = {
        "subject_role": "legal_entity",
        "label": "A",
        "observations": [
            {"field": "entity.legal_name", "value": "A", "ontology_hash": "first"}
        ],
    }
    first = evidence_text(record)
    record["observations"][0]["ontology_hash"] = "second"
    second = evidence_text(record)
    assert content_hash(first) != content_hash(second)
    endpoint, a = engine.embedding_request(first)
    _, b = engine.embedding_request(second)
    assert a["input"] == b["input"]
    assert "ontology_hashes" not in a["input"]
    assert engine.cache_key(
        "embedding", "text-embedding-3-small", a, endpoint
    ) != engine.cache_key("embedding", "text-embedding-3-small", b, endpoint)


def test_budget_keeps_legacy_attempts_after_new_reservations(monkeypatch):
    monkeypatch.setenv("LINK_LENS_MAX_COST_USD", "10")
    settings.cache_clear()
    store.put(
        "runs",
        "r",
        {
            "id": "r",
            "experiment_id": "e",
            "model": "gpt-6-luna",
            "input_tokens": 1000000,
            "output_tokens": 0,
        },
    )


def test_interrupted_reservation_is_exported_once():
    from link_lens.pricing import collect, estimate

    reservation_id = budget.reserve("test", "job", "resolution", "gpt-6-luna", 100, 10)
    missing = collect("test")
    assert len(missing) == 1 and missing[0]["reservation_id"] == reservation_id
    assert estimate(missing)["unpriced_calls"] == 1
    store.event(
        "job",
        "enhancement_usage",
        {
            "experiment_id": "test",
            "reservation_id": reservation_id,
            "stage": "resolution",
            "model": "gpt-6-luna",
            "status": "failed",
            "budget_charge_usd": 0.001,
        },
    )
    assert len(collect("test")) == 1
    previous = budget.summary("e")["charged_usd"]
    key = budget.reserve("e", "r", "retry", "gpt-6-luna", 1000, 1000)
    budget.settle(key, 0, 0)
    assert budget.summary("e")["charged_usd"] == previous


def test_concept_rejections_do_not_block_unrelated_additions():
    from link_lens.ontology_workflow import (
        OntologyReview,
        ConceptDecision,
        reviewed_subset,
    )

    concepts = [
        ontology.Concept(
            name="contact.phone",
            definition="Site contact phone as source reported",
            scope="contact",
            type="string",
        ),
        ontology.Concept(
            name="financial.period",
            definition="A reporting period identified by the source",
            scope="financial_period",
            type="string",
        ),
        ontology.Concept(
            name="financial.tax",
            definition="Period-specific tax payable as source reported",
            scope="financial_period",
            type="decimal",
            requires=["financial.period"],
        ),
    ]
    proposal = Proposal(
        concepts=concepts,
        dispositions=[
            Disposition(
                run_id="s",
                source_field=c.name,
                disposition="new_concept",
                target=c.name,
                evidence_quote=c.name,
                reason="Synthetic exact source header",
            )
            for c in concepts
        ],
    )
    review = OntologyReview(
        decisions=[
            ConceptDecision(
                name=c.name,
                acceptable=c.name != "financial.period",
                reason="Synthetic evidence decision for this concept",
            )
            for c in concepts
        ],
        warnings=[],
    )
    released = reviewed_subset(proposal, review)
    assert [c.name for c in released.concepts] == ["contact.phone"]
    assert [d.disposition for d in released.dispositions] == [
        "new_concept",
        "insufficient_evidence",
        "insufficient_evidence",
    ]
    assert proposal.dispositions[1].target == "financial.period"
    review.decisions.pop()
    with pytest.raises(ValueError, match="every proposed concept"):
        reviewed_subset(proposal, review)
