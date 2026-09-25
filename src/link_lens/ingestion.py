import hashlib
import io
import json
import re
import subprocess
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlencode, urlparse

from pypdf import PdfReader

from . import store
from .contracts import SourceRequest
from .readers import inspect_resource
from .settings import settings

PORTALS = {
    "data.gov.au",
    "data.qld.gov.au",
    "www.data.qld.gov.au",
    "data.nsw.gov.au",
    "data.sa.gov.au",
    "discover.data.vic.gov.au",
}
QUERIES = [
    "business OR company OR charity OR licence OR contract",
    "abn",
    "corporate transparency",
    "employment provider locations",
    "supplier register",
]
PORTFOLIO = [
    "asic-companies",
    "asic-business-names",
    "asic-afs-licensee",
    "acnc-register",
    "corporate-transparency",
    "employment-provider-locations-and-contacts",
]


def safe_url(url):
    p = urlparse(url)
    if p.scheme != "https" or p.username or p.password or p.port not in (None, 443):
        raise ValueError("Only public HTTPS government resources are supported")
    if not p.hostname or not p.hostname.endswith((".gov.au", ".govt.nz")):
        raise ValueError("Resource must be on a government domain")
    return url


def download(url, *, prefix=None, maximum=100_000_000):
    safe_url(url)
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "body"
        headers = Path(tmp) / "headers"
        command = [
            "curl",
            "--fail",
            "--location",
            "--silent",
            "--show-error",
            "--proto",
            "=https",
            "--proto-redir",
            "=https",
            "--connect-timeout",
            "15",
            "--max-time",
            "120",
            "--retry",
            "1",
            "--max-filesize",
            str(maximum),
            "--dump-header",
            str(headers),
            "--output",
            str(output),
        ]
        if prefix:
            command += ["--range", f"0-{prefix - 1}"]
        completed = subprocess.run(
            command + [url], capture_output=True, timeout=255, check=False
        )
        if completed.returncode:
            raise RuntimeError(f"Download failed: {completed.stderr.decode()[:400]}")
        data = output.read_bytes()
        if not data:
            raise ValueError("Resource returned an empty response")
        raw_headers = headers.read_text(errors="replace")
        partial = bool(
            re.search(r"^content-range:", raw_headers, re.IGNORECASE | re.MULTILINE)
        )
        return data, {
            "partial": partial,
            "retrieved_at": store.now(),
            "url": url,
            "bytes": len(data),
        }


def action(portal, name, **params):
    if urlparse(portal).hostname not in PORTALS:
        raise ValueError("Unsupported CKAN portal")
    data, _ = download(
        f"{portal.rstrip('/')}/api/3/action/{name}?{urlencode(params)}",
        maximum=30_000_000,
    )
    result = json.loads(data)
    if not result.get("success"):
        raise ValueError(f"CKAN action failed: {result.get('error')}")
    return result["result"]


def normal_format(resource):
    fmt = resource.get("format", "").lower()
    if "xlsx" in fmt:
        return "xlsx"
    if fmt in ("csv", "tsv"):
        return "csv"
    if "json" in fmt:
        return "json"
    return None


def catalogue_score(dataset):
    title = dataset["title"].lower()
    notes = (dataset.get("notes") or "").lower()
    text = title + " " + notes
    terms = {
        "abn": 0.20,
        "acn": 0.16,
        "company": 0.12,
        "business names": 0.16,
        "licensee": 0.16,
        "licence": 0.12,
        "charities": 0.12,
        "corporate": 0.12,
        "provider": 0.14,
        "supplier": 0.12,
        "register": 0.12,
        "entity": 0.10,
        "locations and contacts": 0.16,
    }
    matches = [
        term for term in terms if re.search(r"\b" + re.escape(term) + r"\b", text)
    ]
    score = 0.08 + sum(terms[t] for t in matches)
    # Current register titles outrank historical annual returns with identical notes.
    if re.search(r"\b(register|registered)\b", title):
        score += 0.12
    if any(normal_format(r) for r in dataset.get("resources", [])):
        score += 0.12
    penalties = [
        term
        for term in ["statistics", "benchmark", "survey", "counts", "projections"]
        if term in title
    ]
    score -= 0.22 * len(penalties)
    return round(min(0.98, max(0.01, score)), 3), matches, penalties


def discover():
    datasets = {}
    queries = []
    for query in QUERIES:
        result = action("https://data.gov.au/data", "package_search", q=query, rows=200)
        queries.append(
            {
                "query": query,
                "returned": len(result["results"]),
                "total_matches": result["count"],
            }
        )
        for d in result["results"]:
            datasets[d["id"]] = d
    if len(datasets) < 500:
        raise RuntimeError(
            f"Only {len(datasets)} unique records; increase catalogue retrieval"
        )
    from .triage import classify_catalogue

    discovery_id = "discovery-" + settings().experiment_id
    decisions = classify_catalogue(datasets, discovery_id)
    ranked = []
    for d in datasets.values():
        score, hits, penalties = catalogue_score(d)
        org = (d.get("organization") or {}).get("title", "unknown")
        ranked.append(
            {
                "dataset_id": d["id"],
                "slug": d["name"],
                "title": d["title"],
                "publisher": org,
                "formats": sorted(
                    {r.get("format", "") for r in d.get("resources", [])}
                ),
                "confidence": round(
                    0.5 * score + 0.5 * decisions[d["id"]]["probability"], 6
                )
                if d["id"] in decisions
                else score,
                "deterministic_score": score,
                "jev": decisions.get(d["id"]),
                "confidence_kind": "uncalibrated 50:50 metadata rule score and Jev relevance score; not measured precision",
                "reason": f"Signals: {', '.join(hits) or 'weak'}; aggregate penalties: {', '.join(penalties) or 'none'}; Jev metadata relevance: {decisions.get(d['id'], {}).get('probability', 'not scored: unsupported format')}",
                "catalogue_url": "https://data.gov.au/data/dataset/" + d["id"],
            }
        )
        store.put(
            "sources",
            d["id"],
            {
                "id": d["id"],
                "slug": d["name"],
                "metadata": d,
                "portal": "https://data.gov.au/data",
            },
            kind="catalogue",
        )
    ranked.sort(key=lambda r: (-r["confidence"], r["dataset_id"]))
    from .downloadability import POLICY, select_downloadable

    shortlist, download_checks = select_downloadable(ranked, datasets)
    audit = {
        "id": discovery_id,
        "experiment_id": settings().experiment_id,
        "triage_method": "Jev on all supported-format catalogue candidates; 0.5 rule score + 0.5 Jev probability; publisher cap 8; bounded GET and reader preflight; no audit labels supplied",
        "jev_candidates": len(decisions),
        "queries": queries,
        "unique_records": len(datasets),
        "publisher_cap": 8,
        "download_policy": POLICY,
        "download_checks_artifact": store.json_blob(
            download_checks, "download-checks.json"
        ),
        "shortlist": shortlist,
        "ranked": ranked,
        "retrieved_at": store.now(),
    }
    audit["catalogue_artifact"] = store.json_blob(
        list(datasets.values()), "catalogue.json"
    )
    store.put("batches", discovery_id, audit, kind="discovery")
    store.put("batches", "discovery", audit, kind="discovery")
    store.put(
        "batches",
        "discovery-current-" + audit["experiment_id"],
        audit,
        kind="discovery",
    )
    return audit


def register(request: SourceRequest):
    d = action(request.portal, "package_show", id=request.dataset_id)
    source = {"id": d["id"], "slug": d["name"], "metadata": d, "portal": request.portal}
    store.put("sources", d["id"], source, kind="registered")
    candidates = [r for r in d["resources"] if normal_format(r)]
    resource_id = request.resource_id
    if not resource_id:
        discovery = store.current_discovery(settings().experiment_id) or {}
        selected = next(
            (
                row
                for row in discovery.get("shortlist", [])
                if row["dataset_id"] == d["id"]
            ),
            {},
        )
        resource_id = selected.get("downloadability", {}).get("resource_id")
    if resource_id:
        candidates = [r for r in candidates if r["id"] == resource_id]
    if not candidates:
        raise ValueError("No supported downloadable CSV/TSV/XLSX/JSON resource")
    # Metadata resource order often includes an Excel equivalent before CSV. CSV is
    # preferred generically; Excel is used when that is the available data format.
    candidates.sort(key=lambda r: 0 if normal_format(r) == "csv" else 1)
    r = candidates[0]
    fmt = normal_format(r)
    data, receipt = download(
        r["url"], prefix=settings().csv_prefix_bytes if fmt == "csv" else None
    )
    artifact = store.blob(data, "application/octet-stream", r.get("name") or r["id"])
    snapshot_id = hashlib.sha256((d["id"] + r["id"] + artifact).encode()).hexdigest()
    existing = store.get("snapshots", snapshot_id)
    if existing:
        return source, existing
    documents = []
    for doc in [
        r for r in d["resources"] if r.get("format", "").lower().endswith("pdf")
    ][:2]:
        try:
            pdf, _ = download(doc["url"], maximum=15_000_000)
            pdf_id = store.blob(
                pdf, "application/pdf", doc.get("name", "publisher notes")
            )
            pages = [
                {"page": i + 1, "text": p.extract_text() or ""}
                for i, p in enumerate(PdfReader(io.BytesIO(pdf)).pages)
            ]
            documents.append({"url": doc["url"], "artifact_id": pdf_id, "pages": pages})
        except Exception as exc:  # noqa: BLE001 -- document retrieval failure is evidence
            documents.append({"url": doc["url"], "error": str(exc)[:400]})
    observed_at = r.get("last_modified")
    snapshot = {
        "id": snapshot_id,
        "source_id": d["id"],
        "resource_id": r["id"],
        "artifact_id": artifact,
        "sha256": artifact,
        "format": fmt,
        "receipt": receipt,
        "observed_at": observed_at,
        "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
        "licence": d.get("license_title") or "unknown",
        "licence_url": d.get("license_url"),
        "documentation": documents,
        "dataset_notes": d.get("notes") or "",
        "inspection": inspect_resource(
            store.blob_path(artifact), fmt, receipt["partial"]
        ),
    }
    store.put("snapshots", snapshot_id, snapshot, d["id"], "snapshot", immutable=True)
    return source, snapshot


def new_run(source, snapshot):
    from .ontology import active_hash

    run = {
        "id": str(uuid.uuid4()),
        "experiment_id": settings().experiment_id,
        "model": settings().model,
        "ontology_hash": active_hash(settings().experiment_id),
        "source_id": source["id"],
        "source_slug": source["slug"],
        "snapshot_id": snapshot["id"],
        "status": "new",
        "created_at": store.now(),
        "model_calls": 0,
        "python_calls": 0,
        "version": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "active_seconds": 0.0,
        "calculated_cost_usd": None,
        "pricing_basis": settings().pricing_basis,
    }
    store.put("runs", run["id"], run, source["id"], "onboarding")
    return run


def recheck_discovery(previous_id, revision_id):
    """Re-rank the saved catalogue with fresh download checks; no new model calls."""
    from .downloadability import POLICY, select_downloadable

    if store.get("batches", revision_id):
        raise ValueError("Revision ID already exists; choose a new ID")
    previous = store.require("batches", previous_id)
    datasets = {d["id"]: d for d in store.read_json(previous["catalogue_artifact"])}
    shortlist, checks = select_downloadable(previous["ranked"], datasets)
    audit = {
        **previous,
        "id": revision_id,
        "supersedes_discovery_id": previous_id,
        "shortlist": shortlist,
        "download_checked_at": store.now(),
        "download_policy": POLICY,
        "download_checks_artifact": store.json_blob(checks, "download-checks.json"),
        "triage_method": previous["triage_method"]
        + "; fresh bounded GET and reader gate",
        "rerun_model_calls": 0,
        "ranking_reuse": "Same saved catalogue and Jev metadata scores; isolates download gate; no evaluation labels used",
    }
    store.put("batches", revision_id, audit, kind="discovery", immutable=True)
    store.put("batches", "discovery", audit, kind="discovery")
    store.put(
        "batches",
        "discovery-current-" + audit["experiment_id"],
        audit,
        kind="discovery",
    )
    return audit
