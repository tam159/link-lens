-- onboarding.mapping, renamed and cast only.
SELECT id AS mapping_id,
       run_id,
       version AS mapping_version,
       sha256_hex(config_hash) AS config_hash,
       model,
       status AS mapping_status,
       generated_by,
       coalesce(proposed_at, created_at) AS proposed_at
FROM {{ source('onboarding', 'mapping') }}
