-- Identity links per batch by rule and review state. A score is a rule or
-- model score, never a probability; `score_kind` says which.
SELECT batch_id,
       rule,
       link_status,
       coalesce(human_review_status, 'not recorded') AS human_review_status,
       score_kind,
       count(*) AS links
FROM {{ ref('stg_identity__link') }}
GROUP BY batch_id, rule, link_status, coalesce(human_review_status, 'not recorded'), score_kind
