---
name: link-lens-evidence-refresh
description: Refresh Link Lens discovery, exported evidence, AI audits, costs or experiment comparisons while preserving provenance. Use for scoped Part 1 reruns, full-result refreshes and evaluation reports; not for starting or repairing source onboarding alone.
---

# Evidence refresh and evaluation

Read root `AGENTS.md`, `outputs/README.md` and the report relevant to the requested change. Use paths relative to the repository root. Prefer existing CLI operations; inspect helper scripts before execution because some contain fixed IDs, authored judgments and top-level writes.

## Freeze scope and provenance

1. Identify whether the task concerns downloads/ranking, inference, extraction/linking, evaluation, pricing or documentation. Run only the necessary stages. A download-only recheck should reuse saved Jev decisions; a pricing update should reuse usage records.
2. Record the experiment, active discovery revision from `store.current_discovery()`, selected run/config/snapshot IDs, batch, worksheet IDs and output destination. Preserve earlier evidence before replacing current outputs. Use a distinct destination for independent experiments.
3. Read scripts' output paths and assumptions before calling them. Do not import a script to inspect it. In particular, an original `discovery-<experiment>` ID can differ from the active download-gated revision. Historical `record_*audit.py` files are not reusable judges for new records.

## Refresh the requested stage

For Part 1 using existing catalogue metadata and cached Jev decisions:

```sh
uv run link-lens discover --recheck-from DISCOVERY_ID --revision NEW_REVISION_ID
```

Use a new revision ID, preserve the previous record, and verify the active pointer afterward. Confirm unique shortlist IDs, rank order, publisher cap and saved GET/reader evidence. Availability means readable under the bounded policy at the check time; it does not guarantee relevant entity data. Never feed audit labels back into the ranking being evaluated. Check whether the selected six sources remain in the shortlist and report substitutions or inconsistencies explicitly.

For result assembly/export, require completed approved runs and use explicit run/batch IDs. Preserve the existing submission unless replacing it is in scope. Check snapshot hashes before claiming two experiments used identical data. Matching model names or source titles alone do not establish comparable inputs.

## Evaluate independently

1. Identify the exact population and sample: all 50 shortlisted datasets, all proposed links, or the assignment's seeded 20/50 worksheets. Do not conflate an exhaustive AI audit with sampled human review.
2. Inspect primary publisher/resource evidence for dataset relevance and identifier/subject-role evidence for links. Record item ID, verdict, supporting evidence and uncertainty. A failed download alone does not prove semantic irrelevance; a successful download alone does not prove relevance.
3. Keep AI labels separate using `import-ai-audit`. Human labels use `import-labels` only when a person actually reviewed the evidence. Preserve indiscriminate/unreviewed submissions as unreviewed, never as measured accuracy.
4. Reuse a prior audit only when item identity and relevant evidence are unchanged, and disclose the reuse. Do not copy labels by row number or force unresolved cases to yes/no.
5. Report supported, unsupported and unresolved counts, numerator/denominator, sample method, threshold and reviewer type. Explain what remains pending in human evaluation without implying AI review completed it.

## Recalculate costs and compare

1. Use stored call events, including failures/retries and inherited recovery attempts. Separate triage, onboarding and deterministic per-record processing; avoid double-counting reused cached decisions as new paid calls.
2. Use `src/link_lens/pricing_rates.json`. When updating rates, verify the official provider page and retain model, units, date, source URL and pricing basis. Azure costs may be estimated using the agreed OpenAI rates; label that estimate.
3. Reconcile input/output/cached tokens as available. Report priced-call coverage and missing usage separately. Unknown usage is not zero; a known-call subtotal is not a complete total.
4. Preserve baseline artifacts. Distinguish effects of model changes, download filtering, catalogue differences, sampling and mapping changes. Do not attribute every improvement to a model when other conditions changed.

## Publish consistent local artifacts

1. Refresh machine-readable exports and generated reports for the correct revision/batch. `scripts/report_current_experiment.py` writes current submission outputs: inspect it before use. Curated `outputs/README.md` and `outputs/COMPARISON.md` still need a consistency pass.
2. Update relevant summaries: `outputs/README.md`, `outputs/COSTS.md`, `outputs/COMPARISON.md`, `WRITEUP.md`, and README/demo if their claims changed. Preserve historical screenshot context. Do not recreate the previously merged overview/review/architecture files.
3. Verify counts from JSON/JSONL, unique IDs, selected config hashes, source contributions, audit population and cost subtotals. Check OKF against structured profiles and relative links. For code changes, run focused tests and the appropriate deterministic suite; do not trigger live inference just to validate prose.
4. Finish with the stages actually rerun, evidence/output paths, changed measurements and pending human actions. Explicitly state when downstream six-source results were preserved during a Part 1-only refresh.
