"""The query layer: every question a client can ask, answered from `serving`.

Each function takes the principal and a release, and applies what the tier
allows: which releases are visible (release lag, history depth) and which
sources (source scope). REST, MCP and GraphQL all call these functions, so the
rules are enforced in one place. Profiles are returned whole; scope applies to
sources, observations, evidence and the OKF tree.
"""

import base64
import binascii
import json
from collections import OrderedDict

from sqlalchemy import text

from .. import bundles
from ..db import is_sha256
from ..okf import render, tree
from ..ontology import checks
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


def page(rows, limit, key, budget=None):
    """Rows of one page and the cursor for the next, from `limit + 1` rows.

    `budget` is the most characters of JSON a page may hold. A page always has
    its first row, and the rows left out come with the next cursor.
    """
    more = len(rows) > limit
    rows = rows[:limit]
    if budget is not None:
        kept, size = [], 0
        for row in rows:
            size += len(json.dumps(dict(row), default=str))
            if kept and size > budget:
                break
            kept.append(row)
        more, rows = more or len(kept) < len(rows), kept
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
    "AND f.entity_id = e.entity_id AND f.concept = '{concept}' AND f.value_text = :{name})"
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
    budget=None,
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
    rows, following = page(rows, limit, lambda row: row["entity_id"], budget)
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


SHOWN = 10  # values or alternatives of one claim that a profile summary lists
CONFIDENCE_KIND = "uncalibrated mapping/source judgements"


def cite(entry):
    """What identifies a piece of evidence, without repeating the claim it backs."""
    return {
        "observation_id": entry.get("id"),
        "source_id": entry.get("source_id"),
        "observed_at": entry.get("observed_at"),
        "observed_at_basis": entry.get("observed_at_basis"),
    }


def option(entry):
    return {
        "value": entry.get("value"),
        "confidence": entry.get("confidence"),
        "evidence": [cite(e) for e in entry.get("provenance") or []],
    }


def claim(concept, field):
    """A profile field with its evidence cited by ID instead of quoted."""
    values, alternatives = field.get("values"), field.get("alternatives") or []
    return {
        "concept": concept,
        "status": field.get("status"),
        "value": field.get("value"),
        "values": None if values is None else [option(v) for v in values[:SHOWN]],
        "values_total": None if values is None else len(values),
        "decision": field.get("decision"),
        "temporal_caveat": field.get("temporal_caveat"),
        "confidence": field.get("confidence"),
        "confidence_kind": CONFIDENCE_KIND,
        "evidence": [cite(e) for e in field.get("provenance") or []],
        "alternatives": [option(a) for a in alternatives[:SHOWN]],
        "alternatives_total": len(alternatives),
    }


def cited_sources(claims):
    for item in claims:
        for entry in item["evidence"]:
            yield entry["source_id"]
        for chosen in (item["values"] or []) + item["alternatives"]:
            for entry in chosen["evidence"]:
                yield entry["source_id"]


def get_profile_summary(connection, principal, release, entity_id):
    """A profile sized for an agent: every claim, its evidence cited by ID.

    The values, statuses, decisions and alternatives are those of `get_profile`.
    What is left out is the copy of each observation that a profile quotes
    (raw locator, record, repeated value); `get_evidence` returns it for an ID.
    A claim with many values lists the first `SHOWN` and says how many there are.
    """
    profile = get_profile(connection, principal, release, entity_id)
    fields = [claim(field["concept"], field) for field in profile["fields"]]
    addresses = [
        {
            "role": address["role"],
            "source_id": address["source_id"],
            "record_id": address["record_id"],
            "fields": [claim(name, f) for name, f in (address["fields"] or {}).items()],
        }
        for address in profile["addresses"]
    ]
    groups = [
        {
            "group_id": group.get("id"),
            "scope": group.get("scope"),
            "source_id": group.get("source_id"),
            "record_id": group.get("source_record_id"),
            "decision": group.get("decision"),
            "fields": [
                claim(name, f) for name, f in (group.get("fields") or {}).items()
            ],
        }
        for group in profile["groups"]
    ]
    parts = addresses + groups
    cited = set(cited_sources(fields + [f for part in parts for f in part["fields"]]))
    cited |= {part["source_id"] for part in parts if part["source_id"]}
    rows = connection.execute(
        text(
            "SELECT source_id, title, licence, licence_title, licence_url "
            "FROM serving.source WHERE release_id = :release "
            "AND source_id = ANY (CAST(:sources AS text[])) ORDER BY source_id"
        ),
        {"release": release["release_id"], "sources": sorted(cited)},
    ).mappings()
    return {
        "entity_id": profile["entity_id"],
        "profile_version": profile["profile_version"],
        "status": profile["status"],
        "uncertainties": profile["uncertainties"],
        "fields": fields,
        "addresses": addresses,
        "groups": groups,
        # A licence is owed for every source a value came from, whatever the
        # key's scope. The title of a source outside the scope is not given.
        "sources": [
            {
                "source_id": row["source_id"],
                "title": row["title"]
                if principal.sources is None or row["source_id"] in principal.sources
                else None,
                "licence": row["licence"] or row["licence_title"] or "unknown",
                "licence_url": row["licence_url"],
            }
            for row in rows
        ],
        "okf_path": profile["okf_path"],
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
    budget=None,
):
    """Source claims about an entity, from the sources this key may see."""
    limit = bound(limit)
    records = connection.execute(
        text(
            "SELECT source_records FROM serving.profile "
            "WHERE release_id = :release AND entity_id = :entity"
        ),
        {"release": release["release_id"], "entity": entity_id},
    ).first()
    if records is None:
        raise not_found(f"Entity {entity_id}")
    # The entity's records are named by its profile; looking observations up by
    # record reads a few index entries instead of every claim of the release.
    wanted = [
        pair
        for pair in records.source_records or []
        if (principal.sources is None or pair[0] in principal.sources)
        and (source is None or pair[0] == source)
        and is_sha256(pair[1])
    ]
    after_source, _, after_id = decode(cursor).rpartition(":")
    sql = (
        f"SELECT {OBSERVATION} FROM serving.observation WHERE release_id = :release "
        # The two array conditions are what the indexes and partition pruning
        # use, and the pair condition keeps a record of one source from matching
        # a record of the same key in another.
        "AND source_id = ANY (CAST(:sources AS text[])) "
        "AND record_key = ANY (CAST(:keys AS bytea[])) "
        "AND (source_id, record_id) IN "
        "(SELECT * FROM unnest(CAST(:sources AS text[]), CAST(:records AS text[]))) "
        "AND (source_id, observation_id) > (:after_source, :after_id)"
    )
    parameters = {
        "release": release["release_id"],
        "sources": [pair[0] for pair in wanted],
        "records": [pair[1] for pair in wanted],
        "keys": [bytes.fromhex(pair[1]) for pair in wanted],
        "after_source": after_source,
        "after_id": after_id,
        "limit": limit + 1,
    }
    if concept:
        sql += " AND concept = :concept"
        parameters["concept"] = concept
    rows = (
        connection.execute(
            text(sql + " ORDER BY source_id, observation_id LIMIT :limit"), parameters
        )
        .mappings()
        .all()
    )
    rows, following = page(
        rows, limit, lambda r: f"{r['source_id']}:{r['observation_id']}", budget
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
    """Identity links behind an entity. A link is a proposal until it is reviewed.

    A link quotes both of its records, so a key sees it only when both of their
    sources are in its scope.
    """
    get_entity(connection, principal, release, entity_id)
    first, parameters = in_scope(principal, "a_source_id")
    second, _ = in_scope(principal, "b_source_id")
    rows = connection.execute(
        text(
            "SELECT link_id, entity_id, rule, rule_version, score, score_kind, threshold, "
            "status, human_review_status, a_source_id, a_record_id, b_source_id, b_record_id, "
            "evidence FROM serving.link WHERE release_id = :release AND entity_id = :entity"
            f"{first}{second} ORDER BY link_id"
        ),
        {"release": release["release_id"], "entity": entity_id, **parameters},
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
        {
            **row,
            "checks": checks(tree.concept_record(row)),
            "okf_path": render.concept_path(row["scope"], row["name"]),
        }
        for row in rows
    ]


def get_bundle(connection, principal, release):
    """The bundle built for this key's client and a release, if its tier has bundles."""
    if not principal.bundle_downloads:
        raise Problem(
            403, "Bundles not in tier", "This tier does not include bundle downloads."
        )
    row = (
        connection.execute(
            text(
                "SELECT scope, source_scope, entity_count, file_count, size_bytes, "
                "sha256, manifest_sha256, uri, created_at FROM serving.bundle "
                "WHERE release_id = :release AND client_id = CAST(:client AS uuid)"
            ),
            {"release": release["release_id"], "client": principal.client_id},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise not_found("A bundle for this client")
    # A bundle holds what the client could see when it was built. If the tier
    # has since been narrowed, the files are no longer the client's to have.
    covered, allowed = row["source_scope"], principal.sources
    if allowed is not None and (covered is None or not set(covered) <= allowed):
        raise Problem(
            409,
            "Bundle out of date",
            "It was built for more sources than this key may now see. Ask for a new one.",
        )
    return {"release_id": release["release_id"], **row}


def bundle_artifact(connection, sha):
    """Where a bundle's bytes are. Only a bundle can be fetched by its hash."""
    uri = connection.execute(
        text("SELECT uri FROM serving.bundle WHERE sha256 = :sha LIMIT 1"), {"sha": sha}
    ).scalar_one_or_none()
    if uri is None:
        raise Problem(404, "Not found", "The link is invalid or has expired.")
    return uri


VIEWERS, _viewers = 128, OrderedDict()


def entity_viewer(connection, principal, release, entity_id):
    """The graph viewer of one entity, its evidence and its sources, as HTML.

    Built from the same pages as the tree and kept by profile version, which
    changes whenever the profile does. Returns the HTML and that version.
    """
    found = get_entity(connection, principal, release, entity_id)
    scope = None if principal.sources is None else tuple(sorted(principal.sources))
    key = (release["release_id"], entity_id, found["profile_version"], scope)
    if key in _viewers:
        _viewers.move_to_end(key)
    else:
        record = tree.release_record(connection, release["release_id"])
        html = bundles.entity_viewer(connection, record, entity_id, principal.sources)
        if html is None:
            raise not_found(f"Entity {entity_id}")
        _viewers[key] = html
        while len(_viewers) > VIEWERS:
            _viewers.popitem(last=False)
    return _viewers[key], found["profile_version"]


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
