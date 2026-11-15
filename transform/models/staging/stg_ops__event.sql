-- ops.event, renamed and cast only.
SELECT id AS event_id,
       owner_id,
       kind AS event_kind,
       at AS event_at,
       experiment_id,
       stage,
       model,
       status AS event_status,
       input_tokens,
       output_tokens,
       calculated_cost_usd,
       budget_charge_usd,
       wall_seconds,
       extra ->> 'reservation_id' AS reservation_id
FROM {{ source('ops', 'event') }}
