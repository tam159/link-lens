-- One row per profile field, with the observation it was selected from and
-- every alternative that was not selected.
SELECT release.id AS release_id,
       profile.entity_key AS entity_id,
       field.position,
       field.concept_name AS concept,
       field.status,
       -- The value as the profile states it, which may be a number. `value_text`
       -- is the same value when it is text, and is what search matches on.
       field.detail -> 'value' AS value,
       field.value AS value_text,
       field.detail -> 'values' AS "values",
       field.observation_source_id,
       sha256_hex(field.observation_id) AS observation_id,
       field.detail ->> 'decision' AS decision,
       field.detail ->> 'temporal_caveat' AS temporal_caveat,
       field.detail -> 'confidence' AS confidence,
       'uncalibrated mapping/source judgements' AS confidence_kind,
       field.detail -> 'provenance' AS provenance,
       field.detail -> 'alternatives' AS alternatives
FROM {{ source('ops', 'release') }} AS release
JOIN {{ source('identity', 'profile') }} AS profile ON profile.batch_id = release.batch_id
JOIN {{ source('identity', 'profile_field') }} AS field ON field.profile_id = profile.id
