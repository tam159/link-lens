{#
  Every row of the model whose `columns` are all present has a row in `to` with
  the same values in `to_columns` (the same names when not given). The built-in
  relationships test compares one column; read models are keyed by the release
  as well.

  Written as a set difference, so each side is read once. A correlated lookup
  between two large views took minutes where this takes seconds.
#}
{% test exists_in(model, columns, to, to_columns=none) %}
{% set others = to_columns or columns %}
select {{ columns | join(', ') }}
from {{ model }}
where {% for column in columns %}{{ column }} is not null{{ " and " if not loop.last }}{% endfor %}

except
select {{ others | join(', ') }}
from {{ to }}
{% endtest %}
