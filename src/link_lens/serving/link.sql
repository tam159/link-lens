-- Identity links of a release. A link is a rule proposal until it is reviewed;
-- its score is a rule score, not a probability.
SELECT release.id AS release_id,
       sha256_hex(link.link_id) AS link_id,
       link.entity_key AS entity_id,
       link.rule,
       link.rule_version,
       link.score,
       link.score_kind,
       link.threshold,
       link.status,
       link.human_review_status,
       link.a_source_id,
       sha256_hex(link.a_record_id) AS a_record_id,
       link.b_source_id,
       sha256_hex(link.b_record_id) AS b_record_id,
       link.evidence
FROM ops.release AS release
JOIN identity.link AS link ON link.batch_id = release.batch_id
