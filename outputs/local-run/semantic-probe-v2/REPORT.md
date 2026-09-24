# Hybrid policy v2 development probe

Baseline: `fa5523f0-7d5a-41d2-af42-59e6362e3046` (`jev-luna-v1`).
This targeted development probe is not a human-labelled benchmark or a precision estimate.
It selected 6 exact normalized-name pairs, 8 fuzzy pairs and 8 service-provider pairs,
excluding matching identifiers and identifier conflicts. The probe questions explored
identity and evidence routes; these are distinct from the final production prompt.

Of 22 successful Jev calls, 18 returned insufficient evidence, 3 different entities,
and 1 same entity with a score of 0.51. None met the 0.98 admission floor.
Estimated cost: $0.005517834, with pricing coverage of 22/22 calls. This is not an invoice.
See `manifest.json`, `decisions.json` and `report.json` for selection and response provenance.

A subsequent cache-only retrieval check reused all 5,644 available vectors with zero
paid calls. At the v2 retrieval floors it produced 373,009 pairs: 371,560 embedding-only,
991 fuzzy-only and 458 from both methods. No retrieved pair had a potential bilateral
admission route. See `cache-validation.json`. The read-only lexical preflight likewise
found no potential admission routes. These checks do not establish population recall.

The evidence therefore supports exposing review candidates and operational visibility;
it does not demonstrate additional correct links or profiles. No full v2 paid enhancement
or held-out human evaluation was run for this implementation.
