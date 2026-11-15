"""Identity: entities, memberships, links and profiles with their fields.

Each row keeps the store's record exactly. An entity row is either the shared
record of an entity, which assembly updates, or the snapshot of an entity that
an enhancement batch owns. Memberships, links, profiles, profile fields and
profile addresses are append-only. A profile's fields and addresses are stored
once, as rows that point at the observation or source record they were
selected from.
"""

from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

HEAD = """
        id         text PRIMARY KEY,
        owner_id   text NOT NULL DEFAULT '',
        kind       text NOT NULL DEFAULT '',
        batch_id   text REFERENCES ops.batch,"""
TAIL = """
        extra      jsonb NOT NULL DEFAULT '{}',
        created_at timestamptz NOT NULL DEFAULT now()"""
DDL = [
    f"""
    CREATE TABLE identity.entity ({HEAD}
        entity_id    text,
        status       text,
        rule_version text,
        identifiers  jsonb,{TAIL}
    )
    """,
    "CREATE INDEX ON identity.entity (entity_id)",
    "CREATE INDEX ON identity.entity (batch_id)",
    "CREATE INDEX ON identity.entity USING gin (identifiers jsonb_path_ops)",
    """
    CREATE VIEW identity.entity_identifier AS
    SELECT entity.id AS entity_row_id,
           entity.entity_id,
           entity.batch_id,
           scheme.key AS scheme,
           identifier.value
    FROM identity.entity
    CROSS JOIN LATERAL jsonb_each(
        CASE WHEN jsonb_typeof(entity.identifiers) = 'object'
             THEN entity.identifiers ELSE '{}' END
    ) AS scheme
    CROSS JOIN LATERAL jsonb_array_elements_text(
        CASE WHEN jsonb_typeof(scheme.value) = 'array'
             THEN scheme.value ELSE '[]' END
    ) AS identifier(value)
    """,
    f"""
    CREATE TABLE identity.membership ({HEAD}
        source_id text,
        record_id sha256,
        entity_id text,{TAIL},
        FOREIGN KEY (source_id, record_id)
            REFERENCES evidence.source_record (source_id, id)
    )
    """,
    "CREATE UNIQUE INDEX ON identity.membership (batch_id, source_id, record_id)",
    "CREATE INDEX ON identity.membership (batch_id, entity_id)",
    f"""
    CREATE TABLE identity.link ({HEAD}
        link_id             sha256,
        entity_key          text,
        rule                text,
        rule_version        text,
        score               double precision,
        score_kind          text,
        threshold           double precision,
        status              text,
        human_review_status text,
        evidence            jsonb,
        a_source_id         text,
        a_record_id         sha256,
        b_source_id         text,
        b_record_id         sha256,{TAIL},
        FOREIGN KEY (a_source_id, a_record_id)
            REFERENCES evidence.source_record (source_id, id),
        FOREIGN KEY (b_source_id, b_record_id)
            REFERENCES evidence.source_record (source_id, id)
    )
    """,
    "CREATE INDEX ON identity.link (batch_id)",
    f"""
    CREATE TABLE identity.profile ({HEAD}
        entity_key      text,
        profile_version sha256,
        policy_version  text,
        status          text,
        uncertainties   jsonb,{TAIL}
    )
    """,
    "CREATE UNIQUE INDEX ON identity.profile (batch_id, entity_key)",
    """
    CREATE TABLE identity.profile_field (
        profile_id            text NOT NULL REFERENCES identity.profile,
        position              integer NOT NULL,
        concept_name          text NOT NULL,
        concept_id            bigint REFERENCES ontology.concept,
        status                text,
        value                 text,
        observation_source_id text,
        observation_id        sha256,
        detail                jsonb NOT NULL,
        PRIMARY KEY (profile_id, position),
        FOREIGN KEY (observation_source_id, observation_id)
            REFERENCES evidence.observation (source_id, id)
    )
    """,
    "CREATE INDEX ON identity.profile_field (concept_id)",
    "CREATE INDEX ON identity.profile_field (observation_source_id, observation_id)",
    """
    CREATE TABLE identity.profile_address (
        profile_id text NOT NULL REFERENCES identity.profile,
        position   integer NOT NULL,
        role       text,
        source_id  text,
        record_id  sha256,
        detail     jsonb NOT NULL,
        PRIMARY KEY (profile_id, position),
        FOREIGN KEY (source_id, record_id)
            REFERENCES evidence.source_record (source_id, id)
    )
    """,
]
APPEND_ONLY = ["membership", "link", "profile", "profile_field", "profile_address"]


def upgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    for statement in DDL:
        op.execute(statement)
    for table in APPEND_ONLY:
        op.execute(
            f"CREATE TRIGGER forbid_update BEFORE UPDATE ON identity.{table} "
            "FOR EACH ROW EXECUTE FUNCTION public.forbid_update()"
        )


def downgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    op.execute("DROP VIEW identity.entity_identifier")
    for table in (
        "profile_address",
        "profile_field",
        "profile",
        "link",
        "membership",
        "entity",
    ):
        op.execute(f"DROP TABLE identity.{table}")
