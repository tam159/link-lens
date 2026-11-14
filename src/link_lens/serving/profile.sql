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
       profile.extra -> 'reconciliation' AS reconciliation
FROM ops.release AS release
JOIN identity.profile AS profile ON profile.batch_id = release.batch_id
