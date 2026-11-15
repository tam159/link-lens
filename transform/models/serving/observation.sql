-- Source claims of a release: every observation extracted with a mapping config
-- that was approved in one of the release's runs, linked to an entity or not.
SELECT release.id AS release_id,
       observation.source_id,
       observation.id AS observation_key,
       sha256_hex(observation.id) AS observation_id,
       observation.record_id AS record_key,
       sha256_hex(observation.record_id) AS record_id,
       membership.entity_id,
       concept.name AS concept,
       observation.value,
       observation.raw_value,
       observation.source_fields,
       observation.group_name,
       observation.field_confidence,
       config.source_reliability,
       'uncalibrated mapping/source judgements' AS confidence_kind,
       observation.observed_at,
       observation.timestamp_basis,
       observation.timezone_assumed,
       observation.ingested_at,
       observation.derivation_level,
       sha256_hex(observation.config_hash) AS config_hash,
       config.subject_role,
       config.source_kind,
       snapshot.licence,
       snapshot.licence_url,
       -- The observation exactly as the extractor wrote it, for rendering its page.
       jsonb_build_object(
           'source_id', observation.source_id,
           'source_record_id', sha256_hex(observation.record_id),
           'observed_at', serving.iso_utc(observation.observed_at),
           'observed_at_basis',
               CASE WHEN observation.timestamp_basis = 'record'
                    THEN 'source record statement field'
                    ELSE snapshot.observed_at_basis END,
           'timezone_assumption',
               CASE WHEN observation.timezone_assumed
                    THEN 'UTC assumed for timezone-naive source timestamp' END,
           'ingested_at', serving.iso_utc(observation.ingested_at),
           'licence', snapshot.licence,
           'extractor_version', observation.engine || ':' || sha256_hex(observation.config_hash),
           'field', concept.name,
           'value',
               CASE WHEN concept.datatype = 'integer' AND observation.value ~ '^[+-]?[0-9]+$'
                        THEN to_jsonb(observation.value::numeric)
                    WHEN concept.datatype = 'boolean' AND observation.value IN ('true', 'false')
                        THEN to_jsonb(observation.value = 'true')
                    ELSE to_jsonb(observation.value) END,
           'source_fields', to_jsonb(observation.source_fields),
           'raw_value', observation.raw_value,
           'raw_locator', record.locator,
           'snapshot_id', record.snapshot_id,
           'config_hash', sha256_hex(observation.config_hash),
           'subject_role', config.subject_role,
           'source_kind', config.source_kind,
           'address_role', config.address_role,
           'confidence', jsonb_build_object(
               'source_reliability', serving.json_float(config.source_reliability),
               'field_confidence', serving.json_float(observation.field_confidence)
           ),
           'confidence_kind', 'uncalibrated mapping/source judgements',
           'derivation_level', observation.derivation_level,
           'id', sha256_hex(observation.id)
       )
       || CASE WHEN config.ontology_hash IS NULL THEN '{}'::jsonb
               ELSE jsonb_build_object(
                   'ontology_hash', sha256_hex(config.ontology_hash),
                   'value_type', concept.datatype,
                   'cardinality', concept.cardinality
               ) END
       || CASE WHEN observation.group_name IS NULL THEN '{}'::jsonb
               ELSE jsonb_build_object(
                   'scope', concept.scope,
                   'group_id', sha256_hex(observation.group_id),
                   'group_name', observation.group_name
               ) END
       || observation.extra AS document
FROM {{ source('ops', 'release') }} AS release
JOIN {{ source('ops', 'batch') }} AS batch ON batch.id = release.batch_id
JOIN {{ source('onboarding', 'run') }} AS run ON run.id = ANY (batch.run_ids)
JOIN {{ source('onboarding', 'approval') }} AS approval
  ON approval.id = run.state ->> 'approval_id' AND approval.decision = 'approved'
JOIN {{ source('onboarding', 'mapping_config') }} AS config ON config.config_hash = approval.config_hash
JOIN {{ source('evidence', 'observation') }} AS observation
  ON observation.config_hash = config.config_hash AND observation.source_id = run.source_id
JOIN {{ source('ontology', 'concept') }} AS concept ON concept.id = observation.concept_id
JOIN {{ source('evidence', 'source_record') }} AS record
  ON record.source_id = observation.source_id AND record.id = observation.record_id
JOIN {{ source('catalog', 'snapshot') }} AS snapshot ON snapshot.id = record.snapshot_id
LEFT JOIN {{ source('identity', 'membership') }} AS membership
  ON membership.batch_id = release.batch_id
 AND membership.source_id = observation.source_id
 AND membership.record_id = observation.record_id
