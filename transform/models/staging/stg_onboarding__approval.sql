-- onboarding.approval, renamed and cast only.
SELECT id AS approval_id,
       run_id,
       mapping_id,
       sha256_hex(config_hash) AS config_hash,
       decision,
       reviewer,
       coalesce(decided_at, created_at) AS decided_at
FROM {{ source('onboarding', 'approval') }}
