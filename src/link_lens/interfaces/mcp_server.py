"""MCP interface: `/mcp`, with `/mcp/data` and `/mcp/files` as narrower mounts.

Two toolsets over one query layer. Data tools answer in JSON; file tools walk the
OKF tree of the same release like a small file system and answer in Markdown.
Every tool is one call into `product.queries`: none writes, runs a command or
accepts SQL, and every result is bounded with a way to ask for the rest.

The same bearer key as REST applies to every HTTP request. A key's tier decides
which toolsets it is shown; a tool outside them does not exist for that key. A
tool call is counted under the `mcp` interface and is subject to the tier's rate
and monthly quota. Listing tools is not counted.

The server keeps no session: any instance can answer any request.
"""

import json
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from typing import Any

import anyio
import mcp.types as types
from jsonschema import Draft202012Validator
from mcp import MCPError
from mcp.server.lowlevel import Server
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse
from starlette.routing import Route

from ..product import Problem, auth, db, limits, models, queries
from ..settings import settings

INTERFACE = "mcp"
PROBLEM = "application/problem+json"
ENTITIES, OBSERVATIONS, ENTRIES, PAGES, MATCHES, LINES = 20, 25, 100, 50, 50, 400
BUDGET = 20_000  # characters of JSON in one page of a list; the rest is a cursor away
READ_ONLY = types.ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)
INSTRUCTIONS = """\
Link Lens holds evidence-backed profiles of businesses, built from public datasets.
Every value is a claim with a status and the source observations behind it.

Statuses: `selected` is the value chosen among the sources; `multiple_values` is a
field that keeps every value; `unresolved` means the sources disagree with equal
authority and no value was chosen, so report the alternatives instead of picking
one. Confidence numbers are uncalibrated judgements, not probabilities. An
identity link is a rule proposal until a person has reviewed it.

Data tools return JSON. File tools read the same release as Markdown pages:
start at `/index.md`. A data result names its page in `okf_path`, and a page
names its entity or observation ID in its frontmatter, so the two styles can be
mixed. Every result names the release it was answered from. When a result has
`next_cursor` or `next_offset`, call again with it to get the rest.
"""
CURSOR = {
    "type": "string",
    "description": "next_cursor of the previous result, to get the next page.",
}
PATH = {
    "type": "string",
    "description": "A path in the OKF tree, starting with /. Folders: /entities, "
    "/evidence, /sources, /ontology.",
}


def limit(maximum, default, what):
    return {
        "type": "integer",
        "minimum": 1,
        "maximum": maximum,
        "description": f"Most {what} to return. Default {default}.",
    }


def schema(properties, required=()):
    return {
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": False,
    }


@dataclass(frozen=True)
class Tool:
    name: str
    toolset: str
    title: str
    description: str
    arguments: dict
    answer: Any  # (connection, principal, release, **arguments) -> (structured, text)

    def definition(self):
        return types.Tool(
            name=self.name,
            title=self.title,
            description=self.description,
            input_schema=self.arguments,
            annotations=READ_ONLY,
        )


def as_json(structured):
    return json.dumps(structured, ensure_ascii=False, default=str)


def data(model, key=None, concepts=True):
    """Wrap a query so its answer passes the response model REST uses."""

    def wrap(query):
        def answer(connection, principal, release, **arguments):
            found = query(connection, principal, release, **arguments)
            names = queries.concept_names(connection, release) if concepts else None
            if key is None:
                checked = models.check(model, found, names).model_dump(mode="json")
            else:
                checked = {
                    key: [
                        item.model_dump(mode="json")
                        for item in models.check_all(model, found, names)
                    ]
                }
            structured = {"release": release["release_id"], **checked}
            return structured, as_json(structured)

        return answer

    return wrap


@data(models.EntityList, concepts=False)
def search_entities(connection, principal, release, **arguments):
    arguments.setdefault("limit", ENTITIES)
    return queries.search_entities(
        connection, principal, release, budget=BUDGET, **arguments
    )


@data(models.ProfileSummary)
def get_profile(connection, principal, release, entity_id):
    return queries.get_profile_summary(connection, principal, release, entity_id)


@data(models.ObservationList)
def list_observations(connection, principal, release, entity_id, **arguments):
    arguments.setdefault("limit", OBSERVATIONS)
    return queries.list_observations(
        connection, principal, release, entity_id, budget=BUDGET, **arguments
    )


@data(models.Evidence)
def get_evidence(connection, principal, release, observation_id):
    return queries.get_evidence(connection, principal, release, observation_id)


def describe_concepts(connection, principal, release, scope=None):
    """Definitions of one scope, or the scopes and their concept names."""
    found = queries.describe_concepts(connection, principal, release, scope=scope)
    names = queries.concept_names(connection, release)
    checked = models.check_all(models.ConceptDefinition, found, names)
    structured = {"release": release["release_id"]}
    if scope is None:
        scopes = {}
        for concept in checked:
            scopes.setdefault(concept.scope, []).append(concept.name)
        structured["scopes"] = [
            {"scope": name, "concepts": concepts} for name, concepts in scopes.items()
        ]
    else:
        structured["scope"] = scope
        structured["concepts"] = [c.model_dump(mode="json") for c in checked]
    return structured, as_json(structured)


def more(structured, key="next_cursor", argument="cursor"):
    following = structured.get(key)
    if following is None:
        return ""
    return f"\n[more: call again with {argument}={json.dumps(following)}]"


def okf_ls(connection, principal, release, path="/", cursor=None, limit=ENTRIES):
    found = queries.okf_ls(
        connection, principal, release, path, cursor=cursor, limit=limit
    )
    if not found["entries"] and found["path"] != "/" and cursor is None:
        raise queries.not_found(f"Folder {found['path']}")
    structured = {"release": release["release_id"], **found}
    lines = [
        entry["path"]
        + ("/" if entry["kind"] == "folder" else "")
        + (f"  ({entry['entries']} entries)" if entry.get("entries") else "")
        + (f"  {entry['title']}" if entry.get("title") else "")
        for entry in found["entries"]
    ]
    return structured, "\n".join(lines) + more(structured)


def okf_read(connection, principal, release, path, offset=0, limit=LINES):
    found = queries.okf_read(
        connection, principal, release, path, offset=offset, limit=limit
    )
    structured = {"release": release["release_id"], **found}
    note = ""
    if found["next_offset"] is not None:
        note = (
            f"\n[lines {found['offset']} to {found['next_offset'] - 1} of "
            f"{found['total_lines']}: call again with offset={found['next_offset']}]"
        )
    return structured, found["text"] + note


def okf_find(connection, principal, release, path="/", limit=PAGES, **filters):
    found = queries.okf_find(
        connection, principal, release, path, limit=limit, **filters
    )
    structured = {"release": release["release_id"], **found}
    lines = [
        "  ".join(
            str(part)
            for part in (page["path"], page["type"], page["status"], page["title"])
            if part
        )
        for page in found["pages"]
    ]
    return structured, "\n".join(lines) + more(structured)


def okf_grep(connection, principal, release, pattern, path, cursor=None, limit=MATCHES):
    found = queries.okf_grep(
        connection, principal, release, pattern, path, cursor=cursor, limit=limit
    )
    structured = {"release": release["release_id"], **found}
    lines = [f"{m['path']}:{m['line_no']}: {m['line']}" for m in found["matches"]]
    return structured, "\n".join(lines) + more(structured)


TOOLS = [
    Tool(
        "search_entities",
        "data",
        "Search entities",
        "Find businesses by any of name (part of the name, any case), ABN, ACN, "
        "state (such as NSW) and entity type. Identifiers match exactly, digits "
        "only. With no argument it lists every entity. Returns `entities` with "
        "`entity_id`, `display_name`, `identifiers`, `status` and `okf_path` (the "
        f"entity's page for okf_read), at most {ENTITIES} a page, and `next_cursor` "
        "when there are more. Use the `entity_id` with get_profile.",
        schema(
            {
                "name": {"type": "string", "description": "Part of the name."},
                "abn": {"type": "string", "description": "ABN, 11 digits."},
                "acn": {"type": "string", "description": "ACN, 9 digits."},
                "state": {"type": "string", "description": "State code, e.g. NSW."},
                "type": {"type": "string", "description": "Entity type, exact."},
                "cursor": CURSOR,
                "limit": limit(100, ENTITIES, "entities"),
            }
        ),
        search_entities,
    ),
    Tool(
        "get_profile",
        "data",
        "Get an entity's profile",
        "The profile of one entity: every field with its `status`, `value` (or "
        "`values` for a multi-valued field), the `decision` that explains the "
        "choice, `alternatives` that were not chosen, and `evidence`, the "
        "observations behind it by `observation_id`. `addresses` and `groups` "
        "(such as one licence) are claims that one source record makes together. "
        "`sources` gives the licence of every source cited. Pass an "
        "`observation_id` to get_evidence for the source record. A field with "
        f"many values lists the first {queries.SHOWN} and gives `values_total`; "
        "list_observations with that concept returns all of them. Status "
        "`unresolved` means no value was chosen: report the alternatives.",
        schema(
            {
                "entity_id": {
                    "type": "string",
                    "description": "From search_entities or a page's frontmatter.",
                }
            },
            ["entity_id"],
        ),
        get_profile,
    ),
    Tool(
        "list_observations",
        "data",
        "List an entity's source claims",
        "Every claim that the sources make about one entity, selected or not, "
        "optionally for one concept (such as entity.legal_name). Each has its "
        "`value`, `raw_value` as published, `source_id`, `observed_at` with "
        "`timestamp_basis` (`record`: the source states the date; `snapshot`: the "
        "date the dataset was published, which does not say when the value "
        f"changed) and `licence`. At most {OBSERVATIONS} a page, fewer when the "
        "values are long, with `next_cursor`.",
        schema(
            {
                "entity_id": {"type": "string"},
                "concept": {
                    "type": "string",
                    "description": "A concept name from describe_concepts.",
                },
                "cursor": CURSOR,
                "limit": limit(100, OBSERVATIONS, "observations"),
            },
            ["entity_id"],
        ),
        list_observations,
    ),
    Tool(
        "get_evidence",
        "data",
        "Get the evidence for one claim",
        "Where one observation came from: the `record` with its row locator in "
        "the source file, the `snapshot` of the dataset with when it was "
        "retrieved, the `source` with title and publisher, and the `licence` to "
        "attribute. Use it to cite a value from get_profile or list_observations.",
        schema(
            {
                "observation_id": {
                    "type": "string",
                    "description": "An observation_id from a profile's evidence "
                    "or from list_observations.",
                }
            },
            ["observation_id"],
        ),
        get_evidence,
    ),
    Tool(
        "describe_concepts",
        "data",
        "Describe ontology concepts",
        "What the field names mean. With no argument: the scopes (entity, "
        "address, licence, ...) and the concept names in each. With `scope`: the "
        "definition, datatype, cardinality (`one` or `many`) and allowed values "
        "of every concept in that scope.",
        schema({"scope": {"type": "string", "description": "A scope name."}}),
        describe_concepts,
    ),
    Tool(
        "okf_ls",
        "files",
        "List a folder",
        "List a folder of the OKF tree, like `ls`. Start at `/`. Folders end "
        "with `/` and show how many entries they hold; `index.md` in a folder is "
        "a page that links to its entries. Entities are under /entities (browse "
        "by-name, by-state, by-type or by-source), cited observations under "
        f"/evidence, sources under /sources, concepts under /ontology. {ENTRIES} "
        "entries a call, with `next_cursor`.",
        schema(
            {"path": PATH, "cursor": CURSOR, "limit": limit(200, ENTRIES, "entries")}
        ),
        okf_ls,
    ),
    Tool(
        "okf_read",
        "files",
        "Read a page",
        "Read one page as Markdown, like `cat`. An entity page has the profile: "
        "each field with its status, value and links to its evidence pages. An "
        "evidence page has one observation with its source record, snapshot and "
        "licence. Frontmatter gives the page's type, status and the entity or "
        f"observation ID, usable with the data tools. Returns {LINES} lines from "
        "`offset`; when the page is longer, the result gives `next_offset`.",
        schema(
            {
                "path": {**PATH, "description": "Path of a page, ending in .md."},
                "offset": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "First line to return, counted from 0.",
                },
                "limit": limit(1000, LINES, "lines"),
            },
            ["path"],
        ),
        okf_read,
    ),
    Tool(
        "okf_find",
        "files",
        "Find pages by frontmatter",
        "Find pages under a folder by what their frontmatter says, like `find`. "
        "`type` is the page type (entity, evidence, source, concept), `status` "
        "the profile or claim status, `tags` a list that must all be present. "
        f"Returns path, type, status and title of each page, {PAGES} a call, "
        "with `next_cursor`. Use okf_grep to search for a value instead.",
        schema(
            {
                "path": PATH,
                "type": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "status": {"type": "string"},
                "cursor": CURSOR,
                "limit": limit(200, PAGES, "pages"),
            }
        ),
        okf_find,
    ),
    Tool(
        "okf_grep",
        "files",
        "Search page text",
        "Search under a folder with a regular expression, like `grep -rn`. It "
        "searches each page's frontmatter and its claims, written one a line as "
        "`concept: value` (for example `entity.abn: 51824753556`), not the "
        "prose. A folder below the root is required, such as /entities or "
        f"/evidence. Returns `path:line: text` for each match, {MATCHES} a call, "
        "with `next_cursor`. Read a matching page with okf_read.",
        schema(
            {
                "pattern": {
                    "type": "string",
                    "description": "A POSIX regular expression, case-sensitive.",
                },
                "path": PATH,
                "cursor": CURSOR,
                "limit": limit(200, MATCHES, "matches"),
            },
            ["pattern", "path"],
        ),
        okf_grep,
    ),
]
VALIDATORS = {tool.name: Draft202012Validator(tool.arguments) for tool in TOOLS}


def shown(principal, toolsets):
    """The tools of this endpoint that the key's tier includes, by name."""
    allowed = principal.toolsets & frozenset(toolsets)
    return {tool.name: tool for tool in TOOLS if tool.toolset in allowed}


def failure(problem):
    """A refusal the agent can read and act on, as a tool result."""
    error = {"status": problem.status, "title": problem.title}
    text = problem.title
    if problem.detail:
        error["detail"] = problem.detail
        text += ": " + problem.detail
    if problem.retry_after is not None:
        error["retry_after_seconds"] = problem.retry_after
        text += f" Retry after {problem.retry_after} seconds."
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        structured_content={"error": error},
        is_error=True,
    )


def run(tool, principal, arguments):
    """Count the call, then answer it. Runs in a worker thread."""
    try:
        # Counting is committed on its own, so it stands if the call then fails.
        with db.session() as connection:
            limits.enforce(connection, principal, INTERFACE)
        errors = sorted(VALIDATORS[tool.name].iter_errors(arguments), key=str)
        if errors:
            where = ".".join(str(part) for part in errors[0].path)
            raise Problem(
                400,
                "Invalid arguments",
                (where + ": " if where else "") + errors[0].message,
            )
        with db.session() as connection:
            release = queries.resolve_release(connection, principal)
            structured, text = tool.answer(connection, principal, release, **arguments)
    except Problem as problem:
        return failure(problem)
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        structured_content=structured,
    )


def build(name, toolsets):
    """An MCP server that offers `toolsets` to keys whose tier includes them."""

    async def list_tools(ctx, params):
        tools = shown(ctx.request.state.principal, toolsets)
        return types.ListToolsResult(
            tools=[tool.definition() for tool in tools.values()]
        )

    async def call_tool(ctx, params):
        principal = ctx.request.state.principal
        tool = shown(principal, toolsets).get(params.name)
        if tool is None:
            raise MCPError(types.INVALID_PARAMS, f"Unknown tool: {params.name}")
        return await anyio.to_thread.run_sync(
            run, tool, principal, dict(params.arguments or {})
        )

    return Server(
        name,
        version="1",
        title="Link Lens",
        instructions=INSTRUCTIONS,
        # The schema of a tool does not depend on the caller, so header
        # validation need not list the tools.
        get_tool_input_schema=lambda tool: (
            VALIDATORS[tool].schema if tool in VALIDATORS else None
        ),
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )


def refusal(problem):
    body = {"type": "about:blank", "title": problem.title, "status": problem.status}
    if problem.detail:
        body["detail"] = problem.detail
    headers = {"WWW-Authenticate": "Bearer"} if problem.status == 401 else {}
    return JSONResponse(body, problem.status, headers=headers, media_type=PROBLEM)


def principal_for(authorization, toolsets):
    with db.session() as connection:
        principal = auth.authenticate(connection, authorization, INTERFACE)
    if not principal.toolsets & frozenset(toolsets):
        raise Problem(
            403,
            "Toolset not in tier",
            "This tier does not include " + " or ".join(sorted(toolsets)) + " tools.",
        )
    return principal


class Endpoint:
    """One MCP mount: checks the key, then hands the request to the MCP server.

    The server and its session manager are made when the app starts, because a
    manager runs once; a test that starts the app again gets new ones.
    """

    def __init__(self, path, toolsets):
        self.path, self.toolsets, self.manager = path, toolsets, None

    @asynccontextmanager
    async def running(self):
        server = build("link-lens" + self.path.replace("/", "-"), self.toolsets)
        hosts = list(settings().mcp_allowed_hosts)
        server.streamable_http_app(
            streamable_http_path="/",
            json_response=True,
            stateless_http=True,
            # A browser page cannot call this server on a user's behalf: every
            # request needs a key that only the client holds.
            transport_security=TransportSecuritySettings(
                enable_dns_rebinding_protection=bool(hosts),
                allowed_hosts=hosts + [host + ":*" for host in hosts],
            ),
        )
        self.manager = server.session_manager
        try:
            async with self.manager.run():
                yield
        finally:
            self.manager = None

    async def __call__(self, scope, receive, send):
        if self.manager is None:
            await refusal(Problem(503, "MCP is not started"))(scope, receive, send)
            return
        headers = {name: value for name, value in scope["headers"]}
        authorization = headers.get(b"authorization", b"").decode("latin-1")
        try:
            principal = await anyio.to_thread.run_sync(
                principal_for, authorization, self.toolsets
            )
        except Problem as problem:
            await refusal(problem)(scope, receive, send)
            return
        scope.setdefault("state", {})["principal"] = principal
        await self.manager.handle_request(scope, receive, send)


ENDPOINTS = [
    Endpoint("/mcp", ("data", "files")),
    Endpoint("/mcp/data", ("data",)),
    Endpoint("/mcp/files", ("files",)),
]
routes = [Route(endpoint.path, endpoint=endpoint) for endpoint in ENDPOINTS]


@asynccontextmanager
async def running():
    """Every endpoint's server, running for as long as the app does."""
    async with AsyncExitStack() as stack:
        for endpoint in ENDPOINTS:
            await stack.enter_async_context(endpoint.running())
        yield
