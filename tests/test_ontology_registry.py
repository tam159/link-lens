"""The ontology registry: digest parity, database rules, gate, export and backfill."""

import json
import zipfile
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from link_lens import backfill, ontology, ontology_export, ontology_gate, store
from link_lens import ontology_workflow as workflow
from link_lens.cli import app
from link_lens.db import ontology as registry
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from typer.testing import CliRunner

ROOT = ontology.digest(ontology.legacy())


def concept(name, scope, **fields):
    return ontology.Concept(
        name=name,
        definition=f"Synthetic definition of {name}",
        type=fields.pop("type", "string"),
        scope=scope,
        **fields,
    ).model_dump()


def child(*concepts, parent=None, version="test"):
    parent = parent or ontology.legacy()
    return {
        "version": version,
        "parent_hash": ontology.digest(parent),
        # A copy: the packaged ontology is cached and must never be edited.
        "concepts": deepcopy(
            {**parent["concepts"], **{c["name"]: c for c in concepts}}
        ),
    }


def rich():
    """A version using every feature a concept can have."""
    return child(
        concept("financial.period", "financial_period"),
        concept("financial.currency", "financial_period"),
        concept(
            "financial.tax",
            "financial_period",
            type="decimal",
            requires=["financial.period", "financial.currency"],
        ),
        concept(
            "site.latitude",
            "service_location",
            type="decimal",
            minimum="-90",
            maximum="90.50",
        ),
        concept(
            "site.kind",
            "service_location",
            type="enum",
            values=["z last", "A first"],
            cardinality="many",
        ),
    )


def count(table):
    with store.engine().connect() as connection:
        return connection.execute(select(func.count()).select_from(table)).scalar_one()


def test_rows_rebuild_each_document_and_hash_exactly():
    submitted = yaml.safe_load(Path("firmable_ontology.yaml").read_text())
    for document in (ontology.legacy(), rich(), submitted):
        key = ontology.register(document)
        rebuilt = ontology.resolve(key)
        assert ontology.digest(rebuilt) == key == ontology.digest(document)
        # Same order too, so `ontology show` prints what it always printed.
        assert json.dumps(rebuilt) == json.dumps(document)
        with store.engine().connect() as connection:
            artifact = registry.version(connection, key)["document_artifact"]
        assert store.read_json(artifact) == document
    assert ontology.resolve(ROOT) == ontology.legacy()


def test_additive_versions_share_their_parents_concept_rows():
    ontology.register(ontology.legacy())
    before = count(registry.concept)
    key = ontology.register(rich())
    assert count(registry.concept) == before + 5
    assert ontology.register(rich()) == key  # registering again changes nothing
    assert count(registry.concept) == before + 5
    assert count(registry.ontology_version) == 2
    with store.engine().connect() as connection:
        introduced = connection.execute(
            select(registry.concept.c.introduced_in).where(
                registry.concept.c.name == "financial.tax"
            )
        ).scalar_one()
    assert introduced == key


def test_document_that_would_change_its_hash_is_refused():
    document = rich()
    del document["concepts"]["site.kind"]["requires"]  # valid, but not canonical
    with pytest.raises(ValueError, match="canonical form"):
        ontology.register(document)
    with pytest.raises(KeyError):
        ontology.resolve(ontology.digest(document))
    with pytest.raises(KeyError):
        ontology.resolve("not-a-hash")


@pytest.mark.parametrize("change", ["remove", "redefine"])
def test_database_rejects_a_version_that_is_not_additive(change):
    parent_key = ontology.register(rich())
    document = child(concept("contact.phone", "contact"), parent=rich(), version="bad")
    if change == "remove":
        del document["concepts"]["entity.legal_name"]
    else:
        document["concepts"]["entity.legal_name"]["definition"] = "A different meaning"
    key = ontology.digest(document)
    # Bypass ontology.register, which refuses this before reaching the database.
    with pytest.raises(IntegrityError, match="removes or redefines"):
        with store.engine().begin() as connection:
            registry.insert_version(connection, key, document, key, ontology.digest)
    with pytest.raises(KeyError):
        ontology.resolve(key)
    assert ontology.resolve(parent_key) == rich()


def test_every_registry_table_is_append_only():
    with store.engine().connect() as connection:
        guarded = set(
            connection.execute(
                text(
                    "SELECT tgrelid::regclass::text FROM pg_trigger "
                    "WHERE tgname = 'forbid_update' "
                    "AND tgrelid::regclass::text LIKE 'ontology.%'"
                )
            ).scalars()
        )
    assert guarded == {f"ontology.{table.name}" for table in registry.TABLES}
    ontology.activate(ontology.register(rich()), "experiment")
    with store.engine().connect() as connection:
        with pytest.raises(DBAPIError, match="append-only"):
            connection.execute(
                text("UPDATE ontology.activation SET status = 'promoted'")
            )


def latest(experiment):
    with store.engine().connect() as connection:
        return registry.latest_activation(connection, experiment)


def test_latest_activation_is_current_and_history_is_kept():
    first, second = ROOT, ontology.register(rich())
    record = ontology.activate(first, "experiment")
    assert record == {
        "ontology_hash": first,
        "experiment_id": "experiment",
        "reviewer": None,
        "status": "experimental",
        "created_at": record["created_at"],
    }
    assert latest("experiment") == record
    ontology.activate(first, "other")
    ontology.activate(second, "experiment")
    assert ontology.active_hash("experiment") == second
    assert ontology.active_hash("other") == first
    assert count(registry.activation) == 3


def stub_gate(monkeypatch, **results):
    """Replace checks so the gate needs no optional packages."""
    for name in ontology_gate.CHECKS:
        result = results.get(name, "pass")
        monkeypatch.setitem(
            ontology_gate.CHECKS,
            name,
            lambda key, document, r=result: (r, {"stub": True}),
        )


def test_promotion_needs_a_gate_run_without_failures(monkeypatch):
    key = ontology.register(rich())
    with pytest.raises(ValueError, match="requires a gate report"):
        ontology.activate(key, "experiment", "reviewer")

    stub_gate(monkeypatch, linkml="fail", additive="fail")
    assert ontology_gate.run(key)["blocks_promotion"]
    with pytest.raises(ValueError, match="failed gate checks: additive, linkml"):
        ontology.activate(key, "experiment", "reviewer")
    assert count(registry.activation) == 0

    stub_gate(monkeypatch, impact="unknown")
    report = ontology_gate.run(key)
    assert not report["blocks_promotion"]
    promoted = ontology.activate(key, "experiment", "reviewer")
    assert promoted["status"] == "promoted" and promoted["reviewer"] == "reviewer"
    # The unknown result is shown to the reviewer and stored with the promotion.
    assert promoted["gate"]["results"]["impact"] == "unknown"
    assert promoted["gate"]["run_at"] == report["run_at"]
    with store.engine().connect() as connection:
        stored = connection.execute(select(registry.activation)).one()
    assert stored.gate_results == promoted["gate"]["results"]
    assert ontology.active_hash("experiment") == key
    assert count(registry.gate_report) == 2 * len(ontology_gate.CHECKS)

    # Only the latest run counts: a later failure blocks the next promotion.
    stub_gate(monkeypatch, registry_digest="fail")
    ontology_gate.run(key)
    with pytest.raises(ValueError, match="registry_digest"):
        ontology.activate(key, "experiment", "reviewer")


def test_gate_without_linkml_still_checks_digest_additivity_and_impact(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "linkml", None)  # as if the group is not installed
    report = ontology_gate.run(ontology.register(rich()))
    results = {c["check"]: c["result"] for c in report["checks"]}
    assert results == {
        "registry_digest": "pass",
        "linkml": "unknown",
        "additive": "pass",
        "shacl_observations": "unknown",
        "impact": "pass",
        "open_ontologies": "unknown",
    }
    additive = next(c for c in report["checks"] if c["check"] == "additive")["detail"]
    assert additive["added"] == sorted(
        [
            "financial.period",
            "financial.currency",
            "financial.tax",
            "site.latitude",
            "site.kind",
        ]
    )
    assert ontology_gate.run(ROOT)["checks"][2]["detail"]["root"] is True


def test_a_check_that_raises_counts_as_failed(monkeypatch):
    def broken(key, document):
        raise RuntimeError("cannot run")

    stub_gate(monkeypatch)
    monkeypatch.setitem(ontology_gate.CHECKS, "linkml", broken)
    report = ontology_gate.run(ROOT)
    assert report["blocks_promotion"]
    assert report["checks"][1]["detail"] == {"error": "RuntimeError: cannot run"}


def test_linkml_maps_scopes_concepts_enums_cardinality_and_bounds():
    document = rich()
    schema = ontology_export.linkml(document, ontology.digest(document))
    assert set(schema["classes"]) == {
        "Entity",
        "Address",
        "FinancialPeriod",
        "ServiceLocation",
        "Observation",
    }
    location = schema["classes"]["ServiceLocation"]["attributes"]
    assert location["site_latitude"] == {
        "description": "Synthetic definition of site.latitude",
        "range": "decimal",
        "annotations": {"concept": "site.latitude"},
        "minimum_value": -90,
        "maximum_value": 90.5,
    }
    assert location["site_kind"]["range"] == "SiteKindValue"
    assert location["site_kind"]["multivalued"] is True
    assert list(schema["enums"]["SiteKindValue"]["permissible_values"]) == [
        "z last",
        "A first",
    ]
    tax = schema["classes"]["FinancialPeriod"]["attributes"]["financial_tax"]
    assert tax["annotations"]["requires"] == "financial.period, financial.currency"
    assert "legal_name" in schema["classes"]["Entity"]["attributes"]
    assert list(schema["enums"]["ConceptName"]["permissible_values"]) == list(
        document["concepts"]
    )


def test_committed_linkml_file_matches_the_promoted_ontology():
    submitted = yaml.safe_load(Path("firmable_ontology.yaml").read_text())
    exported = ontology_export.linkml_yaml(submitted, ontology.digest(submitted))
    assert Path("firmable_ontology.linkml.yaml").read_text() == exported
    assert (
        yaml.safe_load(Path(".linkmllint.yaml").read_text())
        == ontology_export.LINT_CONFIG
    )


def test_generated_linkml_lints_clean_and_lists_every_concept():
    pytest.importorskip("linkml")
    for document in (
        rich(),
        yaml.safe_load(Path("firmable_ontology.yaml").read_text()),
    ):
        key = ontology.digest(document)
        assert ontology_export.lint(ontology_export.linkml_yaml(document, key)) == []
        schema = json.loads(ontology_export.json_schema(document, key))
        assert set(schema["$defs"]["ConceptName"]["enum"]) == set(document["concepts"])
    assert len(schema["$defs"]["ConceptName"]["enum"]) == 59


def test_generated_shacl_accepts_and_rejects_claims():
    pytest.importorskip("linkml")
    pyshacl = pytest.importorskip("pyshacl")
    from rdflib import Graph

    document = rich()
    shapes = Graph().parse(
        data=ontology_export.shacl(document, ontology.digest(document)), format="turtle"
    )
    prefix = f"@prefix l: <{ontology_export.BASE}> .\n"

    def conforms(turtle):
        return pyshacl.validate(
            Graph().parse(data=prefix + turtle, format="turtle"), shacl_graph=shapes
        )[0]

    assert conforms('[] a l:Observation ; l:concept "site.latitude" ; l:value "12.5" .')
    assert not conforms('[] a l:Observation ; l:concept "invented.name" .')
    assert conforms("[] a l:ServiceLocation ; l:site_latitude 12.5 .")
    assert not conforms("[] a l:ServiceLocation ; l:site_latitude 91.0 .")
    assert not conforms('[] a l:ServiceLocation ; l:site_kind "not a value" .')


def test_real_gate_passes_linkml_for_a_valid_version():
    pytest.importorskip("linkml")
    report = ontology_gate.run(ontology.register(rich()))
    linkml = report["checks"][1]
    assert linkml["result"] == "pass" and linkml["detail"]["problems"] == []
    exported = store.blob_path(linkml["detail"]["linkml_artifact"]).read_text()
    assert exported == ontology_export.linkml_yaml(rich(), report["ontology_hash"])
    assert not report["blocks_promotion"]


def proposal_runs(experiment="experiment"):
    """Two inspected runs with frozen discovery partitions, as `propose` needs."""
    store.put("sources", "src", {"metadata": {"title": "Source"}})
    store.put("snapshots", "snap", {"sha256": "hash"})
    for run_id, header in (("run-a", "Phone"), ("run-b", "Period")):
        pack = {
            "reader": {},
            "headers": [header],
            "partitions": {"discovery": [{"values": {header: "x"}}]},
        }
        store.put(
            "runs",
            run_id,
            {
                "id": run_id,
                "experiment_id": experiment,
                "source_id": "src",
                "snapshot_id": "snap",
                "partitions_artifact": store.json_blob(pack),
            },
            "src",
            "onboarding",
        )
    return ["run-a", "run-b"]


def scripted_model(monkeypatch, accept_period=True):
    concepts = [
        ontology.Concept(**concept("contact.phone", "contact")),
        ontology.Concept(**concept("financial.period", "financial_period")),
    ]
    proposal = workflow.Proposal(
        concepts=concepts,
        dispositions=[
            workflow.Disposition(
                run_id=alias,
                source_field=header,
                disposition="new_concept",
                target=target,
                evidence_quote=header,
                reason="Synthetic exact source header",
            )
            for alias, header, target in (
                ("source_1", "Phone", "contact.phone"),
                ("source_2", "Period", "financial.period"),
            )
        ],
    )
    review = workflow.OntologyReview(
        decisions=[
            workflow.ConceptDecision(
                name=c.name,
                acceptable=accept_period or c.name != "financial.period",
                reason="Synthetic evidence decision",
            )
            for c in concepts
        ],
        warnings=[],
    )
    calls = []

    def cached_call(job_id, schema, prompt, stage):
        calls.append(stage)
        return review if schema is workflow.OntologyReview else proposal

    monkeypatch.setattr(workflow, "cached_call", cached_call)
    return calls


def test_proposal_is_stored_as_rows_and_returned_as_before(monkeypatch):
    monkeypatch.setenv("LINK_LENS_EXPERIMENT_ID", "experiment")
    run_ids = proposal_runs()
    calls = scripted_model(monkeypatch, accept_period=False)
    result = workflow.propose(run_ids, activate_experimental=True)

    assert result["status"] == "validated"
    assert (result["accepted_concepts"], result["rejected_concepts"]) == (1, 1)
    assert result["source_run_ids"] == {"source_1": "run-a", "source_2": "run-b"}
    assert set(ontology.resolve(result["ontology_hash"])["concepts"]) - set(
        ontology.legacy()["concepts"]
    ) == {"contact.phone"}
    assert ontology.proposal(result["id"]) == result
    assert ontology.proposals() == [result]
    assert ontology.active_hash("experiment") == result["ontology_hash"]
    assert not store.listing("ontology_events", kind="proposal")

    with store.engine().connect() as connection:
        stored = connection.execute(select(registry.proposal)).one()
        dispositions = connection.execute(
            select(registry.disposition).order_by(registry.disposition.c.position)
        ).all()
        decisions = connection.execute(
            select(registry.concept_decision).order_by(
                registry.concept_decision.c.position
            )
        ).all()
        evidence = connection.execute(select(registry.version_evidence)).one()
    assert (stored.experiment_id, stored.job_run_id) == ("experiment", result["id"])
    assert stored.prompt_version == workflow.PROMPT_VERSION
    assert evidence.evidence_artifact == result["proposal_artifact"]
    # Rows hold what was released: the rejected concept's field has no target.
    assert [
        (d.source_ref, d.run_id, d.source_field, d.disposition, d.target_concept)
        for d in dispositions
    ] == [
        ("source_1", "run-a", "Phone", "new_concept", "contact.phone"),
        ("source_2", "run-b", "Period", "insufficient_evidence", None),
    ]
    assert [(d.concept_name, d.acceptable) for d in decisions] == [
        ("contact.phone", True),
        ("financial.period", False),
    ]

    # Asking again returns the stored proposal without calling the model.
    before = len(calls)
    assert workflow.propose(run_ids) == result
    assert len(calls) == before


def legacy_store(monkeypatch):
    """Rows as the store held them before the registry existed."""
    root_artifact = store.json_blob(ontology.legacy(), "ontology.json")
    document = rich()
    key = ontology.digest(document)
    store.put(
        "ontologies",
        ROOT,
        {
            "id": ROOT,
            "artifact_id": root_artifact,
            "parent_hash": None,
            "version": "0.1",
        },
        kind="ontology",
    )
    store.put(
        "ontologies",
        key,
        {
            "id": key,
            "artifact_id": store.json_blob(document, "ontology.json"),
            "parent_hash": ROOT,
            "version": "test",
        },
        kind="ontology",
    )
    disposition = {
        "run_id": "source_1",
        "source_field": "Phone",
        "disposition": "existing_target",
        "target": "entity.legal_name",
        "evidence_quote": "Phone",
        "reason": "Synthetic reason",
    }
    packets = {
        # Oldest shape: run references written by the model, no critique.
        "ontology-old": {
            "proposal": {
                "concepts": [],
                "dispositions": [
                    {**disposition, "run_id": "run-a"},
                    {**disposition, "run_id": "run-a"},  # a repeated header
                    {**disposition, "run_id": "not-a-run", "source_field": "Other"},
                ],
            },
            "critique": None,
        },
        # Middle shape: aliases, and a critique without per-concept decisions.
        "ontology-mid": {
            "proposal": {"concepts": [], "dispositions": [disposition]},
            "critique": {"acceptable": False, "blocking_issues": ["x"]},
        },
        "ontology-new": {
            "proposal": {"concepts": [], "dispositions": [disposition]},
            "released_proposal": {
                "concepts": [],
                "dispositions": [{**disposition, "reason": "Released reason"}],
            },
            "critique": {
                "decisions": [
                    {"name": "site.kind", "acceptable": True, "reason": "Synthetic"}
                ],
                "warnings": [],
            },
        },
    }
    base = {"run_ids": ["run-a", "run-b"], "parent_hash": ROOT}
    aliases = {"source_1": "run-a", "source_2": "run-b"}
    records = {
        "ontology-old": {**base, "status": "rejected", "ontology_hash": None},
        "ontology-mid": {
            **base,
            "status": "rejected",
            "ontology_hash": None,
            "source_run_ids": aliases,
            "supersedes_proposal_ids": ["ontology-old"],
        },
        "ontology-new": {
            **base,
            "status": "validated",
            "ontology_hash": key,
            "source_run_ids": aliases,
            "accepted_concepts": 5,
            "rejected_concepts": 0,
            "supersedes_proposal_ids": ["ontology-old", "ontology-mid"],
        },
    }
    for proposal_id, record in records.items():
        record.update(
            id=proposal_id, proposal_artifact=store.json_blob(packets[proposal_id])
        )
        store.put("ontology_events", proposal_id, record, "experiment", "proposal")
    store.put(
        "runs",
        "ontology-new",
        {
            "id": "ontology-new",
            "experiment_id": "experiment",
            "model": "m",
            "prompt_version": "p",
        },
        "ontology",
        "ontology",
    )
    evidence = records["ontology-new"]["proposal_artifact"]
    store.put(
        "ontology_events",
        "evidence",
        {"ontology_hash": key, "evidence": evidence},
        kind="proposal_evidence",
    )
    activations = [
        {
            "status": "experimental",
            "reviewer": None,
            "created_at": "2026-09-24T15:25:51.021232+00:00",
        },
        {
            "status": "promoted",
            "reviewer": "owner",
            "created_at": "2026-09-25T01:00:58+00:00",
        },
    ]
    for number, activation in enumerate(activations):
        activation.update(ontology_hash=key, experiment_id="experiment")
        store.put(
            "ontology_events",
            f"a{number}",
            activation,
            "experiment",
            activation["status"],
        )
    store.put(
        "ontology_events", "active-experiment", activations[-1], "experiment", "active"
    )
    store.put(
        "ontology_events",
        "call-1",
        {"artifact_id": evidence},
        "ontology-new",
        "model_cache",
    )
    return key, records, activations


def test_backfill_copies_legacy_rows_and_is_idempotent(monkeypatch):
    key, records, activations = legacy_store(monkeypatch)
    first = backfill.ontology()
    assert first["ontology_hashes"] == sorted([ROOT, key])
    assert first["legacy"] == {
        "ontologies": 2,
        "activations": 2,
        "proposals": 3,
        "proposal_evidence": 1,
    }
    assert backfill.ontology() == first  # a second run inserts nothing
    assert first["registry"]["activation"] == 2
    assert first["registry"]["disposition"] == 5
    assert first["registry"]["concept_decision"] == 1
    assert first["registry"]["gate_report"] == 0

    assert ontology.resolve(key) == rich()
    assert ontology.active_hash("experiment") == key
    assert latest("experiment") == activations[-1]
    assert ontology.proposals() == list(records.values())
    with store.engine().connect() as connection:
        promoted = connection.execute(
            select(registry.activation).where(
                registry.activation.c.status == "promoted"
            )
        ).one()
        stored = connection.execute(
            select(registry.proposal).where(registry.proposal.c.id == "ontology-new")
        ).one()
        unresolved = (
            connection.execute(
                select(registry.disposition.c.source_ref).where(
                    registry.disposition.c.run_id.is_(None)
                )
            )
            .scalars()
            .all()
        )
        released = connection.execute(
            select(registry.disposition.c.reason).where(
                registry.disposition.c.proposal_id == "ontology-new"
            )
        ).scalar_one()
    # A promotion from before the gate existed has no gate to point at.
    assert (promoted.reviewer, promoted.gate_run_at) == ("owner", None)
    assert (stored.model, stored.prompt_version, stored.job_run_id) == (
        "m",
        "p",
        "ontology-new",
    )
    assert unresolved == ["not-a-run"]
    assert released == "Released reason"
    # Legacy rows are copied, not moved; the model cache stays where it is.
    assert len(store.listing("ontology_events")) == 8
    assert len(store.listing("ontologies")) == 2


def test_backfill_refuses_a_pointer_that_disagrees_with_the_history(monkeypatch):
    key, _, activations = legacy_store(monkeypatch)
    store.put(
        "ontology_events",
        "active-experiment",
        {**activations[-1], "ontology_hash": ROOT},
        "experiment",
        "active",
    )
    with pytest.raises(ValueError, match="differs from its legacy pointer"):
        backfill.ontology()
    assert count(registry.ontology_version) == 0  # nothing is kept from a failed run


def test_first_archive_format_restores_into_the_registry(
    tmp_path, monkeypatch, clear_store
):
    from link_lens.frozen import freeze, thaw

    key, records, _ = legacy_store(monkeypatch)
    current = tmp_path / "current.zip"
    freeze(current)
    with zipfile.ZipFile(current) as source:
        data = json.loads(source.read("application.json"))
        assert data["format"] == "link-lens-evidence-2"
        assert all(not rows for rows in data["typed"].values())
        # An archive written before the registry existed has no typed section.
        data["format"] = "link-lens-evidence-1"
        del data["typed"]
        first = tmp_path / "first.zip"
        with zipfile.ZipFile(first, "w") as target:
            target.writestr("application.json", json.dumps(data))
            for name in source.namelist():
                if name.startswith("blobs/"):
                    target.writestr(name, source.read(name))
    clear_store()
    thaw(first)
    assert ontology.resolve(key) == rich()
    assert ontology.active_hash("experiment") == key
    assert ontology.proposals() == list(records.values())

    # The current format carries the registry rows themselves.
    freeze(current)
    clear_store()
    assert thaw(current)["typed"] == sum(
        1
        for _ in json.loads(zipfile.ZipFile(current).read("application.json"))[
            "typed"
        ].values()
        for _ in _
    )
    assert ontology.resolve(key) == rich()
    assert ontology.proposals() == list(records.values())
    # New rows continue after the restored identity values.
    ontology.activate(key, "another")
    assert count(registry.activation) == 3


def test_cli_exports_gates_and_blocks_promotion(monkeypatch, tmp_path):
    monkeypatch.setenv("LINK_LENS_EXPERIMENT_ID", "experiment")
    runner = CliRunner()
    key = ontology.register(rich())
    exported = runner.invoke(app, ["ontology", "export", key])
    assert exported.exit_code == 0
    assert exported.output == ontology_export.linkml_yaml(rich(), key)
    target = tmp_path / "schema.yaml"
    assert (
        runner.invoke(
            app, ["ontology", "export", key, "--output", str(target)]
        ).exit_code
        == 0
    )
    assert target.read_text() == exported.output
    assert (
        runner.invoke(app, ["ontology", "export", key, "--format", "owl"]).exit_code
        == 2
    )

    promote = ["ontology", "promote", key, "--reviewer", "owner"]
    refused = runner.invoke(app, promote)
    assert refused.exit_code == 2 and "gate" in refused.output

    stub_gate(monkeypatch, linkml="fail")
    assert runner.invoke(app, ["ontology", "gate", key]).exit_code == 3
    assert runner.invoke(app, promote).exit_code == 2
    stub_gate(monkeypatch, impact="unknown")
    gated = runner.invoke(app, ["ontology", "gate", key])
    assert (
        gated.exit_code == 0 and json.loads(gated.output)["blocks_promotion"] is False
    )
    promoted = runner.invoke(app, promote)
    assert promoted.exit_code == 0
    assert json.loads(promoted.output)["gate"]["results"]["impact"] == "unknown"
    assert ontology.active_hash("experiment") == key

    shown = json.loads(runner.invoke(app, ["ontology", "show", key]).output)
    assert shown == rich()
    assert runner.invoke(app, ["backfill", "ontology"]).exit_code == 0
    assert deepcopy(shown) == ontology.resolve(key)
