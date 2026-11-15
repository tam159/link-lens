-- Entities of a batch by how many sources support them.
SELECT batch_id,
       supporting_sources,
       count(*) AS entities,
       sum(records)::bigint AS records
FROM (
    SELECT batch_id, entity_id,
           count(DISTINCT source_id) AS supporting_sources,
           count(*) AS records
    FROM {{ ref('stg_identity__membership') }}
    GROUP BY batch_id, entity_id
) AS per_entity
GROUP BY batch_id, supporting_sources
