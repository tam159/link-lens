from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_prefix="LINK_LENS_"
    )
    # Host ports of the local stack. compose.yaml publishes each service on
    # 127.0.0.1 at the port of the same name (LINK_LENS_<NAME>_PORT), with the
    # same defaults. They sit in an uncommon block, 18700 to 18740, so they do
    # not clash with other local apps. Change one in .env and recreate the
    # service; the addresses below follow unless they are set themselves.
    inbox_port: int = 18700
    backend_port: int = 18701
    postgres_port: int = 18702
    sandbox_port: int = 18703
    product_port: int = 18710
    console_port: int = 18720
    dagster_port: int = 18730
    dbt_docs_port: int = 18731
    grafana_port: int = 18740
    # Unset, the local Compose database at postgres_port.
    database_url: str = ""
    # A database role every connection of this process takes, such as
    # linklens_orchestrator. Unset, a connection keeps the rights of its login.
    database_role: str | None = None
    artifact_dir: Path = Path("artifacts")
    # "local" keeps artifact bytes under artifact_dir; "s3" writes new ones to an
    # S3-compatible bucket and reads them through a cache under artifact_dir.
    artifact_store: Literal["local", "s3"] = "local"
    artifact_bucket: str | None = None
    artifact_prefix: str = ""
    artifact_endpoint_url: str | None = None
    # Host names the MCP endpoints answer to, such as "data.example.com". Empty
    # leaves the Host header to the proxy in front; every call needs a key either way.
    mcp_allowed_hosts: list[str] = []
    # Signs bundle download links served by the product service itself, which
    # is how a bundle in the local artifact store is downloaded. Unset, each
    # process makes its own secret, so a link works only on the instance that
    # gave it. A bundle in S3 gets a link signed by S3 instead.
    link_secret: str | None = None
    link_ttl_seconds: int = 300
    # The product service. It authenticates, limits and counts on the primary,
    # where a revoked key stops at once, and reads data from the replica when
    # one is given. Both default to database_url. In production each is a login
    # that is only a member of linklens_product.
    product_database_url: str | None = None
    product_replica_url: str | None = None
    # "database" keeps each key's token bucket in PostgreSQL, right for any
    # number of instances; "memory" keeps it in the process, right for one.
    rate_limit_store: Literal["database", "memory"] = "database"
    # /metrics answers only to this bearer token; unset, there is no /metrics.
    metrics_token: str | None = None
    # The dbt project that `link-lens dbt` and the orchestrator run, relative to
    # the working directory like the paths above.
    dbt_project_dir: Path = Path("transform")
    # Who may sign in to the operations console while no identity provider is
    # connected: a JSON object of token -> {"name": ..., "role": ...}, with role
    # engineer, product_owner or admin. A token is a secret a person holds.
    # Empty or not valid JSON, nobody can sign in. For development and one machine.
    admin_users: str = ""
    # Where alerts are posted: an incoming-webhook URL that accepts {"text": ...},
    # as Slack's and most chat tools' do. Unset, an alert is logged and not sent.
    # The URL is a secret and is never logged.
    alert_webhook_url: str | None = None
    # Base addresses used in alert links and by the operations console. Unset,
    # each is http://localhost at its port above.
    dagster_url: str = ""
    inbox_url: str = ""
    # Base addresses the operations console links to.
    dashboards_url: str = ""
    product_url: str = ""
    ontology_path: Path = Path("firmable_ontology.yaml")
    model: str = "gpt-6-luna"
    experiment_id: str = "jev-gpt6-luna-ontology-v1"
    triage_model: str = "typesafe/jev-1.13"
    triage_workers: int = 6
    embedding_model: str = "text-embedding-3-small"
    resolution_model: str = "typesafe/jev-1.13"
    enhancement_max_cost_usd: float = 10.0
    enhancement_workers: int = 6
    enhancement_max_pairs: int = 500
    embedding_batch_size: int = 64
    enhancement_retries: int = 2
    sandbox_url: str = ""
    sandbox_token: str = "local-development-only"
    # The LangGraph backend as the CLI reaches it; review links in the Inbox use
    # it too, so the backend's own value is its address on this machine.
    api_url: str = ""
    max_model_calls: int = 50
    max_python_calls: int = 10
    mapping_max_output_tokens: int = Field(default=16000, ge=7000, le=32000)
    max_mapping_versions: int = 8
    max_input_tokens: int = 9_000_000
    max_output_tokens: int = 2_000_000
    max_active_seconds: int = 900
    max_cost_usd: float = Field(default=10.0, ge=0, allow_inf_nan=False)
    input_usd_per_million: float | None = None
    output_usd_per_million: float | None = None
    pricing_multiplier: float = 1.0
    pricing_basis: str = "unknown; no provider rates configured"
    sample_pool_size: int = 5000
    csv_prefix_bytes: int = 8_388_608
    reviewer: str = "local-user"

    @model_validator(mode="after")
    def local_addresses(self):
        """Fill each address left unset from its host port."""
        defaults = {
            "database_url": "postgresql+psycopg://linklens:linklens@localhost:"
            f"{self.postgres_port}/linklens",
            "api_url": f"http://localhost:{self.backend_port}",
            "sandbox_url": f"http://localhost:{self.sandbox_port}",
            "inbox_url": f"http://localhost:{self.inbox_port}",
            "product_url": f"http://localhost:{self.product_port}",
            "dagster_url": f"http://localhost:{self.dagster_port}",
            "dashboards_url": f"http://localhost:{self.grafana_port}",
        }
        for name, value in defaults.items():
            if not getattr(self, name):
                setattr(self, name, value)
        return self


@lru_cache
def settings() -> Settings:
    return Settings()
