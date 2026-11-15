{#
  No two rows share the same values in `columns`. A read model's key is usually
  the release and one or two more columns.
#}
{% test unique_combination(model, columns) %}
select {{ columns | join(', ') }}, count(*) as rows
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1
{% endtest %}
