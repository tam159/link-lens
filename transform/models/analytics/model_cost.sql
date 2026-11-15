-- Model calls per experiment, kind of call, stage, model and outcome, with the
-- tokens and the cost recorded when each call ran. A call whose tokens were
-- not reported is counted in `unknown_usage_calls` and adds nothing to the
-- sums: unknown is not zero. An attempt that reserved budget and left no usage
-- receipt is a call too, of kind `attempt_without_receipt`.
--
-- The calls here are the calls `link-lens usage` counts. The costs are not its
-- list-price estimate: that report prices saved responses with a rates file,
-- neither of which SQL can read. `recorded_cost_usd` is what was calculated
-- when the call ran, and `budget_charge_usd` what the budget was charged.
WITH receipts AS (
    SELECT coalesce(event.experiment_id, run.experiment_id, 'terra-baseline') AS experiment_id,
           event.event_kind,
           coalesce(event.stage, 'unknown') AS stage,
           event.model,
           coalesce(event.event_status, 'unknown') AS event_status,
           event.input_tokens,
           event.output_tokens,
           event.calculated_cost_usd,
           event.budget_charge_usd
    FROM {{ ref('stg_ops__event') }} AS event
    LEFT JOIN {{ ref('stg_onboarding__run') }} AS run ON run.run_id = event.owner_id
    WHERE event.event_kind IN ('model_usage', 'triage_usage', 'enhancement_usage')
),
without_receipt AS (
    SELECT attempt.experiment_id,
           'attempt_without_receipt' AS event_kind,
           coalesce(attempt.stage, 'unknown') AS stage,
           attempt.model,
           'receipt_missing' AS event_status,
           NULL::bigint AS input_tokens,
           NULL::bigint AS output_tokens,
           NULL::double precision AS calculated_cost_usd,
           attempt.charge_usd AS budget_charge_usd
    FROM {{ ref('stg_ops__model_call') }} AS attempt
    WHERE attempt.stage IS DISTINCT FROM 'legacy_attempts'
      AND NOT EXISTS (
          SELECT 1 FROM {{ ref('stg_ops__event') }} AS event
          WHERE event.reservation_id = attempt.model_call_id
      )
)
SELECT experiment_id,
       event_kind,
       stage,
       model,
       event_status,
       count(*) AS calls,
       count(*) FILTER (WHERE input_tokens IS NOT NULL
                          AND output_tokens IS NOT NULL) AS known_usage_calls,
       count(*) FILTER (WHERE input_tokens IS NULL
                           OR output_tokens IS NULL) AS unknown_usage_calls,
       sum(input_tokens)::bigint AS input_tokens,
       sum(output_tokens)::bigint AS output_tokens,
       count(calculated_cost_usd) AS calls_with_recorded_cost,
       sum(calculated_cost_usd) AS recorded_cost_usd,
       sum(budget_charge_usd) AS budget_charge_usd
FROM (SELECT * FROM receipts UNION ALL SELECT * FROM without_receipt) AS calls
GROUP BY experiment_id, event_kind, stage, model, event_status
