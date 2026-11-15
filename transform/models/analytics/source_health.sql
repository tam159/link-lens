-- One row per registered source: when it was last checked and changed, whether
-- it is due, and whether its latest onboarding run waits for a person.
-- `refresh_status` is worked out when the model is read. Drift is not here:
-- a drift check returns its result and stores nothing yet.
SELECT state.source_id,
       state.source_title,
       source.publisher,
       source.portal || '/dataset/' || source.slug AS portal_url,
       '/sources/' || state.source_id || '.md' AS okf_path,
       (extract(epoch FROM state.cadence) / 86400)::double precision AS cadence_days,
       state.last_checked_at,
       state.next_check_due_at,
       state.last_changed_at,
       state.latest_snapshot_id,
       state.approved_config_hash,
       state.approved_at,
       latest.run_id AS latest_run_id,
       latest.run_status AS latest_run_status,
       coalesce(latest.run_status = 'needs_review', false) AS waiting_for_review,
       CASE WHEN latest.run_status = 'needs_review' THEN latest.waiting_since END AS waiting_since,
       CASE WHEN state.cadence IS NULL THEN 'no_cadence'
            WHEN state.last_checked_at IS NULL THEN 'never_checked'
            WHEN state.next_check_due_at < now() THEN 'stale'
            ELSE 'fresh' END AS refresh_status,
       CASE WHEN state.next_check_due_at < now()
            THEN (extract(epoch FROM now() - state.next_check_due_at) / 86400)::double precision
            END AS days_overdue
FROM {{ ref('stg_catalog__source_state') }} AS state
JOIN {{ ref('stg_catalog__source') }} AS source ON source.source_id = state.source_id
LEFT JOIN LATERAL (
    SELECT run.run_id,
           run.run_status,
           coalesce(
               (SELECT max(mapping.proposed_at)
                FROM {{ ref('stg_onboarding__mapping') }} AS mapping
                WHERE mapping.run_id = run.run_id),
               run.completed_at, run.started_at, run.created_at
           ) AS waiting_since
    FROM {{ ref('stg_onboarding__run') }} AS run
    WHERE run.source_id = state.source_id AND run.run_kind = 'onboarding'
    ORDER BY coalesce(run.started_at, run.created_at) DESC, run.run_id DESC
    LIMIT 1
) AS latest ON true
WHERE state.source_kind = 'registered'
