"""Catalog: artifacts, sources and snapshots.

`source` and `snapshot` keep the store's record exactly: typed columns hold the
fields that are present and well formed, and `extra` holds every other key. A
reference column is filled only when the row it points at exists, so a foreign
key never dangles. `owner_id` and `kind` are the store's listing filters.
Snapshots and artifacts are append-only.
"""

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

DDL = [
    """
    CREATE TABLE catalog.artifact (
        sha256     sha256 PRIMARY KEY,
        uri        text NOT NULL,
        media_type text NOT NULL,
        size       bigint NOT NULL CHECK (size >= 0),
        name       text NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE catalog.source (
        id         text PRIMARY KEY,
        owner_id   text NOT NULL DEFAULT '',
        kind       text NOT NULL DEFAULT '',
        portal     text,
        slug       text,
        metadata   jsonb,
        title      text GENERATED ALWAYS AS (metadata ->> 'title') STORED,
        publisher  text GENERATED ALWAYS AS (metadata -> 'organization' ->> 'title') STORED,
        extra      jsonb NOT NULL DEFAULT '{}',
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX ON catalog.source (kind)",
    """
    CREATE TABLE catalog.snapshot (
        id                text PRIMARY KEY,
        owner_id          text NOT NULL DEFAULT '',
        kind              text NOT NULL DEFAULT '',
        source_id         text REFERENCES catalog.source,
        resource_id       text,
        artifact_sha      sha256 REFERENCES catalog.artifact,
        format            text,
        licence           text,
        licence_url       text,
        observed_at       timestamptz,
        observed_at_basis text,
        retrieved_at      timestamptz,
        documentation     jsonb,
        dataset_notes     text,
        receipt           jsonb,
        inspection        jsonb,
        extra             jsonb NOT NULL DEFAULT '{}',
        created_at        timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX ON catalog.snapshot (source_id)",
]


def upgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    for statement in DDL:
        op.execute(statement)
    for table in ("artifact", "snapshot"):
        op.execute(
            f"CREATE TRIGGER forbid_update BEFORE UPDATE ON catalog.{table} "
            "FOR EACH ROW EXECUTE FUNCTION public.forbid_update()"
        )


def downgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    for table in ("snapshot", "source", "artifact"):
        op.execute(f"DROP TABLE catalog.{table}")
