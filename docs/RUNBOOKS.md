# Runbooks

What to do when something in the data flow needs a person. Each runbook says how you find out, what to look at, what to do, and what not to do. How the pieces work is in the [engineering guide](ENGINEERING.md); why they are built this way is in the [orchestration plan](ORCHESTRATION_PLAN.md).

Commands run from the repository root. The local addresses are the Dagster UI at http://localhost:3070, Grafana at http://localhost:3080, dbt's documentation at http://localhost:3090, the Agent Inbox at http://localhost:3000 and, when started, the operations console at http://localhost:8200. Where a runbook gives a command to set a cadence, pause a source or record a release, a signed-in product owner can do the same in the console.

Three things only a person does, in every runbook: approve a mapping, promote an ontology, record a release. Dagster cannot do them, and no runbook asks you to work around that.

| Something happened | Runbook |
|---|---|
| A refresh run failed, or a source is overdue | [A source's refresh failed](#a-sources-refresh-failed) |
| A source's file changed shape | [A source drifted](#a-source-drifted) |
| A mapping has waited in the Inbox for days | [A review is stuck](#a-review-is-stuck) |
| The models did not build after a release or a migration | [A release build failed](#a-release-build-failed) |
| Paid steps are refused, or the budget alert fired | [The budget cap is reached](#the-budget-cap-is-reached) |
| A release must be served again from a backup | [Restoring a release](#restoring-a-release) |
| The Dagster UI is down or a schedule shows an error | [Dagster itself](#dagster-itself) |
| Nobody can sign in to the console, or an action shows as unfinished | [The operations console](#the-operations-console) |
| Taking and checking backups | [Backups](#backups) |

## A source's refresh failed

**How you find out.** An alert "Run failed" or "Source overdue", the source health dashboard (status `failing` or `stale`, with the last error), or a red run of `refresh_source` in the Dagster UI.

**Look at.**

```sh
uv run link-lens source state SOURCE_ID      # last check, failures in a row, last error, retry_after
uv run link-lens source due                  # what is due now and what is overdue, with the reason
```

The run in the Dagster UI shows which step failed: `snapshot` (the download) or `observations` (the extraction).

**Do.**

- **The download failed** (`Download failed`, a timeout, a 5xx from the publisher). Nothing to do at first: the failure is counted and the schedule tries again after an hour, then two, then four, never longer than the cadence. If it has failed three times, open the dataset's page on the portal (linked from the dashboard). If the publisher moved or withdrew the file, pause the source so it stops asking, and decide whether to onboard the new location as a new source.

  ```sh
  uv run link-lens source pause SOURCE_ID --reviewer YOUR_NAME
  uv run link-lens source resume SOURCE_ID
  ```

- **You want to try now** instead of waiting: run the check by hand. A success ends the backoff.

  ```sh
  uv run link-lens source check SOURCE_ID
  ```

- **The extraction failed with "cannot be extracted"**: that is drift or a missing approval, not a failure. Go to [A source drifted](#a-source-drifted).
- **The extraction failed with anything else**: re-run the failed step from the run's page (Re-execute, From failure). Extraction stores each observation once, so a second run cannot duplicate. A run that failed in Dagster itself (a worker that died, an error in Dagster's own storage, the step never started) is run again from the failure by the daemon, twice at most; look at the run's page before doing it by hand.
- **The file was downloaded but never extracted** (the `snapshot` step succeeded, `observations` did not, and the retries are spent): the schedule will not try again, because the bytes have not changed since. Re-execute the run from its failure, or materialise `observations` for that source's partition. `uv run link-lens source backfill` finds a snapshot with no observations at all under the mapping in force, not one extracted in part; when unsure, extract again, which stores only what is missing.

**Do not** delete a snapshot, a drift check or observations to "reset" a source. They are append-only and the database refuses; a reset is never what fixes a refresh.

## A source drifted

**How you find out.** An alert "Source drifted", the `schema_drift` check failing on `snapshot`, or `drift_status = blocked` on the source health dashboard.

**What it means.** The publisher's new file no longer has a column the approved mapping uses, or its format changed. Extraction of that snapshot is refused. The previous snapshot, its observations and every release are unaffected.

**Look at.**

```sh
uv run link-lens source drift SOURCE_ID      # the reasons; exits 3 when extraction is blocked
```

**Do.** The new shape needs a mapping that a person approves.

1. Start an onboarding run for the new snapshot: in the Dagster UI, materialise `onboarding_request` for the source's partition. This spends on model calls within the run's budget. It starts nothing if the snapshot already has a run.
2. Review the proposed mapping in the Agent Inbox and accept it, or respond with what to change.
3. On approval the sensor `mapping_approved` requests extraction for the source. Nothing else is needed.

If the change is only a new or removed column the mapping does not use, the check reports `changed` and does not block: extraction continues, and nothing needs doing unless the new column is worth mapping.

**Do not** turn on the `drift_detected` sensor to save step 1 unless you mean every future drift to start a paid onboarding run by itself.

## A review is stuck

**How you find out.** The source health dashboard: "Waiting for review" and "Longest wait, days", and the row's `waiting_since`.

**Look at.** The source's item in the Agent Inbox, and the run:

```sh
uv run link-lens runs                        # status per run; needs_review is waiting for a person
```

**Do.**

- Review it: accept, or respond with feedback, which asks the agent for a revision.
- If the run's thread is gone (the Inbox shows nothing for it), recover the review as the engineering guide describes under **Recovering a requested revision after its attempt budget is exhausted**.
- If the source is not worth the review now, ignore the item. The source keeps serving from its last approved mapping, and refreshes that still fit that mapping continue.

**Do not** approve to clear the queue. An approval is for one exact mapping config and is what every later extraction of that source rests on.

## A release build failed

**How you find out.** An alert "Run failed" for `build_models`, a red run in the Dagster UI after `release create` or after a migration, or the product service answering errors because a view is missing.

**What is and is not affected.** `link-lens release create` records the release, its OKF tree and the bundles of scopes that follow a release, in its own command; a failure after that does not undo the release. The build that can fail afterwards is dbt's: the `serving` views and the reporting models with their tests.

**Look at.** The run's page names the model or the test. To see it outside Dagster:

```sh
uv run link-lens dbt build                   # the same build; exit 1 names what failed
uv run link-lens release show                # the release and its page counts
```

**Do.**

- **A model failed to build** (a column is missing after a migration, a contract mismatch): fix the model or its contract in `transform/models/`, check it beside the live views, then build.

  ```sh
  uv run link-lens serving-compare --build   # exit 3 lists every view that answers differently
  uv run link-lens dbt build
  ```

- **A test failed** (a status the tests do not know, an enum value outside the ontology, a claim without a licence): the views are built and serving. Read what the test found before anything else; it is telling you about the data of that release. If the data is right and the test is out of date, change the test in the same change as its reason.
- **The views are missing** (a new or restored database, or a downgrade): the sensor `models_missing` requests the build within two minutes. By hand it is `uv run link-lens dbt build`.
- **A bundle failed** inside `release create`: the release stands. Build the bundle again; the same release and scope always give the same archive.

  ```sh
  uv run link-lens release bundle RELEASE_ID --scope SCOPE
  ```

**Do not** build only the serving models into `serving` (`dbt run --select serving`): replacing a view drops the reporting views that read it until the next full build. Build the whole project.

## The budget cap is reached

**How you find out.** An alert "Budget" at 80% and again at the cap, or a paid step refusing with a budget error.

**What it means.** The experiment's model budget (`LINK_LENS_MAX_COST_USD`) is reserved before every model call and settled after. At the cap, onboarding and discovery refuse to make further calls. The deterministic flow does not use it: refreshes, extraction, batches, the dbt build and the product service keep working.

**Look at.**

```sh
uv run link-lens ontology budget             # cap, charged, attempts, unsettled attempts
uv run link-lens usage                       # calls per stage and the list-price estimate
```

In Grafana, the product overview has model calls and the budget ledger by experiment and stage.

**Do.**

- Find what spent it: the ledger by stage shows it. A run that failed and was retried keeps every attempt's charge; that is deliberate.
- Unsettled attempts are reservations whose call never reported back. They keep their charge. Do not edit them.
- Raising the cap is the owner's decision: change `LINK_LENS_MAX_COST_USD` in `.env` and recreate the backend and the Dagster services. A new experiment ID starts a new budget; use one only for a genuinely separate run.

**Do not** retry a paid step from the Dagster UI in a loop. Dagster never retries one by itself for this reason.

## Restoring a release

**When.** The database is lost or damaged and clients must be served the release they had.

**What you need.** A dump of `linklens` and the artifact store (the `artifacts/` directory or the bucket). Dagster's own database is not needed to serve a release.

**Do.**

```sh
# On an empty PostgreSQL 17 with the vector extension available:
psql -c "CREATE ROLE linklens_migrator NOLOGIN" -c "CREATE ROLE linklens_pipeline NOLOGIN" \
     -c "CREATE ROLE linklens_product NOLOGIN" -c "CREATE ROLE linklens_transform NOLOGIN" \
     -c "CREATE ROLE linklens_analyst NOLOGIN" -c "CREATE ROLE linklens_orchestrator NOLOGIN"
createdb linklens && pg_restore -d linklens linklens-TIME.dump
uv run alembic upgrade head                  # only if the code is newer than the dump
uv run link-lens dbt build                   # the views, if the dump predates them or a migration dropped them
uv run python scripts/migration_baseline.py --typed --check outputs/local-run/migration-baseline.json
uv run link-lens release digest RELEASE_ID   # must equal the digest noted before the loss
```

The digest covers the batch, the ontology version, every profile version and every page path of the release: equal digests mean the same profiles and the same tree. Note a release's digest when you record it, so there is something to compare with.

A release's OKF pages and bundles are in the dump and the artifact store; nothing is rebuilt for them. The serving views are rebuilt by dbt and answer the same, because a release serves only what was stored when it was recorded.

**Do not** restore into a database that already holds data, and do not create a release again to "repair" one: a second release is a different release with a different ID.

## Dagster itself

**The UI does not answer.**

```sh
docker compose --profile orchestration ps
docker compose --profile orchestration logs dagster-webserver --tail 50
docker compose --profile orchestration up -d
```

A webserver that exits at once with a configuration error is reading a `dagster.yaml` it does not accept; the log names the key.

**A schedule or sensor shows an error.** Open it in the UI under Automation; the tick has the error. The usual cause is code that expects a column a migration has not created yet: apply the migration, and the next tick is clean. Stop the Dagster services while migrating, with the backend.

**Nothing refreshes.** The schedule only acts on sources with a cadence, an approved mapping and no pause:

```sh
uv run link-lens source due
uv run link-lens source cadence SOURCE_ID --days 7
```

**No alerts arrive.** Without `LINK_LENS_ALERT_WEBHOOK_URL` each alert is one `alert.unsent` line in the Dagster daemon's log. With it set, a failed delivery is an `alert.failed` line; the alert is not sent again.

**The assets fail with "must work on the database as linklens_orchestrator".** The Dagster services lost `LINK_LENS_DATABASE_ROLE`, or their login is not a member of that role. They refuse to work with more rights than they should have; fix the configuration, do not remove the check.

**Starting again from nothing.** Dagster's database holds its own history only. Stop the two services, `DROP DATABASE dagster` as the administrator, start them: they come back empty, the sensors start from the present, and nothing of the product is lost.

## The operations console

**Nobody can sign in.** The console signs in only the people listed in `LINK_LENS_ADMIN_USERS`, one line of JSON in `.env`. Nothing listed, a line that is not valid JSON (the log has `console.users_unreadable`), or a role other than `engineer`, `product_owner` or `admin` signs nobody in. Fix the line and recreate the service:

```sh
docker compose --profile console up -d --force-recreate admin
docker compose --profile console logs admin --tail 30
```

**A page says the reporting models are not built.** The console reads a source's status from `analytics`. Build the models: `uv run link-lens dbt build`, or wait for Dagster's `models_missing` sensor.

**An action shows as `unfinished` in the audit log.** Its request was recorded and the service stopped before recording the outcome. Look at the target to see whether the change happened: the source's page, the release list, the client's keys. Asking again is safe for everything except issuing a key, which would make a second key; revoke the one you cannot account for.

**Adding a source failed after "Confirm".** The log row says why. If the onboarding server did not answer, the source and its snapshot are registered and its run exists but was never started: confirm again once the backend is up. The same run is started, and nothing is registered or spent twice.

**Someone should no longer have access.** Remove their token from `LINK_LENS_ADMIN_USERS` and recreate the service. A token does not expire by itself.

**Do not** hand out one token to several people: the audit log would record them all under one name.

## Backups

```sh
scripts/backup_databases.sh /path/to/backups        # both databases; prunes Dagster dumps older than 7 days
scripts/backup_databases.sh /path/to/backups 14     # keep Dagster's for 14 days instead
```

The script dumps `linklens` and `dagster`, checks that each archive lists, and writes a checksum beside each. It never deletes a `linklens` dump: that is the application's data and may be the only copy, so how long to keep those is a decision, not a default. Dagster's dumps are run history and are pruned.

Artifact bytes are in neither dump. Back up `artifacts/` or the bucket with them, and keep a dump and the artifacts of the same moment together.

Before a migration, take a dump with the services stopped and rehearse on a restored copy first; the engineering guide has the procedure under **Changing a database that holds data**.
