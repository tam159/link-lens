-- ontology.concept_value, renamed and cast only.
SELECT concept_id,
       value AS allowed_value,
       position
FROM {{ source('ontology', 'concept_value') }}
