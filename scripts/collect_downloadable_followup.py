"""Read companion resources for the frozen download-gated shortlist; no labels."""

import io
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pypdf import PdfReader

from link_lens import store
from link_lens.downloadability import probe_resource
from link_lens.ingestion import download

rows = [
    json.loads(l)
    for l in Path("outputs/part1-downloadable/shortlist.jsonl").read_text().splitlines()
]


def collect(n):
    r = rows[n - 1]
    d = store.require("sources", r["dataset_id"])["metadata"]
    choices = [
        x
        for x in d["resources"]
        if (
            "pdf" in x.get("format", "").lower()
            if n in [31, 37, 44, 45]
            else "party" in (x.get("name", "") + " " + x.get("url", "")).lower()
        )
    ]
    result = {"rank": n, "dataset_id": r["dataset_id"], "attempts": []}
    for res in choices[:3]:
        if n in [31, 37, 44, 45]:
            data, receipt = download(res["url"], maximum=10_000_000)
            a = {
                **receipt,
                "artifact_id": store.blob(data, name="triage-followup.pdf"),
                "pages": [
                    p.extract_text() for p in PdfReader(io.BytesIO(data)).pages[:3]
                ],
            }
        else:
            a = probe_resource(res)
        result["attempts"].append(a)
    return result


with ThreadPoolExecutor(max_workers=4) as pool:
    result = list(pool.map(collect, [28, 32, 33, 31, 37, 44, 45]))
Path("outputs/part1-downloadable/followup.json").write_text(
    json.dumps(result, indent=2)
)
for r in result:
    print(r["rank"])
    for a in r["attempts"]:
        if "pages" in a:
            print(a["pages"][0][:1900])
        else:
            print(str(a.get("sample", {}).get("rows", [])[:3])[:1700])
