"""Portable application evidence; workflow checkpoints deliberately stay on Agent Server."""

import hashlib
import json
import zipfile
from pathlib import Path
from . import store


def freeze(path: Path):
    records = {name: [] for name in store.TABLES}
    from sqlalchemy import select

    with (
        store.engine()
        .connect()
        .execution_options(
            isolation_level="REPEATABLE READ"
            if store.engine().dialect.name == "postgresql"
            else "SERIALIZABLE"
        ) as connection
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as out:
        out.writestr(
            "application.json",
            json.dumps(
                {
                    "format": "link-lens-evidence-1",
                    "created_at": store.now(),
                    "tables": records,
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
            data["format"] != "link-lens-evidence-1"
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
    return {
        "restored": sum(len(rows) for rows in data["tables"].values()),
        "workflow_resume": "not restored; frozen evidence is read-only demonstration material",
    }
