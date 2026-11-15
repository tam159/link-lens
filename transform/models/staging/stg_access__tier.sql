-- access.tier, renamed and cast only.
SELECT id AS tier_id,
       monthly_quota,
       rate_per_minute,
       interfaces,
       toolsets,
       source_scope,
       bundle_downloads,
       release_lag,
       history_depth
FROM {{ source('access', 'tier') }}
