-- access.api_key, renamed and cast only.
SELECT id AS key_id,
       client_id,
       prefix AS key_prefix,
       label AS key_label,
       created_at,
       expires_at,
       revoked_at
FROM {{ source('access', 'api_key') }}
