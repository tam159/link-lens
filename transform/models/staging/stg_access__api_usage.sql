-- access.api_usage, renamed and cast only.
SELECT key_id,
       day,
       interface,
       calls
FROM {{ source('access', 'api_usage') }}
