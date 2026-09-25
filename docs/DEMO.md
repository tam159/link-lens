# Demonstrate the submitted approach

The final submission is `jev-gpt6-luna-ontology-v1`, promoted by the user on 25 September 2026. [Live OKF viewer](https://tam159.github.io/link-lens/), [saved results](../outputs/README.md), [exact IDs](../outputs/submission-manifest.json).

## 1. Explain the result — about one minute

Show 50 shortlisted datasets, six approved mappings and 60 profiles. Explain: Jev ranks catalogue evidence; GPT-6 Luna proposes ontology additions and mappings; deterministic code validates contracts and extracts approved observations; hybrid retrieval and Jev assess identity under evidence constraints. The bounded enhancement added no links in this run. Human evidence evaluation remains pending.

The ontology has 59 concepts; 43 additions emit claims and 24 contribute to profiles. Show the short flexible-ontology note in [README](../README.md), then a scoped licence group. More fields do not imply more valid identity links.

## 2. Show the reviewed mappings

Open [Agent Inbox](http://localhost:3000) after [local startup](../README.md#run-locally), or use the [saved approval manifest](../outputs/approval-manifest.json). The six reviews are completed; an empty Interrupted tab is expected. Accept approves an exact config and ontology hash; Respond requests a new proposal; Ignore defers extraction. Do not resend acceptance just for a demonstration.

![Historical Inbox queue](images/agent-inbox-all-reviews.png)

*Historical screenshot of an earlier queue, not the current completion state.*

![Historical mapping review](images/agent-inbox-review-details.png)

*Earlier ACNC proposal. Current reviewed configurations and hashes are in `outputs/mappings/`; the screenshot's version is historical.*

## 3. Follow a profile back to evidence

Open [the submitted viewer](../outputs/okf/viewer.html), choose **Business Profile**, select a company and inspect source citations, alternatives, observation locators and scoped registration/licence groups. Source/field scores are uncalibrated; source publication times are not necessarily change times.

![Historical profile layout](images/okf-business-profile.png)

*Historical Terra profile view illustrating navigation. Use the current viewer for the 60 submitted profiles.*

Choose **Public Data Source** and inspect ASIC AFS: it now contributes evidence to 29 profiles through approved mixed ABN/ACN handling and scoped licence facts. Companies, AFS, ACNC and ATO contribute. Business names and employment locations emit observations but remain outside linked profiles.

![Historical source layout](images/okf-data-source.png)

*Historical source screenshot; its counts and connections differ from the promoted cohort. Graph edges are evidence citations, not additional identity links.*

## 4. Explain limitations and evaluation

Show the [concept coverage](../outputs/concept-coverage.json), [remaining omissions](../outputs/ontology-coverage.json) and [comparison](../outputs/COMPARISON.md). Monetary measures remain unmapped. Enhancement assessed 500 pairs; 81,745 remain pending at that limit. It produced two locality-conflict annotations and no extra links or selected-value changes. The shared conservative budget charge is $0.643798072, including five unknown-usage attempts; the priced subtotal is $0.432441472.

Open the [20-dataset](../outputs/triage-review.html) and [50-link](../outputs/link-review.html) human worksheets. They are separate from completed mapping approvals. No human accuracy result is claimed, and old AI labels are not reused. Enhanced source-removal membership effects may be incomplete because those counterfactuals use cached evidence only.

## Live seventh-source demo

A seventh source is future work for this promoted cohort. The earlier ACNC 2024 AIS preflight and commands are preserved in the [historical demo](../experiments/jev-luna-v1-submission/docs/DEMO.md#live-seventh-source-demo); its three overlap examples belong to the old 52-profile cohort. Recheck source availability, identifier overlap and publisher evidence before creating a new run. Never carry its old overlap count into the current submission.

Use [the onboarding procedure](../.agents/skills/link-lens-onboarding/SKILL.md), the active ontology and a separate experiment/output directory. A new source needs agent-generated mapping, final validation and human approval before its contribution can be measured.

## Optional: restore a frozen demo

The saved HTML/Markdown, mappings, profiles and gzip evidence require no database. A fresh checkout does not recreate live threads. Historical `demo/jev-luna-v1.zip` and `demo/frozen.zip` restore earlier evidence only; see the [historical restore instructions](../experiments/jev-luna-v1-submission/docs/DEMO.md#optional-restore-a-frozen-demo). They are not archives of this final submission.

Archive compatibility is tested with isolated fixtures. A live restore of the full expanded experiment has not been demonstrated; the current full database may exceed the demo loader's 750 MB uncompressed bound. Preserve live PostgreSQL and `artifacts/`; use a separate empty database for any restore and never delete runtime volumes as routine cleanup.

Large JSONL files in the submitted evidence are compressed losslessly. Use `gzip -dc outputs/observations.jsonl.gz` or Python `gzip.open(..., 'rt')`; verify the uncompressed hash against [the compression manifest](../outputs/compressed-artifacts.json).
