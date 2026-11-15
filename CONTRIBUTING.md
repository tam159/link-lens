# Making a change to Link Lens

This page is for the two engineers who change the data flow: the AI engineer and the analytics engineer. It says who owns what, and how to add the three things that change most often: a dbt model, a Dagster asset and a console action. Setup and commands are in the [README](README.md); how each piece is run and recovered is in the [engineering guide](docs/ENGINEERING.md); why it is built this way is in the [orchestration plan](docs/ORCHESTRATION_PLAN.md). Coding agents read [AGENTS.md](AGENTS.md), which holds the same rules in more detail.

## Who owns what

| Object | Owner | Tool | Where |
|---|---|---|---|
| Core schemas `ontology`, `catalog`, `onboarding`, `evidence`, `identity`, `ops`, `access`; the `legacy` history; the helpers in `public` | Both engineers | Alembic | `migrations/versions/` |
| Extraction, identity resolution, profile policy, ontology workflow, refresh steps | AI engineer | Python library | `src/link_lens/` |
| Onboarding and review flow | AI engineer | LangGraph, Agent Inbox | `src/link_lens/agent.py` |
| The twelve `serving` views clients read | Analytics engineer | dbt models with enforced contracts | `transform/models/serving/` |
| The `serving` tables built by algorithm (`okf_page`, `okf_line`, `okf_index`) and the `serving` functions | AI engineer | Alembic owns them; `releases.create` fills them | `migrations/`, `src/link_lens/releases.py` |
| Everything in `analytics`: staging views and reporting models | Analytics engineer | dbt; Alembic owns the schema and its grants | `transform/models/staging/`, `transform/models/analytics/` |
| Schedules, sensors, freshness, alerts | Analytics engineer, with the AI engineer for steps that call a model | Dagster | `orchestration/link_lens_dagster/` |
| Product service, REST, MCP | AI engineer | Python | `src/link_lens/product/`, `src/link_lens/interfaces/` |
| Dashboards | Analytics engineer | Grafana, as JSON files | `deploy/grafana/dashboards/` |
| Operations console | AI engineer builds it; the product owner uses it | Python API and static pages | `src/link_lens/admin/` |

**The rule that prevents conflicts: Alembic and dbt never manage the same relation.** Alembic owns every table that holds state, every schema and every grant to a schema. dbt owns only derived relations. A test fails if a migration creates a view in `serving` or if dbt builds anything outside `analytics`, `serving` and `serving_next`.

**Three decisions belong to a person and to no code:** approving a mapping (Agent Inbox), promoting an ontology (`link-lens ontology promote`), and recording a release (the console or `link-lens release create`). Dagster reacts to the rows they leave and never writes one; its database role cannot.

## How a change gets in

1. Branch off `main`. Keep commits small.
2. Run the tests that cover the change, then the whole suite and the lint:

   ```sh
   uv run pytest -q
   uv run --group orchestration pytest -q tests/test_orchestration.py
   uv run ruff check src/link_lens tests --exclude _vendor --select F
   ```

   Database tests start their own PostgreSQL in Docker. They never touch the `linklens` database.
3. Update the document that owns what you changed. A decision that differs from the plan is written into the plan's phase and its risk table.
4. CI runs two jobs: the application (lint, migrations up, down and up, the published contracts, the kept bundle, the suite) and the orchestration (the runtime image has neither tool; dbt builds and tests every model; Dagster's definitions load; the Dagster image builds and loads by itself).
5. A change that adds a migration reaches the local database only by the procedure in the engineering guide under **Changing a database that holds data**: backup, rehearsal on a copy, services stopped, migrate, `link-lens dbt build`, both baseline checks at zero.

## Writing a dbt model

The project is in `transform/`, on dbt Core 1.12 with the PostgreSQL adapter. dbt works as `linklens_transform`, which reads the core schemas and creates only in `analytics`, `serving` and `serving_next`.

**A reporting model** (in `analytics`, for the team and the dashboards, never for clients):

1. Read core tables through a staging view. If the table has none yet, add `transform/models/staging/stg_<schema>__<table>.sql`: rename and cast only, nothing joined or filtered, reading `{{ source('<schema>', '<table>') }}`. Declare the source in `transform/models/sources/sources.yml` and describe the view in `_staging.yml`.
2. Write the model in `transform/models/analytics/<name>.sql` as one `SELECT` over `{{ ref('stg_...') }}`. Start the file with a comment that says what one row is and what the figures do and do not mean.
3. Describe it in `_analytics.yml`: every column, a key test (`unique_combination` with `arguments: {columns: [...]}`), and `not_null` where it holds. Test arguments go under `arguments:`.
4. If it adds things up, add a singular test in `transform/tests/` that its total equals the table it reads, like `model_cost_reconciles_with_events.sql`.
5. Keep kinds of evidence apart. Never add human labels and AI labels into one figure. Show a score as uncalibrated unless a person measured it, with the sample size and date beside it. Count an unknown as its own column, never as a zero in a sum.
6. Grants come from `dbt_project.yml`: reporting models are readable by `linklens_analyst` (Grafana) and `linklens_pipeline` (the console and the CLI). Staging views are granted to nobody.
7. Build and test it: `uv run link-lens dbt build --select +<name>`, then the whole project with `uv run link-lens dbt build`.

**A dashboard panel** reads `analytics.<model>` only. Add the panel to the dashboard's JSON file in `deploy/grafana/dashboards/` (an edit in the Grafana UI is not saved), list the model under the dashboard's exposure in `transform/models/analytics/_exposures.yml`, and run `uv run pytest -q tests/test_dashboards.py`, which runs every panel's query as the analyst.

**A serving view** is what clients read, so it changes with more care:

1. Change the model in `transform/models/serving/` and its contract in `_serving.yml` together. A column or type that differs from the contract fails the build.
2. Compare before replacing: `uv run link-lens serving-compare --build` builds the serving models into `serving_next` and compares them with the live views. It exits 3 and lists every view that answers differently. Go on only when the differences are the ones you meant.
3. Build the whole project into `serving` with `uv run link-lens dbt build`. Never build only the serving models into `serving`: replacing a view drops the reporting views that read it until the next full build.
4. Keep both conditions that pin a release in `serving.observation` and `serving.evidence`: the snapshot the release's run was onboarded on, and observations loaded by the time the release was recorded.
5. If the REST or MCP answers change on purpose, regenerate the published contracts with `UPDATE_CONTRACTS=1 uv run pytest tests/test_production.py` and review the difference in `docs/api/` like code.

Where Dagster runs, it builds the models itself after a release (`release_recorded`) and whenever views it owns are missing (`models_missing`).

## Writing a Dagster asset

The code location is `orchestration/link_lens_dagster/`, on open-source Dagster 1.13. **Dagster calls the library; it holds no pipeline logic.**

1. **Write the step in the library first**, usually in `src/link_lens/refresh.py`: a function with explicit IDs that returns a small result record and writes nothing new when it is run again. Load rows with `store.put_many` or `store.put_observations`, which skip what is already stored. Give it a test of its own, including the second run.
2. **Raise `refresh.Blocked` when a person must act** (no approved mapping, drift that blocks): the asset turns it into a failure that is not retried.
3. **Write the asset** in `assets/<area>.py` as a few lines: call the step through the `pipeline` resource (`pipeline.steps.<step>(...)`), yield a `MaterializeResult` with the result record as metadata and a `data_version` from a digest of what was stored, and add asset checks that read the database to confirm it. Partition by source with `partitions_def=sources` when the step is per source. Put it in a pool: `database`, `downloads`, or `model_calls` for a step that calls a model.
4. **A step that spends on model calls** gets no retry policy, starts only when a person asks or a sensor that is off by default is turned on, and relies on the application's budget, which stays the only authority on spend.
5. **Register it** in `definitions.py`, with a job if a schedule or sensor launches it. A job whose steps are deterministic and store nothing twice may carry the `RETRIED` tags, so that the daemon runs it again from its failure when a worker or Dagster itself fails. Steps that fail are retried by their asset's retry policy, not by this.
6. **A sensor reacts to rows a person recorded and starts from the present**: on its first tick it stores a cursor at the newest row and launches nothing, so turning it on never replays history. A schedule reads what is due from the registry (`sources.due`); cadence and pause are data a person sets, never constants in Dagster.
7. **Test it** in `tests/test_orchestration.py`, materialising the asset against the test database as `linklens_orchestrator`, the role Dagster works as. The `Pipeline` resource fails if the library is working as anyone else. Then check that the definitions load: `uv run dagster definitions validate --workspace orchestration/workspace.yaml`.
8. **The deployment runs from the image**: after the change, rebuild it with `docker compose --profile orchestration build dagster-webserver`. In development, reload the code location in the UI.

A new table that records a human decision must revoke the orchestrator's default `INSERT` and `UPDATE` on it in its migration, and be added to `test_orchestrator_role_cannot_record_a_human_decision`.

## Writing a console action

1. Put the action in the library first, with a CLI command that writes the same records. No rule lives only in the API.
2. Add a function to `src/link_lens/admin/service.py` that wraps the library call in `audit.acting(principal, "<area>.<verb>", target, request)` and fills the outcome with IDs, never a key or a secret.
3. Add the route to `src/link_lens/admin/app.py` with `needs("<role>", "<area>.<verb>")`. The role is checked there, not in the pages.
4. Add the screen to `static/console.js`, building elements with `h(...)` and calling `api(...)`. Never set markup from data, and never call anything but `/admin`.
5. Test the role refusals, the audit rows and the parity with the CLI in `tests/test_admin.py`.

Try a console change on a throwaway copy of the database, never on the real one: adding a source there starts a paid onboarding run, and a release, a client or a key is a person's decision.
