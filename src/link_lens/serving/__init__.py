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
