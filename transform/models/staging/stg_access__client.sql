-- access.client, renamed and cast only.
SELECT id AS client_id,
       name AS client_name,
       tier_id,
       status AS client_status,
       created_at
FROM {{ source('access', 'client') }}
