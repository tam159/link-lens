"""Repository for the `ontology` schema. Callers own the transaction."""

from datetime import UTC, datetime

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    Table,
    Text,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, insert

from .types import Sha256

metadata = MetaData(schema="ontology")
timestamp = DateTime(timezone=True)

ontology_version = Table(
    "ontology_version",
    metadata,
    Column("hash", Sha256, primary_key=True),
    Column("parent_hash", Sha256),
    Column("label", Text),
    Column("document_artifact", Sha256),
    Column("created_at", timestamp),
)
concept = Table(
    "concept",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("name", Text),
    Column("content_hash", Sha256),
    Column("scope", Text),
    Column("datatype", Text),
    Column("cardinality", Text),
    Column("definition", Text),
    Column("minimum", Text),
    Column("maximum", Text),
    Column("introduced_in", Sha256),
)
concept_value = Table(
    "concept_value",
    metadata,
    Column("concept_id", BigInteger, primary_key=True),
    Column("value", Text, primary_key=True),
    Column("position", Integer),
)
concept_requires = Table(
    "concept_requires",
    metadata,
    Column("concept_id", BigInteger, primary_key=True),
    Column("required_concept_id", BigInteger, primary_key=True),
    Column("position", Integer),
)
version_concept = Table(
    "version_concept",
    metadata,
    Column("version_hash", Sha256, primary_key=True),
    Column("concept_id", BigInteger, primary_key=True),
    Column("name", Text),
    Column("position", Integer),
)
version_evidence = Table(
    "version_evidence",
    metadata,
    Column("version_hash", Sha256, primary_key=True),
    Column("evidence_artifact", Sha256, primary_key=True),
    Column("created_at", timestamp),
)
proposal = Table(
    "proposal",
    metadata,
    Column("id", Text, primary_key=True),
    Column("experiment_id", Text),
    Column("parent_hash", Sha256),
    Column("ontology_hash", Sha256),
    Column("job_run_id", Text),
    Column("status", Text),
    Column("model", Text),
    Column("prompt_version", Text),
    Column("proposal_artifact", Sha256),
    Column("accepted_concepts", Integer),
    Column("rejected_concepts", Integer),
    Column("supersedes_proposal_ids", ARRAY(Text)),
    Column("created_at", timestamp),
)
proposal_run = Table(
    "proposal_run",
    metadata,
    Column("proposal_id", Text, primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("run_id", Text),
    Column("alias", Text),
)
disposition = Table(
    "disposition",
    metadata,
    Column("proposal_id", Text, primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("source_ref", Text),
    Column("source_field", Text),
    Column("run_id", Text),
    Column("disposition", Text),
    Column("target_concept", Text),
    Column("evidence_quote", Text),
    Column("reason", Text),
)
concept_decision = Table(
    "concept_decision",
    metadata,
    Column("proposal_id", Text, primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("concept_name", Text),
    Column("acceptable", Boolean),
    Column("reason", Text),
)
activation = Table(
    "activation",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("experiment_id", Text),
    Column("version_hash", Sha256),
    Column("status", Text),
    Column("reviewer", Text),
    Column("created_at", timestamp),
    Column("gate_run_at", timestamp),
    Column("gate_results", JSONB(none_as_null=True)),
)
gate_report = Table(
    "gate_report",
    metadata,
    Column("version_hash", Sha256, primary_key=True),
    Column("check_name", Text, primary_key=True),
    Column("result", Text),
    Column("detail", JSONB),
    Column("created_at", timestamp, primary_key=True),
)

# Insertion order for archives; a table follows the tables it references.
TABLES = [
    ontology_version,
    concept,
    concept_value,
    concept_requires,
    version_concept,
    version_evidence,
    proposal,
    proposal_run,
    disposition,
    concept_decision,
    activation,
    gate_report,
]


def iso(value):
    """Timestamps leave the repository as the UTC ISO strings the store has always used."""
    return None if value is None else value.astimezone(UTC).isoformat()


def insert_version(connection, key, document, artifact, concept_hash, created_at=None):
    """Store a version with its concepts and members. False if it already exists.

    `concept_hash` maps a concept definition to its content hash. Concepts already
    stored with the same name and definition are reused, so an additive version
    shares its parent's rows.
    """
    values = {
        "hash": key,
        "parent_hash": document.get("parent_hash"),
        "label": document["version"],
        "document_artifact": artifact,
    }
    if created_at is not None:
        values["created_at"] = created_at
    created = connection.execute(
        insert(ontology_version)
        .values(values)
        .on_conflict_do_nothing()
        .returning(ontology_version.c.hash)
    ).first()
    if created is None:
        return False

    ids, fresh = {}, []
    for name, definition in document["concepts"].items():
        content = concept_hash(definition)
        row = connection.execute(
            insert(concept)
            .values(
                name=name,
                content_hash=content,
                scope=definition["scope"],
                datatype=definition["type"],
                cardinality=definition["cardinality"],
                definition=definition["definition"],
                minimum=definition["minimum"],
                maximum=definition["maximum"],
                introduced_in=key,
            )
            .on_conflict_do_nothing()
            .returning(concept.c.id)
        ).first()
        if row is None:
            ids[name] = connection.execute(
                select(concept.c.id).where(
                    concept.c.name == name, concept.c.content_hash == content
                )
            ).scalar_one()
        else:
            ids[name] = row.id
            fresh.append(name)

    value_rows = [
        {"concept_id": ids[name], "value": value, "position": position}
        for name in fresh
        for position, value in enumerate(document["concepts"][name]["values"])
    ]
    if value_rows:
        connection.execute(insert(concept_value), value_rows)
    require_rows = [
        {
            "concept_id": ids[name],
            "required_concept_id": ids[required],
            "position": position,
        }
        for name in fresh
        for position, required in enumerate(document["concepts"][name]["requires"])
    ]
    if require_rows:
        connection.execute(insert(concept_requires), require_rows)
    connection.execute(
        insert(version_concept),
        [
            {
                "version_hash": key,
                "concept_id": ids[name],
                "name": name,
                "position": position,
            }
            for position, name in enumerate(document["concepts"])
        ],
    )
    return True


def version(connection, key):
    row = connection.execute(
        select(ontology_version).where(ontology_version.c.hash == key)
    ).first()
    return None if row is None else dict(row._mapping)


def concept_ids(connection, key):
    """Concept IDs of a version by name."""
    return {
        row.name: row.concept_id
        for row in connection.execute(
            select(version_concept.c.name, version_concept.c.concept_id).where(
                version_concept.c.version_hash == key
            )
        )
    }


def version_hashes(connection):
    return list(
        connection.execute(
            select(ontology_version.c.hash).order_by(ontology_version.c.hash)
        ).scalars()
    )


def document(connection, key):
    """Rebuild a version's document from its rows, in the original order."""
    head = version(connection, key)
    if head is None:
        return None
    members = connection.execute(
        select(concept)
        .join(version_concept, version_concept.c.concept_id == concept.c.id)
        .where(version_concept.c.version_hash == key)
        .order_by(version_concept.c.position)
    ).all()
    ids = [m.id for m in members]
    values = {i: [] for i in ids}
    for row in connection.execute(
        select(concept_value.c.concept_id, concept_value.c.value)
        .where(concept_value.c.concept_id.in_(ids))
        .order_by(concept_value.c.concept_id, concept_value.c.position)
    ):
        values[row.concept_id].append(row.value)
    required = concept.alias("required")
    requires = {i: [] for i in ids}
    for row in connection.execute(
        select(concept_requires.c.concept_id, required.c.name)
        .join(required, required.c.id == concept_requires.c.required_concept_id)
        .where(concept_requires.c.concept_id.in_(ids))
        .order_by(concept_requires.c.concept_id, concept_requires.c.position)
    ):
        requires[row.concept_id].append(row.name)
    return {
        "version": head["label"],
        "parent_hash": head["parent_hash"],
        "concepts": {
            m.name: {
                "name": m.name,
                "definition": m.definition,
                "type": m.datatype,
                "scope": m.scope,
                "cardinality": m.cardinality,
                "values": values[m.id],
                "requires": requires[m.id],
                "minimum": m.minimum,
                "maximum": m.maximum,
            }
            for m in members
        },
    }


def add_evidence(connection, key, evidence_artifact, created_at=None):
    values = {"version_hash": key, "evidence_artifact": evidence_artifact}
    if created_at is not None:
        values["created_at"] = created_at
    connection.execute(insert(version_evidence).values(values).on_conflict_do_nothing())


def append_activation(connection, record, gate=None):
    """Append an activation. `gate` is the gate run a promotion relied on."""
    return (
        connection.execute(
            insert(activation)
            .values(
                experiment_id=record["experiment_id"],
                version_hash=record["ontology_hash"],
                status=record["status"],
                reviewer=record["reviewer"],
                created_at=datetime.fromisoformat(record["created_at"]),
                gate_run_at=datetime.fromisoformat(gate["run_at"]) if gate else None,
                gate_results=gate["results"] if gate else None,
            )
            .on_conflict_do_nothing()
        ).rowcount
        == 1
    )


def latest_activation(connection, experiment_id):
    row = connection.execute(
        select(activation)
        .where(activation.c.experiment_id == experiment_id)
        .order_by(activation.c.created_at.desc(), activation.c.id.desc())
        .limit(1)
    ).first()
    if row is None:
        return None
    return {
        "ontology_hash": row.version_hash,
        "experiment_id": row.experiment_id,
        "reviewer": row.reviewer,
        "status": row.status,
        "created_at": iso(row.created_at),
    }


def insert_proposal(connection, record, runs, dispositions, decisions):
    """Store a proposal with its runs, dispositions and concept decisions.

    False if the proposal already exists; nothing is written in that case.
    """
    created = connection.execute(
        insert(proposal)
        .values(record)
        .on_conflict_do_nothing()
        .returning(proposal.c.id)
    ).first()
    if created is None:
        return False
    for table, rows in (
        (proposal_run, runs),
        (disposition, dispositions),
        (concept_decision, decisions),
    ):
        if rows:
            connection.execute(
                insert(table),
                [
                    {"proposal_id": record["id"], "position": position, **row}
                    for position, row in enumerate(rows)
                ],
            )
    return True


def _proposal_record(connection, row):
    """The proposal as the dict the workflow has always returned."""
    runs = connection.execute(
        select(proposal_run.c.run_id, proposal_run.c.alias)
        .where(proposal_run.c.proposal_id == row.id)
        .order_by(proposal_run.c.position)
    ).all()
    record = {
        "id": row.id,
        "ontology_hash": row.ontology_hash,
        "proposal_artifact": row.proposal_artifact,
        "run_ids": [r.run_id for r in runs],
        "status": row.status,
        "parent_hash": row.parent_hash,
    }
    # Earlier proposals were stored without these keys; absent stays absent.
    if any(r.alias is not None for r in runs):
        record["source_run_ids"] = {r.alias: r.run_id for r in runs}
    if row.accepted_concepts is not None:
        record["accepted_concepts"] = row.accepted_concepts
    if row.rejected_concepts is not None:
        record["rejected_concepts"] = row.rejected_concepts
    if row.supersedes_proposal_ids is not None:
        record["supersedes_proposal_ids"] = list(row.supersedes_proposal_ids)
    return record


def get_proposal(connection, key):
    row = connection.execute(select(proposal).where(proposal.c.id == key)).first()
    return None if row is None else _proposal_record(connection, row)


def list_proposals(connection):
    rows = connection.execute(
        select(proposal).order_by(proposal.c.created_at, proposal.c.id)
    ).all()
    return [_proposal_record(connection, row) for row in rows]


def insert_gate_run(connection, key, checks, run_at):
    connection.execute(
        insert(gate_report),
        [
            {
                "version_hash": key,
                "check_name": check["check"],
                "result": check["result"],
                "detail": check["detail"],
                "created_at": run_at,
            }
            for check in checks
        ],
    )


def latest_gate_run(connection, key):
    """The most recent gate run for a version, or None if it was never gated."""
    run_at = connection.execute(
        select(func.max(gate_report.c.created_at)).where(
            gate_report.c.version_hash == key
        )
    ).scalar_one()
    if run_at is None:
        return None
    rows = connection.execute(
        select(gate_report)
        .where(gate_report.c.version_hash == key, gate_report.c.created_at == run_at)
        .order_by(gate_report.c.check_name)
    ).all()
    return {
        "ontology_hash": key,
        "run_at": iso(run_at),
        "checks": [
            {"check": r.check_name, "result": r.result, "detail": r.detail}
            for r in rows
        ],
    }
