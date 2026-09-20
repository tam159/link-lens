"""Small local application API mounted beside Agent Server's thread/run API."""

from fastapi import FastAPI
from fastapi.responses import FileResponse
from . import store, ingestion, evaluation
from .contracts import SourceRequest, ReviewLabel, StrictModel

app = FastAPI(title="Link Lens application API")


@app.exception_handler(KeyError)
async def missing(request, exc):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.get("/api/health")
def health():
    with store.engine().connect() as conn:
        from sqlalchemy import text

        conn.execute(text("select 1"))
    return {"status": "ok"}


@app.post("/api/sources")
def register(body: SourceRequest):
    source, snapshot = ingestion.register(body)
    return ingestion.new_run(source, snapshot)


@app.get("/api/runs")
def runs():
    return store.listing("runs")


@app.get("/api/runs/{run_id}")
def run(run_id: str):
    value = store.require("runs", run_id)
    return {**value, "events": store.listing("events", owner=run_id)}


@app.get("/api/profiles")
def profiles(batch_id: str):
    return store.listing("profiles", owner=batch_id)


@app.get("/api/artifacts/{artifact_id}")
def artifact(artifact_id: str):
    meta = store.require("artifacts", artifact_id)
    headers = {"X-Content-Type-Options": "nosniff"}
    if meta["media_type"] == "text/html":
        # Viewer has inline bundled JS plus pinned CDN assets; isolated from API cookies.
        headers["Content-Security-Policy"] = (
            "sandbox allow-scripts allow-popups; default-src 'none'; script-src 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; style-src 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src data: https:; connect-src 'none'"
        )
    return FileResponse(
        store.blob_path(artifact_id), media_type=meta["media_type"], headers=headers
    )


class LabelImport(StrictModel):
    worksheet_id: str
    labels: list[ReviewLabel]


@app.post("/api/evaluations")
def labels(body: LabelImport):
    return evaluation.import_labels(
        body.worksheet_id, [l.model_dump() for l in body.labels]
    )


# The custom app middleware wraps Agent Server's routes as well as /api routes.
from .runtime_compat import (
    ResumeCompatibilityMiddleware,
    install_checkpoint_flush_guard,
)

install_checkpoint_flush_guard()
app.add_middleware(ResumeCompatibilityMiddleware)
