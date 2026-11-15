-- Calls per client and month against the tier's monthly quota. The quota is the
-- tier's value today, not the one in force when the calls were made.
SELECT date_trunc('month', daily.day)::date AS month,
       daily.client_id,
       daily.client_name,
       daily.tier_id,
       sum(daily.calls)::bigint AS calls,
       tier.monthly_quota,
       CASE WHEN tier.monthly_quota > 0
            THEN round(sum(daily.calls)::numeric / tier.monthly_quota, 4) END AS quota_used
FROM {{ ref('usage_daily') }} AS daily
JOIN {{ ref('stg_access__tier') }} AS tier ON tier.tier_id = daily.tier_id
GROUP BY 1, daily.client_id, daily.client_name, daily.tier_id, tier.monthly_quota
