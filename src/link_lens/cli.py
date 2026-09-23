"""Reproducible commands; graph execution always uses Agent Server checkpoints."""

import json
from pathlib import Path

import typer
from langgraph_sdk import get_sync_client

from . import evaluation, exports, ingestion, store
from .contracts import SourceRequest, StrictModel
from .settings import settings

app = typer.Typer(no_args_is_help=True)


def show(value):
    typer.echo(json.dumps(value, indent=2, ensure_ascii=False, default=str))


def client():
    return get_sync_client(url=settings().api_url)


@app.command()
def discover(recheck_from: str | None = None, revision: str | None = None):
    """Discover afresh, or recheck a saved catalogue without new model calls."""
    if bool(recheck_from) != bool(revision):
        raise typer.BadParameter("Use --recheck-from and --revision together")
    result = (
        ingestion.recheck_discovery(recheck_from, revision)
        if recheck_from
        else ingestion.discover()
    )
    show(
        {
            "unique_records": result["unique_records"],
            "shortlist": len(result["shortlist"]),
            "portfolio_in_shortlist": [
                r["slug"]
                for r in result["shortlist"]
                if r["slug"] in ingestion.PORTFOLIO
            ],
        }
    )


@app.command()
def register(dataset: str, resource: str | None = None):
    """Download an immutable snapshot and create a run, without model calls."""
    source, snapshot = ingestion.register(
        SourceRequest(dataset_id=dataset, resource_id=resource)
    )
    show(ingestion.new_run(source, snapshot))


@app.command()
def onboard(run_id: str):
    """Start a durable graph thread; inspect progress with runs or Agent Inbox."""
    run = store.require("runs", run_id)
    if run.get("thread_id"):
        raise typer.BadParameter(
            "This run already has a thread; review or inspect it instead of duplicating execution"
        )
    c = client()
    thread = c.threads.create(
        metadata={
            "application": "link-lens",
            "onboarding_run_id": run_id,
            "source": run["source_slug"],
        }
    )
    run["thread_id"] = thread["thread_id"]
    store.put("runs", run_id, run, run["source_id"], "onboarding")
    result = c.runs.create(
        thread["thread_id"],
        "onboard",
        input={"run_id": run_id, "feedback": run.get("carried_feedback", "none")},
        config={"recursion_limit": 40},
    )
    show(
        {
            "run_id": run_id,
            "thread_id": thread["thread_id"],
            "server_run_id": result["run_id"],
        }
    )


@app.command()
def recover(run_id: str, feedback: str = typer.Option(..., "--feedback")):
    """Prepare a linked replacement without model calls; start it with onboard."""
    from .recovery import prepare_recovery

    try:
        run = prepare_recovery(run_id, feedback)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    show(
        {
            "run_id": run["id"],
            "supersedes_run_id": run["supersedes_run_id"],
            "status": run["status"],
            "thread_id": run.get("thread_id"),
            "next_command": f"uv run link-lens onboard {run['id']}"
            if not run.get("thread_id")
            else None,
        }
    )


@app.command()
def portfolio(start: bool = False):
    """Register the six only if present in the computed shortlist. --start spends API tokens."""
    shortlist = store.require("batches", "discovery")["shortlist"]
    by_slug = {r["slug"]: r for r in shortlist}
    missing = set(ingestion.PORTFOLIO) - set(by_slug)
    if missing:
        raise typer.BadParameter(
            "Portfolio is not fully in generated shortlist: " + str(missing)
        )
    for slug in ingestion.PORTFOLIO:
        existing = [
            r
            for r in store.listing("runs")
            if r["source_slug"] == slug
            and r.get("experiment_id", "terra-baseline") == settings().experiment_id
        ]
        if existing:
            show(
                {
                    "source": slug,
                    "existing_run_id": existing[-1]["id"],
                    "status": existing[-1]["status"],
                }
            )
            continue
        source, snapshot = ingestion.register(
            SourceRequest(dataset_id=by_slug[slug]["dataset_id"])
        )
        run = ingestion.new_run(source, snapshot)
        show({"source": slug, "run_id": run["id"]})
        if start:
            onboard(run["id"])


@app.command()
def runs(run_id: str | None = None):
    if run_id:
        show(store.require("runs", run_id))
    else:
        show(
            [
                {
                    k: r.get(k)
                    for k in [
                        "id",
                        "source_slug",
                        "status",
                        "version",
                        "model_calls",
                        "thread_id",
                        "error",
                    ]
                }
                for r in store.listing("runs")
            ]
        )


@app.command()
def review(run_id: str, decision: str, feedback: str = ""):
    """Human CLI equivalent of Inbox Accept/Respond/Ignore; never edits mappings."""
    run = store.require("runs", run_id)
    if run["status"] != "waiting_for_human":
        raise typer.BadParameter("Run is not awaiting review")
    mapping = store.require("mappings", run["mapping_id"])
    if decision not in ("accept", "respond", "ignore"):
        raise typer.BadParameter("Use accept, respond, or ignore")
    response = {
        "type": "response" if decision == "respond" else decision,
        "args": feedback
        if decision == "respond"
        else {"config_hash": mapping["config_hash"]},
    }
    show(
        client().runs.create(
            run["thread_id"], "onboard", command={"resume": [response]}
        )
    )


@app.command()
def assemble(
    run_ids: list[str],
    minimum_profiles: int = 50,
    cohort_pool_size: int | None = None,
    baseline_batch_id: str | None = None,
):
    from .pipeline import assemble as build

    show(build(run_ids, minimum_profiles, cohort_pool_size, baseline_batch_id))


@app.command()
def export(
    output: Path = Path("outputs"),
    batch_id: str | None = None,
    experiment_id: str | None = None,
):
    show(exports.export(output, batch_id, experiment_id or settings().experiment_id))


@app.command()
def worksheet(
    kind: str,
    batch_id: str = "discovery",
    output: Path = Path("review-worksheet.json"),
    seed: int = 159,
):
    if kind not in ("triage", "links"):
        raise typer.BadParameter("Use triage or links")
    if batch_id == "discovery":
        batch_id = store.current_discovery(settings().experiment_id)["id"]
    packet = evaluation.worksheet(kind, batch_id, seed)
    exports.write_json(output, packet)
    from .review_ui import prepare_review_page

    prepare_review_page(packet, output.with_suffix(".html"))
    show(
        {
            "worksheet_id": packet["id"],
            "path": str(output),
            "items": len(packet["items"]),
        }
    )


@app.command()
def import_labels(path: Path, unreviewed: bool = False, review_note: str | None = None):
    """Import completed fields in an exported worksheet; blank rows remain unknown."""
    packet = json.loads(path.read_text())
    if packet.get("review_type") == "ai_assisted":
        raise typer.BadParameter(
            "Use import-ai-audit for AI judgments; these are not human labels."
        )
    labels = [
        {k: r[k] for k in ["item_id", "verdict", "reviewer", "evidence"]}
        for r in packet["items"]
        if r.get("verdict")
    ]
    if unreviewed and not review_note:
        raise typer.BadParameter("--unreviewed requires --review-note")
    artifact = store.blob(path.read_bytes(), "application/json", path.name)
    store.event(
        packet["id"],
        "label_submission",
        {
            "artifact_id": artifact,
            "reviewed": not unreviewed,
            "review_note": review_note,
        },
    )
    show(
        evaluation.import_labels(
            packet["id"], labels, reviewed=not unreviewed, review_note=review_note
        )
    )


@app.command()
def import_ai_audit(path: Path):
    """Import an explicitly AI-assisted audit without changing human labels."""
    packet = json.loads(path.read_text())
    if packet.get("review_type") != "ai_assisted":
        raise typer.BadParameter("Expected review_type=ai_assisted")
    artifact = store.blob(path.read_bytes(), "application/json", path.name)
    labels = [
        {k: r[k] for k in ["item_id", "verdict", "reviewer", "evidence"]}
        for r in packet["items"]
    ]
    show(evaluation.import_ai_labels(packet["id"], labels, evidence_artifact=artifact))


@app.command()
def evaluation_report(worksheet_id: str):
    show(evaluation.report(worksheet_id))


@app.command()
def smoke_model():
    """One small live structured-output call; token usage is recorded like onboarding."""
    from .llm import call

    class Smoke(StrictModel):
        result: str

    run = ingestion.new_run(
        {"id": "connectivity-test", "slug": "connectivity-test"},
        {"id": "connectivity-test"},
    )
    result = call(
        run["id"], Smoke, "Return result = tool calling works.", "connectivity"
    )
    updated = store.require("runs", run["id"])
    updated["status"] = "connectivity_passed"
    store.put("runs", run["id"], updated, run["source_id"], "connectivity")
    show(
        {
            "result": result.model_dump(),
            "run_id": run["id"],
            "input_tokens": updated["input_tokens"],
            "output_tokens": updated["output_tokens"],
            "usage_has_estimates": updated["usage_has_estimates"],
        }
    )


@app.command()
def usage(experiment_id: str | None = None):
    """Estimate experiment costs using the same saved rates as cost-summary.json."""
    from .pricing import collect, estimate

    experiment_id = experiment_id or settings().experiment_id
    report = estimate(collect(experiment_id))
    show(
        {
            "experiment_id": experiment_id,
            **{
                k: v
                for k, v in report.items()
                if k not in {"pricing_snapshot", "call_details"}
            },
        }
    )


@app.command()
def freeze(output: Path = Path("demo/frozen.zip")):
    from .frozen import freeze as save

    show(save(output))


@app.command()
def thaw(path: Path = Path("demo/frozen.zip")):
    from .frozen import thaw as restore

    show(restore(path))
