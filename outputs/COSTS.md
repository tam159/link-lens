# Submission API costs

Experiment: `jev-gpt6-luna-ontology-v1`. All figures are USD provider-based estimates, not a complete invoice. [Budget ledger](budget.json), [per-attempt usage](cost-usage.json), [pricing snapshot and calculations](cost-summary.json).

| Measurement | Value |
|---|---:|
| Shared estimated cap | $10 |
| Conservative charged amount, including unknown-usage reservations | $0.643798072 |
| Attempts, including failures, retries and interrupted reservations | 1,002 |
| Attempts with priced usage | 997 |
| Unknown-usage attempts | 5 |
| Priced-call subtotal | $0.432441472 |
| Complete billed total | Unknown |

The shared PostgreSQL reservation ledger covers Jev discovery, GPT-6 Luna reader/mapping/ontology calls, embedding batches, Jev identity assessment and Luna conflict annotations. Reservations happen before calls under an advisory lock. Unknown usage retains a conservative charge; retries create new attempts and cannot reset the experiment budget. Reported costs and token estimates have distinct provenance.

The ledger retains the rejected ontology jobs, recovery runs, failed preflight, interrupted requests, and both embedding serializations. A final cache-only reporting replay made no new model calls. [Enhancement-only cost summary](enhancement-cost-summary.json) and [receipts](enhancement-cost-usage.json) are subsets of the experiment ledger, not additional costs.

GPT-6 Luna's recorded short-context rates per million tokens are $0.10 input, $0.01 cached input, $0.125 cache writes and $0.50 output; the recorded long-context tier is $0.20/$0.02/$0.25/$0.75. Reservations use conservative tiers; applicable provider adjustments are configurable. OpenAI list rates approximate this deployment's costs. Jev uses its saved OpenRouter pricing basis. The exact dated sources and cache/endpoint categories are in the pricing snapshot; no pricing refresh or new inference was performed for submission promotion.

Infrastructure, downloads, local computation and assistant development activity are outside the application's API ledger. The previous submission's $0.261160344 subtotal covered a different workload and incomplete usage; see the [comparison](COMPARISON.md), not a claimed percentage saving.
