"""The dbt project as assets: the serving views clients read and the reporting models.

Every dbt model is an asset and every dbt test an asset check. dbt works as its
own database role, `linklens_transform`, never as the orchestrator's.
"""

import os
from pathlib import Path

import dagster as dg
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets

from .snapshots import RETRY

# The dbt project beside this code location; its build files go where the
# process may write, since the project itself may be mounted read-only.
PROJECT_DIR = Path(
    os.environ.get("LINK_LENS_DBT_PROJECT_DIR")
    or Path(__file__).resolve().parents[3] / "transform"
).resolve()
TARGET_DIR = Path(os.environ.get("LINK_LENS_DBT_TARGET_PATH") or PROJECT_DIR / "target")

# The core table that stands for each asset of this code location: a model that
# reads it is downstream of that asset. dbt allows one source per asset key, so
# an asset's other tables, and every table nothing here writes, keep a key of
# their own under `core`.
WRITTEN_BY = {
    ("catalog", "snapshot"): "snapshot",
    ("evidence", "observation"): "observations",
    ("identity", "profile"): "identity_batch",
}


class Translator(DagsterDbtTranslator):
    def get_asset_key(self, dbt_resource_props):
        if dbt_resource_props["resource_type"] == "source":
            written = WRITTEN_BY.get(
                (dbt_resource_props["source_name"], dbt_resource_props["name"])
            )
            if written:
                return dg.AssetKey(written)
            return dg.AssetKey(
                ["core", dbt_resource_props["source_name"], dbt_resource_props["name"]]
            )
        return dg.AssetKey([dbt_resource_props["fqn"][1], dbt_resource_props["name"]])

    def get_group_name(self, dbt_resource_props):
        return dbt_resource_props["fqn"][1]


def manifest():
    """Path of the dbt manifest, parsed again when a project file is newer than it."""
    from link_lens import transform

    path = TARGET_DIR / "manifest.json"
    sources = [
        p
        for p in PROJECT_DIR.rglob("*")
        if p.suffix in {".sql", ".yml"} and TARGET_DIR not in p.parents
    ]
    if not path.exists() or path.stat().st_mtime < max(
        p.stat().st_mtime for p in sources
    ):
        finished = transform.run(
            ["parse"],
            # Parsing connects to nothing; any well-formed address will do.
            url="postgresql://parse@localhost/parse",
            project_dir=PROJECT_DIR,
            env={
                "DBT_TARGET_PATH": str(TARGET_DIR),
                "DBT_LOG_PATH": str(TARGET_DIR / "logs"),
            },
            capture_output=True,
            text=True,
        )
        if finished.returncode != 0:
            raise RuntimeError(
                "dbt could not parse the transform project:\n" + finished.stdout
            )
    return path


project = DbtProject(
    project_dir=PROJECT_DIR, target_path=TARGET_DIR, profiles_dir=PROJECT_DIR
)
dbt = DbtCliResource(project_dir=project)


@dbt_assets(
    manifest=manifest(),
    project=project,
    dagster_dbt_translator=Translator(),
    pool="database",
    retry_policy=RETRY,
)
def models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    """Build the selected dbt models and run their tests, as `link-lens dbt build` does."""
    from link_lens import transform

    # dbt takes its connection from the same database URL as the library.
    os.environ.update(transform.environment())
    os.environ["DBT_LOG_PATH"] = str(TARGET_DIR / "logs")
    yield from dbt.cli(["build"], context=context, target_path=TARGET_DIR).stream()
