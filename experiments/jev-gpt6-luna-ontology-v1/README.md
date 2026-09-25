# Ontology expansion experiment — preserved promotion evidence

**Promoted to the submission on 25 September 2026.** The final reviewer-facing files are in [outputs](../../outputs/README.md); this folder preserves the pre-promotion experiment and its limitations.

All six mappings were human-approved and extracted. The new deterministic assembly and bounded hybrid enhancement are exported separately. **60 profiles contain evidence for 24 new ontology concepts**, with 61 identifier-supported links. The original submission and submitted ontology remain preserved; experimental activation is not submission promotion.

Experiment: `jev-gpt6-luna-ontology-v1`. See the [run and batch manifest](manifest.json), [exact mapping approvals](approval-manifest.json), [baseline viewer](baseline/okf/viewer.html) and [enhanced viewer](enhanced/okf/viewer.html).

## What the ontology adds

The experimental registry contains **59 concepts: 15 preserved and 44 additions**. One proposal was rejected. Of the additions, **43 are mapped and emit observations; 24 contribute to linked profiles**. `entity.operating_country` remains unused because the approved ACNC mapping could not support its semantics safely. [Concept-level measurements](concept-coverage.json), [definitions](baseline/ontologies/4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227.json).

The six approved mappings cover **110 source columns**, versus 27 previously, with 21 explicit unmapped dispositions. Column coverage is not accuracy or ownership evidence. The [coverage report](baseline/ontology-coverage.json) retains every remaining omission reason.

| Source | Mapped columns, old → new | Unmapped | Observation occurrences | Profiles receiving evidence |
|---|---:|---:|---:|---:|
| acnc-register | 11 → 66 | 3 | 20,778 | 13 |
| asic-afs-licensee | 4 → 10 | 1 | 31,336 | 29 |
| asic-business-names | 1 → 7 | 1 | 4,269 | 0 |
| asic-companies | 6 → 12 | 3 | 9,890 | 38 |
| corporate-transparency | 1 → 2 | 7 | 1,993 | 41 |
| employment-provider-locations-and-contacts | 4 → 13 | 6 | 11,574 | 0 |

Source contributions overlap and must not be summed as unique businesses. AFS's corrected mixed ABN/ACN handling now supplies validated identity evidence and scoped licence details to 29 profiles. Business-name registrations and employment locations still contribute no linked profiles; their extracted claims remain available separately.

## Preserved submission, new assembly and enhancement

| Measurement | Preserved submission | New deterministic assembly | Hybrid + reconciliation |
|---|---:|---:|---:|
| Selected source rows | 6,000 | 6,000 | Same 6,000 |
| Observation occurrences | 20,838 | 79,840 | 79,840 |
| Unique observation IDs | 20,838 | 79,113 | 79,113 |
| Linked profiles | 52 | 60 | 60 |
| Proposed links | 52 | 61 | 61 |
| Sources contributing to profiles | 3 | 4 | 4 |
| New concepts contributing to profiles | — | 24 | 24 |

The new exports include 727 repeated, identical licence-condition observations from repeated source values; these are **not additional unique claims**. Duplicate IDs have identical contents. Scoped licences, registrations and reporting periods remain separate bundles. [Comparison](comparison.json), [verification](verification.json).

Fresh Jev discovery retrieved **945 catalogue records and shortlisted 50**. All six original source identities remain shortlisted. Four snapshots changed; corporate transparency and employment-provider bytes match the baseline. The model, ontology, mappings, source snapshots and chosen cohort differ from the preserved submission, so this is **not a causal measure of ontology improvement**. Baseline versus enhancement uses identical approved observations and selected rows.

## What enhancement actually did

Hybrid retrieval used `text-embedding-3-small`, Jev identity decisions and GPT-6 Luna conflict annotations. **It admitted no additional identity links.** It assessed 500 candidate pairs, blocked 87,328 incompatible pairs deterministically and left **81,745 pairs pending at the 500-new-pair limit**. The dollar budget was not exhausted. Two unreviewed candidate records remain in the [review queue](enhanced/review_candidates.jsonl); a review candidate is not a confirmed match.

Two source-grounded locality-conflict annotations were generated. No selected profile values changed after correcting the scoped-value comparison's JSON serialization issue. [Enhancement comparison and retrieval coverage](enhanced/comparison.json), [profiles](enhanced/profiles.jsonl).

The [baseline source-removal report](baseline/source-removal.json) measures deterministic deletion effects. Enhanced source-removal runs use cached judgments only and remain **incomplete** where changed evidence lacks a cached assessment; their unknown membership effects are not zero. [Enhanced source-removal report](enhanced/source-removal.json).

## Costs and run history

The shared conservative budget charge is **$0.643798072 / $10**, including five reservations with unknown usage. The priced-call subtotal is **$0.432441472 for 997 calls**. These are provider-based estimates, not a complete invoice; unknown usage is not zero. Interrupted attempts, retries, superseded onboarding runs and the earlier embedding serialization remain in the ledger. [Experiment-wide budget](budget.json), [all usage](cost-usage.json), [pricing coverage](cost-summary.json). The enhanced directory's cost report covers enhancement only.

Two ontology jobs were rejected and preserved. The third released individually accepted concepts and excluded rejected dependencies. The original Chat Completions preflight failed; the Responses preflight succeeded without substituting models. Linked onboarding recoveries retained frozen partitions and cost history. [Proposal evidence](baseline/ontology-proposals/), [run lineage](manifest.json).

During enhancement, scoped observations were removed from the identity judge's input. Ontology hashes remain in cache keys but are excluded from embedding text. Old vectors and attempts were retained. The final reporting replay reused cached decisions with new identity calls disabled.

## Remaining limits and human evaluation

- Financial amounts remain unmapped: the evidence and accepted definitions did not establish suitable amount/currency semantics. Exact decimals and missing-value handling are implemented and tested, but financial enrichment is not demonstrated.
- ACNC legal names, ambiguous alternate names and overseas-country semantics remain deliberately unmapped where the source documentation does not support the target assertion.
- Business-name registrations do not establish holder identity. Employment locations have no ABN/ACN or independent ownership evidence sufficient for the linking policy.
- Mapping approval is complete. Human evidence evaluation is still pending: [20 shortlisted datasets](triage-review.html), [50 baseline links](baseline/link-review.html) and [50 enhanced links](enhanced/link-review.html). These are separate from mapping review.
- The [enhancement worksheet](enhancement-review/worksheet.json.gz) separates development and held-out entity groups and includes outside-retrieval samples and explicit identifier-derived controls. Controls are not human ground truth. No human precision, recall or correctness improvement is claimed.
- Experimental ontology and result promotion remain separate human decisions. The user subsequently approved promotion; see the current submission manifest.

## Verification and reproduction

**105 tests passed; four gated integrations skipped.** Ruff F checks and whitespace checks passed. [Recorded checks](checks.json). Export checks verify ontology bindings, consistent observation IDs, profile citations, single-source-record scoped bundles and unchanged baseline/enhancement selections. Both viewers contain 1,676 documents and 3,220 edges with zero broken internal links. Archive compatibility and restoration were tested with isolated fixtures; this report does not claim a live restore of the entire new experiment.

Recompute export comparisons without model calls:

```sh
uv run python scripts/report_ontology_experiment.py --root experiments/jev-gpt6-luna-ontology-v1
```

For a future explicitly scoped continuation of pending enhancement, use the baseline batch in `manifest.json`, the same experiment/model environment and `enhance --max-pairs N`. Successful decisions are cached, and all new attempts remain subject to the shared $10 cap. Pending review labels must never be inferred from model output.
