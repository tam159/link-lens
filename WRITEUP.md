# Link Lens — flexible ontology and evidence-backed business profiles

Link Lens turns an unfamiliar public dataset into a mapping that a person reviews. The final approach uses **Jev for discovery, GPT-6 Luna for ontology evolution and onboarding, deterministic extraction, and bounded hybrid enhancement**. PostgreSQL and immutable artifacts preserve decisions and provenance; OKF presents the saved evidence. [Live viewer](https://tam159.github.io/link-lens/), [results](outputs/README.md).

## Approach and controls

Discovery combines Jev's relevance assessment with deterministic signals, then checks downloads and readers before selecting 50 datasets under a publisher cap. Availability is not semantic correctness, and evaluation labels never influence ranking. The fresh run retrieved 945 catalogue records and retained the same six source identities across four publishers.

**The ontology can expand without source-specific extraction code.** GPT-6 Luna examines frozen discovery rows, publisher documentation, existing definitions and unmapped fields. It proposes missed existing mappings or reusable additions; consolidation removes duplication, and a separate semantic critique checks meaning and ownership. Deterministic code verifies evidence quotations, supported types, additive compatibility, dependencies and scope. Valid additions activate experimentally; human mapping approval and submission promotion are separate decisions. Validation and held-out final rows are excluded from proposals.

The promoted ontology contains 59 concepts, including 44 additions to immutable v0.1. Each declares meaning, type, subject scope, cardinality and required companions. New runs, approvals, observations and caches pin its content hash. Scoped locations, contacts, licences, registrations and financial periods stay in separate groups: a licence date cannot become a company date, nor can one reporting year win over another. Decimal values remain exact; missing amounts never become zero.

One LangGraph onboarding agent investigates readers, optionally explores discovery data in a restricted sandbox, proposes declarative mappings, receives validation feedback and a separate critique, then passes an unused final slice before review. Human acceptance binds the exact config and ontology hash. Revisions require fresh approval; failed final tests do not permit tuning against exposed rows. The shared engine executes typed operations and indicator-to-category collections; generated Python is never the extractor.

Identity begins with validated ABN/ACN and compatible subject roles. Hybrid enhancement retrieves candidates using fuzzy names and embeddings, asks Jev about identity and corroboration, then applies deterministic conflict and cluster constraints. Names alone, service locations and scoped claims cannot establish company identity. Jev can assess equivalent field representations; Luna annotates unresolved conflicts with source citations. Original values, alternatives and provenance remain visible. Scores are uncalibrated.

## Measured outcome

All six agent-generated mappings were approved. From 6,000 selected source rows, the pipeline emitted **79,840 observation occurrences, representing 79,113 unique claims**, and produced **61 links and 60 profiles**. The 727 repeated claims are identical licence conditions. Selection deliberately favours identifier overlap from bounded pools; these are not population coverage estimates.

| Source | Profiles receiving evidence | Main outcome or limitation |
|---|---:|---|
| ASIC Companies | 38 | Current names, validated identifiers and scoped registration metadata |
| ASIC AFS | 29 | Corrected mixed ABN/ACN handling; licence-specific details preserved |
| ACNC | 13 | Charity categories, purposes and beneficiaries; ambiguous names remain unmapped |
| Corporate transparency | 41 | Identifiers and periods; amounts lack accepted amount/currency semantics |
| Business names | 0 | Registration facts do not establish holder identity |
| Employment providers | 0 | Scoped contacts and coordinates do not establish legal ownership |

Counts overlap. **43 added concepts emit observations; 24 contribute to linked profiles.** This is stronger evidence of utility than simply reducing unmapped fields. Hybrid enhancement assessed 500 pairs and added no links or selected-value changes. It produced two locality-conflict annotations; 81,745 pairs remain unassessed at the pair limit and two review candidates remain unreviewed. Source-removal reports distinguish deterministic deletion effects from incomplete cache-only enhanced counterfactuals.

The viewer contains 1,676 documents and 3,220 evidence edges with zero broken internal links. Edges are document citations, not extra identity links. [Counts and provenance](outputs/README.md), [old versus new](outputs/COMPARISON.md).

## Evaluation, cost and limits

Mapping approval and user promotion are complete. **Human evidence evaluation remains pending**: 20 shortlisted datasets and 50 links have separate worksheets. Enhancement evaluation separates development and held-out entity groups and samples outside retrieval. Historical AI audits are not labels for this new evidence. No human precision, recall or false-positive result is claimed.

The shared $10 estimated API budget covers discovery, ontology, onboarding, embeddings and enhancement, including retries and interrupted attempts. Reservations use a database lock; unknown usage retains its charge. **The conservative charge is $0.643798072; 997 of 1,002 attempts have priced usage totalling $0.432441472.** Five unknown-usage attempts prevent a complete billed total. Provider list rates approximate deployment cost; infrastructure and development activity are outside the application ledger. [Cost evidence](outputs/COSTS.md).

Four snapshots, the model, ontology, mappings and cohort changed from the previous submission. Its 52 profiles versus today's 60 is not a controlled model or ontology benchmark. Financial enrichment remains incomplete, and the full new database archive has not been live-restored. Saved exports require no credentials; fresh runtime inference requires provider access and new human mapping decisions.

At 500 sources, acquisition/schema drift and review throughput are likely to dominate before matching quality alone. Next work: evidence-reviewed evaluation and prioritised pending pairs; schema-change monitoring and reusable ontology refinement; bulk writes, incremental recomputation and model-upgrade shadow comparisons. Old links, ontologies and approvals remain versioned for replay and rollback.
