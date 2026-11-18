"""Links from ontology concepts to terms of shared vocabularies.

`ontology.concept_reference` records that a person judged a concept to match a
term of another vocabulary, such as schema.org or the W3C Registered
Organization Vocabulary, and how closely: exact, close, broad, narrow or
related, the SKOS mapping relations. A person withdraws a link with a later
row; the latest row for a concept and a term says whether the link stands.

The links are not part of an ontology version. A version's hash is the digest of
its document, and the document is unchanged: a link can be recorded or
withdrawn after the version is promoted, without a new version or a new mapping
approval. Rows are append-only, and only a person records them: the
orchestrator's role may read them and nothing more.
"""

from alembic import op

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    op.execute(
        """
        CREATE TABLE ontology.concept_reference (
            id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            concept_id  bigint NOT NULL REFERENCES ontology.concept,
            iri         text NOT NULL CHECK (iri ~ '^https?://[^\\s<>"]+$'),
            match       text NOT NULL
                        CHECK (match IN ('exact', 'close', 'broad', 'narrow', 'related')),
            action      text NOT NULL CHECK (action IN ('add', 'withdraw')),
            reviewer    text NOT NULL CHECK (reviewer <> ''),
            note        text,
            recorded_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX ON ontology.concept_reference (concept_id, iri, recorded_at, id)"
    )
    op.execute(
        "CREATE TRIGGER forbid_update BEFORE UPDATE ON ontology.concept_reference "
        "FOR EACH ROW EXECUTE FUNCTION public.forbid_update()"
    )
    # A person's decision: the orchestrator may read it and nothing more.
    op.execute(
        "REVOKE INSERT, UPDATE ON ontology.concept_reference FROM linklens_orchestrator"
    )


def downgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    # Views are dbt's and serving.concept reads this table; dbt builds them again.
    op.execute(
        """
        DO $do$
        DECLARE
            name text;
        BEGIN
            FOR name IN
                SELECT schemaname || '.' || quote_ident(viewname) FROM pg_views
                WHERE viewowner = 'linklens_transform'
            LOOP
                EXECUTE format('DROP VIEW IF EXISTS %s CASCADE', name);
            END LOOP;
        END
        $do$
        """
    )
    op.execute("DROP TABLE ontology.concept_reference")
