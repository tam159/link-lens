-- Links per batch, onboarding runs and profiles per release equal their tables.
select 'identity_link_summary' as model, counted.n, stored.n as stored
from (select coalesce(sum(links), 0) as n from {{ ref('identity_link_summary') }}) as counted,
     (select count(*) as n from {{ source('identity', 'link') }}) as stored
where counted.n <> stored.n
union all
select 'onboarding_run', counted.n, stored.n
from (select count(*) as n from {{ ref('onboarding_run') }}) as counted,
     (select count(*) as n from {{ source('onboarding', 'run') }} where kind = 'onboarding') as stored
where counted.n <> stored.n
union all
select 'release_overview', counted.n, stored.n
from (select coalesce(sum(profiles), 0) as n from {{ ref('release_overview') }}) as counted,
     (select count(*) as n
      from {{ source('ops', 'release') }} as release
      join {{ source('identity', 'profile') }} as profile on profile.batch_id = release.batch_id) as stored
where counted.n <> stored.n
union all
select 'release_profile_changes', counted.n, stored.n
from (select coalesce(sum(profiles_added + profiles_changed + profiles_unchanged), 0) as n
      from {{ ref('release_profile_changes') }}) as counted,
     (select coalesce(sum(profiles), 0) as n from {{ ref('release_overview') }}) as stored
where counted.n <> stored.n
