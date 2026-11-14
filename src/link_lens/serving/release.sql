-- Releases, newest last. A release names the batch and ontology version clients see.
SELECT release.id AS release_id,
       release.batch_id,
       sha256_hex(release.ontology_hash) AS ontology_hash,
       release.released_by,
       release.released_at,
       release.notes,
       batch.kind AS batch_kind,
       batch.experiment_id,
       release.id = max(release.id) OVER () AS is_latest
FROM ops.release AS release
JOIN ops.batch AS batch ON batch.id = release.batch_id
