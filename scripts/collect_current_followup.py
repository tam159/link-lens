"""Targeted additional audit evidence; never used as inference input."""

import csv
import io
import json
from pathlib import Path
from pypdf import PdfReader
from link_lens import store, ingestion

root = Path("outputs/ai-audit")
rows = json.loads((root / "full-triage-evidence.json").read_text())
out = []
for r in rows:
    rank = r["rank"]
    if rank not in [4, 5, 7, 9, 24, 26, 40, 41, 45, 47, 48, 49]:
        continue
    a = {"rank": rank}
    try:
        if rank in [4, 5, 9, 24, 26, 49]:
            a["artifact_id"] = r["attempts"][0]["artifact_id"]
            raw = store.blob_path(a["artifact_id"]).read_bytes()
        else:
            res = next(
                x
                for x in r["resources"]
                if (
                    "party-activity" in x["url"]
                    if rank in [41, 47, 48]
                    else x.get("format", "").lower().endswith("pdf")
                )
            )
            a["url"] = res["url"]
            raw, a["receipt"] = ingestion.download(
                res["url"], prefix=524288 if rank in [41, 47, 48] else None
            )
            a["artifact_id"] = store.blob(raw)
        if rank in [7, 40, 45]:
            a["pages"] = [
                {"page": n + 1, "text": p.extract_text()}
                for n, p in enumerate(PdfReader(io.BytesIO(raw)).pages[:6])
            ]
        else:
            text = raw.decode("utf-8-sig", errors="replace")
            dialect = csv.Sniffer().sniff(text[:16000], delimiters=",\t;|")
            examples = []
            for n, row in enumerate(
                csv.DictReader(io.StringIO(text, newline=""), dialect=dialect), 2
            ):
                if rank in [24, 26, 49] or any(
                    "pty" in str(v).lower()
                    or "limited" in str(v).lower()
                    or "ltd" in str(v).lower()
                    for v in row.values()
                ):
                    examples.append(
                        {
                            "row": n,
                            "values": {
                                k: v
                                for k, v in row.items()
                                if k
                                and any(
                                    t in k.lower()
                                    for t in [
                                        "name",
                                        "abn",
                                        "acn",
                                        "party",
                                        "firm",
                                        "org",
                                        "brand",
                                        "website",
                                    ]
                                )
                            },
                        }
                    )
                if len(examples) == 3:
                    break
            a["examples"] = examples
    except Exception as exc:
        a["error"] = str(exc)[:400]
    out.append(a)
    (root / "current-followup.json").write_text(json.dumps(out, indent=2) + "\n")
    print(
        rank, str(a.get("examples", a.get("pages", a.get("error"))))[:1000], flush=True
    )
