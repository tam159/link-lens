-- How much each ontology concept is used: observations, sources that state it
-- and mapping configs that map it. A concept nothing maps is `never_mapped`.
SELECT concept.concept,
       concept.scope,
       concept.datatype,
       concept.cardinality,
       '/ontology/' || concept.scope || '/' || concept.concept || '.md' AS okf_path,
       coalesce(observed.observations, 0) AS observations,
       coalesce(observed.sources, 0) AS sources,
       coalesce(mapped.mapping_configs, 0) AS mapping_configs,
       coalesce(mapped.mapping_configs, 0) = 0 AS never_mapped
FROM {{ ref('stg_ontology__concept') }} AS concept
LEFT JOIN (
    SELECT concept_id, count(*) AS observations, count(DISTINCT source_id) AS sources
    FROM {{ ref('stg_evidence__observation') }}
    GROUP BY concept_id
) AS observed ON observed.concept_id = concept.concept_id
LEFT JOIN (
    SELECT concept_id, count(DISTINCT config_hash) AS mapping_configs
    FROM {{ ref('stg_onboarding__mapping_field') }}
    GROUP BY concept_id
) AS mapped ON mapped.concept_id = concept.concept_id
