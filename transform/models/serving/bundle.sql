-- Bundles a client may download: the latest archive built for each release and
-- client, with where its bytes are. Named scopes such as `demo` are not served.
SELECT DISTINCT ON (bundle.release_id, bundle.client_id)
       bundle.release_id,
       bundle.client_id,
       bundle.scope,
       bundle.source_scope,
       bundle.entity_count,
       bundle.file_count,
       bundle.size_bytes,
       sha256_hex(bundle.artifact_sha) AS sha256,
       sha256_hex(bundle.manifest_sha) AS manifest_sha256,
       artifact.uri,
       bundle.created_at
FROM {{ source('ops', 'release_bundle') }} AS bundle
JOIN {{ source('catalog', 'artifact') }} AS artifact ON artifact.sha256 = bundle.artifact_sha
WHERE bundle.client_id IS NOT NULL
ORDER BY bundle.release_id, bundle.client_id, bundle.id DESC
