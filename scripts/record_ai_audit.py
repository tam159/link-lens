"""Materialize the assistant's 18 Sep 2026 judgments, not an automatic evaluator.

The assistant inspected all 50 raw name/identifier pairs and each dataset's
sample/documentation. Notes below are those judgments. Do not reuse on new data.
"""

import json
from pathlib import Path
from link_lens import store

ROOT = Path("outputs/ai-audit")
triage = json.loads((ROOT / "triage-evidence.json").read_text())
links = json.loads((ROOT / "link-evidence.json").read_text())
followups = json.loads((ROOT / "followup-evidence.json").read_text())
# These statements refer to the original seeded worksheet ordering, not new samples.
notes = [
    (
        "yes",
        "The CSV has named commercial venues: FacilityID 82 is Zephyrs Cafe (Food outlet), and 94 is Thargo Roadhouse (Service station). This satisfies the broad contains-businesses criterion. Most rows are facilities; names identify venues, not verified legal operators. No ABN/ACN or ownership inference is justified.",
    ),
    (
        "yes",
        "TEL Register sheet rows 2 and 3 explicitly name TEL holders SYNTECH RESOURCES PTY LTD and TA Australia Security Agent Pty Ltd. Repeated licence versions and expired records are present; holder identity must be kept separate from sites and current licence status.",
    ),
    (
        "yes",
        "Attached 5 July 2022 PDF page 1 names Myport pty ltd trading as Gigafy in Name_of_SIP and prints ABN 32 121 129 280. Contains an identifiable business even though resources are PDF/geospatial, outside the initial tabular extractor. Project address is not automatically a registered business address.",
    ),
    (
        "yes",
        "Attached PDF page 1 dated 27 Sep 2021 explicitly states Lynham Networks Pty Ltd gives the notice. Letterhead prints Lightning Wholesale and ABN 17 602 258 337. This is business-bearing documentation; the XLSX rows themselves are development sites (e.g. 75-135 Bolinda Road). Do not infer separate companies from project names or assign the letterhead ABN without resolving its role.",
    ),
    (
        "no",
        "Publisher description explicitly says monthly number of driver licence renewals by how early they were paid. That is an aggregate count grain, not identifiable businesses. Resource returned zero bytes; explanatory TXT returned 403. This negative judgment is based on publisher metadata, not a claimed inspection of unavailable rows.",
    ),
    (
        "yes",
        "2016 workbook Sheet1 row 2 contains ABN 11000047950 and Sydney Missionary & Bible College, alongside registration, location and financial fields. Charities are organisations, not all incorporated companies; annual/group financial reporting requires grain checks.",
    ),
    (
        "yes",
        "2024 AIS CSV row 2 contains ABN 11000047950, Sydney Missionary & Bible College, Registered, and reporting dates. Row 3 is Integricare Limited, ABN 11000073870. Entity-level records with explicit identifiers; consolidated financial reports must not imply group identity.",
    ),
    (
        "yes",
        "The tab-separated sample contains NETWEALTH PTY LTD with AFS_REP_ACN 119484043 and ASPIRA ADVICE SOLUTIONS PTY LTD with ACN 627832820. Earlier rows are natural persons. Representative ACN identifies the representative, while AFS_LIC_NUM is a licence number, not the representative company identifier.",
    ),
    (
        "yes",
        "IPLORD CSV rows 2-3 name bacoz developments pty ltd with party_id value 1.0, AU/VIC/3214 and different financial years. Counts are repeated per named party/year rather than anonymous national aggregates. party_id is a local key, not a verified ABN; no name-only automatic merge.",
    ),
    (
        "yes",
        "Workbook Anticipatory notice sheet row 2 has Name_of_SIP DGtek Pty Ltd and a contract statement naming that company. Project_Area is 29-37 Genoa Street, Moorabbin. A single-company notice qualifies, although project geometry/address must not become company identity or headquarters.",
    ),
    (
        "yes",
        "Tab-separated company sample rows 2-3 have ACN 000000019, ABN 89000000019, former name LOVINI HOLDINGS PTY LTD and current MONAKA PTY LTD. Explicit business identifiers are present; Current Name Indicator is essential to avoid presenting former names as current.",
    ),
    (
        "yes",
        "Attached PDF page 1 dated 27 Oct 2021 names Lynham Networks Pty Ltd as the notifying company. XLSX holds site references, addresses and dates, not separate company rows. Letterhead ABN 17 602 258 337 appears under Lightning Wholesale; role requires care. Business-bearing, but low diversity alongside other Lynham notices.",
    ),
    (
        "yes",
        "Attached PDF page 1 dated 03 Sep 2021 names Lynham Networks Pty Ltd; XLSX includes LHN_SMITH at 5-9 Smith Street, Epping. The company is identifiable from the notice, not from converting the development into a business. Metadata says VIC while spreadsheet says NSW for that site: preserve this discrepancy. Repeated notices do not add distinct companies.",
    ),
    (
        "unsure",
        "Catalogue describes an ACT Government contracts list, but CSV export and the alternative official JSON resource endpoint both returned HTTP 403. Likely business suppliers, but no supplier rows were inspected. Do not count metadata plausibility as a verified positive.",
    ),
    (
        "yes",
        "Credit representative CSV includes BOQ SPECIALIST PTY LTD with CRED_REP_ABN_ACN 94110704464, and CEMRUN PTY LTD with 97071719205. Also contains natural persons with blank IDs. Mixed ABN/ACN semantics and representative versus appointing licensee must remain distinct.",
    ),
    (
        "yes",
        "CSV rows 2-3 explicitly identify licensees CHARLESTOWN GOLF CLUB LTD and BAROOGA SPORTS CLUB LTD as well as licence/premises names. Contains businesses, but licence ID is not ABN/ACN, premises can differ from holder, and this resource is a June 2020 snapshot.",
    ),
    (
        "yes",
        "CSV rows 2-3 identify provider/site labels Vision Australia and Job Centre Australia, with websites and service-location addresses. Identifiable organisation evidence, but no ABN/ACN. DIS_SITE_CODE is a site code and SITE_NAME is not established as a legal company name; repeated locations must not create separate companies.",
    ),
    (
        "unsure",
        "Catalogue describes contracts with suppliers above $25,000, but both CSV and alternative official JSON endpoints returned HTTP 403. Supplier-level data is plausible; unavailable rows prevent a verified decision. Not counted as either correct or incorrect.",
    ),
    (
        "yes",
        "2019 AIS CSV contains abn and charity name fields, including St Peters Pre-School Ltd / 11002389746 and Chrysalis School For Rudolf Steiner Education Ltd / 11002595422. These are organisation-level reporting records. Historical annual values and consolidated reports require temporal/grain checks.",
    ),
    (
        "yes",
        "Financial-adviser CSV row 2 names individual JOHN PETER CORNIPS and separately LICENCE_NAME BJT FINANCIAL PLANNING PTY. LTD. with LICENCE_ABN 25005620824. Row 3 names HOOD SWEENEY SECURITIES PTY LTD / 40081455165. Contains identifiable companies as licensees; never assign a licensee ABN to the adviser as the same entity.",
    ),
]
assert len(notes) == len(triage) == 20 and len(links) == 50
refs = {
    name: store.blob((ROOT / name).read_bytes(), "application/json", name)
    for name in ["triage-evidence.json", "link-evidence.json", "followup-evidence.json"]
}
common = {
    "review_type": "ai_assisted",
    "reviewer": "Codex assistant (AI)",
    "review_date": "2026-09-18",
    "method": "Assistant inspection of raw source names, identifiers, roles, sample records and publisher documents. Scripts collect and format evidence; they do not independently establish truth.",
    "limitations": [
        "Not a human hand-check. No human-ground-truth precision claim.",
        "Same source snapshots used by the pipeline can share errors; no external live ABR/company verification for each pair.",
        "Link sample is the 50-link constructed overlap cohort, not a population sample. Only Companies, ACNC and AFS contribute links.",
        "Dataset audit checks existence of identifiable businesses, not extraction readiness, freshness or business purity.",
        "Downloads are samples except full XLSX/PDF documents; no claim to review every source row.",
        "Assistant audit token cost and wall time are not in the application model-call ledger and are unknown.",
    ],
    "evidence_artifacts": refs,
}
for kind, data in [("triage", triage), ("links", links)]:
    sheet = json.loads(
        Path(
            "outputs/" + ("link" if kind == "links" else kind) + "-review.json"
        ).read_text()
    )
    assert [i["item_id"] for i in sheet["items"]] == [i["item_id"] for i in data]
    packet = {
        **common,
        "id": sheet["id"],
        "kind": sheet["kind"],
        "batch_id": sheet["batch_id"],
        "seed": sheet["seed"],
        "threshold": sheet["threshold"],
        "items": [],
    }
    for n, item in enumerate(data, 1):
        if kind == "triage":
            verdict, note = notes[n - 1]
            urls = [a["url"] for a in item["attempts"]] + [
                a["url"] for a in followups if a["number"] == n
            ]
            evidence_refs = {
                "dataset_id": item["item_id"],
                "catalogue_url": f"https://data.gov.au/data/dataset/{item['item_id']}",
                "resource_urls": urls,
                "evidence_entry": n,
            }
        else:
            a, b = item["raw_records"]
            va, vb = a["values"], b["values"]
            name = lambda v: next(
                v[k].strip()
                for k in ["Company Name", "Charity_Legal_Name", "AFS_LIC_NAME"]
                if k in v
            )
            abn = lambda v: v.get("ABN", v.get("AFS_LIC_ABN_ACN", "")).strip()
            ida, idb = abn(va), abn(vb)
            if n == 35:
                identifier = va["ACN"]
                assert identifier == vb["AFS_LIC_ABN_ACN"] == "000022480"
                assert (
                    10
                    - sum(int(c) * w for c, w in zip(identifier[:8], range(8, 0, -1)))
                    % 10
                ) % 10 == int(identifier[-1])
                detail = f"Explicit ACN {identifier} agrees. Company ABN is sentinel 0 and is not used; nine-digit AFS value is treated as ACN, never padded into an ABN."
            else:
                assert ida == idb and len(ida) == 11
                ds = list(map(int, ida))
                ds[0] -= 1
                assert (
                    sum(
                        d * w
                        for d, w in zip(ds, [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19])
                    )
                    % 89
                    == 0
                )
                detail = f"Explicit ABN {ida} agrees and passes an independently written checksum calculation."
            special = {
                7: "LIMITED versus Ltd is a suffix abbreviation.",
                20: 'Names differ by an extra "the" before Northern Beaches and LTD/Limited; locality and organisation agree.',
                24: "ACNC omits LIMITED. The explicit shared ABN differs from the company ACN suffix; this is a useful counterexample to deriving ACN from ABN.",
                43: "ACNC adds an apostrophe after MATRONS; the organisation name otherwise agrees.",
                39: "Other organisation names list several Legacy branches; this link uses the legal-name record, not a claim that all branches are one entity.",
            }.get(n, "Names agree after case/outer-whitespace normalization.")
            note = f'{a["source"]["slug"]}: "{name(va)}"; {b["source"]["slug"]}: "{name(vb)}". {detail} {special} The compared fields identify the company/registered organisation or licensee itself, not its parent or appointee. Supported within these snapshots; not independent registry ground truth.'
            verdict = "yes"
            evidence_refs = {
                "evidence_entry": n,
                "raw_records": [
                    {
                        "source": r["source"],
                        "record_id": r["record_id"],
                        "locator": r["locator"],
                    }
                    for r in item["raw_records"]
                ],
            }
        packet["items"].append(
            {
                "item_id": item["item_id"],
                "verdict": verdict,
                "reviewer": common["reviewer"],
                "evidence": note,
                "evidence_refs": evidence_refs,
            }
        )
    (ROOT / f"{kind}-audit.json").write_text(json.dumps(packet, indent=2) + "\n")
print(
    "Recorded 20 dataset judgments and 50 pair judgments as AI-assisted; human labels untouched."
)
