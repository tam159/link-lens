"""Persist the assistant's 19 September full-shortlist judgments, not an auto-labeler."""

import html
import json
from collections import Counter
from pathlib import Path
from link_lens import store, evaluation
from link_lens.contracts import content_hash

root = Path("outputs/ai-audit")
evidence = json.loads((root / "full-triage-evidence.json").read_text())
old = {
    r["item_id"]: r
    for r in json.loads((root / "triage-audit.json").read_text())["items"]
}
notes = {
    2: (
        "yes",
        "CSV row 2 identifies IPIB PTY LTD with AFS_LIC_ABN_ACN 85007186003, and row 3 IMC PACIFIC PTY LTD / 89099273846. Licence-holder records contain businesses; licence numbers, licence conditions and corporate identity remain separate.",
    ),
    3: (
        "yes",
        "CSV row 2 identifies RELI CAPITAL LTD, CRED_LIC_ABN_ACN 80005443292 and credit licence 219612. Explicit company and identifier evidence; status describes the licence and is not company registration status.",
    ),
    6: (
        "yes",
        "Rows 2-4 name Plumbing Gas and Solar, Bruce Ward Training and Elite Power Services, with BN_ABN values. Business names qualify for discovery but are not legal-entity names or proof of holder relationships; the approved production mapping conservatively leaves identity ownership unresolved.",
    ),
    7: (
        "yes",
        "The downloaded CSV is only a resource index, not business records. Retrieved ABN Lookup Bulk Extract documentation pages 3-4 explicitly defines entity-name, ABN, ACN and trading-name records in linked XML archives; page 6 supplies example ABNs. Strong documentary evidence of business content, but bulk XML rows were not downloaded/verified in this audit. XML/ZIP is outside the current extractor; apparent CSV readiness is misleading.",
    ),
    8: (
        "yes",
        "The sampled TSV includes SMSF_CAPACITY_FIRM_NAME GPP Audit Pty Limited with capacity Member (Partner) of Audit firm, and OZ Independent Audit Services Pty Ltd with Employee of Audit Firm. Main subjects are individual auditors, with repeated conditions. Firm names are identifiable businesses, but SMSF_PERSON_ABN must not be assigned to the employer firm.",
    ),
    9: (
        "unsure",
        "Publisher metadata describes licensee and business names, but sampled official-linked CloudFront downloads failed. No licence rows were inspected; plausible relevance remains unresolved, not a false positive.",
    ),
    11: (
        "yes",
        "2022-23 Report sheet row 2 names (UI!) THE URBAN INSTITUTE PTY LTD / 95608464535; row 3 @HOME ARCHITECTURE PTY LTD / 53666147271. Company-level R&D expenditure with income year. Information sheet precedes data; identifiers, periods and amended figures require explicit parsing.",
    ),
    12: (
        "yes",
        "Income tax details sheet row 2 names 1 MENDS STREET PTY LTD / ABN 94600082111. Other sheets include PRRT disclosures. Identifiable corporate tax subjects exist; tax reporting grain and group/ownership semantics are not established merely by a valid ABN, so this positive relevance label does not override the approved unknown-role mapping.",
    ),
    13: (
        "no",
        "Inspected CSV rows describe Nerang administration-building rooms/materials: FL/EQ No, Occurence ID, Floor ID, sample analysis and Asset Owner GCCC. The accompanying 55-page plan describes generic consultant/contractor roles rather than a business register. These are council asset/survey records, not identifiable business subjects. No business records established in inspected material; this is an audit judgment, not proof that every attachment lacks incidental organisation mentions.",
    ),
    14: (
        "yes",
        "CSV row 2 names U3A Inner North Incorporated with ABN 51214424410 and charity address/website fields. Explicit organisation records; withheld data and charity-versus-company distinctions still require mapping care.",
    ),
    15: (
        "unsure",
        "Publisher describes notifiable invoices for goods and services over $25,000. Both CSV and JSON export routes returned HTTP 403. Supplier business content is plausible, but no invoice rows were inspected, so relevance remains unresolved.",
    ),
    16: (
        "yes",
        "Sheet1 row 2 names Alberton Primary School / ABN 35954747085; row 3 Allansford and District Primary School / 37051817052. Identifiable ABN-bearing organisations qualify under the same broad organisation scope used for charities. Public schools are not automatically private companies; dates indicate a historical 2015 extract.",
    ),
    22: (
        "yes",
        "CSV rows 2-3 contain Sydney Missionary & Bible College / 11000047950 and Integricare Limited / 11000073870, with 2020 AIS reporting dates and websites. Organisation-year records, not anonymous statistics; group reports and synthetic group identifiers require exclusions or separate roles.",
    ),
    23: (
        "yes",
        "CSV rows 2-3 identify Sydney Missionary & Bible College / 11000047950 and Integricare Limited / 11000073870 in the 2022 AIS. Websites and submission dates are supplied. Relevant entity-year records; repeated annual extracts do not add independent publisher evidence.",
    ),
    26: (
        "no",
        "CSV headers and sampled rows are respondent survey answers: DURINT, DATE, demographics and Q1-Q21/QD fields, with free-text opinions about trust. The record subject is an anonymous respondent, not a named charity/business. Incidental mentions in opinions do not provide dependable business-profile claims. Negative for entity-bearing records, not a claim that no organisation name appears anywhere in the survey.",
    ),
    27: (
        "yes",
        "RSO Register sheet row 2 identifies Corporation (Company), OVER THE TOP ROOF RESTORATIONS PTY. LTD, ACN 090444714; row 3 $Uccess Pty Ltd / ACN 600137942. Explicit corporation identifiers and operator roles. Other operator types can be persons; RSO registration numbers are not ACNs.",
    ),
    29: (
        "yes",
        "Initial XLSX download exceeded the 30 MB collection cap; a bounded 80 MB retry succeeded. Sheet1 row 2 contains ABN 11000047950 and Charity_Name Sydney Missionary & Bible College; row 3 Integricare Limited / 11000073870. Organisation-level 2015 AIS records are directly observed. Historical data and explanatory-note year inconsistencies warrant temporal care.",
    ),
    30: (
        "unsure",
        "Both limousine and taxi transfer CSV URLs returned empty bodies. Metadata describes licence transfer prices and locations, which may be anonymous transactions; it does not establish whether individual licensees are identifiable. Unlike an explicitly aggregate monthly count dataset, this cannot be safely classified without rows.",
    ),
    32: (
        "yes",
        "Downloaded certificate CSV row 2 identifies Zauner Construction Pty Limited, ABN 21087732607; row 3 ELLIS AIR CONDITIONING PROPRIETARY LIMITED / 13004601790. Entity and trade names, certificate status, issue and expiry dates are explicit. Public Salesforce-hosted endpoint is outside the current government-domain ingestion allowlist, so relevance does not imply immediate onboarding compatibility.",
    ),
    33: (
        "yes",
        "2017-18 sheet row 2 contains Alchemy Resources Limited / ABN 17124444122 and allocation 206250; later sheets repeat companies by year. Identifiable applicant entities; introductory sheet and year-specific credit amounts must not be flattened into timeless attributes.",
    ),
    35: (
        "yes",
        "Attached notice page 1 dated 27 Oct 2021 explicitly names Lynham Networks Pty Ltd as the notifying company. Letterhead says Lightning Wholesale and prints ABN 17 602 258 337; this relationship needs role evidence before assigning the ABN. Business-bearing notice, but duplicates company evidence in other Lynham entries and does not make each development a company.",
    ),
    38: (
        "yes",
        "Retrieved notice page 1 dated 27 Oct 2021 names Lynham Networks Pty Ltd and identifies the network-infrastructure contracting role. Same notice bytes as other October entries; relevant business documentation but little incremental entity diversity. Development areas are not business identities.",
    ),
    39: (
        "yes",
        "Retrieved notice page 1 dated 03 Sep 2021 names Lynham Networks Pty Ltd. This establishes business content for the Kingswood entry, not a separate company per site. It shares the notice with other September entries; preserve this duplication and do not conflate letterhead branding with proven ownership.",
    ),
    40: (
        "yes",
        "Outcome Rates Data sheet row 2 explicitly contains ORG_NAME AIMBIG EMPLOYMENT PTY LTD and ORG_CD VVFE. Subsequent rows repeat the provider by contract, area and disability group. Although values are aggregated performance metrics, named provider organisations are identifiable; ORG_CD is only a source-local key, not an ABN.",
    ),
    41: (
        "yes",
        "Retrieved October notice page 1 explicitly names Lynham Networks Pty Ltd. Company-bearing notice, shared with other October development entries; adds a project/notice rather than an independently identified company. Do not map project addresses as headquarters.",
    ),
    42: (
        "yes",
        "Retrieved September notice page 1 explicitly names Lynham Networks Pty Ltd. Business relevance is supported by the attached document. It shares notice content with other September entries; the North Melbourne project does not represent a separate legal entity.",
    ),
    43: (
        "yes",
        "PDF page 1 names VostroNet (Australia) Pty Ltd and ABN 64 602 624 215, and lists Lidcombe, West Ryde and Rhodes project areas. Direct business and identifier evidence; distinguish company office from project areas and historical estimated completion dates.",
    ),
    47: (
        "unsure",
        "Metadata explicitly describes historical commercial buildings, owners/company names and business types. The only listed CSV returned HTTP 403, so no trader rows were inspected. Strong candidate plausibility, but unavailable primary records leave this audit unresolved.",
    ),
    48: (
        "no",
        "Metadata identifies pedestrian-crossing locations on the state road network, not business entities. The catalogue CSV/GeoJSON links return an HTML landing page rather than data; the official REST query returned two Armadale Rd crossing records with ROAD_NAME, XING_TYPE, OBJECTID and coordinates, with no business identity fields. Crossing IDs and road locations are physical assets, not business identifiers. This classification follows the dataset subject and available schema, not a claim to inspect every record.",
    ),
    50: (
        "no",
        "Publisher explicitly describes monthly numbers of public-vehicle registrations and licence conditions. This is aggregate count data, not identified licensees. CSV and JSON attempts returned 403, so this negative judgment is metadata-based and does not claim inspection of unavailable rows.",
    ),
}
assert len(notes) == 30
items = []
for r in evidence:
    n = r["rank"]
    if r["item_id"] in old:
        verdict, note = old[r["item_id"]]["verdict"], old[r["item_id"]]["evidence"]
        basis = "Re-assessed saved source evidence from the original 20-item audit; no new verdict change."
    else:
        verdict, note = notes[n]
        basis = "New evidence assessment for expanded census."
    items.append(
        {
            "rank": n,
            "item_id": r["item_id"],
            "title": r["title"],
            "verdict": verdict,
            "reviewer": "Codex assistant (AI)",
            "evidence": note,
            "assessment_basis": basis,
            "catalogue_url": "https://data.gov.au/data/dataset/" + r["item_id"],
            "resource_evidence": [
                {
                    "url": a["url"],
                    "artifact_id": a.get("artifact_id"),
                    "error": a.get("error") or a.get("parse_error"),
                }
                for a in r["attempts"]
            ],
        }
    )
assert len(items) == 50 and len({r["item_id"] for r in items}) == 50
sha = store.blob(
    (root / "full-triage-evidence.json").read_bytes(),
    "application/json",
    "full-triage-evidence.json",
)
worksheet_id = content_hash(
    {
        "scope": "full_shortlist_ai_census",
        "items": [r["item_id"] for r in items],
        "date": "2026-09-19",
    }
)
packet = {
    "id": worksheet_id,
    "kind": "triage_full_shortlist",
    "review_type": "ai_assisted",
    "reviewed_on": "2026-09-19",
    "sampling": "Census of the existing ranked 50; no reranking or replacement",
    "seed": None,
    "threshold": None,
    "items": items,
    "evidence_artifact": sha,
    "criterion": "Identifiable business/organisation subjects or explicit company-bearing source documents. Includes charities, ABN-bearing schools, named commercial venues and secondary business roles; incidental names in anonymous opinions or asset-management guidance do not establish business subjects. Relevance does not imply supported extraction, linkability, freshness or unique entities.",
}
(root / "full-triage-audit.json").write_text(json.dumps(packet, indent=2) + "\n")
# Separate namespace: never expand or replace the required 20-item human worksheet.
store.put("evaluations", worksheet_id, packet, "discovery", "ai_census", immutable=True)
aid = store.blob(
    (root / "full-triage-audit.json").read_bytes(),
    "application/json",
    "full-triage-audit.json",
)
labels = [
    {k: r[k] for k in ["item_id", "verdict", "reviewer", "evidence"]} for r in items
]
summary = evaluation.import_ai_labels(worksheet_id, labels, evidence_artifact=aid)
(root / "full-triage-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
counts = Counter(r["verdict"] for r in items)
print(dict(counts))
intro = f"""# Full shortlist AI-assisted audit — 19 September 2026

**All 50 ranked datasets assessed: {counts["yes"]} relevant, {counts["no"]} irrelevant, {counts["unsure"]} unresolved.** This is a census of the saved shortlist, not a new random sample. Human evaluation remains incomplete (0/20 triage and 0/50 links evidence-reviewed). The original 20-item AI audit remains 17 relevant / 1 irrelevant / 2 unresolved; the 50-link AI audit is unchanged.

The negative fraction among resolved assistant judgments is **{counts["no"]}/{counts["yes"] + counts["no"]} = {100 * counts["no"] / (counts["yes"] + counts["no"]):.2f}%**. Over all 50, {counts["no"]} are judged negative and {counts["unsure"]} unknown; do not count unknowns as correct. This is not human-measured precision, population accuracy, or a confidence interval.

## Method and qualifications

Each item was assessed for identifiable business/organisation content using source rows, workbook sheets, source documents or explicit publisher descriptions. The original 20 items were re-assessed using their retained evidence; fresh evidence was gathered for the other 30. No claim is made that all 50 resources were freshly downloaded or every row read. Downloads were bounded. Successful HTTP responses with empty bodies or HTML were treated as unusable data. Original ranks and deterministic scores remain unchanged.

The criterion includes charities and ABN-bearing public schools, named commercial venues, businesses in secondary roles (auditor firms/licensees) and notifying companies in telecom documents. It excludes records whose subjects are anonymous survey respondents, road assets or aggregate counts. Incidental references in guidance or opinions are not dependable business-profile records. This broad definition is disclosed so a reviewer can apply a stricter company-only definition if needed.

The ABN Bulk Extract is positive based on explicit publisher schema/documentation; its CSV is only a resource index and the bulk XML records were not inspected. Some negatives rely on explicit publisher descriptions because downloads failed. These distinctions are recorded per item. All unresolved items have insufficient accessible data for a justified yes/no decision.

## Findings that matter for the project

- **Discovery relevance is not extraction readiness.** XML/ZIP, PDF-only evidence, introductory worksheets, external hosting and HTML disguised by format metadata need different handling.
- **Dataset count is not entity diversity.** Eight Lynham notices identify the same company; annual ACNC returns repeat many organisations.
- **Aggregate values can still be useful.** DES outcome statistics name providers, so that dataset is relevant; anonymous monthly vehicle/licence counts are not.
- **Secondary roles matter.** SMSF auditor rows include audit firms; adviser rows include licensee companies. Do not merge the person with the organisation.
- **Ranking improvements remain future work.** Check actual resource type/access, distinguish entity grain from keyword matches, and penalise duplicate notice/annual-series coverage. Do not retune against this audit and call the result independent evaluation.

## Per-dataset judgments, in original rank order

| Rank | Dataset | Verdict | Evidence and limitation |
|---|---|---|---|
"""
for r in items:
    clean = lambda s: s.replace("|", "/").replace("\n", " ")
    intro += f"| {r['rank']} | [{clean(r['title'])}]({r['catalogue_url']}) | {r['verdict']} | {clean(r['evidence'])} |\n"
intro += "\n[Full evidence](full-triage-evidence.json) · [Structured labels](full-triage-audit.json) · [Summary](full-triage-summary.json) · [Original 20-item audit](REPORT.md)\n"
(root / "FULL_SHORTLIST_REPORT.md").write_text(intro)
e = html.escape
parts = [
    '<!doctype html><html lang="en"><meta charset="utf-8"><title>Full shortlist audit</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto;padding:0 16px;line-height:1.5}details{border:1px solid #ccc;padding:12px;margin:8px 0}summary{cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>',
    f'<h1>Full shortlist AI audit</h1><p>{counts["yes"]} relevant · {counts["no"]} irrelevant · {counts["unsure"]} unresolved. Human review remains incomplete.</p><p><a href="FULL_SHORTLIST_REPORT.md">Method and limitations</a></p>',
]
for r in items:
    parts.append(
        f'<details><summary>{r["rank"]}. {e(r["verdict"].upper())} — {e(r["title"])}</summary><p>{e(r["evidence"])}</p><p><a href="{e(r["catalogue_url"])}">Catalogue</a></p><pre>{e(json.dumps(r["resource_evidence"], indent=2))}</pre></details>'
    )
(root / "full-shortlist-report.html").write_text("\n".join(parts) + "\n</html>")
