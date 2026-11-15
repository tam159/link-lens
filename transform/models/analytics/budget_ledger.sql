-- The budget ledger per experiment, stage, model and state: what was reserved
-- before the calls and what was charged after them. A reservation that was
-- never settled keeps its charge, as the budget does.
SELECT experiment_id,
       coalesce(stage, 'unknown') AS stage,
       model,
       call_status,
       count(*) AS attempts,
       sum(reservation_usd) AS reservation_usd,
       sum(charge_usd) AS charge_usd
FROM {{ ref('stg_ops__model_call') }}
GROUP BY experiment_id, coalesce(stage, 'unknown'), model, call_status
