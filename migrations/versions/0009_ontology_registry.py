"""Ontology registry: versions, concepts, proposals, activations and gate reports.

Every table is append-only: an ontology version, its concepts and the records of
how it was proposed, checked and activated never change after they are written.
A version must contain every concept of its parent, checked when the inserting
transaction commits. A rejected proposal may repeat a source field or a concept,
so dispositions and concept decisions are keyed by their position. Bounds are kept as the text the ontology states, because a
version's hash is computed from that text.
"""

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

TABLES = [
    "ontology_version",
    "concept",
    "concept_value",
    "concept_requires",
    "version_concept",
    "version_evidence",
    "proposal",
    "proposal_run",
    "disposition",
    "concept_decision",
    "activation",
    "gate_report",
]

DDL = [
    """
    CREATE TABLE ontology.ontology_version (
        hash              sha256 PRIMARY KEY,
        parent_hash       sha256 REFERENCES ontology.ontology_version,
        label             text NOT NULL,
        document_artifact sha256 NOT NULL,
        created_at        timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE ontology.concept (
        id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        name          text NOT NULL,
        content_hash  sha256 NOT NULL,
        scope         text NOT NULL,
        datatype      text NOT NULL,
        cardinality   text NOT NULL CHECK (cardinality IN ('one', 'many')),
        definition    text NOT NULL,
        minimum       text CHECK (minimum IS NULL OR pg_input_is_valid(minimum, 'numeric')),
        maximum       text CHECK (maximum IS NULL OR pg_input_is_valid(maximum, 'numeric')),
        introduced_in sha256 NOT NULL REFERENCES ontology.ontology_version,
        UNIQUE (name, content_hash),
        UNIQUE (id, name)
    )
    """,
    """
    CREATE TABLE ontology.concept_value (
        concept_id bigint NOT NULL REFERENCES ontology.concept,
        value      text NOT NULL,
        position   int NOT NULL,
        PRIMARY KEY (concept_id, value),
        UNIQUE (concept_id, position)
    )
    """,
    """
    CREATE TABLE ontology.concept_requires (
        concept_id          bigint NOT NULL REFERENCES ontology.concept,
        required_concept_id bigint NOT NULL REFERENCES ontology.concept,
        position            int NOT NULL,
        PRIMARY KEY (concept_id, required_concept_id),
        UNIQUE (concept_id, position)
    )
    """,
    """
    CREATE TABLE ontology.version_concept (
        version_hash sha256 NOT NULL REFERENCES ontology.ontology_version,
        concept_id   bigint NOT NULL,
        name         text NOT NULL,
        position     int NOT NULL,
        PRIMARY KEY (version_hash, concept_id),
        UNIQUE (version_hash, name),
        UNIQUE (version_hash, position),
        FOREIGN KEY (concept_id, name) REFERENCES ontology.concept (id, name)
    )
    """,
    """
    CREATE TABLE ontology.version_evidence (
        version_hash      sha256 NOT NULL REFERENCES ontology.ontology_version,
        evidence_artifact sha256 NOT NULL,
        created_at        timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (version_hash, evidence_artifact)
    )
    """,
    """
    CREATE TABLE ontology.proposal (
        id                      text PRIMARY KEY,
        experiment_id           text NOT NULL,
        parent_hash             sha256 NOT NULL REFERENCES ontology.ontology_version,
        ontology_hash           sha256 REFERENCES ontology.ontology_version,
        job_run_id              text,
        status                  text NOT NULL CHECK (status IN ('validated', 'rejected')),
        model                   text,
        prompt_version          text,
        proposal_artifact       sha256 NOT NULL,
        accepted_concepts       int,
        rejected_concepts       int,
        supersedes_proposal_ids text[],
        created_at              timestamptz NOT NULL,
        CHECK ((status = 'validated') = (ontology_hash IS NOT NULL))
    )
    """,
    """
    CREATE TABLE ontology.proposal_run (
        proposal_id text NOT NULL REFERENCES ontology.proposal,
        position    int NOT NULL,
        run_id      text NOT NULL,
        alias       text,
        PRIMARY KEY (proposal_id, position),
        UNIQUE (proposal_id, run_id)
    )
    """,
    """
    CREATE TABLE ontology.disposition (
        proposal_id    text NOT NULL REFERENCES ontology.proposal,
        source_ref     text NOT NULL,
        source_field   text NOT NULL,
        position       int NOT NULL,
        run_id         text,
        disposition    text NOT NULL CHECK (disposition IN (
            'existing_target', 'new_concept', 'insufficient_evidence',
            'non_domain_metadata')),
        target_concept text,
        evidence_quote text NOT NULL,
        reason         text NOT NULL,
        PRIMARY KEY (proposal_id, position)
    )
    """,
    "CREATE INDEX ON ontology.disposition (proposal_id, source_field)",
    """
    CREATE TABLE ontology.concept_decision (
        proposal_id  text NOT NULL REFERENCES ontology.proposal,
        concept_name text NOT NULL,
        position     int NOT NULL,
        acceptable   boolean NOT NULL,
        reason       text NOT NULL,
        PRIMARY KEY (proposal_id, position)
    )
    """,
    """
    CREATE TABLE ontology.activation (
        id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        experiment_id text NOT NULL,
        version_hash  sha256 NOT NULL REFERENCES ontology.ontology_version,
        status        text NOT NULL CHECK (status IN ('experimental', 'promoted')),
        reviewer      text,
        created_at    timestamptz NOT NULL,
        gate_run_at   timestamptz,
        gate_results  jsonb,
        CHECK ((status = 'promoted') = (reviewer IS NOT NULL)),
        CHECK ((gate_run_at IS NULL) = (gate_results IS NULL)),
        UNIQUE (experiment_id, version_hash, status, created_at)
    )
    """,
    "CREATE INDEX ON ontology.activation (experiment_id, created_at DESC, id DESC)",
    """
    CREATE TABLE ontology.gate_report (
        version_hash sha256 NOT NULL REFERENCES ontology.ontology_version,
        check_name   text NOT NULL,
        result       text NOT NULL CHECK (result IN ('pass', 'fail', 'unknown')),
        detail       jsonb NOT NULL,
        created_at   timestamptz NOT NULL,
        PRIMARY KEY (version_hash, check_name, created_at)
    )
    """,
    """
    CREATE FUNCTION ontology.require_additive() RETURNS trigger
    LANGUAGE plpgsql AS $function$
    BEGIN
        IF NEW.parent_hash IS NOT NULL AND EXISTS (
            SELECT 1 FROM ontology.version_concept parent
            WHERE parent.version_hash = NEW.parent_hash
              AND NOT EXISTS (
                  SELECT 1 FROM ontology.version_concept child
                  WHERE child.version_hash = NEW.hash
                    AND child.concept_id = parent.concept_id)
        ) THEN
            RAISE EXCEPTION
                'ontology version % removes or redefines a concept of its parent',
                encode(NEW.hash, 'hex')
                USING ERRCODE = 'check_violation';
        END IF;
        RETURN NULL;
    END
    $function$
    """,
    """
    CREATE CONSTRAINT TRIGGER require_additive
    AFTER INSERT ON ontology.ontology_version
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION ontology.require_additive()
    """,
]


def upgrade():
    # Objects are created as the migrator so its default privileges apply.
    op.execute("SET LOCAL ROLE linklens_migrator")
    for statement in DDL:
        op.execute(statement)
    for table in TABLES:
        op.execute(
            f"CREATE TRIGGER forbid_update BEFORE UPDATE ON ontology.{table} "
            "FOR EACH ROW EXECUTE FUNCTION public.forbid_update()"
        )


def downgrade():
    op.execute("SET LOCAL ROLE linklens_migrator")
    for table in reversed(TABLES):
        op.execute(f"DROP TABLE ontology.{table}")
    op.execute("DROP FUNCTION ontology.require_additive()")
