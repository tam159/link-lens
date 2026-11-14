"""The OKF tree of a release as a virtual file system: ls, read, find, grep.

Nothing is stored as files. Folders and search come from the tables built when
the release was created; a page is rendered when it is read. Every function
takes the release and, optionally, the sources a caller may see. A page that
belongs to one source (a source page, an evidence page) is hidden from a caller
whose scope does not include that source.
"""

import re

from sqlalchemy import text

from .. import releases
from ..db import catalog, evidence, identity
from ..db import ontology as registry
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


def render_page(connection, release, page):
    """The text of one stored page."""
    at = release["released_at"]
    if page.type == "Business Profile":
        profile = identity.profile
        rows = (
            connection.execute(
                profile.select().where(
                    profile.c.batch_id == release["batch_id"],
                    profile.c.entity_key == page.entity_id,
                )
            )
            .mappings()
            .all()
        )
        payload = identity.profiles.load(connection, rows)[0]
        cited = [key for key in render.cited_ids(payload) if len(key) == 64]
        observation, concept = evidence.observation, registry.concept
        claims = connection.execute(
            observation.select()
            .with_only_columns(observation.c.id, concept.c.name)
            .join(concept, concept.c.id == observation.c.concept_id)
            .where(evidence.among(observation.c.id, cited))
            .order_by(observation.c.id)
        ).all()
        return render.render_entity(payload, [tuple(c) for c in claims], at)
    if page.type == "Field Observation":
        found = list(evidence.observations(connection, [page.observation_id]))
        return render.render_evidence(found[0], at)
    if page.type == "Public Data Source":
        return render.render_source(catalog.sources.get(connection, page.source_id), at)
    document = registry.document(connection, release["ontology_hash"])
    return render.render_concept(
        document["concepts"][page.concept_name], release["ontology_hash"], at
    )


def page_text(connection, release, path, sources=None):
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
            "SELECT type, entity_id, source_id, sha256_hex(observation_id) AS observation_id, "
            f"concept_name FROM serving.okf_page WHERE release_id = :release AND path = :path {scope}"
        ),
        {"release": release_id, "path": path, **parameters},
    ).first()
    if page is None:
        raise KeyError(f"{path} not found")
    return render_page(connection, release, page)


def read(connection, release_id, path, sources=None, offset=0, limit=None):
    """One page as text, or some of its lines.

    `offset` is the first line to return, counted from 0, and `limit` the number
    of lines. `next_offset` is None when the page has been read to its end.
    """
    release = releases.get(connection, release_id)
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
        text(
            "SELECT path, type, title, description, tags, status, entity_id, source_id "
            "FROM serving.okf_page WHERE release_id = :release AND path LIKE :pattern "
            "AND path > :cursor "
            "AND (CAST(:type AS text) IS NULL OR type = :type) "
            "AND (CAST(:status AS text) IS NULL OR status = :status) "
            f"AND (CAST(:tags AS text[]) IS NULL OR tags @> :tags) {scope} "
            "ORDER BY path LIMIT :limit"
        ),
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
        text(
            "SELECT path, line_no, line FROM serving.okf_line "
            "WHERE release_id = :release AND path LIKE :pattern AND line ~ :expression "
            f"AND (path, line_no) > (:after_path, :after_line) {scope} "
            "ORDER BY path, line_no LIMIT :limit"
        ),
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
