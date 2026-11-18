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
       ) AS requires,
       -- Links a person recorded to terms of other vocabularies, as they stood
       -- when the release was recorded: for each term, the latest row by then.
       COALESCE((
           SELECT jsonb_agg(jsonb_build_object('iri', link.iri, 'match', link.match)
                            ORDER BY link.iri)
           FROM (
               SELECT DISTINCT ON (recorded.iri) recorded.iri, recorded.match, recorded.action
               FROM {{ source('ontology', 'concept_reference') }} AS recorded
               WHERE recorded.concept_id = concept.id
                 AND recorded.recorded_at <= release.released_at
               ORDER BY recorded.iri, recorded.recorded_at DESC, recorded.id DESC
           ) AS link
           WHERE link.action = 'add'
       ), '[]'::jsonb) AS vocabulary_references,
       -- The source columns the release's approved mappings read this concept
       -- from, one column a field. Each names its source: the product service
       -- shows a key only the headers of sources it may see.
       COALESCE((
           SELECT jsonb_agg(jsonb_build_object('source_id', header.source_id,
                                               'header', header.name)
                            ORDER BY header.source_id, header.name)
           FROM (
               SELECT DISTINCT run.source_id, field.source_fields[1] AS name
               FROM {{ source('ops', 'batch') }} AS batch
               JOIN {{ source('onboarding', 'run') }} AS run ON run.id = ANY (batch.run_ids)
               JOIN {{ source('onboarding', 'approval') }} AS approval
                 ON approval.id = run.state ->> 'approval_id' AND approval.decision = 'approved'
               JOIN {{ source('onboarding', 'mapping_field') }} AS field
                 ON field.config_hash = approval.config_hash
               WHERE batch.id = release.batch_id
                 AND field.concept_id = concept.id
                 AND cardinality(field.source_fields) = 1
           ) AS header
       ), '[]'::jsonb) AS source_headers
FROM {{ source('ops', 'release') }} AS release
JOIN {{ source('ontology', 'version_concept') }} AS member ON member.version_hash = release.ontology_hash
JOIN {{ source('ontology', 'concept') }} AS concept ON concept.id = member.concept_id
