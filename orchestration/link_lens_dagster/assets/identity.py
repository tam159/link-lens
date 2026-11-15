"""A batch of entities, proposed links and profiles."""

import dagster as dg

from ..resources import Pipeline
from .extraction import observations


class BatchConfig(dg.Config):
    minimum_profiles: int = 50
    # Records per source read after approval to find the cohort; unset uses the
    # records each run sampled.
    cohort_pool_size: int | None = None
    baseline_batch_id: str | None = None
    # Unset assembles from the approved run of every registered source.
    run_ids: list[str] = []


@dg.asset(
    deps=[observations],
    group_name="identity",
    pool="database",
    check_specs=[
        dg.AssetCheckSpec(
            "selected_fields_cite_evidence",
            asset="identity_batch",
            description="Every selected profile field points at the observation it was selected from.",
        ),
        dg.AssetCheckSpec(
            "counts_match_the_batch",
            asset="identity_batch",
            description="The profiles and links stored for the batch equal the counts it recorded.",
        ),
    ],
)
def identity_batch(
    context: dg.AssetExecutionContext, config: BatchConfig, pipeline: Pipeline
):
    """Resolve identities and assemble profiles from the approved runs. Deterministic.

    Every materialisation is a new batch; none is rewritten. A batch is served
    to nobody until a person records a release of it. The hybrid enhancement
    pass makes paid calls and is not part of this asset.
    """
    from link_lens.refresh import Blocked

    try:
        result = pipeline.steps.assemble(
            config.run_ids or None,
            config.minimum_profiles,
            config.cohort_pool_size,
            config.baseline_batch_id,
        )
    except Blocked as blocked:
        raise dg.Failure(description=str(blocked), allow_retries=False) from blocked
    batch = result["batch_id"]
    yield dg.MaterializeResult(
        data_version=dg.DataVersion(result["profile_digest"]),
        metadata={
            "batch_id": batch,
            "runs": len(result["run_ids"]),
            "profiles": result["counts"]["profiles"],
            "links": result["counts"]["links"],
            "observations": result["counts"]["observations"],
            "unlinked": result["counts"]["unlinked"],
            "profile_digest": result["profile_digest"],
        },
    )
    uncited = pipeline.scalar(
        "SELECT count(*) FROM identity.profile_field f "
        "JOIN identity.profile p ON p.id = f.profile_id "
        "WHERE p.batch_id = :batch AND f.status = 'selected' AND f.observation_id IS NULL",
        batch=batch,
    )
    yield dg.AssetCheckResult(
        check_name="selected_fields_cite_evidence",
        passed=uncited == 0,
        metadata={"selected_fields_without_an_observation": uncited},
    )
    stored = pipeline.rows(
        "SELECT (SELECT count(*) FROM identity.profile WHERE batch_id = :batch) AS profiles, "
        "(SELECT count(*) FROM identity.link WHERE batch_id = :batch) AS links",
        batch=batch,
    )[0]
    yield dg.AssetCheckResult(
        check_name="counts_match_the_batch",
        passed=(stored["profiles"], stored["links"])
        == (result["counts"]["profiles"], result["counts"]["links"]),
        metadata={
            "stored_profiles": stored["profiles"],
            "stored_links": stored["links"],
        },
    )
