"""Persist the assistant's inspected 52-pair census, not an automatic truth labeler."""

import html
import json
from pathlib import Path
from link_lens import store, evaluation, exports
from link_lens.contracts import content_hash

root = Path("outputs/ai-audit")
rows = json.loads((root / "link-evidence.json").read_text())
current = json.loads(Path("outputs/current-run.json").read_text())
assert current["batch_id"] == "fa5523f0-7d5a-41d2-af42-59e6362e3046", (
    "Judgments apply only to the inspected batch"
)
assert len(rows) == 52
# Individually inspected name differences; every other pair agrees ignoring case/space.
notes = {
    2: "Dots/spaces in W.H. versus WH differ.",
    4: "ACNC omits LIMITED; exact ABN supports the same Northcott organisation. Its ACN differs from the ABN suffix, so suffix derivation would be wrong.",
    6: "PROPRIETARY LIMITED is abbreviated PTY LTD.",
    9: "LIMITED/LTD suffix difference.",
    12: "Punctuation in PTY. differs.",
    14: "LIMITED/LTD suffix difference.",
    16: "LIMITED/LTD suffix difference.",
    20: "LIMITED/LTD suffix difference.",
    21: "LIMITED/LTD suffix difference.",
    25: "LIMITED/LTD suffix difference.",
    30: "PTY. LIMITED versus PTY LTD.",
    31: "Trailing full stop differs.",
    32: "LIMITED/LTD suffix difference.",
    38: "LIMITED/LTD suffix difference.",
    39: "LIMITED/LTD suffix difference.",
    42: "ACNC adds an apostrophe after MATRONS.",
    45: "ACNC omits the second THE and spells LIMITED instead of LTD; the distinctive organisation and exact ABN agree.",
    48: "LIMITED/LTD suffix difference.",
}
packet = {
    "kind": "links",
    "batch_id": current["batch_id"],
    "sampling": "Census of every proposed link in the overlap-selected batch (52 links); not a population sample",
    "seed": None,
    "threshold": 0.99,
    "review_type": "ai_assisted",
    "items": [],
}
for row in rows:
    a, b = row["raw_records"]
    va, vb = a["values"], b["values"]
    abn = va["ABN"].strip()
    assert abn == vb["ABN"].strip() == row["link"]["evidence"]["identifier"]
    assert row["link"]["evidence"]["identifier_type"] == "entity.abn"
    digits = [int(c) for c in abn]
    digits[0] -= 1
    assert (
        len(abn) == 11
        and sum(d * w for d, w in zip(digits, [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]))
        % 89
        == 0
    )
    assert va["Current Name Indicator"] == "Y"
    na = va["Company Name"].strip()
    nb = (vb.get("Charity_Legal_Name") or vb.get("Name")).strip()
    if row["number"] not in notes:
        assert na.casefold() == nb.casefold(), (row["number"], na, nb)
    detail = notes.get(
        row["number"], "Names agree after case/outer-whitespace normalization."
    )
    role = (
        "ATO corporate tax entity is linked only by its own reported ABN; no parent, subsidiary or consolidated group identity is inferred."
        if b["source"]["slug"] == "corporate-transparency"
        else "ACNC charity legal-name/ABN record identifies the organisation itself, not another organisation mentioned in its activities."
    )
    note = f"{a['source']['slug']} row {a['locator']['row']}: {na}; {b['source']['slug']} row {b['locator']['row']}: {nb}. Explicit ABN {abn} agrees and passes a separately written checksum calculation. {detail} {role} Supported within these snapshots, not independent registry ground truth."
    packet["items"].append(
        {
            "item_id": row["item_id"],
            "number": row["number"],
            "verdict": "yes",
            "reviewer": "assistant evidence audit; separate from Jev triage/Luna mapping",
            "evidence": note,
            "evidence_refs": [
                {
                    "source": r["source"],
                    "record_id": r["record_id"],
                    "locator": r["locator"],
                }
                for r in [a, b]
            ],
        }
    )
packet["id"] = content_hash(
    {
        "kind": "ai-all-links",
        "batch": packet["batch_id"],
        "items": [r["item_id"] for r in rows],
    }
)
store.put(
    "evaluations",
    packet["id"],
    packet,
    packet["batch_id"],
    "ai_link_census",
    immutable=True,
)
artifact = store.json_blob(rows, "jev-luna-link-evidence.json")
labels = [
    {k: i[k] for k in ["item_id", "verdict", "reviewer", "evidence"]}
    for i in packet["items"]
]
summary = evaluation.import_ai_labels(packet["id"], labels, evidence_artifact=artifact)
# Required seeded 50-link worksheet gets a separate AI view, never human labels.
sheet = json.loads(Path("outputs/link-review.json").read_text())
wanted = {i["item_id"] for i in sheet["items"]}
evaluation.import_ai_labels(
    sheet["id"],
    [i for i in labels if i["item_id"] in wanted],
    evidence_artifact=artifact,
)
exports.write_json(root / "links-audit.json", packet)
exports.write_json(root / "links-summary.json", summary)
intro = """# New link census: all 52 proposed links

**52 supported, 0 unsupported, 0 unresolved.** All use explicit ABN equality with compatible names and source roles. Raw rows, locators, source URLs and mapping IDs are retained in [link-evidence.json](link-evidence.json); individual judgments in [links-audit.json](links-audit.json).

This is an AI evidence audit, not human-measured precision or independent registry ground truth. The shared parser reads raw rows, while checksum arithmetic is implemented separately from the resolver. The assistant inspected names and subject roles, including suffix/punctuation differences and Northcott's nonmatching ACN suffix. Shared publisher errors remain possible. ATO monetary totals/group accounting are not claims that every group member is the same entity.

The 50-entity seed cohort plus deterministic filler yielded two additional overlapping entities: BROWN-FORMAN AUSTRALIA and ARKEMA. Thus the output has 52 links/profiles, not exactly 50. Every output link is audited; the required seeded human worksheet still samples 50 and remains unreviewed. Confidence 0.99 is a rule score, not measured probability. There is no recall estimate and no evidence of 100% population accuracy.

The links comprise 35 Companies–ATO pairs and 17 Companies–ACNC pairs. AFS, Business Names and Employment contribute no linked profile evidence in this batch. Compare all denominators and abstentions, not just supported-link counts.

| # | Verdict | Evidence |
|---:|---|---|
"""
(root / "LINKS_REPORT.md").write_text(
    intro
    + "\n".join(
        f"| {i['number']} | {i['verdict']} | {i['evidence'].replace('|', '/')} |"
        for i in packet["items"]
    )
    + "\n"
)
(root / "links-report.html").write_text(
    '<!doctype html><meta charset="utf-8"><title>All 52 link judgments</title><style>body{font:16px system-ui;max-width:1000px;margin:40px auto}li{margin:20px 0}</style><h1>52/52 links supported by AI evidence audit</h1><p>Selected overlap cohort; not human ground truth or population accuracy.</p><ol>'
    + "".join("<li>" + html.escape(i["evidence"]) + "</li>" for i in packet["items"])
    + "</ol>"
)
print(json.dumps(summary, indent=2))
