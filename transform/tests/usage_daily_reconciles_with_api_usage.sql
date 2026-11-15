-- Every counted call is in usage_daily, once, and in usage_monthly.
select 'usage_daily' as model, daily.calls, stored.calls as stored
from (select coalesce(sum(calls), 0) as calls from {{ ref('usage_daily') }}) as daily,
     (select coalesce(sum(calls), 0) as calls from {{ source('access', 'api_usage') }}) as stored
where daily.calls <> stored.calls
union all
select 'usage_monthly', monthly.calls, stored.calls
from (select coalesce(sum(calls), 0) as calls from {{ ref('usage_monthly') }}) as monthly,
     (select coalesce(sum(calls), 0) as calls from {{ source('access', 'api_usage') }}) as stored
where monthly.calls <> stored.calls
