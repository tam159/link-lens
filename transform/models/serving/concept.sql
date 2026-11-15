-- Concepts of the ontology version a release was made under.
SELECT release.id AS release_id,
       concept.name,
       concept.scope,
       concept.datatype,
       concept.cardinality,
       concept.definition,
       concept.minimum,
       concept.maximum,
       member.position,
       ARRAY(
           SELECT allowed.value
           FROM {{ source('ontology', 'concept_value') }} AS allowed
           WHERE allowed.concept_id = concept.id
           ORDER BY allowed.position
       ) AS allowed_values,
       ARRAY(
           SELECT companion.name
           FROM {{ source('ontology', 'concept_requires') }} AS needed
           JOIN {{ source('ontology', 'concept') }} AS companion ON companion.id = needed.required_concept_id
           WHERE needed.concept_id = concept.id
           ORDER BY needed.position
       ) AS requires
FROM {{ source('ops', 'release') }} AS release
JOIN {{ source('ontology', 'version_concept') }} AS member ON member.version_hash = release.ontology_hash
JOIN {{ source('ontology', 'concept') }} AS concept ON concept.id = member.concept_id
