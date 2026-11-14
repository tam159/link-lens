-- Sources of a release, with the licence of the snapshot each run used.
SELECT release.id AS release_id,
       source.id AS source_id,
       source.title,
       source.publisher,
       source.portal,
       source.slug,
       run.id AS run_id,
       snapshot.id AS snapshot_id,
       snapshot.licence,
       snapshot.licence_url,
       snapshot.retrieved_at
FROM ops.release AS release
JOIN ops.batch AS batch ON batch.id = release.batch_id
JOIN onboarding.run AS run ON run.id = ANY (batch.run_ids)
JOIN catalog.source AS source ON source.id = run.source_id
LEFT JOIN catalog.snapshot AS snapshot ON snapshot.id = run.snapshot_id
