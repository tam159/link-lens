-- Calls to the product service per day, client, tier and interface. Usage is
-- counted per key; a client's keys are added up. There is no route or tool here:
-- the product service does not record one.
SELECT usage.day,
       client.client_id,
       client.client_name,
       client.tier_id,
       usage.interface,
       count(DISTINCT usage.key_id) AS keys,
       sum(usage.calls)::bigint AS calls
FROM {{ ref('stg_access__api_usage') }} AS usage
JOIN {{ ref('stg_access__api_key') }} AS key ON key.key_id = usage.key_id
JOIN {{ ref('stg_access__client') }} AS client ON client.client_id = key.client_id
GROUP BY usage.day, client.client_id, client.client_name, client.tier_id, usage.interface
