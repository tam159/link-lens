# Working on Link Lens

## Purpose and starting points

Link Lens onboards unfamiliar public business datasets, produces agent-generated declarative mappings for human approval, then deterministically extracts observations, links entities and builds evidence-backed profiles. It began as a locally runnable assignment submission, and those results and experiments are preserved. On top of it are a production data model in typed PostgreSQL schemas and a read-only product service (REST, MCP, bundles) that serves a release a person has recorded. Everything still runs locally: nothing is hosted, and no release has been recorded for clients unless the stored data says so. A second plan adds Dagster for the deterministic data flow and dbt for derived SQL; dbt now builds the `serving` views that clients read and the reporting models in `analytics`, Grafana shows three dashboards over those, and Dagster holds the deterministic data flow as assets, checks and sensors. A schedule refreshes each source by the cadence a person set for it, and sensors alert on failures, drift, overdue sources and the budget; no cadence is set and no alert channel is configured, so both are idle until someone does. Both tools are the open-source editions and run in local Docker; an override runs them as a deployment, from their image and with a login of their own. An operations console, an admin API with its pages, lets a signed-in person add and manage sources, record releases and manage clients, and writes every change to an audit log. Its sign-in is a list of tokens for development; no identity provider is connected, and the other UIs have no sign-in at all, so every UI stays on the machine. Routine operation needs no terminal: Dagster runs the data flow, people decide in the Agent Inbox and the console, and a Compose service takes backups once a person starts it. The local stack is not cut over yet: that is the owner's checklist under **Routine operation** in the engineering guide, and nothing on it is done unless the stored data says so. The CLI stays for one-off work, recovery, ontology promotion and bundle scopes, and every pipeline command still works as before.

Read only the documentation relevant to your task:

| File | Owns |
|---|---|
| [README.md](README.md) | Setup, environment variables, commands, architecture and workflow diagrams |
| [WRITEUP.md](WRITEUP.md) | Reviewer-facing explanation, decisions, results and limitations |
| [docs/DEMO.md](docs/DEMO.md) | Illustrated presentation, seventh-source run and optional frozen restore |
| [docs/ENGINEERING.md](docs/ENGINEERING.md) | Implementation details, verification, operations and recovery |
| [docs/PRODUCTION_PLAN.md](docs/PRODUCTION_PLAN.md) | The production work phase by phase: what was built, where it differs from the first sketch, measured results, what is open, and the risk table |
| [docs/ORCHESTRATION_PLAN.md](docs/ORCHESTRATION_PLAN.md) | The Dagster and dbt work phase by phase (D0 to D7): who owns which relation, what each phase must settle against the code, what was built and measured, and its risk table |
| [CONTRIBUTING.md](CONTRIBUTING.md) | For the two engineers: who owns which object, how a change gets in, and how to write a dbt model, a Dagster asset or a console action |
| [docs/RUNBOOKS.md](docs/RUNBOOKS.md) | What to do when the data flow needs a person: a failed refresh, drift, a stuck review, a failed release build, the budget cap, restoring a release, Dagster itself, backups |
| [docs/api/](docs/api/) | The published REST (`openapi.json`) and MCP (`mcp-tools.json`) contracts, checked against the code by a test |
| [outputs/README.md](outputs/README.md) | Current submission results, approvals and evaluation status |
| [outputs/COMPARISON.md](outputs/COMPARISON.md) | Previous versus current approach and download-gate comparison |

Resolve current experiment, discovery revision, run IDs, batch IDs, the migration revision, which orchestration phase is built and whether a release exists from settings, the plans and stored/exported metadata. Do not assume an ID or count in an old document is still current. `store.current_discovery()` resolves the active discovery revision; `link-lens release list` shows the releases.

## Code map

Application code is in `src/link_lens/`:

| Modules | Responsibility |
|---|---|
| `cli.py`, `api.py`, `settings.py` | CLI, application routes and environment settings |
| `ingestion.py`, `triage.py`, `downloadability.py` | CKAN discovery, Jev relevance ranking, download/reader preflight and registration |
| `sources.py`, `drift.py`, `refresh.py`, `alerts.py` | Refresh facts per source (cadence, last check, last change, approved mapping, pause, failed checks) and which sources are due or overdue, one-line alerts to a webhook, the drift check of a snapshot against its approved mapping and its stored result, and the refresh steps an orchestrator calls: check a source for new bytes, extract a snapshot under the approved mapping, request onboarding, assemble a batch |
| `agent.py`, `llm.py` | Bounded LangGraph onboarding, model calls, validation, critique and Inbox interrupts |
| `contracts.py`, `readers.py`, `extraction.py` | Typed mapping contract, shared readers and declarative extraction |
| `resolution.py`, `profiles.py`, `pipeline.py` | Deterministic linking, profile decisions and assembly |
| `store.py`, `blobs.py`, `frozen.py` | Store facade over typed and legacy tables, artifact byte storage (local or S3-compatible) and archive/restore |
| `db/`, `backfill.py`, `logs.py` | Typed-schema helpers and repositories (`db/ontology.py`, `db/catalog.py`, `db/onboarding.py`, `db/evidence.py`, `db/identity.py`, `db/ops.py`), copies from the legacy tables, and JSON-line command logs |
| `ontology.py`, `ontology_workflow.py`, `ontology_gate.py`, `ontology_export.py` | Ontology registry, proposal job, promotion gate, and LinkML/SHACL/JSON Schema export |
| `evaluation.py`, `review_ui.py` | Separate human/AI evaluation records and review worksheets |
| `measurements.py`, `pricing.py`, `pricing_rates.json` | Usage, pricing basis and cost calculations |
| `exports.py`, `_vendor/okf/` | Generated JSONL/CSV/OKF and viewer; retain vendor attribution |
| `releases.py`, `okf/`, `serving.py` | Human-recorded releases, the OKF renderer, index, virtual tree and bundle, and the comparison of serving views between two schemas. The read models themselves are dbt models in `transform/models/serving/` |
| `product/`, `interfaces/rest.py`, `interfaces/mcp_server.py` | The read-only product service: API keys and tiers, limits, the query layer over `serving`, response models, the REST routes and the MCP tools |
| `bundles.py`, `artifacts.py` | Release bundles for a named scope or a client, the per-entity viewer, and moving artifact bytes to object storage |
| `admin/` | The operations console: the admin API and its routes (`app.py`), sign-in and roles (`auth.py`), the audit log (`audit.py`), what the console reads and does over the library (`service.py`) and its pages as static files (`static/`) |
| `transform.py` | Runs the `dbt` command on the transform project with the connection taken from the application's database URL; does not import dbt |
| `sandbox.py`, `runtime_compat.py` | Restricted Python execution and pinned runtime compatibility fixes |

`migrations/` contains Alembic migrations as explicit SQL, each with a downgrade; `tests/` contains deterministic tests and explicitly gated integrations. `compose.yaml`, `deploy/` and `langgraph.json` define local services; `deploy/alerts.yml` holds alert rules for the product service.

Two folders beside `src/` belong to the orchestration plan and are not part of the `link_lens` package:

| Folder | Responsibility |
|---|---|
| `transform/` | The dbt project: `dbt_project.yml`, a profile configured by the environment, a schema-name macro, the declared sources (`models/sources`), the twelve serving read models with their contracts, tests and exposures (`models/serving`), the reporting models (`models/analytics`) over thin staging views (`models/staging`), and generic and singular tests (`tests/`) |
| `orchestration/` | The Dagster code location `link_lens_dagster`: assets (`assets/snapshots.py`, `extraction.py`, `onboarding.py`, `identity.py`, and `models.py` for the dbt project), `sensors.py`, `schedules.py` (the due-source schedule, the freshness check, the weekly batch, run retention), `alerting.py` (alert sensors), `resources.py`, `partitions.py` and `definitions.py`. Beside it, `workspace.yaml` and the instance configuration `dagster.yaml` |

`deploy/Dockerfile.dagster` builds the one image that holds Dagster and dbt, self-contained; `deploy/dagster-db.sql` creates Dagster's own database; `deploy/compose.deploy.yaml` runs the Dagster services as a deployment and `deploy/service-logins.sql` creates the login they use then. `scripts/backup_databases.sh` dumps both databases and is safe to run: it reads, and prunes only its own Dagster dumps. `deploy/grafana/` holds Grafana's provisioning and the dashboards as JSON files, and `deploy/grafana-db.sql` creates the login Grafana reads with. Read scripts before executing them: several `scripts/` files have top-level side effects, fixed experiment IDs or authored audit judgments. They are not all reusable library functions. Two are safe, read-only tools: `scripts/migration_baseline.py` compares a database with the recorded baseline, and `scripts/mcp_agent_eval.py` runs fixed tasks against the MCP server without a model.

## Development commands

Run from the repository root. Use Python 3.13 and `uv`; `.venv` is the virtual environment and `.env` is configuration. Add dependencies with `uv add` and update `uv.lock` intentionally.

```sh
uv sync --frozen
uv run link-lens --help
uv run pytest -q
uv run ruff check src/link_lens tests --exclude _vendor --select F
```

For the production data model and the product service:

```sh
uv run alembic upgrade head     # applies migrations; it creates no serving view
uv run link-lens dbt build      # builds the serving views and runs their tests
uv run python scripts/migration_baseline.py --typed --check outputs/local-run/migration-baseline.json
uv run link-lens release list   # what clients can be served; empty until a person records one
UPDATE_CONTRACTS=1 uv run pytest tests/test_production.py     # after a meant REST or MCP change
UPDATE_FIXTURES=1 uv run pytest tests/test_fixture_bundle.py  # after a meant change to a page
```

dbt is installed by a plain `uv sync`, because the tests build the serving views with it. Dagster is in a dependency group of its own:

```sh
uv sync --frozen --group orchestration
uv run link-lens dbt debug      # dbt on the configured database, as linklens_transform
uv run link-lens serving-compare --build   # build the serving models into serving_next and compare; exits 3 on a difference
uv run dagster definitions validate --workspace orchestration/workspace.yaml
uv run pytest -q tests/test_orchestration.py   # skipped without the orchestration group
uv run link-lens source check SOURCE      # download again; a snapshot only if the bytes changed
uv run link-lens source extract SOURCE    # under the approved mapping; exits 3 when blocked
uv run link-lens source due               # what the schedule would refresh now, and what is overdue
uv run link-lens source backfill          # outstanding extraction; a dry run unless --apply
docker compose --profile orchestration up -d --build   # Dagster UI on http://localhost:3070
docker compose --profile dashboards up -d              # Grafana on http://localhost:3080
docker compose --profile console up -d admin           # operations console on http://localhost:8200
docker compose --profile backups up -d backup          # daily dumps of both databases to LINK_LENS_BACKUP_DIR
uv run link-lens source preview DATASET                # what registering would download; writes nothing
uv run link-lens release preview --batch-id BATCH      # against the latest release; exits 3 if a check fails
docker compose --profile orchestration build dagster-webserver   # after a change the deployment should run
scripts/backup_databases.sh /path/to/backups           # both databases; see docs/RUNBOOKS.md
```

Run relevant tests first and broader checks when the change warrants them. Deterministic tests use isolated fixtures; those that touch the store run on PostgreSQL in a throwaway container (Docker required, see README **Verification**). Live model and Docker integrations are separate. Documentation-only edits need link/command consistency checks, not a paid pipeline rerun. Consult `tests/test_sandbox_integration.py` before enabling `RUN_DOCKER_TESTS=1`.

Service startup and provider setup live in README. Default local ports: Inbox 3000, backend 2024, PostgreSQL 5439, sandbox controller 8091, product service 8100, the Dagster UI 3070 and dbt's documentation 3090 when the `orchestration` profile is started, Grafana 3080 when the `dashboards` profile is, and the operations console 8200 when the `console` profile is. The graph ID is `onboard`. The development server supplies the graph checkpointer; PostgreSQL stores application evidence separately. Frozen application archives do not recreate LangGraph threads/checkpoints.

The local stack runs the code of the folder that Compose is started from:

- Run `docker compose` from the repository root. Compose mounts that folder's `./src` and `./migrations` into the running backend and product service with reload on, so an edit there reaches the running services at once. Started from another checkout or worktree, it builds and runs that folder's code instead.
- The backend runs `alembic upgrade head` when it starts. A new migration therefore reaches the local database at the next backend start. The procedure for changing that database is under **Outputs, secrets and scope**. The backend image has no dbt, so starting it never builds or refreshes a serving view; that is `uv run link-lens dbt build` on the host.
- The backend, sandbox controller and product service share the image `link-lens-backend:local`. After a dependency change, rebuild it with `docker compose build backend` and recreate the service that needs it.
- Dagster and dbt run in their own image, `link-lens-dagster:local`, and only with `docker compose --profile orchestration`. The services are `dagster-db` (creates the `dagster` login and database when missing, then exits), `dagster-webserver` and `dagster-daemon`. They mount `./orchestration`, `./transform` and `./src`; reload the code location in the UI after an edit. After a change to the `orchestration` or `transform` group, rebuild with `docker compose --profile orchestration build dagster-webserver`. With `-f compose.yaml -f deploy/compose.deploy.yaml` the same services run from the image alone: an edit then reaches them only through a rebuild, they need `LINK_LENS_DAGSTER_POSTGRES_PASSWORD` and `LINK_LENS_ORCHESTRATION_PASSWORD`, and the migrations must have run first.
- Grafana runs only with `docker compose --profile dashboards`: `grafana-db` creates the `linklens_grafana` login when missing and exits, and `grafana` loads its data source and dashboards from `deploy/grafana/`. A dashboard edited in the UI is not saved; change the JSON file.
- The operations console runs only with `docker compose --profile console`: the service `admin`, from the backend image with `./src` mounted and reload on. It works on the database as `linklens_pipeline`, gets no provider key, and signs in only the people listed in `LINK_LENS_ADMIN_USERS`; with none listed, nobody.
- Backups on a timer run only with `docker compose --profile backups`: the service `backup` runs `deploy/backup-loop.sh` in a PostgreSQL image and writes to `LINK_LENS_BACKUP_DIR`. It never deletes a `linklens` dump; it is not started on the local stack unless the owner starts it.
- Tests never use the `linklens` database. They start their own container or use `LINK_LENS_TEST_DATABASE_URL`.

## Contracts to preserve

### Submission pipeline

- The submitted approach uses Jev for discovery/identity, `gpt-6-luna` for ontology/onboarding/conflict annotations, and `text-embedding-3-small` for hybrid retrieval. The promoted ontology seeds new experiments; legacy mappings retain frozen v0.1. Model names are configurable and provider access is deployment-specific. Do not silently change models during a comparison.
- Part 1 combines deterministic and Jev relevance signals with download/readability checks. A successful download is evidence of availability, not proof of business relevance. Audit labels must not influence the frozen ranking being evaluated.
- One onboarding graph investigates and revises mappings. Exploration Python runs only through the sandbox. Approved extraction uses the shared declarative engine, never generated Python or unrestricted expressions embedded in configs.
- An ontology version's hash is the digest of its document and must rebuild from the registry rows. Registry tables are append-only and versions are additive. Promotion is a human action that needs a recorded gate run with no failed check; a gate result is not a promotion.
- Keep discovery, validation feedback and held-out final records separate. Freeze reader/partition decisions before inference; never expose reserved records to exploration. A failed final test does not authorise repeated tuning against that same test set.
- Accept approves the exact stored config hash; Respond requests revision; Ignore defers. Config changes require fresh approval. Preserve reviewer, feedback, timestamps and idempotent resume/extraction. Never substitute AI acceptance for the user's mapping review.
- Keep bounded calls, tokens, execution time, mapping versions and costs. Preserve failed/retried calls and explicit recovery lineage; do not reset budgets invisibly.
- Only the trusted sandbox controller has Docker-daemon access. Execution containers receive no network, credentials, Docker socket or repository mount. Preserve resource limits, bounded outputs and cleanup on failure. This is local-development isolation, not a production multi-tenant security claim.
- Link on validated identifiers with compatible subject roles. Never derive ACN from an ABN suffix, merge on name alone, or ignore conflicting identifiers/ownership ambiguity. Preserve source records and versioned membership decisions.
- Preserve raw values, exact source locators, timestamp policy, separate confidence dimensions, alternatives and cohesive address bundles. Uncalibrated scores are rule/model scores, not measured probabilities. Missing defensible timestamps require quarantine rather than invented dates.
- PostgreSQL and immutable artifacts are authoritative; OKF is a generated view. Serve artifacts by registered ID, not arbitrary filesystem paths. Version schema changes with Alembic.
- AI audits, human mapping approvals and human evidence evaluations are different activities. Unknown/unreviewed labels are not correct answers. An AI audit cannot complete the assignment's human evaluation requirement.
- Include all model attempts in usage. Missing usage is unknown, not zero. State estimated pricing basis and priced-call coverage; do not present a partial subtotal as the complete bill. Per-record processing is deterministic unless explicitly changed.

### Production data model and product service

`docs/PRODUCTION_PLAN.md` section 4 lists the rules every phase kept; these are the ones a change is most likely to meet.

- **IDs and records do not change.** Ontology digests, mapping `config_hash`, observation IDs, record IDs and `profile_version` keep their values. Every record lives in a typed table behind `store.py` and must read back exactly as it was written. Snapshots, mapping configs, mappings, approvals, source records, observations, releases and bundles are append-only. A settled model call never changes. An artifact row may change only its `uri`.
- **Writing.** Write a batch and what it owns with `store.put_many`, batch first, and observations with `store.put_observations`. Write each pipeline step as a function with explicit IDs that returns a small result record and writes nothing new when repeated. No table gets one partition per source.
- **`legacy` is read-only history.** Nothing writes it. Do not add a migration that drops it: the backend migrates on start, and the plan lists what must happen first.
- **Commands.** CLI commands log JSON lines to standard error and results to standard output. Exit codes: 0 done, 1 failed, 2 called wrongly, 3 ran and found something that blocks the next step.
- **A person records what clients see.** A release (`link-lens release create`, or the console), a tier, client or key (`link-lens access`, or the console), a bundle scope and a client's bundle (`link-lens release scope`, `release bundle`) and an ontology promotion are human actions. No pipeline step and no agent acting for someone creates one on a real database; test fixtures and throwaway copies are the exception.
- **Serving.** A serving read model is one `SELECT` in `transform/models/serving/`, a dbt model with an enforced contract in `_serving.yml`; change the file and its contract, not the view. Run `link-lens serving-compare --build`, which builds the serving models into `serving_next` and compares them with the live views, and build into `serving` only when the differences are the ones you meant. Migrations create no view: after `alembic upgrade head` on any database, run `link-lens dbt build`. OKF pages come from `okf/render.py` only, and an entity, evidence, source or concept page is the same bytes in the tree, in a bundle and over an interface.
- **The product service only reads.** It runs as `linklens_product`, reads `serving` and the access tables, and writes only usage counts and rate buckets. It never reads a core schema. It checks the key and counts the call on the primary and reads data from the replica when one is configured.
- **Evidence is never tiered or hidden.** Every answer carries status, provenance, alternatives, score kind, timestamp basis and licence. A key limited to some sources must not reach another source's observations, evidence, links or pages by any route. Profiles are answered whole; that is a recorded decision, not an oversight.
- **Keys.** A key is shown once at creation. Only its prefix and the hash of its secret are stored, and only its prefix is ever logged.
- **MCP.** A tool is one read-only call into `product/queries.py` with a closed argument schema and a bounded result that says how to continue. It never writes, runs a command or accepts SQL. Read the installed `mcp` SDK's documentation before changing `interfaces/mcp_server.py`; version 2 differs from earlier ones.
- **Bundles.** A bundle is the same bytes whenever it is built for the same release and scope. The index pages of a named scope list only that scope.
- **Published contracts and the kept bundle.** `docs/api/` and `tests/fixtures/okf_bundle` change only on purpose, with the commands above, and the difference is reviewed like code.
- **No paid call for this work.** Migrations, backfills, releases, the product service and `scripts/mcp_agent_eval.py` are verified with deterministic checks against stored data.

### Orchestration and transformation

`docs/ORCHESTRATION_PLAN.md` sections 2 and 3 hold the decisions and the ownership table; these are the rules a change is most likely to meet.

- **Alembic and dbt never manage the same relation.** Alembic owns every table that holds state, every schema and every grant to a schema. dbt owns only derived relations: the twelve views in `serving`, candidates in `serving_next`, and whatever is built in `analytics`. In `serving`, the three `okf_*` tables and the functions are Alembic's and are filled by `releases.create`; no dbt model replaces them.
- **dbt works as `linklens_transform`.** The profile sets that role on every connection. It reads the core schemas, creates only in `serving`, `serving_next` and `analytics`, and reads neither `legacy` nor the hash of a key's secret. dbt grants `SELECT` on each serving model to `linklens_product` and `linklens_pipeline` and on each reporting model to `linklens_analyst`, in `dbt_project.yml`. Give the role more only by a migration, and say why in the plan.
- **Nothing in `analytics` is served to clients.** The product role has no access to it. The team and Grafana read it as `linklens_analyst`, which can read the granted reporting models and nothing else: no core table, no serving view, no staging view, no key. The console and the CLI read the same granted models as `linklens_pipeline`, and no staging view.
- **Reporting keeps kinds of evidence apart.** A model never adds human labels and AI labels into one figure, and a test fails if `evaluation_summary` does. A score or confidence is shown as uncalibrated unless a person measured it, with the sample size and date beside it. An unknown is a count of its own, never a zero in a sum.
- **A reporting model reconciles with its tables.** A new model in `transform/models/analytics` gets a key test and, where it adds things up, a test that its total equals the table it reads.
- **Dashboards read models, not tables.** A Grafana panel queries `analytics.<model>` only, each dashboard is a dbt exposure, and `tests/test_dashboards.py` runs every panel's query as the analyst. Build the whole project when building into `serving`: replacing a serving view drops the reporting views that read it until they are rebuilt.
- **Dagster's own storage is the `dagster` database**, with a login that has no right on the application's schemas. It never goes into a schema of the application's database, and application state never goes into Dagster's.
- **Observation IDs include the download time.** An observation's `ingested_at` is its snapshot's retrieval time and is part of its content hash. Two environments that each download the same file store the same observations under different IDs, and their batches and releases differ in IDs only. Compare environments by content; within one database Dagster and the CLI give identical IDs.
- **A snapshot extracted in part looks extracted.** Onboarding extracts a sample of a file, the schedule extracts only files whose bytes changed, and `source backfill` looks only for a snapshot with no observations under the mapping in force. Nothing reports a source left with its sample. Until completed extractions are recorded, a full extraction is a cutover step (materialise `observations` for all partitions), and it adds rows to a real database only when the owner asks.
- **Dagster calls the library and reacts to rows.** An asset is a few lines over a step in `refresh.py` with explicit IDs, and attaches the step's result record as metadata. Dagster holds no pipeline logic and keeps no copy of a fact that PostgreSQL holds. A new step goes into the library first, with its own test, and is idempotent.
- **Dagster works as `linklens_orchestrator`.** Its processes set `LINK_LENS_DATABASE_ROLE`, and every asset fails if the library is working as anyone else. That role cannot insert or update a mapping approval, an ontology activation, a release, a bundle scope, a bundle or a review label, and has nothing in `access`, `serving` or `analytics`. A new table that records a human decision must revoke the role's default privileges on it in its migration.
- **Sensors react to what a person recorded and start from the present.** A new approval requests extraction, a new release requests the dbt build, a promotion is only reported. Turning a sensor on never replays history.
- **Cadence, pause and failures are data in the registry.** `sources.due` decides what a schedule refreshes; there is one schedule for all sources and none per source. A person sets a cadence or pauses a source (`link-lens source cadence`, `source pause --reviewer`); Dagster only reads them. The scheduled flow makes no model call: a refresh downloads, checks drift and extracts.
- **Be polite to publishers.** A scheduled check sends the validators of the last download and stores nothing on `304`; a failed check backs off; the schedule caps refreshes per portal and evaluation. Keep all three when changing `ingestion.download`, `sources.due` or the schedule.
- **An alert never raises and never shows its address.** `alerts.send` posts one line to `LINK_LENS_ALERT_WEBHOOK_URL`, or logs it when none is set, and returns whether it was delivered. The URL is a secret: it comes from the environment and is in no log line. An alert sensor moves its cursor whether or not the alert was delivered.
- **Paid steps never start by themselves and are never retried by Dagster.** `onboarding_request` and `source_catalogue` have no retry policy, and only the deterministic jobs `refresh_source`, `extract_observations` and `build_models` carry the tags that let the daemon re-run a crashed run (`run_retries` in `dagster.yaml`); the sensor that requests onboarding on drift is off by default, and discovery refuses to run without `confirm_paid_calls`. The application's budget stays the only authority on spend.
- **A refresh is a run, and carries an approval; it never makes one.** Extracting a snapshot other than the one a source was onboarded on records a run of kind `refresh` that names the mapping and the approval of the run it refreshes. A batch is assembled from each source's newest such run (`refresh.current_runs`). The run exists only when the drift check did not block; a shape the approved mapping cannot read still waits for a person. Code that lists runs must say which kinds it means: a refresh is not an onboarding attempt.
- **A batch is a sample, and a refresh resamples it.** Assembly picks records by record ID, which changes with every snapshot, so a batch after a refresh differs by more than the rows that changed. Do not present the difference between two batches or releases across a refresh as change in the sources. The plan's D3a section has the measurements and the two ways forward.
- **A release serves what was stored when it was recorded.** `serving.observation` and `serving.evidence` take only the snapshot the release's run was onboarded on and only observations loaded by then (`evidence.observation.loaded_at`), so a later extraction adds nothing to an existing release. Keep both conditions when changing those models.
- **Open source, in local Docker.** Dagster is the open-source edition and dbt is dbt Core, by the owner's decision of 2026-11-15. Do not add a dependency on a hosted offering of either. Only the sandbox controller has the Docker socket: Dagster runs its runs as processes, never as containers it starts.
- **Where Dagster runs, it builds the views.** The sensor `models_missing` requests the dbt build when views dbt owns are missing, and `release_recorded` after a release. `link-lens dbt build` is for a database Dagster does not watch and for recovery.
- **No UI has a real sign-in.** The Dagster UI and dbt's documentation have none, Grafana has one shared admin account, and the console has a list of tokens for development. All are published on the loopback address only. Do not publish them further without a proxy or an identity provider that signs people in.
- **The tools stay out of the runtime image.** Dagster and dbt are in the `orchestration` and `transform` dependency groups, and `dev` includes `transform`; the backend, product service and sandbox images install no group. The lock file is shared, so after any change to those groups compare `uv export --no-dev` before and after and say what moved.
- **Read the installed versions' documentation before changing `orchestration/` or `transform/`.** Both tools change often. dbt stays on dbt Core 1.12; version 2 is a separate decision.
- **dbt, Dagster and Grafana report nothing to their vendors.** Usage statistics are off in `dbt_project.yml`, telemetry in `dagster.yaml`, and reporting and update checks in the `grafana` service; keep them off.

### Operations console

`docs/ORCHESTRATION_PLAN.md`, phase D6, has what was built and why; these are the rules a change is most likely to meet.

- **Every route under `/admin` needs a signed-in person, and the role is checked in the API.** A new route declares its role with `needs(role, action)`. Hiding something in the pages is a convenience, never the control. There is no default account: with nobody listed in `LINK_LENS_ADMIN_USERS`, nobody signs in.
- **A route is a few lines over the library function the CLI calls.** A new console action goes into the library first, with a CLI command that writes the same records. No rule lives only in the API.
- **Every change is recorded around the call that makes it.** Use `audit.acting`: the request is committed before the change and the outcome after, under one `action_id`. `ops.admin_action` is append-only and the orchestrator's role cannot write it. Reads and previews are not recorded.
- **No key or secret enters the log.** Issuing a key records its ID and prefix. A token is never written to a table or a log line. Keep `audit.scrub` in front of every row.
- **A preview writes nothing.** `ingestion.preview` and `releases.preview` store no row and no artifact; the tests count the store before and after.
- **Adding a source is a paid action.** It needs `confirm_paid_calls`, shows the estimate, the cap and what remains, and is refused when the estimate would take the budget over its cap. Never confirm one against the real backend to try the console: use a throwaway copy with a stand-in for the onboarding server.
- **The console acts for the person signed in.** A release, a client, a tier, a key, a cadence and a pause made there are that person's decisions. No agent signs in to the console on a real database to make one; try changes on a throwaway copy.
- **The pages call `/admin` and nothing else.** They are static files with no build step, hold no credential, and build the page from values, never from markup. The console's content security policy allows only its own files.
- **The console works as `linklens_pipeline`** and gets no provider key. It reads a source's status from `analytics.source_health`, the one place that defines it.
- **The console links to the other tools and copies none.** Review stays in the Agent Inbox, running and scheduling in Dagster, numbers on the dashboards, ontology promotion and bundle scopes on the command line.

## Outputs, secrets and scope

- `outputs/` holds the current submission. Export experimental reruns to a distinct directory such as `outputs/local-run/`; replace submission artifacts only when the task calls for it.
- `experiments/` preserves earlier evidence for comparison. Do not rewrite a baseline to match new code or metrics. Keep IDs, hashes, snapshots and measurement provenance traceable.
- `artifacts/`, database volumes and `.langgraph_api/` are runtime state. Do not delete them or run `docker compose down -v` as routine cleanup. Restore archives only into an appropriate empty database.
- The local `linklens` database and `artifacts/` may be the only copy of the experiment data. Before a migration reaches that database: take a `pg_dump`, rehearse the migration on a restored copy in a throwaway container, stop the backend, the product service and the Dagster services, migrate, build the serving views with `link-lens dbt build`, and run both baseline checks, which must report zero differences. Say where the backup is. Ask before a step that changes or deletes existing rows rather than adds to them. `docs/ENGINEERING.md` has the commands.
- `outputs/local-run/migration-baseline.json` records what the store held before the production migrations. Check against it; do not write it again. Building a bundle adds an artifact, so the artifact count grows by one for each bundle.
- Generated OKF of new runs, releases and bundles is not committed. `outputs/okf` stays as submitted.
- `local/` and `walkthrough/` are ignored personal/educational material. Do not promote their hand-authored mappings into agent-generated submission results or expose private notes in public docs.
- `.env` and `.codex/` remain ignored. Never print credentials, copy secrets into reports, or overwrite an existing `.env`. Document configuration through `.env.example` with placeholders. Keep `AGENTS.md`, repository skills and workspace files eligible for version control.
- Check a helper script's input/output scope before running it. In particular, ensure reporting/worksheet scripts use the active discovery revision rather than an original `discovery-<experiment>` ID. Existing `record_*audit.py` judgments apply to their original evidence, not new shortlists or batches.
- Respect the requested scope: a Part 1 rerun does not require re-onboarding six sources; a cost recalculation does not require new inference; a documentation update does not require starting services.

## Documentation and completion

Keep documentation in English and distinguish implemented, measured, assumed and future work. Update the owning document and link to detail instead of duplicating entire sections. Architecture is now in root README; do not recreate `docs/ARCHITECTURE.md`. The demo is consolidated in `docs/DEMO.md`; results/reviews/evaluation instructions are consolidated in `outputs/README.md`. For production work, `docs/PRODUCTION_PLAN.md` is the record, and for Dagster and dbt work `docs/ORCHESTRATION_PLAN.md` is: when a decision changes or the code turns out to differ from the plan, say so there, in the phase's section and in the risk table, instead of deviating silently. `docs/ENGINEERING.md` holds how to operate what the plan describes.

Generated exports and curated explanations have different owners: report scripts can refresh machine data and generated status files, but manually check README, WRITEUP, comparison and demo claims afterward. Preserve screenshot dates and historical context. Verify relative links and Mermaid syntax when editing docs.

For a completed coding task, report what changed, what checks ran and any remaining limitation. Do not claim a live run, approval, human evaluation or measured cost without its evidence.

## Reusable procedures

- [Source onboarding and review](.agents/skills/link-lens-onboarding/SKILL.md): a new source, seventh-source demonstration, or interrupted onboarding recovery.
- [Evidence refresh and evaluation](.agents/skills/link-lens-evidence-refresh/SKILL.md): scoped reruns, audits, measurements and comparisons.

These are repository skills in Codex's `.agents/skills` discovery location. Other coding tools can read the linked instructions directly.

Which routine runs where, and what each CLI command is still for, is the table under **Routine operation** in [docs/ENGINEERING.md](docs/ENGINEERING.md). How to add a dbt model, a Dagster asset or a console action is in [CONTRIBUTING.md](CONTRIBUTING.md).

Procedures for the production work are sections of [docs/ENGINEERING.md](docs/ENGINEERING.md), under **Database layout, migrations and the baseline**: migrating an existing database, backfilling, recording a release, managing access, building bundles, moving artifacts to object storage, restoring into an empty environment, running dbt and Dagster locally, and refreshing a source through Dagster or by hand.

## GitHub identity

When using `gh` in this project under `/Users/may/tech/`, check `gh api user --jq .login` and switch with `gh auth switch --user tam159` if needed. Do not publish or push merely because local implementation is complete.
