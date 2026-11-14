"""Shared database helpers: the sha256 domain and the append-only trigger function.

`sha256` stores a digest as 32 raw bytes. `sha256_hex` and `sha256_from_hex`
convert to and from the 64-character hex form used everywhere else. Attach
`forbid_update()` to an append-only table with:

    CREATE TRIGGER forbid_update BEFORE UPDATE ON some.table
    FOR EACH ROW EXECUTE FUNCTION public.forbid_update();
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE DOMAIN public.sha256 AS bytea CHECK (octet_length(VALUE) = 32)")
    op.execute(
        """
        CREATE FUNCTION public.sha256_hex(public.sha256) RETURNS text
        LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE
        RETURN encode($1, 'hex')
        """
    )
    op.execute(
        """
        CREATE FUNCTION public.sha256_from_hex(text) RETURNS public.sha256
        LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE
        RETURN decode($1, 'hex')::public.sha256
        """
    )
    op.execute(
        """
        CREATE FUNCTION public.forbid_update() RETURNS trigger
        LANGUAGE plpgsql AS $function$
        BEGIN
            RAISE EXCEPTION '% on %.% is not allowed: rows are append-only',
                TG_OP, TG_TABLE_SCHEMA, TG_TABLE_NAME
                USING ERRCODE = 'restrict_violation';
        END
        $function$
        """
    )


def downgrade():
    op.execute("DROP FUNCTION public.forbid_update()")
    op.execute("DROP FUNCTION public.sha256_from_hex(text)")
    op.execute("DROP FUNCTION public.sha256_hex(public.sha256)")
    op.execute("DROP DOMAIN public.sha256")
