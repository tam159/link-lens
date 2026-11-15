-- Profile fields of each release by concept and status: how many have one
-- selected value, several values, or none that could be resolved.
SELECT release_id,
       concept,
       count(*) AS fields,
       count(*) FILTER (WHERE status = 'selected') AS selected,
       count(*) FILTER (WHERE status = 'multiple_values') AS multiple_values,
       count(*) FILTER (WHERE status = 'unresolved') AS unresolved
FROM {{ ref('profile_field') }}
GROUP BY release_id, concept
