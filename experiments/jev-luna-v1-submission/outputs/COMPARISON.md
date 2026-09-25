# Comparison — Terra baseline to the final Jev + Luna approach

**Current approach:** Jev metadata triage plus deterministic download checks, followed by Luna onboarding. The latest change reran **Part 1 only**: all 50 shortlisted datasets now have a readable downloaded resource. Its AI audit found **47 supported, 1 unsupported and 2 unresolved**. The six approved mappings, 52 links and 52 profiles are unchanged.

## 1. Three stages of the project

| Dimension | Original baseline | Initial Jev + Luna | Final approach |
|---|---|---|---|
| Part 1 ranking | Deterministic metadata rules | Rules + Jev metadata scores | Same rules + Jev scores, with download/reader gate |
| Catalogue records | 945 | 945 | Same saved 945-record catalogue as initial Jev run |
| Jev decisions | None | 213 candidates scored | Reused all saved scores; no new calls |
| Ranked shortlist | 50 datasets | 50 datasets | **50 download-verified datasets** |
| Download verification before selection | Format metadata only | Format metadata only | Actual bounded GET and reader check |
| Full-shortlist AI audit | 39 supported / 5 unsupported / 6 unresolved | 36 supported / 0 unsupported / 14 unresolved | **47 supported / 1 unsupported / 2 unresolved** |
| Part 2 model | gpt-5.6-terra | gpt-5.6-luna | Same approved Luna configurations |
| Approved portfolio configurations | 6 | 6 | Same 6; all remain in the revised shortlist |
| Observations | 20,851 | 20,838 | **20,838 — unchanged** |
| Links / profiles | 50 / 50 | 52 / 52 | **52 / 52 — unchanged** |
| Unlinked records | 5,535 | 5,543 | **5,543 — unchanged** |
| All-link AI audit | 50/50 supported | 52/52 supported | Same 52/52 evidence audit |
| Evaluation completion | AI audits complete; human checks pending | AI audits complete; human checks pending | **Partially complete: AI audits complete; human checks pending** |

These are operational before/after results. The move from Terra to Luna also involved prompt changes, different revision histories and different selected entity cohorts. It does not isolate model quality. The latest download-gate comparison is narrower: the catalogue and Jev scores stayed fixed, and only Part 1 selection and its audit changed.

## 2. What the download gate improved

The previous 14 unresolved cases comprised **13 access-related cases and one ambiguous brand-identity case**. Code now checks that a candidate resource is accessible and readable before it enters the shortlist.

| Part 1 revision measurement | Result |
|---|---:|
| Candidate datasets checked | 93 |
| Candidates with a passing resource | 55 |
| Selected after ranking and publisher cap | **50** |
| Entries retained from initial Jev shortlist | 35 |
| Entries replaced | 15 |
| Entries shared with original Terra shortlist | 26 |
| Additional model calls / model API cost | **0 / $0** |
| Existing portfolio sources retained | **6/6** |

The eight-per-publisher cap and existing relevance ranking remain in place. No evaluation labels were used to select replacements, and the shortlist was frozen before the new AI audit.

**Downloadability and relevance are separate checks.** Both current unresolved entries are appliance datasets whose downloaded rows show a brand without establishing its legal owner. The unsupported entry is an asbestos asset register. They remain in the evaluated shortlist: successful downloading does not guarantee business relevance.

The gate checks a bounded CSV/TSV sample or a complete size-bounded XLSX/JSON response. It rejects empty responses, HTML pages, unreadable data, unsupported ZIP payloads and CSV download indexes. Passing establishes availability under this policy at the check time; it does not guarantee full-file ingestion, legal-entity identity or future availability. Some datasets qualify through older resources or companion tables. [Policy, receipts and reproduction commands](part1-downloadable/REPORT.md).

## 3. How to interpret the evaluation

| AI shortlist audit | Supported | Unsupported | Unresolved | Unsupported among resolved judgments |
|---|---:|---:|---:|---:|
| Terra baseline | 39 | 5 | 6 | 5/44 = 11.36% |
| Initial Jev shortlist | 36 | 0 | 14 | 0/36 = 0%, with 14 unresolved |
| Download-verified Jev shortlist | **47** | **1** | **2** | **1/48 = 2.08%**, with 2 unresolved |

The final shortlist has stronger inspected evidence coverage: 48 of 50 judgments are resolved, compared with 36 initially. The initial zero-negative result concealed more unknowns; it was not evidence of perfect triage. These percentages describe **AI evidence judgments**, not human-measured false-positive rates or general model accuracy. The lists differ, and the broad relevance criterion includes charities, named commercial venues and public organisations as well as companies.

Human worksheets remain ready for **20 datasets and 50 links**. The new dataset worksheet corresponds to the refreshed shortlist; the link worksheet remains tied to the unchanged pipeline batch. Mapping approvals are complete and are separate from these evidence checks. [Current dataset audit](ai-audit/FULL_SHORTLIST_REPORT.md), [link audit](ai-audit/LINKS_REPORT.md), [evaluation status](README.md#9-complete-the-human-evaluation).

## 4. Cost and token comparison

| Measurement | Terra baseline | Jev + Luna, including latest Part 1 revision |
|---|---:|---:|
| Application model calls | 52 | 292: 213 Jev + 79 Luna |
| Calls with priced usage | 50/52 | 275/292 |
| Calls with unavailable usage | 2 | 17 |
| Recorded input tokens | 543,853 | 836,479 |
| Recorded output tokens | 58,322 | 82,696 |
| Estimated priced subtotal | **$2.0150253 (~$2.02)** | **$0.261160344 (~$0.26)** |
| Per-record LLM calls for extraction, linking and profiles | 0 | 0 |
| Additional API cost for download-gate rerun | — | **$0: cached Jev scores reused** |

These are estimates for recorded usage, including failed and superseded attempts. Missing usage is not counted as zero. Published OpenAI rates approximate Azure cost; Jev uses its saved published rates. Infrastructure, download computation and assistant development/audit costs are outside this ledger.

For a closer cost comparison, separate the six-source onboarding attempts from catalogue triage and extras:

| Scope | Calls | Priced | Usage unavailable | Estimated USD subtotal |
|---|---:|---:|---:|---:|
| Terra — all attempts for the six portfolio sources | 47 | 45 | 2 | $1.85625030 |
| Luna — all attempts for the same six sources | 78 | 61 | 17 | $0.25308870 |
| Jev — catalogue triage | 213 | 213 | 0 | $0.007996044 |
| Luna — connectivity check | 1 | 1 | 0 | $0.00007560 |

The whole Terra total additionally includes historical seventh-source work and connectivity. Even the six-source comparison has different retry/review histories and usage coverage, so it supports a lower **recorded subtotal**, not an exact percentage saving for equivalent workloads. [Current receipts and rates](COSTS.md), [baseline costs](../experiments/terra-baseline/outputs/COSTS.md).

## 5. Profile contributions: what changed with Luna

The six source snapshots match the Terra baseline byte-for-byte. Their approved mappings and selected cohorts differ; the latest Part 1 download checks did not modify either.

| Source | Terra profiles receiving evidence | Luna profiles receiving evidence | Interpretation |
|---|---:|---:|---|
| ASIC Companies | 47 | **52** | Company identifiers anchor the current linked cohort. |
| ACNC Charities | 35 | **17** | Both approaches extract charity evidence; the selected cohort differs. |
| ASIC AFS Licensees | 18 | **0** | Final Luna mapping extracts addresses but leaves mixed ABN/ACN unmapped. Identifier inference is a next improvement. |
| ASIC Business Names | 0 | **0** | Trading-name extraction remains separate from uncertain holder identity. |
| ATO Corporate Tax Transparency | 0 | **35** | The approved legal-entity role enables ABN-based identity support. |
| Employment Locations | 0 | **0** | Site records remain unlinked without strong entity identifiers. |

Contribution counts overlap; adding them does not give unique entities. **52 versus 50 profiles is not a measured recall gain.** The overlap-selected cohorts were designed to demonstrate profile assembly, not population coverage.

For AFS, the shared engine already supports length/checksum classification of the documented ABN-or-ACN field. An overly conservative semantic critique caused the approved Luna mapping to omit it. Improving that inference could recover coverage; the stored approved configuration has been preserved. ATO illustrates a different benefit: removing it leaves selected field values unchanged but removes provenance and cross-source support for 35 profiles. [Source-removal results](source-removal.json), [mapping review history](README.md#8-mapping-approvals).

## 6. Preserved evidence and reproduction

- **Terra baseline:** [original overview](../experiments/terra-baseline/outputs/README.md) and [archive manifest](../experiments/terra-baseline/manifest.json).
- **Initial Jev shortlist:** [preserved overview](../experiments/jev-luna-before-download-gate/README.md), audit and hashed files in the same archive directory.
- **Final Part 1:** [download-check report](part1-downloadable/REPORT.md), [ranked shortlist](shortlist.jsonl) and [all-50 audit](ai-audit/FULL_SHORTLIST_REPORT.md).
- **Structured comparison:** [comparison.json](comparison.json), including shortlist membership changes, snapshot equality and cost scopes.
- **Current presentation entry point:** [Results and evaluation](README.md).

The latest revision verified that observations, links, unlinked records, profiles, selected records and source-removal outputs retained their original hashes. The existing frozen database demo predates this Part 1 revision; use the current output files for the refreshed shortlist and audit.
