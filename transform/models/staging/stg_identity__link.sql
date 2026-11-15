-- identity.link, renamed and cast only.
SELECT batch_id,
       sha256_hex(link_id) AS link_id,
       entity_key AS entity_id,
       rule,
       rule_version,
       score,
       score_kind,
       status AS link_status,
       human_review_status
FROM {{ source('identity', 'link') }}
