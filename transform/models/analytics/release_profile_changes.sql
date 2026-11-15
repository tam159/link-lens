-- Profiles added, removed and changed between each release and the one before
-- it. A profile is unchanged when its entity and its profile version are the
-- same. The first release has no predecessor, so all its profiles are added.
WITH ordered AS (
    SELECT release_id, lag(release_id) OVER (ORDER BY release_id) AS previous_release_id
    FROM {{ ref('release') }}
),
cur AS (
    SELECT ordered.release_id, profile.entity_id, profile.profile_version
    FROM ordered
    JOIN {{ ref('profile') }} AS profile ON profile.release_id = ordered.release_id
),
prev AS (
    SELECT ordered.release_id, profile.entity_id, profile.profile_version
    FROM ordered
    JOIN {{ ref('profile') }} AS profile ON profile.release_id = ordered.previous_release_id
),
compared AS (
    SELECT coalesce(cur.release_id, prev.release_id) AS release_id,
           cur.entity_id AS cur_entity,
           prev.entity_id AS prev_entity,
           cur.profile_version AS cur_version,
           prev.profile_version AS prev_version
    FROM cur
    FULL JOIN prev ON prev.release_id = cur.release_id AND prev.entity_id = cur.entity_id
)
SELECT ordered.release_id,
       ordered.previous_release_id,
       count(*) FILTER (WHERE compared.cur_entity IS NOT NULL AND compared.prev_entity IS NULL) AS profiles_added,
       count(*) FILTER (WHERE compared.cur_entity IS NULL AND compared.prev_entity IS NOT NULL) AS profiles_removed,
       count(*) FILTER (WHERE compared.cur_version <> compared.prev_version) AS profiles_changed,
       count(*) FILTER (WHERE compared.cur_version = compared.prev_version) AS profiles_unchanged
FROM ordered
LEFT JOIN compared ON compared.release_id = ordered.release_id
GROUP BY ordered.release_id, ordered.previous_release_id
