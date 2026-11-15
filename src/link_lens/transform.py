"""Run dbt on the transform project, against the database the application uses.

dbt reads its connection from `transform/profiles.yml`, which takes the host,
port, user, password and database from `LINK_LENS_DBT_*` variables. `environment`
derives them from the application's database URL, so dbt, the pipeline and an
orchestrator cannot end up on different databases. The profile makes dbt work as
the `linklens_transform` role whatever it logs in as.

This module does not import dbt, which is installed only with the `transform`
dependency group; it runs the `dbt` command of the current environment.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from sqlalchemy.engine import make_url

from .settings import settings


def environment(url=None):
    """The `LINK_LENS_DBT_*` variables for a database URL; the configured one by default."""
    parsed = make_url(url or settings().database_url)
    return {
        "LINK_LENS_DBT_HOST": parsed.host or "localhost",
        "LINK_LENS_DBT_PORT": str(parsed.port or 5432),
        "LINK_LENS_DBT_USER": parsed.username or "",
        "LINK_LENS_DBT_PASSWORD": parsed.password or "",
        "LINK_LENS_DBT_DATABASE": parsed.database or "",
    }


def executable():
    """Path of the `dbt` command in this environment, or None when it is not installed."""
    beside = Path(sys.executable).parent / "dbt"
    return str(beside) if beside.exists() else shutil.which("dbt")


def run(arguments, url=None, project_dir=None, **options):
    """Run `dbt ARGUMENTS` on the transform project; returns the finished process.

    dbt's exit codes: 0 done, 1 a model or a test failed, 2 dbt could not run
    what was asked. `options` go to `subprocess.run`; `env` adds variables.
    """
    dbt = executable()
    if dbt is None:
        raise FileNotFoundError(
            "dbt is not installed in this environment; run "
            "`uv sync --group transform --group orchestration`"
        )
    project = Path(project_dir or settings().dbt_project_dir).resolve()
    if not (project / "dbt_project.yml").exists():
        raise FileNotFoundError(
            f"No dbt project at {project}; run from the repository root"
        )
    variables = {
        **os.environ,
        **environment(url),
        "DBT_PROJECT_DIR": str(project),
        "DBT_PROFILES_DIR": str(project),
        **options.pop("env", {}),
    }
    return subprocess.run([dbt, *arguments], env=variables, **options)


def candidate(schema="serving_next", **options):
    """Build the serving models, and only those, into another schema.

    Everything else stays as it is: the reporting models read the serving models
    by reference, and a build of the whole project with another serving schema
    would point them at the candidate. `options` are those of `run`.
    """
    if not schema.replace("_", "").isalnum():
        raise ValueError(f"Not a schema name: {schema}")
    return run(
        ["run", "--select", "serving", "--vars", f"{{serving_schema: {schema}}}"],
        **options,
    )
