"""The Grafana dashboards: files that read the reporting models and nothing else."""

import json
import re
from pathlib import Path

import pytest
import yaml
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
DASHBOARDS = sorted((ROOT / "deploy/grafana/dashboards").glob("*.json"))
EXPOSURES = yaml.safe_load(
    (ROOT / "transform/models/analytics/_exposures.yml").read_text()
)["exposures"]


def queries(board):
    return [
        (panel["title"], target["rawSql"])
        for panel in board["panels"]
        for target in panel.get("targets", [])
    ]


def test_there_are_three_dashboards_each_declared_as_an_exposure():
    boards = [json.loads(path.read_text()) for path in DASHBOARDS]
    assert sorted(board["title"] for board in boards) == [
        "Data quality",
        "Product overview",
        "Source health",
    ]
    by_url = {exposure["url"].rsplit("/", 1)[-1]: exposure for exposure in EXPOSURES}
    for path, board in zip(DASHBOARDS, boards):
        assert path.stem == board["uid"]
        exposure = by_url[board["uid"]]
        assert exposure["type"] == "dashboard"
        read = {
            model
            for _, sql in queries(board)
            for model in re.findall(r"analytics\.([a-z_]+)", sql)
        }
        # A dashboard reads exactly the models its exposure names.
        assert {f"ref('{model}')" for model in read} == set(exposure["depends_on"])


@pytest.mark.parametrize("path", DASHBOARDS, ids=lambda path: path.stem)
def test_every_panel_reads_only_reporting_models_as_the_analyst(path, database):
    board = json.loads(path.read_text())
    assert queries(board)
    with database.connect() as connection:
        connection.execute(text("SET LOCAL ROLE linklens_analyst"))
        for title, sql in queries(board):
            relations = re.findall(r"(?:FROM|JOIN)\s+([a-z_]+\.[a-z_]+)", sql)
            assert relations, title
            for relation in relations:
                schema, name = relation.split(".")
                # Never a core table, a serving view or a staging view.
                assert schema == "analytics" and not name.startswith("stg_"), title
            # Grafana fills its time filter in; any true condition will do here.
            runnable = re.sub(r"\$__timeFilter\([^)]*\)\)?", "true", sql)
            assert "$" not in runnable, title
            connection.execute(text(runnable)).all()
        connection.rollback()


def test_a_row_links_to_its_evidence():
    """A source, a concept or a release on a dashboard links to its page."""
    links = {
        link["title"]
        for path in DASHBOARDS
        for panel in json.loads(path.read_text())["panels"]
        for override in panel.get("fieldConfig", {}).get("overrides", [])
        for prop in override["properties"]
        if prop["id"] == "links"
        for link in prop["value"]
    }
    assert {
        "Dataset on its portal",
        "OKF page (needs an API key)",
        "Release tree (needs an API key)",
        "Agent Inbox",
        "Dagster",
    } <= links


def test_grafana_holds_no_secret_and_reads_as_the_analyst_login():
    source = (ROOT / "deploy/grafana/provisioning/datasources/linklens.yml").read_text()
    config = yaml.safe_load(source)["datasources"][0]
    assert config["user"] == "linklens_grafana"
    assert config["secureJsonData"]["password"].startswith("${")
    assert "IN ROLE linklens_analyst" in (ROOT / "deploy/grafana-db.sql").read_text()
    grafana = yaml.safe_load((ROOT / "compose.yaml").read_text())["services"]["grafana"]
    assert grafana["profiles"] == ["dashboards"]
    assert grafana["environment"]["GF_AUTH_ANONYMOUS_ENABLED"] == "false"
    assert grafana["ports"] == ["127.0.0.1:${LINK_LENS_GRAFANA_PORT:-18740}:3080"]
