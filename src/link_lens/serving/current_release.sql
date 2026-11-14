-- The latest release: what "current" means for every other read model.
SELECT release.id AS release_id,
       release.batch_id,
       sha256_hex(release.ontology_hash) AS ontology_hash,
       release.released_by,
       release.released_at
FROM ops.release AS release
ORDER BY release.id DESC
LIMIT 1
