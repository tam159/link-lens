-- ops.evaluation, renamed and cast only.
SELECT id AS evaluation_id,
       kind AS evaluation_kind,
       worksheet_id,
       item_id,
       verdict,
       reviewer,
       review_type,
       labelled_at,
       batch_id,
       extra ->> 'kind' AS worksheet_kind
FROM {{ source('ops', 'evaluation') }}
