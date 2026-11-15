"""Access: tiers, clients, API keys and usage, and what the product role may touch.

A tier is a row, so prices and limits change without code. A key is stored as a
prefix and the SHA-256 of its secret; the secret itself is shown once and never
kept. The product role reads the access tables to authenticate and counts calls
in `api_usage`; it can change nothing else.

Two helper functions let a serving view print a timestamp and a number exactly
as the pipeline wrote them, and four indexes serve entity search and evidence lookup.
"""

from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None

DDL = [
    """
    CREATE TABLE access.tier (
        id               text PRIMARY KEY,
        monthly_quota    bigint CHECK (monthly_quota >= 0),
        rate_per_minute  integer NOT NULL CHECK (rate_per_minute > 0),
        interfaces       text[] NOT NULL,
        toolsets         text[] NOT NULL,
        source_scope     text[],
        bundle_downloads boolean NOT NULL DEFAULT false,
        release_lag      integer NOT NULL DEFAULT 0 CHECK (release_lag >= 0),
        history_depth    integer CHECK (history_depth >= 1),
        CHECK (interfaces <@ ARRAY['rest', 'mcp', 'graphql']),
        CHECK (toolsets <@ ARRAY['data', 'files'])
    )
    """,
    """
    CREATE TABLE access.client (
        id         uuid PRIMARY KEY,
        name       text NOT NULL,
        tier_id    text NOT NULL REFERENCES access.tier,
        status     text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended')),
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE access.api_key (
        id         uuid PRIMARY KEY,
        client_id  uuid NOT NULL REFERENCES access.client,
        prefix     text NOT NULL UNIQUE,
        key_hash   sha256 NOT NULL,
        label      text,
        created_at timestamptz NOT NULL DEFAULT now(),
        expires_at timestamptz,
        revoked_at timestamptz
    )
    """,
    "CREATE INDEX ON access.api_key (client_id)",
    """
    CREATE TABLE access.api_usage (
        key_id    uuid NOT NULL REFERENCES access.api_key,
        day       date NOT NULL,
        interface text NOT NULL,
        calls     bigint NOT NULL DEFAULT 0,
        PRIMARY KEY (key_id, day, interface)
    )
    """,
    "GRANT SELECT ON access.tier, access.client, access.api_key TO linklens_product",
    "GRANT SELECT, INSERT, UPDATE ON access.api_usage TO linklens_product",
    """
    CREATE FUNCTION serving.iso_utc(timestamptz) RETURNS text
    LANGUAGE sql IMMUTABLE PARALLEL SAFE
    RETURN to_char($1 AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS')
        || CASE WHEN extract(microseconds FROM $1)::bigint % 1000000 <> 0
                THEN '.' || to_char($1 AT TIME ZONE 'UTC', 'US') ELSE '' END
        || '+00:00'
    """,
    """
    CREATE FUNCTION serving.json_float(double precision) RETURNS jsonb
    LANGUAGE sql IMMUTABLE PARALLEL SAFE
    RETURN CASE WHEN $1 = trunc($1) AND abs($1) < 1e15
                THEN to_jsonb(round($1::numeric, 1)) ELSE to_jsonb($1) END
    """,
    # An observation is looked up by its ID alone when a client asks for evidence.
    "CREATE INDEX observation_id ON evidence.observation (id)",
    "CREATE INDEX ON identity.profile_field (concept_name, value)",
    "CREATE INDEX profile_field_name_trgm ON identity.profile_field "
    "USING gin (value gin_trgm_ops) WHERE concept_name = 'entity.legal_name'",
    "CREATE INDEX profile_address_state ON identity.profile_address "
    "((detail -> 'fields' -> 'address.state' ->> 'value'))",
]
INDEXES = [
    "evidence.observation_id",
    "identity.profile_address_state",
    "identity.profile_field_name_trgm",
    "identity.profile_field_concept_name_value_idx",
]


def upgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    for statement in DDL:
        op.execute(statement)


def downgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    # Serving views may call the helper functions; they are applied again after
    # the downgrade from their files.
    op.execute(
        """
        DO $do$
        DECLARE
            name text;
        BEGIN
            FOR name IN SELECT viewname FROM pg_views WHERE schemaname = 'serving' LOOP
                EXECUTE format('DROP VIEW serving.%I', name);
            END LOOP;
        END
        $do$
        """
    )
    for index in INDEXES:
        op.execute(f"DROP INDEX {index}")
    op.execute("DROP FUNCTION serving.json_float(double precision)")
    op.execute("DROP FUNCTION serving.iso_utc(timestamptz)")
    for table in ("api_usage", "api_key", "client", "tier"):
        op.execute(f"DROP TABLE access.{table}")
