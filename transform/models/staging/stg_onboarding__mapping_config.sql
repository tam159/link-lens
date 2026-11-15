-- onboarding.mapping_config, renamed and cast only.
SELECT sha256_hex(config_hash) AS config_hash,
       sha256_hex(ontology_hash) AS ontology_hash,
       subject_role,
       source_kind,
       source_reliability,
       jsonb_array_length(coalesce(config -> 'fields', '[]')) AS mapped_fields,
       jsonb_array_length(coalesce(config -> 'unmapped_fields', '[]')) AS unmapped_fields,
       created_at
FROM {{ source('onboarding', 'mapping_config') }}
