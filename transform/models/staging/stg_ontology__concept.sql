-- ontology.concept, renamed and cast only.
SELECT id AS concept_id,
       name AS concept,
       scope,
       datatype,
       cardinality
FROM {{ source('ontology', 'concept') }}
