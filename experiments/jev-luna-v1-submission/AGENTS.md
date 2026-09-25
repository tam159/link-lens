# Working on Link Lens

## Purpose and starting points

Link Lens onboards unfamiliar public business datasets, produces agent-generated declarative mappings for human approval, then deterministically extracts observations, links entities and builds evidence-backed profiles. This is a locally runnable assignment submission with preserved experiments, not a production hosted service.

Read only the documentation relevant to your task:

| File | Owns |
|---|---|
| [README.md](README.md) | Setup, environment variables, commands, architecture and workflow diagrams |
| [WRITEUP.md](WRITEUP.md) | Reviewer-facing explanation, decisions, results and limitations |
| [docs/DEMO.md](docs/DEMO.md) | Illustrated presentation, seventh-source run and optional frozen restore |
| [docs/ENGINEERING.md](docs/ENGINEERING.md) | Implementation details, verification, operations and recovery |
| [outputs/README.md](outputs/README.md) | Current submission results, approvals and evaluation status |
| [outputs/COMPARISON.md](outputs/COMPARISON.md) | Previous versus current approach and download-gate comparison |

Resolve current experiment, discovery revision, run IDs and batch IDs from settings and stored/exported metadata. Do not assume an ID or count in an old document is still current. `store.current_discovery()` resolves the active discovery revision.

## Code map

Application code is in `src/link_lens/`:

| Modules | Responsibility |
|---|---|
| `cli.py`, `api.py`, `settings.py` | CLI, application routes and environment settings |
| `ingestion.py`, `triage.py`, `downloadability.py` | CKAN discovery, Jev relevance ranking, download/reader preflight and registration |
| `agent.py`, `llm.py` | Bounded LangGraph onboarding, model calls, validation, critique and Inbox interrupts |
| `contracts.py`, `readers.py`, `extraction.py` | Typed mapping contract, shared readers and declarative extraction |
| `resolution.py`, `profiles.py`, `pipeline.py` | Deterministic linking, profile decisions and assembly |
| `store.py`, `frozen.py` | PostgreSQL evidence, content-addressed artifacts and archive/restore |
| `evaluation.py`, `review_ui.py` | Separate human/AI evaluation records and review worksheets |
| `measurements.py`, `pricing.py`, `pricing_rates.json` | Usage, pricing basis and cost calculations |
| `exports.py`, `_vendor/okf/` | Generated JSONL/CSV/OKF and viewer; retain vendor attribution |
| `sandbox.py`, `runtime_compat.py` | Restricted Python execution and pinned runtime compatibility fixes |

`migrations/` contains Alembic migrations; `tests/` contains deterministic tests and explicitly gated integrations. `compose.yaml`, `deploy/` and `langgraph.json` define local services. Read scripts before executing them: several `scripts/` files have top-level side effects, fixed experiment IDs or authored audit judgments. They are not all reusable library functions.

## Development commands

Run from the repository root. Use Python 3.13 and `uv`; `.venv` is the virtual environment and `.env` is configuration. Add dependencies with `uv add` and update `uv.lock` intentionally.

```sh
uv sync --frozen
uv run link-lens --help
uv run pytest -q
uv run ruff check src/link_lens tests --exclude _vendor --select F
```

Run relevant tests first and broader checks when the change warrants them. Deterministic tests use isolated fixtures; live model and Docker integrations are separate. Documentation-only edits need link/command consistency checks, not a paid pipeline rerun. Consult `tests/test_sandbox_integration.py` before enabling `RUN_DOCKER_TESTS=1`.

Service startup and provider setup live in README. Default local ports: Inbox 3000, backend 2024, PostgreSQL 5439, sandbox controller 8091. The graph ID is `onboard`. The development server supplies the graph checkpointer; PostgreSQL stores application evidence separately. Frozen application archives do not recreate LangGraph threads/checkpoints.

## Contracts to preserve

- The submitted approach uses Jev for Part 1 and `gpt-5.6-luna` for Part 2. Model names are configurable and provider access is deployment-specific. Do not silently change models during a comparison.
- Part 1 combines deterministic and Jev relevance signals with download/readability checks. A successful download is evidence of availability, not proof of business relevance. Audit labels must not influence the frozen ranking being evaluated.
- One onboarding graph investigates and revises mappings. Exploration Python runs only through the sandbox. Approved extraction uses the shared declarative engine, never generated Python or unrestricted expressions embedded in configs.
- Keep discovery, validation feedback and held-out final records separate. Freeze reader/partition decisions before inference; never expose reserved records to exploration. A failed final test does not authorise repeated tuning against that same test set.
- Accept approves the exact stored config hash; Respond requests revision; Ignore defers. Config changes require fresh approval. Preserve reviewer, feedback, timestamps and idempotent resume/extraction. Never substitute AI acceptance for the user's mapping review.
- Keep bounded calls, tokens, execution time, mapping versions and costs. Preserve failed/retried calls and explicit recovery lineage; do not reset budgets invisibly.
- Only the trusted sandbox controller has Docker-daemon access. Execution containers receive no network, credentials, Docker socket or repository mount. Preserve resource limits, bounded outputs and cleanup on failure. This is local-development isolation, not a production multi-tenant security claim.
- Link on validated identifiers with compatible subject roles. Never derive ACN from an ABN suffix, merge on name alone, or ignore conflicting identifiers/ownership ambiguity. Preserve source records and versioned membership decisions.
- Preserve raw values, exact source locators, timestamp policy, separate confidence dimensions, alternatives and cohesive address bundles. Uncalibrated scores are rule/model scores, not measured probabilities. Missing defensible timestamps require quarantine rather than invented dates.
- PostgreSQL and immutable artifacts are authoritative; OKF is a generated view. Serve artifacts by registered ID, not arbitrary filesystem paths. Version schema changes with Alembic.
- AI audits, human mapping approvals and human evidence evaluations are different activities. Unknown/unreviewed labels are not correct answers. An AI audit cannot complete the assignment's human evaluation requirement.
- Include all model attempts in usage. Missing usage is unknown, not zero. State estimated pricing basis and priced-call coverage; do not present a partial subtotal as the complete bill. Per-record processing is deterministic unless explicitly changed.

## Outputs, secrets and scope

- `outputs/` holds the current submission. Export experimental reruns to a distinct directory such as `outputs/local-run/`; replace submission artifacts only when the task calls for it.
- `experiments/` preserves earlier evidence for comparison. Do not rewrite a baseline to match new code or metrics. Keep IDs, hashes, snapshots and measurement provenance traceable.
- `artifacts/`, database volumes and `.langgraph_api/` are runtime state. Do not delete them or run `docker compose down -v` as routine cleanup. Restore archives only into an appropriate empty database.
- `local/` and `walkthrough/` are ignored personal/educational material. Do not promote their hand-authored mappings into agent-generated submission results or expose private notes in public docs.
- `.env` and `.codex/` remain ignored. Never print credentials, copy secrets into reports, or overwrite an existing `.env`. Document configuration through `.env.example` with placeholders. Keep `AGENTS.md`, repository skills and workspace files eligible for version control.
- Check a helper script's input/output scope before running it. In particular, ensure reporting/worksheet scripts use the active discovery revision rather than an original `discovery-<experiment>` ID. Existing `record_*audit.py` judgments apply to their original evidence, not new shortlists or batches.
- Respect the requested scope: a Part 1 rerun does not require re-onboarding six sources; a cost recalculation does not require new inference; a documentation update does not require starting services.

## Documentation and completion

Keep documentation in English and distinguish implemented, measured, assumed and future work. Update the owning document and link to detail instead of duplicating entire sections. Architecture is now in root README; do not recreate `docs/ARCHITECTURE.md`. The demo is consolidated in `docs/DEMO.md`; results/reviews/evaluation instructions are consolidated in `outputs/README.md`.

Generated exports and curated explanations have different owners: report scripts can refresh machine data and generated status files, but manually check README, WRITEUP, comparison and demo claims afterward. Preserve screenshot dates and historical context. Verify relative links and Mermaid syntax when editing docs.

For a completed coding task, report what changed, what checks ran and any remaining limitation. Do not claim a live run, approval, human evaluation or measured cost without its evidence.

## Reusable procedures

- [Source onboarding and review](.agents/skills/link-lens-onboarding/SKILL.md): a new source, seventh-source demonstration, or interrupted onboarding recovery.
- [Evidence refresh and evaluation](.agents/skills/link-lens-evidence-refresh/SKILL.md): scoped reruns, audits, measurements and comparisons.

These are repository skills in Codex's `.agents/skills` discovery location. Other coding tools can read the linked instructions directly.

## GitHub identity

When using `gh` in this project under `/Users/may/tech/`, check `gh api user --jq .login` and switch with `gh auth switch --user tam159` if needed. Do not publish or push merely because local implementation is complete.
