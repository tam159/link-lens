"""Render saved AI judgments without generating or changing verdicts."""

import html
import json
from pathlib import Path
from link_lens import evaluation, measurements

root = Path("outputs/ai-audit")
triage = json.loads((root / "triage-audit.json").read_text())
links = json.loads((root / "links-audit.json").read_text())
sources = json.loads((root / "triage-evidence.json").read_text())
summary = [evaluation.ai_report(p["id"]) for p in [triage, links]]
full_summary_path = root / "full-triage-summary.json"
full_summary = (
    json.loads(full_summary_path.read_text()) if full_summary_path.exists() else None
)
if full_summary:
    summary.append(full_summary)
(root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
Path("outputs/measurement-summary.json").write_text(
    json.dumps(measurements.summary(), indent=2) + "\n"
)
intro = """# AI-assisted evidence audit — 18 September 2026

The assistant reviewed all 20 sampled datasets and all 50 proposed links. **This is an AI-assisted evidence audit, not the assignment's requested human hand-check.** Tam's original all-Yes files remain unchanged and unreviewed. Human precision and human triage false-positive rate remain unknown.

| Audit | Supported | Not supported | Unresolved |
|---|---:|---:|---:|
| Dataset relevance | 17 | 1 | 2 |
| Proposed links | 50 | 0 | 0 |

Dataset negative fraction among resolved AI judgments: **1/18 = 5.6%**. Across the full sample, 1/20 is negative and 2/20 are unresolved; the possible negative fraction is 5–15% if only those unresolved decisions change. This is not a statistical confidence interval or human-measured false-positive rate. The negative judgment uses explicit publisher metadata; its underlying download was unavailable. Two ACT datasets remain unresolved after HTTP 403 responses from both CSV and JSON endpoints.

Link support is **50/50 at the pipeline's 0.99 rule threshold**, not evidence of 100% population accuracy. These are all links from an intentionally selected 50-entity overlap cohort, randomly ordered with seed 159. They cover Companies, ACNC and AFS only. The 20 datasets were sampled from the 50-row shortlist with seed 159. No retuning of discovery or linking was done against these labels.

## What was checked

For every pair, the assistant compared the original source names, identifiers and subject fields, rather than simply accepting the generated profile or match score. Forty-nine pairs share an explicit ABN; one shares an explicit ACN with a missing ABN. A separately written checksum calculation checked the matched values. Names and roles were inspected individually, including the four name variants. This is a separate review pass, not independent real-world truth: the same source errors could affect both pipeline and audit. No live ABR check was performed for every company.

For triage, the criterion is existence of identifiable business/organisation information, not whether all rows are companies or the shared extractor can process the resource. Samples include named venues, corporate representatives, licensees embedded in adviser records, and companies named in attached telecom PDFs. Repeated telecom notices add little entity diversity. PDF-only business evidence is relevant to discovery but does not prove tabular extraction readiness. Raw samples, full retrieved PDFs/XLSX files, source URLs, snapshot hashes and pair row locators are retained in the evidence artifacts.

## Useful interview examples

- **Link 35:** The Uniting Church trust association matches on explicit ACN `000022480`; the Companies ABN is `0`, a missing-value sentinel.
- **Link 24:** Northcott has the same explicit ABN in both sources, but that ABN's suffix differs from its company ACN. Never derive ACN from ABN.
- **Triage 20:** An adviser is a person; the separate licence-name and licence-ABN fields identify a company. They are not the same entity.
- **Triage 1:** A toilet map contains Zephyrs Cafe and Thargo Roadhouse, but does not establish their legal operators. Relevant does not mean safe to merge.
- **Triage 13:** The notice's metadata and spreadsheet disagree on the state of Epping. Preserve the disagreement rather than silently correcting it.

**Suggested answer:** “I used a separate assistant review of all 70 items, retained per-item evidence and separated those judgments from human evaluation. It supported 50 links and found 17 relevant datasets, one irrelevant dataset and two unavailable cases. I have not completed the requested human hand-check, so I do not claim human-measured precision. A stronger model is not ground truth.”

The assistant review's token cost and active time were not measured by the application's LangSmith/usage ledger. They are unknown and excluded from onboarding cost claims.

## Evidence files

- [Dataset judgments](triage-audit.json) and [raw dataset evidence](triage-evidence.json)
- [Link judgments](links-audit.json) and [raw source pairs](link-evidence.json)
- [PDF text and retry results](followup-evidence.json)
- [Machine-readable summary](summary.json)

Use `uv run link-lens import-ai-audit outputs/ai-audit/triage-audit.json` (and `links-audit.json`) to restore AI judgments. `import-labels` rejects these explicitly AI-tagged files. Actual human review is still needed if the submission must satisfy the hand-check requirement; merely accepting these conclusions without inspecting evidence would not supply that review.
"""
if full_summary:
    title, body = intro.split("\n", 1)
    intro = (
        title
        + "\n\nLatest: [full 50-dataset audit](FULL_SHORTLIST_REPORT.md): "
        + str(full_summary["supported"])
        + " relevant, "
        + str(full_summary["not_supported"])
        + " irrelevant, "
        + str(full_summary["unresolved"])
        + " unresolved. The original sample below is preserved; human evaluation remains incomplete.\n"
        + body
    )
(root / "REPORT.md").write_text(intro)
e = html.escape
parts = [
    '<!doctype html><html lang="en"><meta charset="utf-8"><title>AI-assisted evidence audit</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto;padding:0 20px;line-height:1.5}details{border:1px solid #ccc;border-radius:6px;padding:12px;margin:8px 0}summary{cursor:pointer;font-weight:600}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f5f5;padding:12px}a{color:#1659ac}.note{padding:15px;background:#fff4d1}</style><h1>AI-assisted evidence audit</h1><p class="note">Not a human hand-check. Human evaluation remains incomplete. Original unreviewed responses are preserved.</p><p><b>Links:</b> 50 supported / 50. <b>Datasets:</b> 17 relevant, 1 irrelevant, 2 unresolved. These are assistant judgments, not measured human precision.</p><p>Open the <a href="REPORT.md">method, limitations and interview summary</a>. Expand an item for its reasoning and exact evidence references.</p>'
]
for packet in [triage, links]:
    parts.append("<h2>" + e(packet["kind"]) + "</h2>")
    for n, row in enumerate(packet["items"], 1):
        title = (
            sources[n - 1]["title"]
            if packet["kind"] == "triage"
            else row["evidence"].split(";")[0]
        )
        parts.append(
            f"<details><summary>{n}. {e(row['verdict'].upper())} — {e(title)}</summary><p>{e(row['evidence'])}</p><pre>{e(json.dumps(row['evidence_refs'], indent=2))}</pre></details>"
        )
if full_summary:
    parts.insert(
        1,
        '<p>Latest: <a href="full-shortlist-report.html">full 50-dataset audit</a>. Original sample and link review below are preserved.</p>',
    )
parts.append("</html>")
(root / "report.html").write_text("\n".join(parts))
