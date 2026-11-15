-- evidence.source_record, renamed and cast only.
SELECT source_id,
       sha256_hex(id) AS record_id,
       snapshot_id
FROM {{ source('evidence', 'source_record') }}
