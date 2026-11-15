"""Rate limits shared by every product instance, and artifacts that can move.

`access.rate_bucket` holds one token bucket per key, so the per-minute limit is
the same whichever instance answers. It is unlogged: it changes on every call,
and losing it in a crash only refills the buckets.

An artifact's bytes may move from the local directory to object storage. Its
row stays append-only except for `uri`, which says where the bytes are now.
"""

from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    op.execute(
        """
        CREATE UNLOGGED TABLE access.rate_bucket (
            key_id     uuid PRIMARY KEY REFERENCES access.api_key,
            tokens     double precision NOT NULL,
            updated_at timestamptz NOT NULL
        )
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE ON access.rate_bucket TO linklens_product")
    op.execute(
        """
        CREATE FUNCTION catalog.artifact_moves_only() RETURNS trigger
        LANGUAGE plpgsql AS $function$
        BEGIN
            IF (NEW.sha256, NEW.media_type, NEW.size, NEW.name, NEW.created_at)
               IS DISTINCT FROM
               (OLD.sha256, OLD.media_type, OLD.size, OLD.name, OLD.created_at) THEN
                RAISE EXCEPTION 'catalog.artifact is append-only: only uri may change'
                    USING ERRCODE = 'restrict_violation';
            END IF;
            RETURN NEW;
        END
        $function$
        """
    )
    op.execute("DROP TRIGGER forbid_update ON catalog.artifact")
    op.execute(
        "CREATE TRIGGER moves_only BEFORE UPDATE ON catalog.artifact "
        "FOR EACH ROW EXECUTE FUNCTION catalog.artifact_moves_only()"
    )


def downgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    op.execute("DROP TRIGGER moves_only ON catalog.artifact")
    op.execute(
        "CREATE TRIGGER forbid_update BEFORE UPDATE ON catalog.artifact "
        "FOR EACH ROW EXECUTE FUNCTION public.forbid_update()"
    )
    op.execute("DROP FUNCTION catalog.artifact_moves_only()")
    op.execute("DROP TABLE access.rate_bucket")
