from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_prefix="LINK_LENS_"
    )
    database_url: str = "postgresql+psycopg://linklens:linklens@localhost:5439/linklens"
    artifact_dir: Path = Path("artifacts")
    ontology_path: Path = Path("firmable_ontology.yaml")
    model: str = "gpt-5.6-luna"
    experiment_id: str = "jev-luna-v1"
    triage_model: str = "typesafe/jev-1.13"
    triage_workers: int = 6
    sandbox_url: str = "http://localhost:8091"
    sandbox_token: str = "local-development-only"
    api_url: str = "http://localhost:2024"
    max_model_calls: int = 12
    max_python_calls: int = 8
    max_mapping_versions: int = 3
    max_input_tokens: int = 100_000
    max_output_tokens: int = 24_000
    max_active_seconds: int = 900
    max_cost_usd: float = 10.0
    input_usd_per_million: float | None = None
    output_usd_per_million: float | None = None
    pricing_basis: str = "unknown; no provider rates configured"
    sample_pool_size: int = 5000
    csv_prefix_bytes: int = 8_388_608
    reviewer: str = "local-user"


@lru_cache
def settings() -> Settings:
    return Settings()
