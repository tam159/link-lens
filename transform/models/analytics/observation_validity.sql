-- Observations of enum concepts per source, and how many state a value the
-- ontology does not allow. Checksums of identifiers and records set aside for
-- a missing timestamp are not here: extraction does not store them as rows.
SELECT observation.source_id,
       concept.concept,
       count(*) AS observations,
       count(*) FILTER (
           WHERE NOT EXISTS (
               SELECT 1 FROM {{ ref('stg_ontology__concept_value') }} AS allowed
               WHERE allowed.concept_id = observation.concept_id
                 AND allowed.allowed_value = observation.value
           )
       ) AS outside_allowed_values
FROM {{ ref('stg_evidence__observation') }} AS observation
JOIN {{ ref('stg_ontology__concept') }} AS concept ON concept.concept_id = observation.concept_id
WHERE concept.datatype = 'enum'
GROUP BY observation.source_id, concept.concept
