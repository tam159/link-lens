# Current experiment costs

Only `jev-luna-v1` is included; earlier Terra receipts remain archived.

Measured subtotal: **$0.26116034**, covering **275/292 calls**. Unpriced calls: 17. All six sources are approved and the pipeline is complete; missing usage still prevents a complete cost total.

| Stage/run | Calls | Priced | Estimated USD |
|---|---:|---:|---:|
| employment-provider-locations-and-contacts (052e2d92-1bc2-4ba4-b542-8494e0f03cf0) | 6 | 4 | 0.00960330 |
| asic-afs-licensee (23fca114-0f59-4df6-9e5b-ec0be3971727) | 6 | 6 | 0.02739530 |
| corporate-transparency (28fb2b8c-85e9-4732-9e53-d38066fa9bf6) | 2 | 2 | 0.00481080 |
| acnc-register (2ea0c664-13ab-4fe5-aba3-e19dbedecfde) | 2 | 2 | 0.01366130 |
| asic-afs-licensee (3fc655c5-d7eb-4132-bbb8-d3175e5d731b) | 5 | 4 | 0.01551230 |
| asic-afs-licensee (42e0a217-dc32-4078-8309-65098f5a831b) | 4 | 4 | 0.02172090 |
| connectivity-test (4aff62a3-b3f4-4f85-ac91-4af6c53743e9) | 1 | 1 | 0.00007560 |
| asic-afs-licensee (4eb70b95-c3b4-4619-b928-3e928167a63b) | 5 | 2 | 0.00998825 |
| asic-business-names (5d4dac7c-3b4d-4dee-8bc1-40c1f30dbdb8) | 7 | 7 | 0.02364390 |
| asic-companies (6013401c-e43c-4d93-a436-cbbe998e57bc) | 4 | 4 | 0.01695540 |
| acnc-register (6429eee3-39c1-45cf-b38c-06df2715fba5) | 5 | 4 | 0.02685645 |
| employment-provider-locations-and-contacts (7c816605-4497-4040-b96d-a8f93580517b) | 4 | 2 | 0.00609505 |
| asic-business-names (8acd7625-6835-4790-af94-aaa88cec9c03) | 5 | 3 | 0.00761275 |
| corporate-transparency (dc73418c-f7a4-413d-9639-8d63f48bbb27) | 6 | 3 | 0.00492275 |
| catalogue triage (discovery-jev-luna-v1) | 213 | 213 | 0.00799604 |
| asic-afs-licensee (e3431ab3-0276-423b-9c18-36afa2eaec55) | 5 | 5 | 0.02189245 |
| asic-companies (e619a3e2-1ac5-4c56-8f9a-64ef0bd80918) | 6 | 4 | 0.01476550 |
| acnc-register (f2810464-ad88-4896-9022-984951fc7d58) | 6 | 5 | 0.02765230 |

Rates are stored together in [pricing_rates.json](../src/link_lens/pricing_rates.json): Jev input $0.042/M, output $0/M; Luna standard short-context input $0.20/M, cache read $0.02/M, cache write $0.25/M, output $1.20/M. OpenAI rates are the agreed Azure estimate. Jev response-reported cost is retained alongside the published-rate calculation.

No output-token charge for Jev does not mean zero output tokens. Failures with missing usage remain unpriced. No per-record LLM calls occur in extraction/linking/profile assembly; infrastructure costs are outside this estimate. Assistant development and audit tokens are not available in the application ledger.

See [per-call calculations](cost-summary.json), [usage ledger](cost-usage.json), and [comparison](COMPARISON.md).
