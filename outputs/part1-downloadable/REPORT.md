# Part 1 rerun: download-verified shortlist

**Result: 50 ranked datasets passed a real GET and reader preflight. AI audit: 47 supported, 1 unsupported, 2 unresolved.** The human 20-item worksheet is ready; human review remains pending. All six existing portfolio sources remain included. Parts 2–4 were not rerun: the observations, links, profiles, selection and source-removal files retain their original SHA-256 hashes.

## What changed

Previously the code checked format metadata, not download success. Of the earlier 14 unresolved audit items, 13 concerned inaccessible/empty downloads and one concerned ambiguous brand ownership. The new gate checks candidate resources in the existing ranked order, retains the eight-per-publisher cap, and selects the first 50 passing candidates. It examined 93 candidates: 55 had an available resource; the ranking/cap selected 50. Thirty-five old shortlist entries remain and 15 are replaced.

This rerun reuses the same 945-record catalogue and 213 saved Jev metadata decisions. No fresh catalogue retrieval or model inference was needed: **zero additional application model calls or LLM cost**. Download/network/computation costs and this assistant's audit usage are not in the application API ledger. The overall priced subtotal remains $0.261160344 for 275/292 calls.

## What “download-verified” means

The code GETs actual content rather than relying on HEAD or filename. CSV/TSV uses a bounded 1 MiB sample; XLSX/JSON must fit a 100 MB complete response. It rejects empty bodies, HTML responses, unreadable tables, ZIP payloads disguised as CSV and CSV resource indexes pointing to unsupported bulk formats. It tries up to twelve supported resources per dataset, including alternative resources. Publisher-linked public external hosting is allowed; non-public destinations are blocked, and legacy HTTP URLs are tried over HTTPS.

Receipts include time, URL, HTTP status/error, bytes, sample hash and parsed evidence. A failure means unavailable **at the check time under these bounds and reader policy**—not permanently unavailable. A passing prefix does not guarantee a complete multi-gigabyte file will ingest successfully. A dataset can pass through an older resource or companion table; the selected resource ID is explicit. External-host preflight eligibility is broader than the existing government-domain registration policy, so some non-portfolio sources still need a reviewed acquisition-policy extension before onboarding. All six already-onboarded portfolio sources remain usable.

Three iterations were retained during development: v1 exposed over-restrictive host checks, v2 allowed public external hosting, and v3 excluded resource-index CSVs. The final revision is `discovery-jev-luna-v1-downloadable-v3`. Superseded attempts are not the published shortlist.

## Evaluation after freezing the shortlist

All 50 ranks were reviewed using fresh download samples and, where necessary, fresh companion party tables or signed declarations. No audit labels were fed to Jev or used to repair ranks after evaluation.

- **47 supported:** identifiable organisations, including charities, public bodies and named commercial venues under the declared broad relevance criterion. Some require companion documents or joined party tables before mapping.
- **1 unsupported:** Asbestos Register contains asset/material records; a fixed council-owner abbreviation does not make its rows business subjects.
- **2 unresolved:** labelled and non-labelled appliance data show Daikin brand information without establishing the owning legal organisation in inspected fields. These are semantic uncertainty, not access failures.

The AI negative fraction is **1/48 = 2.08% among resolved judgments**, with **2/50 unresolved**. This is not a human false-positive estimate or a guarantee about every row. The old 36/0/14 and new 47/1/2 results reflect a filtering-policy change and different shortlist membership, not a model-only benchmark.

[All 50 judgments](FULL_SHORTLIST_REPORT.md) · [Expandable audit](full-shortlist-report.html) · [Download receipts](download-checks.json) · [Companion evidence](followup.json) · [Frozen ranking](shortlist.jsonl) · [Preserved prior results](../../experiments/jev-luna-before-download-gate/README.md).

## Repeat the Part 1 operation

Fresh catalogue + Jev decisions + download gate (spends API tokens for uncached metadata):

```sh
uv run link-lens discover
```

Recheck the saved catalogue/ranking without new Jev calls; choose a new revision ID for each rerun:

```sh
uv run link-lens discover \
  --recheck-from discovery-jev-luna-v1 \
  --revision discovery-jev-luna-v1-downloadable-demo-1
uv run link-lens worksheet triage \
  --batch-id discovery-jev-luna-v1-downloadable-demo-1 \
  --output outputs/triage-review-demo.json
```

The CLI updates the current-discovery pointer while retaining the historical record. It does not run onboarding, extraction, resolution or profiles. The evidence collector and authored audit scripts for this saved run live in `scripts/recheck_part1_downloads.py`, `scripts/collect_downloadable_followup.py` and `scripts/record_downloadable_audit.py`; the last script's judgments apply only to this frozen shortlist and must not be reused as labels for a changed run.

The existing frozen database archive predates this Part 1 revision. It remains a valid six-source profile demo; the current Part 1 evidence is supplied in this directory and the main outputs. Restore that archive into a separate demo database rather than using it to overwrite this revision.
