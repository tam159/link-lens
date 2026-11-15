-- Entities in a release: one row per profile, with its name and identifiers.
-- Identifiers come from the profile's own fields, so they belong to the release.
SELECT release.id AS release_id,
       profile.entity_key AS entity_id,
       profile.id AS profile_id,
       name.value AS display_name,
       (
           SELECT jsonb_object_agg(field.concept_name, field.value)
           FROM {{ source('identity', 'profile_field') }} AS field
           WHERE field.profile_id = profile.id
             AND field.concept_name IN ('entity.abn', 'entity.acn', 'entity.nzbn')
             AND field.value IS NOT NULL
       ) AS identifiers,
       profile.status,
       sha256_hex(profile.profile_version) AS profile_version
FROM {{ source('ops', 'release') }} AS release
JOIN {{ source('identity', 'profile') }} AS profile ON profile.batch_id = release.batch_id
LEFT JOIN {{ source('identity', 'profile_field') }} AS name
       ON name.profile_id = profile.id AND name.concept_name = 'entity.legal_name'
