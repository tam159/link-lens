-- ops.batch, renamed and cast only.
SELECT id AS batch_id,
       kind AS batch_kind,
       experiment_id,
       baseline_batch_id,
       cardinality(run_ids) AS runs,
       (counts ->> 'observations')::bigint AS counted_observations,
       (counts ->> 'links')::bigint AS counted_links,
       (counts ->> 'profiles')::bigint AS counted_profiles,
       (counts ->> 'unlinked')::bigint AS counted_unlinked,
       coalesce(recorded_at, created_at) AS recorded_at
FROM {{ source('ops', 'batch') }}
