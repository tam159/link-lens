-- catalog.drift_check, renamed and cast only.
SELECT snapshot_id,
       sha256_hex(config_hash) AS config_hash,
       source_id,
       status AS drift_status,
       blocking,
       reasons,
       checked_at
FROM {{ source('catalog', 'drift_check') }}
