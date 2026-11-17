# Engineering notes and verification

[Agent design](#part-2-langgraph-agent-design) · [Implementation](#implementation-notes) · [Verification](#verification-evidence) · [Operations](#operations-and-recovery)

## Part 2: LangGraph agent design

This section describes the implemented graph in [agent.py](../src/link_lens/agent.py), rather than a proposed architecture. It is one bounded workflow with **eight nodes**, three kinds of structured model response and an optional Python investigation. Acquisition/registration happens before the graph; cross-source linking and profile assembly happen afterward.

### Nodes and conditional edges

```mermaid
flowchart TD
    Start([START]) --> Entry{"Stored run status"}
    Entry -->|Other| Inspect["inspect · model selects reader"]
    Entry -->|waiting_for_human| Review["review · Inbox interrupt"]
    Entry -->|completed| Done([END])
    Inspect -->|Reader parse error; bounded retry| Inspect
    Inspect -->|Freeze reader and partitions| Explore["explore · optional sandbox Python"]
    Explore --> Propose["propose · model emits MappingSpec"]
    Propose -->|Malformed typed response; within bounds| Propose
    Propose -->|Mapping saved| Validate["validate · deterministic checks"]
    Validate -->|Blocking issues| Propose
    Validate -->|Passed| Critique["critique · model emits SemanticReview"]
    Critique -->|Malformed response; bounded retry| Critique
    Critique -->|Semantic blockers| Propose
    Critique -->|Acceptable for human review| Final["final · unused held-out slice"]
    Final -->|Failed| Done
    Final -->|Passed; packet saved| Review
    Review -->|Respond; feedback| Propose
    Review -->|Ignore; deferred| Done
    Review -->|Accept exact config hash| Extract["extract · shared engine"]
    Extract -->|Completed| Done
```

`build_graph()` registers conditional edges for every node using the returned `state["route"]`; `"end"` maps to LangGraph `END`. The diagram shows the routes the node implementations actually emit. `START` dispatch is distinct from resuming a checkpointed interrupt. Exhausted proposal versions also route to `END` with `needs_review`; this status does not itself create an Inbox approval packet. Wrapped-node exceptions route to `END` with `failed` or `budget_exhausted`; framework interrupts propagate normally. `final` is not wrapped by `safe_node`, so an unexpected exception there surfaces as a graph error.

| Node | Work and model involvement | Saved evidence / next step |
|---|---|---|
| `inspect` | Inspect physical structure; model returns `AnalysisPlan` with reader, grain hypothesis, uncertainty and optional Python. Parse using the proposed reader. | Save analysis and partition artifacts. Reader errors retry up to three structural attempts; success → `explore`. An existing analysis skips reinspection. |
| `explore` | Execute the proposed Python once when present, using up to 300 discovery records and supplied documentation. No model call here. | Save code, bounded output, exit status and duration → `propose`. An existing exploration artifact is reused; an execution failure is retained as feedback, not automatically retried. |
| `propose` | Model returns `MappingSpec`, using discovery examples, ontology, exploration, prior diagnostics and human feedback. Reader must stay frozen. | Save immutable mapping version and hash → `validate`. Malformed output retries `propose`; version/call budgets still apply. |
| `validate` | Run the shared validator on up to 250 validation records; check the reader matches the frozen reader. No model call. | Save diagnostics → `critique` on pass, otherwise `propose`. Bounded examples become feedback data. |
| `critique` | Separate model call returns `SemanticReview` about subject role, ownership, field meaning and evidence. Uses the same configured model, not an independent ground-truth judge. | Save critique → `final` when acceptable with no blockers, otherwise `propose`. One format retry is allowed; the second malformed critique fails. |
| `final` | Validate the frozen proposal on the next unused slice of up to 100 final records. No model call. | Advance `final_cursor`, save record IDs and report. Pass saves the review packet → `review`; failure ends the attempt without a tuning loop. |
| `review` | Pause with `interrupt()` and an Agent Inbox payload. No model call; config editing is disabled. | Save an idempotent decision tied to the config hash. Accept → `extract`; Respond → `propose` with feedback; Ignore → `END`. |
| `extract` | Verify exact-hash approval, then extract the first up to 1,000 records in source order from the partition pool. No model call. | Save immutable observations, extraction artifact and completed status → `END`. Later cohort assembly is a separate deterministic operation. |

### State: what is checkpointed versus persisted

The graph uses `State(TypedDict, total=False)`, with no message-history reducer. Nodes return partial state updates; large records and configs are retrieved through `run_id` rather than carried in the checkpoint.

| Location | Fields / contents | Purpose |
|---|---|---|
| Graph state | `run_id: str` | Locate the authoritative run, source and snapshot. Required to execute nodes even though the TypedDict allows partial updates. |
| Graph state | `route: str` | Select the next node or `end`; this is a control-flow value, not the run's business status. |
| Graph state | `feedback: str` | Carry malformed-proposal feedback or the human's revision request into `propose`; cleared after a valid proposal is stored. |
| LangGraph checkpoint | State, execution position and pending interrupt | Resume the workflow. The development server supplies the checkpointer; tests can inject one through `build_graph(checkpointer=...)`. |
| PostgreSQL run record | Status, mapping/version, artifact references, validation/critique, final cursor, approval ID, counters and timing | Persist progress, decisions and measurements beyond a single node call. `run_data()` reloads it; `update()` saves changes. |
| PostgreSQL evidence records | Source/snapshot metadata, immutable mappings, approvals, observations and events | Preserve provenance and exact configuration identity. |
| Content-addressed artifacts | Analysis, partitioned records, exploration output, review Markdown and extraction results | Store larger evidence payloads. The agent receives selected context, not arbitrary filesystem access to these artifacts. |

```mermaid
flowchart LR
    Checkpoint["LangGraph checkpoint: run_id, route, feedback, interrupt"] --> Node["Executing node"]
    Node <-->|Load run; persist decisions| DB[(PostgreSQL)]
    DB -->|Artifact IDs| Artifacts[(Content-addressed evidence)]
    Artifacts -->|Selected discovery context| Model["Luna structured call"]
    Artifacts -->|Discovery records and documentation only| Sandbox["Restricted Python container"]
    Model -->|Typed result| Node
    Sandbox -->|Bounded output| Node
```

### Tools and typed model responses

The graph controls which operation runs next. There is **no generic `ToolNode` or ReAct tool-selection loop**. [llm.py](../src/link_lens/llm.py) uses `with_structured_output(..., method="function_calling", include_raw=True)` to obtain validated Pydantic responses. The model's optional Python is a field in `AnalysisPlan`; the `explore` node invokes the sandbox wrapper explicitly.

| Interface | Who invokes it? | Input → output / boundary |
|---|---|---|
| `call(..., AnalysisPlan, ..., "inspect")` | `inspect` | Source documentation + structural preview → reader, grain, uncertainties and optional investigation code. |
| `call(..., MappingSpec, ..., "propose_mapping")` | `propose` | Evidence + ontology + bounded feedback → declarative mapping. No embedded extraction Python. |
| `call(..., SemanticReview, ..., "semantic_critique")` | `critique` | Proposal and evidence → acceptability, blockers and warnings. Quality check, not measured accuracy. |
| `inspect_resource()`, `read_records()`, `partition()` | `inspect`, as ordinary Python functions | Snapshot bytes → structural preview, parsed pool and disjoint partitions. Not model-callable filesystem tools. |
| `python_tool()`, traced as `execute_discovery_python` | `explore` | Proposed code + supplied discovery records/documentation → bounded execution output. The container receives no credentials, network, repository or Docker socket. |
| `validate()` | `validate` and `final` | Mapping + designated records → deterministic report. Final-test rows are not supplied to the model for revision. |
| `interrupt()` / resume response | `review` and Agent Inbox | Review packet → Accept, Respond or Ignore. Acceptance binds the stored hash, never returned edited config arguments. |
| `extract()` | `extract`, after approval | Approved mapping + records → observations and issues. No per-record LLM calls. |

**Why this is agentic:** model decisions affect reader choice, exploration code and mapping semantics; actual parser/validation/critique/human feedback changes later proposals. **What is bounded:** default limits are eight mapping versions, fifty model calls, ten Python executions, 9,000,000 input tokens and 2,000,000 output tokens per attempt, plus a 900-second active-time limit and the configured cost budget. Token totals are cumulative across model calls; each call still reserves up to 7,000 output tokens. These are the current defaults; preserved submission runs used the earlier limits of twelve model calls, 100,000 input tokens and 24,000 output tokens. The graph normally offers one optional Python investigation, not ten automatic exploration iterations. Reader and critique repair loops also consume the call budget. A human revision traverses validation and critique again and consumes another unused final slice before fresh approval.

For evidence, inspect [saved onboarding runs](../outputs/onboarding/) and [current approval packets](../outputs/README.md). [Graph tests](../tests/test_graph.py), [budget tests](../tests/test_budgets.py) and [review recovery tests](../tests/test_review_recovery.py) exercise these boundaries. This design reference does not imply every saved source used Python or needed every revision path.

## Implementation notes

**Current approach:** Jev triage + Luna onboarding, completed batch and AI audits. [Live status](../outputs/README.md) and [comparison](../outputs/COMPARISON.md) supersede prior measured outcomes below. Historical examples and acceptance results below describe the preserved Terra baseline unless explicitly dated as the new run.

### Work scope and time

This is the expanded reusable-project implementation requested after the educational walkthrough. Docker services, sandbox broker, Agent Inbox, PostgreSQL and OKF viewer go beyond the assignment's minimum. Do not present this project as six hours of work.

Development began in the preceding active session on 2026-09-17 UTC and continued after a user pause on 2026-09-18 UTC. The complete active development duration was not instrumented from the start and is **unknown**. Container creation times and the long pause are not development-time measurements. Runtime onboarding seconds are separately measured in usage receipts. Subsequent explicitly recorded work intervals belong in `docs/work-log.jsonl`; do not reconstruct precise hours from file timestamps.

### Implemented boundaries

One graph controls inspection, optional isolated exploration, typed proposal, deterministic validation, independent semantic critique, final holdout and mapping-level review. The model has discovery samples and bounded validation feedback. It receives no path/file-reading tool into the repository or full snapshot. The broker accepts supplied discovery records, not a snapshot path. The model does not run the extractor as generated code.

The initial physical reader is frozen before record partitioning. Structural reader errors now return bounded diagnostics to the model for at most three attempts before any partition is frozen. After partitioning, mapping revision cannot change the reader and invalidate the holdout. The seventh-source first attempt predated this repair loop and failed; the corrected run and original failure are both retained.

The initial six form a publisher/format portfolio selected from the generated shortlist. ASIC Credit Licensees is reserved for generalisation. A different resource in the same publisher family is a modest transfer test, not proof of arbitrary-source generalisation.

### Observed engineering failures

1. Docker `put_archive` and `get_archive` do not provide the desired live read/write access to our read-only-root tmpfs setup. Input is now copied with bounded fixed-path exec operations; output is read through a bounded fixed-path exec operation. Agent code still receives no mounts, network or daemon socket.
2. LangGraph file-path imports do not preserve package-relative imports. `langgraph.json` now uses installed module paths.
3. In the installed LangGraph version, `GraphInterrupt` is an Exception. A generic error wrapper initially swallowed it in a deterministic test. It is now explicitly re-raised, and the graph test covers interrupt/revision/resume.
4. Agent Inbox's native Accept response carries `args: null`. The backend binds acceptance to the immutable config at the paused review node. An explicit CLI hash is checked; an edited object never replaces the saved config. Direct config edits are disabled.
5. First live Companies run produced unqualified canonical field names because the tool schema described `canonical_field` as an unrestricted string. Validation rejected all three attempts. The shared contract now exposes the exact ontology enum. Failed calls remain in the usage ledger; the corrected run is a separate attempt.

### Confidence and timestamp policy

Source reliability, field mapping confidence and linking rule score remain separate and uncalibrated. Checksums validate identifier shape, not whether a source assigned it to the correct subject. A publication proxy is not a company-change date. Timezone-naive CKAN timestamps are marked with an explicit UTC assumption. Missing timestamp evidence quarantines records.

### Current scale limits

As submitted, the implementation used bounded in-memory source samples, JSON payload tables and individual upserts. It was appropriate for the demonstration, not 15 million companies. At 500 sources the first practical bottlenecks are review throughput and acquisition/schema-drift management, followed by database write batching and index design.

The production work since then addressed the storage part of that list: typed relational columns and indexes, observations and source records in hash partitions, bulk loading with `COPY`, an object storage backend for artifacts, refresh facts and a drift check per source, and read models for serving. What it did not change: the pipeline still reads bounded samples into memory and recomputes a batch as a whole, there are no worker leases or scheduled refreshes, and review throughput is still one person in the Inbox. The data is still 60 profiles from six sources, so nothing has been measured at scale beyond synthetic sets of about 100,000 pages. The [production plan](PRODUCTION_PLAN.md) names what to revisit first in its risk table.

6. AFS critique incorrectly claimed an 11-digit ABN could also pass the 9-digit ACN validator. The critique prompt now receives authoritative operation semantics. It remains a fallible check, not ground truth.
7. Date transformations initially allowed DD/MM/YYYY as a string argument, although Python requires `%d/%m/%Y`. The shared typed operation now describes and validates strptime directives.
8. The seventh source initially selected tab despite a coherent comma-delimited preview. A shared pre-partition reader-repair loop and explicit preference for actual-resource evidence were added. The later run reached review in three model calls; this is not an untouched holdout experiment.

## Verification evidence

The promoted expanded-ontology run passed **106 deterministic tests; four gated integrations skipped**. Tests cover immutable ontology versions, legacy replay, exact approvals, held-out separation, scoped grouping, missing financial values, concurrent budget reservations, interruption receipts, cache isolation and archive fixtures. Ruff F and export/link checks passed. [Recorded checks](../outputs/checks.json).

The six approved mappings yield 60 profiles and 61 links, with 79,840 observation occurrences / 79,113 unique claims. Both OKF exports have 1,676 documents, 3,220 citation edges and no broken internal links. Human evidence review remains pending; saved mapping approvals do not measure link precision.

Earlier runtime/checkpoint repairs, Terra/Luna audits, Docker checks and live archive restore measurements are preserved in the [historical engineering guide](../experiments/jev-luna-v1-submission/docs/ENGINEERING.md). They do not establish a live restore or human evaluation for this expanded experiment.

With the production data model and the product service, on 15 November 2026 the suite is **229 passed, four gated integrations skipped**, on PostgreSQL. The added tests cover each migration up and down, exact read-back of every record from the typed tables, append-only tables, role permissions, the ontology gate, releases and the OKF tree, every REST route and MCP tool, source scope, limits, bundles, and the published contracts. For the submitted data itself the evidence is the migration baseline: after every phase the stored rows and the same records read back from the typed tables matched it with zero differences. No model call, mapping approval or human evaluation was made for that work, and the counts in the paragraphs above are unchanged.

## Operations and recovery

The selected submission configuration is `jev-gpt6-luna-ontology-v1`. Exact promoted run, batch, ontology and snapshot IDs are in `outputs/submission-manifest.json`. Its outputs are in `outputs/`.
The previous deterministic + Terra run remains in `experiments/terra-baseline/`;
`manifest.json` hashes its archived files. Do not overwrite that archive or reuse its approvals.

### Database layout, migrations and the baseline

The [production plan](PRODUCTION_PLAN.md) moved the store from 17 generic JSON tables to typed tables, one domain at a time, and added a read-only product service on top. This section says how the result works and how to operate it. It follows the order in which the phases were applied to the local database, and each part ends with what was measured on that day; the plan has the reasons and the full results.

Where things stand on 15 November 2026:

| Part | State |
|---|---|
| Schema | Migration `0029`. Records live in `ontology`, `catalog`, `onboarding`, `evidence`, `identity`, `ops` and `access`. `legacy` holds the earlier tables, read-only. `analytics` holds dbt's reporting models. |
| Application | Still reads and writes through `store.py`, which returns the same records as before. |
| What clients see | Views in `serving`, built by dbt, for a release that a person records. None is recorded on the local database. |
| Product service | Compose service `product` on port 18710: REST, MCP, bundle links and an entity viewer. It refuses every call until a release and a key exist. |
| Dagster, dbt and Grafana | [Orchestration plan](ORCHESTRATION_PLAN.md) phases D0 to D7: dbt owns and builds the serving views and the reporting models, Grafana shows three dashboards over those, and Dagster holds the data flow as assets with sensors on approvals and releases, a schedule that refreshes sources by their cadence, and alert sensors. Both tools are open source and run in local Docker, for development or, with an override, as a deployment. Cut over on 2026-11-15 (see [Routine operation](#routine-operation-where-each-routine-runs)): every source has a cadence and Dagster refreshes it; alerts are logged, not sent, by the owner's choice. |
| Operations console | Compose service `admin` on port 18720 (profile `console`): sources, releases, clients and an audit log, for a signed-in person. Its sign-in is a list of tokens; no identity provider is connected. |
| Not done | The end of the side-by-side period on 2026-11-29; recording completed full extractions, so that a snapshot extracted only in part is visible; hosting, an identity provider for reviewer sign-in, the agent runtime licence and dropping `legacy`. |

| To do this | Read |
|---|---|
| Apply a new migration to a database that holds data | [Changing a database that holds data](#changing-a-database-that-holds-data) |
| Record a release, export it, manage keys | [Releases and the OKF tree](#releases-and-the-okf-tree-migration-0018), [Product service and REST](#product-service-and-rest-migration-0019) |
| Connect an agent | [MCP interface](#mcp-interface) |
| Build a bundle | [Bundles and the entity viewer](#bundles-and-the-entity-viewer-migration-0020) |
| Run more than one instance, a replica, metrics, a bucket | [Running as a service](#running-as-a-service-migration-0021) |
| Run dbt or the Dagster UI | [Dagster and dbt foundations](#dagster-and-dbt-foundations-migration-0022) |
| Change a serving read model, or build the views on a database | [dbt owns the serving views](#dbt-owns-the-serving-views-migrations-0023-and-0024) |
| Add a reporting model or a dashboard panel, or open the dashboards | [Reporting models and dashboards](#reporting-models-and-dashboards-migration-0025) |
| Refresh a source, extract it, or see what Dagster would do | [Dagster runs the data flow](#dagster-runs-the-data-flow-migrations-0026-and-0027) |
| Set a cadence, pause a source, connect alerts, backfill after a mapping change | [Schedules, freshness and alerts](#schedules-freshness-and-alerts-migration-0028) |
| Run Dagster as a deployment, rebuild its image, back up | [Dagster and dbt as a deployment](#dagster-and-dbt-as-a-deployment) |
| Add a source, record a release or manage clients without a terminal | [Operations console](#operations-console-migration-0029) |
| Know where a routine runs now, and what the CLI is still for | [Routine operation](#routine-operation-where-each-routine-runs) |
| Something failed and needs a person | [RUNBOOKS.md](RUNBOOKS.md) |
| Restore somewhere else and check it | [Restoring into an empty environment](#restoring-into-an-empty-environment) |

#### Routine operation: where each routine runs

Phase D7 of the [orchestration plan](ORCHESTRATION_PLAN.md) moved the routines off the terminal. Running the product day to day needs no command: the data flow runs in Dagster, people decide in the Agent Inbox and the console, and the dashboards and alerts say what needs them. The CLI stays, for one-off work, for recovery, and for the decisions that have no screen yet; the last column says what each command is still for.

| Routine | Where it happens | Who | The command, kept for |
|---|---|---|---|
| Check each source for a new file | Dagster schedule `due_sources`, every 15 minutes, for sources whose cadence is due | Nobody | `source check`: try one now, end a backoff |
| Drift check and extraction of a new file | The same run, `refresh_source`; after a new approval, the sensor `mapping_approved`. A run whose worker or engine failed is run again from the failure by the daemon, twice at most | Nobody | `source drift`, `source extract`, `source backfill`: look, or catch up after a mapping change |
| Rebuild the serving views and reporting models | Dagster sensors `release_recorded` and `models_missing` | Nobody | `dbt build`: a database Dagster does not watch, recovery |
| Bundles of the scopes that follow a release | Built by recording the release | Nobody | `release bundle`: rebuild one, or a client's bundle |
| Keep Dagster's run history short | Dagster schedule `prune_run_history`, nightly | Nobody | None |
| Back up both databases | Compose service `backup` (profile `backups`), daily, once a person starts it | Nobody, once started | `scripts/backup_databases.sh`: a backup now, before a migration |
| Add a source | Console: search, preview, confirm | Product owner | `register`, then `onboard` |
| Set how often a source is checked, pause or resume it | Console, the source's page | Product owner | `source cadence`, `source pause`, `source resume` |
| Review a proposed mapping | Agent Inbox | Reviewer | `review` |
| Onboard again after drift (paid) | Dagster UI: materialise `onboarding_request` for the source | Engineer | `onboard`, `recover` |
| Assemble a batch | Dagster UI: launch the job `assemble_batch`, or turn on the schedule `weekly_batch` | Engineer or product owner | `assemble` (no run IDs: the same step) |
| Compare a batch with the current release and record a release | Console, Releases | Product owner | `release preview`, `release create` |
| Clients, tiers and keys | Console, Clients | Admin | `access` |
| Promote an ontology | Command line only | Reviewer | `ontology gate`, `ontology promote` |
| Name a bundle scope, build a client's bundle | Command line only | Product owner | `release scope`, `release bundle --client` |
| See what is due, stale, failing or drifted | Console home, Grafana's source health dashboard, alerts, the Dagster UI | Everyone | `source due`, `source state` |
| See cost and usage | Grafana's product overview dashboard | Everyone | `usage`, `access usage` |

What still needs a person who can use a terminal is not routine: a migration (the procedure under [Changing a database that holds data](#changing-a-database-that-holds-data)), a restore, recovering an onboarding run, an ontology promotion, and the evaluation work of the submission. The submission's own path, "Run the six-source pipeline" in the README, stays as it is: it reproduces the submitted results and is not how the product is run.

**Cutting over a database that holds data.** Moving a stack from manual runs to this table is a set of decisions, each the owner's, in this order. The local stack was cut over on 2026-11-15; what the owner chose for it is under **The local stack's cutover** below.

1. People who sign in to the console: `LINK_LENS_ADMIN_USERS`, one token per person.
2. Backups: set `LINK_LENS_BACKUP_DIR` and `LINK_LENS_BACKUP_KEEP`, and start the `backup` service.
3. Where alerts go: `LINK_LENS_ALERT_WEBHOOK_URL` for the Dagster services.
4. The extraction left outstanding from before: snapshots registered by onboarding were extracted only as far as their review needed, and the schedule extracts only files whose bytes changed. Once, in the Dagster UI, materialise `observations` for all partitions (a backfill). The UI warns that the snapshots of some sources were never materialised in Dagster; that is expected, because those snapshots were registered before Dagster ran, and extraction reads them from the database. On a copy of the local database, extracting the six sources' files in full stored about 2.1 million observations; the local database holds 374,335. From a terminal the same is `uv run link-lens source extract SOURCE_ID` for each source. `link-lens source backfill` does not find this case: it looks for a snapshot with no observations under the mapping in force, and a snapshot extracted in part has some.
5. A cadence for each source, in the console. The schedule starts checking the next quarter hour.
6. If wanted, the deployment override for the Dagster services (see [Dagster and dbt as a deployment](#dagster-and-dbt-as-a-deployment)).
7. A period of side-by-side running before nobody runs the commands any more. Compare by content, not by observation ID: an observation's ID includes the time its file was downloaded, so two environments that each download the same file give the same observations under different IDs. Within one database, Dagster and the CLI give the same IDs, batches and releases.

**The local stack's cutover.** Done on 2026-11-15 by the owner's decisions:

| Decision | What the owner chose |
|---|---|
| Who signs in to the console | The owner, as admin |
| How often each source is checked | Every 7 days for ACNC Registered Charities and the three ASIC registers (Financial Services Licensees, Business Names, Company), which change within days; every 30 days for Corporate Tax Transparency (published annually) and Employment Services Provider Locations (last changed 2016) |
| Where alerts go | Nowhere: the owner looks at the Dagster UI and the source health dashboard. Each alert is a line in the Dagster daemon's log |
| Backups | Daily, into `/Users/may/link-lens-backups`, keeping the newest 3 dumps of each database because the disk is nearly full. A dump taken just before the cutover, `linklens-pre-cutover-20261115T102958.dump`, is kept by name |
| The outstanding extraction | After the first scheduled check |
| Side by side | Until 2026-11-29, two weekly checks |
| Deployment mode for Dagster | Not yet; development mode stays |

What happened: the cadences were set at 10:30 UTC. At 10:45 the schedule refreshed five sources, and at 11:00 the sixth; all six runs succeeded. Four files had changed since September and were extracted in full under their approved mappings (4 snapshots, 4 runs of kind `refresh`, 2,064,418 observations), and every drift check was `unchanged`. The two unchanged sources were then extracted in full with `link-lens source extract` (44,900 and 4,847 observations); extracting again stored nothing. The database went from 374,335 observations to 2,488,500. Every source is `fresh`, next due on 2026-11-22 or 2026-12-15. The legacy baseline check still reports zero differences; the typed check against the recorded baseline reports 56, all of them additions (27 counts up, 27 digests of sets that grew, the new run kind `refresh`), none missing or smaller. All 149 dbt tests pass, the reconciliations included. A dump of the database is now about 270 MB, so three take about 0.8 GB.

**Backups without a terminal.** The service runs `deploy/backup-loop.sh`, the same dumps as `scripts/backup_databases.sh`: both databases each day, each checked to list and given a checksum. It keeps the newest `LINK_LENS_BACKUP_KEEP` dumps of each database (7 by default) and removes older ones only after a new dump of that database has been written and checked, so a run of failures never leaves fewer good copies. It touches only files named `<database>-<time>.dump` and their checksums; a dump named otherwise, such as `linklens-pre-<something>.dump` taken before a migration, stays until a person removes it. A `linklens` dump is about 270 MB since the cutover. Set the folder and the number kept first:

```sh
# .env: LINK_LENS_BACKUP_DIR=/path/to/backups and LINK_LENS_BACKUP_KEEP=3
docker compose --profile backups up -d backup
docker compose --profile backups logs backup --tail 10
```

Artifact bytes are in neither dump; copy `artifacts/` or the bucket with them.

#### Foundations (migrations 0003 to 0008)

Phase 0 changed where the 17 generic tables are and how their payload is typed, and nothing else.

- **Layout.** Migrations `0003` to `0008` enable `vector` and `pg_trgm`, create the schemas `ontology`, `catalog`, `onboarding`, `evidence`, `identity`, `ops`, `access`, `serving` and `legacy`, move the 17 tables into `legacy`, and convert `payload` from `json` to `jsonb`. The eight new schemas other than `legacy` were empty until their phase.
- **Image.** Compose uses `pgvector/pgvector:pg17-trixie`. The plain `pg17` tag is a Debian bookworm build (glibc 2.36); a data volume created by `postgres:17` on Debian trixie (glibc 2.41) would report a collation version mismatch under it.
- **Helpers.** The `sha256` domain stores a digest as 32 bytes; `link_lens.db.Sha256` presents it to Python as the usual 64-character hex string. `forbid_update()` is the trigger function for append-only tables. `link_lens.db.copy_insert` loads rows with `COPY` into a staging table followed by `INSERT ... ON CONFLICT DO NOTHING`, so a repeated load inserts nothing.
- **Roles.** `linklens_migrator` owns the schemas, `linklens_pipeline` reads and writes the core schemas and, since migration `0017`, only reads `legacy`, and `linklens_product` reads `serving` and the access tables. They are `NOLOGIN` groups without passwords; the local stack still connects as the `linklens` superuser. `DELETE` is not granted by default.
- **Migrations are explicit SQL.** `migrations/env.py` has no metadata and does not autogenerate. Each migration runs in its own transaction. `alembic downgrade base` drops the tables and is only for an empty database; on a database with data, downgrade to `0002`.
- **jsonb and key order.** `jsonb` keeps every value but reorders object keys. Stored IDs and hashes are computed with sorted keys and do not change. Files regenerated from payloads (for example `mapping-v1.json`, `run.json`, `events.json`, `cost-usage.json`) list the same values with keys in a different order. OKF pages are rendered from artifacts and are unaffected.

#### Ontology registry (migration 0009)

The ontology registry (migration `0009`, Phase 1) is the first typed domain. Its tables are created as `linklens_migrator`, so `linklens_pipeline` receives its default privileges. `uv run link-lens backfill ontology` copies versions, proposal evidence, activations and proposals from `legacy.ontologies` and `legacy.ontology_events`; it is idempotent, verifies each copy against its legacy record before committing, and leaves the legacy rows and the model cache where they are. New ontology records are written only to the registry. `freeze` now writes archive format 2, which adds the registry rows; `thaw` still reads format 1 and runs the backfill after restoring it.

On 2026-11-14 the local database moved from `0008` to `0009` and was backfilled: 2 versions, 59 concepts, 3 proposals with 393 dispositions and 45 concept decisions, and 2 activations. `ontology show` and `ontology diff` printed the same bytes as before for both versions, and the baseline check reported zero differences.

#### Evidence spine (migrations 0010 to 0014)

The evidence spine (migrations `0010` to `0012`, Phase 2) moves artifacts, sources, snapshots, runs, mappings, approvals and observations to the `catalog`, `onboarding` and `evidence` schemas. Callers still use `store.put`, `get`, `require` and `listing`; `store.py` routes these seven tables to the typed repositories.

- **Exact records.** A source, snapshot, run, mapping or approval reads back exactly as it was written. A field sits in its typed column when the value is present and well formed, and in the row's JSON column otherwise. A reference column is filled only when the row it points at exists, so no foreign key dangles; `link-lens backfill spine` reports values that stayed outside their column.
- **Observations.** `evidence.observation` references its source record, concept and mapping config. Licence, snapshot, locator, roles and source reliability are read through those references instead of being copied onto each row, and each observation still reads back exactly as the extractor produced it. `store.put_observations` loads them with `COPY`; an observation that is already stored is skipped. The legacy `owner_id` of an observation (whichever run or source stored it first) is not kept.
- **Mapping configs.** A config is stored once in `onboarding.mapping_config` under its content hash, and `onboarding.mapping` references it, because two runs may propose the same config. `onboarding.mapping_field` indexes each config's fields by concept.
- **Partitions.** Source records and observations are each 32 hash partitions on `source_id` (migration `0013`). The count does not grow with the number of sources; a source's rows stay in one partition and the two tables stay aligned.
- **Refresh facts.** `catalog.source_refresh` stores each source's intended cadence and last check; the view `catalog.source_state` adds the latest snapshot, when the bytes last changed and the approved mapping in force. `link-lens source state`, `source cadence SOURCE --days N` and `source drift SOURCE` read, set and check them. `drift.detect` compares a snapshot's header with the approved mapping and is not scheduled anywhere.
- **Exit codes.** 0 the command did its work, 1 it failed, 2 it was called wrongly, 3 it ran and found something that blocks the next step (a failed gate check, blocking drift).
- **Artifacts.** `blobs.py` writes bytes to the local artifact directory or, with `LINK_LENS_ARTIFACT_STORE=s3`, to an S3-compatible bucket read through a local cache. `catalog.artifact.uri` records where each artifact is. The S3 backend is tested with a stand-in client only, not against a real bucket.
- **Archives.** `freeze` reads records through the store, so an archive has the same shape whether a table is generic or typed.

```sh
uv run link-lens backfill spine
uv run python scripts/migration_baseline.py --typed --check outputs/local-run/migration-baseline.json
```

`backfill spine` copies in dependency order, is idempotent, and verifies that every copied record reads back exactly as its legacy row. The `--typed` check computes counts and digests per table, experiment, batch and mapping config from the typed schemas and compares them with the baseline.

On 2026-11-14 the local database moved from `0009` to `0012` and was backfilled in 58 seconds: 26,610 artifacts, 949 sources, 12 snapshots, 73 runs, 107 mappings in 107 configs with 602 mapping fields, 52 approvals, 23,101 source records and 374,335 observations. No observation needed its JSON column. Eleven runs name a pseudo-source (`ontology`, `connectivity-test`) and eight a snapshot that was never stored; those values stay in the run's JSON column. Both baseline checks reported zero differences, a second backfill copied nothing, and `evidence.observation` takes 223 MB where `legacy.observations` takes 722 MB. The same day the two evidence tables were rebuilt as hash partitions (`0013`, 8 seconds) and the refresh table and view were added (`0014`); both baseline checks again reported zero differences. Before that, on a restored copy, eight CLI commands printed the same bytes as before and an export of the submission batch produced the same 1,747 files with equal values.

#### Identity and operations (migrations 0015 to 0017)

Identity and operations (migrations `0015` to `0017`, Phase 3) complete the move: batches, triage decisions, cached model responses, model calls, events, evaluations, entities, memberships, links and profiles are served from the `ops` and `identity` schemas, and the pipeline role can no longer write `legacy`.

- **Batches.** `assemble` and `enhance` write a batch and everything it owns in one transaction with `store.put_many`, batch first. The store's `batches` name still answers for batches, triage decisions (`triage-…`) and cached responses (`enhance-cache-…`), which are now three tables.
- **Profiles.** A profile's fields and addresses are rows in `identity.profile_field` and `identity.profile_address`; each keeps the field exactly and points at the observation or source record it cites. The profile reads back unchanged, so `profile_version` is unaffected.
- **Model calls.** A reservation in `ops.model_call` may change until it is settled; after that the database refuses any change. Usage events in `ops.event` are written when a call starts and completed when it ends. `ops.evaluation` holds the current label per item; human and AI labels have separate kinds.
- **Embeddings.** New embeddings are also stored in `ops.embedding`, with an HNSW index for cosine similarity. Cached embeddings from earlier runs are not copied.
- **Logs.** `link-lens` writes one JSON line to standard error when a command finishes or fails, with the command, exit code and duration. Results stay on standard output.

```sh
uv run link-lens backfill identity-ops
```

On 2026-11-14 the local database moved from `0014` to `0017` and was backfilled in 69 seconds: 26 batches, 1,067 triage decisions, 18,395 cached responses, 1,002 model calls, 9,178 events, 411 evaluations, 298 entities, 1,235 memberships, 621 links and 614 profiles with 3,465 fields. Both baseline checks reported zero differences. On a restored copy, re-running `assemble` for the promoted batch reproduced all 60 profile versions without a model call, and the reports and export matched the previous code's output.

#### Releases and the OKF tree (migration 0018)

Releases and the OKF tree (migration `0018`, Phase 4) are what a client sees.

- **Release.** `link-lens release create --batch-id BATCH --reviewer NAME` records that a batch, under the ontology its runs were onboarded with, is released, and builds that release's OKF page, line and index rows in the same transaction. It is a human action; no pipeline step calls it. A release never changes, and a later release does not touch an earlier one. `release list` and `release show` report them.
- **Serving views.** Each read model is one commented `SELECT`, and every view carries `release_id`. The `linklens_product` role can read `serving` and nothing else. As first built, the files were in `src/link_lens/serving/` and `serving.apply` created a view per file after every `alembic upgrade`. Since migration `0024` they are dbt models; see [dbt owns the serving views](#dbt-owns-the-serving-views-migrations-0023-and-0024).
- **Pages.** `okf/render.py` renders an entity, evidence, source, concept or index page from records, with no clock and no store, so a page of a release is the same bytes every time. Pages are not stored: `okf/tree.py` renders one when it is read.
- **Tree.** `tree.ls`, `read`, `find` and `grep` take a release and, optionally, the sources a caller may see. `grep` searches each page's frontmatter and its claims written as `concept: value`, and needs a folder below the root. An index page lists at most 200 entries; a larger folder is split by the next character of its names.
- **Bundle.** `link-lens release export DIR` writes a release's tree to a folder with the same functions and checks every link. `link-lens export` for a batch uses the same renderer and paths.

```sh
uv run link-lens release create --batch-id BATCH_ID --reviewer NAME
uv run link-lens release show
uv run link-lens release export outputs/local-run/release-1
```

On 2026-11-14 the local database moved from `0017` to `0018`. No release has been created on it. On a restored copy, a release of the submission batch produced the same 60 entity pages, 1,610 evidence pages and 6 source pages as `outputs/okf`, apart from link paths, key order and the generation time, with no broken link.

#### Product service and REST (migration 0019)

The product service (migration `0019`, Phase 5) is what a paying client calls. It is a separate process from the backend and only reads.

- **Access.** A tier is a row in `access.tier`: calls a minute, calls a month, interfaces, toolsets, sources, release lag and history depth. A client belongs to a tier and holds keys. A key is `ll_<prefix>_<secret>`; the prefix and the SHA-256 of the secret are stored, and the key is printed once by `link-lens access key create`. Creating tiers, clients and keys is a person's action.
- **A call.** `product/auth.py` turns `Authorization: Bearer` into a principal, `product/limits.py` refuses a call over the rate or the monthly quota and counts the others, and `product/queries.py` answers from `serving` for one release. Every query runs as `linklens_product`, which can read `serving` and the access tables and can write only usage counts.
- **Release and scope.** A key reads the latest release its tier allows (`release_lag`), or an older one with `?release=` within `history_depth`. A key limited to some sources sees only their sources, observations, evidence pages and links between them. Profiles are answered whole.
- **REST.** `interfaces/rest.py` holds the routes under `/v1`; the route table is in the [plan](PRODUCTION_PLAN.md#phase-5-access-product-service-and-rest) and at `/openapi.json`. Errors are problem details, lists use keyset cursors, every answer names its release in `X-LinkLens-Release`, and `Accept: text/markdown` on an entity returns its OKF page.
- **As first built, and since.** In this phase the rate limit was held in the process and the service logged in with the local user, setting its role per transaction. Phase 9 moved the bucket into PostgreSQL and lets the service log in as a role of its own; see [Running as a service](#running-as-a-service-migration-0021). Locally it still uses the local user.

```sh
docker compose up -d product          # http://localhost:18710, /health needs no key
uv run link-lens access tier set starter --rate-per-minute 60 --monthly-quota 10000 --interface rest
uv run link-lens access client create "Example client" --tier starter
uv run link-lens access key create CLIENT_ID --label first
uv run link-lens access usage
```

On 2026-11-14 the local database moved from `0018` to `0019`. No tier, client or key has been created on it. On a restored copy with a rehearsal release, all 60 profiles answered over REST matched the stored profiles, and every route answered in under 35 ms.

#### MCP interface

The MCP interface (Phase 6, no migration) offers the same data to agents from the same service.

- **Endpoints.** `/mcp` offers both toolsets, `/mcp/data` and `/mcp/files` one each. All use Streamable HTTP, answer in JSON and keep no session. The bearer key is the REST key; its tier needs `mcp` among its interfaces and at least one toolset.
- **Tools.** `interfaces/mcp_server.py` defines nine read-only tools, each one call into `product/queries.py`: `search_entities`, `get_profile`, `list_observations`, `get_evidence`, `describe_concepts`, and `okf_ls`, `okf_read`, `okf_find`, `okf_grep`. A key is shown only the tools of its tier's toolsets.
- **Results.** Each result has structured content and the same JSON, or the Markdown, as text, names its release, and is bounded: `next_cursor` or `next_offset` continues it. `get_profile` answers a summary that cites evidence by observation ID; `get_evidence` returns the record behind an ID.
- **Limits.** A tool call is counted under `mcp` and shares the client's monthly quota with REST. A call over a limit, an unknown entity or a bad argument is an error result the agent can read, with a status and, for a limit, the seconds to wait. A bad key is HTTP 401 or 403.
- **Hosts.** Set `LINK_LENS_MCP_ALLOWED_HOSTS` (a JSON list) to make the service refuse other Host headers; empty leaves that to the proxy in front.
- **Evaluation.** `scripts/mcp_agent_eval.py` runs ten fixed tasks with each toolset through an MCP client that has only a URL and a key, and fails when the two toolsets disagree. Its plans are written out; it calls no model.

```sh
uv run link-lens access tier set professional --rate-per-minute 300 --interface rest --interface mcp --toolset data --toolset files
LINK_LENS_API_KEY=KEY uv run python scripts/mcp_agent_eval.py --url http://localhost:18710
```

The backend, sandbox controller and product service share one image, which must contain the `mcp` package. After pulling a change to the dependencies, run `docker compose build backend` and `docker compose up -d` from the repository root. Compose runs the code of the folder it is started from, so started from another checkout it builds that checkout's code.

#### Bundles and the entity viewer (migration 0020)

Bundles and the per-entity viewer (migration `0020`, Phase 8) give real files of a release.

- **Scope.** A named scope such as `demo` is a list of at most 500 entities that a person sets with `link-lens release scope set`. `client:<client id>` is everything that client's tier may see.
- **Bundle.** `link-lens release bundle [RELEASE] --scope SCOPE` writes the files through the tree's renderer, checks every link, adds the vendored viewer and a `manifest.json` with each file's hash, and stores one gzip tar as an artifact. The same release and scope always make the same archive, so building again adds nothing. `release create` builds every scope marked to follow a release, after the release is committed; a bundle that fails is reported and can be built again.
- **Download.** `GET /v1/bundles/{release}` gives a key whose tier includes bundles a link to its client's bundle that expires in five minutes. The link is signed by S3 when the bundle is there, otherwise by the product service with `LINK_LENS_LINK_SECRET`.
- **Viewer.** `GET /v1/entities/{id}/viewer` returns the graph of one entity, its evidence and its sources as one HTML page, kept by profile version.
- **Generated OKF is not committed.** New OKF folders under `outputs/` are ignored. `outputs/okf` stays as submitted. `tests/fixtures/okf_bundle` is a small bundle that a test compares with the renderer; write it again with `UPDATE_FIXTURES=1 uv run pytest tests/test_fixture_bundle.py` when a change to a page is meant.

```sh
uv run link-lens release scope set demo --reviewer NAME --entity ENTITY_ID --entity ENTITY_ID
uv run link-lens release bundle --scope demo
uv run link-lens release bundle --scope client:CLIENT_ID
uv run link-lens release bundles
```

#### Running as a service (migration 0021)

Running as a service (migration `0021`, Phase 9). What needs a hosting provider is not done; the [plan](PRODUCTION_PLAN.md#phase-9-production-infrastructure-and-cutover) lists it.

- **Primary and replica.** Give the product service `LINK_LENS_PRODUCT_DATABASE_URL` and `LINK_LENS_PRODUCT_REPLICA_URL`. It reads the key, applies limits and counts the call on the primary, and reads data from the replica. Each URL should be a login that is only a member of `linklens_product`; create it by hand, since a password does not belong in a migration: `CREATE ROLE linklens_product_service LOGIN PASSWORD '...' IN ROLE linklens_product`.
- **Limits across instances.** Each key's bucket is a row in `access.rate_bucket`, so any number of instances share it. `LINK_LENS_RATE_LIMIT_STORE=memory` keeps it in the process, for a single instance.
- **Logs and metrics.** Each request is one JSON line on standard error with `request_id`, route, status, `ms`, `key_prefix`, `client_id` and `tier`; the ID is also the `X-Request-ID` response header, and one sent by the caller is kept. Set `LINK_LENS_METRICS_TOKEN` to open `/metrics` to a scraper that sends it as a bearer token. `deploy/alerts.yml` holds Prometheus rules for error rate, slow answers and silence.
- **Artifacts to object storage.** With `LINK_LENS_ARTIFACT_STORE=s3` and a bucket, `link-lens artifacts migrate --dry-run` reads every local artifact and checks its hash; without `--dry-run` it copies each, checks the stored bytes and records the new location. It deletes nothing and can be run again. Exit code 3 means an artifact was missing or did not match.
- **Published contracts.** `docs/api/openapi.json` and `docs/api/mcp-tools.json` are what clients build against. A test fails when the code differs; `UPDATE_CONTRACTS=1 uv run pytest tests/test_production.py` writes them again when the change is meant.

#### Dagster and dbt foundations (migration 0022)

Dagster and dbt foundations (migration `0022`, phase D0 of the [orchestration plan](ORCHESTRATION_PLAN.md)). Both tools are installed and run; neither does any work yet. The plan says what each later phase adds.

- **Dependency groups.** `orchestration` (Dagster 1.13, dagster-webserver, dagster-postgres, dagster-dbt) and `transform` (dbt Core 1.12, dbt-postgres 1.11) are installed by `uv sync --frozen --group orchestration --group transform`, never by a plain `uv sync`. The backend image installs no group, so the backend, product service and sandbox controller contain neither tool. The lock file is shared by every group: adding these moved `pathspec` in the backend image from 1.1.1 to 1.0.4.
- **Schema and role.** `analytics` is owned by `linklens_migrator` and filled only by dbt. `linklens_transform` is a `NOLOGIN` group like the other three: it reads `ontology`, `catalog`, `onboarding`, `evidence`, `identity`, `ops` and `serving`, including tables the migrator creates later, reads `access.tier`, `client`, `api_usage` and every column of `api_key` except `key_hash`, and as of `0022` may create relations only in `analytics`. It cannot read `legacy` or `access.rate_bucket`. Migrations `0023` and `0024` later let it create in `serving_next` and `serving`. The downgrade of `0022` drops whatever the role owns, which is only relations dbt can build again.
- **dbt.** The project is `transform/`. Its profile has one target, configured by the environment, and sets the role `linklens_transform` on every connection, as the product service sets its own. `uv run link-lens dbt ARGS` runs dbt with the connection taken from `LINK_LENS_DATABASE_URL` and returns dbt's exit code (0 done, 1 a model or a test failed, 2 dbt could not run what was asked). Run directly from `transform/`, dbt uses the `LINK_LENS_DBT_*` variables, which default to the local Compose database. A model's schema is used exactly as configured (`macros/generate_schema_name.sql`), because every developer has a database of their own and the product service reads `serving` by that name. dbt 1.12 loads a `.env` file from the working directory upward; it needs only the database settings.
- **Dagster.** The code location is the package `orchestration/link_lens_dagster`, loaded through `orchestration/workspace.yaml`, whose paths are relative to that file. `orchestration/dagster.yaml` is the instance configuration of the Compose services.
- **Dagster's own storage** is a database named `dagster` on the same server, owned by a login named `dagster`. `deploy/dagster-db.sql` creates both when they are missing and changes nothing that exists; the Compose service `dagster-db` runs it. That login can connect to the server but has no right on any schema of `linklens`. A `pg_dump` of `linklens` does not include it, which is intended: Dagster's history is not application data.
- **Compose.** `dagster-db`, `dagster-webserver` and `dagster-daemon` start only with the `orchestration` profile and use the image `link-lens-dagster:local` (`deploy/Dockerfile.dagster`). The UI is on port 18730, bound to this machine, and has no sign-in. The services are given no connection to `linklens` yet; phase D3 adds it with the first assets.
- **Nothing is reported to the vendors.** dbt's usage statistics and Dagster's telemetry and first-run dialog are switched off in `dbt_project.yml` and `dagster.yaml`.

```sh
uv sync --frozen --group orchestration --group transform
uv run link-lens dbt debug
uv run link-lens dbt build
uv run dagster definitions validate --workspace orchestration/workspace.yaml
docker compose --profile orchestration up -d --build     # http://localhost:18730
docker compose --profile orchestration stop dagster-webserver dagster-daemon
```

To remove Dagster's storage and start it empty again, stop the two services and run `DROP DATABASE dagster` as the `linklens` user; the next start creates it again. This deletes run history only.

On 2026-11-15 the local database moved from `0021` to `0022` after a fresh backup and a rehearsal on a restored copy, where one step down and up again was also run. Both baseline checks reported zero differences before and after, and the backend, Agent Inbox, sandbox controller and product service answered their health checks on an image rebuilt from the new lock file. `dbt debug` and an empty `dbt build` succeeded on the local database as `linklens_transform`, and the Dagster UI showed the code location `link_lens` loaded with no assets, jobs, schedules or sensors, its 22 tables in the `dagster` database and none in `linklens`.

#### dbt owns the serving views (migrations 0023 and 0024)

dbt owns the serving views (migrations `0023` and `0024`, phase D1 of the [orchestration plan](ORCHESTRATION_PLAN.md)). What clients read is the same; who creates it changed.

- **Models.** Each of the twelve read models is a file in `transform/models/serving/`, the SQL it was before with table names written as `source()` calls. dbt builds each as a view in `serving`, owned by `linklens_transform`, and grants `SELECT` to `linklens_product` and `linklens_pipeline`. The tables they read are declared in `transform/models/sources/sources.yml`.
- **Contracts.** `_serving.yml` declares every column of every model with its type, and the contract is enforced: a build fails when a column is added, removed, renamed or retyped without the contract changing too. Each model, column and source table has a description; `link-lens dbt docs generate` writes the documentation site to `transform/target/`.
- **Tests.** `link-lens dbt build` builds the views and then runs 96 tests on them: keys are unique and present, a profile field's observation and concept exist in the release, every observation has its evidence row and its source, statuses hold only known values, enum concepts hold only values the ontology registry allows, and no claim lacks a licence or a timestamp basis. `link-lens dbt run` builds without testing.
- **Migrations create no view.** `alembic upgrade head` creates tables. On a new database, after a restore, and after a downgrade that passed `0024`, run `link-lens dbt build`. The backend image has no dbt, so starting the backend does not do this. `link-lens release create` refuses, naming the command, when the views are missing.
- **Two owners in one schema.** In `serving`, dbt owns the views. Alembic owns the `okf_page`, `okf_line` and `okf_index` tables, which `release create` fills, and the functions `iso_utc`, `json_float` and `create_release_partitions`. A test fails if a migration creates a view there or dbt owns a relation outside `serving`, `serving_next` and `analytics`.
- **Changing a read model.** Build the candidate beside the live views, compare, then build where clients read:

```sh
uv run link-lens serving-compare --build   # exit 3 and a list when a view answers differently
uv run link-lens dbt build
```

`--build` builds the serving models, and only those, into `serving_next`. Do not build the whole project with another serving schema: the reporting models read the serving models by reference and would then read the candidate. `serving-compare` compares the two schemas view by view: the columns with their types, and for each release the row count and a digest over every row. A difference you meant, such as a new column, is listed like any other; read the list before building. A contract change is a change to what clients receive, so check `docs/api/` and the interface tests with it.

- **Source freshness.** `link-lens dbt source freshness` warns when the newest snapshot or release is older than 45 days. The number is a placeholder until sources have cadences.

On 2026-11-15, on a restored copy with two rehearsal releases, the dbt-built views in `serving_next` matched the hand-written views in every column, count and digest (up to 149,349 rows a view); after the switch the views in `serving` gave the same fingerprint and the same release digests, all 96 tests passed in 23 seconds, and the product service answered all 60 profiles with the stored profile version. The local database then moved from `0022` to `0024` with both baseline checks at zero differences; it has no release, so its views are empty.

#### Reporting models and dashboards (migration 0025)

Reporting models and dashboards (migration `0025`, phase D2 of the [orchestration plan](ORCHESTRATION_PLAN.md)). Nothing here is served to clients.

- **Models.** Sixteen models in `transform/models/analytics/`, built as views in the `analytics` schema: `usage_daily` and `usage_monthly`; `source_health`, `source_coverage` and `concept_usage`; `onboarding_run`; `identity_link_summary`, `identity_entity_support` and `batch_overview`; `model_cost` and `budget_ledger`; `release_overview`, `release_profile_changes` and `release_field_status`; `evaluation_summary`; `observation_validity`. `_analytics.yml` describes every column. They read 21 staging views (`stg_<schema>__<table>`), each one core table with its columns renamed and cast, or the serving models.
- **Tests.** Each model has a key test, and six tests check that totals equal the tables they come from. `evaluation_summary` keeps human review and AI audit in separate rows, and a test fails if a label is counted under the wrong kind.
- **Adding a model.** Write `transform/models/analytics/NAME.sql` as one `SELECT` over `ref()` calls, describe it in `_analytics.yml` with a key test, add a reconciliation test under `transform/tests/` if it adds things up, and run `link-lens dbt build`. The folder's settings give it its schema and its grant; no migration and no Python is needed. A core table not read before needs a line in `models/sources/sources.yml` and a staging view.
- **What the cost models are.** `model_cost` counts the calls `link-lens usage` counts, per stage, with tokens, the cost recorded when each call ran and the budget charge. It does not hold that report's list-price estimate, which is priced from saved response files. `budget_ledger` equals `budget.summary`.
- **Who can read.** `linklens_analyst` (migration `0025`) may use `analytics` and select the sixteen models; it cannot read a core table, a serving view, a staging view or a key. A person or a tool gets a login that is a member: `CREATE ROLE name LOGIN PASSWORD '...' IN ROLE linklens_analyst`.
- **Grafana.** `docker compose --profile dashboards up -d` starts `grafana-db`, which creates the login `linklens_grafana` when it is missing, and `grafana` (13.0.2) on port 18740, bound to this machine. Sign in as `admin` with `LINK_LENS_GRAFANA_ADMIN_PASSWORD` (`admin` when unset). The data source and the folder of dashboards are loaded from `deploy/grafana/provisioning/`; reporting to the vendor and update checks are off.
- **Dashboards.** `deploy/grafana/dashboards/` holds three JSON files: product overview, data quality and source health. Every panel queries `analytics.<model>`. A change made in the Grafana UI is not saved: export the dashboard's JSON, replace the file, add any newly read model to `transform/models/analytics/_exposures.yml`, and run `uv run pytest tests/test_dashboards.py`, which runs every panel's query as the analyst.
- **Links to evidence.** A source links to its dataset on the publisher's portal and to its OKF page, a concept and a release to their OKF pages. The OKF links go to the product service and need an API key, so they do not open from a plain browser click yet.
- **Not shown, because it is not stored:** the route or tool of a call, drift checks, why a record stayed unlinked, identifier checksums and records set aside for a missing timestamp.

```sh
uv run link-lens dbt build                     # serving views, reporting models and their tests
docker compose --profile dashboards up -d      # http://localhost:18740
docker compose --profile dashboards stop grafana
```

On 2026-11-15 the local database moved from `0024` to `0025` with both baseline checks at zero differences, and `dbt build` there passed 49 models and 147 tests. On a restored copy with two rehearsal releases the models reconciled with their tables and with `link-lens usage` (1,002, 6,001 and 52 calls for the three experiments), and all 38 panel queries answered through Grafana.

#### Dagster runs the data flow (migrations 0026 and 0027)

Dagster runs the data flow (migrations `0026` and `0027`, phase D3 of the [orchestration plan](ORCHESTRATION_PLAN.md)). It calls the library; the logic is in `src/link_lens/refresh.py`.

- **Steps.** `refresh.check(source_id)` downloads a source again and registers a snapshot only if the bytes changed. `refresh.check_drift` compares a snapshot with the mapping approved for the source and stores the result. `refresh.extract(source_id, snapshot_id, limit)` extracts a snapshot under that mapping and refuses when none is approved or the shape has drifted. `refresh.request_onboarding` starts an onboarding run for a snapshot, once. `refresh.assemble` assembles a batch. Each returns a small record and, except `assemble`, writes nothing when repeated.
- **Assets.** `snapshot`, `observations` and `onboarding_request` have one partition per registered source. `identity_batch` and `source_catalogue` have none. `models` is the dbt project: 49 models, each an asset. The jobs are `refresh_source` (snapshot, then observations), `extract_observations`, `request_onboarding`, `assemble_batch` and `build_models`.
- **Checks.** `schema_drift` on `snapshot` is blocking: when the snapshot no longer fits the approved mapping, extraction in the same run does not start. `observations` checks that every observation has its record and that everything extracted is stored; `identity_batch` that selected fields cite an observation and that counts match; and each dbt test is a check on its model.
- **Sensors.** `registered_sources` adds a partition per registered source. `mapping_approved` requests `extract_observations` for a source when a person approves a mapping. `release_recorded` requests `build_models` when a person records a release. `ontology_promoted` reports a promotion and starts nothing. `drift_detected` requests onboarding on blocking drift and is off until someone turns it on. Each starts from the present the first time it runs.
- **Unchanged means no work.** When the publisher's bytes are the same, `snapshot` emits nothing and `observations` does not run. Set `force: true` in the `snapshot` step's configuration to emit it anyway.
- **Role.** The Dagster services set `LINK_LENS_DATABASE_ROLE=linklens_orchestrator`, so every connection of the library takes that role (migration `0027`). It writes snapshots, runs, drift checks, records, observations, batches, entities, links, profiles and usage. It cannot insert or update an approval, an ontology activation, a release, a bundle scope, a bundle or a review label, and has no access to `access`, `serving` or `analytics`. An asset fails at once if the library is connected as anyone else. In production the login is a member of that role only.
- **Paid steps.** `onboarding_request` and `source_catalogue` spend on model calls. Dagster starts them only when a person materialises them (or turns on `drift_detected`), never retries them, and runs them one at a time (pool `model_calls`). `source_catalogue` refuses to run without `confirm_paid_calls: true`.
- **Stored drift checks.** `catalog.drift_check` (migration `0026`) has one row per snapshot and mapping config: status, whether it blocks, and the reasons. `link-lens source drift` still only prints; `source extract` and the assets record.
- **A release serves what was stored when it was recorded.** `evidence.observation.loaded_at` (migration `0026`) is when a row was stored; rows from before the migration carry 1970-01-01. `serving.observation` and `serving.evidence` take only the snapshot the release's run was onboarded on and only rows loaded by the time the release was recorded. Extracting more later changes no release.
- **A refresh reaches the next batch (phase D3a).** When `refresh.extract` extracts a snapshot other than the one the source was onboarded on, it records a run of kind `refresh`: completed, no model call, naming the mapping and the approval of the run it refreshes. No approval is created. `refresh.current_runs()` gives each registered source's run for its newest snapshot under the mapping in force, and `identity_batch` and `refresh.assemble` assemble from those. A batch still serves nobody until a person records a release, and a release recorded earlier does not change.
- **A batch after a refresh also changes by resampling.** Assembly is a sample: at least `minimum_profiles` linked entities and at most 1,000 records a source, chosen by record ID. A refresh gives every record of the source a new ID, so a different record can represent an entity and different extra entities link. On a copy, editing three rows changed a selected value for 16 of 59 common entities. Each profile is correct for the records it was built from; the difference between two batches is not a clean measure of what the publisher changed. The plan's D3a section has the detail and the choices.
- **Refresh runs and the baseline.** A refresh adds a run row, so the run counts of `migration_baseline.py --typed` differ from the baseline by the refreshes made, as the artifact count does for bundles. None has been made on the local database.

```sh
uv run link-lens source check SOURCE_ID                 # download again; no model call
uv run link-lens source extract SOURCE_ID --limit 25000  # exit 3 when blocked
docker compose --profile orchestration up -d             # http://localhost:18730
```

In the Dagster UI, a source is refreshed by materialising `snapshot` and `observations` for its partition (job `refresh_source`). To run the assets outside Dagster's services, set `LINK_LENS_DATABASE_ROLE=linklens_orchestrator` first.

On 2026-11-15, on a restored copy, a refresh of one real source with three edited rows went from changed bytes to a refresh run, a batch whose three profiles select the new values, and a release that serves the new snapshot, while two earlier releases kept their digests. Before that, also on a restored copy, the assets extracted 25,000 records a source for the six sources: every observation stored before was reproduced, 941,433 more were stored, a second extraction stored nothing, and the two rehearsal releases still served 38,302 and 149,349 observations. `identity_batch` twice reproduced the 60 profile versions of the deterministic batch behind the promoted one. The local database then moved from `0025` to `0027` with both baseline checks at zero differences; no asset has been materialised on it.

#### Schedules, freshness and alerts (migration 0028)

Schedules, freshness and alerts (migration `0028`, phase D4 of the [orchestration plan](ORCHESTRATION_PLAN.md)). Sources refresh on their own cadence and the team hears about problems. Both are idle until a cadence and a webhook are set.

- **Cadence.** `link-lens source cadence SOURCE --days N` sets how often a source is checked; `--days` left out clears it. The schedule `due_sources` asks `sources.due` every 15 minutes and requests `refresh_source` for each source it names: one with a cadence and an approved mapping, not paused, never checked or past its last check plus cadence, and not waiting out a failure. `link-lens source due` prints the same answer by hand.
- **Pause.** `link-lens source pause SOURCE --reviewer NAME` stops scheduled checks of a source and records who paused it; `source resume SOURCE` starts them again. A paused source is not overdue.
- **Politeness.** A check sends the `ETag` or `Last-Modified` of the last download of that resource; on `304` nothing is transferred, the check is recorded and the stored snapshot stays the latest. A failed check is counted, and the next attempt waits an hour, then two, then four, up to the cadence. One evaluation starts at most 50 refreshes and 5 for one publisher portal (`MAX_PER_TICK`, `MAX_PER_HOST` in `schedules.py`), and two downloads run at once.
- **Lateness.** `sources.overdue` lists sources overdue by more than an hour or with three failed checks in a row. The hourly check `sources_checked_on_time` shows it in the Dagster UI, and `analytics.source_health` and the source health dashboard show status, days overdue, failures, the last error, and drift.
- **Alerts.** Set `LINK_LENS_ALERT_WEBHOOK_URL` for the Dagster services (in `.env`) to an incoming webhook that accepts `{"text": ...}`, and recreate them. Five sensors then post one line each: a failed run, a check that did not pass, drift, a source overdue or failing, and the model budget at 80% and at its cap. Each names the source and links to the run or the asset (`LINK_LENS_DAGSTER_URL`, `LINK_LENS_INBOX_URL`). Without the URL each alert is one `alert.unsent` log line. The URL is a secret and is never logged.
- **Backfill.** After a mapping changes, `link-lens source backfill [SOURCE]` lists each registered source's latest snapshot, its observations under the mapping now in force, and whether it needs extracting or is blocked by drift. Nothing is written without `--apply`; the command exits 3 when a source is blocked. In Dagster, launch `extract_observations` for the same sources.
- **Batches.** `weekly_batch` is defined and stopped. Turn it on in the Dagster UI when a weekly batch is wanted; read phase D3a of the plan first.
- **Dagster's own history.** `prune_run_history` deletes finished runs older than 90 days every night; evaluations of schedules and sensors are kept 30 days.

```sh
uv run link-lens source cadence SOURCE_ID --days 7
uv run link-lens source pause SOURCE_ID --reviewer NAME
uv run link-lens source due
uv run link-lens source backfill              # a dry run
uv run link-lens source backfill --apply
```

On 2026-11-15 the local database moved from `0027` to `0028` with both baseline checks at zero differences. A test refreshes 300 fixture sources with mixed cadences for a simulated week, and another sends each alert type to a local webhook. No source has a cadence and no webhook is configured on the local stack.

#### Dagster and dbt as a deployment

Dagster and dbt as a deployment (phase D5 of the [orchestration plan](ORCHESTRATION_PLAN.md), no migration). By the owner's decision both are the open-source editions and run in local Docker. What to do when something fails is in [RUNBOOKS.md](RUNBOOKS.md).

- **One image.** `link-lens-dagster:local` (`deploy/Dockerfile.dagster`) holds open-source Dagster, dbt Core with the PostgreSQL adapter, the code location, the dbt project and the library, at the versions in `uv.lock`. It runs with nothing of the checkout mounted. Its entrypoint copies `orchestration/dagster.yaml` into `DAGSTER_HOME`, a volume, at every start. Rebuild it after any change the deployment should run:

  ```sh
  docker compose --profile orchestration build dagster-webserver
  ```

- **Two ways to run it.** Development: `docker compose --profile orchestration up -d` mounts the checkout over the image's code, logs in as the administrator and takes the orchestrator's role. Deployment:

  ```sh
  docker compose -f compose.yaml -f deploy/compose.deploy.yaml --profile orchestration up -d
  ```

  The override removes the mounts, restarts the services when they stop, and refuses to start without `LINK_LENS_DAGSTER_POSTGRES_PASSWORD` and `LINK_LENS_ORCHESTRATION_PASSWORD`. Use passwords without characters that need escaping in a URL. Run the migrations first.
- **The service login.** With the override, `dagster-db` also runs `deploy/service-logins.sql`, which creates `linklens_orchestration`: a login that inherits nothing and can only become `linklens_orchestrator` (the assets) or `linklens_transform` (dbt). Taken by itself it can read nothing. An existing login is left as it is; change its password with `ALTER ROLE`.
- **Views without a command.** The sensor `models_missing` requests `build_models` when views that dbt owns are missing, and `release_recorded` after a release. On a database Dagster watches, nobody runs `link-lens dbt build` after a migration or a restore.
- **dbt's documentation.** Each build writes the documentation site into Dagster's volume, and the service `dbt-docs` serves it on port 18731. When the service starts and finds no site there, it runs `dbt docs generate` first, which only reads the database; if that fails the folder is served as it is until the next build. To refresh it by hand: `docker compose exec -e DBT_LOG_PATH=/opt/dagster/home/dbt-target/logs dagster-webserver link-lens dbt docs generate --target-path /opt/dagster/home/dbt-target`.
- **No sign-in.** The open-source Dagster UI has none, and neither has the documentation server. Both, and Grafana, are published on the loopback address only. Publishing them further needs a proxy that signs people in.
- **Runs are processes, not containers.** Dagster's default launcher runs each run inside the service that launched it. The launcher that starts a container per run needs the Docker socket, which only the sandbox controller may have.
- **Backups.** `scripts/backup_databases.sh DIRECTORY [DAYS]` dumps `linklens` and `dagster`, checks each archive and writes a checksum. It prunes its own `dagster` dumps after 7 days and never deletes a `linklens` dump.
- **Upgrading a tool.** Change its pin in `pyproject.toml`, `uv lock`, compare `uv export --no-dev` before and after, rebuild the image, and try it on a copy. A Dagster upgrade may migrate Dagster's own database. dbt Core stays below 1.13 while dagster-dbt requires it.

On 2026-11-15 a second Compose project was run as a deployment beside the real stack, on a restore of the newest backup: the services worked as `linklens_orchestrator` through the limited login and were refused an insert of a release; with every dbt view dropped, Dagster rebuilt all 50 in 22 seconds without being asked; a release recorded with the CLI was built for in 26 seconds and served 60 profiles to the product role; an extraction launched through Dagster ran in the daemon; and the daemon came back healthy after a restart. The project was removed afterwards. The real stack runs the same image in development mode.

#### Operations console (migration 0029)

The operations console (phase D6 of the [orchestration plan](ORCHESTRATION_PLAN.md), migration `0029`) is an admin API and its pages, in `src/link_lens/admin/`. It is a third service beside the backend and the product service, and it is the only one that acts for a signed-in person.

- **Start it.** List who may sign in, then start the service. It answers on http://localhost:18720, loopback only.

  ```sh
  # .env, one line of JSON: token -> name and role (engineer, product_owner, admin)
  # LINK_LENS_ADMIN_USERS={"A_LONG_RANDOM_TOKEN":{"name":"Your Name","role":"admin"}}
  docker compose --profile console up -d admin
  ```

  A token can be made with `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`. After changing the list, recreate the service: `docker compose --profile console up -d --force-recreate admin`. With nothing listed, or a list that is not valid JSON, nobody can sign in.
- **What it is.** `admin/app.py` has the routes and the role each needs; `admin/service.py` has what the console reads and does, each function a few lines over the library function the CLI calls; `admin/auth.py` signs people in; `admin/audit.py` writes the log; `admin/static/` has three static files, the pages. The pages call `/admin` on their own origin and nothing else, and hold no credential.
- **Roles.** `engineer` reads sources, releases, ontology versions and what needs attention. `product_owner` also searches the catalogue, previews and adds sources, sets a cadence, pauses and resumes, and previews and records releases. `admin` also manages clients, tiers and keys and reads the audit log. The API checks the role; the menu only follows it.
- **Signing in.** `auth.authenticate` tries each resolver in a list. The one that exists reads `LINK_LENS_ADMIN_USERS`. A script sends `Authorization: Bearer TOKEN`; a browser signs in once and gets the token in a cookie that the page's code cannot read and that is sent only to the console. A change made with the cookie must carry the header `X-LinkLens-Console`, which only the console's pages set. An identity provider is one more resolver returning the same name and role.
- **The audit log.** `ops.admin_action` is append-only. A change is two rows with one `action_id`: `requested`, committed before the change, then `done` or `failed`. A change refused for the person's role or for the budget is one row, `refused`. A request with no outcome was cut off; the console shows it as `unfinished`. Nothing named like a key, secret, token, password or hash is written, and a new key is recorded by its ID and prefix. Actions taken on the command line are not in this table.

  ```sql
  SELECT at, actor, role, action, target, phase, result FROM ops.admin_action ORDER BY id DESC LIMIT 50;
  ```

- **Adding a source.** Search reads the saved catalogue and ranks by the active discovery revision; relevance is an uncalibrated score. Preview asks the portal for the dataset, downloads the file with the same bounds as registering, inspects it in a temporary file and stores nothing. Confirm calls `ingestion.register` and `refresh.request_onboarding`, which starts the onboarding graph on the backend: paid model calls, within the run's own limits. The estimate shown is the median recorded cost of completed onboarding runs. The API refuses without `confirm_paid_calls`, and when the estimate would take the budget over `LINK_LENS_MAX_COST_USD`.
- **Recording a release.** The comparison (`releases.preview`, also `link-lens release preview --batch-id BATCH`) counts profiles added, changed, removed and unchanged against the latest release and runs four checks. After a refresh, part of the difference is resampling; the page says so when the batch has refreshed sources. Recording calls `releases.create` with the signed-in person as the reviewer. Where Dagster runs, its sensor then builds the models as for a release from the command line.
- **Clients, tiers and keys.** The functions behind `link-lens access`. A key is shown once, in the answer to the request that issued it; the answer is marked not to be stored, and no later answer or log row holds it. Revoking keeps the key's row.
- **Database role.** The service sets `LINK_LENS_DATABASE_ROLE=linklens_pipeline`. Migration `0029` lets that role use the `analytics` schema and dbt grants it the reporting models, so the console reads a source's status from `analytics.source_health`. If the models are not built the console answers 503 and names `link-lens dbt build`.
- **No provider key.** The service gets the database, the artifact store, the backend's address and the settings a new run records, and nothing else from `.env`.
- **Command-line equivalents.** `link-lens source preview DATASET`, `register` and `onboard`, `source cadence`, `source pause` and `resume`, `release preview` and `create`, `access tier set` and `list`, `access client create`, `set` and `list`, `access key create` and `revoke`.
- **Trying a change.** Do not confirm a source, record a release or issue a key on the real database to see the console work. Restore a backup into a throwaway container, clone the artifact store, and run the app against them with a stand-in for the onboarding server:

  ```sh
  LINK_LENS_DATABASE_URL=postgresql+psycopg://linklens:PASSWORD@localhost:PORT/linklens LINK_LENS_DATABASE_ROLE=linklens_pipeline \
  LINK_LENS_ARTIFACT_DIR=/path/to/a/copy LINK_LENS_API_URL=http://127.0.0.1:STAND_IN_PORT \
  LINK_LENS_ADMIN_USERS='{"trial-token":{"name":"Trial","role":"admin"}}' \
  uv run uvicorn link_lens.admin.app:app --host 127.0.0.1 --port 8201
  ```

On 2026-11-15 migration `0029` was rehearsed on a restored copy and applied to the local database with the services stopped; both baseline checks reported zero differences (backup `/Users/may/link-lens-backups/linklens-pre-d6-cutover-20261115T070652.dump`). On a throwaway copy the whole flow was done in the browser: a dataset searched, previewed and added, seen waiting for review and, after a fixture approval and a 7 day cadence, fresh; the submission batch compared and released; a tier, a client and a key created and the key revoked; seven changes read in the audit log. The real database holds no console action, release, client or cadence, and the running console lists nobody.

#### Restoring into an empty environment

Restoring into an empty environment and checking it serves the same release:

```sh
# On the source: note what the release serves, then dump.
uv run link-lens release digest
pg_dump -U linklens -d linklens -Fc -f linklens.dump

# On the target: the roles first, then the data, then any newer migrations.
# A dump taken before migration 0022 does not need linklens_transform, nor one before 0025
# linklens_analyst, nor one before 0027 linklens_orchestrator.
psql -c "CREATE ROLE linklens_migrator NOLOGIN" -c "CREATE ROLE linklens_pipeline NOLOGIN" -c "CREATE ROLE linklens_product NOLOGIN" -c "CREATE ROLE linklens_transform NOLOGIN" -c "CREATE ROLE linklens_analyst NOLOGIN" -c "CREATE ROLE linklens_orchestrator NOLOGIN"
createdb linklens && pg_restore -d linklens linklens.dump
uv run alembic upgrade head
uv run link-lens dbt build         # the serving views; a dump taken at 0024 or later already has them
uv run python scripts/migration_baseline.py --typed --check outputs/local-run/migration-baseline.json
uv run link-lens release digest      # must print the same digest
```

Artifact bytes are not in the dump: copy the artifact directory, or point both environments at the same bucket. On 2026-11-15 these steps were run on a copy of the local database with a rehearsal release: the digest and all 60 profile versions were the same after the restore. The same day the local database moved from `0019` to `0021`; nothing has been created in the new tables.

#### The migration baseline

The migration baseline records what the store holds, so each later migration and backfill can be checked against it. It is read-only and works on both layouts:

```sh
uv run python scripts/migration_baseline.py --check outputs/local-run/migration-baseline.json
```

`outputs/local-run/migration-baseline.json` was written from the local database on 2026-11-14, before migration. It holds row counts and ID digests per table, kind and owner, counts per experiment and batch, and digests over ontology hashes, mapping `config_hash` values, observation IDs, source record IDs and profile versions.

#### Changing a database that holds data

The backend runs `alembic upgrade head` when it starts, so a new migration reaches the database at the next backend start whether or not anyone meant it to. For a database whose data matters, such as the local one, apply a migration on purpose instead:

1. Take a backup and check that it lists: `pg_dump -Fc`, then `pg_restore --list`.
2. Rehearse on a copy: restore the backup into a throwaway `pgvector/pgvector:pg17-trixie` container (create the `NOLOGIN` roles first: three, `linklens_transform` as well for a dump taken at `0022` or later, and `linklens_analyst` at `0025` or later), run `uv run alembic upgrade head` and any backfill there with `LINK_LENS_DATABASE_URL` pointing at the copy, and run both baseline checks.
3. On the real database: stop the backend, the product service, the console and, if they run, the Dagster services (they run the checkout's code and fail on a column that is not there yet, and the schedule would add rows between the two readings below). Take a fresh backup, save the typed figures, upgrade, run the backfill if the phase has one, build the serving views with dbt, and run both checks.
4. Start the services and check them: `/api/health` and `/api/runs` on port 18701, the Inbox on 18700, `/health` on 18703 and 18710.

```sh
docker compose --profile orchestration --profile console stop backend product admin dagster-webserver dagster-daemon
docker compose exec -T postgres pg_dump -U linklens -d linklens -Fc > /Users/may/link-lens-backups/linklens-pre-MIGRATION-TIME.dump
uv run python scripts/migration_baseline.py --typed --output /tmp/typed-before.json
uv run alembic upgrade head
uv run link-lens dbt build
uv run python scripts/migration_baseline.py --check outputs/local-run/migration-baseline.json
uv run python scripts/migration_baseline.py --typed --check /tmp/typed-before.json
docker compose --profile orchestration --profile console up -d
```

Both checks must report `0 difference(s)`. The first compares the legacy rows, which never change, with the recorded baseline. The second compares the records read back from the typed tables with the same reading taken just before the migration. Until the cutover on 2026-11-15 the typed check compared with the recorded baseline too (`--typed --check outputs/local-run/migration-baseline.json`); since then refreshes add snapshots, runs and observations, so that comparison reports what they added, and the reading taken before the migration is the one to match. Name the backup `linklens-pre-<something>.dump`: the backup service never removes a dump named that way. Each migration has a downgrade, and one step down and up again is tested; a downgrade that passes `0024` drops the serving views, and `link-lens dbt build` after the next upgrade puts them back. Building a bundle adds an artifact, so after the first bundle the artifact count differs from the baseline by the number of bundles built.

Every phase was applied to the local database this way on 14 and 15 November 2026, and each time both checks reported zero differences.

Work happens on branches in one checkout, and the backend runs the migrations of whatever is checked out. Once a branch's migration is applied, a checkout without that migration file cannot start the backend: Alembic stops because it does not know the database's revision. Keep the branch checked out until it is merged, or downgrade before switching.

The first of these moves, from the layout before the plan, is the largest. It rewrites every table under an exclusive lock, and it changes the PostgreSQL image:

```sh
docker compose stop backend
docker exec link-lens-postgres-1 pg_dump -U linklens -d linklens -Fc > ../linklens-before-phase0.dump
docker compose up -d postgres     # recreates the container on the pgvector image; the volume is kept
uv run alembic upgrade head
uv run python scripts/migration_baseline.py --check outputs/local-run/migration-baseline.json
docker compose up -d backend
```

The check must report `0 difference(s)`. To go back to the layout before the plan, stop the backend, run `uv run alembic downgrade 0002` and check out the previous code; the baseline check passes on that layout too. That was tested when the legacy tables still held everything. Since phase 3 new records are written only to the typed tables, and a downgrade drops those tables without copying anything back, so going back that far would lose whatever was written since.

Measured on 2026-11-14 on a restored copy of the local database (434,994 rows, 374,335 observations): upgrade about 6 seconds and downgrade about 8 seconds with `fsync` off, zero baseline differences in both directions, identical rows read through the old and new `store.py`, identical output from `link-lens usage`, `runs`, `ontology show`, `ontology diff`, `ontology budget` and `evaluation-report`, and an export of the submission batch with the same 1,747 files and values. The local database itself was then migrated the same day with the steps above: `0002` to `0008` in 8 seconds on PostgreSQL 17.12, zero baseline differences before and after the backend restart, and healthy backend, Agent Inbox and sandbox controller. No model call was made.

### Reproduce discovery and onboarding

Compose mounts local `src/` read-only into the backend and sandbox controller. LangGraph's development server and Uvicorn automatically reload Python changes, so routine code edits do not require an image rebuild. The backend also mounts migrations, Alembic configuration, graph configuration and the ontology. These mounts apply only to the trusted services; agent execution containers still receive no repository mount.

After changing Compose configuration, apply it with `docker compose up -d --no-deps backend sandbox-controller`. Dependency or Dockerfile changes still require `docker compose up -d --build backend sandbox-controller`. After editing `.env`, use `docker compose up -d --no-deps --force-recreate backend` to load new environment values. Non-Python configuration changes may require `docker compose restart backend`; restarting also applies new migrations. Reloading restarts the worker, so make edits between active onboarding jobs. PostgreSQL, artifacts and the checkpoint volume remain persistent.

```sh
uv sync --frozen
docker compose up -d --build
uv run link-lens discover
uv run link-lens portfolio
uv run link-lens runs
uv run link-lens onboard RUN_ID
```

`.env` needs `OPENROUTER_API_KEY` for Jev and the existing Azure `OPENAI_API_KEY` / `OPENAI_API_BASE` for Luna. New defaults are `LINK_LENS_MODEL=gpt-6-luna` and `LINK_LENS_EXPERIMENT_ID=jev-gpt6-luna-ontology-v1`; existing `.env` settings override them. Optional LangSmith settings apply. No secrets are written to reports. Onboard each new portfolio run ID once; the portfolio command skips existing runs in the same experiment. To start a separate experiment, choose a new experiment ID consistently in host and backend environments before starting.

Discovery scores all supported-format candidates using Jev. The combined rank is 50% existing rule score + 50% Jev relevance. Publisher cap: eight; shortlist: fifty. This is a disclosed heuristic, not a calibrated relevance probability. There is no audit-label feedback into ranking. Saved successful decisions are reused on retry; failed calls retain usage receipts and cannot silently become successful scores.

### Review the current configs

Open [Agent Inbox](http://localhost:18700) or use the source links in [the current overview](../outputs/README.md). Review the exact new Luna-generated configs. Accept, Respond, or Ignore. Old Terra approvals never approve new configs.

A run at `needs_review` or `failed` has not passed the workflow and is not ready to accept. Its errors must be diagnosed; a fresh bounded run retains a `supersedes_run_id` link and all old costs. No automatic fallback to Terra, hand-edited mapping, hidden budget reset or test-set-guided repair is used.

### After all six current configs are accepted

The submitted runs have already completed. For an independent rerun, select explicit completed run IDs, assemble, then enhance in a separate output directory:

```sh
uv run link-lens assemble RUN_1 RUN_2 RUN_3 RUN_4 RUN_5 RUN_6 --cohort-pool-size 25000
uv run link-lens export --batch-id BASELINE_BATCH_ID --output outputs/local-run/new-run/baseline
uv run link-lens enhance --batch-id BASELINE_BATCH_ID --retrieval hybrid --reconcile --output outputs/local-run/new-run/enhanced
```

The old `report_current_experiment.py`, `finish_current_experiment.py` and authored audit scripts describe earlier experiments. Do not run them against the promoted submission. Mapping approval, evidence evaluation and submission promotion are separate decisions. No archived labels approve new evidence.

### Recovering a requested revision after its attempt budget is exhausted

For an attempt that stopped before reaching Inbox (`needs_review`, `budget_exhausted` or `failed`), prepare a replacement with explicit feedback:

```sh
uv run link-lens recover STOPPED_RUN_ID --feedback "Correct the semantic critique; leave unsupported claims unmapped."
uv run link-lens onboard NEW_RUN_ID
```

`recover` prints the replacement ID and exact next command without making model calls. It requires the same configured experiment and model, a frozen reader/partitions, and unused final-test records. It carries the existing mapping, validation and critique into a fresh bounded attempt, preserves the maximum consumed final cursor for the snapshot, and records `supersedes_run_id` and the recovery request. Old attempts and their costs remain unchanged. Repeating the same recovery request returns the existing replacement. Final-test failures cannot be recovered this way. The replacement must pass validation and receive fresh human approval; recovery is not approval.

Choose feedback based on the stop reason, visible with `uv run link-lens runs --run-id STOPPED_RUN_ID`:

| Stop reason | Suggested `--feedback` |
|---|---|
| Semantic critique or exhausted mapping revisions | `Address the previous semantic critique. Correct mappings only where supported by source evidence; leave unsupported or ambiguous fields unmapped. Preserve mappings that remain valid.` |
| Temporary API or sandbox failure, after fixing its cause | `Retry after the temporary infrastructure failure. Preserve the existing reader and supported mappings.` |
| Specific unsupported mapping | `EXAD includes external administration and receivership, not only liquidation. Map EXAD to unknown or leave it unmapped. Preserve other supported mappings.` |

`Retry to onboard` is accepted, but gives little direction. Prefer actionable feedback; the previous critique is already carried forward. For budget exhaustion, diagnose the cause first: a replacement has the same configured limits and may fail again. A `needs_review` run may have stopped without an Inbox interrupt; only review-ready runs reach `waiting_for_human`.

When the user has actually requested a revision, a stopped attempt can be replaced explicitly:

```sh
uv run python scripts/recover_review_revisions.py EXHAUSTED_RUN_ID
uv run link-lens usage
```

The script requires a recorded revision request, preserves the frozen partitions and consumed final-test cursor, links `supersedes_run_id`, and carries forward the generated configuration and semantic critique. It does not approve anything. Repeated execution returns the existing replacement instead of launching duplicates. Original token/version bounds are not increased; the new bounded attempt and all prior costs remain visible. The latest interrupted review needs a fresh Accept decision.

### Completed run and saved demonstration

All six runs in `outputs/current-run.json` are approved. The selected enhanced batch contains 60 profiles and 61 links. Open `outputs/okf/viewer.html` or the published Pages site. Human evidence evaluation remains pending. Historical database ZIPs reproduce earlier experiments, not this submission; full new-experiment archive restoration is unverified.

The [experiment archive](../experiments/jev-gpt6-luna-ontology-v1/README.md) preserves deterministic and enhanced exports. [The previous submission](../experiments/jev-luna-v1-submission/outputs/README.md) retains its original counts, approvals, audits and checksums. Large JSONL exports are losslessly compressed with SHA-256 manifests; the viewer is uncompressed HTML. The promotion manifest records the exact approved viewer hash.

## Experimental hybrid enhancement

`enhance` runs after mapping approval and extraction. It reads an immutable batch,
reuses its exact selected record IDs, and publishes a new experimental batch. It
neither re-onboards sources nor modifies submission artifacts. Older batches without
candidate metadata are reconstructed from their approved mappings/snapshots; every
reconstructed observation must equal the frozen observation before inference starts.

```sh
# Read-only evidence coverage, no model calls:
uv run link-lens enhance --batch-id BASELINE_BATCH_ID --preflight-only
# Bounded paid assessment, with progress on stderr:
uv run link-lens enhance --batch-id BASELINE_BATCH_ID --max-pairs 50
# Lexical-only retrieval ablation; still uses Jev for identity decisions:
uv run link-lens enhance --batch-id BASELINE_BATCH_ID --retrieval fuzzy --no-reconcile \
  --output outputs/local-run/fuzzy-enhancement
uv run link-lens enhance-worksheet --batch-id DERIVED_BATCH_ID
# After a human labels the combined worksheet, evaluate one frozen split:
uv run link-lens enhance-evaluate --batch-id DERIVED_BATCH_ID \
  --labels outputs/local-run/enhancement-review/worksheet.json --split heldout
```

Replace placeholders with stored batch IDs. Enhancement commands without `--preflight-only` make paid calls;
worksheet generation and evaluation do not. Provider requirements are OpenRouter
access to the configured Jev model, an OpenAI-compatible embedding endpoint exposing
`text-embedding-3-small`, and the configured onboarding model for conflict annotations.
Optional `LINK_LENS_EMBEDDING_API_BASE` and `LINK_LENS_EMBEDDING_API_KEY` override the
normal OpenAI endpoint/key. `.env.example` documents all enhancement settings.

Implementation entry points:

- `enhancement.py`: frozen input reconstruction, orchestration, immutable derived
  batches, source-impact replay and separate exports.
- `semantic_resolution.py`: labelled evidence packets, RapidFuzz name retrieval,
  local cosine retrieval, eligibility gates and cluster construction.
- `enhancement_models.py`: Jev, embeddings and structured conflict annotations;
  typed contracts live in `enhancement_contracts.py`.
- `reconciliation.py`: complete-pair equivalence groups and original-value provenance.
- `enhancement_evaluation.py`: human worksheets and benchmark reports.

Each record retrieves up to 20 candidates per other source per retrieval method.
Policy `hybrid-evidence-2` uses initial 0.80 fuzzy and cosine retrieval floors; these
are experimental retrieval filters, not identity confidence thresholds. Fuzzy and
embedding sets are unioned. Embeddings default to 1,536 dimensions and batches of
64 inputs; unchanged individual vectors from the first policy remain reusable.

Assessment and admission are separate. Sparse candidates can be assessed by Jev
and exported for human review, but matching names alone cannot create membership.
Potential admission routes include an entity website domain, compatible full
registered/business addresses, or an exact distinctive name plus matching locality,
state and postcode with registered/business roles. An explicitly co-stated legal /
trading alias can accompany that location evidence. Service-location evidence needs
an exact distinctive name, matching full address and postcode, compatible roles,
and clear ownership. Conflicting location components block the alternative routes.
These combinations are experimental: neither a postcode nor industry alone suffices.
Frequency features flag repeated names, domains and addresses.
Jev separately judges identity, name compatibility, corroboration and ownership.
The same-entity score and all three supporting judgments must reach 0.98, with a
0.10 identity margin. These are versioned experimental thresholds.

Exact clusters remain anchors. New attachments require direct support from an
original anchor record. A component spanning existing IDs is deferred as a whole.
Without an anchor, every cross-source pair must qualify; missing, failed or unqueried
edges never establish transitive identity. Provisional IDs are deterministic at
creation and retained by explicit record membership on subsequent derived batches.
Passing pair decisions can still be deferred by cluster checks; inspect both exports.

The default enhancement limit is $10 per stable job, additionally bounded by the shared experiment cap, six concurrent requests and
two retries per failed request. At most 500 new identity pairs are attempted per
invocation (`--max-pairs` overrides this); successful cached decisions do not count.
Potential admission routes are prioritized, followed by exact names and retrieval
scores. Remaining pairs stay pending, never classified as nonmatches. Repeating the
same command assesses the next uncached pairs within the cumulative dollar budget.
`--max-pairs` limits identity assessment only; embeddings and reconciliation also
consume the shared budget. Progress reports stages, cache hits and attempts to stderr;
`--no-progress` disables it and stdout remains the final JSON result.

Job identity binds the parent artifact and policy;
retrying the same command retains spend. Each request reserves cost under the shared
PostgreSQL advisory lock before dispatch; interrupted/unknown attempts retain their
reservation. Reservations are not measured bills. Successful responses cache by
complete request, endpoint, model and protocol version. Changing evidence invalidates
cache reuse. The provider-reported model, usage, request/response artifacts, failures
and timing are saved. Unknown usage stays unpriced. Changing a provider behind the
same endpoint/model alias requires a policy-version change to deliberately invalidate
cached responses. The dollar gate is based on saved provider rate estimates, not an
invoice guarantee.

Budget exhaustion or provider failure produces explicit pending work. Re-run with
the same parent and policy to reuse successful calls; an explicit `--budget` raises
the job ceiling without resetting historical charges; the shared experiment cap still applies. New parent batches
create new jobs with explicit lineage. Policy v2 also creates a distinct job and budget
from v1, while reusing unchanged embedding and profile caches. Identity prompt changes
invalidate the old decision cache. `--no-reconcile` disables model profile work.
No inference is silently replaced with a positive or negative label.

Source-removal analysis applies the same hybrid policy and allows only identical
cached model inputs. Removing a source can change frequency evidence and require new
judgments: those reports are marked incomplete with unknown membership-change metrics.
This analysis never silently spends on fresh counterfactual calls or falls back to
exact-only resolution. Profile-value effects keep original membership fixed.

The experimental export includes candidate/cluster decisions, pending work, entities,
links, profiles, observations, selection, policy, cost receipts and comparison data.
`review_candidates.jsonl` contains unreviewed deferred candidates and their evidence;
`preflight.json` reports source coverage and potential lexical corroboration routes.
Preflight does not retrieve embeddings or estimate accuracy. With no routes it warns
that assessment may produce review candidates without additional links or profiles.
Default destination: `outputs/local-run/enhanced-v2/`. Submission destinations and
`experiments/` are rejected before inference. PostgreSQL stores enhanced entity
snapshots under batch ownership; ordinary `assemble` reads only canonical `entity`
records. Existing domain tables suffice; there is no database schema migration.

### Human evaluation of enhancements

The worksheet samples retrieved and outside-candidate pairs separately, records the
sampling population, and assigns entire known/provisional entity groups to one
split. Development/heldout convenience files accompany the combined worksheet;
retain the combined worksheet for evaluation so leakage can be checked across both.
For uncertain identities, a human must correct grouping before interpreting split
independence. Same-entity human labels require common entity groups. Any record or
entity group occurring in both splits is rejected.

Use `same`, `different`, `unknown`, or leave `label` null. Every human label requires
`reviewer`, `reviewed_at` and `evidence_notes`. Inspect raw locators and address/subject
roles, including shared premises/domains, brands, branches and ambiguous ownership.
Identifier-masked controls are explicitly separate from human ground truth; do not
copy their expected identity into human labels. No evaluation labels are supplied to
inference. Freeze the policy before heldout review; do not tune against heldout labels.

Reports show labelled-benchmark retrieval recall, linkage precision/recall, additional
correct matches, contaminating labelled pairs and a Wilson precision interval.
Unknown/unreviewed items are excluded. These stratified benchmark metrics do not
estimate population performance. Observed semantic precision of 99% is a target,
not an automatic promotion switch. The user explicitly promoted the bounded run into the submission. Its live cost and contribution measurements are in [the results](../outputs/README.md); human accuracy remains unmeasured.

Provider references: [OpenAI embeddings](https://developers.openai.com/api/docs/guides/embeddings),
[embedding pricing](https://developers.openai.com/api/docs/models/text-embedding-3-small),
[Jev typed decisions](https://openrouter.ai/docs/guides/community/jev-tutorial),
[TypeSafe confidence](https://docs.typesafe.ai/confidence).


## Experimental ontology evolution

Run `uv run alembic upgrade head` before using the registry. The `ontology` schema stores
each version as rows: `ontology_version`, `concept` with its values and required companions,
`version_concept` membership, proposals with their dispositions and concept decisions,
activations and gate reports. Every table rejects updates, and a version that removes or
redefines a concept of its parent is rejected when its transaction commits. A version's
hash is still the digest of its document: `ontology.resolve()` rebuilds the document from
the rows and checks the hash, and the original JSON artifact is kept as an independent copy.
The packaged v0.1 ontology preserves old mappings and approval hashes. The promoted root `firmable_ontology.yaml` seeds a new experiment when no active version exists; an existing experiment pin always takes precedence. New mappings
include `ontology_hash`; changing its meaning requires a new mapping and approval.
Experimental additions cannot redefine or remove a parent concept.

Use the same environment in the host CLI and backend, without overwriting `.env`:

```sh
export LINK_LENS_EXPERIMENT_ID=jev-gpt6-luna-ontology-v1
export LINK_LENS_MODEL=gpt-6-luna
export LINK_LENS_MAX_COST_USD=10
docker compose up -d backend
```

After discovery and registration, prepare each selected run before starting its graph:

```sh
uv run link-lens ontology prepare --run-id RUN_1 --run-id RUN_2
uv run link-lens ontology propose --run-id RUN_1 --run-id RUN_2 --activate-experimental
uv run link-lens ontology show ONTOLOGY_HASH
uv run link-lens ontology diff PARENT_HASH ONTOLOGY_HASH
uv run link-lens ontology budget
uv run link-lens onboard RUN_1
```

Repeat `--run-id` for all six sources. `prepare` performs paid reader inference and
freezes partitions; it does not propose mappings. `propose` reads only discovery
records and publisher documentation. It makes at most one source proposal each,
one consolidation, at most one structural repair, and a critique deciding each concept individually. Successful responses
are cached by complete evidence, model, prompt and schema. A failed API attempt stays
in the ledger. A rejected job remains rejected; do not silently loop against it.

The proposal artifact records one disposition per source header: `existing_target`,
`new_concept`, `insufficient_evidence`, or `non_domain_metadata`. Literal evidence
quotes must exist in the input. The model receives short source aliases bound to stored run IDs by the engine. Semantic critique remains an AI judgment, not human
validation. Rejected concepts and concepts depending on rejected companions remain unmapped; independently accepted additions can activate together. Successful activation updates only selected unstarted runs and the
experiment's ontology pointer. It never rewrites the submitted YAML or accepts a mapping.
`ontology promote HASH --reviewer NAME` records a human decision on that exact version;
it does not publish artifacts or approve source mappings.

Promotion needs a recorded gate run with no failed check:

```sh
uv sync --frozen --group ontology          # linkml and pyshacl, not in the runtime image
uv run link-lens ontology gate ONTOLOGY_HASH
uv run link-lens ontology promote ONTOLOGY_HASH --reviewer NAME
uv run link-lens ontology export ONTOLOGY_HASH --format linkml --output firmable_ontology.linkml.yaml
```

`ontology gate` writes one `ontology.gate_report` row per check and exits 3 if any fails.
The checks are: the rows rebuild the hash and equal the stored artifact; the LinkML export
passes `linkml-lint` and generates SHACL and JSON Schema; the version is additive against
its parent. Since Phase 2 a sample of stored observations is validated against the generated SHACL
shapes, and an impact report counts the mapping configs and observations that use each
concept a version adds. The optional Open Ontologies check is not configured and is
recorded as `unknown`. `unknown` does not block; the results are stored with
the promotion and printed for the reviewer. Without the `ontology` dependency group the
LinkML check is `unknown` too. The promotion recorded on 2026-09-25 predates the gate and
has no gate run.

`ontology export` also writes `--format shacl` and `--format jsonschema`. The committed
`firmable_ontology.linkml.yaml` is the export of the promoted version, so a promotion shows
up as a diff; a test fails when it drifts from `firmable_ontology.yaml`. Class and attribute
IRIs use the placeholder namespace `https://linklens.example/ontology/` until a real one is chosen.

Definitions specify type, scope, cardinality, numeric bounds and required companion
concepts. Scoped fields use a mapping `group` name; the engine derives group identity
from source/record/group, preserving each row's bundle. Financial claims require their
period and currency when declared as companions; absent values quarantine dependent
claims. Decimal values remain exact JSON strings, integers/booleans use JSON scalar
types, and all retain raw values. `indicator_categories` takes named source columns,
a column-to-category `values` mapping and an exact truth marker in `argument`.
Blank input never becomes zero. Generated Python is not an extraction mechanism.
Scoped groups are exported intact and excluded from cross-record reconciliation
and the identity judge's observation payload. They are not additional identifier-linking
rules. Unlinked source claims remain visible. Embedding cache keys retain ontology
hashes, while provider input excludes those hashes and serialization metadata so
that shared cache metadata cannot influence semantic similarity. This serialization
uses `hybrid-evidence-2`; older vectors and their paid-call receipts are retained.

### Where each concept rule is applied, and what the exports carry

A concept implies more rules than any of its exports states, and some of its fields are
descriptions that no code checks. `ontology.checks(concept)` lists the rules of one
concept with the steps that apply each one: `mapping` (a mapping that breaks the rule
fails validation in `contracts.MappingSpec` and cannot be approved), `extraction` (a
value that breaks it is quarantined in `extraction.extract`, not stored) and `profile`
(how `profiles.assemble_profiles` treats the stored claims). An empty list means no code
applies the rule. Each concept page shows this list under **Checks**, and
`describe_concepts` returns it as `checks`, over REST and MCP alike. A test feeds a value
that breaks each rule `checks` puts at extraction and expects the engine to refuse it.

The exports are generated views of a version and carry less. In the table, *covered*
means the export states the rule, *lossy* that it states a different rule, *carried*
that the text travels as a description or annotation no validator reads, and
*excluded* that the export does not mention it. The JSON Schema column describes the
scope classes under `$defs`. The schema's top level is `Observation`, which checks only
that `concept` is a known name and `value` is text or null, and nothing refers to the
scope classes.

| Rule | Applied by | LinkML | SHACL | JSON Schema |
|---|---|---|---|---|
| Enum: one of the allowed values | extraction | covered (enum range) | covered (`sh:in`) | covered (enum) |
| Date written `YYYY-MM-DD` | extraction | covered (`date`) | covered (`xsd:date`) | covered (`format: date`) |
| Integer, boolean | extraction | covered | covered | covered |
| Decimal kept as exact text | extraction | covered (`decimal`) | covered (`xsd:decimal`) | lossy: `number`, while stored values are strings |
| Numeric bounds | extraction | covered | covered (`sh:minInclusive`, `sh:maxInclusive`) | covered |
| ABN, ACN, NZBN shape and checksum, by the concept's local name | extraction | excluded | excluded | excluded |
| Required companions (`requires`) | mapping and extraction | carried (annotation) | excluded | excluded |
| Scope and groups | mapping and profile | covered as one class per scope; groups excluded | covered as classes; groups excluded | covered as classes; groups excluded |
| Address fields kept together per record | profile | excluded | excluded | excluded |
| Cardinality `one` | profile: one value is chosen, or none when equal claims disagree | covered (not multivalued) | lossy: `sh:maxCount 1`, while every claim is kept | covered (not an array) |
| Cardinality `many` | profile: every value kept | covered (`multivalued`) | covered | covered (array) |
| Meaning (`definition`) | a person, when approving a mapping | carried (description) | carried (`sh:description`) | carried (description) |

Three consequences are worth knowing before a client relies on an export:

- **Identifier checks travel by name, not by concept.** Extraction checks a value as an
  ABN, ACN or NZBN when the concept's local name is `abn`, `acn` or `nzbn`, in any
  namespace. `v0.1.yaml` declares a `pattern` for them, but the registry has no field for
  it and drops it, so no export carries it. A concept that holds an identifier under
  another name gets only the operations its mapping chooses: the approved ASIC
  business-names mapping only trims `registration.business_name_abn`, so nothing checks
  that value's shape or checksum.
- **The SHACL gate check cannot fail on cardinality.** `check_shacl_observations` turns each
  sampled observation into its own node, so `sh:maxCount 1` never meets a second value.
  Several claims for a cardinality-`one` concept are normal: they are what profiles choose
  between.
- **JSON Schema types a decimal as a number.** A consumer that validates stored values
  against the scope classes would reject the exact decimal strings the engine writes.

The shared ledger reserves conservative model cost before every request, under the
existing database advisory lock. It includes Jev discovery, ontology, onboarding,
embedding, Jev enhancement and LLM explanations, including failed/retried attempts.
Unknown usage retains its reservation. Completed calls use reported cost when present,
otherwise conservative token rates. `LINK_LENS_PRICING_MULTIPLIER` defaults to 1.0;
set it to the provider's documented uplift, e.g. 1.1 for applicable regional processing.
The $10 cap is an estimate, not an invoice guarantee. Existing call/token/time limits
and the enhancement job cap still apply. An exhausted shared budget stops new calls;
creating another job in the same experiment does not reset it.

After exact mapping approvals, assemble and export a deterministic batch, then run
`enhance --batch-id BATCH_ID --retrieval hybrid --reconcile` with the same experiment
and model environment. Preserve baseline and enhanced exports in separate directories.
Reports include ontology snapshots, proposals, usage and budget state. Human mapping
reviews and human evaluation worksheets must not be replaced by AI approvals.

Once both exports exist, measure concept emission, profile contribution and evidence
consistency without making model calls or changing the submission:

```sh
uv run python scripts/report_ontology_experiment.py --root experiments/jev-gpt6-luna-ontology-v1
```

The report compares the preserved submission, new deterministic assembly and enhanced
assembly separately. It checks observation bindings, profile citations, scoped bundles,
OKF links and identical baseline/enhancement selections. Results and remaining human
evaluation work are recorded in the [experiment report](../experiments/jev-gpt6-luna-ontology-v1/README.md).
