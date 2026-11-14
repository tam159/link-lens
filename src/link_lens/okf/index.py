"""Index folders for an OKF tree. No index page lists more than `LIMIT` entries.

A listing that is too long is split one level deeper by the next character of
each entry's sort key, as often as needed: `by-name` becomes `by-name/k`, then
`by-name/k/ki`. Every index page therefore links only to its own entries or to
the folders directly below it.
"""

import os
import re
from collections import namedtuple

from . import render

LIMIT = 200
Row = namedtuple(
    "Row", "parent position label target is_folder entry_count description source_id"
)
Entry = namedtuple("Entry", "key label target description source_id")
ENTITY = "profile with claim-level evidence and alternatives."


def slug(text):
    """A folder-safe, lower-case form of a name; never empty."""
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-") or "-"


def split(parent, entries, depth=0):
    """Rows for `parent`, splitting into sub-folders while it has too many entries."""
    entries = sorted(entries, key=lambda e: (e.key, e.label, e.target))
    if len(entries) <= LIMIT:
        return [
            Row(
                parent,
                position,
                e.label,
                e.target,
                False,
                1,
                e.description,
                e.source_id,
            )
            for position, e in enumerate(entries)
        ]
    keys = [entry.key for entry in entries]
    numbered = keys[0] == keys[-1]
    if numbered:
        # Every key is the same, so no further character tells them apart.
        groups = {
            str(number + 1): entries[start : start + LIMIT]
            for number, start in enumerate(range(0, len(entries), LIMIT))
        }
    else:
        # Split at the first character where the keys differ, skipping what
        # they all share, so no folder holds a single sub-folder.
        shared = len(os.path.commonprefix([keys[0], keys[-1]]))
        depth = max(depth, shared)
        groups = {}
        for entry in entries:
            groups.setdefault(entry.key[: depth + 1], []).append(entry)
    rows = []
    for position, (prefix, members) in enumerate(sorted(groups.items())):
        child = f"{parent}/{prefix}"
        rows.append(
            Row(
                parent,
                position,
                prefix,
                child,
                True,
                len(members),
                f"{len(members)} entries.",
                None,
            )
        )
        if numbered:
            rows += [
                Row(child, n, e.label, e.target, False, 1, e.description, e.source_id)
                for n, e in enumerate(members)
            ]
        else:
            rows += split(child, members, depth + 1)
    return rows


def folder(parent, position, name, count, description, source_id=None):
    return Row(
        parent,
        position,
        name,
        f"{parent.rstrip('/')}/{name}",
        True,
        count,
        description,
        source_id,
    )


def facet(parent, values, describe):
    """A folder per facet value, each split by name. `values` maps value to entries."""
    rows = []
    merged = {}
    for value, entries in values.items():
        merged.setdefault(slug(value), (value, []))[1].extend(entries)
    for position, (name, (value, entries)) in enumerate(sorted(merged.items())):
        source = entries[0].source_id if describe == "source" else None
        rows.append(
            folder(
                parent,
                position,
                name,
                len(entries),
                f"{value}: {len(entries)} entities.",
                source,
            )
        )
        rows += split(f"{parent}/{name}", entries)
    return rows


def build(entities, sources, concepts):
    """All index rows of a tree.

    `entities` are dicts with `id`, `name`, `states`, `types` and `sources`;
    `sources` are `(source_id, title)`; `concepts` are `(scope, name, definition)`.
    """
    by_name, by_state, by_type, by_source = [], {}, {}, {}
    for entity in entities:
        target = render.entity_path(entity["id"])
        entry = Entry(slug(entity["name"]), entity["name"], target, ENTITY, None)
        by_name.append(entry)
        for state in entity["states"]:
            by_state.setdefault(state, []).append(entry)
        for kind in entity["types"]:
            by_type.setdefault(kind, []).append(entry)
        for source in entity["sources"]:
            by_source.setdefault(source, []).append(entry._replace(source_id=source))
    scopes = {}
    for scope, name, definition in concepts:
        scopes.setdefault(scope, []).append(
            Entry(name, name, render.concept_path(scope, name), definition, None)
        )
    total = len(by_name)
    facets = [
        ("by-state", "entities by address state.", by_state, "state"),
        ("by-type", "entities by entity type.", by_type, "type"),
        ("by-source", "entities by contributing source.", by_source, "source"),
    ]
    # A folder is listed only when it has something in it, so no link is dead.
    top = [
        ("entities", total, "generated profiles and evidence."),
        ("sources", len(sources), "publisher metadata."),
        ("ontology", len(concepts), "concepts a claim can be about."),
    ]
    rows = [
        folder("/", position, name, count, description)
        for position, (name, count, description) in enumerate(t for t in top if t[1])
    ]
    if total:
        inside = [("by-name", "entities by name.")] + [
            (name, description) for name, description, values, _ in facets if values
        ]
        rows += [
            folder("/entities", position, name, total, description)
            for position, (name, description) in enumerate(inside)
        ]
        rows += split("/entities/by-name", by_name)
        for name, _, values, describe in facets:
            rows += facet(f"/entities/{name}", values, describe)
    rows += split(
        "/sources",
        [
            Entry(
                slug(title),
                title,
                render.source_path(source_id),
                "publisher metadata and licence.",
                source_id,
            )
            for source_id, title in sources
        ],
    )
    for position, (scope, members) in enumerate(sorted(scopes.items())):
        rows.append(
            folder(
                "/ontology", position, scope, len(members), f"{len(members)} concepts."
            )
        )
        rows += split(f"/ontology/{scope}", members)
    return rows


FACETS = {"states": "address.state", "types": "entity.entity_type"}


def field_values(profile, concept):
    """Values a profile states for a concept, in its fields and its addresses."""
    holders = [profile.get("fields") or {}]
    holders += [a.get("fields") or {} for a in profile.get("addresses") or []]
    values = []
    for fields in holders:
        field = fields.get(concept) or {}
        found = field.get("values") if "values" in field else [field.get("value")]
        values += [v for v in found or [] if isinstance(v, str) and v]
    return sorted(set(values))


def summary(profile):
    """What the index needs to know about one profile."""
    return {
        "id": profile["canonical_entity_key"],
        "name": render.profile_title(profile),
        "sources": sorted({r[0] for r in profile["source_records"]}),
        **{name: field_values(profile, concept) for name, concept in FACETS.items()},
    }


def pages(rows):
    """Index pages by path, from the rows of a whole tree."""
    folders = {}
    for row in rows:
        folders.setdefault(row.parent, []).append(row)
    return {
        render.index_path(parent): page(parent, group)
        for parent, group in folders.items()
    }


TITLES = {
    "/": "Link Lens",
    "/entities": "Entities",
    "/sources": "Sources",
    "/ontology": "Ontology",
}


def title(folder_path):
    return TITLES.get(folder_path) or folder_path.rsplit("/", 1)[-1]


def page(folder_path, rows):
    """The index page of one folder, from its rows."""
    entries = [
        (
            row.label,
            render.index_path(row.target) if row.is_folder else row.target,
            row.description,
        )
        for row in rows
    ]
    text = render.render_index(folder_path, title(folder_path), entries)
    if folder_path == "/":
        text += (
            "\nThe document graph represents evidence links; it is not proof of "
            "business identity.\n"
        )
    return text
