"""Persist explicitly authored evidence judgments for the Jev/Luna shortlist.

Not an automatic classifier. Never run this against a different shortlist.
"""

import html
import json
from pathlib import Path
from link_lens import store, evaluation, exports
from link_lens.contracts import content_hash

root = Path("outputs/ai-audit")
evidence = json.loads((root / "full-triage-evidence.json").read_text())
follow = json.loads((root / "current-followup.json").read_text())
notes = {
    1: (
        "yes",
        "CSV row 2: RELI CAPITAL LTD, mixed identifier 80005443292, credit licence 219612. Licence-holder business records; licence status is not entity status.",
    ),
    2: (
        "yes",
        "CSV rows 2–3: IPIB PTY LTD / 85007186003 and IMC PACIFIC PTY LTD / 89099273846. Identifiable AFS holders; mixed ABN/ACN requires length and checksum handling.",
    ),
    3: (
        "yes",
        "TSV rows 2–3 share ACN 000000019 and ABN 89000000019 across LOVINI HOLDINGS and MONAKA names. Current/historic name distinction matters; rows are not separate companies.",
    ),
    4: (
        "yes",
        "Follow-up raw CSV rows 5–6 identify NETWEALTH PTY LTD / ACN 119484043 and ASPIRA ADVICE SOLUTIONS PTY LTD / 627832820. Mixture of individuals and companies; representative is distinct from appointing licensee.",
    ),
    5: (
        "yes",
        "Follow-up CSV row 23 identifies BOQ SPECIALIST PTY LTD / 94110704464; row 24 BAYMAN PTY. LIMITED / 60003993388. Mixed individual and organisation representatives; do not merge with licence holder.",
    ),
    6: (
        "yes",
        "Rows 2–3 identify Plumbing Gas and Solar and Bruce Ward Training with BN_ABN values. Business-name subjects qualify, but name/ABN ownership semantics still need explicit mapping and review.",
    ),
    7: (
        "yes",
        "Downloaded CSV is a resource index. Publisher bulk-extract PDF pages 3–5 defines ABN/entity/legal-name records in XML, supporting relevance through documentation. Bulk XML rows were not inspected; CSV metadata overstates shared-engine readiness.",
    ),
    8: (
        "unsure",
        "Both sampled official-linked CloudFront licence-category CSV URLs returned HTTP 404. Metadata is plausible, but rows were unavailable. Jev 0.94 is not verification.",
    ),
    9: (
        "yes",
        "Follow-up row 9 has SMSF_CAPACITY_FIRM_NAME GPP Audit Pty Limited. Main subject is an individual auditor; employer firm is a secondary organisation. Auditor ABN must not be assigned to that firm.",
    ),
    10: (
        "yes",
        "2022-23 Report sheet includes (UI!) THE URBAN INSTITUTE PTY LTD / 95608464535 and @HOME ARCHITECTURE PTY LTD / 53666147271. Information sheet precedes organisation-level expenditure records.",
    ),
    11: (
        "yes",
        "Income-tax workbook describes entity-level disclosures and contains named companies and ABNs. Introductory sheet explains reporting scope; entity-level relevance does not settle tax-group identity or dates.",
    ),
    12: (
        "yes",
        "CSV row 2 names AUSTRALIAN BUSINESS INSURANCE ADVISERS (ABIA) PTY LTD / ACN 081402379; row 3 BLACKBURNE & DIXON PTY LTD / 008876033. Banning record status is not company registration status.",
    ),
    13: (
        "yes",
        "Register CSV supplies Charity_Legal_Name, ABN, address and website fields with populated organisation records. Charities are not necessarily companies; registration and status are ACNC-specific.",
    ),
    14: (
        "yes",
        "Sheet1 row 2 Alberton Primary School / 35954747085, row 3 Allansford and District Primary School / 37051817052. ABN-bearing public organisations qualify under the broad organisation criterion; this is a historical 2015 extract.",
    ),
    15: (
        "yes",
        "CSV row 2 Charlestown Golf Club Ltd / licence LIQC300200019 and separate Licensee Name; row 3 Barooga Sports Club Ltd. Identifiable venues/holders, not anonymous licence totals.",
    ),
    16: (
        "yes",
        "Group-member workbook row 2 Purpose Real Estate Ltd / 11616332444; row 3 G-Force Recruitment Ltd / 15006145222. Member charities and group names are separate fields; no group-to-member identity merge.",
    ),
    17: (
        "yes",
        "AIS CSV names Sydney Missionary & Bible College / 11000047950 and Integricare Limited / 11000073870, with reporting dates and websites. Organisation-year grain; repeated years are not new entities.",
    ),
    18: (
        "yes",
        "2022 AIS CSV again supplies named charities, ABNs, reporting dates and financial fields. Relevance is supported, but overlap with other ACNC years is not independent corroboration.",
    ),
    19: (
        "yes",
        "2019 AIS CSV includes ABN, charity name, other names and address fields with populated charity rows. Historic yearly returns require group and period handling.",
    ),
    20: (
        "yes",
        "Workbook identifies OVER THE TOP ROOF RESTORATIONS PTY. LTD / ACN 090444714 and $Uccess Pty Ltd / ACN 600137942, explicitly Corporation (Company). Operator registration status is source-specific.",
    ),
    21: (
        "yes",
        "Main XLSX exceeded the 30 MB audit limit. Publisher explanatory PDF page 3 explicitly defines charity ABN and formal legal-name fields for each record. Documentary support only; main 2015 rows not inspected in this fresh audit.",
    ),
    22: (
        "yes",
        "Main XLSX exceeded audit limit, but group-reporting workbook member sheet identifies Abundant Life Church Incorporated / 11595120337 and its PBI operator / 29146062217. Group summary and member identities must stay distinct.",
    ),
    23: (
        "yes",
        "Companion group workbook lists BOND UNIVERSITY LIMITED / 88010694121 and CAMPUS OPERATIONS PTY. LTD. / 54010929316. Main XLSX exceeded limit; positive based on actual member rows, not synthetic group IDs.",
    ),
    24: (
        "yes",
        "Initial collector newline parsing failed; follow-up reads raw artifact with newline-safe CSV. Rows 2–4 name Vision Australia and Job Centre Australia with locations. These are service sites, lacking strong entity identifiers.",
    ),
    25: (
        "yes",
        "Annual workbook sheets name Alchemy Resources Limited / 17124444122 and Andromeda Metals Limited / 75061503375 alongside allocations. Entity-year monetary data, not anonymous totals.",
    ),
    26: (
        "yes",
        "Follow-up party_name rows identify bacoz developments pty ltd. Party/year IP statistics retain organisation identity; synthetic party IDs are not ABNs and cannot prove identity alone.",
    ),
    27: (
        "yes",
        "Location CSV contains LicenseeName, TradingAs, premises fields; OAKLAND HUNT CLUB appears as holder and trading name. Distinguish individual holders and venue names from legal entities.",
    ),
    28: (
        "yes",
        "Certificate rows name Zauner Construction Pty Limited / 21087732607 and ELLIS AIR CONDITIONING PROPRIETARY LIMITED / 13004601790. Identifiable organisations; code certification status is not corporate status.",
    ),
    29: (
        "unsure",
        "Historical company-register index metadata is plausible, but sampled Queensland download returned an empty resource. No company rows inspected; historical scope would also limit current usefulness.",
    ),
    30: (
        "unsure",
        "ACT Contracts 2020 CSV and JSON endpoints both returned HTTP 403. Supplier relevance is plausible from metadata, not established from inspected contract records.",
    ),
    31: (
        "unsure",
        "Notifiable Invoices CSV and JSON endpoints both returned HTTP 403. Supplier records could qualify, but no rows inspected.",
    ),
    32: (
        "unsure",
        "Mount Gambier traders CSV returned HTTP 403. Metadata mentions company/owner history, but actual content could not be confirmed.",
    ),
    33: (
        "unsure",
        "Both State Library contract CSV downloads returned empty resources. Claimed contract/supplier content is unverified; no empty file treated as evidence.",
    ),
    34: (
        "unsure",
        "Both discount-offer and business-venue CSV downloads returned empty resources. Metadata is strongly relevant, but business rows were not inspected.",
    ),
    35: (
        "unsure",
        "Rockhampton historical company-index CSV returned an empty resource. No actual company records inspected.",
    ),
    36: (
        "unsure",
        "South Australian liquor/gaming licence CSV and linked documentation returned HTTP 403. Record-level business content remains unverified.",
    ),
    37: (
        "unsure",
        "Both Queensland health contract-disclosure CSVs returned empty resources. Procurement descriptions alone do not verify supplier rows.",
    ),
    38: (
        "unsure",
        "ACT contracts CSV and JSON returned HTTP 403. No supplier rows inspected; retain unresolved rather than count relevant by title.",
    ),
    39: (
        "yes",
        "CSV delimiter parse failed; declaration PDF page 1 explicitly names VostroNet (Australia) Pty Ltd, ABN 64 602 624 215 and ACN 602 624 215. Company is the declaring subject, not incidental. Superloop affiliation must not become identity.",
    ),
    40: (
        "yes",
        "Newest resources labelled CSV are ZIP archives; initial decoding failed and a full download exceeded the audit limit. Follow-up 2022 organisation-list CSV names Integricare / 11000073870, Morris Mcmahon and Colas with ABNs. Relevance supported by older actual rows; latest-year payload not verified.",
    ),
    41: (
        "yes",
        "Application file alone lacks company names. Follow-up party-activity CSV row 7 identifies pizzeys patent and trade mark attorneys pty ltd / ABN 55626186356, role submitter. Submitter is not necessarily applicant/owner.",
    ),
    42: (
        "yes",
        "Workbook Sheet1 row 2 explicitly gives Name_of_SIP Netbay Free WiFi Pty Ltd and a service area. Organisation is the declared provider; area is not registered business address.",
    ),
    43: (
        "unsure",
        "Companion Card business-venue CSV returned an empty resource. Plausible business directory not verified from rows.",
    ),
    44: (
        "yes",
        "List of VTTC reports sheet row 4 names ACCIONA AGUA AUSTRALIA PTY LTD / 84128531742, with repeated years and published-report links. Entity/report-year grain; parent-origin field is not a parent identity.",
    ),
    45: (
        "yes",
        "Spreadsheet describes project areas without legal-name column. Follow-up signed declaration PDF page 1 names Lynham Networks Pty Ltd trading as Lightning Wholesale / ABN 17 602 258 337. Evidence is a company statement, not merely an incidental mention.",
    ),
    46: (
        "unsure",
        "ACT NoWaste CSV and JSON both returned HTTP 403. Waste-business licence metadata is relevant-looking, but no rows inspected.",
    ),
    47: (
        "yes",
        "Application table alone lacks names; PBR party-activity follow-up row 2 identifies grasslanz technology limited, party_type organisation, role applicant. ABN blank; relevant foreign organisations need not be automatically linkable.",
    ),
    48: (
        "yes",
        "Design party-activity follow-up row 2 identifies watson chiarella pty ltd, party_type organisation, role opposition_respondent. Historical/superseded data; role is distinct from applicant/owner.",
    ),
    49: (
        "unsure",
        "Product rows expose brand Daikin and brand/product website, but no verified legal organisation or supplier identity in inspected fields. Brand can denote several related businesses. Under the declared identifiable-organisation criterion, this is insufficient to mark relevant or prove the entire dataset irrelevant.",
    ),
    50: (
        "yes",
        "TEL Register workbook row 2 names SYNTECH RESOURCES PTY LTD as holder; later rows include TA Australia Security Agent Pty Ltd and DGR GLOBAL LIMITED. Licences/activities/locations are distinct from entity status.",
    ),
}
assert len(evidence) == 50 and set(notes) == set(range(1, 51))
shortlist = store.require("batches", "discovery-jev-luna-v1")["shortlist"]
assert [r["dataset_id"] for r in shortlist] == [r["item_id"] for r in evidence]
packet = {
    "kind": "triage",
    "batch_id": "discovery-jev-luna-v1",
    "sampling": "Census of all 50 newly ranked datasets; fresh bounded resource samples plus targeted documentation/secondary-resource checks",
    "seed": None,
    "threshold": None,
    "review_type": "ai_assisted",
    "items": [],
}
for r in evidence:
    verdict, note = notes[r["rank"]]
    packet["items"].append(
        {
            "item_id": r["item_id"],
            "rank": r["rank"],
            "title": r["title"],
            "verdict": verdict,
            "reviewer": "assistant evidence audit (separate from Jev ranking and Luna inference)",
            "evidence": note,
            "resource_urls": [a["url"] for a in r["attempts"]]
            + [a["url"] for a in follow if a["rank"] == r["rank"] and a.get("url")],
        }
    )
packet["id"] = content_hash(
    {
        "kind": "ai-full-shortlist",
        "batch": packet["batch_id"],
        "item_ids": [i["item_id"] for i in packet["items"]],
    }
)
store.put(
    "evaluations", packet["id"], packet, packet["batch_id"], "ai_census", immutable=True
)
artifact = store.json_blob(
    {"evidence": evidence, "followup": follow}, "jev-luna-full-triage-evidence.json"
)
summary = evaluation.import_ai_labels(
    packet["id"],
    [
        {k: i[k] for k in ["item_id", "verdict", "reviewer", "evidence"]}
        for i in packet["items"]
    ],
    evidence_artifact=artifact,
)
exports.write_json(root / "full-triage-audit.json", packet)
exports.write_json(root / "full-triage-summary.json", summary)
intro = f"""# New shortlist: full AI evidence audit

**{summary["supported"]} relevant, {summary["not_supported"]} unsupported, {summary["unresolved"]} unresolved, across all 50 datasets.** Human evaluation remains incomplete. This is not 100% accuracy: inaccessible/ambiguous cases remain unresolved, and relevance does not mean ready for extraction or linking.

Fresh resource attempts and targeted follow-ups are in [full-triage-evidence.json](full-triage-evidence.json) and [current-followup.json](current-followup.json). Exact judgments: [full-triage-audit.json](full-triage-audit.json). The main API usage ledger excludes this assistant's audit tokens, which are not available here.

Criterion: identifiable businesses/organisations as subjects, licence holders, suppliers, service providers or explicit secondary organisation roles. Includes charities and ABN-bearing public organisations; excludes anonymous totals and incidental mentions. A brand alone does not prove a company identity. Publisher schema documentation can support relevance, but is explicitly distinguished from inspected data rows. Downloads are bounded samples, not exhaustive row checks. No Jev probabilities or prior audit labels are used as correctness labels.

The shortlist was not changed after these judgments. High Jev scores cannot fix HTTP 403/404, empty files, misleading format metadata, historical coverage or ambiguous brand ownership. An apparently better resolved negative fraction can conceal more unknowns; compare the complete denominator and unresolved count.

The original 20-item human worksheet is unfilled. This full census is stored as `ai_census` with `ai_label`, not human labels. The separate [all-link census](LINKS_REPORT.md) covers the completed approved batch.

| Rank | Dataset | Verdict | Evidence and limitation |
|---:|---|---|---|
"""
lines = [
    f"| {i['rank']} | {i['title'].replace('|', '/')} | {i['verdict']} | {i['evidence'].replace('|', '/')} |"
    for i in packet["items"]
]
(root / "FULL_SHORTLIST_REPORT.md").write_text(intro + "\n".join(lines) + "\n")
(root / "full-shortlist-report.html").write_text(
    '<!doctype html><meta charset="utf-8"><title>Jev/Luna full shortlist audit</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto}td,th{padding:12px;border:1px solid #ddd;vertical-align:top}table{border-collapse:collapse}</style><h1>New shortlist AI evidence audit</h1><p>'
    + html.escape(
        f"{summary['supported']} relevant / {summary['not_supported']} unsupported / {summary['unresolved']} unresolved. AI audit, not human ground truth."
    )
    + "</p><table><tr><th>Rank</th><th>Dataset</th><th>Verdict</th><th>Evidence</th></tr>"
    + "".join(
        "<tr>"
        + "".join(
            "<td>" + html.escape(str(i[k])) + "</td>"
            for k in ["rank", "title", "verdict", "evidence"]
        )
        + "</tr>"
        for i in packet["items"]
    )
    + "</table>"
)
print(json.dumps(summary, indent=2))
