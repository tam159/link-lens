"""Reproducible commands; graph execution always uses Agent Server checkpoints."""

import json
from pathlib import Path

import typer
from langgraph_sdk import get_sync_client

from . import evaluation, exports, ingestion, store
from .contracts import SourceRequest, StrictModel, content_hash
from .settings import settings

app = typer.Typer(no_args_is_help=True)


# Exit codes, so an orchestrator can tell what happened without reading output:
# 0 the command did its work; 1 it failed; 2 it was called wrongly (Typer's own
# code); 3 it ran and found something that blocks the next step, such as a failed
# gate check or a snapshot the approved mapping cannot read.
EXIT_BLOCKED = 3


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
    from . import refresh

    run = store.require("runs", run_id)
    try:
        show(refresh.start_thread(run, client()))
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


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
    # The configured experiment's discovery, not whichever experiment ran last.
    shortlist = (
        store.current_discovery(settings().experiment_id)
        or store.require("batches", "discovery")
    )["shortlist"]
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
def enhance(
    batch_id: str = typer.Option(..., help="Frozen approved baseline batch"),
    output: Path = Path("outputs/local-run/enhanced-v2"),
    retrieval: str = "hybrid",
    reconcile: bool = True,
    budget: float | None = None,
    max_pairs: int | None = typer.Option(
        None,
        min=0,
        help="Maximum NEW identity pair requests; cached judgments are free",
    ),
    preflight_only: bool = False,
    progress: bool = True,
):
    """Experimental semantic resolution and profile reconciliation (paid inference)."""
    from .enhancement import enhance as build
    from .enhancement_contracts import EnhancementPolicy

    if retrieval not in {"fuzzy", "hybrid"}:
        raise typer.BadParameter("Use fuzzy or hybrid")
    cfg = settings()
    policy = EnhancementPolicy(
        retrieval=retrieval,
        reconcile=reconcile,
        embedding_model=cfg.embedding_model,
        decision_model=cfg.resolution_model,
        explanation_model=cfg.model,
    )
    from .enhancement_progress import Progress

    show(
        build(
            batch_id,
            policy,
            output,
            budget,
            max_pairs=max_pairs,
            preflight_only=preflight_only,
            progress=Progress(progress),
        )
    )


@app.command()
def enhance_worksheet(
    batch_id: str = typer.Option(...),
    output: Path = Path("outputs/local-run/enhancement-review"),
    sample_size: int = 200,
    seed: int = 159,
):
    """Create unlabelled human evaluation worksheets without model calls."""
    from .enhancement import validate_output
    from .enhancement_evaluation import worksheet

    validate_output(output)
    batch = store.require("batches", batch_id)
    result = store.read_json(batch["result_artifact"])
    packet = worksheet(result, sample_size, seed)
    worksheet_id = "enhancement-review-" + content_hash(packet)[:40]
    store.put(
        "evaluations",
        worksheet_id,
        packet,
        batch_id,
        "enhancement_worksheet",
        immutable=True,
    )
    exports.write_json(output / "worksheet.json", packet)
    for split in ("development", "heldout"):
        exports.write_json(
            output / (split + ".json"),
            {
                **packet,
                "items": [i for i in packet["items"] if i["split"] == split],
                "records": [
                    r
                    for r in packet["records"]
                    if (r["source_id"], r["source_record_id"])
                    in {
                        tuple(i[side])
                        for i in packet["items"]
                        if i["split"] == split
                        for side in ("left", "right")
                    }
                ],
                "masked_identifier_controls": [
                    c
                    for c in packet["masked_identifier_controls"]
                    if c["split"] == split
                ],
            },
        )
    show(
        {
            "worksheet_id": worksheet_id,
            "path": str(output / "worksheet.json"),
            "items": len(packet["items"]),
            "status": "human_labels_pending",
        }
    )


@app.command()
def enhance_evaluate(
    batch_id: str = typer.Option(...),
    labels: Path = typer.Option(
        ...,
        help="Combined worksheet with human labels; include both splits for leakage checks",
    ),
    split: str = "heldout",
    output: Path = Path("outputs/local-run/enhancement-review/report.json"),
):
    """Evaluate frozen predictions against human labels, never AI audit labels."""
    from .enhancement import validate_output
    from .enhancement_evaluation import evaluate

    validate_output(output)
    batch = store.require("batches", batch_id)
    result = store.read_json(batch["result_artifact"])
    packet = json.loads(labels.read_text())
    report = evaluate(result, packet, split)
    evidence_id = store.json_blob(packet, "enhancement-human-labels.json")
    report["labels_artifact"] = evidence_id
    report_id = "enhancement-report-" + content_hash(report)[:40]
    store.put(
        "evaluations", report_id, report, batch_id, "enhancement_report", immutable=True
    )
    exports.write_json(output, report)
    show(report)


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
    try:
        result = call(
            run["id"], Smoke, "Return result = tool calling works.", "connectivity"
        )
    except Exception as exc:
        failed = store.require("runs", run["id"])
        failed.update(status="failed", error=type(exc).__name__)
        store.put("runs", run["id"], failed, run["source_id"], "connectivity")
        raise
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


ontology_app = typer.Typer(help="Versioned discovery-only ontology evolution")
app.add_typer(ontology_app, name="ontology")


@ontology_app.command("prepare")
def ontology_prepare(run_id: list[str] = typer.Option(...)):
    """Inspect/freeze new runs without starting mapping inference or a graph thread."""
    from .agent import inspect_node

    for rid in run_id:
        run = store.require("runs", rid)
        if run.get("thread_id") or run.get("mapping_id"):
            raise typer.BadParameter("Use new runs before mapping/thread creation")
        for _ in range(3):
            result = inspect_node({"run_id": rid})
            if result["route"] != "inspect":
                break
        show({"run_id": rid, "status": store.require("runs", rid)["status"]})


@ontology_app.command("propose")
def ontology_propose(
    run_id: list[str] = typer.Option(...), activate_experimental: bool = False
):
    from .ontology_workflow import propose

    show(propose(run_id, activate_experimental))


@ontology_app.command("show")
def ontology_show(ontology_hash: str):
    from .ontology import resolve

    show(resolve(ontology_hash))


@ontology_app.command("diff")
def ontology_diff(parent_hash: str, ontology_hash: str):
    from .ontology import resolve

    parent, child = resolve(parent_hash), resolve(ontology_hash)
    show(
        {
            "added": {
                k: v
                for k, v in child["concepts"].items()
                if k not in parent["concepts"]
            },
            "changed": [
                k
                for k in parent["concepts"]
                if child["concepts"].get(k) != parent["concepts"][k]
            ],
        }
    )


@ontology_app.command("export")
def ontology_export_command(
    ontology_hash: str,
    format: str = typer.Option("linkml", "--format"),
    output: Path | None = typer.Option(None, "--output"),
):
    """Write a version as LinkML, or as SHACL or JSON Schema generated from it."""
    from . import ontology_export
    from .ontology import resolve

    if format not in ontology_export.FORMATS:
        raise typer.BadParameter("Use linkml, shacl or jsonschema")
    text = ontology_export.FORMATS[format](resolve(ontology_hash), ontology_hash)
    if output:
        output.write_text(text)
    else:
        typer.echo(text, nl=False)


@ontology_app.command("gate")
def ontology_gate_command(ontology_hash: str):
    """Run and record the promotion checks. Exits 3 if a check fails."""
    from . import ontology_gate

    report = ontology_gate.run(ontology_hash)
    show(report)
    if report["blocks_promotion"]:
        raise typer.Exit(EXIT_BLOCKED)


@ontology_app.command("promote")
def ontology_promote(ontology_hash: str, reviewer: str = typer.Option(...)):
    """Record explicit human promotion; does not approve mappings or rewrite outputs."""
    from .ontology import activate

    if not reviewer.strip():
        raise typer.BadParameter("Reviewer required")
    try:
        show(activate(ontology_hash, settings().experiment_id, reviewer))
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


@ontology_app.command("budget")
def ontology_budget():
    from .budget import summary

    show(summary(settings().experiment_id))


backfill_app = typer.Typer(help="Copy legacy rows into the typed schemas.")
app.add_typer(backfill_app, name="backfill")


@backfill_app.command("ontology")
def backfill_ontology():
    """Copy ontology versions, activations and proposals into the registry."""
    from . import backfill

    show(backfill.ontology())


@backfill_app.command("spine")
def backfill_spine():
    """Copy artifacts, sources, snapshots, runs, mappings, approvals and observations."""
    from . import backfill

    show(backfill.evidence_spine())


@backfill_app.command("identity-ops")
def backfill_identity_ops():
    """Copy batches, caches, model calls, events, evaluations and identity results."""
    from . import backfill

    show(backfill.identity_and_operations())


source_app = typer.Typer(help="Refresh facts and drift checks for sources.")
app.add_typer(source_app, name="source")


@source_app.command("state")
def source_state(source_id: str | None = None, kind: str | None = None):
    """Cadence, last check, last change and approved mapping, per source."""
    from . import sources

    show(sources.state(source_id, kind))


@source_app.command("cadence")
def source_cadence(source_id: str, days: float | None = typer.Option(None, "--days")):
    """Set how often a source should be checked. Without --days, clear it."""
    from . import sources

    try:
        show(sources.set_cadence(source_id, days))
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


@source_app.command("drift")
def source_drift(source_id: str, snapshot_id: str | None = None):
    """Compare a snapshot with the source's approved mapping. Exits 3 if it blocks.

    Uses the source's latest snapshot unless one is named.
    """
    from . import drift, sources

    facts = sources.state(source_id)[0]
    if not facts["approved_config_hash"]:
        raise typer.BadParameter("The source has no approved mapping")
    snapshot_id = snapshot_id or facts["latest_snapshot_id"]
    if not snapshot_id:
        raise typer.BadParameter("The source has no snapshot")
    result = drift.detect(snapshot_id, facts["approved_config_hash"])
    show({"source_id": source_id, **result})
    if result["blocking"]:
        raise typer.Exit(EXIT_BLOCKED)


@source_app.command("check")
def source_check(source_id: str):
    """Download a source again; a snapshot is registered only if the bytes changed."""
    from . import refresh

    show(refresh.check(source_id))


@source_app.command("extract")
def source_extract(
    source_id: str,
    snapshot_id: str | None = None,
    limit: int | None = typer.Option(None, "--limit", help="Records to read."),
):
    """Extract a snapshot under the mapping approved for the source. Exits 3 if blocked.

    The latest snapshot unless one is named. Nothing is extracted without an
    approved mapping, or when the snapshot's shape has drifted from it; the
    drift check is recorded. Extracting again stores nothing new.
    """
    from . import refresh

    try:
        show(refresh.extract(source_id, snapshot_id, limit))
    except refresh.Blocked as blocked:
        show({"source_id": source_id, "blocked": str(blocked)})
        raise typer.Exit(EXIT_BLOCKED) from blocked


access_app = typer.Typer(help="Tiers, clients and API keys of the product service.")
tier_app = typer.Typer(help="Tiers: what a class of client may do.")
client_app = typer.Typer(help="Clients: who holds keys.")
key_app = typer.Typer(help="API keys.")
app.add_typer(access_app, name="access")
access_app.add_typer(tier_app, name="tier")
access_app.add_typer(client_app, name="client")
access_app.add_typer(key_app, name="key")


def managing(action, *arguments, **options):
    """Run an access administration step, reporting a wrong argument as such."""
    try:
        return action(*arguments, **options)
    except (ValueError, KeyError) as error:
        raise typer.BadParameter(str(error).strip("'")) from error


@tier_app.command("set")
def access_tier_set(
    tier_id: str,
    rate_per_minute: int = typer.Option(..., "--rate-per-minute"),
    monthly_quota: int | None = typer.Option(None, "--monthly-quota"),
    interface: list[str] = typer.Option(["rest"], "--interface"),
    toolset: list[str] = typer.Option([], "--toolset"),
    source: list[str] = typer.Option(
        [], "--source", help="Repeat to limit the tier to sources."
    ),
    bundle_downloads: bool = False,
    release_lag: int = 0,
    history_depth: int | None = None,
):
    """Create a tier or replace its limits. Without --source the tier sees every source."""
    from .product import keys

    show(
        managing(
            keys.set_tier,
            tier_id,
            rate_per_minute,
            monthly_quota,
            interface,
            toolset,
            source or None,
            bundle_downloads,
            release_lag,
            history_depth,
        )
    )


@client_app.command("create")
def access_client_create(name: str, tier: str = typer.Option(..., "--tier")):
    from .product import keys

    show(managing(keys.create_client, name, tier))


@key_app.command("create")
def access_key_create(
    client_id: str,
    label: str | None = typer.Option(None, "--label"),
    expires_in_days: int | None = typer.Option(None, "--expires-in-days"),
):
    """Create a key. It is printed once here and cannot be shown again."""
    from .product import keys

    show(managing(keys.create_key, client_id, label, expires_in_days))


@key_app.command("revoke")
def access_key_revoke(prefix: str):
    """Revoke a key by its prefix, the part between `ll_` and the secret."""
    from .product import keys

    show(managing(keys.revoke_key, prefix))


@access_app.command("usage")
def access_usage(client_id: str | None = None, since: str | None = None):
    """Calls per client, key, interface and month."""
    from .product import keys

    show(managing(keys.usage, client_id, since))


release_app = typer.Typer(help="Releases: what clients see, recorded by a person.")
app.add_typer(release_app, name="release")


@release_app.command("create")
def release_create(
    batch_id: str = typer.Option(..., "--batch-id"),
    reviewer: str = typer.Option(..., "--reviewer"),
    notes: str | None = typer.Option(None, "--notes"),
):
    """Record a release of a batch and build its OKF tree. Never run by a pipeline."""
    from . import releases

    try:
        show(releases.create(batch_id, reviewer, notes))
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


@release_app.command("list")
def release_list():
    from . import releases

    show(releases.listing())


@release_app.command("show")
def release_show(release_id: int | None = None):
    """A release and the pages built for it. Without an ID, the latest release."""
    from . import releases

    show(releases.show(release_id))


@release_app.command("export")
def release_export(output: Path, release_id: int | None = None):
    """Write a release's OKF tree to a folder and check its links."""
    from . import exports
    from .okf import bundle

    written = bundle.write(release_id, output)
    show({**written, **exports.check_bundle(output)})


@release_app.command("digest")
def release_digest(release_id: int | None = typer.Argument(None)):
    """A fingerprint of what a release serves, to compare two environments."""
    from . import releases

    show(releases.digest(release_id))


artifacts_app = typer.Typer(help="Artifact bytes and where they are stored.")
app.add_typer(artifacts_app, name="artifacts")


@artifacts_app.command("migrate")
def artifacts_migrate(
    limit: int | None = typer.Option(None, "--limit", help="Move at most this many."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Check, copy nothing."),
):
    """Copy local artifacts to the configured object store, verifying each hash."""
    from . import artifacts

    try:
        moved = artifacts.migrate(limit, dry_run)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    show(moved)
    if moved["missing"] or moved["mismatched"]:
        raise typer.Exit(EXIT_BLOCKED)


scope_app = typer.Typer(help="Named bundle scopes: bounded lists of entities.")
release_app.add_typer(scope_app, name="scope")


@scope_app.command("set")
def release_scope_set(
    name: str,
    reviewer: str = typer.Option(..., "--reviewer"),
    entity: list[str] = typer.Option([], "--entity", help="An entity ID; repeat."),
    entities_file: Path | None = typer.Option(
        None, "--entities-file", help="A file with one entity ID a line."
    ),
    manual: bool = typer.Option(
        False, "--manual", help="Do not build this scope when a release is created."
    ),
):
    """Name the entities of a bundle scope such as `demo`. Replaces the list."""
    from . import bundles

    chosen = list(entity)
    if entities_file:
        chosen += [line.strip() for line in entities_file.read_text().splitlines()]
    try:
        show(bundles.set_scope(name, [e for e in chosen if e], reviewer, not manual))
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


@scope_app.command("list")
def release_scope_list():
    from . import bundles

    show(bundles.scopes())


@release_app.command("bundle")
def release_bundle(
    release_id: int | None = typer.Argument(
        None, help="The latest release by default."
    ),
    scope: str = typer.Option(
        ..., "--scope", help="A named scope such as demo, or client:<client id>."
    ),
):
    """Build a release's bundle for a scope: files, link check, viewer, archive."""
    from . import bundles

    try:
        show(bundles.build(release_id, scope))
    except KeyError as error:
        raise typer.BadParameter(str(error.args[0])) from error


@release_app.command("bundles")
def release_bundles(release_id: int | None = None):
    """Bundles built so far, newest first."""
    from . import bundles

    show(bundles.listing(release_id))


@app.command("serving-compare")
def serving_compare(
    candidate: str = "serving_next",
    reference: str = "serving",
    build: bool = typer.Option(
        False, "--build", help="Build the serving models into the candidate first."
    ),
):
    """Compare the serving views built in one schema with those in another.

    Columns, and per release the row count and a digest of every row. For a
    changed model: `serving-compare --build` builds the serving models into
    serving_next and compares them with what clients read; build into serving
    only when it reports no difference you did not mean. Exits 3 on a difference.
    """
    import sys

    from . import serving, transform

    if build:
        # dbt's own report goes to standard error; the result stays on standard output.
        code = transform.candidate(candidate, stdout=sys.stderr).returncode
        if code:
            raise typer.Exit(code)
    with store.engine().connect() as connection:
        result = serving.compare(connection, candidate, reference)
    show(result)
    if result["differences"]:
        raise typer.Exit(EXIT_BLOCKED)


@app.command(
    "dbt",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
)
def dbt(context: typer.Context):
    """Run dbt on the transform project: `link-lens dbt build`, `link-lens dbt debug`.

    dbt connects to the configured database and works as linklens_transform.
    Everything after `dbt` is passed to it, and its exit code is returned:
    0 done, 1 a model or a test failed, 2 dbt could not run what was asked.
    """
    from . import transform

    raise typer.Exit(transform.run(context.args).returncode)


def main():
    """Console entry point: run the command and log how it ended.

    Typer sets the exit code: 0, 2 for a wrong call, or the code a command chose.
    A command that raises is logged with its error type and exits 1.
    """
    import logging
    import sys
    import time

    from . import logs

    logs.configure()
    started = time.monotonic()
    command = " ".join(a for a in sys.argv[1:3] if not a.startswith("-"))

    def seconds():
        return round(time.monotonic() - started, 3)

    try:
        app()
    except SystemExit as stop:
        code = stop.code if isinstance(stop.code, int) else int(stop.code is not None)
        logs.event(
            "command.finished",
            logging.INFO if code == 0 else logging.WARNING,
            command=command,
            exit_code=code,
            seconds=seconds(),
        )
        raise
    except Exception as error:
        logs.event(
            "command.failed",
            logging.ERROR,
            command=command,
            exit_code=1,
            seconds=seconds(),
            **logs.error_fields(error),
        )
        raise
