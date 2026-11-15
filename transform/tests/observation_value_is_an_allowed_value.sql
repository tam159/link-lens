-- An observation of an enum concept states one of that concept's allowed values.
-- The values come from the ontology registry through the concept model, so a
-- new ontology version changes what this test accepts without an edit here.
select observation.release_id, observation.source_id, observation.observation_id,
       observation.concept, observation.value
from {{ ref('observation') }} as observation
join {{ ref('concept') }} as concept
  on concept.release_id = observation.release_id and concept.name = observation.concept
where concept.datatype = 'enum'
  and not (observation.value = any (concept.allowed_values))
