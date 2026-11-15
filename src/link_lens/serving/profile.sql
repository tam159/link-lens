-- Profiles in a release. Statuses and scores are labels, never probabilities.
SELECT release.id AS release_id,
       profile.entity_key AS entity_id,
       profile.id AS profile_id,
       sha256_hex(profile.profile_version) AS profile_version,
       profile.policy_version,
       profile.status,
       profile.uncertainties,
       profile.extra -> 'source_records' AS source_records,
       profile.extra -> 'groups' AS groups,
       profile.extra -> 'reconciliation' AS reconciliation,
       -- The profile exactly as the pipeline wrote it, for rendering its page.
       jsonb_strip_nulls(
           jsonb_build_object(
               'canonical_entity_key', profile.entity_key,
               'profile_version', sha256_hex(profile.profile_version),
               'policy_version', profile.policy_version,
               'status', profile.status
           )
       )
       || CASE WHEN profile.uncertainties IS NULL THEN '{}'::jsonb
               ELSE jsonb_build_object('uncertainties', profile.uncertainties) END
       || profile.extra
       || coalesce(
           (
               SELECT jsonb_build_object('fields', jsonb_object_agg(field.concept_name, field.detail))
               FROM identity.profile_field AS field
               WHERE field.profile_id = profile.id
               HAVING count(*) > 0
           ),
           '{}'::jsonb
       )
       || coalesce(
           (
               SELECT jsonb_build_object('addresses', jsonb_agg(address.detail ORDER BY address.position))
               FROM identity.profile_address AS address
               WHERE address.profile_id = profile.id
               HAVING count(*) > 0
           ),
           '{}'::jsonb
       ) AS document
FROM ops.release AS release
JOIN identity.profile AS profile ON profile.batch_id = release.batch_id
