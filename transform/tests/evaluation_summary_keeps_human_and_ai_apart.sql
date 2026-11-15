-- Labels counted per kind of review equal the stored labels of that kind, so
-- no human label is counted as an AI label or the other way round, and none
-- is lost. The summary has no row that adds the two kinds together.
select counted.review_kind, counted.labels, stored.labels as stored
from (select review_kind, sum(sample_size) as labels
      from {{ ref('evaluation_summary') }} group by review_kind) as counted
full join (select case kind when 'human_label' then 'human' else 'ai' end as review_kind,
                  count(*) as labels
           from {{ source('ops', 'evaluation') }}
           where kind in ('human_label', 'ai_label') group by 1) as stored
  on stored.review_kind = counted.review_kind
where counted.labels is distinct from stored.labels
   or coalesce(counted.review_kind, stored.review_kind) not in ('human', 'ai')
