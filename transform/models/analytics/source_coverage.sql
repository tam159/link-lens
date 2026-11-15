-- What each registered source contributes: records, observations and concepts,
-- and how much of its file the approved mapping in force leaves unmapped.
SELECT state.source_id,
       state.source_title,
       '/sources/' || state.source_id || '.md' AS okf_path,
       coalesce(stored.records, 0) AS records,
       coalesce(stored.observations, 0) AS observations,
       coalesce(stored.concepts_used, 0) AS concepts_used,
       state.approved_config_hash,
       config.mapped_fields,
       config.unmapped_fields,
       CASE WHEN config.mapped_fields + config.unmapped_fields > 0
            THEN round(config.unmapped_fields::numeric
                       / (config.mapped_fields + config.unmapped_fields), 4) END AS unmapped_share
FROM {{ ref('stg_catalog__source_state') }} AS state
LEFT JOIN (
    SELECT source_id,
           count(DISTINCT record_id) AS records,
           count(*) AS observations,
           count(DISTINCT concept_id) AS concepts_used
    FROM {{ ref('stg_evidence__observation') }}
    GROUP BY source_id
) AS stored ON stored.source_id = state.source_id
LEFT JOIN {{ ref('stg_onboarding__mapping_config') }} AS config
       ON config.config_hash = state.approved_config_hash
WHERE state.source_kind = 'registered'
