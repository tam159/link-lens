-- Addresses of a profile. One source record's address fields stay together.
SELECT release.id AS release_id,
       profile.entity_key AS entity_id,
       address.position,
       address.role,
       address.source_id,
       sha256_hex(address.record_id) AS record_id,
       address.detail -> 'fields' AS fields
FROM {{ source('ops', 'release') }} AS release
JOIN {{ source('identity', 'profile') }} AS profile ON profile.batch_id = release.batch_id
JOIN {{ source('identity', 'profile_address') }} AS address ON address.profile_id = profile.id
