"""The console's audit log, and reporting access for the people who operate.

`ops.admin_action` records what a signed-in person did through the operations
console: who, in which role, what, to what, and how it ended. It is append-only.
A request is written and committed before the change it asks for, and its
outcome after, under the same `action_id`: a change can never exist without a
row saying who asked for it, and a request with no outcome is one that was cut
off. A refused request is one row. `request` never holds a key or a secret.

Only a person's session writes here: the orchestrator's role may not.

The pipeline role, which the console and the CLI work as, may now read the
reporting models in `analytics`, so the console shows a source's status from
the one place that defines it. dbt grants the models; this grants the schema.
"""

from alembic import op

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    op.execute(
        """
        CREATE TABLE ops.admin_action (
            id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            action_id uuid NOT NULL,
            phase     text NOT NULL CHECK (phase IN ('requested', 'done', 'failed', 'refused')),
            actor     text NOT NULL CHECK (actor <> ''),
            role      text NOT NULL,
            action    text NOT NULL,     -- source.register, release.create, key.issue, ...
            target    text NOT NULL,
            request   jsonb NOT NULL,    -- never a key or a secret
            result    jsonb,
            at        timestamptz NOT NULL DEFAULT now(),
            UNIQUE (action_id, phase)
        )
        """
    )
    op.execute("CREATE INDEX ON ops.admin_action (at)")
    op.execute(
        "CREATE TRIGGER forbid_update BEFORE UPDATE ON ops.admin_action "
        "FOR EACH ROW EXECUTE FUNCTION public.forbid_update()"
    )
    # A record of what people did: the orchestrator may read it and nothing more.
    op.execute("REVOKE INSERT, UPDATE ON ops.admin_action FROM linklens_orchestrator")
    op.execute("GRANT USAGE ON SCHEMA analytics TO linklens_pipeline")


def downgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    op.execute("REVOKE USAGE ON SCHEMA analytics FROM linklens_pipeline")
    op.execute("DROP TABLE ops.admin_action")
