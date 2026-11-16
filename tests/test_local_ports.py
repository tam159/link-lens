"""The local stack's host ports: one set of defaults in settings, Compose and the dashboards."""

import json
import re
from pathlib import Path

import yaml

from link_lens.settings import Settings

ROOT = Path(__file__).resolve().parents[1]

# Compose service -> (settings field, port inside the network)
PUBLISHED = {
    "frontend": ("inbox_port", 3000),
    "backend": ("backend_port", 2024),
    "postgres": ("postgres_port", 5432),
    "sandbox-controller": ("sandbox_port", 8091),
    "product": ("product_port", 8100),
    "admin": ("console_port", 8200),
    "dagster-webserver": ("dagster_port", 3070),
    "dbt-docs": ("dbt_docs_port", 3090),
    "grafana": ("grafana_port", 3080),
}


def defaults():
    return Settings(_env_file=None)


def test_compose_publishes_each_service_on_its_configurable_port():
    services = yaml.safe_load((ROOT / "compose.yaml").read_text())["services"]
    config = defaults()
    for service, (field, inside) in PUBLISHED.items():
        variable = "LINK_LENS_" + field.upper()
        expected = f"127.0.0.1:${{{variable}:-{getattr(config, field)}}}:{inside}"
        assert services[service]["ports"] == [expected], service
    published = [
        port for service in services.values() for port in service.get("ports", [])
    ]
    assert len(published) == len(PUBLISHED)
    assert all(port.startswith("127.0.0.1:") for port in published)


def test_ports_are_distinct_and_outside_the_ephemeral_range():
    config = defaults()
    ports = [getattr(config, field) for field, _ in PUBLISHED.values()]
    assert len(set(ports)) == len(ports)
    assert all(1024 < port < 32768 for port in ports)


def test_addresses_follow_the_ports_unless_set(monkeypatch):
    for variable in ("LINK_LENS_PRODUCT_URL", "LINK_LENS_DATABASE_URL"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("LINK_LENS_PRODUCT_PORT", "19110")
    monkeypatch.setenv("LINK_LENS_POSTGRES_PORT", "19102")
    monkeypatch.setenv("LINK_LENS_INBOX_URL", "http://inbox.example")
    config = Settings(_env_file=None)
    assert config.product_url == "http://localhost:19110"
    assert config.database_url.endswith("@localhost:19102/linklens")
    assert config.inbox_url == "http://inbox.example"


def test_compose_passes_the_link_ports_with_the_same_defaults():
    services = yaml.safe_load((ROOT / "compose.yaml").read_text())["services"]
    config = defaults()
    for service, fields in {
        "admin": ("dagster_port", "inbox_port", "grafana_port", "product_port"),
        "dagster-webserver": ("dagster_port", "inbox_port"),
    }.items():
        environment = services[service]["environment"]
        for field in fields:
            variable = "LINK_LENS_" + field.upper()
            assert environment[variable] == f"${{{variable}:-{getattr(config, field)}}}"
    backend = services["backend"]["environment"]["LINK_LENS_API_URL"]
    assert backend == f"http://localhost:${{LINK_LENS_BACKEND_PORT:-{config.backend_port}}}"


def test_dashboard_links_default_to_the_local_ports():
    config = defaults()
    expected = {
        "product_url": f"http://localhost:{config.product_port}",
        "dagster_url": f"http://localhost:{config.dagster_port}",
        "inbox_url": f"http://localhost:{config.inbox_port}",
    }
    for path in sorted((ROOT / "deploy/grafana/dashboards").glob("*.json")):
        variables = {
            item["name"]: item["query"]
            for item in json.loads(path.read_text())["templating"]["list"]
            if item["name"] in expected
        }
        assert variables == expected, path.name


def test_env_example_lists_every_port_with_its_default():
    text = (ROOT / ".env.example").read_text()
    config = defaults()
    for field, _ in PUBLISHED.values():
        variable = "LINK_LENS_" + field.upper()
        assert re.search(rf"^{variable}={getattr(config, field)}$", text, re.M), variable
