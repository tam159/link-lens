"""What the console reads and does.

Each function is a few lines over the library function the CLI calls, so the
console and the command line write the same records. A function that changes
something takes the signed-in person first and records the change in the audit
log around the call that makes it.
"""

import math
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from .. import budget, ingestion, refresh, releases, sources, store
from ..contracts import SourceRequest
from ..product import keys
from ..settings import settings
from . import audit


class Refused(Exception):
    """A request turned away before anything was tried. Recorded, and answered with 409."""


class Unavailable(RuntimeError):
    """Something the console reads is not built yet."""


def plain(value):
    """A database value as JSON can carry it."""
    if isinstance(value, dict):
        return {name: plain(item) for name, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, (bytes, memoryview)):
        return bytes(value).hex()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def read(sql, **parameters):
    with store.engine().connect() as connection:
        return [
            plain(dict(row))
            for row in connection.execute(text(sql), parameters).mappings()
        ]


def reporting(sql, **parameters):
    """Read a reporting model; say so plainly when dbt has not built it."""
    try:
        return read(sql, **parameters)
    except ProgrammingError as error:
        raise Unavailable(
            "The reporting models are not built; run `link-lens dbt build`"
        ) from error


def links():
    """Where the other tools are. The console links to them and copies none."""
    config = settings()
    return {
        "dagster": config.dagster_url.rstrip("/"),
        "inbox": config.inbox_url.rstrip("/"),
        "dashboards": config.dashboards_url.rstrip("/"),
        "product": config.product_url.rstrip("/"),
    }


# Sources


def source_links(row):
    there = links()
    return {
        "portal": row["portal_url"],
        "okf": f"{there['product']}/v1/okf{row['okf_path']}",
        "dagster": f"{there['dagster']}/assets/snapshot?partition={row['source_id']}",
        "dashboard": f"{there['dashboards']}/d/link-lens-source-health",
        "inbox": there["inbox"] if row["waiting_for_review"] else None,
    }


def source_list(source_id=None):
    """Registered sources with their status, from the one model that defines it."""
    rows = reporting(
        "SELECT * FROM analytics.source_health "
        "WHERE (CAST(:source AS text) IS NULL OR source_id = :source) "
        "ORDER BY source_title, source_id",
        source=source_id,
    )
    return [{**row, "links": source_links(row)} for row in rows]


def source(source_id):
    found = source_list(source_id)
    if not found:
        raise KeyError(f"sources/{source_id} not found")
    return {
        **found[0],
        "snapshots": read(
            "SELECT id AS snapshot_id, format, licence, retrieved_at, observed_at, "
            "(receipt ->> 'bytes')::bigint AS bytes FROM catalog.snapshot "
            "WHERE source_id = :source ORDER BY retrieved_at DESC NULLS LAST LIMIT 20",
            source=source_id,
        ),
        "runs": read(
            "SELECT id AS run_id, kind, status, snapshot_id, thread_id, created_at, "
            "completed_at, model_calls, calculated_cost_usd FROM onboarding.run "
            "WHERE source_id = :source ORDER BY created_at DESC LIMIT 20",
            source=source_id,
        ),
        "drift_checks": read(
            "SELECT snapshot_id, status, blocking, reasons, checked_at "
            "FROM catalog.drift_check WHERE source_id = :source "
            "ORDER BY checked_at DESC LIMIT 10",
            source=source_id,
        ),
        "actions": [
            action
            for action in audit.listing(limit=500)
            if action["target"] == source_id
            or (action["result"] or {}).get("source_id") == source_id
        ][:20],
    }


def catalogue(query="", limit=50):
    """Datasets of the saved catalogue that match, best ranked first. Reads only what is stored."""
    # The experiment's own discovery revision, else the active one it was seeded from.
    discovery = (
        store.current_discovery(settings().experiment_id)
        or store.current_discovery()
        or {}
    )
    ranked = {row["dataset_id"]: row for row in discovery.get("ranked", [])}
    pattern = (
        "%"
        + query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        + "%"
    )
    rows = read(
        "SELECT id AS dataset_id, slug, title, publisher, kind, "
        "metadata ->> 'license_title' AS licence, "
        "(SELECT array_agg(DISTINCT upper(r ->> 'format') ORDER BY upper(r ->> 'format')) "
        " FROM jsonb_array_elements(coalesce(metadata -> 'resources', '[]')) AS r "
        " WHERE coalesce(r ->> 'format', '') <> '') AS formats "
        "FROM catalog.source "
        "WHERE title ILIKE :pattern OR publisher ILIKE :pattern OR slug ILIKE :pattern",
        pattern=pattern,
    )
    for row in rows:
        score = ranked.get(row["dataset_id"], {})
        row["registered"] = row.pop("kind") == "registered"
        row["relevance"] = score.get("confidence")
        # A rule and model score, never a measured probability.
        row["relevance_kind"] = "uncalibrated" if score else None
        row["catalogue_url"] = score.get("catalogue_url")
    rows.sort(key=lambda row: (-(row["relevance"] or 0.0), row["dataset_id"]))
    return {"matches": len(rows), "datasets": rows[:limit]}


def source_preview(dataset_id, resource_id=None):
    """What adding a dataset would download and what onboarding it is likely to cost. Writes nothing."""
    request = SourceRequest(dataset_id=dataset_id, resource_id=resource_id)
    return {**ingestion.preview(request), "budget": budget.onboarding_estimate()}


def add_source(
    principal, client, dataset_id, resource_id=None, confirm_paid_calls=False
):
    """Register a dataset and its snapshot and request onboarding, which makes paid model calls."""
    if not confirm_paid_calls:
        raise ValueError(
            "Adding a source starts onboarding, which makes paid model calls; "
            "confirm_paid_calls must be true"
        )
    estimate = budget.onboarding_estimate()
    if not estimate["affordable"]:
        reason = (
            f"The budget would be exceeded: {estimate['remaining_usd']:.2f} USD remains of "
            f"{estimate['cap_usd']:.2f} and onboarding is estimated at "
            f"{estimate['estimate_usd'] or 0.0:.2f}"
        )
        audit.refused(principal, "source.register", dataset_id, reason)
        raise Refused(reason)
    request = SourceRequest(dataset_id=dataset_id, resource_id=resource_id)
    asked = {"dataset_id": dataset_id, "resource_id": resource_id}
    with audit.acting(principal, "source.register", dataset_id, asked) as outcome:
        registered, snapshot = ingestion.register(request)
        requested = refresh.request_onboarding(registered["id"], client, snapshot["id"])
        outcome.update(
            source_id=registered["id"],
            snapshot_id=snapshot["id"],
            run_id=requested["run_id"],
            onboarding_started=requested["started"],
        )
    return {**outcome, "slug": registered["slug"], "budget": estimate}


def update_source(principal, source_id, changes):
    """Set or clear a source's cadence, pause it or resume it. Dagster reads the result."""
    sources.state(source_id)
    with audit.acting(principal, "source.update", source_id, changes) as outcome:
        if "cadence_days" in changes:
            sources.set_cadence(source_id, changes["cadence_days"])
        if changes.get("paused") is True:
            sources.pause(source_id, principal.name)
        if changes.get("paused") is False:
            sources.resume(source_id)
        facts = sources.state(source_id)[0]
        outcome.update(
            cadence_days=facts["cadence_days"],
            paused=facts["paused_at"] is not None,
            paused_by=facts["paused_by"],
        )
    return source(source_id)


# Releases


def release_list():
    """Releases, newest first, and the batches one could be recorded from."""
    return {
        "releases": releases.listing()[::-1],
        "batches": reporting(
            "SELECT * FROM analytics.batch_overview WHERE runs > 0 "
            "ORDER BY recorded_at DESC NULLS LAST, batch_id LIMIT 20"
        ),
    }


def create_release(principal, batch_id, notes=None):
    """Record a release in the signed-in person's name, exactly as `link-lens release create` does."""
    asked = {"batch_id": batch_id, "notes": notes}
    with audit.acting(principal, "release.create", batch_id, asked) as outcome:
        release = releases.create(batch_id, principal.name, notes)
        outcome.update(
            release_id=release["release_id"],
            ontology_hash=release["ontology_hash"],
            bundles=len(release.get("bundles") or []),
        )
    return release


# Ontology, read-only


def ontology_versions():
    """Versions with their latest gate run, and every activation. Promotion stays a CLI action."""
    versions = read(
        "SELECT sha256_hex(hash) AS ontology_hash, sha256_hex(parent_hash) AS parent_hash, "
        "label, created_at FROM ontology.ontology_version ORDER BY created_at, hash"
    )
    checks = read(
        "SELECT sha256_hex(version_hash) AS ontology_hash, check_name, result, detail, "
        "created_at FROM ontology.gate_report AS report "
        "WHERE created_at = (SELECT max(created_at) FROM ontology.gate_report "
        "                    WHERE version_hash = report.version_hash) "
        "ORDER BY check_name"
    )
    activations = read(
        "SELECT sha256_hex(version_hash) AS ontology_hash, experiment_id, status, reviewer, "
        "created_at, gate_run_at FROM ontology.activation ORDER BY created_at DESC, id DESC"
    )
    for version in versions:
        gate = [
            row for row in checks if row["ontology_hash"] == version["ontology_hash"]
        ]
        version["gate"] = (
            {
                "run_at": gate[0]["created_at"],
                "passed": all(row["result"] != "fail" for row in gate),
                "checks": [
                    {
                        "check": row["check_name"],
                        "result": row["result"],
                        "detail": row["detail"],
                    }
                    for row in gate
                ],
            }
            if gate
            else None
        )
        version["activations"] = [
            row
            for row in activations
            if row["ontology_hash"] == version["ontology_hash"]
        ]
    return versions[::-1]


# Clients, tiers and keys


def access():
    return {"clients": keys.clients(), "tiers": plain(keys.tiers())}


def create_client(principal, name, tier_id):
    asked = {"name": name, "tier_id": tier_id}
    with audit.acting(principal, "client.create", name, asked) as outcome:
        client = keys.create_client(name, tier_id)
        outcome.update(client_id=client["client_id"])
    return client


def update_client(principal, client_id, changes):
    with audit.acting(principal, "client.update", client_id, changes) as outcome:
        if changes.get("tier_id") is not None:
            outcome.update(keys.set_client_tier(client_id, changes["tier_id"]))
        if changes.get("status") is not None:
            outcome.update(keys.set_client_status(client_id, changes["status"]))
    return dict(outcome)


def issue_key(principal, client_id, label=None, expires_in_days=None):
    """Create a key. The answer carries it once; the audit log gets its prefix only."""
    asked = {"label": label, "expires_in_days": expires_in_days}
    with audit.acting(principal, "key.issue", client_id, asked) as outcome:
        key = keys.create_key(client_id, label, expires_in_days)
        outcome.update(key_id=key["key_id"], prefix=key["prefix"])
    return key


def revoke_key(principal, prefix):
    with audit.acting(principal, "key.revoke", prefix, {}) as outcome:
        outcome.update(keys.revoke_key(prefix))
    return dict(outcome)


def set_tier(principal, tier_id, limits):
    with audit.acting(principal, "tier.set", tier_id, limits) as outcome:
        tier = plain(keys.set_tier(tier_id, **limits))
        outcome.update(tier)
    return tier


# Home


def home():
    """What needs a person, and where to look further."""
    attention = []
    rows = source_list()
    for row in rows:
        reasons = [
            reason
            for reason, applies in (
                ("waiting for review", row["waiting_for_review"]),
                (
                    "drifted: the approved mapping cannot read the new file",
                    row["drift_status"] == "blocked",
                ),
                ("checks are failing", row["refresh_status"] == "failing"),
                ("overdue for a check", row["refresh_status"] == "stale"),
            )
            if applies
        ]
        if reasons:
            attention.append(
                {
                    "source_id": row["source_id"],
                    "source_title": row["source_title"],
                    "reasons": reasons,
                    "waiting_since": row["waiting_since"],
                    "links": row["links"],
                }
            )
    listed = releases.listing()
    return {
        "attention": attention,
        "sources": {
            "registered": len(rows),
            "with_cadence": sum(row["cadence_days"] is not None for row in rows),
            "paused": sum(row["paused"] for row in rows),
        },
        "latest_release": listed[-1] if listed else None,
        "budget": budget.onboarding_estimate(),
        "links": {
            **links(),
            "product_overview": f"{links()['dashboards']}/d/link-lens-product-overview",
            "data_quality": f"{links()['dashboards']}/d/link-lens-data-quality",
            "source_health": f"{links()['dashboards']}/d/link-lens-source-health",
        },
    }
