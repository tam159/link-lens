"""Moving artifact bytes from the local directory to the configured object store.

An artifact is named by its SHA-256, so a move is: read the local bytes, check
them against the hash, write them to the bucket, read them back and check
again, and only then record the new location. Nothing local is deleted. A move
that was interrupted or run twice does no harm: an artifact already in the
bucket is skipped.
"""

import hashlib

from sqlalchemy import text

from . import blobs, logs, store


def migrate(limit=None, dry_run=False):
    """Copy every artifact still local to the object store. Returns counts.

    `missing` are artifacts whose local file is absent, and `mismatched` those
    whose bytes do not match their hash, before or after the copy; neither is
    moved. The caller should treat a non-zero count of either as a failure.
    """
    stores = blobs.stores()
    if "s3" not in stores:
        raise ValueError(
            "Set LINK_LENS_ARTIFACT_STORE=s3 and a bucket to move artifacts"
        )
    local, remote = stores["local"], stores["s3"]
    counts = {"moved": 0, "bytes": 0, "missing": 0, "mismatched": 0, "remaining": 0}
    faults = []
    with store.engine().connect() as connection:
        rows = connection.execute(
            text(
                "SELECT sha256_hex(sha256) AS sha, uri FROM catalog.artifact "
                "WHERE uri LIKE 'local:%' ORDER BY sha256"
            )
        ).all()
    for position, row in enumerate(rows):
        if limit is not None and counts["moved"] >= limit:
            counts["remaining"] = len(rows) - position
            break
        try:
            data = local.path(row.uri, row.sha).read_bytes()
        except FileNotFoundError:
            counts["missing"] += 1
            faults.append({"sha256": row.sha, "fault": "missing"})
            continue
        if hashlib.sha256(data).hexdigest() != row.sha:
            counts["mismatched"] += 1
            faults.append({"sha256": row.sha, "fault": "local bytes do not match"})
            continue
        if not dry_run:
            uri = remote.put(row.sha, data)
            if hashlib.sha256(remote.fetch(uri)).hexdigest() != row.sha:
                counts["mismatched"] += 1
                faults.append({"sha256": row.sha, "fault": "stored bytes do not match"})
                continue
            with store.engine().begin() as connection:
                connection.execute(
                    text(
                        "UPDATE catalog.artifact SET uri = :uri "
                        "WHERE sha256 = sha256_from_hex(:sha) AND uri = :was"
                    ),
                    {"uri": uri, "sha": row.sha, "was": row.uri},
                )
        counts["moved"] += 1
        counts["bytes"] += len(data)
    logs.event("artifacts.migrated", dry_run=dry_run, **counts)
    return {**counts, "dry_run": dry_run, "faults": faults[:50]}
