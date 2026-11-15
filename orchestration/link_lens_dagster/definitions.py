"""What the code location offers: assets, the jobs that select them, and sensors.

The deterministic flow per source is snapshot -> schema_drift check ->
observations. A batch, the dbt models and the two paid requests are their own
jobs. Nothing here records a mapping approval, an ontology promotion or a
release: the sensors react to those rows after a person wrote them.
"""

import dagster as dg

# Absolute imports: the workspace loads this file by path, with the folder
# above the package on the import path.
from link_lens_dagster import alerting, schedules, sensors
from link_lens_dagster.assets.extraction import observations
from link_lens_dagster.assets.identity import identity_batch
from link_lens_dagster.assets.models import dbt, models
from link_lens_dagster.assets.onboarding import onboarding_request, source_catalogue
from link_lens_dagster.assets.snapshots import snapshot
from link_lens_dagster.resources import LangGraph, Pipeline

refresh_source = dg.define_asset_job(
    "refresh_source",
    selection=dg.AssetSelection.assets(snapshot, observations),
    description="Check one source for new bytes; if they changed and still fit the approved mapping, extract them.",
)
extract_observations = dg.define_asset_job(
    "extract_observations",
    selection=dg.AssetSelection.assets(observations),
    description="Extract a source's latest snapshot under its approved mapping.",
)
request_onboarding = dg.define_asset_job(
    "request_onboarding",
    selection=dg.AssetSelection.assets(onboarding_request),
    description="Start an onboarding run for a source's latest snapshot. Model calls follow.",
)
assemble_batch = dg.define_asset_job(
    "assemble_batch",
    selection=dg.AssetSelection.assets(identity_batch),
    description="Assemble a new batch of entities, links and profiles. Serves nobody until released.",
)
build_models = dg.define_asset_job(
    "build_models",
    selection=dg.AssetSelection.assets(models),
    description="Build every dbt model and run every dbt test.",
)

defs = dg.Definitions(
    assets=[
        snapshot,
        observations,
        onboarding_request,
        source_catalogue,
        identity_batch,
        models,
    ],
    jobs=[
        refresh_source,
        extract_observations,
        request_onboarding,
        assemble_batch,
        build_models,
        schedules.check_source_freshness,
        schedules.prune_run_history,
    ],
    asset_checks=[schedules.sources_checked_on_time],
    schedules=[
        schedules.due_sources_schedule(refresh_source),
        schedules.freshness_schedule,
        schedules.weekly_batch_schedule(assemble_batch),
        schedules.retention_schedule,
    ],
    sensors=[
        sensors.registered_sources,
        sensors.approval_sensor(extract_observations),
        sensors.release_sensor(build_models),
        sensors.ontology_promoted,
        sensors.drift_sensor(request_onboarding),
        alerting.alert_run_failed,
        alerting.alert_check_failed,
        alerting.alert_drift,
        alerting.alert_overdue_sources,
        alerting.alert_budget,
    ],
    resources={"pipeline": Pipeline(), "langgraph": LangGraph(), "dbt": dbt},
)
