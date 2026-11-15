-- onboarding.mapping_field, renamed and cast only.
SELECT sha256_hex(config_hash) AS config_hash,
       position,
       concept_id,
       group_name,
       source_fields
FROM {{ source('onboarding', 'mapping_field') }}
