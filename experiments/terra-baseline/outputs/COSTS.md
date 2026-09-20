# Published-rate cost estimate

**Recalculated 19 September 2026: $2.0150253 (about $2.02) for 50 measurable calls out of 52.** We use OpenAI prices as the agreed approximation for deployment costs. Two Employment calls lack usage and are excluded. Includes failed/superseded attempts, connectivity and seventh-source onboarding. No new model calls were made for this recalculation.

## Saved prices

Source: [OpenAI API pricing](https://developers.openai.com/api/docs/pricing), checked 19 September 2026. USD per million tokens, **Standard, short context**:

| Model | Ordinary input | Cache read | Cache write | Output |
|---|---:|---:|---:|---:|
| gpt-5.6-sol | $4.00 | $0.40 | $5.00 | $20.00 |
| gpt-5.6-terra | $2.00 | $0.20 | $2.50 | $12.00 |
| gpt-5.6-luna | $0.20 | $0.02 | $0.25 | $1.20 |

[Machine-readable pricing snapshot](../src/link_lens/pricing_rates.json) also stores the published long-context, Batch, Flex and Fast rates. Sol's promotional pricing is listed through at least 21 November 2026. OpenAI list prices are our working cost assumption. Regional uplift, taxes and negotiated adjustments are excluded.

## Calculation

All 52 saved responses identify `gpt-5.6-terra-2026-07-09` and service tier `default`. We use **Standard short-context pricing as the agreed estimation basis**. The 50 measurable calls have at most 20,278 input tokens each. The calculator is deliberately bounded to that verified workload; larger calls remain unpriced rather than guessing a context tier.

[Prompt-caching documentation](https://developers.openai.com/api/docs/guides/prompt-caching) specifies that cache-write pricing replaces the normal input rate for those tokens; it is not an additional charge. Saved LangChain usage separates `cache_read` and `cache_creation` within input tokens.

| Token category | Recorded tokens | Applied rate / million | Estimated USD |
|---|---:|---:|---:|
| Ordinary input | 6,607 | $2.00 | $0.0132140 |
| Cache reads | 17,899 | $0.20 | $0.0035798 |
| Cache writes | 519,347 | $2.50 | $1.2983675 |
| Output | 58,322 | $12.00 | $0.6998640 |
| **Measured subtotal** | **602,175** | | **$2.0150253** |

Formula: `((input - cache_read - cache_creation) × input_rate + cache_read × read_rate + cache_creation × write_rate + output × output_rate) / 1,000,000`.

Input categories sum to **543,853 tokens**. Reasoning tokens, if present, are already within output and are not added again. Missing cache breakdowns or usage remain unpriced. Rates are applied per call, without rounding individual calls to cents.

## Per-source subtotal, including retries

| Source | Measured subtotal |
|---|---:|
| acnc-register | $0.303299 |
| asic-afs-licensee | $0.420656 |
| asic-business-names | $0.185992 |
| asic-companies | $0.645941 |
| asic-credit-licensee | $0.158019 |
| connectivity-test | $0.000756 |
| corporate-transparency | $0.146381 |
| employment-provider-locations-and-contacts | $0.153981 |

Employment's subtotal is incomplete because two calls are unpriced. A successful-run-only onboarding example: Credit Licensees costs **$0.131898** for its three-call successful run; including its earlier failed run gives **$0.158019**. This is a one-time onboarding estimate. Deterministic per-record processing makes **zero LLM calls and costs $0 in LLM fees**. CPU/storage costs are outside this model-cost estimate.

**Budget conclusion:** estimated cost for priced calls is **$2.02, below the $10 target**. Two calls with missing usage are excluded, so this does not cover all 52 calls. Coding-assistant work, the AI evidence audit and infrastructure are outside this estimate.

## Reproduce and inspect

```sh
# Uses the saved usage ledger; no database or model credentials needed.
uv run python scripts/recalculate_costs.py
# Refresh the ledger from the application database, then recalculate.
uv run python scripts/recalculate_costs.py --refresh-ledger
```

[Cost summary](cost-summary.json) contains per-call and per-run estimates and the rate snapshot. [Usage ledger](cost-usage.json) contains only accounting metadata and references to original response artifacts. [Measurement summary](measurement-summary.json) exposes the result under `published_rate_estimate`. Original receipt pricing fields are preserved; this retrospective estimate does not alter historical decisions or enable a new live budget policy.
