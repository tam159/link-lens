"""Asset checks live with the asset they check, so they run in the same step.

snapshot        schema_drift (blocking): the snapshot still fits the approved mapping
observations    observations_have_records, extraction_is_complete
identity_batch  selected_fields_cite_evidence, counts_match_the_batch
dbt models      every dbt test, as a check on the model it tests
"""
