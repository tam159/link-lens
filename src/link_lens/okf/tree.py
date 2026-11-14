"""The OKF tree of a release as a virtual file system: ls, read, find, grep.

Nothing is stored as files. Folders and search come from the tables built when
the release was created; a page is rendered when it is read. Everything is read
from the `serving` schema, so the product role, which can read nothing else,
can serve the whole tree. Every function
takes the release and, optionally, the sources a caller may see. A page that
belongs to one source (a source page, an evidence page) is hidden from a caller
whose scope does not include that source.
"""

import re

from sqlalchemy import text

from ..db.records import render_time
from . import index, render

PAGE_LIMIT = 200
MAX_LIMIT = 1000


def visible(sources):
    """SQL for the scope filter, and its parameters."""
    if sources is None:
        return "", {}
    return " AND (source_id IS NULL OR source_id = ANY(:sources))", {
        "sources": list(sources)
    }


def folder(path):
    path = "/" + path.strip("/")
    return path


def bound(limit):
    return max(1, min(int(limit), MAX_LIMIT))


def ls(connection, release_id, path="/", sources=None, cursor=None, limit=PAGE_LIMIT):
    """Entries of a folder, by name. Returns `entries` and a `next_cursor` or None."""
    path, limit = folder(path), bound(limit)
    scope, parameters = visible(sources)
    prefix = "/" if path == "/" else path + "/"
    rows = connection.execute(
        text(
            f"""
            SELECT name, bool_or(is_folder) AS is_folder, max(entry_count) AS entry_count,
                   min(title) AS title
            FROM (
                SELECT split_part(substr(path, :start), '/', 1) AS name,
                       position('/' IN substr(path, :start)) > 0 AS is_folder,
                       1 AS entry_count, title
                FROM serving.okf_page
                WHERE release_id = :release AND path LIKE :pattern {scope}
                UNION ALL
                SELECT substr(target, :start), true, entry_count, NULL
                FROM serving.okf_index
                WHERE release_id = :release AND parent = :parent AND is_folder {scope}
                UNION ALL
                SELECT 'index.md', false, count(*)::int, NULL
                FROM serving.okf_index
                WHERE release_id = :release AND parent = :parent {scope}
                HAVING count(*) > 0
            ) AS entries
            WHERE name > :cursor
            GROUP BY name ORDER BY name LIMIT :limit
            """
        ),
        {
            "release": release_id,
            "start": len(prefix) + 1,
            "pattern": escape(prefix) + "%",
            "parent": path,
            "cursor": cursor or "",
            "limit": limit + 1,
            **parameters,
        },
    ).all()
    entries = [
        {
            "name": row.name + ("/" if row.is_folder else ""),
            "path": prefix + row.name,
            "kind": "folder" if row.is_folder else "page",
            **({"title": row.title} if row.title and not row.is_folder else {}),
            **({"entries": row.entry_count} if row.is_folder else {}),
        }
        for row in rows[:limit]
    ]
    return {
        "path": path,
        "entries": entries,
        "next_cursor": rows[limit - 1].name if len(rows) > limit else None,
    }


def escape(value):
    """A literal for LIKE."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def one(connection, sql, **parameters):
    row = connection.execute(text(sql), parameters).mappings().first()
    if row is None:
        raise KeyError("The page's record is not in this release")
    return row


def render_page(connection, release, page, cache=None):
    """The text of one stored page, from the serving read models alone.

    `cache` is a dict a caller may share between pages of one release.
    """
    at, release_id = release["released_at"], release["release_id"]
    if page.type == "Business Profile":
        profile = one(
            connection,
            "SELECT document FROM serving.profile "
            "WHERE release_id = :release AND entity_id = :entity",
            release=release_id,
            entity=page.entity_id,
        )["document"]
        # A cited ID is a claim when the release has an evidence page for it.
        cited = [render.evidence_path(key) for key in render.cited_ids(profile)]
        claims = connection.execute(
            text(
                "SELECT sha256_hex(observation_id), concept_name FROM serving.okf_page "
                "WHERE release_id = :release AND path = ANY(:paths) ORDER BY 1"
            ),
            {"release": release_id, "paths": cited},
        ).all()
        return render.render_entity(profile, [tuple(c) for c in claims], at)
    if page.type == "Field Observation":
        observation = one(
            connection,
            "SELECT document FROM serving.observation WHERE release_id = :release "
            "AND source_id = :source AND observation_key = sha256_from_hex(:observation)",
            release=release_id,
            source=page.observation_source_id,
            observation=page.observation_id,
        )["document"]
        return render.render_evidence(observation, at)
    if page.type == "Public Data Source":
        source = one(
            connection,
            "SELECT * FROM serving.source WHERE release_id = :release AND source_id = :source",
            release=release_id,
            source=page.source_id,
        )
        return render.render_source(source_record(source), at)
    concept = one(
        connection,
        "SELECT * FROM serving.concept WHERE release_id = :release AND name = :name",
        release=release_id,
        name=page.concept_name,
    )
    return render.render_concept(concept_record(concept), release["ontology_hash"], at)


def source_record(row):
    """What a source page needs, in the shape the renderer takes."""
    metadata = {"title": row["title"], "license_title": row["licence_title"]}
    if row["publisher"] is not None:
        metadata["organization"] = {"title": row["publisher"]}
    return {"id": row["source_id"], "portal": row["portal"], "metadata": metadata}


def concept_record(row):
    return {
        "name": row["name"],
        "definition": row["definition"],
        "type": row["datatype"],
        "scope": row["scope"],
        "cardinality": row["cardinality"],
        "values": list(row["allowed_values"]),
        "requires": list(row["requires"]),
        "minimum": row["minimum"],
        "maximum": row["maximum"],
    }


def release_record(connection, release_id=None):
    """A release as the serving layer shows it; the latest when no ID is given."""
    row = (
        connection.execute(
            text(
                "SELECT release_id, batch_id, ontology_hash, released_by, released_at, notes "
                "FROM serving.release WHERE CAST(:release AS bigint) IS NULL "
                "OR release_id = :release ORDER BY release_id DESC LIMIT 1"
            ),
            {"release": release_id},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise KeyError(
            "No release has been created"
            if release_id is None
            else f"releases/{release_id} not found"
        )
    return {**row, "released_at": render_time(row["released_at"])}


def page_text(connection, release, path, sources=None, cache=None):
    scope, parameters = visible(sources)
    release_id = release["release_id"]
    if path == render.ROOT_INDEX or path.endswith("/index.md"):
        parent = "/" if path == render.ROOT_INDEX else path[: -len("/index.md")]
        rows = connection.execute(
            text(
                "SELECT parent, position, label, target, is_folder, entry_count, "
                "description, source_id FROM serving.okf_index "
                f"WHERE release_id = :release AND parent = :parent {scope} ORDER BY position"
            ),
            {"release": release_id, "parent": parent, **parameters},
        ).all()
        if not rows:
            raise KeyError(f"{path} not found")
        return index.page(parent, [index.Row(*row) for row in rows])
    page = connection.execute(
        text(
            "SELECT type, entity_id, source_id, observation_source_id, "
            "sha256_hex(observation_id) AS observation_id, concept_name "
            f"FROM serving.okf_page WHERE release_id = :release AND path = :path {scope}"
        ),
        {"release": release_id, "path": path, **parameters},
    ).first()
    if page is None:
        raise KeyError(f"{path} not found")
    return render_page(connection, release, page, cache)


def read(connection, release_id, path, sources=None, offset=0, limit=None):
    """One page as text, or some of its lines.

    `offset` is the first line to return, counted from 0, and `limit` the number
    of lines. `next_offset` is None when the page has been read to its end.
    """
    release = release_record(connection, release_id)
    body = page_text(connection, release, folder(path), sources)
    lines = body.splitlines(keepends=True)
    end = len(lines) if limit is None else min(len(lines), offset + bound(limit))
    return {
        "path": folder(path),
        "text": body
        if offset == 0 and end == len(lines)
        else "".join(lines[offset:end]),
        "total_lines": len(lines),
        "offset": offset,
        "next_offset": end if end < len(lines) else None,
    }


FIND = (
    "SELECT path, type, title, description, tags, status, entity_id, source_id "
    "FROM serving.okf_page WHERE release_id = :release AND path LIKE :pattern "
    "AND path > :cursor "
    "AND (CAST(:type AS text) IS NULL OR type = :type) "
    "AND (CAST(:status AS text) IS NULL OR status = :status) "
    "AND (CAST(:tags AS text[]) IS NULL OR tags @> :tags) {scope} "
    "ORDER BY path LIMIT :limit"
)
GREP = (
    "SELECT path, line_no, line FROM serving.okf_line "
    "WHERE release_id = :release AND path LIKE :pattern AND line ~ :expression "
    "AND (path, line_no) > (:after_path, :after_line) {scope} "
    "ORDER BY path, line_no LIMIT :limit"
)


def find(
    connection,
    release_id,
    path="/",
    type=None,
    tags=None,
    status=None,
    sources=None,
    cursor=None,
    limit=100,
):
    """Pages under a folder that match the given type, tags and status."""
    path, limit = folder(path), bound(limit)
    scope, parameters = visible(sources)
    rows = connection.execute(
        text(FIND.format(scope=scope)),
        {
            "release": release_id,
            "pattern": escape("/" if path == "/" else path + "/") + "%",
            "cursor": cursor or "",
            "type": type,
            "status": status,
            "tags": list(tags) if tags else None,
            "limit": limit + 1,
            **parameters,
        },
    ).all()
    return {
        "pages": [dict(row._mapping) for row in rows[:limit]],
        "next_cursor": rows[limit - 1].path if len(rows) > limit else None,
    }


def grep(connection, release_id, pattern, path, sources=None, cursor=None, limit=100):
    """Lines under a folder that match a regular expression.

    A folder below the root is required, so a search never covers a whole
    release. Searched lines are each page's frontmatter and its claims, written
    `concept: value`. `cursor` is the `next_cursor` of the previous call.
    """
    path, limit = folder(path), bound(limit)
    if path == "/":
        raise ValueError("grep needs a folder, such as /entities or /evidence")
    re.compile(pattern)
    scope, parameters = visible(sources)
    after_path, _, after_line = (cursor or ":0").rpartition(":")
    rows = connection.execute(
        text(GREP.format(scope=scope)),
        {
            "release": release_id,
            "pattern": escape(path + "/") + "%",
            "expression": pattern,
            "after_path": after_path,
            "after_line": int(after_line),
            "limit": limit + 1,
            **parameters,
        },
    ).all()
    matches = [dict(row._mapping) for row in rows[:limit]]
    last = rows[limit - 1] if len(rows) > limit else None
    return {
        "matches": matches,
        "next_cursor": f"{last.path}:{last.line_no}" if last else None,
    }
