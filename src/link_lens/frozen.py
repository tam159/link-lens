"""Portable application evidence; workflow checkpoints deliberately stay on Agent Server."""

import hashlib
import json
import zipfile
from pathlib import Path

from sqlalchemy import text

from . import store
from .db import ontology as ontology_registry

# Typed tables in the archive, in insertion order. Format 1 archives hold only
# the generic tables; their ontology rows are copied into the registry on restore.
TYPED = ontology_registry.TABLES
FORMATS = ("link-lens-evidence-1", "link-lens-evidence-2")


def qualified(table):
    return f"{table.schema}.{table.name}"


def restore_typed(connection, typed):
    """Insert archived typed rows. Existing rows must be identical."""
    restored = 0
    for table in TYPED:
        rows = typed.get(qualified(table)) or []
        if not rows:
            continue
        name, rows = qualified(table), {"rows": json.dumps(rows)}
        source = f"jsonb_populate_recordset(NULL::{name}, CAST(:rows AS jsonb))"
        restored += connection.execute(
            text(
                f"INSERT INTO {name} OVERRIDING SYSTEM VALUE "
                f"SELECT * FROM {source} ON CONFLICT DO NOTHING"
            ),
            rows,
        ).rowcount
        different = connection.execute(
            text(
                f"SELECT count(*) FROM {source} AS archived WHERE NOT EXISTS "
                f"(SELECT 1 FROM {name} AS stored WHERE stored = archived)"
            ),
            rows,
        ).scalar_one()
        if different:
            raise ValueError("Restore requires an empty database or identical records")
        if "id" in table.c and table.c.id.type.python_type is int:
            # Restored rows keep their IDs; move the identity sequence past them.
            connection.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('{name}', 'id'), "
                    f"(SELECT max(id) FROM {name}))"
                )
            )
    return restored


def freeze(path: Path):
    records = {name: [] for name in store.TABLES}
    from sqlalchemy import select

    with (
        store.engine()
        .connect()
        .execution_options(isolation_level="REPEATABLE READ") as connection
    ):
        for name, table in store.TABLES.items():
            records[name] = [
                {
                    "id": r.id,
                    "owner_id": r.owner_id,
                    "kind": r.kind,
                    "payload": r.payload,
                }
                for r in connection.execute(select(table))
            ]
        typed = {
            qualified(table): list(
                connection.execute(
                    text(f"SELECT to_jsonb(t) FROM {qualified(table)} AS t ORDER BY t")
                ).scalars()
            )
            for table in TYPED
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as out:
        out.writestr(
            "application.json",
            json.dumps(
                {
                    "format": FORMATS[-1],
                    "created_at": store.now(),
                    "tables": records,
                    "typed": typed,
                },
                ensure_ascii=False,
            ),
        )
        for artifact in records["artifacts"]:
            key = artifact["id"]
            out.write(store.blob_path(key), "blobs/" + key)
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "note": "Application evidence only. Does not create human decisions or restore resumable graph threads.",
    }


def thaw(path: Path):
    with zipfile.ZipFile(path) as source:
        # The two-experiment demo includes both baselines, audits and failed attempts
        # (~527 MB uncompressed). Keep a finite bound while allowing that evidence.
        if sum(i.file_size for i in source.infolist()) > 750_000_000:
            raise ValueError("Evidence archive exceeds local demo size limit")
        data = json.loads(source.read("application.json"))
        if (
            data["format"] not in FORMATS
            or not set(data["tables"]).issubset(store.TABLES)
            or not (
                set(store.TABLES)
                - {"ontologies", "ontology_events", "budget_reservations"}
            ).issubset(data["tables"])
        ):
            raise ValueError("Unsupported evidence format")
        # Verify all content and conflicts before writing domain records.
        for name, rows in data["tables"].items():
            for row in rows:
                old = store.get(name, row["id"])
                if old is not None and old != row["payload"]:
                    raise ValueError(
                        "Restore requires an empty database or identical records"
                    )
        for artifact in data["tables"]["artifacts"]:
            key = artifact["id"]
            payload = source.read("blobs/" + key)
            if hashlib.sha256(payload).hexdigest() != key:
                raise ValueError("Artifact hash mismatch")
        # Typed rows restore in one transaction and fail before anything else is
        # written if the database already holds different rows.
        with store.engine().begin() as connection:
            typed = restore_typed(connection, data.get("typed") or {})
        for artifact in data["tables"]["artifacts"]:
            meta = artifact["payload"]
            store.blob(
                source.read("blobs/" + artifact["id"]), meta["media_type"], meta["name"]
            )
        for name, rows in data["tables"].items():
            for row in rows:
                store.put(
                    name,
                    row["id"],
                    row["payload"],
                    row["owner_id"],
                    row["kind"],
                    immutable=True,
                )
    if data["format"] == FORMATS[0]:
        from . import backfill

        backfill.ontology()
    return {
        "restored": sum(len(rows) for rows in data["tables"].values()),
        "typed": typed,
        "workflow_resume": "not restored; frozen evidence is read-only demonstration material",
    }
