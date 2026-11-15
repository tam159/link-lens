-- evidence.observation, renamed and cast only.
SELECT source_id,
       sha256_hex(id) AS observation_id,
       sha256_hex(record_id) AS record_id,
       concept_id,
       sha256_hex(config_hash) AS config_hash,
       value,
       timestamp_basis,
       observed_at,
       ingested_at
FROM {{ source('evidence', 'observation') }}
