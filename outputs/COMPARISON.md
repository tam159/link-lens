# Previous submission versus the final approach

The user promoted `jev-gpt6-luna-ontology-v1` on 25 September 2026. Earlier results are preserved under [jev-luna-v1-submission](../experiments/jev-luna-v1-submission/outputs/README.md), with original commit and file hashes. The earlier Terra comparison remains available there and under [terra-baseline](../experiments/jev-luna-v1-submission/outputs/COMPARISON.md).

| Dimension | Previous Jev + GPT-5.6 Luna submission | Final expanded-ontology submission |
|---|---|---|
| Discovery | 945 records, 50 shortlisted, download-gated revision | Fresh Jev discovery; 945 records, 50 shortlisted; same six source identities retained |
| Ontology | 15 canonical targets | 59 concepts: immutable parent + 44 validated additions |
| Mapping generation | GPT-5.6 Luna | GPT-6 Luna, with separate ontology proposal/consolidation/critique |
| Mapped source columns | 27 | 110; 21 explicit unmapped columns |
| Selected rows | 6,000 | 6,000, with a newly selected overlap cohort |
| Observation occurrences / unique claims | 20,838 / 20,838 | 79,840 / 79,113 |
| Proposed links / profiles | 52 / 52 | 61 / 60 |
| Sources contributing to linked profiles | 3 | 4 |
| New concepts contributing to profiles | — | 24 of 44 accepted additions |
| Enhancement | Exact identifiers and deterministic profiles | Same exact baseline, plus hybrid retrieval, Jev decisions and Luna conflict annotations |
| Priced subtotal / coverage | $0.261160344; 275/292 calls | $0.432441472; 997/1,002 attempts |
| Shared conservative charge | No experiment-wide reservation ledger | $0.643798072 / $10, including five unknown-usage reservations |
| Human evidence evaluation | Pending | Pending; old AI labels not reused |

## What actually improved

AFS mixed ABN/ACN handling now supplies independently validated identifiers; its profile contribution increased from zero to 29. Scoped licence conditions and dates remain distinct from company facts. ACNC classifications, company registration metadata and reporting-period evidence contribute to profiles. New service-location/contact concepts emit evidence, but still do not establish legal ownership or produce linked employment-provider profiles. Business-name registrations likewise remain unlinked.

The new ontology emits 43 of its 44 additions; 24 additions appear in linked-profile evidence. The unused concept is `entity.operating_country`. Financial amount concepts were not released with adequate currency semantics; income and tax amounts remain unmapped. Fewer omissions alone is not success. [Per-concept evidence](concept-coverage.json), [per-source evidence](source-contributions.json).

## Isolating the enhancement effect

[New deterministic assembly](../experiments/jev-gpt6-luna-ontology-v1/baseline/ontology-coverage.json) and the final enhanced result use the same snapshots, mappings, selected rows and observations. Both have 60 profiles and 61 links. Enhancement added **zero links and zero selected-value changes**, plus two locality-conflict annotations and two unreviewed candidate records. It assessed 500 pairs; 81,745 remain pending at the pair limit. Retrieval coverage is not recall, and no human-verified accuracy improvement is claimed. [Detailed enhancement comparison](enhancement-comparison.json).

## Comparison limits

Four of six snapshots changed; corporate transparency and employment-provider bytes stayed identical. Model, ontology, mapping choices, snapshot and cohort changes therefore confound a causal comparison against the previous submission. Source contribution counts overlap. 727 repeated identical licence-condition observations are disclosed separately from unique claims. Old AI audits describe old populations; the current 20-dataset and 50-link worksheets remain unreviewed.

The [machine comparison](comparison.json) and [submission manifest](submission-manifest.json) bind counts to exact evidence. Recompute without inference:

```sh
uv run python scripts/report_ontology_experiment.py --root experiments/jev-gpt6-luna-ontology-v1
```
