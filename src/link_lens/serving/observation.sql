-- Source claims of a release: every observation extracted with a mapping config
-- that was approved in one of the release's runs, linked to an entity or not.
SELECT release.id AS release_id,
       observation.source_id,
       sha256_hex(observation.id) AS observation_id,
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
       config.source_kind
FROM ops.release AS release
JOIN ops.batch AS batch ON batch.id = release.batch_id
JOIN onboarding.run AS run ON run.id = ANY (batch.run_ids)
JOIN onboarding.approval AS approval
  ON approval.id = run.state ->> 'approval_id' AND approval.decision = 'approved'
JOIN onboarding.mapping_config AS config ON config.config_hash = approval.config_hash
JOIN evidence.observation AS observation
  ON observation.config_hash = config.config_hash AND observation.source_id = run.source_id
JOIN ontology.concept AS concept ON concept.id = observation.concept_id
LEFT JOIN identity.membership AS membership
  ON membership.batch_id = release.batch_id
 AND membership.source_id = observation.source_id
 AND membership.record_id = observation.record_id
