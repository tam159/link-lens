"""Authored AI judgments for the frozen Part 1 revision; never human labels."""

import html
import json
from pathlib import Path

from link_lens import evaluation, exports, store
from link_lens.contracts import content_hash
from link_lens.review_ui import prepare_review_page

root = Path("outputs/part1-downloadable")
audit = json.loads((root / "discovery-audit.json").read_text())
assert audit["id"] == "discovery-jev-luna-v1-downloadable-v3"
rows = audit["shortlist"]
assert content_hash([r["dataset_id"] for r in rows]) == '0b3c694d3e311f490a400239c8d524285867dc03e351903c690835de8a1627ea'
checks = json.loads((root / "download-checks.json").read_text())
follow = json.loads((root / "followup.json").read_text())
# Each note is an evidence judgment after reading the stored rows/documents.
notes = {
    1: "CSV row 2: RELI CAPITAL LTD, identifier 80005443292, licence 219612. Holder records; licence status is distinct from company status.",
    2: "CSV row 2: IPIB PTY LTD / 85007186003. Explicit licensee name and mixed ABN/ACN field; classification and checksums are needed before linking.",
    3: "TSV rows 2–3: LOVINI HOLDINGS / MONAKA PTY LTD share ACN 000000019 and ABN 89000000019. Current and historical names must not become separate companies.",
    4: "CSV row 5: NETWEALTH PTY LTD / ACN 119484043. Mixed individual and company representatives; appointing licensee is a different role.",
    5: "CSV row 23: BOQ SPECIALIST PTY LTD / 94110704464. Company representative is identifiable; not automatically identical to appointing holder.",
    6: "CSV row 2: Plumbing Gas and Solar / BN_ABN 30947976159. Business name is relevant, but identifier ownership still needs semantic review.",
    7: "CSV row 9: SMSF_CAPACITY_FIRM_NAME is GPP Audit Pty Limited. Firm is a secondary organisation, distinct from the individual auditor and auditor ABN.",
    8: "2022-23 Report sheet row 2: (UI!) THE URBAN INSTITUTE PTY LTD / 95608464535. Company-level expenditure; information sheet is not the data header.",
    9: "Income tax details row 2: 1 MENDS STREET PTY LTD / 94600082111. Named tax entities; reporting periods and tax-group scope require care.",
    10: "CSV row 2: AUSTRALIAN BUSINESS INSURANCE ADVISERS (ABIA) PTY LTD / ACN 081402379. Banning status is not general entity status.",
    11: "CSV row 2: U3A Inner North Incorporated / 51214424410, with address and website. Charity organisations qualify, even when not companies.",
    12: "Sheet1 row 2: Alberton Primary School / 35954747085. ABN-bearing public organisation qualifies under the declared broad criterion; historical 2015 data.",
    13: "CSV row 2 identifies CHARLESTOWN GOLF CLUB LTD as licensee, with separate venue name and licence number. Distinguish holder from premises.",
    14: "Account Advanced Find View row 2: Purpose Real Estate Ltd / 11616332444, alongside Coast2Bay Housing_ACNC Group. Member and group identities are distinct. Passed resource is the companion member workbook.",
    15: "CSV row 2: Sydney Missionary & Bible College / 11000047950, reporting dates and website. Organisation-year record, not a new entity each year.",
    16: "CSV row 2: Sydney Missionary & Bible College / 11000047950, 2022 reporting period. Overlap with other years is not independent evidence.",
    17: "CSV row 2: Sydney Missionary & Bible College / 11000047950 with address and annual financial fields. Historical charity return.",
    18: "Registered Suitable Operators row 2: OVER THE TOP ROOF RESTORATIONS PTY. LTD / ACN 090444714, explicitly Corporation (Company). External publisher-linked Azure file downloaded successfully.",
    19: "Sheet1 row 2: Sydney Missionary & Bible College / 11000047950. Main 2015 workbook was downloaded and parsed, improving on the earlier documentation-only audit.",
    20: "Sheet1 row 2: Sydney Missionary & Bible College / 11000047950. Main 2017 workbook now inspected; organisation-year grain and reporting-group caveats remain.",
    21: "Sheet1 row 2: Sydney Missionary & Bible College / 11000047950. Main 2014 workbook now inspected; identifier stored alongside charity name and address.",
    22: "CSV rows 2–3 identify Vision Australia and Job Centre Australia with site addresses. Identifiable service providers but no strong ABN/ACN in these rows.",
    23: "2017-18 sheet row 2: Alchemy Resources Limited / 17124444122; later sheets contain other entity-year allocations. Not anonymous totals.",
    24: "CSV row 2: bacoz developments pty ltd with country au and party/year IP counts. Synthetic party ID is not an ABN.",
    25: "CSV row 3 names OAKLAND HUNT CLUB as licensee and trading name. Mixed individuals, venue names and organisations require distinct roles.",
    26: "CSV row 2: Zauner Construction Pty Limited / 21087732607. Salesforce-hosted certificate export is accessible; certification status is source-specific.",
    27: "Passed CSV row 2: Morris; Mcmahon & Co Pty Ltd / 11000143082, reporting year 2020-21. Repeated metric rows do not represent distinct businesses. Latest resources may be ZIP; the verified resource is older.",
    28: "Application CSV alone lacks parties. Fresh companion design party-activity row 3 names mccormicks law / 51158618261, country au, organisation and opposition-agent role. Agent is not necessarily IP owner.",
    29: "Sheet1 row 2: Name_of_SIP Netbay Free WiFi Pty Ltd with St Kilda service area. Provider is explicit; project address is not registered office.",
    30: "List of VTTC reports row 4: ACCIONA AGUA AUSTRALIA PTY LTD / 84128531742. Repeated reporting years and ultimate-parent origin do not establish parent identity.",
    31: "Workbook provides service areas. Fresh companion signed PDF page 1 explicitly identifies Lynham Networks Pty Ltd trading as Lightning Wholesale / ABN 17 602 258 337 and references the spreadsheet. Mapping needs document-level context.",
    32: "Application CSV requires companion parties. Fresh design party-activity row 2 identifies cotters patent & trade mark attorneys, country au, ABN 34291651910.0; patent row 3 identifies madderns pty ltd. Roles must remain distinct.",
    33: "Fresh companion design party-activity row 2: watson chiarella pty ltd, organisation, country au, opposition respondent. Historical/superseded source; blank ABN limits linking.",
    34: "Downloaded product rows show Brand Daikin and representative URL daikin.co.nz, but no verified legal organisation or supplier ownership. Brand-only evidence remains unresolved; availability does not resolve entity semantics.",
    35: "TEL Register row 2: SYNTECH RESOURCES PTY LTD as licence holder; row 3 TA Australia Security Agent Pty Ltd. Activities and licence state are distinct from company identity/status.",
    36: "Downloaded labelled-product resource also shows Daikin brand and website without verified legal organisation ownership in inspected fields. Retain unresolved rather than infer identity from brand.",
    37: "Workbook describes Maroochydore project area; fresh signed PDF page 1 identifies Lynham Networks Pty Ltd / 17 602 258 337 and references the attached spreadsheet. Subject is declarant, not incidental publisher.",
    38: "Anticipatory notice sheet row 2 explicitly names DGtek Pty Ltd in Name_of_SIP for Cremorne. Project location must not become registered address.",
    39: "Sheet1 row 2 explicitly names Netbay Free WiFi Pty Ltd and Clayton service area. Organisation subject supported without ABN-based linking.",
    40: "Outcome Rates Data row 2: ORG_NAME AIMBIG EMPLOYMENT PTY LTD with organisation code VVFE. Provider-level outcome aggregates retain explicit organisation identity; codes are not national identifiers.",
    41: "All 32 sampled data rows concern asbestos locations/materials, with fixed owner abbreviation GCCC. No business subject/contractor identity; government asset ownership alone is incidental under the declared criterion. Unsupported in inspected resource, not a proof about every possible future version.",
    42: "CSV row 60 names Thargo Roadhouse, FacilityType Service station. Named commercial venues qualify under the declared broad criterion; most sampled rows are public facilities, and venue name does not establish legal owner.",
    43: "CSV rows 3–5 name Goulburn Mulwaree Council, Upper Lachlan Shire Council and Cessnock City Council as agencies with agency-level access-application outcomes. Supports identifiable public organisations under broad organisation scope, not named private-sector applicants; business-only interpretation would exclude it.",
    44: "Workbook has project areas; fresh signed PDF page 1 names Lynham Networks Pty Ltd trading as Lightning Wholesale / ABN 17 602 258 337 as contracting infrastructure provider. Needs document-level identity context.",
    45: "Workbook has project areas; fresh signed PDF page 1 names Lynham Networks Pty Ltd / 17 602 258 337 and explicitly references the 31Jan2025 spreadsheet. Relevant declarant, with document-level mapping needed.",
    46: "Board characteristics sheet row 4 names Children's Services Coordination Board with Public Entity status; row 5 Disciplinary Appeals Board. Named public bodies qualify under broad organisation scope, though totals in other sheets and board members are different grains.",
    47: "Anticipatory notice row 2 identifies DGtek Pty Ltd as Name_of_SIP and contracting party. Earlier notice for the same Cremorne area is not an independent company.",
    48: "Sheet1 row 2 names VostroNet (Australia) Pty Ltd as Name_of_SIP and contracting party for an Adelaide project. Historical estimated completion date is not company status.",
    49: "Sheet1 row 2 names Netbay Free WiFi Pty Ltd for Surrey Hills service area. Repeated provider across notices is not multiple entities.",
    50: "Sheet1 row 2 names VostroNet (Australia) Pty Ltd for Lidcombe and says it entered a development project contract. Provider identity is explicit; service-area polygons describe infrastructure.",
}
assert len(rows) == 50 and len(notes) == 50
packet = {
    "id": content_hash(["downloadable-ai-census", audit["id"]]),
    "kind": "triage",
    "batch_id": audit["id"],
    "sampling": "Census of frozen 50 download-gated ranks; bounded fresh resource evidence and companion documents; no reranking after judgments",
    "seed": None,
    "threshold": None,
    "review_type": "ai_assisted",
    "items": [],
}
for n, r in enumerate(rows, 1):
    a = next(
        a for a in checks[r["dataset_id"]]["attempts"] if a["status"] == "available"
    )
    packet["items"].append(
        {
            "item_id": r["dataset_id"],
            "rank": n,
            "title": r["title"],
            "verdict": "unsure" if n in [34, 36] else "no" if n == 41 else "yes",
            "reviewer": "assistant evidence audit",
            "evidence": notes[n],
            "artifact_id": a["artifact_id"],
            "resource_urls": [a["url"]]
            + [a["url"] for f in follow if f["rank"] == n for a in f["attempts"]],
        }
    )
store.put(
    "evaluations", packet["id"], packet, packet["batch_id"], "ai_census", immutable=True
)
artifact = store.json_blob(
    {"checks": checks, "followup": follow}, "downloadable-audit-evidence.json"
)
summary = evaluation.import_ai_labels(
    packet["id"],
    [
        {k: i[k] for k in ["item_id", "verdict", "reviewer", "evidence"]}
        for i in packet["items"]
    ],
    evidence_artifact=artifact,
)
for dest in [root, Path("outputs/ai-audit")]:
    exports.write_json(dest / "full-triage-audit.json", packet)
    exports.write_json(dest / "full-triage-summary.json", summary)
    exports.write_json(
        dest / "full-triage-evidence.json", {"checks": checks, "followup": follow}
    )
    intro = """# Download-verified shortlist: all-50 AI audit

**47 supported, 1 unsupported, 2 unresolved. All 50 passed a bounded download and reader check.** Human evaluation is partially complete: AI audit finished; the 20-item human hand-check is pending.

This is an AI evidence audit, not human precision. Among 48 resolved AI judgments, 1/48 (2.08%) is unsupported; 2/50 remain unresolved. Brand ownership explains both unresolved cases, not download failure. Asbestos asset records are the unsupported case. Named commercial venues, charities and public organisations qualify under the declared broad organisation criterion; this is broader than incorporated companies. GIPA councils and public boards are explicitly identified as public-sector cases. Relevance does not imply immediate mapping or linking readiness.

The ranking was frozen before audit and was not repaired using these judgments. Samples are bounded, not exhaustive. Some datasets need companion party tables or a signed declaration to identify the subject; source-level context still requires Part 2 review. The previous audit is preserved in [the pre-gate archive](../../experiments/jev-luna-before-download-gate/ai-audit/FULL_SHORTLIST_REPORT.md).

[Exact judgments](full-triage-audit.json), [fresh samples and companion evidence](full-triage-evidence.json). Raw download sample hashes and resource URLs are recorded per item. Application cost is unchanged: cached Jev scores were reused, and assistant audit tokens are outside the application ledger. Parts 2–4 were not rerun; their 52-link audit remains separate.

| Rank | Dataset | Verdict | Evidence |
|---:|---|---|---|
"""
    (dest / "FULL_SHORTLIST_REPORT.md").write_text(
        intro
        + "\n".join(
            f"| {i['rank']} | {i['title'].replace('|', '/')} | {i['verdict']} | {i['evidence'].replace('|', '/')} |"
            for i in packet["items"]
        )
        + "\n"
    )
    (dest / "full-shortlist-report.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Download-verified shortlist audit</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto}td{padding:10px;border:1px solid #ddd}table{border-collapse:collapse}</style><h1>47 supported · 1 unsupported · 2 unresolved</h1><p>50/50 download preflights passed. AI audit; human hand-check pending.</p><table>'
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
# Publish only the Part 1 revision; keep downstream exports byte-for-byte.
for key in ["discovery", "discovery-current-" + audit["experiment_id"]]:
    store.put("batches", key, audit, kind="discovery")
exports.jsonl(Path("outputs/shortlist.jsonl"), rows)
exports.write_json(
    Path("outputs/discovery-audit.json"),
    {k: v for k, v in audit.items() if k not in ["ranked", "shortlist"]},
)
worksheet = evaluation.worksheet("triage", audit["id"])
exports.write_json(Path("outputs/triage-review.json"), worksheet)
prepare_review_page(worksheet, Path("outputs/triage-review.html"))
from link_lens.measurements import summary as measurements

exports.write_json(
    Path("outputs/measurement-summary.json"), measurements(audit["experiment_id"])
)
print(json.dumps(summary, indent=2))
