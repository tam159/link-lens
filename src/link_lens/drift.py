"""Has a source's file changed shape since its mapping was approved?

A mapping names the reader it was written for and every column it saw: the
columns it maps, filters on or takes labels and timestamps from, and the ones
it deliberately leaves unmapped. Drift is any difference between that and a new
snapshot. A column the mapping uses going missing stops extraction; a new or
removed unused column does not, but the mapping has not seen the new shape.
"""

from . import store
from .contracts import ReaderSpec
from .readers import read_records


def expected(config):
    """Columns the mapping uses, and all columns it saw, used or not."""
    used = set()
    for field in config.get("fields", []):
        used.update(field.get("source_fields", []))
        used.update(rule["field"] for rule in field.get("when", []))
    used.update(rule["field"] for rule in config.get("filters", []))
    for key in ("subject_label_field", "observed_at_field"):
        if config.get(key):
            used.add(config[key])
    unused = {item["source_field"] for item in config.get("unmapped_fields", [])}
    return used, used | unused


def compare(config, snapshot_format, headers):
    """Compare a snapshot's format and headers with what a mapping config expects.

    Returns `{"status": "unchanged" | "changed", "reasons": [...]}`. Each reason
    has a `kind` (`format`, `missing_used_column`, `removed_unused_column`,
    `new_column`), the `column` where one applies, and whether it is `blocking`,
    which means the approved mapping cannot extract from this snapshot.
    """
    reasons = []
    reader_format = config["reader"]["format"]
    if snapshot_format != reader_format:
        reasons.append(
            {
                "kind": "format",
                "blocking": True,
                "detail": f"mapping reads {reader_format}, snapshot is {snapshot_format}",
            }
        )
    used, known = expected(config)
    present = set(headers)
    for column in sorted(used - present):
        reasons.append(
            {"kind": "missing_used_column", "column": column, "blocking": True}
        )
    for column in sorted(known - used - present):
        reasons.append(
            {"kind": "removed_unused_column", "column": column, "blocking": False}
        )
    for column in sorted(present - known):
        reasons.append({"kind": "new_column", "column": column, "blocking": False})
    return {
        "status": "changed" if reasons else "unchanged",
        "blocking": any(reason["blocking"] for reason in reasons),
        "reasons": reasons,
    }


def detect(snapshot_id, config_hash=None, config=None):
    """Read a stored snapshot's header with a mapping's reader and compare.

    Pass the approved config or its hash. A reader that cannot open the snapshot
    at all is reported as a blocking `reader` reason. Reads only; writes nothing.
    """
    snapshot = store.require("snapshots", snapshot_id)
    if config is None:
        from .db import onboarding
        from sqlalchemy import select

        with store.engine().connect() as connection:
            config = connection.execute(
                select(onboarding.mapping_config.c.config).where(
                    onboarding.mapping_config.c.config_hash == config_hash
                )
            ).scalar_one_or_none()
        if config is None:
            raise KeyError(f"mapping config {config_hash} not found")
    result = {"snapshot_id": snapshot_id, "config_hash": config_hash}
    try:
        headers, _ = read_records(
            store.blob_path(snapshot["artifact_id"]),
            ReaderSpec.model_validate(config["reader"]),
            snapshot["sha256"],
            snapshot.get("receipt", {}).get("partial", False),
            limit=1,
        )
    except Exception as error:  # noqa: BLE001 -- an unreadable snapshot is the finding
        return {
            **result,
            "status": "changed",
            "blocking": True,
            "reasons": [
                {
                    "kind": "reader",
                    "blocking": True,
                    "detail": f"{type(error).__name__}: {error}"[:400],
                }
            ],
        }
    return {**result, **compare(config, snapshot.get("format"), headers)}
