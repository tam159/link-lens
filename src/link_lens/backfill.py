"""Copy legacy rows into the typed schemas. Legacy rows are read, never changed.

Each backfill is idempotent and verifies its own result before committing.
"""

from sqlalchemy import func, select

from . import blobs, store
from . import ontology as ontologies
from .db import catalog, copy_insert, evidence, onboarding
from .db import ontology as registry
from .db.records import same


def ontology():
    """Copy ontology versions, evidence, activations and proposals from legacy.

    Verifies that every version's rows rebuild its document and hash, that each
    experiment's current activation equals its legacy `active` pointer, and that
    every proposal reads back as its legacy record. Model cache rows stay in
    `legacy.ontology_events` until the operations schema exists.
    """
    versions = store.TABLES["ontologies"]
    events = store.TABLES["ontology_events"]
    with store.engine().connect() as connection:
        stored = connection.execute(
            select(versions.c.id, versions.c.payload, versions.c.created_at).order_by(
                versions.c.created_at, versions.c.id
            )
        ).all()
        history = connection.execute(
            select(
                events.c.owner_id, events.c.kind, events.c.payload, events.c.created_at
            )
            .where(events.c.kind != "model_cache")
            .order_by(events.c.created_at, events.c.id)
        ).all()

    # Proposal jobs are runs; the store serves them wherever runs are kept.
    jobs = {job["id"]: job for job in store.listing("runs", kind="ontology")}

    # The packaged v0.1 ontology is the root of every version, stored or not.
    root = ontologies.digest(ontologies.legacy())
    pending = [
        (
            row.id,
            store.read_json(row.payload["artifact_id"]),
            row.payload["artifact_id"],
            row.created_at,
        )
        for row in stored
    ]
    if root not in {key for key, *_ in pending}:
        artifact = store.json_blob(ontologies.legacy(), "ontology.json")
        pending.insert(0, (root, ontologies.legacy(), artifact, None))

    with store.engine().begin() as connection:
        known = set(registry.version_hashes(connection))
        while pending:
            ready = [
                item
                for item in pending
                if item[1].get("parent_hash") is None or item[1]["parent_hash"] in known
            ]
            if not ready:
                raise ValueError(
                    "Ontology versions reference a parent that is not stored"
                )
            for key, document, artifact, created_at in ready:
                if ontologies.digest(document) != key:
                    raise ValueError(f"Ontology artifact does not match its hash {key}")
                registry.insert_version(
                    connection, key, document, artifact, ontologies.digest, created_at
                )
                if registry.document(connection, key) != document:
                    raise ValueError(f"Ontology {key} does not rebuild from its rows")
                known.add(key)
            pending = [item for item in pending if item[0] not in known]

        for row in history:
            if row.kind == "proposal_evidence":
                registry.add_evidence(
                    connection,
                    row.payload["ontology_hash"],
                    row.payload["evidence"],
                    row.created_at,
                )
        activations = [
            r.payload for r in history if r.kind in ("experimental", "promoted")
        ]
        for record in sorted(activations, key=lambda r: r["created_at"]):
            registry.append_activation(connection, record)
        for row in history:
            if row.kind == "active" and (
                registry.latest_activation(connection, row.owner_id) != row.payload
            ):
                raise ValueError(
                    f"Current activation for {row.owner_id} differs from its legacy pointer"
                )

        for row in history:
            if row.kind != "proposal":
                continue
            record = row.payload
            packet = store.read_json(record["proposal_artifact"])
            aliases = record.get("source_run_ids") or {}
            alias_of = {run: alias for alias, run in aliases.items()}
            job = jobs.get(record["id"], {})
            # What was released, or what was proposed when nothing was released.
            final = packet.get("released_proposal") or packet["proposal"]
            # Critiques before per-concept decisions have no rows to copy.
            decisions = (packet.get("critique") or {}).get("decisions") or []
            registry.insert_proposal(
                connection,
                {
                    "id": record["id"],
                    "experiment_id": job.get("experiment_id", row.owner_id),
                    "parent_hash": record["parent_hash"],
                    "ontology_hash": record["ontology_hash"],
                    "job_run_id": record["id"] if job else None,
                    "status": record["status"],
                    "model": job.get("model"),
                    "prompt_version": job.get("prompt_version"),
                    "proposal_artifact": record["proposal_artifact"],
                    "accepted_concepts": record.get("accepted_concepts"),
                    "rejected_concepts": record.get("rejected_concepts"),
                    "supersedes_proposal_ids": record.get("supersedes_proposal_ids"),
                    "created_at": row.created_at,
                },
                [
                    {"run_id": run, "alias": alias_of.get(run)}
                    for run in record["run_ids"]
                ],
                [
                    {
                        "source_ref": d["run_id"],
                        "source_field": d["source_field"],
                        # A reference the model wrote that names no run stays unresolved.
                        "run_id": aliases.get(d["run_id"])
                        or (d["run_id"] if d["run_id"] in record["run_ids"] else None),
                        "disposition": d["disposition"],
                        "target_concept": d.get("target"),
                        "evidence_quote": d["evidence_quote"],
                        "reason": d["reason"],
                    }
                    for d in final["dispositions"]
                ],
                [
                    {
                        "concept_name": d["name"],
                        "acceptable": d["acceptable"],
                        "reason": d["reason"],
                    }
                    for d in decisions
                ],
            )
            if registry.get_proposal(connection, record["id"]) != record:
                raise ValueError(
                    f"Proposal {record['id']} does not read back as stored"
                )

        return {
            "legacy": {
                "ontologies": len(stored),
                "activations": len(activations),
                "proposals": sum(r.kind == "proposal" for r in history),
                "proposal_evidence": sum(
                    r.kind == "proposal_evidence" for r in history
                ),
            },
            "registry": {
                table.name: connection.execute(
                    select(func.count()).select_from(table)
                ).scalar_one()
                for table in registry.TABLES
            },
            "ontology_hashes": registry.version_hashes(connection),
        }


def _legacy(connection, name, where=None):
    table = store.TABLES[name]
    statement = select(table).order_by(table.c.created_at, table.c.id)
    return connection.execute(
        statement if where is None else statement.where(where)
    ).all()


def _copy_records(name, rows):
    """Copy generic rows into a record table and verify each copy."""
    target = store.RECORDS[name]
    with store.engine().begin() as connection:
        before = {key for key, *_ in target.records(connection)}
        for row in rows:
            if row.id not in before:
                target.put(
                    connection,
                    row.id,
                    row.payload,
                    row.owner_id,
                    row.kind,
                    created_at=row.created_at,
                )
        copies = {key: rest for key, *rest in target.records(connection)}
        for row in rows:
            # A row copied by an earlier run may have changed since if its table
            # is mutable; only what this run copied must equal its source.
            if row.id in before and not target.append_only:
                continue
            owner, kind, payload, created_at = copies[row.id]
            if not same(payload, row.payload) or (owner, kind, created_at) != (
                row.owner_id,
                row.kind,
                row.created_at,
            ):
                raise ValueError(f"{name}/{row.id} does not read back as stored")
        return {
            "legacy": len(rows),
            "copied": len(copies.keys() - before),
            "typed": len(copies),
            "not_in_typed_column": target.unresolved(connection),
        }


def evidence_spine(chunk=20000):
    """Copy artifacts, sources, snapshots, runs, mappings, approvals and observations.

    Runs in dependency order, is idempotent, and verifies that every copied
    record reads back from the typed tables exactly as the legacy row holds it.
    `not_in_typed_column` counts values a typed column could not hold, such as a
    run's source that is not a registered source.
    """
    report = {}
    with store.engine().connect() as connection:
        artifacts = _legacy(connection, "artifacts")
        legacy_rows = {
            name: _legacy(connection, name)
            for name in ("sources", "snapshots", "runs", "mappings", "approvals")
        }

    with store.engine().begin() as connection:
        inserted = copy_insert(
            connection,
            catalog.artifact,
            (
                {
                    "sha256": row.id,
                    "uri": "local:" + blobs.relative(row.id),
                    "media_type": row.payload["media_type"],
                    "size": row.payload["size"],
                    "name": row.payload["name"],
                    "created_at": row.created_at,
                }
                for row in artifacts
            ),
        )
        copies = {
            key: payload
            for key, _, _, payload, _ in catalog.artifact_records(connection)
        }
        for row in artifacts:
            if not same(copies[row.id], row.payload):
                raise ValueError(f"artifacts/{row.id} does not read back as stored")
        report["artifacts"] = {
            "legacy": len(artifacts),
            "copied": inserted,
            "typed": len(copies),
        }

    # A run may supersede an earlier run; copy the superseded ones first.
    runs, placed, waiting = [], set(), list(legacy_rows["runs"])
    while waiting:
        ready = [
            row
            for row in waiting
            if row.payload.get("supersedes_run_id") not in {r.id for r in waiting}
            or row.payload.get("supersedes_run_id") == row.id
        ] or waiting
        runs.extend(ready)
        placed.update(row.id for row in ready)
        waiting = [row for row in waiting if row.id not in placed]
    legacy_rows["runs"] = runs

    store._prepare_mappings()
    for name in ("sources", "snapshots", "runs", "mappings", "approvals"):
        report[name] = _copy_records(name, legacy_rows[name])
    with store.engine().connect() as connection:
        report["mapping_configs"] = connection.execute(
            select(func.count()).select_from(onboarding.mapping_config)
        ).scalar_one()
        report["mapping_fields"] = connection.execute(
            select(func.count()).select_from(onboarding.mapping_field)
        ).scalar_one()

    legacy = store.TABLES["observations"]
    root = store._root_hash()
    total = copied = with_extra = 0
    extra_keys, last = {}, ""
    while True:
        with store.engine().begin() as connection:
            rows = connection.execute(
                select(legacy.c.id, legacy.c.payload)
                .where(legacy.c.id > last)
                .order_by(legacy.c.id)
                .limit(chunk)
            ).all()
            if not rows:
                break
            last = rows[-1].id
            total += len(rows)
            copied += evidence.insert_observations(
                connection, [row.payload for row in rows], root
            )
            typed = {
                o["id"]: o
                for o in evidence.observations(connection, [row.id for row in rows])
            }
            for row in rows:
                if row.id not in typed or not same(typed[row.id], row.payload):
                    raise ValueError(
                        f"observations/{row.id} does not read back as stored"
                    )
            for row in connection.execute(
                select(evidence.observation.c.extra).where(
                    evidence.among(evidence.observation.c.id, [row.id for row in rows]),
                    evidence.observation.c.extra != {},
                )
            ):
                with_extra += 1
                for key in row.extra:
                    extra_keys[key] = extra_keys.get(key, 0) + 1
    with store.engine().connect() as connection:
        report["observations"] = {
            "legacy": total,
            "copied": copied,
            "typed": evidence.count(connection),
            "kept_outside_columns": with_extra,
            "keys_kept_outside_columns": extra_keys,
        }
        report["source_records"] = connection.execute(
            select(func.count()).select_from(evidence.source_record)
        ).scalar_one()
    return report
