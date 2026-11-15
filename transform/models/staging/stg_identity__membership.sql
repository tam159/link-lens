-- identity.membership, renamed and cast only.
SELECT batch_id,
       source_id,
       sha256_hex(record_id) AS record_id,
       entity_id
FROM {{ source('identity', 'membership') }}
