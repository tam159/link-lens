"""Release bundles: a release's OKF files as one archive, for a demo or a client.

A bundle is built through the same renderer as the tree, so a page in a bundle
holds the bytes `okf_read` returns for its path. Each bundle is checked for
broken links, gets the vendored viewer, and is stored as an artifact with a
manifest that lists every file and its hash.

Scopes: a named scope such as `demo` is a bounded list of entities a person
chose; `client:<id>` is everything the client's tier may see. A named scope is
built when a release is created; a client's bundle is built on request.

Every step takes its IDs as parameters and writes nothing new when repeated.
"""

import gzip
import hashlib
import io
import json
import logging
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from . import exports, logs, store
from ._vendor.okf.viewer.generator import generate_visualization
from .db import serving
from .okf import bundle as tree_files
from .okf import index, render, tree

LIMIT = 500  # entities in a named scope; the table enforces the same bound
VIEWER = "viewer.html"
MANIFEST = "manifest.json"
TITLE = "Link Lens: evidence dossiers"


def scope_record(row):
    return {**row._mapping, "set_at": row.set_at.isoformat()}


def set_scope(name, entity_ids, reviewer, on_release=True):
    """Name a bounded list of entities. A human action; replaces the list."""
    entity_ids = sorted(set(entity_ids))
    if not reviewer or not reviewer.strip():
        raise ValueError("A scope needs the name of the person setting it")
    if not 1 <= len(entity_ids) <= LIMIT:
        raise ValueError(f"A scope holds between 1 and {LIMIT} entities")
    table = serving.bundle_scope
    values = {
        "entity_ids": entity_ids,
        "on_release": on_release,
        "set_by": reviewer.strip(),
        "set_at": datetime.now(UTC),
    }
    with store.engine().begin() as connection:
        row = connection.execute(
            insert(table)
            .values(name=name, **values)
            .on_conflict_do_update(index_elements=["name"], set_=values)
            .returning(table)
        ).one()
    logs.event("bundle.scope_set", scope=name, entities=len(entity_ids))
    return scope_record(row)


def scopes():
    with store.engine().connect() as connection:
        rows = connection.execute(
            select(serving.bundle_scope).order_by(serving.bundle_scope.c.name)
        )
        return [scope_record(row) for row in rows]


def subset(connection, release, entity_ids, sources=None, ontology=True):
    """Pages of some entities with their evidence, sources and a matching index.

    Returns `path: text` and the entities found. An entity that is not in the
    release is left out. Entity, evidence, source and concept pages are the
    tree's own; index pages list only what the subset holds.
    """
    files, summaries, cited, cache = {}, [], set(), {}

    def page(path):
        try:
            files[path] = tree.page_text(connection, release, path, sources, cache)
        except KeyError:
            return False  # not in this release, or from a source out of scope
        return True

    for entity_id in entity_ids:
        profile = connection.execute(
            text(
                "SELECT document FROM serving.profile "
                "WHERE release_id = :release AND entity_id = :entity"
            ),
            {"release": release["release_id"], "entity": entity_id},
        ).scalar_one_or_none()
        if profile is None or not page(render.entity_path(entity_id)):
            continue
        summaries.append(index.summary(profile))
        cited.update(record[0] for record in profile["source_records"])
        for observation_id in render.cited_ids(profile):
            page(render.evidence_path(observation_id))
    titles = dict(
        connection.execute(
            text(
                "SELECT source_id, coalesce(title, source_id) FROM serving.source "
                "WHERE release_id = :release AND source_id = ANY (CAST(:ids AS text[]))"
            ),
            {"release": release["release_id"], "ids": sorted(cited)},
        ).all()
    )
    shown = [(i, titles[i]) for i in sorted(titles) if page(render.source_path(i))]
    for summary in summaries:
        summary["sources"] = [s for s in summary["sources"] if s in dict(shown)]
    concepts = []
    if ontology:
        rows = connection.execute(
            text(
                "SELECT scope, name, definition FROM serving.concept "
                "WHERE release_id = :release ORDER BY position"
            ),
            {"release": release["release_id"]},
        ).all()
        concepts = [tuple(row) for row in rows if page(render.concept_path(*row[:2]))]
    files.update(index.pages(index.build(summaries, shown, concepts)))
    return files, [summary["id"] for summary in summaries]


def viewer(root, name=TITLE):
    """The vendored viewer for a folder, as HTML."""
    with tempfile.TemporaryDirectory() as out:
        target = Path(out) / VIEWER
        generate_visualization(Path(root), target, bundle_name=name)
        return target.read_text()


def entity_viewer(connection, release, entity_id, sources=None):
    """A viewer of one entity, its evidence and its sources, or None if unknown."""
    files, found = subset(connection, release, [entity_id], sources, ontology=False)
    if not found:
        return None
    with tempfile.TemporaryDirectory() as root:
        tree_files.put(root, files)
        return viewer(root, f"Link Lens: {entity_id}")


def manifest(root, release, scope, sources, entities):
    """What a bundle holds: every file with its hash, in path order."""
    root = Path(root)
    files = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size": path.stat().st_size,
        }
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != MANIFEST
    ]
    return {
        "format": 1,
        "release_id": release["release_id"],
        "released_at": release["released_at"],
        "batch_id": release["batch_id"],
        "ontology_hash": release["ontology_hash"],
        "scope": scope,
        "source_scope": None if sources is None else sorted(sources),
        "entities": entities,
        "files": files,
    }


def archive(root, stamp):
    """A gzip tar of a folder that is the same bytes whenever it is made."""
    root, buffer = Path(root), io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as tar:
            for path in sorted(p for p in root.rglob("*") if p.is_file()):
                info = tarfile.TarInfo(path.relative_to(root).as_posix())
                info.size, info.mtime, info.mode = path.stat().st_size, stamp, 0o644
                with path.open("rb") as file:
                    tar.addfile(info, file)
    return buffer.getvalue()


def selection(connection, scope):
    """Who a scope is for: its entities, or the client and the sources it may see."""
    if scope.startswith("client:"):
        row = connection.execute(
            text(
                "SELECT client.id, tier.source_scope FROM access.client AS client "
                "JOIN access.tier AS tier ON tier.id = client.tier_id "
                "WHERE client.id = CAST(:client AS uuid)"
            ),
            {"client": scope.removeprefix("client:")},
        ).first()
        if row is None:
            raise KeyError(f"{scope} not found")
        return {"client_id": str(row.id), "sources": row.source_scope, "entities": None}
    table = serving.bundle_scope
    row = connection.execute(select(table).where(table.c.name == scope)).first()
    if row is None:
        raise KeyError(f"Bundle scope {scope} not found")
    return {"client_id": None, "sources": None, "entities": row.entity_ids}


def record(row, created):
    return {
        **{k: v for k, v in row._mapping.items() if k != "created_at"},
        "created_at": row.created_at.isoformat(),
        "created": created,
    }


def build(release_id, scope):
    """Build the bundle of a release for a scope and store it. Returns its record.

    Building the same release and scope again produces the same archive and adds
    no row; `created` says whether this call added one.
    """
    table = serving.release_bundle
    with store.engine().connect() as connection, tempfile.TemporaryDirectory() as tmp:
        release = tree.release_record(connection, release_id)
        chosen = selection(connection, scope)
        sources, root = chosen["sources"], Path(tmp)
        if chosen["entities"] is None:
            written = tree_files.write_tree(connection, release, root, sources)
            entities = sum(
                path.startswith("/entities/") and not path.endswith("/index.md")
                for path in written
            )
            withheld = set()
            if sources is not None:
                everything = tree_files.paths(connection, release)
                withheld = {p.lstrip("/") for p in set(everything) - set(written)}
        else:
            files, found = subset(connection, release, chosen["entities"])
            tree_files.put(root, files)
            entities, withheld = len(found), set()
        checked = exports.check_bundle(root, frozenset(withheld))
        (root / VIEWER).write_text(viewer(root))
        listed = manifest(root, release, scope, sources, entities)
        described = json.dumps(listed, indent=1, sort_keys=True).encode() + b"\n"
        (root / MANIFEST).write_bytes(described)
        stamp = int(datetime.fromisoformat(release["released_at"]).timestamp())
        data = archive(root, stamp)
    artifact = store.blob(
        data, "application/gzip", f"release-{release['release_id']}-{scope}.tar.gz"
    )
    values = {
        "release_id": release["release_id"],
        "scope": scope,
        "client_id": chosen["client_id"],
        "source_scope": None if sources is None else sorted(sources),
        "entity_count": entities,
        "file_count": len(listed["files"]) + 1,
        "size_bytes": len(data),
        "artifact_sha": artifact,
        "manifest_sha": hashlib.sha256(described).hexdigest(),
    }
    with store.engine().begin() as connection:
        row = connection.execute(
            insert(table)
            .values(**values)
            .on_conflict_do_nothing(
                index_elements=["release_id", "scope", "manifest_sha"]
            )
            .returning(table)
        ).first()
        created = row is not None
        if row is None:
            row = connection.execute(
                select(table).where(
                    table.c.release_id == values["release_id"],
                    table.c.scope == scope,
                    table.c.manifest_sha == values["manifest_sha"],
                )
            ).one()
    result = {
        **record(row, created),
        "withheld_links": checked.get("withheld_links", 0),
    }
    logs.event(
        "bundle.built", **{k: v for k, v in result.items() if k != "source_scope"}
    )
    return result


def on_release(release_id):
    """Build the bundle of every scope marked to follow a release.

    The release already exists; a bundle that fails is reported, not raised,
    and can be built again with `link-lens release bundle`.
    """
    built = []
    for scope in scopes():
        if not scope["on_release"]:
            continue
        try:
            built.append(build(release_id, scope["name"]))
        except Exception as error:  # the release stands whatever a bundle does
            logs.event(
                "bundle.failed",
                logging.ERROR,
                scope=scope["name"],
                **logs.error_fields(error),
            )
            built.append({"scope": scope["name"], "error": str(error)})
    return built


def listing(release_id=None):
    """Bundles built so far, newest first."""
    table = serving.release_bundle
    statement = select(table).order_by(table.c.id.desc())
    if release_id is not None:
        statement = statement.where(table.c.release_id == release_id)
    with store.engine().connect() as connection:
        return [record(row, False) for row in connection.execute(statement)]
