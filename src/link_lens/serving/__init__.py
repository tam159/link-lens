"""Serving read models: one SQL file per model, each a single SELECT.

The files are the definition. `apply` creates a view in the `serving` schema
for each, named after the file, and records the file's digest on the view so an
unchanged view is left alone. It runs after every `alembic upgrade`.
"""

import hashlib
from importlib import resources

from sqlalchemy import text

MODELS = (
    "release",
    "current_release",
    "entity",
    "profile",
    "profile_field",
    "profile_address",
    "observation",
    "evidence",
    "link",
    "source",
    "concept",
    "bundle",
)


def sql(name):
    """The SELECT that defines a read model."""
    return resources.files(__package__).joinpath(name + ".sql").read_text()


def apply(connection):
    """Create or refresh the serving views. Returns the names that changed."""
    if connection.execute(text("SELECT to_regclass('ops.release')")).scalar() is None:
        return []
    connection.execute(text("SET LOCAL ROLE linklens_migrator"))
    applied = dict(
        connection.execute(
            text(
                "SELECT c.relname, obj_description(c.oid) FROM pg_class c "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'serving' AND c.relkind = 'v'"
            )
        ).all()
    )
    changed = []
    for name in MODELS:
        body = sql(name)
        mark = "sha256:" + hashlib.sha256(body.encode()).hexdigest()
        if applied.get(name) == mark:
            continue
        connection.execute(text(f"DROP VIEW IF EXISTS serving.{name}"))
        connection.execute(text(f"CREATE VIEW serving.{name} AS\n{body}"))
        connection.execute(text(f"COMMENT ON VIEW serving.{name} IS '{mark}'"))
        changed.append(name)
    for name in applied.keys() - set(MODELS):
        connection.execute(text(f"DROP VIEW serving.{name}"))
        changed.append(name)
    connection.execute(text("RESET ROLE"))
    return changed


def compare(connection, candidate="serving_next", reference="serving"):
    """Compare the views of two schemas, release by release.

    For every view: the columns with their types, and per release the number of
    rows and a digest over every row, document columns included. Returns the
    figures and a list of differences, which is empty when a build into
    `candidate` would answer exactly as `reference` does. Reads only.
    """
    for schema in (candidate, reference):
        if not schema.replace("_", "").isalnum():
            raise ValueError(f"Not a schema name: {schema}")

    def views(schema):
        return set(
            connection.execute(
                text("SELECT viewname FROM pg_views WHERE schemaname = :schema"),
                {"schema": schema},
            ).scalars()
        )

    def columns(schema, name):
        return [
            tuple(row)
            for row in connection.execute(
                text(
                    "SELECT a.attname, format_type(a.atttypid, a.atttypmod) "
                    "FROM pg_attribute a WHERE a.attrelid = to_regclass(:view) "
                    "AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum"
                ),
                {"view": f"{schema}.{name}"},
            )
        ]

    def rows(schema, name):
        # A digest per release that does not depend on the order rows come in.
        return {
            row.release_id: (row.rows, row.digest)
            for row in connection.execute(
                text(
                    "SELECT release_id, count(*) AS rows, "
                    "md5(string_agg(hash, '' ORDER BY hash)) AS digest "
                    f'FROM (SELECT release_id, md5(v::text) AS hash FROM {schema}."{name}" v) hashed '
                    "GROUP BY release_id"
                )
            )
        }

    ours, theirs = views(candidate), views(reference)
    differences = [
        f"{name}: only in {reference if name in theirs else candidate}"
        for name in sorted(ours ^ theirs)
    ]
    result = {}
    for name in sorted(ours & theirs):
        same_columns = columns(candidate, name) == columns(reference, name)
        if not same_columns:
            differences.append(f"{name}: columns or types differ")
        left, right = rows(candidate, name), rows(reference, name)
        releases = {}
        for release in sorted(left.keys() | right.keys()):
            a, b = left.get(release), right.get(release)
            releases[release] = {
                "rows": {candidate: a and a[0], reference: b and b[0]},
                "equal": a == b,
            }
            if a != b:
                differences.append(f"{name}: release {release} differs")
        result[name] = {"columns_equal": same_columns, "releases": releases}
    return {
        "candidate": candidate,
        "reference": reference,
        "views": result,
        "differences": differences,
    }
