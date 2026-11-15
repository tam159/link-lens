-- Where a claim comes from: its record's exact locator, the snapshot, the
-- source and the licence. Attribution travels with every claim.
SELECT release.id AS release_id,
       observation.source_id,
       observation.id AS observation_key,
       sha256_hex(observation.id) AS observation_id,
       sha256_hex(observation.record_id) AS record_id,
       record.sheet,
       record.row_no,
       record.locator,
       record.snapshot_id,
       snapshot.format,
       snapshot.observed_at AS snapshot_observed_at,
       snapshot.observed_at_basis AS snapshot_observed_at_basis,
       snapshot.retrieved_at,
       snapshot.licence,
       snapshot.licence_url,
       source.title AS source_title,
       source.publisher,
       source.portal
FROM ops.release AS release
JOIN ops.batch AS batch ON batch.id = release.batch_id
JOIN onboarding.run AS run ON run.id = ANY (batch.run_ids)
JOIN onboarding.approval AS approval
  ON approval.id = run.state ->> 'approval_id' AND approval.decision = 'approved'
JOIN evidence.observation AS observation
  ON observation.config_hash = approval.config_hash AND observation.source_id = run.source_id
JOIN evidence.source_record AS record
  ON record.source_id = observation.source_id AND record.id = observation.record_id
JOIN catalog.snapshot AS snapshot ON snapshot.id = record.snapshot_id
JOIN catalog.source AS source ON source.id = observation.source_id
