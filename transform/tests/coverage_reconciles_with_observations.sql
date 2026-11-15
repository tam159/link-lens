-- Observations counted per source and per concept equal the stored observations.
select 'source_coverage' as model, counted.observations, stored.observations as stored
from (select coalesce(sum(observations), 0) as observations from {{ ref('source_coverage') }}) as counted,
     (select count(*) as observations
      from {{ source('evidence', 'observation') }} as observation
      join {{ source('catalog', 'source') }} as source
        on source.id = observation.source_id and source.kind = 'registered') as stored
where counted.observations <> stored.observations
union all
select 'concept_usage', counted.observations, stored.observations
from (select coalesce(sum(observations), 0) as observations from {{ ref('concept_usage') }}) as counted,
     (select count(*) as observations from {{ source('evidence', 'observation') }}) as stored
where counted.observations <> stored.observations
