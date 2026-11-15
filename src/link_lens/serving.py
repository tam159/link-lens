"""Serving read models: the views clients are answered from.

Each read model is a dbt model in `transform/models/serving`, one SELECT with an
enforced contract, built as a view owned by `linklens_transform`. Alembic owns
nothing here but the schema, the three `okf_*` tables and their functions.

A changed model is built into `serving_next` first and compared with what
`serving` holds, release by release, before it is built where clients read it.
"""

from sqlalchemy import text


def built(connection, schema="serving"):
    """Names of the views that exist in a schema."""
    return sorted(
        connection.execute(
            text("SELECT viewname FROM pg_views WHERE schemaname = :schema"),
            {"schema": schema},
        ).scalars()
    )


def require(connection):
    """Fail with what to do when the serving views have not been built."""
    if "profile" not in built(connection):
        raise ValueError(
            "The serving views are not built. Run `link-lens dbt build` on this "
            "database: alembic creates the tables, dbt the views."
        )


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
