-- Calls, tokens and recorded cost in model_cost equal the usage events, plus
-- the budget attempts that left no receipt. Nothing is dropped or counted twice.
with model as (
    select coalesce(sum(calls) filter (where event_kind <> 'attempt_without_receipt'), 0) as calls,
           coalesce(sum(calls) filter (where event_kind = 'attempt_without_receipt'), 0) as attempts,
           coalesce(sum(input_tokens), 0) as input_tokens,
           coalesce(sum(recorded_cost_usd), 0) as cost,
           coalesce(sum(unknown_usage_calls) filter (where event_kind <> 'attempt_without_receipt'), 0) as unknown
    from {{ ref('model_cost') }}
),
stored as (
    select count(*) as calls,
           coalesce(sum(input_tokens), 0) as input_tokens,
           coalesce(sum(calculated_cost_usd), 0) as cost,
           count(*) filter (where input_tokens is null or output_tokens is null) as unknown
    from {{ source('ops', 'event') }}
    where kind in ('model_usage', 'triage_usage', 'enhancement_usage')
),
missing as (
    select count(*) as attempts
    from {{ source('ops', 'model_call') }} as attempt
    where attempt.stage is distinct from 'legacy_attempts'
      and not exists (
          select 1 from {{ source('ops', 'event') }} as event
          where event.extra ->> 'reservation_id' = attempt.id
      )
)
select model.*, stored.calls as stored_calls, missing.attempts as stored_attempts
from model, stored, missing
where model.calls <> stored.calls
   or model.attempts <> missing.attempts
   or model.input_tokens <> stored.input_tokens
   or model.unknown <> stored.unknown
   or abs(model.cost - stored.cost) > 1e-9
