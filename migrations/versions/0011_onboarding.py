"""Onboarding: runs, mapping configs, mappings, mapping fields and approvals.

A mapping config is stored once under its content hash; a mapping is one
proposal of a config in a run, so two runs may propose the same config. An
approval names the run and the exact config hash it accepts. `run`, `mapping`
and `approval` keep the store's record exactly, as the catalog tables do; a run
is the only mutable table here.
"""

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

DDL = [
    """
    CREATE TABLE onboarding.run (
        id                 text PRIMARY KEY,
        owner_id           text NOT NULL DEFAULT '',
        kind               text NOT NULL DEFAULT '',
        experiment_id      text,
        source_id          text REFERENCES catalog.source,
        snapshot_id        text REFERENCES catalog.snapshot,
        ontology_hash      sha256 REFERENCES ontology.ontology_version,
        supersedes_run_id  text REFERENCES onboarding.run,
        status             text,
        model              text,
        prompt_version     text,
        thread_id          text,
        model_calls        integer,
        python_calls       integer,
        input_tokens       bigint,
        output_tokens      bigint,
        active_seconds     double precision,
        calculated_cost_usd double precision,
        started_at         timestamptz,
        completed_at       timestamptz,
        state              jsonb NOT NULL DEFAULT '{}',
        created_at         timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX ON onboarding.run (experiment_id)",
    "CREATE INDEX ON onboarding.run (source_id)",
    """
    CREATE TABLE onboarding.mapping_config (
        config_hash        sha256 PRIMARY KEY,
        config             jsonb NOT NULL,
        ontology_hash      sha256 REFERENCES ontology.ontology_version,
        subject_role       text NOT NULL,
        source_kind        text NOT NULL,
        address_role       text NOT NULL,
        source_reliability double precision NOT NULL,
        created_at         timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE onboarding.mapping_field (
        config_hash   sha256 NOT NULL REFERENCES onboarding.mapping_config,
        position      integer NOT NULL,
        concept_id    bigint NOT NULL REFERENCES ontology.concept,
        group_name    text NOT NULL DEFAULT '',
        source_fields text[] NOT NULL,
        PRIMARY KEY (config_hash, position)
    )
    """,
    "CREATE INDEX ON onboarding.mapping_field (concept_id)",
    """
    CREATE TABLE onboarding.mapping (
        id           text PRIMARY KEY,
        owner_id     text NOT NULL DEFAULT '',
        kind         text NOT NULL DEFAULT '',
        run_id       text REFERENCES onboarding.run,
        version      integer,
        config_hash  sha256 REFERENCES onboarding.mapping_config,
        model        text,
        status       text,
        generated_by text,
        proposed_at  timestamptz,
        extra        jsonb NOT NULL DEFAULT '{}',
        created_at   timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX ON onboarding.mapping (run_id)",
    "CREATE INDEX ON onboarding.mapping (config_hash)",
    """
    CREATE TABLE onboarding.approval (
        id             text PRIMARY KEY,
        owner_id       text NOT NULL DEFAULT '',
        kind           text NOT NULL DEFAULT '',
        run_id         text REFERENCES onboarding.run,
        mapping_id     text REFERENCES onboarding.mapping,
        config_hash    sha256 REFERENCES onboarding.mapping_config,
        decision       text,
        reviewer       text,
        feedback       text,
        identity_basis text,
        decided_at     timestamptz,
        extra          jsonb NOT NULL DEFAULT '{}',
        created_at     timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX ON onboarding.approval (run_id)",
    "CREATE INDEX ON onboarding.approval (config_hash)",
]
APPEND_ONLY = ["mapping_config", "mapping_field", "mapping", "approval"]


def upgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    for statement in DDL:
        op.execute(statement)
    for table in APPEND_ONLY:
        op.execute(
            f"CREATE TRIGGER forbid_update BEFORE UPDATE ON onboarding.{table} "
            "FOR EACH ROW EXECUTE FUNCTION public.forbid_update()"
        )


def downgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    for table in ("approval", "mapping", "mapping_field", "mapping_config", "run"):
        op.execute(f"DROP TABLE onboarding.{table}")
