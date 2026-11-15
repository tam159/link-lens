-- A selected profile value of an enum concept is one of its allowed values.
select field.release_id, field.entity_id, field.concept, field.value_text
from {{ ref('profile_field') }} as field
join {{ ref('concept') }} as concept
  on concept.release_id = field.release_id and concept.name = field.concept
where concept.datatype = 'enum'
  and field.value_text is not null
  and not (field.value_text = any (concept.allowed_values))
