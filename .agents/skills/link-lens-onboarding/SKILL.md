---
name: link-lens-onboarding
description: Onboard a new Link Lens dataset, demonstrate seventh-source generalisation, or diagnose and resume mapping review. Use for source registration, agent runs and approval/extraction recovery; not for documentation-only edits or Part 1 ranking refreshes.
---

# Source onboarding and review

Read root `AGENTS.md`, then the relevant sections of `README.md`, `docs/DEMO.md` and `docs/ENGINEERING.md`. All paths and commands below are relative to the repository root.

## Establish the run

1. Determine the requested dataset/resource, experiment, existing source/run/thread IDs and desired output directory. Use existing authorisation; ask only for genuinely missing decisions. Do not start a duplicate run when the user asks to resume one.
2. Inspect current metadata with `uv run link-lens runs` and `uv run link-lens runs --run-id RUN_ID`. Use command `--help` and read `cli.py`/`agent.py` for behaviour before state-changing recovery.
3. For an independent experiment, use a new experiment ID consistently in host CLI and backend configuration. Backend settings are cached; recreate the backend after environment changes as described in README. Do not overwrite or print `.env` secrets.
4. Verify services and the fixed sandbox image. A provider smoke test makes a metered call: run it when connectivity needs checking for an authorised live task, not automatically for saved-result inspection.

## Select evidence and start

1. Confirm publisher, resource URL, licence, record grain, timestamp evidence and reader support. For a seventh source intended to enrich profiles, inspect validated identifier overlap with the existing cohort. A plausible overlap is a selection hypothesis, not an extracted contribution.
2. Follow the current seventh-source example in `docs/DEMO.md`; do not hard-code its run IDs into reusable code. Do not create a hand-written mapping or source-specific extractor to make the demonstration succeed.
3. Register and start only when needed:

```sh
uv run link-lens register DATASET_ID --resource RESOURCE_ID
uv run link-lens onboard RUN_ID
uv run link-lens runs --run-id RUN_ID
```

4. Confirm the agent freezes reader settings and disjoint partitions, explores discovery data only, proposes typed mappings, receives bounded validation feedback, critiques semantics and reaches final validation within budgets. Preserve real failures and revisions in the ledger.

## Review or recover

1. At an interrupt, give the user the Inbox/thread location and a concise account of the proposed semantics and uncertainties. Mapping acceptance belongs to the human reviewer. Do not invoke `review ... accept` on their behalf without explicit authorisation for that exact proposal.
2. Accept must refer to the immutable config hash. Respond is feedback followed by revision and another review; a new “Requires Action” state can therefore be expected. Ignore defers and must prevent extraction.
3. Diagnose UI/resume failures using the thread state, application run, stored approval hash and backend error. Distinguish a recorded approval followed by failed extraction from an unrecorded approval. Preserve idempotency and avoid duplicate extraction when resuming.
4. Read `runtime_compat.py` and recovery tests before changing nullable resume handling or checkpoint persistence. Add a focused regression test for the actual failure.
5. Do not hand-edit generated mappings, leak final-test records, silently increase budgets or mark failures completed. Recovery attempts must retain predecessor IDs and costs. Feedback revisions require another valid final slice and fresh approval.

## Complete and demonstrate

1. Verify completed status and observations before assembling. Use explicit selected run IDs and a separate export directory:

```sh
uv run link-lens assemble RUN_1 RUN_2 RUN_3 RUN_4 RUN_5 RUN_6 RUN_7 --cohort-pool-size 25000
uv run link-lens export --batch-id BATCH_ID --output outputs/seventh-source-run
```

2. Compare source contribution and cross-source linking support with the six-source batch. Count actual profiles receiving evidence from the new source; include an example claim with provenance. Do not infer contribution merely from an approved config or source appearing in the viewer.
3. Report dataset/resource, snapshot/config hash, run/thread/batch IDs, approval state, outputs, usage and any unfinished steps. Update the demo and relevant results documents only for demonstrated behaviour. Keep the six-source submission and historical comparison intact unless replacement was requested.
