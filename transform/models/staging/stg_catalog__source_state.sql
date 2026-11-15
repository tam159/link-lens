-- catalog.source_state, renamed and cast only.
SELECT source_id,
       kind AS source_kind,
       title AS source_title,
       cadence,
       last_checked_at,
       next_check_due_at,
       latest_snapshot_id,
       last_changed_at,
       sha256_hex(approved_config_hash) AS approved_config_hash,
       approved_mapping_id,
       approved_run_id,
       approved_at
FROM {{ source('catalog', 'source_state') }}
