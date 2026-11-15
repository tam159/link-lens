-- ops.model_call, renamed and cast only.
SELECT id AS model_call_id,
       experiment_id,
       caller_id,
       stage,
       model,
       status AS call_status,
       input_tokens,
       output_tokens,
       reservation_usd,
       charge_usd,
       created_at
FROM {{ source('ops', 'model_call') }}
