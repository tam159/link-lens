-- catalog.source, renamed and cast only.
SELECT id AS source_id,
       kind AS source_kind,
       title AS source_title,
       publisher,
       portal,
       slug,
       created_at
FROM {{ source('catalog', 'source') }}
