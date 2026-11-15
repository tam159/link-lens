-- Review labels per worksheet, with human review and AI audit as separate rows.
-- `review_kind` is part of every row's key: a human label and an AI label are
-- different activities and are never added into one figure. `share_yes` is
-- measured on the labelled sample only; `sample_size` and the dates say how
-- large and how old that sample is. An AI audit is not a human evaluation.
SELECT CASE label.evaluation_kind WHEN 'human_label' THEN 'human' ELSE 'ai' END AS review_kind,
       label.worksheet_id,
       coalesce(worksheet.worksheet_kind,
                CASE worksheet.evaluation_kind WHEN 'enhancement_worksheet' THEN 'enhancement' END,
                'not recorded') AS worksheet_kind,
       count(*) AS sample_size,
       count(*) FILTER (WHERE label.verdict = 'yes') AS verdict_yes,
       count(*) FILTER (WHERE label.verdict = 'no') AS verdict_no,
       count(*) FILTER (WHERE label.verdict NOT IN ('yes', 'no') OR label.verdict IS NULL) AS verdict_unsure,
       CASE WHEN count(*) FILTER (WHERE label.verdict IN ('yes', 'no')) > 0
            THEN round(count(*) FILTER (WHERE label.verdict = 'yes')::numeric
                       / count(*) FILTER (WHERE label.verdict IN ('yes', 'no')), 4) END AS share_yes,
       count(DISTINCT label.reviewer) AS reviewers,
       min(label.labelled_at) AS first_labelled_at,
       max(label.labelled_at) AS last_labelled_at
FROM {{ ref('stg_ops__evaluation') }} AS label
LEFT JOIN {{ ref('stg_ops__evaluation') }} AS worksheet
       ON worksheet.evaluation_id = label.worksheet_id
      AND worksheet.evaluation_kind IN ('worksheet', 'enhancement_worksheet')
WHERE label.evaluation_kind IN ('human_label', 'ai_label')
GROUP BY 1, label.worksheet_id, 3
