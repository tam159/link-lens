"""The product service: `uvicorn link_lens.product.app:app`.

Read-only, separate from the pipeline and the review tools, and connected as
the product database role. It is not mounted in `langgraph.json`.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from ..interfaces import rest
from . import Problem

app = FastAPI(
    title="Link Lens",
    version="1",
    description=(
        "Evidence-backed profiles of public business data. Every answer carries "
        "its status, provenance, alternatives, score kind, timestamp basis and licence."
    ),
)
app.include_router(rest.router)
PROBLEM = "application/problem+json"


def problem(status, title, detail=None, headers=None):
    body = {"type": "about:blank", "title": title, "status": status}
    if detail:
        body["detail"] = detail
    return JSONResponse(body, status_code=status, media_type=PROBLEM, headers=headers)


@app.exception_handler(Problem)
async def known_problem(request: Request, error: Problem):
    headers = {"WWW-Authenticate": "Bearer"} if error.status == 401 else {}
    if error.retry_after is not None:
        headers["Retry-After"] = str(error.retry_after)
    return problem(error.status, error.title, error.detail, headers)


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, error: RequestValidationError):
    detail = "; ".join(
        f"{'.'.join(str(part) for part in item['loc'][1:])}: {item['msg']}"
        for item in error.errors()
    )
    return problem(422, "Invalid request", detail)


@app.exception_handler(HTTPException)
async def http_problem(request: Request, error: HTTPException):
    return problem(error.status_code, str(error.detail))


@app.get("/health", include_in_schema=False)
def health():
    """Whether the service is up. No key needed; says nothing about data."""
    return {"status": "ok"}
