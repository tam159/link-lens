"""Releases: a human record that one batch, under one ontology, is what clients see.

Creating a release is never part of a pipeline run. It writes the release row
and builds the OKF page, line and index rows for it in one transaction. A
release never changes afterwards, and creating another does not touch it.
"""

import hashlib
import json

from sqlalchemy import select, text

from . import logs, ontology, store
from . import serving as views
from .db import catalog, copy_insert, evidence, identity, ops, serving
from .db import ontology as registry
from .db.records import render_time
from .okf import index, render

CHUNK = 500


def record(row):
    return {
        "release_id": row.id,
        "batch_id": row.batch_id,
        "ontology_hash": row.ontology_hash,
        "released_by": row.released_by,
        "released_at": render_time(row.released_at),
        "notes": row.notes,
    }


def get(connection, release_id=None):
    """A release by ID, or the latest one."""
    table = serving.release
    statement = select(table).order_by(table.c.id.desc()).limit(1)
    if release_id is not None:
        statement = statement.where(table.c.id == release_id)
    row = connection.execute(statement).first()
    if row is None:
        raise KeyError(
            "No release has been created"
            if release_id is None
            else f"releases/{release_id} not found"
        )
    return record(row)


def listing():
    with store.engine().connect() as connection:
        table = serving.release
        return [
            record(row)
            for row in connection.execute(select(table).order_by(table.c.id))
        ]


def show(release_id=None):
    """A release with the number of pages built for it, by type."""
    with store.engine().connect() as connection:
        found = get(connection, release_id)
        pages = connection.execute(
            text(
                "SELECT type, count(*) FROM serving.okf_page "
                "WHERE release_id = :release GROUP BY type ORDER BY type"
            ),
            {"release": found["release_id"]},
        ).all()
        folders = connection.execute(
            text(
                "SELECT count(DISTINCT parent) FROM serving.okf_index "
                "WHERE release_id = :release"
            ),
            {"release": found["release_id"]},
        ).scalar_one()
    return {**found, "pages": dict(map(tuple, pages)), "index_pages": folders}


def digest(release_id=None):
    """A fingerprint of what a release serves, to compare two environments.

    It covers the batch, the ontology version, every entity with its profile
    version, and every page path. Two databases that give the same digest for a
    release serve the same profiles and the same tree for it.
    """
    with store.engine().connect() as connection:
        release = get(connection, release_id)
        keys = {"release": release["release_id"]}
        profiles = connection.execute(
            text(
                "SELECT entity_id, profile_version FROM serving.profile "
                "WHERE release_id = :release ORDER BY entity_id"
            ),
            keys,
        ).all()
        pages = (
            connection.execute(
                text(
                    "SELECT path FROM serving.okf_page WHERE release_id = :release ORDER BY path"
                ),
                keys,
            )
            .scalars()
            .all()
        )
    stated = {
        "batch_id": release["batch_id"],
        "ontology_hash": release["ontology_hash"],
        "profiles": [list(row) for row in profiles],
        "pages": pages,
    }
    encoded = json.dumps(stated, sort_keys=True, separators=(",", ":")).encode()
    return {
        "release_id": release["release_id"],
        "batch_id": release["batch_id"],
        "ontology_hash": release["ontology_hash"],
        "profiles": len(profiles),
        "pages": len(pages),
        "digest": hashlib.sha256(encoded).hexdigest(),
    }


def claim_lines(fields, suffix=""):
    """`concept: value` lines for a set of profile fields."""
    lines = []
    for name, field in fields.items():
        values = field.get("values") if "values" in field else [field.get("value")]
        lines += [
            f"{name}: {value}{suffix}" for value in values or [] if value is not None
        ]
    return lines


def entity_lines(profile):
    lines = [
        "type: Business Profile",
        "title: " + render.profile_title(profile),
        "status: draft",
        "profile_version: " + profile["profile_version"],
        "entity_id: " + profile["canonical_entity_key"],
    ]
    lines += claim_lines(profile.get("fields") or {})
    for address in profile.get("addresses") or []:
        lines += claim_lines(address.get("fields") or {}, f" ({address.get('role')})")
    return lines


def build(connection, release):
    """Build the OKF page, line and index rows of a release. Returns counts."""
    release_id, at = release["release_id"], release["released_at"]
    batch = ops.batches.get(connection, release["batch_id"])
    document = registry.document(connection, release["ontology_hash"])
    pages, lines, entities, cited = [], [], [], {}

    def add(path, kind, title, description, tags, page_lines, **keys):
        pages.append(
            {
                "release_id": release_id,
                "path": path,
                "type": kind,
                "title": title,
                "description": description,
                "tags": tags,
                "status": keys.pop("status", None),
                "entity_id": None,
                "source_id": None,
                "observation_source_id": None,
                "observation_id": None,
                "concept_name": None,
                **keys,
            }
        )
        lines.extend(
            {
                "release_id": release_id,
                "path": path,
                "line_no": number,
                "line": line,
                "source_id": keys.get("source_id"),
            }
            for number, line in enumerate(page_lines, 1)
        )

    profile = identity.profile
    keys = list(
        connection.execute(
            select(profile.c.id)
            .where(profile.c.batch_id == release["batch_id"])
            .order_by(profile.c.id)
        ).scalars()
    )
    for start in range(0, len(keys), CHUNK):
        rows = (
            connection.execute(
                select(profile).where(
                    evidence.among(profile.c.id, keys[start : start + CHUNK])
                )
            )
            .mappings()
            .all()
        )
        for payload in identity.profiles.load(connection, rows):
            entity_id = payload["canonical_entity_key"]
            title = render.profile_title(payload)
            add(
                render.entity_path(entity_id),
                "Business Profile",
                title,
                "Versioned profile assembled from proposed identity links.",
                ["entity", "proposed-identity"],
                entity_lines(payload),
                status="draft",
                entity_id=entity_id,
            )
            entities.append(index.summary(payload))
            for observation_id in render.cited_ids(payload):
                cited[observation_id] = True

    # Evidence pages exist for the observations that a profile cites.
    observation, concept = evidence.observation, registry.concept
    wanted = [key for key in cited if len(key) == 64]
    for start in range(0, len(wanted), 5000):
        for row in connection.execute(
            select(
                observation.c.source_id,
                observation.c.id,
                observation.c.value,
                concept.c.name,
            )
            .join(concept, concept.c.id == observation.c.concept_id)
            .where(evidence.among(observation.c.id, wanted[start : start + 5000]))
        ):
            add(
                render.evidence_path(row.id),
                "Field Observation",
                f"{row.name}: {row.value}",
                "A source claim, not independent proof of identity.",
                ["evidence"],
                [
                    "type: Field Observation",
                    f"observation_id: {row.id}",
                    f"{row.name}: {row.value}",
                    f"source: {row.source_id}",
                ],
                source_id=row.source_id,
                observation_source_id=row.source_id,
                observation_id=row.id,
                concept_name=row.name,
            )

    sources = []
    run = store.RECORDS["runs"]
    for run_id in batch.get("run_ids") or []:
        source_id = (run.get(connection, run_id) or {}).get("source_id")
        source = catalog.sources.get(connection, source_id) if source_id else None
        if source is None or any(source_id == seen for seen, _ in sources):
            continue
        meta = source.get("metadata") or {}
        title = meta.get("title") or source_id
        publisher = (meta.get("organization") or {}).get("title", "unknown")
        add(
            render.source_path(source_id),
            "Public Data Source",
            title,
            "Publisher, source role and licence.",
            ["source"],
            [
                "type: Public Data Source",
                "title: " + title,
                "publisher: " + publisher,
                "licence: " + (meta.get("license_title") or "unknown"),
            ],
            source_id=source_id,
        )
        sources.append((source_id, title))

    concepts = []
    for name, definition in document["concepts"].items():
        add(
            render.concept_path(definition["scope"], name),
            "Ontology Concept",
            name,
            definition["definition"],
            ["ontology", definition["scope"]],
            [
                "type: Ontology Concept",
                "name: " + name,
                "scope: " + definition["scope"],
                "datatype: " + definition["type"],
                "definition: " + definition["definition"],
            ],
            concept_name=name,
        )
        concepts.append((definition["scope"], name, definition["definition"]))

    rows = [
        {"release_id": release_id, **row._asdict()}
        for row in index.build(entities, sources, concepts)
    ]
    connection.execute(
        text("SELECT serving.create_release_partitions(:release)"),
        {"release": release_id},
    )
    copy_insert(connection, serving.okf_page, pages)
    copy_insert(connection, serving.okf_line, lines)
    copy_insert(connection, serving.okf_index, rows)
    return {
        "generated_at": at,
        "pages": len(pages),
        "lines": len(lines),
        "index_entries": len(rows),
        "entities": len(entities),
        "evidence": sum(p["type"] == "Field Observation" for p in pages),
        "sources": len(sources),
        "concepts": len(concepts),
    }


def batch_version(batch_id):
    """The batch and the one ontology version its runs were onboarded under."""
    batch = store.require("batches", batch_id)
    if not batch.get("run_ids"):
        raise ValueError(f"{batch_id} is not an assembled batch")
    versions = {
        store.require("runs", run_id).get("ontology_hash")
        or ontology.digest(ontology.legacy())
        for run_id in batch["run_ids"]
    }
    if len(versions) != 1:
        raise ValueError(
            "The batch's runs were onboarded under different ontology versions"
        )
    return batch, versions.pop()


def preview(batch_id):
    """What a release of a batch would be, against the latest release. Writes nothing.

    Profiles added, removed and changed by entity and profile version, and the
    checks a release should pass. A batch assembled after a source was
    refreshed also differs by resampling; `refreshed_sources` says when to read
    the comparison with that in mind.
    """
    batch, version = batch_version(batch_id)
    with store.engine().connect() as connection:
        current = connection.execute(
            text("SELECT id, batch_id FROM ops.release ORDER BY id DESC LIMIT 1")
        ).first()
        profiles = text(
            "SELECT entity_key, sha256_hex(profile_version) FROM identity.profile "
            "WHERE batch_id = :batch"
        )
        new = dict(connection.execute(profiles, {"batch": batch_id}).all())
        old = (
            dict(connection.execute(profiles, {"batch": current.batch_id}).all())
            if current
            else {}
        )
        uncited = connection.execute(
            text(
                "SELECT count(*) FROM identity.profile_field f "
                "JOIN identity.profile p ON p.id = f.profile_id "
                "WHERE p.batch_id = :batch AND f.status = 'selected' "
                "AND f.observation_id IS NULL"
            ),
            {"batch": batch_id},
        ).scalar_one()
        links = connection.execute(
            text("SELECT count(*) FROM identity.link WHERE batch_id = :batch"),
            {"batch": batch_id},
        ).scalar_one()
        refreshed = connection.execute(
            text(
                "SELECT count(*) FROM onboarding.run "
                "WHERE id = ANY(:runs) AND kind = 'refresh'"
            ),
            {"runs": list(batch["run_ids"])},
        ).scalar_one()
        views = views_built(connection)
    already = bool(current) and current.batch_id == batch_id
    checks = [
        {"check": "the batch has profiles", "passed": bool(new)},
        {"check": "every selected field cites an observation", "passed": uncited == 0},
        {"check": "the serving views are built", "passed": views},
        {"check": "the batch is not the one already released", "passed": not already},
    ]
    return {
        "batch_id": batch_id,
        "ontology_hash": version,
        "runs": len(batch["run_ids"]),
        "profiles": len(new),
        "links": links,
        "current_release_id": current.id if current else None,
        "profiles_added": len(new.keys() - old.keys()),
        "profiles_removed": len(old.keys() - new.keys()),
        "profiles_changed": sum(new[e] != old[e] for e in new.keys() & old.keys()),
        "profiles_unchanged": sum(new[e] == old[e] for e in new.keys() & old.keys()),
        "refreshed_sources": refreshed,
        "checks": checks,
        "ready": all(check["passed"] for check in checks),
    }


def views_built(connection):
    try:
        views.require(connection)
    except ValueError:
        return False
    return True


def create(batch_id, reviewer, notes=None):
    """Record a release of a batch and build its OKF tree. A human action.

    The ontology version is the one the batch's runs were onboarded under; a
    batch whose runs disagree cannot be released.
    """
    if not reviewer or not reviewer.strip():
        raise ValueError("A release needs the name of the person releasing it")
    batch, version = batch_version(batch_id)
    ontology.register(ontology.legacy())
    ontology.resolve(version)
    table = serving.release
    with store.engine().begin() as connection:
        # The bundles built after the commit, and every client, read the views.
        views.require(connection)
        row = connection.execute(
            table.insert()
            .values(
                batch_id=batch_id,
                ontology_hash=version,
                released_by=reviewer.strip(),
                notes=notes,
            )
            .returning(table)
        ).one()
        release = record(row)
        counts = build(connection, release)
    logs.event(
        "release.created",
        **{k: v for k, v in release.items() if k != "notes"},
        **counts,
    )
    # The release is committed. Bundles of the scopes that follow a release are
    # built from it now, so none needs a command of its own.
    from . import bundles

    return {**release, **counts, "bundles": bundles.on_release(release["release_id"])}
