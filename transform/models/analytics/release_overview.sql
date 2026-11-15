-- What each release serves, counted from the serving models clients read.
SELECT release.release_id,
       release.batch_id,
       release.ontology_hash,
       release.released_by,
       release.released_at,
       release.is_latest,
       (SELECT count(*) FROM {{ ref('source') }} AS s WHERE s.release_id = release.release_id) AS sources,
       (SELECT count(DISTINCT (o.source_id, o.record_id)) FROM {{ ref('observation') }} AS o
        WHERE o.release_id = release.release_id) AS records,
       (SELECT count(*) FROM {{ ref('observation') }} AS o WHERE o.release_id = release.release_id) AS observations,
       (SELECT count(*) FROM {{ ref('entity') }} AS e WHERE e.release_id = release.release_id) AS entities,
       (SELECT count(*) FROM {{ ref('link') }} AS l WHERE l.release_id = release.release_id) AS links,
       (SELECT count(*) FROM {{ ref('profile') }} AS p WHERE p.release_id = release.release_id) AS profiles,
       (SELECT count(*) FROM {{ ref('concept') }} AS c WHERE c.release_id = release.release_id) AS concepts
FROM {{ ref('release') }} AS release
