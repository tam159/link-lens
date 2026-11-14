-- One row per profile field, with the observation it was selected from and
-- every alternative that was not selected.
SELECT release.id AS release_id,
       profile.entity_key AS entity_id,
       field.position,
       field.concept_name AS concept,
       field.status,
       field.value,
       field.detail -> 'values' AS "values",
       field.observation_source_id,
       sha256_hex(field.observation_id) AS observation_id,
       field.detail ->> 'decision' AS decision,
       field.detail ->> 'temporal_caveat' AS temporal_caveat,
       field.detail -> 'confidence' AS confidence,
       'uncalibrated mapping/source judgements' AS confidence_kind,
       field.detail -> 'provenance' AS provenance,
       field.detail -> 'alternatives' AS alternatives
FROM ops.release AS release
JOIN identity.profile AS profile ON profile.batch_id = release.batch_id
JOIN identity.profile_field AS field ON field.profile_id = profile.id
