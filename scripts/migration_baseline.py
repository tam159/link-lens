"""Record what the generic store holds, to verify each migration and backfill.

Read-only: one REPEATABLE READ, READ ONLY transaction, on either layout of the 17
generic tables (`public` before migration 0005, `legacy` after it).

    uv run python scripts/migration_baseline.py
    uv run python scripts/migration_baseline.py --check outputs/local-run/migration-baseline.json

    uv run python scripts/migration_baseline.py --typed --check outputs/local-run/migration-baseline.json

The first form writes `outputs/local-run/migration-baseline.json` and refuses to
replace an existing file without `--force`. The second recomputes the baseline and
compares it with a saved one; `generated_at` and `environment` are not compared.
The third computes the same figures from the typed schemas, for the domains that
have moved, and compares only those with the saved baseline.

Once a database has grown past that baseline (refreshes add snapshots, runs and
observations), compare a migration with the database just before it instead:

    uv run python scripts/migration_baseline.py --typed --output before.json
    # ... migrate ...
    uv run python scripts/migration_baseline.py --typed --check before.json

`--typed --output` writes the typed figures to a file of your choosing; it never
writes the default baseline file, which records the database before the
production migrations.

A digest is the SHA-256 of the values sorted by code point and joined by newlines.
`payloads` digests `id:md5(payload::jsonb::text)`, PostgreSQL's canonical jsonb
text, so it is the same before and after the json to jsonb conversion.
"""

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

FORMAT = "link-lens-migration-baseline-1"
DEFAULT_OUTPUT = Path("outputs/local-run/migration-baseline.json")
UNSET = "(unset)"
NOT_COMPARED = ("generated_at", "environment")
TABLES = [
    "ontologies",
    "ontology_events",
    "budget_reservations",
    "sources",
    "snapshots",
    "runs",
    "mappings",
    "approvals",
    "observations",
    "entities",
    "memberships",
    "links",
    "profiles",
    "evaluations",
    "artifacts",
    "events",
    "batches",
]


def digest(values):
    return hashlib.sha256("\n".join(sorted(values)).encode()).hexdigest()


def summary(values):
    values = list(values)
    return {"count": len(values), "digest": digest(values)}


def table_summary(rows):
    """Counts and ID digests for one table, by kind and by owner within a kind."""
    kinds = defaultdict(lambda: defaultdict(list))
    for row in rows:
        kinds[row.kind][row.owner_id].append(row.id)
    return {
        "rows": len(rows),
        "ids": digest(r.id for r in rows),
        "payloads": digest(f"{r.id}:{r.payload_md5}" for r in rows),
        "kinds": {
            kind: {
                "rows": sum(len(ids) for ids in owners.values()),
                "ids": digest(i for ids in owners.values() for i in ids),
                "owners": {
                    owner: {"rows": len(ids), "ids": digest(ids)}
                    for owner, ids in owners.items()
                },
            }
            for kind, owners in kinds.items()
        },
    }


def collect(connection):
    """Build the baseline from an open connection. Runs SELECT statements only."""

    def query(sql):
        return connection.execute(text(sql.format(schema=schema))).all()

    schema = connection.execute(
        text(
            "SELECT table_schema FROM information_schema.tables "
            "WHERE table_name = 'observations' AND table_schema IN ('legacy', 'public')"
        )
    ).scalar_one()

    tables = {
        name: table_summary(
            query(
                "SELECT id, kind, owner_id, md5(payload::jsonb::text) AS payload_md5 "
                f"FROM {{schema}}.{name}"
            )
        )
        for name in TABLES
    }

    runs = query(
        "SELECT id, kind, coalesce(payload->>'experiment_id', '{unset}') AS experiment "
        "FROM {{schema}}.runs".format(unset=UNSET)
    )
    experiment_of = {r.id: r.experiment for r in runs}
    mappings = query(
        "SELECT id, owner_id AS run_id, payload->>'config_hash' AS config_hash "
        "FROM {schema}.mappings"
    )
    approvals = query("SELECT id, owner_id AS run_id FROM {schema}.approvals")
    observations = query(
        "SELECT id, payload->>'config_hash' AS config_hash, "
        "(payload->>'source_id') || ':' || (payload->>'source_record_id') AS record "
        "FROM {schema}.observations"
    )
    reservations = query(
        "SELECT coalesce(payload->>'experiment_id', owner_id) AS experiment "
        "FROM {schema}.budget_reservations"
    )
    batches = query(
        "SELECT id, kind, payload->>'experiment_id' AS experiment, "
        "payload->>'baseline_batch_id' AS baseline_batch_id, "
        "payload->'run_ids' AS run_ids, payload->'counts' AS counts "
        "FROM {schema}.batches WHERE kind IN ('pipeline', 'enhancement')"
    )
    memberships = query(
        "SELECT id, owner_id AS batch_id, payload->>'entity_id' AS entity_id "
        "FROM {schema}.memberships"
    )
    links = query("SELECT id, owner_id AS batch_id FROM {schema}.links")
    profiles = query(
        "SELECT id, owner_id AS batch_id, payload->>'profile_version' AS version "
        "FROM {schema}.profiles"
    )

    # An observation's owner is a run when extraction stored it and a source when
    # assembly did, so its run is found through the mapping it was extracted with.
    run_of_config = {m.config_hash: m.run_id for m in mappings}
    by_run = defaultdict(list)
    for row in observations:
        by_run[run_of_config.get(row.config_hash)].append(row)

    def evidence(run_ids):
        rows = [row for run_id in run_ids for row in by_run.get(run_id, [])]
        return {
            "observations": summary(r.id for r in rows),
            "source_records": summary({r.record for r in rows}),
        }

    experiments = {}
    names = set(experiment_of.values()) | {r.experiment for r in reservations}
    names |= {b.experiment for b in batches if b.experiment}
    for name in names:
        run_ids = [r.id for r in runs if r.experiment == name]
        experiments[name] = {
            "runs": dict(Counter(r.kind for r in runs if r.experiment == name)),
            "mappings": summary(m.config_hash for m in mappings if m.run_id in run_ids),
            "approvals": summary(a.id for a in approvals if a.run_id in run_ids),
            **evidence(run_ids),
            "budget_reservations": sum(r.experiment == name for r in reservations),
        }

    batch_summaries = {}
    for batch in batches:
        run_ids = batch.run_ids or []
        own = [m for m in memberships if m.batch_id == batch.id]
        batch_summaries[batch.id] = {
            "kind": batch.kind,
            # A pipeline batch has no experiment of its own; its runs carry it.
            "experiments": sorted(
                {experiment_of.get(r, UNSET) for r in run_ids}
                | ({batch.experiment} if batch.experiment else set())
            ),
            "baseline_batch_id": batch.baseline_batch_id,
            "stored_counts": batch.counts,
            "runs": summary(run_ids),
            # Observations stored for the batch's runs, not the batch's cohort.
            **evidence(run_ids),
            "memberships": summary(m.id for m in own),
            "entities": summary({m.entity_id for m in own}),
            "links": summary(r.id for r in links if r.batch_id == batch.id),
            "profile_versions": summary(
                f"{p.id}:{p.version}" for p in profiles if p.batch_id == batch.id
            ),
        }

    by_config = defaultdict(list)
    for row in observations:
        by_config[row.config_hash].append(row.id)

    return {
        "format": FORMAT,
        "tables": tables,
        "experiments": experiments,
        "batches": batch_summaries,
        "observations_by_config_hash": {
            config: summary(ids) for config, ids in by_config.items()
        },
        "digests": {
            "ontology_hashes": summary(
                r.id for r in query("SELECT id FROM {schema}.ontologies")
            ),
            "config_hashes": summary(m.config_hash for m in mappings),
            "observation_ids": summary(r.id for r in observations),
            "observations_without_mapping": summary(r.id for r in by_run[None]),
            "record_ids": summary({r.record for r in observations}),
            "profile_versions": summary(f"{p.id}:{p.version}" for p in profiles),
        },
        "environment": {
            "schema": schema,
            "payload_type": connection.execute(
                text(
                    "SELECT data_type FROM information_schema.columns "
                    "WHERE table_schema = :schema AND table_name = 'observations' "
                    "AND column_name = 'payload'"
                ),
                {"schema": schema},
            ).scalar_one(),
            "alembic_version": connection.execute(
                text("SELECT version_num FROM public.alembic_version")
            ).scalar_one_or_none(),
        },
    }


RECORD_TABLES = {
    "sources": "catalog.source",
    "snapshots": "catalog.snapshot",
    "runs": "onboarding.run",
    "mappings": "onboarding.mapping",
    "approvals": "onboarding.approval",
    "entities": "identity.entity",
    "memberships": "identity.membership",
    "links": "identity.link",
    "profiles": "identity.profile",
    "evaluations": "ops.evaluation",
    "events": "ops.event",
    "budget_reservations": "ops.model_call",
}
# The store's batches table is three typed tables; the model cache also holds
# the ontology job's cached responses, which were never batches.
BATCHES = """
    SELECT id, kind, owner_id, '' AS payload_md5 FROM ops.batch
    UNION ALL SELECT id, kind, owner_id, '' FROM ops.triage_decision
    UNION ALL SELECT id, kind, owner_id, '' FROM ops.model_cache WHERE kind <> 'model_cache'
"""


def collect_typed(connection):
    """The baseline figures that the typed schemas can answer.

    Covers every table except the legacy ontology history, whose content is in
    the ontology registry. Payload digests are not computed, because typed rows
    are not stored as one JSON text.
    """

    def query(sql):
        return connection.execute(text(sql)).all()

    def grouped(rows):
        summary = table_summary(rows)
        del summary["payloads"]  # typed rows are not stored as one JSON text
        return summary

    tables = {
        name: grouped(
            query(f"SELECT id, kind, owner_id, '' AS payload_md5 FROM {table}")
        )
        for name, table in RECORD_TABLES.items()
    }
    tables["batches"] = grouped(query(BATCHES))
    tables["artifacts"] = grouped(
        query(
            "SELECT sha256_hex(sha256) AS id, '' AS kind, '' AS owner_id, "
            "'' AS payload_md5 FROM catalog.artifact"
        )
    )
    runs = query(
        "SELECT id, kind, coalesce(experiment_id, '{unset}') AS experiment "
        "FROM onboarding.run".format(unset=UNSET)
    )
    experiment_of = {r.id: r.experiment for r in runs}
    mappings = query(
        "SELECT id, owner_id AS run_id, sha256_hex(config_hash) AS config_hash "
        "FROM onboarding.mapping"
    )
    approvals = query("SELECT id, owner_id AS run_id FROM onboarding.approval")
    observations = query(
        "SELECT sha256_hex(id) AS id, sha256_hex(config_hash) AS config_hash, "
        "source_id || ':' || sha256_hex(record_id) AS record "
        "FROM evidence.observation"
    )
    tables["observations"] = {
        "rows": len(observations),
        "ids": digest(r.id for r in observations),
    }
    batches = query(
        "SELECT id, kind, experiment_id AS experiment, baseline_batch_id, run_ids, "
        "counts FROM ops.batch WHERE kind IN ('pipeline', 'enhancement')"
    )
    reservations = query(
        "SELECT coalesce(experiment_id, owner_id) AS experiment FROM ops.model_call"
    )
    memberships = query(
        "SELECT id, owner_id AS batch_id, entity_id FROM identity.membership"
    )
    links = query("SELECT id, owner_id AS batch_id FROM identity.link")
    profiles = query(
        "SELECT id, owner_id AS batch_id, sha256_hex(profile_version) AS version "
        "FROM identity.profile"
    )

    run_of_config = {m.config_hash: m.run_id for m in mappings}
    by_run, by_config = defaultdict(list), defaultdict(list)
    for row in observations:
        by_run[run_of_config.get(row.config_hash)].append(row)
        by_config[row.config_hash].append(row.id)

    def evidence(run_ids):
        rows = [row for run_id in run_ids for row in by_run.get(run_id, [])]
        return {
            "observations": summary(r.id for r in rows),
            "source_records": summary({r.record for r in rows}),
        }

    experiments = {}
    names = set(experiment_of.values()) | {r.experiment for r in reservations}
    names |= {b.experiment for b in batches if b.experiment}
    for name in names:
        run_ids = [r.id for r in runs if r.experiment == name]
        experiments[name] = {
            "runs": dict(Counter(r.kind for r in runs if r.experiment == name)),
            "mappings": summary(m.config_hash for m in mappings if m.run_id in run_ids),
            "approvals": summary(a.id for a in approvals if a.run_id in run_ids),
            **evidence(run_ids),
            "budget_reservations": sum(r.experiment == name for r in reservations),
        }
    batch_summaries = {}
    for batch in batches:
        run_ids = batch.run_ids or []
        own = [m for m in memberships if m.batch_id == batch.id]
        batch_summaries[batch.id] = {
            "kind": batch.kind,
            "experiments": sorted(
                {experiment_of.get(r, UNSET) for r in run_ids}
                | ({batch.experiment} if batch.experiment else set())
            ),
            "baseline_batch_id": batch.baseline_batch_id,
            "stored_counts": batch.counts,
            "runs": summary(run_ids),
            **evidence(run_ids),
            "memberships": summary(m.id for m in own),
            "entities": summary({m.entity_id for m in own}),
            "links": summary(r.id for r in links if r.batch_id == batch.id),
            "profile_versions": summary(
                f"{p.id}:{p.version}" for p in profiles if p.batch_id == batch.id
            ),
        }
    return {
        "tables": tables,
        "experiments": experiments,
        "batches": batch_summaries,
        "observations_by_config_hash": {
            config: summary(ids) for config, ids in by_config.items()
        },
        "digests": {
            "ontology_hashes": summary(
                r.id
                for r in query(
                    "SELECT sha256_hex(hash) AS id FROM ontology.ontology_version"
                )
            ),
            "config_hashes": summary(m.config_hash for m in mappings),
            "observation_ids": summary(r.id for r in observations),
            "observations_without_mapping": summary(r.id for r in by_run[None]),
            "record_ids": summary(
                r.record
                for r in query(
                    "SELECT source_id || ':' || sha256_hex(id) AS record "
                    "FROM evidence.source_record"
                )
            ),
            "profile_versions": summary(f"{p.id}:{p.version}" for p in profiles),
        },
    }


def baseline(database_url, typed=False):
    engine = create_engine(database_url, poolclass=NullPool)
    try:
        with engine.connect().execution_options(
            isolation_level="REPEATABLE READ", postgresql_readonly=True
        ) as connection:
            return (collect_typed if typed else collect)(connection)
    finally:
        engine.dispose()


def covered(saved, current):
    """The part of a saved baseline that `current` has figures for."""
    if isinstance(saved, dict) and isinstance(current, dict):
        return {k: covered(saved[k], current[k]) for k in current if k in saved}
    return saved


def comparable(value):
    return {k: v for k, v in value.items() if k not in NOT_COMPARED}


def differences(old, new, path=""):
    """Paths whose values differ between two baselines."""
    if isinstance(old, dict) and isinstance(new, dict):
        found = []
        for key in sorted(old.keys() | new.keys()):
            here = f"{path}/{key}"
            if key not in old or key not in new:
                found.append(here + (" (missing)" if key not in new else " (added)"))
            else:
                found.extend(differences(old[key], new[key], here))
        return found
    return [] if old == new else [f"{path}: {old!r} -> {new!r}"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", type=Path, help="compare with a saved baseline")
    parser.add_argument(
        "--typed",
        action="store_true",
        help="compute from the typed schemas; with --check, or --output to another file",
    )
    parser.add_argument("--force", action="store_true", help="replace --output")
    parser.add_argument("--database-url", help="default: LINK_LENS_DATABASE_URL")
    args = parser.parse_args(argv)

    if args.typed and not args.check and args.output == DEFAULT_OUTPUT:
        parser.error(
            "--typed compares with a saved baseline (--check FILE) or writes the "
            "typed figures to another file (--output FILE); it never replaces "
            f"{DEFAULT_OUTPUT}"
        )
    if not args.check and args.output.exists() and not args.force:
        parser.error(f"{args.output} exists; use --check to compare or --force")
    url = args.database_url
    if not url:
        from link_lens.settings import settings

        url = settings().database_url
    current = baseline(url, args.typed)

    if args.check:
        saved = json.loads(args.check.read_text())
        if args.typed:
            saved = covered(saved, current)
            # A batch or experiment the typed schemas do not know is a difference.
            for section in ("experiments", "batches", "observations_by_config_hash"):
                current[section] = {
                    **{k: None for k in json.loads(args.check.read_text())[section]},
                    **current[section],
                }
                saved[section] = {
                    **{k: None for k in current[section]},
                    **saved[section],
                }
        found = differences(comparable(saved), comparable(current))
        for line in found[:50]:
            print(line)
        print(f"{len(found)} difference(s) from {args.check}")
        return 1 if found else 0

    current["generated_at"] = datetime.now(UTC).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(current, indent=1, sort_keys=True) + "\n")
    print(f"wrote {args.output}")
    for name, value in current.get("digests", {}).items():
        print(f"{name}: {value['count']} {value['digest']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
