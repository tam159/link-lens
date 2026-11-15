"""The admin API and the console's pages: `uvicorn link_lens.admin.app:app`.

Internal, separate from the product service (which only reads and answers
clients) and from `api.py` beside the LangGraph server. Every route under
`/admin` needs a signed-in person; the role a route needs is checked here, and
a change that is refused for its role is recorded. The pages under `/console`
are static files that call `/admin` and nothing else.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException

from .. import budget, logs, releases
from ..settings import settings
from . import audit, auth, service

SAFE = ("GET", "HEAD", "OPTIONS")
PROBLEM = "application/problem+json"


@asynccontextmanager
async def lifespan(app):
    logs.configure()
    yield


# No generated documentation: nothing about the API is served to someone not signed in.
app = FastAPI(
    lifespan=lifespan,
    title="Link Lens operations console",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


class Problem(Exception):
    def __init__(self, status, title, detail=None):
        super().__init__(title)
        self.status, self.title, self.detail = status, title, detail


def problem(status, title, detail=None):
    body = {"type": "about:blank", "title": title, "status": status}
    if detail:
        body["detail"] = detail
    return JSONResponse(body, status_code=status, media_type=PROBLEM)


@app.exception_handler(Problem)
async def known_problem(request: Request, error: Problem):
    return problem(error.status, error.title, error.detail)


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


@app.exception_handler(KeyError)
async def not_found(request: Request, error: KeyError):
    return problem(404, "Not found", str(error).strip("'\""))


@app.exception_handler(service.Refused)
@app.exception_handler(budget.BudgetExceeded)
async def refused(request: Request, error: Exception):
    return problem(409, "Refused", str(error))


@app.exception_handler(service.Unavailable)
async def unavailable(request: Request, error: service.Unavailable):
    return problem(503, "Not available", str(error))


@app.exception_handler(ValueError)
async def wrong(request: Request, error: ValueError):
    # The library's own refusals: a blocked step, a batch that cannot be released.
    return problem(400, "Cannot be done", str(error)[:600])


@app.exception_handler(RuntimeError)
async def failed(request: Request, error: RuntimeError):
    # A publisher or the onboarding server did not answer as needed.
    return problem(502, "A step failed", str(error)[:600])


@app.middleware("http")
async def headers(request: Request, call_next):
    response = await call_next(request)
    # An answer can hold a new key: nothing between here and the person keeps it.
    if request.url.path.startswith("/admin"):
        response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    )
    return response


# Signing in


def signed_in(request: Request) -> auth.Principal:
    header = request.headers.get("authorization", "")
    by_cookie = not header.lower().startswith("bearer ")
    token = request.cookies.get(auth.COOKIE) if by_cookie else header[7:].strip()
    principal = auth.authenticate(token)
    if principal is None:
        raise Problem(401, "Sign in")
    if (
        by_cookie
        and request.method not in SAFE
        and auth.CONSOLE_HEADER not in request.headers
    ):
        raise Problem(403, "Forbidden", "A change must come from the console itself")
    return principal


def needs(role, action=None):
    """A dependency that lets through only a person in `role` or above."""

    def check(request: Request, principal: auth.Principal = Depends(signed_in)):
        if not principal.may(role):
            if request.method not in SAFE:
                audit.refused(
                    principal,
                    action or request.method,
                    request.url.path,
                    f"needs the role {role}",
                )
            raise Problem(403, "Forbidden", f"This needs the role {role}")
        return principal

    return check


ENGINEER = Depends(needs("engineer"))


def langgraph():
    """The onboarding server a new source's run is started on."""
    from langgraph_sdk import get_sync_client

    return get_sync_client(url=settings().api_url)


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SignIn(Body):
    token: str


@app.post("/admin/session")
def sign_in(body: SignIn, request: Request, response: Response):
    principal = auth.authenticate(body.token)
    if principal is None:
        logs.event("console.sign_in_refused")
        raise Problem(401, "Sign in", "That token is not known")
    response.set_cookie(
        auth.COOKIE,
        body.token,
        httponly=True,
        samesite="strict",
        secure=request.url.scheme == "https",
        max_age=12 * 3600,
        path="/admin",
    )
    logs.event("console.sign_in", actor=principal.name, role=principal.role)
    return {"name": principal.name, "role": principal.role}


@app.delete("/admin/session")
def sign_out(response: Response):
    response.delete_cookie(auth.COOKIE, path="/admin")
    return {"signed_out": True}


@app.get("/admin/me")
def me(principal: auth.Principal = ENGINEER):
    return {"name": principal.name, "role": principal.role, "roles": auth.ROLES}


@app.get("/admin/home", dependencies=[ENGINEER])
def home():
    return service.home()


# Sources


class Dataset(Body):
    dataset_id: str = Field(min_length=1)
    resource_id: str | None = None


class NewSource(Dataset):
    confirm_paid_calls: bool = False


class SourceChange(Body):
    cadence_days: float | None = Field(None, gt=0)
    paused: bool | None = None


@app.get("/admin/catalogue", dependencies=[Depends(needs("product_owner"))])
def catalogue(q: str = "", limit: int = 50):
    return service.catalogue(q, max(1, min(limit, 200)))


@app.post("/admin/sources/preview", dependencies=[Depends(needs("product_owner"))])
def preview_source(body: Dataset):
    return service.source_preview(body.dataset_id, body.resource_id)


@app.post("/admin/sources", status_code=201)
def add_source(
    body: NewSource,
    principal: auth.Principal = Depends(needs("product_owner", "source.register")),
    client=Depends(langgraph),
):
    return service.add_source(
        principal, client, body.dataset_id, body.resource_id, body.confirm_paid_calls
    )


@app.patch("/admin/sources/{source_id}")
def update_source(
    source_id: str,
    body: SourceChange,
    principal: auth.Principal = Depends(needs("product_owner", "source.update")),
):
    return service.update_source(
        principal, source_id, body.model_dump(exclude_unset=True)
    )


@app.get("/admin/sources", dependencies=[ENGINEER])
def sources():
    return service.source_list()


@app.get("/admin/sources/{source_id}", dependencies=[ENGINEER])
def source(source_id: str):
    return service.source(source_id)


# Releases


class NewRelease(Body):
    batch_id: str = Field(min_length=1)
    notes: str | None = None


@app.get("/admin/releases", dependencies=[ENGINEER])
def release_list():
    return service.release_list()


@app.get("/admin/releases/preview", dependencies=[Depends(needs("product_owner"))])
def preview_release(batch_id: str):
    return releases.preview(batch_id)


@app.post("/admin/releases", status_code=201)
def create_release(
    body: NewRelease,
    principal: auth.Principal = Depends(needs("product_owner", "release.create")),
):
    return service.create_release(principal, body.batch_id, body.notes)


# Ontology, read-only


@app.get("/admin/ontology/versions", dependencies=[ENGINEER])
def ontology_versions():
    return service.ontology_versions()


# Clients, tiers and keys


class NewClient(Body):
    name: str = Field(min_length=1)
    tier_id: str


class ClientChange(Body):
    tier_id: str | None = None
    status: Literal["active", "suspended"] | None = None


class NewKey(Body):
    label: str | None = None
    expires_in_days: int | None = Field(None, gt=0)


class Tier(Body):
    rate_per_minute: int = Field(gt=0)
    monthly_quota: int | None = Field(None, gt=0)
    interfaces: list[str] = ["rest"]
    toolsets: list[str] = []
    source_scope: list[str] | None = None
    bundle_downloads: bool = False
    release_lag: int = Field(0, ge=0)
    history_depth: int | None = Field(None, ge=0)


@app.get("/admin/clients", dependencies=[Depends(needs("admin"))])
def clients():
    return service.access()


@app.post("/admin/clients", status_code=201)
def create_client(
    body: NewClient,
    principal: auth.Principal = Depends(needs("admin", "client.create")),
):
    return service.create_client(principal, body.name, body.tier_id)


@app.patch("/admin/clients/{client_id}")
def update_client(
    client_id: str,
    body: ClientChange,
    principal: auth.Principal = Depends(needs("admin", "client.update")),
):
    return service.update_client(
        principal, client_id, body.model_dump(exclude_unset=True)
    )


@app.post("/admin/clients/{client_id}/keys", status_code=201)
def issue_key(
    client_id: str,
    body: NewKey,
    principal: auth.Principal = Depends(needs("admin", "key.issue")),
):
    return service.issue_key(principal, client_id, body.label, body.expires_in_days)


@app.delete("/admin/keys/{prefix}")
def revoke_key(
    prefix: str, principal: auth.Principal = Depends(needs("admin", "key.revoke"))
):
    """Revokes: the key's row is kept and gets the time it was revoked."""
    return service.revoke_key(principal, prefix)


@app.put("/admin/tiers/{tier_id}")
def set_tier(
    tier_id: str,
    body: Tier,
    principal: auth.Principal = Depends(needs("admin", "tier.set")),
):
    return service.set_tier(principal, tier_id, body.model_dump())


@app.get("/admin/actions", dependencies=[Depends(needs("admin"))])
def actions(limit: int = 100, before: int | None = None):
    return audit.listing(max(1, min(limit, 500)), before)


# The pages


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/console/")


app.mount(
    "/console",
    StaticFiles(directory=Path(__file__).parent / "static", html=True),
    name="console",
)
