"""Pure functions that turn records into OKF pages. No store, no clock.

The same functions serve a single page on request, the virtual file tree and a
bundle written to disk, so the three can never disagree. `generated_at` is
passed in; a release uses its own time, which makes every page reproducible.
"""

import html
import json
import posixpath

import yaml

EXPORTER = "process:link-lens-exporter-1"
ROOT_INDEX = "/index.md"
# Keys a reader wants first; any other key follows in alphabetical order.
FIRST_KEYS = (
    "canonical_entity_key",
    "id",
    "name",
    "field",
    "role",
    "scope",
    "value",
    "values",
    "status",
    "decision",
    "confidence",
    "provenance",
    "alternatives",
    "fields",
)
RANK = {key: number for number, key in enumerate(FIRST_KEYS)}


def ordered(value):
    """The same value with object keys in a fixed, readable order."""
    if isinstance(value, dict):
        keys = sorted(value, key=lambda key: (RANK.get(key, len(RANK)), key))
        return {key: ordered(value[key]) for key in keys}
    if isinstance(value, list):
        return [ordered(item) for item in value]
    return value


def dump(value):
    return json.dumps(ordered(value), indent=2, ensure_ascii=False)


def entity_path(entity_id):
    return f"/entities/{entity_id[:2]}/{entity_id}.md"


def evidence_path(observation_id):
    return f"/evidence/{observation_id[:2]}/{observation_id}.md"


def source_path(source_id):
    return f"/sources/{source_id}.md"


def concept_path(scope, name):
    return f"/ontology/{scope}/{name}.md"


def index_path(folder):
    return ROOT_INDEX if folder == "/" else folder + "/index.md"


def link(page, target):
    """A relative link from one page to another page or folder index."""
    return posixpath.relpath(target, posixpath.dirname(page))


def document(frontmatter, body):
    return (
        "---\n"
        + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
        + "---\n\n"
        + body
        + "\n"
    )


def generated(at):
    return {"by": EXPORTER, "at": at}


def profile_title(profile):
    name = profile.get("fields", {}).get("entity.legal_name", {}).get("value")
    return name if isinstance(name, str) and name else profile["canonical_entity_key"]


def cited_ids(value, found=None):
    """Every `id` inside a profile, which is where it cites observations."""
    found = set() if found is None else found
    if isinstance(value, dict):
        if isinstance(value.get("id"), str):
            found.add(value["id"])
        for item in value.values():
            cited_ids(item, found)
    elif isinstance(value, list):
        for item in value:
            cited_ids(item, found)
    return found


def render_entity(profile, claims, generated_at):
    """An entity page. `claims` are `(observation_id, field)` in observation order."""
    page = entity_path(profile["canonical_entity_key"])
    links = [
        f"* [{field}]({link(page, evidence_path(oid))}) - source value and exact raw locator."
        for oid, field in claims
    ]
    # JSON is the exact profile, so no loss of alternatives or confidence dimensions.
    return document(
        {
            "type": "Business Profile",
            "title": profile_title(profile),
            "description": "Versioned profile assembled from proposed identity links.",
            "tags": ["entity", "proposed-identity"],
            "generated": generated(generated_at),
            "status": "draft",
            "profile_version": profile["profile_version"],
            # The ID the data tools and REST take, so a reader can switch style.
            "entity_id": profile["canonical_entity_key"],
            "sources": [
                {"resource": link(page, source_path(source))}
                for source in sorted({r[0] for r in profile["source_records"]})
            ],
        },
        "# Profile\n\nIdentity scores are uncalibrated. Review of a mapping does not "
        "verify every identity link.\n\n```json\n"
        + dump(profile)
        + "\n```\n\n# Evidence\n\n"
        + "\n".join(links),
    )


def render_evidence(observation, generated_at):
    page = evidence_path(observation["id"])
    source = link(page, source_path(observation["source_id"]))
    return document(
        {
            "type": "Field Observation",
            "title": observation["field"] + ": " + str(observation["value"]),
            "description": "A source claim, not independent proof of identity.",
            "generated": generated(generated_at),
            "tags": ["evidence"],
            "observation_id": observation["id"],
            "sources": [{"resource": source}],
        },
        "[Source](" + source + ")\n\n```json\n" + dump(observation) + "\n```",
    )


def render_source(source, generated_at):
    meta = source["metadata"]
    record = source["portal"] + "/dataset/" + source["id"]
    publisher = html.escape((meta.get("organization") or {}).get("title", "unknown"))
    licence = html.escape(meta.get("license_title") or "unknown")
    return document(
        {
            "type": "Public Data Source",
            "title": meta["title"],
            "description": "Publisher, source role and licence.",
            "generated": generated(generated_at),
            "resource": record,
            "tags": ["source"],
        },
        f"# Publisher\n\n{publisher}\n\nLicence: {licence}.\n\n[Catalogue record]({record})",
    )


def render_concept(concept, ontology_hash, generated_at):
    rows = [
        ("Scope", concept["scope"]),
        ("Type", concept["type"]),
        ("Cardinality", concept["cardinality"]),
        ("Minimum", concept["minimum"]),
        ("Maximum", concept["maximum"]),
        ("Requires", ", ".join(concept["requires"])),
    ]
    body = "# Definition\n\n" + html.escape(concept["definition"]) + "\n\n"
    body += "\n".join(f"* {label}: {value}" for label, value in rows if value)
    if concept["values"]:
        body += "\n\n# Allowed values\n\n" + "\n".join(
            "* " + html.escape(value) for value in concept["values"]
        )
    return document(
        {
            "type": "Ontology Concept",
            "title": concept["name"],
            "description": concept["definition"],
            "generated": generated(generated_at),
            "tags": ["ontology", concept["scope"]],
            "ontology_hash": ontology_hash,
        },
        body,
    )


def render_index(folder, title, entries):
    """An index page. `entries` are `(label, target_path, description)`."""
    page = index_path(folder)
    lines = [
        f"* [{html.escape(label)}]({link(page, target)}) - {description}"
        for label, target, description in entries
    ]
    head = '---\nokf_version: "0.2"\n---\n\n' if folder == "/" else ""
    return head + "# " + title + "\n\n" + "\n".join(lines) + "\n"
