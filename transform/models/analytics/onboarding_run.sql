-- One row per onboarding run: how many mapping versions it took, how often a
-- person asked for a revision, and how long from the first proposal to approval.
-- The validation figures are those of the run's validation sample, not of the
-- whole source.
SELECT run.run_id,
       run.source_id,
       run.experiment_id,
       run.run_status,
       run.model,
       coalesce(mapping.versions, 0) AS mapping_versions,
       coalesce(review.revisions_requested, 0) AS revisions_requested,
       mapping.first_proposed_at,
       review.approved_at,
       CASE WHEN review.approved_at IS NOT NULL AND mapping.first_proposed_at IS NOT NULL
            THEN (extract(epoch FROM review.approved_at - mapping.first_proposed_at) / 3600)::double precision
            END AS hours_to_approval,
       run.model_calls,
       run.input_tokens,
       run.output_tokens,
       run.calculated_cost_usd,
       run.validation_records,
       run.validation_quarantined_fields,
       run.started_at,
       run.completed_at
FROM {{ ref('stg_onboarding__run') }} AS run
LEFT JOIN (
    SELECT run_id, count(*) AS versions, min(proposed_at) AS first_proposed_at
    FROM {{ ref('stg_onboarding__mapping') }}
    GROUP BY run_id
) AS mapping ON mapping.run_id = run.run_id
LEFT JOIN (
    SELECT run_id,
           count(*) FILTER (WHERE decision = 'revision_requested') AS revisions_requested,
           min(decided_at) FILTER (WHERE decision = 'approved') AS approved_at
    FROM {{ ref('stg_onboarding__approval') }}
    GROUP BY run_id
) AS review ON review.run_id = run.run_id
WHERE run.run_kind = 'onboarding'
