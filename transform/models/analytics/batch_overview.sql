-- Assembled batches with the counts recorded when they were built, and the
-- releases that serve them. `counted_unlinked` is a count only: why a record
-- stayed unlinked is not stored as rows.
SELECT batch.batch_id,
       batch.batch_kind,
       batch.experiment_id,
       batch.baseline_batch_id,
       batch.runs,
       batch.counted_observations,
       batch.counted_links,
       batch.counted_profiles,
       batch.counted_unlinked,
       batch.recorded_at,
       ARRAY(
           SELECT release.release_id FROM {{ ref('release') }} AS release
           WHERE release.batch_id = batch.batch_id ORDER BY release.release_id
       ) AS release_ids
FROM {{ ref('stg_ops__batch') }} AS batch
WHERE batch.batch_kind IN ('pipeline', 'enhancement')
