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
           FROM ontology.concept_value AS allowed
           WHERE allowed.concept_id = concept.id
           ORDER BY allowed.position
       ) AS allowed_values
FROM ops.release AS release
JOIN ontology.version_concept AS member ON member.version_hash = release.ontology_hash
JOIN ontology.concept AS concept ON concept.id = member.concept_id
