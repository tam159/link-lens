"""The query layer: every question a client can ask, answered from `serving`.

Each function takes the principal and a release, and applies what the tier
allows: which releases are visible (release lag, history depth) and which
sources (source scope). REST, MCP and GraphQL all call these functions, so the
rules are enforced in one place. Profiles are returned whole; scope applies to
sources, observations, evidence and the OKF tree.
"""

import base64
import binascii

from sqlalchemy import text

from ..db import is_sha256
from ..okf import render, tree
from . import Problem

DEFAULT_LIMIT, MAX_LIMIT = 50, 200
_concepts = {}


def bound(limit):
    return max(1, min(int(limit or DEFAULT_LIMIT), MAX_LIMIT))


def encode(value):
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def decode(cursor):
    if not cursor:
        return ""
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        return base64.b64decode(padded, altchars=b"-_", validate=True).decode()
    except (binascii.Error, UnicodeDecodeError) as error:
        raise Problem(
            400, "Invalid cursor", "Pass next_cursor exactly as returned."
        ) from error


def page(rows, limit, key):
    """Rows of one page and the cursor for the next, from `limit + 1` rows."""
    more = len(rows) > limit
    rows = rows[:limit]
    return rows, encode(key(rows[-1])) if more and rows else None


def not_found(what):
    return Problem(
        404, "Not found", f"{what} is not in this release or not visible to this key."
    )


def visible_releases(connection, principal):
    """Releases this principal may see, newest first.

    `release_lag` hides that many of the newest releases; `history_depth` then
    limits how many are visible, counting the current one.
    """
    rows = connection.execute(
        text(
            "SELECT release_id, ontology_hash, released_at, notes FROM serving.release "
            "ORDER BY release_id DESC OFFSET :lag LIMIT :depth"
        ),
        {"lag": principal.release_lag, "depth": principal.history_depth},
    ).mappings()
    return [dict(row) for row in rows]


def resolve_release(connection, principal, requested=None):
    """The release a call is answered from: the one asked for, or the current one."""
    releases = visible_releases(connection, principal)
    if not releases:
        raise Problem(
            404, "No release available", "No release is visible to this key yet."
        )
    if requested is None:
        return releases[0]
    for release in releases:
        if release["release_id"] == requested:
            return release
    raise Problem(
        404, "Release not available", f"Release {requested} is not visible to this key."
    )


def list_releases(connection, principal):
    releases = visible_releases(connection, principal)
    return [
        {**release, "is_current": number == 0}
        for number, release in enumerate(releases)
    ]


def in_scope(principal, column="source_id"):
    """SQL and parameters that keep a query inside the principal's sources."""
    if principal.sources is None:
        return "", {}
    return f" AND {column} = ANY(:scope)", {"scope": sorted(principal.sources)}


def concept_names(connection, release):
    """Concept names of a release's ontology. A release never changes, so they are kept."""
    key = release["release_id"]
    if key not in _concepts:
        _concepts[key] = frozenset(
            connection.execute(
                text("SELECT name FROM serving.concept WHERE release_id = :release"),
                {"release": key},
            ).scalars()
        )
    return _concepts[key]


def entity(row):
    return {
        "entity_id": row["entity_id"],
        "display_name": row["display_name"],
        "identifiers": row["identifiers"] or {},
        "status": row["status"],
        "profile_version": row["profile_version"],
        "okf_path": render.entity_path(row["entity_id"]),
    }


FIELD_MATCH = (
    " AND EXISTS (SELECT 1 FROM serving.profile_field AS f WHERE f.release_id = e.release_id "
    "AND f.entity_id = e.entity_id AND f.concept = '{concept}' AND f.value = :{name})"
)


def search_entities(
    connection,
    principal,
    release,
    name=None,
    abn=None,
    acn=None,
    state=None,
    type=None,
    cursor=None,
    limit=None,
):
    """Entities of a release, by any of name, ABN, ACN, state and entity type."""
    limit = bound(limit)
    sql = (
        "SELECT e.entity_id, e.display_name, e.identifiers, e.status, e.profile_version "
        "FROM serving.entity AS e WHERE e.release_id = :release AND e.entity_id > :after"
    )
    parameters = {
        "release": release["release_id"],
        "after": decode(cursor),
        "limit": limit + 1,
    }
    if name:
        sql += " AND e.display_name ILIKE :name"
        parameters["name"] = "%" + tree.escape(name) + "%"
    for key, value, concept in (
        ("abn", abn, "entity.abn"),
        ("acn", acn, "entity.acn"),
        ("type", type, "entity.entity_type"),
    ):
        if value:
            sql += FIELD_MATCH.format(concept=concept, name=key)
            parameters[key] = "".join(value.split()) if key != "type" else value
    if state:
        sql += (
            " AND (EXISTS (SELECT 1 FROM serving.profile_address AS a "
            "WHERE a.release_id = e.release_id AND a.entity_id = e.entity_id "
            "AND a.fields -> 'address.state' ->> 'value' = :state)"
            + FIELD_MATCH.format(concept="address.state", name="state").replace(
                " AND ", " OR ", 1
            )
            + ")"
        )
        parameters["state"] = state
    rows = (
        connection.execute(text(sql + " ORDER BY e.entity_id LIMIT :limit"), parameters)
        .mappings()
        .all()
    )
    rows, following = page(rows, limit, lambda row: row["entity_id"])
    return {"entities": [entity(row) for row in rows], "next_cursor": following}


def get_entity(connection, principal, release, entity_id):
    row = (
        connection.execute(
            text(
                "SELECT entity_id, display_name, identifiers, status, profile_version "
                "FROM serving.entity WHERE release_id = :release AND entity_id = :entity"
            ),
            {"release": release["release_id"], "entity": entity_id},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise not_found(f"Entity {entity_id}")
    return entity(row)


def get_profile(connection, principal, release, entity_id):
    """An entity's profile: every field with its status, evidence and alternatives."""
    keys = {"release": release["release_id"], "entity": entity_id}
    head = (
        connection.execute(
            text(
                "SELECT entity_id, profile_version, policy_version, status, uncertainties, "
                "source_records, groups, reconciliation FROM serving.profile "
                "WHERE release_id = :release AND entity_id = :entity"
            ),
            keys,
        )
        .mappings()
        .first()
    )
    if head is None:
        raise not_found(f"Entity {entity_id}")
    fields = connection.execute(
        text(
            'SELECT concept, status, value, "values", decision, temporal_caveat, confidence, '
            "confidence_kind, observation_source_id, observation_id, provenance, alternatives "
            "FROM serving.profile_field WHERE release_id = :release AND entity_id = :entity "
            "ORDER BY position"
        ),
        keys,
    ).mappings()
    addresses = connection.execute(
        text(
            "SELECT role, source_id, record_id, fields FROM serving.profile_address "
            "WHERE release_id = :release AND entity_id = :entity ORDER BY position"
        ),
        keys,
    ).mappings()
    return {
        "entity_id": head["entity_id"],
        "profile_version": head["profile_version"],
        "policy_version": head["policy_version"],
        "status": head["status"],
        "uncertainties": head["uncertainties"] or [],
        "fields": [
            {
                "concept": field["concept"],
                "status": field["status"],
                "value": field["value"],
                "values": field["values"],
                "decision": field["decision"],
                "temporal_caveat": field["temporal_caveat"],
                "confidence": field["confidence"],
                "confidence_kind": field["confidence_kind"],
                "observation": {
                    "source_id": field["observation_source_id"],
                    "observation_id": field["observation_id"],
                }
                if field["observation_id"]
                else None,
                "provenance": field["provenance"] or [],
                "alternatives": field["alternatives"] or [],
            }
            for field in fields
        ],
        "addresses": [dict(address) for address in addresses],
        "groups": head["groups"] or [],
        "source_records": head["source_records"] or [],
        "reconciliation": head["reconciliation"],
        "okf_path": render.entity_path(head["entity_id"]),
    }


OBSERVATION = (
    "observation_id, source_id, record_id, entity_id, concept, value, raw_value, "
    "source_fields, group_name, field_confidence, source_reliability, confidence_kind, "
    "observed_at, timestamp_basis, timezone_assumed, ingested_at, derivation_level, "
    "licence, licence_url"
)


def list_observations(
    connection,
    principal,
    release,
    entity_id,
    concept=None,
    source=None,
    cursor=None,
    limit=None,
):
    """Source claims about an entity, from the sources this key may see."""
    get_entity(connection, principal, release, entity_id)
    limit = bound(limit)
    scope, parameters = in_scope(principal)
    after_source, _, after_id = decode(cursor).rpartition(":")
    sql = (
        f"SELECT {OBSERVATION} FROM serving.observation WHERE release_id = :release "
        "AND entity_id = :entity AND (source_id, observation_id) > (:after_source, :after_id)"
        + scope
    )
    parameters.update(
        release=release["release_id"],
        entity=entity_id,
        after_source=after_source,
        after_id=after_id,
        limit=limit + 1,
    )
    if concept:
        sql += " AND concept = :concept"
        parameters["concept"] = concept
    if source:
        sql += " AND source_id = :source"
        parameters["source"] = source
    rows = (
        connection.execute(
            text(sql + " ORDER BY source_id, observation_id LIMIT :limit"), parameters
        )
        .mappings()
        .all()
    )
    rows, following = page(
        rows, limit, lambda r: f"{r['source_id']}:{r['observation_id']}"
    )
    return {"observations": [dict(row) for row in rows], "next_cursor": following}


def get_evidence(connection, principal, release, observation_id):
    """One claim with where it comes from: record, snapshot, source and licence."""
    if not is_sha256(observation_id):
        raise not_found(f"Observation {observation_id}")
    scope, parameters = in_scope(principal, "o.source_id")
    row = (
        connection.execute(
            text(
                "SELECT o.observation_id, o.source_id, o.record_id, o.entity_id, o.concept, "
                "o.value, o.raw_value, o.source_fields, o.group_name, o.field_confidence, "
                "o.source_reliability, o.confidence_kind, o.observed_at, o.timestamp_basis, "
                "o.timezone_assumed, o.ingested_at, o.derivation_level, o.licence, o.licence_url, "
                "e.sheet, e.row_no, e.locator, e.snapshot_id, e.format, e.snapshot_observed_at, "
                "e.snapshot_observed_at_basis, e.retrieved_at, e.source_title, e.publisher, e.portal "
                "FROM serving.observation AS o JOIN serving.evidence AS e "
                "ON e.release_id = o.release_id AND e.source_id = o.source_id "
                "AND e.observation_key = o.observation_key "
                "WHERE o.release_id = :release AND o.observation_key = sha256_from_hex(:observation)"
                + scope
            ),
            {
                "release": release["release_id"],
                "observation": observation_id,
                **parameters,
            },
        )
        .mappings()
        .first()
    )
    if row is None:
        raise not_found(f"Observation {observation_id}")
    return {
        "observation": {key: row[key] for key in OBSERVATION.split(", ")},
        "record": {
            "record_id": row["record_id"],
            "sheet": row["sheet"],
            "row_no": row["row_no"],
            "locator": row["locator"],
        },
        "snapshot": {
            "snapshot_id": row["snapshot_id"],
            "format": row["format"],
            "observed_at": row["snapshot_observed_at"],
            "observed_at_basis": row["snapshot_observed_at_basis"],
            "retrieved_at": row["retrieved_at"],
        },
        "source": {
            "source_id": row["source_id"],
            "title": row["source_title"],
            "publisher": row["publisher"],
            "portal": row["portal"],
        },
        "licence": row["licence"],
        "licence_url": row["licence_url"],
    }


def list_links(connection, principal, release, entity_id):
    """Identity links behind an entity. A link is a proposal until it is reviewed."""
    get_entity(connection, principal, release, entity_id)
    rows = connection.execute(
        text(
            "SELECT link_id, entity_id, rule, rule_version, score, score_kind, threshold, "
            "status, human_review_status, a_source_id, a_record_id, b_source_id, b_record_id, "
            "evidence FROM serving.link WHERE release_id = :release AND entity_id = :entity "
            "ORDER BY link_id"
        ),
        {"release": release["release_id"], "entity": entity_id},
    ).mappings()
    return [
        {
            **{
                k: row[k]
                for k in ("link_id", "entity_id", "rule", "rule_version", "score")
            },
            **{
                k: row[k]
                for k in ("score_kind", "threshold", "status", "human_review_status")
            },
            "records": [
                {"source_id": row["a_source_id"], "record_id": row["a_record_id"]},
                {"source_id": row["b_source_id"], "record_id": row["b_record_id"]},
            ],
            "evidence": row["evidence"],
        }
        for row in rows
    ]


def source(row):
    return {
        "source_id": row["source_id"],
        "title": row["title"],
        "publisher": row["publisher"],
        "portal": row["portal"],
        "licence": row["licence"] or row["licence_title"] or "unknown",
        "licence_url": row["licence_url"],
        "snapshot_id": row["snapshot_id"],
        "retrieved_at": row["retrieved_at"],
        "okf_path": render.source_path(row["source_id"]),
    }


def list_sources(connection, principal, release, source_id=None):
    scope, parameters = in_scope(principal)
    sql = "SELECT * FROM serving.source WHERE release_id = :release" + scope
    parameters["release"] = release["release_id"]
    if source_id is not None:
        sql += " AND source_id = :source"
        parameters["source"] = source_id
    rows = connection.execute(
        text(sql + " ORDER BY title, source_id"), parameters
    ).mappings()
    return [source(row) for row in rows]


def get_source(connection, principal, release, source_id):
    found = list_sources(connection, principal, release, source_id)
    if not found:
        raise not_found(f"Source {source_id}")
    return found[0]


def describe_concepts(connection, principal, release, scope=None):
    """Concepts of the release's ontology, in the ontology's own order."""
    rows = connection.execute(
        text(
            "SELECT name, scope, datatype, cardinality, definition, minimum, maximum, "
            "allowed_values, requires FROM serving.concept WHERE release_id = :release "
            "AND (CAST(:scope AS text) IS NULL OR scope = :scope) ORDER BY position"
        ),
        {"release": release["release_id"], "scope": scope},
    ).mappings()
    return [
        {**row, "okf_path": render.concept_path(row["scope"], row["name"])}
        for row in rows
    ]


def okf(call, connection, principal, release, *arguments, **options):
    """Run a tree function for this principal, turning its errors into problems."""
    try:
        return call(
            connection,
            release["release_id"],
            *arguments,
            sources=principal.sources,
            **options,
        )
    except KeyError as error:
        raise not_found("The path") from error
    except ValueError as error:
        raise Problem(400, "Invalid request", str(error)) from error


def okf_ls(connection, principal, release, path="/", cursor=None, limit=None):
    return okf(
        tree.ls, connection, principal, release, path, cursor=cursor, limit=limit or 200
    )


def okf_read(connection, principal, release, path, offset=0, limit=None):
    return okf(
        tree.read, connection, principal, release, path, offset=offset, limit=limit
    )


def okf_find(
    connection,
    principal,
    release,
    path="/",
    type=None,
    tags=None,
    status=None,
    cursor=None,
    limit=None,
):
    return okf(
        tree.find,
        connection,
        principal,
        release,
        path,
        type=type,
        tags=tags,
        status=status,
        cursor=cursor,
        limit=limit or 100,
    )


def okf_grep(connection, principal, release, pattern, path, cursor=None, limit=None):
    import re

    try:
        re.compile(pattern)
    except re.error as error:
        raise Problem(400, "Invalid pattern", str(error)) from error
    return okf(
        tree.grep,
        connection,
        principal,
        release,
        pattern,
        path,
        cursor=cursor,
        limit=limit or 100,
    )
