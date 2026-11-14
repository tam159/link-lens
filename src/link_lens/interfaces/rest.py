"""REST interface: `/v1`. Every route is one call into the query layer.

Conventions: a bearer key on every call; `?release=` to read an older release
the key may see; `X-LinkLens-Release` on every answer; keyset cursors; problem
details for errors; `Accept: text/markdown` on an entity route returns its OKF
page.
"""

from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from sqlalchemy.engine import Connection

from ..okf import render
from ..product import auth, db, limits, models, queries

INTERFACE = "rest"
router = APIRouter(prefix="/v1")
MARKDOWN = "text/markdown"


@dataclass
class Call:
    """What a route works with: a connection, who is calling, and the release."""

    connection: Connection
    principal: auth.Principal
    release: dict
    response: Response

    @property
    def concepts(self):
        return queries.concept_names(self.connection, self.release)

    def ask(self, query, *arguments, **options):
        return query(
            self.connection, self.principal, self.release, *arguments, **options
        )


def call(
    response: Response,
    authorization: Annotated[str | None, Header()] = None,
    release: Annotated[
        int | None,
        Query(description="A release this key may see; the current one by default."),
    ] = None,
):
    # Counting the call is committed on its own, so it stands even if the
    # request then fails.
    with db.session() as connection:
        principal = auth.authenticate(connection, authorization, INTERFACE)
        limits.enforce(connection, principal, INTERFACE)
    with db.session() as connection:
        chosen = queries.resolve_release(connection, principal, release)
        response.headers[RELEASE_HEADER] = str(chosen["release_id"])
        yield Call(connection, principal, chosen, response)


RELEASE_HEADER = "X-LinkLens-Release"
Caller = Annotated[Call, Depends(call)]
Cursor = Annotated[str | None, Query(description="next_cursor of the previous page.")]
Limit = Annotated[int | None, Query(ge=1, le=queries.MAX_LIMIT)]


def wants_markdown(request):
    return MARKDOWN in request.headers.get("accept", "")


def markdown(caller, path, **headers):
    page = caller.ask(queries.okf_read, path)
    return Response(
        page["text"],
        media_type=MARKDOWN,
        headers={RELEASE_HEADER: str(caller.release["release_id"]), **headers},
    )


@router.get("/entities", response_model=models.EntityList)
def entities(
    caller: Caller,
    name: str | None = None,
    abn: str | None = None,
    acn: str | None = None,
    state: str | None = None,
    type: str | None = None,
    cursor: Cursor = None,
    limit: Limit = None,
):
    """Entities matching any of name, ABN, ACN, state and entity type."""
    found = caller.ask(
        queries.search_entities,
        name=name,
        abn=abn,
        acn=acn,
        state=state,
        type=type,
        cursor=cursor,
        limit=limit,
    )
    return models.check(models.EntityList, found)


@router.get("/entities/{entity_id}", response_model=models.Entity)
def entity(caller: Caller, entity_id: str, request: Request):
    """An entity with its identifiers and the path of its OKF page."""
    found = caller.ask(queries.get_entity, entity_id)
    if wants_markdown(request):
        return markdown(caller, found["okf_path"])
    return models.check(models.Entity, found)


@router.get("/entities/{entity_id}/profile", response_model=models.Profile)
def profile(
    caller: Caller,
    entity_id: str,
    request: Request,
    if_none_match: Annotated[str | None, Header()] = None,
):
    """Profile fields with status, evidence and alternatives. `ETag` is the profile version."""
    found = caller.ask(queries.get_profile, entity_id)
    etag = f'"{found["profile_version"]}"'
    headers = {"ETag": etag, RELEASE_HEADER: str(caller.release["release_id"])}
    if if_none_match == etag:
        return Response(status_code=304, headers=headers)
    if wants_markdown(request):
        return markdown(caller, found["okf_path"], ETag=etag)
    caller.response.headers["ETag"] = etag
    return models.check(models.Profile, found, caller.concepts)


@router.get("/entities/{entity_id}/observations", response_model=models.ObservationList)
def observations(
    caller: Caller,
    entity_id: str,
    concept: str | None = None,
    source: str | None = None,
    cursor: Cursor = None,
    limit: Limit = None,
):
    """Source claims about an entity, each with its licence and timestamp basis."""
    found = caller.ask(
        queries.list_observations,
        entity_id,
        concept=concept,
        source=source,
        cursor=cursor,
        limit=limit,
    )
    return models.check(models.ObservationList, found, caller.concepts)


@router.get("/entities/{entity_id}/links", response_model=list[models.Link])
def links(caller: Caller, entity_id: str):
    """Identity links behind an entity, with rule, score kind and review status."""
    return models.check_all(models.Link, caller.ask(queries.list_links, entity_id))


@router.get("/observations/{observation_id}", response_model=models.Evidence)
def observation(caller: Caller, observation_id: str):
    """One claim with its record locator, snapshot, source and licence."""
    found = caller.ask(queries.get_evidence, observation_id)
    return models.check(models.Evidence, found, caller.concepts)


@router.get("/sources", response_model=list[models.Source])
def sources(caller: Caller):
    """Sources of the release that this key may see, with their licences."""
    return models.check_all(models.Source, caller.ask(queries.list_sources))


@router.get("/sources/{source_id}", response_model=models.Source)
def source(caller: Caller, source_id: str):
    return models.check(models.Source, caller.ask(queries.get_source, source_id))


@router.get("/ontology/concepts", response_model=list[models.ConceptDefinition])
def concepts(caller: Caller, scope: str | None = None):
    """Concepts of the ontology version the release was made under."""
    found = caller.ask(queries.describe_concepts, scope=scope)
    return models.check_all(models.ConceptDefinition, found, caller.concepts)


@router.get("/releases", response_model=list[models.Release])
def releases(caller: Caller):
    """Releases this key may see, newest first."""
    found = queries.list_releases(caller.connection, caller.principal)
    return models.check_all(models.Release, found)


@router.get("/releases/current", response_model=models.Release)
def current_release(caller: Caller):
    found = queries.list_releases(caller.connection, caller.principal)
    return models.check(models.Release, found[0])


@router.get("/okf", response_model=dict[str, Any])
@router.get("/okf/{path:path}", response_model=dict[str, Any])
def okf(caller: Caller, path: str = "", cursor: str | None = None, limit: Limit = None):
    """One OKF page as Markdown, or the listing of a folder as JSON."""
    path = "/" + path.strip("/")
    if path.endswith(".md"):
        return markdown(caller, path)
    listing = caller.ask(queries.okf_ls, path, cursor=cursor, limit=limit)
    if not listing["entries"] and path != "/":
        raise queries.not_found(f"Folder {path}")
    listing["index"] = render.index_path(path)
    return listing
