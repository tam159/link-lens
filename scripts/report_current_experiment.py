"""Refresh scoped outputs and comparison; no model calls or mapping approvals."""

import json
from pathlib import Path

from link_lens import exports, store
from link_lens.ingestion import PORTFOLIO
from link_lens.settings import settings

root = Path("outputs")
experiment = settings().experiment_id
runs = [r for r in store.listing("runs") if r.get("experiment_id") == experiment]
latest = {r["source_slug"]: r for r in runs if r["source_slug"] in PORTFOLIO}
portfolio = [latest[slug] for slug in PORTFOLIO if slug in latest]
batches = [
    b
    for b in store.listing("batches", kind="pipeline")
    if set(b["run_ids"]).issubset({r["id"] for r in portfolio})
]
batch = batches[-1] if batches else None
if batch:
    exports.export(
        root, None, experiment
    )  # retain failed/replaced attempt evidence too
exports.export(root, batch["id"] if batch else None, experiment)
m = json.loads((root / "measurement-summary.json").read_text())
cost = json.loads((root / "cost-summary.json").read_text())
oldroot = Path("experiments/terra-baseline/outputs")
oldcost = json.loads((oldroot / "cost-summary.json").read_text())
old = store.require("batches", "discovery-terra-baseline")
new = store.current_discovery(experiment)
oldids = {r["dataset_id"] for r in old["shortlist"]}
newids = {r["dataset_id"] for r in new["shortlist"]}
oldcat = {d["id"] for d in store.read_json(old["catalogue_artifact"])}
newcat = {d["id"] for d in store.read_json(new["catalogue_artifact"])}
snapshots = []
for run in portfolio:
    previous = [
        r
        for r in store.listing("runs")
        if r.get("experiment_id", "terra-baseline") == "terra-baseline"
        and r["source_slug"] == run["source_slug"]
        and r["status"] == "completed"
    ]
    snapshots.append(
        {
            "source": run["source_slug"],
            "same_snapshot_as_baseline": bool(
                previous and previous[-1]["snapshot_id"] == run["snapshot_id"]
            ),
        }
    )
auditpath = root / "ai-audit/full-triage-summary.json"
audit = json.loads(auditpath.read_text()) if auditpath.exists() else None
linkpath = root / "ai-audit/links-summary.json"
link_audit = json.loads(linkpath.read_text()) if linkpath.exists() else None
contributions = []
if batch:
    result = store.read_json(batch["result_artifact"])
    for run in portfolio:
        sid = run["source_id"]
        contributions.append(
            {
                "source": run["source_slug"],
                "source_id": sid,
                "observations": sum(
                    o["source_id"] == sid for o in result["observations"]
                ),
                "profiles_receiving_evidence": sum(
                    sid in {ref[0] for ref in p["source_records"]}
                    for p in result["profiles"]
                ),
            }
        )
exports.write_json(root / "source-contributions.json", contributions)


def scope_cost(report, sources):
    calls = [c for c in report["call_details"] if c["source"] in sources]
    known = [c for c in calls if c["estimated_standard_list_cost_usd"] is not None]
    return {
        "calls": len(calls),
        "priced": len(known),
        "unpriced": len(calls) - len(known),
        "subtotal_usd": sum(c["estimated_standard_list_cost_usd"] for c in known),
    }


common_costs = {
    "baseline_six_sources_all_attempts": scope_cost(oldcost, PORTFOLIO),
    "current_six_sources_all_attempts": scope_cost(cost, PORTFOLIO),
    "current_jev_triage": scope_cost(cost, ["catalogue triage"]),
}
comparison = {
    "generated_at": store.now(),
    "current_experiment": experiment,
    "baseline_cost": {
        k: oldcost[k]
        for k in ["calls", "priced_calls", "unpriced_calls", "measured_subtotal_usd"]
    },
    "current_cost": {
        k: cost[k]
        for k in ["calls", "priced_calls", "unpriced_calls", "measured_subtotal_usd"]
    },
    "baseline_counts": {
        "observations": 20851,
        "links": 50,
        "unlinked": 5535,
        "profiles": 50,
    },
    "current_counts": batch["counts"] if batch else None,
    "baseline_ai_triage": {"yes": 39, "no": 5, "unsure": 6},
    "current_ai_triage": audit,
    "current_ai_links": link_audit,
    "comparable_cost_scopes": common_costs,
    "source_contributions": contributions,
    "shortlist_overlap": len(oldids & newids),
    "shortlist_added": sorted(newids - oldids),
    "shortlist_removed": sorted(oldids - newids),
    "catalogue_overlap": len(oldcat & newcat),
    "catalogue_added": sorted(newcat - oldcat),
    "catalogue_removed": sorted(oldcat - newcat),
    "snapshots": snapshots,
    "caveat": "Operational before/after comparison, not controlled model-only A/B test. Baseline includes development failures and a seventh-source run. Prompt improvements and review/recovery counts differ. Missing usage excludes some calls from cost subtotals. AI audits are not human ground truth.",
}
if new.get("supersedes_discovery_id"):
    prior = store.require("batches", new["supersedes_discovery_id"])
    prior_ids = {r["dataset_id"] for r in prior["shortlist"]}
    prior_audits = [
        w for w in store.listing("evaluations", owner=prior["id"], kind="ai_census")
    ]
    from link_lens import evaluation

    prior_report = (
        evaluation.ai_report(prior_audits[-1]["id"]) if prior_audits else None
    )
    comparison["download_gate_revision"] = {
        "id": new["id"],
        "previous_audit": prior_report,
        "retained": len(prior_ids & newids),
        "replaced": len(prior_ids - newids),
        "additional_model_calls": new.get("rerun_model_calls"),
        "downstream_rerun": False,
    }
exports.write_json(root / "comparison.json", comparison)
exports.write_json(
    root / "current-run.json",
    {
        "experiment_id": experiment,
        "discovery_id": new["id"],
        "run_ids": [r["id"] for r in portfolio],
        "batch_id": batch["id"] if batch else None,
        "snapshots": snapshots,
    },
)
rows = []
for r in portfolio:
    thread = r.get("thread_id")
    url = f"http://localhost:3000/?agent_inbox=51ac7658-4563-4acc-96e0-22f899803cc7&offset=0&limit=10&inbox=all&view_state_thread_id={thread}"
    rows.append(
        f"| {r['source_slug']} | {r['status']} | {r['version']} | {r['model_calls']} | [Inbox]({url}) |"
    )
counts_text = (
    f"{batch['counts']['observations']:,} observations; {batch['counts']['links']} links; {batch['counts']['unlinked']:,} unlinked records; {batch['counts']['profiles']} profiles"
    if batch
    else "Pending fresh approvals"
)
status = (
    "Pipeline exported"
    if batch
    else "Onboarding / mapping review; new links and profiles not yet produced"
)
# outputs/README.md is the curated assignment checklist; keep automatic refreshes separate.
(root / "RUN_STATUS.md").write_text(f"""# Current submission outputs: Jev + Luna

Experiment `{experiment}`. Updated {store.now()}.

**Status: {status}.** Prior Terra results are preserved separately in [the baseline archive](../experiments/terra-baseline/outputs/README.md).

| Assignment stage | Current evidence |
|---|---|
| 1 — Discovery and triage | {new["unique_records"]} unique records; {new["jev_candidates"]} Jev-scored supported-format candidates; [50 ranked datasets](shortlist.jsonl) |
| 2 — Schema inference | Fresh `gpt-5.6-luna` runs; [versioned configs and review packets](onboarding/) |
| 3–4 — Linking and profiles | {counts_text} |
| 5 — Evaluation | [50-dataset audit](ai-audit/FULL_SHORTLIST_REPORT.md): {audit["supported"] if audit else "pending"} supported / {audit["not_supported"] if audit else "pending"} unsupported / {audit["unresolved"] if audit else "pending"} unresolved. [All-link audit](ai-audit/LINKS_REPORT.md): {str(link_audit["supported"]) + "/" + str(link_audit["sample_size"]) + " supported" if link_audit else "pending"}. Human evaluation remains incomplete. |
| Tokens | {m["total_measured_input_tokens"]:,} input / {m["total_measured_output_tokens"]:,} output, across {cost["calls"]} calls including failures |
| Estimated cost | ${cost["measured_subtotal_usd"]:.6f}; {cost["priced_calls"]}/{cost["calls"]} priced calls; [cost details](COSTS.md) |
| Per-record LLM processing | 0 calls / $0 LLM fees for extraction, linking and profiles |

## Source contributions

| Source | Observations | Profiles receiving evidence |
|---|---:|---:|
{chr(10).join(f"| {v['source']} | {v['observations']} | {v['profiles_receiving_evidence']} |" for v in contributions)}

Only Companies, ATO and ACNC contribute to these profiles. AFS's approved partial mapping omits identifiers; Business Names omits uncertain ABN ownership; Employment has no usable IDs. See the [comparison](COMPARISON.md) for coverage losses and cohort bias.

## Mapping reviews

Read [review notes](README.md#8-mapping-approvals) first for source-specific decisions and the latest recovery status.

| Source | Status | Version | Model calls | Review |
|---|---|---:|---:|---|
{chr(10).join(rows)}

Accept approves the exact Luna config. Previous Terra approvals do not apply. Respond requests a revision and Ignore prevents extraction.

## Detailed files

- [OKF viewer](okf/viewer.html), [profiles](profiles.jsonl), [links](links.jsonl), [unlinked queue](unlinked.jsonl), [observations](observations.jsonl).
- [Source contributions](source-contributions.json) and [source-removal analysis](source-removal.json).
- [Comparison](COMPARISON.md): previous versus current, with scope and data differences.
- [Measurements](measurement-summary.json): scoped runtime, usage, evaluations and pipeline counts.
- [Cost ledger](cost-usage.json) and [calculation](cost-summary.json): saved per-call metadata.
- [Discovery audit](discovery-audit.json): queries, policy and immutable catalogue artifact.
- [Current run IDs](current-run.json): inputs for resuming this experiment.
- [Reproduction and continuation](../docs/ENGINEERING.md#operations-and-recovery).

Jev judges metadata relevance, not download availability or identity. Its probability and the combined ranking score are uncalibrated for this task. AI evidence audits never become human labels.
""")
(root / "COSTS.md").write_text(
    f"""# Current experiment costs

Only `{experiment}` is included; earlier Terra receipts remain archived.

Measured subtotal: **${cost["measured_subtotal_usd"]:.8f}**, covering **{cost["priced_calls"]}/{cost["calls"]} calls**. Unpriced calls: {cost["unpriced_calls"]}. {"All six sources are approved and the pipeline is complete; missing usage still prevents a complete cost total." if batch else "Onboarding/review is ongoing."}

| Stage/run | Calls | Priced | Estimated USD |
|---|---:|---:|---:|
"""
    + "\n".join(
        f"| {r['source']} ({r['run_id']}) | {r['calls']} | {r['priced_calls']} | {r['measured_subtotal_usd']:.8f} |"
        for r in cost["per_run"]
    )
    + """

Rates are stored together in [pricing_rates.json](../src/link_lens/pricing_rates.json): Jev input $0.042/M, output $0/M; Luna standard short-context input $0.20/M, cache read $0.02/M, cache write $0.25/M, output $1.20/M. OpenAI rates are the agreed Azure estimate. Jev response-reported cost is retained alongside the published-rate calculation.

No output-token charge for Jev does not mean zero output tokens. Failures with missing usage remain unpriced. No per-record LLM calls occur in extraction/linking/profile assembly; infrastructure costs are outside this estimate. Assistant development and audit tokens are not available in the application ledger.

See [per-call calculations](cost-summary.json), [usage ledger](cost-usage.json), and [comparison](COMPARISON.md).
"""
)
# COMPARISON.md is the curated three-stage account; automatic metrics stay separate.
(root / "COMPARISON_STATUS.md").write_text(f"""# Previous versus current approach

| Dimension | Previous: deterministic + Terra | Current: Jev + Luna |
|---|---|---|
| Role | Preserved baseline | Selected final submission approach; {"pipeline complete" if batch else "rerun in progress"} |
| Catalogue records | {old["unique_records"]} | {new["unique_records"]} |
| Triage | Deterministic metadata rules | Rules + Jev on {new["jev_candidates"]} candidates |
| Shortlist | 50 | 50; {len(oldids & newids)} retained, {len(newids - oldids)} changed |
| Onboarding model | gpt-5.6-terra | gpt-5.6-luna |
| Model calls | {oldcost["calls"]} | {cost["calls"]} (includes Jev) |
| Estimated cost | ${oldcost["measured_subtotal_usd"]:.6f}; {oldcost["unpriced_calls"]} unpriced | ${cost["measured_subtotal_usd"]:.6f}; {cost["unpriced_calls"]} unpriced |
| Full shortlist AI audit | 39 relevant / 5 irrelevant / 6 unresolved | {(str(audit["supported"]) + " supported / " + str(audit["not_supported"]) + " unsupported / " + str(audit["unresolved"]) + " unresolved") if audit else "Pending evidence review"} |
| Links / profiles | 50 / 50 | {str(batch["counts"]["links"]) + " / " + str(batch["counts"]["profiles"]) if batch else "Pending fresh approvals"} |
| Link AI audit | 50 supported / 0 unsupported / 0 unresolved | {str(link_audit["supported"]) + " supported / " + str(link_audit["not_supported"]) + " unsupported / " + str(link_audit["unresolved"]) + " unresolved" if link_audit else "Pending"} |
| Evaluation completion | AI complete; human checks pending | AI complete; human checks pending |

This is an operational comparison, **not a controlled model-only experiment**. Catalogue overlap is {len(oldcat & newcat)} records; {len(newcat - oldcat)} were added and {len(oldcat - newcat)} removed. Snapshot equality per source is recorded in [comparison.json](comparison.json). Both runs use the same six-source portfolio, shared extraction/linking policies and sampling limits, but configurations are generated anew.

The baseline's $2.02 includes development failures, superseded attempts, connectivity tests and a seventh source. The current run includes Jev triage, Luna retries and several human-requested revision recoveries. Missing usage differs (2 versus {cost["unpriced_calls"]}); do not interpret subtotal differences as a measured percentage saving for equally complete workloads. AI triage labels judge evidence, not Jev confidence; a passing download check does not establish business relevance. No human accuracy claim is made.

## Matched cost scope

| Scope | Calls | Priced | Unpriced | USD subtotal |
|---|---:|---:|---:|---:|
{chr(10).join(f"| {name} | {v['calls']} | {v['priced']} | {v['unpriced']} | {v['subtotal_usd']:.8f} |" for name, v in common_costs.items())}

Both six-source rows include every attempt for those source names; connectivity and the historical seventh source are excluded. Jev is shown separately. Workflow and review counts still differ.

## Quality and contribution trade-offs

All six snapshots match the baseline byte-for-byte, but only 943/945 catalogue IDs overlap. The final cohorts differ, so 52 versus 50 links is not a recall gain. ATO now has a legal-entity subject role and contributes 35 profiles. Luna's final AFS mapping leaves the documented mixed ABN/ACN column unmapped following an overly conservative critique, so AFS contributes zero versus 18 previously. Length/checksum classification is supported by the shared engine and the documented ABN-or-ACN column; the model's claim that a separate type flag is always required is not an engine limitation. We retain the approved partial output and disclose this loss of extraction coverage rather than editing the mapping after approval.

The current audit counts above apply to the active discovery revision. See [the comparison](COMPARISON.md) for the initial Jev shortlist and the subsequent download-gate change. Resolved-only support cannot establish a model-only improvement. Lower token prices do not prove Luna is as capable as Terra. Failed/replaced attempts and feedback-driven changes remain visible.

| Source | Observations | Profiles receiving evidence |
|---|---:|---:|
{chr(10).join(f"| {v['source']} | {v['observations']} | {v['profiles_receiving_evidence']} |" for v in contributions)}

[Frozen baseline](../experiments/terra-baseline/manifest.json) contains file hashes and its original outputs, docs, pricing and frozen demo. [Current overview](README.md) is the entry point for the new submission.
""")
print(
    json.dumps(
        {
            "status": status,
            "cost_usd": cost["measured_subtotal_usd"],
            "runs": [(r["source_slug"], r["status"]) for r in portfolio],
        },
        indent=2,
    )
)
