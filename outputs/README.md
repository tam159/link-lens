# Submission results and evaluation

**Promoted 25 September 2026 by the user.** Final approach: Jev discovery, **GPT-6 Luna ontology evolution and onboarding**, one deterministic extraction engine, then bounded hybrid retrieval and evidence-preserving reconciliation. Experiment: `jev-gpt6-luna-ontology-v1`. [Exact runs, snapshots, ontology and batch IDs](submission-manifest.json).

**[Open the submitted OKF viewer](https://tam159.github.io/link-lens/)** · [Local viewer](okf/viewer.html) · [Write-up](../WRITEUP.md) · [Comparison](COMPARISON.md).

All six generated mappings were human-approved. The submission contains **60 profiles, 61 proposed links and 79,840 observation occurrences (79,113 unique claims)**. Four sources contribute to profiles. The ontology has **59 concepts**, including 44 additions: 43 additions emit observations and 24 contribute to linked profiles. Mapping approval and submission promotion are complete; **human evidence evaluation remains pending**. No previous AI audit is presented as an audit of these new records.

## 1. Completeness against the assignment

| Part | Delivered | Remaining limit |
|---|---|---|
| Discovery | 945 catalogue records → 50 download-checked shortlisted datasets; all six source identities retained | Human 20-dataset relevance review pending |
| Inference | Six approved declarative configs bound to one ontology hash; frozen discovery/validation/final partitions | Some fields remain unsupported; monetary measures remain unmapped |
| Extraction | 6,000 selected rows, 1,000 per source; 79,840 observations | Sampled overlap cohort, not population coverage |
| Identification | 61 identifier-supported links and 5,879 unlinked records; hybrid retrieval and Jev assessment executed | No additional semantic links admitted; 81,745 candidate pairs pending at the 500-new-pair limit |
| Profiles | 60 profiles with confidence dimensions, provenance, alternatives and scoped groups | Source-removal membership counterfactuals remain incomplete when cached judgments are unavailable |
| Evaluation | Separate human worksheets and enhancement development/held-out samples | Precision, recall and false-positive rates remain unknown |
| Delivery | Code, versioned ontology, mappings, compressed evidence, write-up and OKF viewer | A live restore of this full experiment has not been demonstrated |

The overlap cohort is selected from bounded pools of up to 25,000 records per source and filled deterministically to 1,000 rows/source. 727 repeated licence-condition values produce identical repeated observation IDs; they are not extra unique claims. [Selection](selection.json), [checksums for compressed files](compressed-artifacts.json).

## 2. What was processed, and which sources contributed

| Approved source config | Observation occurrences | Profiles receiving evidence |
|---|---:|---:|
| [acnc-register](mappings/acnc-register.json) | 20,778 | 13 |
| [asic-afs-licensee](mappings/asic-afs-licensee.json) | 31,336 | 29 |
| [asic-business-names](mappings/asic-business-names.json) | 4,269 | 0 |
| [asic-companies](mappings/asic-companies.json) | 9,890 | 38 |
| [corporate-transparency](mappings/corporate-transparency.json) | 1,993 | 41 |
| [employment-provider-locations-and-contacts](mappings/employment-provider-locations-and-contacts.json) | 11,574 | 0 |

Contribution counts overlap. AFS now maps mixed ABN/ACN with independent checksum validation and keeps licence details scoped. Business names remain registration-scoped; employment contacts and coordinates remain site-scoped. Neither establishes sufficient holder identity for a linked profile in this cohort. ACNC classifications contribute; ambiguous legal-name and overseas-country assertions remain unmapped. ATO contributes identifiers and reporting periods, but not amounts.

[Source contribution data](source-contributions.json), [concept contribution data](concept-coverage.json), [mapping coverage and omission reasons](ontology-coverage.json).

The [deterministic removal report](source-removal-baseline.json) separates changed values, provenance and identity support. The [enhanced removal report](source-removal.json) explicitly marks incomplete counterfactuals; missing model decisions are not negative decisions or zero effects.

## 3. Evaluation progress and results

All six mapping reviews are complete. The [20-dataset worksheet](triage-review.html) and [50-link worksheet](link-review.html) are **unreviewed**. Their metrics remain unknown. The [enhancement worksheet](enhancement-review/worksheet.json.gz) includes 460 items, entity-separated development/held-out samples, outside-retrieval examples and separately identified identifier-derived controls. Controls are not human ground truth.

Hybrid retrieval embedded 5,996 of 6,000 records and retrieved 169,628 pairs. Jev assessed 500 pairs; deterministic incompatibility checks blocked 87,328. 555 pairs were deferred, including exact-identifier pairs handled by the baseline resolver; 81,745 remained pending at the pair limit, not the dollar limit. Two [review candidates](review_candidates.jsonl) remain unreviewed. Two GPT-6 Luna locality-conflict annotations were produced. **No new links or selected-value changes resulted.** [Enhancement measurements](enhancement-comparison.json).

Historical AI audits apply only to their [preserved earlier evidence](../experiments/jev-luna-v1-submission/outputs/README.md). They have not been transferred to this submission.

## 4. Ontology and approval boundary

[The promoted ontology](../firmable_ontology.yaml) defines meaning, type, scope, cardinality and required companions. GPT-6 Luna proposes and consolidates concepts from discovery evidence and documentation, then separately critiques semantics. Deterministic code checks evidence quotations, additive changes, types and dependencies before experimental activation. A person approves exact mapping hashes and explicitly promotes the result. Held-out rows never enter ontology proposals.

Immutable v0.1 remains packaged for legacy replay. New observations retain the ontology hash; licences, contacts, locations, registrations and financial periods remain cohesive groups. [Proposal evidence](ontology-proposals/), [ontology snapshot](ontologies/), [exact approvals](approval-manifest.json).

## 5. Costs and validation

The shared ledger charges **$0.643798072 of the $10 cap**, including five unknown-usage reservations. **997 of 1,002 attempts** have priced usage, giving a **$0.432441472 subtotal**; a complete invoice total is unknown. Failed, interrupted and superseded attempts remain included. [Cost scope and receipts](COSTS.md).

Deterministic tests, lint and export checks are recorded in [checks.json](checks.json). Both baseline and enhanced OKF exports have **1,676 documents, 3,220 citation edges and zero broken internal links**. These are document citations, not additional identity links. [Export verification](verification.json).

## 6. Files and reproduction

- [Observations](observations.jsonl.gz), [links](links.jsonl), [profiles](profiles.jsonl), [unlinked records](unlinked.jsonl).
- [Candidate decisions](candidate_decisions.jsonl.gz), [policy](policy.json), [pending embedding work](pending_inference.jsonl); pending identity work is in candidate decisions.
- [Baseline and enhanced experiment archive](../experiments/jev-gpt6-luna-ontology-v1/README.md), [previous submission](../experiments/jev-luna-v1-submission/outputs/README.md).

Large JSONL files use lossless gzip for GitHub portability. Read with `gzip.open(path, 'rt')` in Python or `gzip -dc FILE.jsonl.gz`; hashes of the uncompressed bytes are recorded. Database evidence and immutable blobs remain authoritative; these files do not populate a fresh database or restore workflow threads.

## 8. Mapping approvals

The [approval manifest](approval-manifest.json) records all six reviewed configs, ontology bindings and completed extraction. Mappings were generated by the onboarding agent, not manually edited for promotion. Promotion does not approve pending identity candidates or evaluation labels.

## 9. Complete the human evaluation

Review the [dataset](triage-review.html) and [link](link-review.html) evidence, fill genuine labels with reviewer and notes, then import the downloaded packets with `uv run link-lens import-labels PATH`. Inspect enhancement development and held-out sets separately; never tune against held-out labels. Unknown/unreviewed items remain excluded from correctness metrics.
