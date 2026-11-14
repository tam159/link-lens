"""Ten fixed tasks, run once with each MCP toolset, by a scripted agent.

    LINK_LENS_API_KEY=ll_... uv run python scripts/mcp_agent_eval.py \\
        --url http://localhost:8100 --output outputs/local-run/mcp-eval.json

The client is given only a URL and a key. Each task has two plans: one that uses
only the data tools and reads their JSON, and one that uses only the file tools
and reads their Markdown, as an agent with that toolset would. A task succeeds
when both plans reach the same answer. The record says, per task and toolset,
the answer and how many tool calls it took.

No model is called: the plans are written out below, so a run costs nothing and
gives the same result every time. It shows that each task can be done with
either toolset and what it costs in calls. It does not show how well a given
model picks tools from their descriptions; that needs a model-driven run.

Reads only. Exit code 0 when every task agrees, 1 otherwise.
"""

import argparse
import asyncio
import json
import os
import re
import sys
from contextlib import asynccontextmanager

import httpx2
import yaml
from mcp import Client
from mcp.client.streamable_http import streamable_http_client


class Agent:
    """A client of one toolset that counts the calls it makes."""

    def __init__(self, session, sleep=asyncio.sleep):
        self.session, self.sleep, self.calls = session, sleep, 0

    async def call(self, tool, **arguments):
        """The result of a tool call: its structured content and its text."""
        while True:
            self.calls += 1
            result = await self.session.call_tool(tool, arguments)
            text = "".join(part.text for part in result.content)
            if not result.is_error:
                return result.structured_content, text
            error = (result.structured_content or {}).get("error", {})
            wait = error.get("retry_after_seconds")
            if error.get("status") != 429 or wait is None or wait > 90:
                raise RuntimeError(f"{tool}: {text}")
            await self.sleep(wait)

    async def page(self, path):
        """A whole page as text, read in as many calls as it needs."""
        text, offset = "", 0
        while offset is not None:
            part, _ = await self.call("okf_read", path=path, offset=offset)
            text, offset = text + part["text"], part["next_offset"]
        return text

    async def profile_page(self, subject):
        """The entity's page: its frontmatter and the profile it carries."""
        text = await self.page(subject["okf_path"])
        return frontmatter(text), block(text)


def frontmatter(text):
    return yaml.safe_load(text.split("---\n")[1])


def block(text):
    """The JSON a page carries in its first fenced block."""
    return json.loads(re.search(r"```json\n(.*?)\n```", text, re.S).group(1))


def page_id(path):
    return path.rsplit("/", 1)[1].removesuffix(".md")


def evidence_path(observation_id):
    return f"/evidence/{observation_id[:2]}/{observation_id}.md"


def unsettled(fields):
    """The first field by name that is not simply selected, else the first field.

    By name, because the two styles list a profile's fields in different orders.
    """
    fields = sorted(fields)
    for name, status in fields:
        if status != "selected":
            return name
    return fields[0][0]


# Each task: a question, and how to answer it with each toolset.


async def find_by_abn_data(agent, subject):
    found, _ = await agent.call("search_entities", abn=subject["abn"])
    entity = found["entities"][0]
    return {"entity_id": entity["entity_id"], "name": entity["display_name"]}


async def find_by_abn_files(agent, subject):
    pattern = f"^entity\\.abn: {subject['abn']}$"
    found, _ = await agent.call("okf_grep", pattern=pattern, path="/entities")
    path = found["matches"][0]["path"]
    pattern = "^(entity_id|entity\\.legal_name): "
    lines, _ = await agent.call(
        "okf_grep", pattern=pattern, path=path.rsplit("/", 1)[0]
    )
    stated = {
        m["line"].split(": ", 1)[0]: m["line"].split(": ", 1)[1]
        for m in lines["matches"]
        if m["path"] == path
    }
    return {"entity_id": stated["entity_id"], "name": stated["entity.legal_name"]}


async def find_by_name_data(agent, subject):
    ids, cursor = [], None
    while True:
        arguments = {"name": subject["word"], "limit": 100}
        found, _ = await agent.call(
            "search_entities", **arguments, **({"cursor": cursor} if cursor else {})
        )
        ids += [entity["entity_id"] for entity in found["entities"]]
        cursor = found["next_cursor"]
        if not cursor:
            return {"entities": sorted(ids)}


async def find_by_name_files(agent, subject):
    pattern = "(?i)^entity\\.legal_name: .*" + re.escape(subject["word"])
    ids, cursor = set(), None
    while True:
        found, _ = await agent.call(
            "okf_grep",
            pattern=pattern,
            path="/entities",
            limit=200,
            **({"cursor": cursor} if cursor else {}),
        )
        ids |= {page_id(match["path"]) for match in found["matches"]}
        cursor = found["next_cursor"]
        if not cursor:
            return {"entities": sorted(ids)}


async def cite_legal_name_data(agent, subject):
    profile, _ = await agent.call("get_profile", entity_id=subject["entity_id"])
    field = next(f for f in profile["fields"] if f["concept"] == "entity.legal_name")
    cited = []
    for entry in field["evidence"]:
        evidence, _ = await agent.call(
            "get_evidence", observation_id=entry["observation_id"]
        )
        cited.append(
            {
                "observation_id": entry["observation_id"],
                "source": evidence["source"]["title"],
                "licence": evidence["licence"],
                "row": evidence["record"]["locator"].get("row"),
            }
        )
    return {"value": field["value"], "cited": sorted(cited, key=json.dumps)}


async def cite_legal_name_files(agent, subject):
    _, profile = await agent.profile_page(subject)
    field = profile["fields"]["entity.legal_name"]
    cited = []
    for entry in field["provenance"]:
        claim = block(await agent.page(evidence_path(entry["id"])))
        source = frontmatter(await agent.page(f"/sources/{claim['source_id']}.md"))
        cited.append(
            {
                "observation_id": entry["id"],
                "source": source["title"],
                "licence": claim["licence"],
                "row": claim["raw_locator"].get("row"),
            }
        )
    return {"value": field["value"], "cited": sorted(cited, key=json.dumps)}


async def source_licences_data(agent, subject):
    profile, _ = await agent.call("get_profile", entity_id=subject["entity_id"])
    return {
        "licences": sorted([s["source_id"], s["licence"]] for s in profile["sources"])
    }


async def source_licences_files(agent, subject):
    front, _ = await agent.profile_page(subject)
    licences = []
    for source in front["sources"]:
        path = "/sources/" + source["resource"].rsplit("/", 1)[1]
        text = await agent.page(path)
        licence = re.search(r"^Licence: (.*)\.$", text, re.M).group(1)
        licences.append([page_id(path), licence])
    return {"licences": sorted(licences)}


def explained(name, field):
    listed = field.get("values") or field.get("alternatives") or []
    return {
        "concept": name,
        "status": field["status"],
        "decision": field.get("decision"),
        "values": field.get("values_total", len(listed)),
    }


async def explain_field_data(agent, subject):
    profile, _ = await agent.call("get_profile", entity_id=subject["entity_id"])
    fields = {f["concept"]: f for f in profile["fields"]}
    name = unsettled([(n, f["status"]) for n, f in fields.items()])
    field = fields[name]
    count = field["values_total"]
    if count is None:
        count = field["alternatives_total"]
    return {**explained(name, field), "values": count}


async def explain_field_files(agent, subject):
    _, profile = await agent.profile_page(subject)
    name = unsettled([(n, f["status"]) for n, f in profile["fields"].items()])
    return explained(name, profile["fields"][name])


async def profile_status_data(agent, subject):
    profile, _ = await agent.call("get_profile", entity_id=subject["entity_id"])
    return {key: profile[key] for key in ("status", "profile_version", "uncertainties")}


async def profile_status_files(agent, subject):
    _, profile = await agent.profile_page(subject)
    return {key: profile[key] for key in ("status", "profile_version", "uncertainties")}


async def address_state_data(agent, subject):
    profile, _ = await agent.call("get_profile", entity_id=subject["entity_id"])
    states = []
    for address in profile["addresses"]:
        fields = {f["concept"]: f["value"] for f in address["fields"]}
        states.append([address["role"], fields.get("address.state")])
    return {"addresses": states}


async def address_state_files(agent, subject):
    _, profile = await agent.profile_page(subject)
    return {
        "addresses": [
            [a.get("role"), a["fields"].get("address.state", {}).get("value")]
            for a in profile.get("addresses") or []
        ]
    }


async def concept_meaning_data(agent, subject):
    described, _ = await agent.call("describe_concepts", scope="entity")
    concept = next(c for c in described["concepts"] if c["name"] == "entity.abn")
    return {key: concept[key] for key in ("definition", "datatype", "cardinality")}


async def concept_meaning_files(agent, subject):
    text = await agent.page("/ontology/entity/entity.abn.md")
    body = text.split("---\n", 2)[2]
    return {
        "definition": re.search(r"# Definition\n\n(.*?)\n\n", body, re.S).group(1),
        "datatype": re.search(r"^\* Type: (.*)$", body, re.M).group(1),
        "cardinality": re.search(r"^\* Cardinality: (.*)$", body, re.M).group(1),
    }


async def raw_value_data(agent, subject):
    profile, _ = await agent.call("get_profile", entity_id=subject["entity_id"])
    field = next(f for f in profile["fields"] if f["concept"] == "entity.abn")
    observation_id = sorted(e["observation_id"] for e in field["evidence"])[0]
    evidence, _ = await agent.call("get_evidence", observation_id=observation_id)
    return {
        "observation_id": observation_id,
        "raw_value": evidence["observation"]["raw_value"],
        "source_fields": evidence["observation"]["source_fields"],
        "row": evidence["record"]["locator"].get("row"),
    }


async def raw_value_files(agent, subject):
    _, profile = await agent.profile_page(subject)
    cited = profile["fields"]["entity.abn"]["provenance"]
    observation_id = sorted(entry["id"] for entry in cited)[0]
    claim = block(await agent.page(evidence_path(observation_id)))
    return {
        "observation_id": observation_id,
        "raw_value": claim["raw_value"],
        "source_fields": claim["source_fields"],
        "row": claim["raw_locator"].get("row"),
    }


async def count_entities_data(agent, subject):
    count, cursor = 0, None
    while True:
        found, _ = await agent.call(
            "search_entities", limit=100, **({"cursor": cursor} if cursor else {})
        )
        count, cursor = count + len(found["entities"]), found["next_cursor"]
        if not cursor:
            return {"entities": count}


async def count_entities_files(agent, subject):
    count, cursor = 0, None
    while True:
        found, _ = await agent.call(
            "okf_find",
            path="/entities",
            type="Business Profile",
            limit=200,
            **({"cursor": cursor} if cursor else {}),
        )
        count, cursor = count + len(found["pages"]), found["next_cursor"]
        if not cursor:
            return {"entities": count}


TASKS = [
    ("Find a company by its ABN", find_by_abn_data, find_by_abn_files),
    ("Find companies by part of a name", find_by_name_data, find_by_name_files),
    ("Cite the source of its legal name", cite_legal_name_data, cite_legal_name_files),
    ("List the licence of each source", source_licences_data, source_licences_files),
    ("Explain a field that is not settled", explain_field_data, explain_field_files),
    (
        "State the profile's status and caveats",
        profile_status_data,
        profile_status_files,
    ),
    ("Give the state of each address", address_state_data, address_state_files),
    ("Say what a concept means", concept_meaning_data, concept_meaning_files),
    ("Give the raw value behind its ABN", raw_value_data, raw_value_files),
    ("Count the entities of the release", count_entities_data, count_entities_files),
]


async def attempt(plan, agent, subject):
    before = agent.calls
    try:
        answer, error = await plan(agent, subject), None
    except Exception as failure:  # a plan that cannot finish is a failed task
        answer, error = None, f"{type(failure).__name__}: {failure}"
    return {"answer": answer, "calls": agent.calls - before, "error": error}


async def evaluate(connect, abn=None, sleep=asyncio.sleep):
    """Run every task with each toolset. `connect(path)` yields an MCP session."""
    async with connect("/mcp/data") as data, connect("/mcp/files") as files:
        tools = {
            "data": sorted(t.name for t in (await data.list_tools()).tools),
            "files": sorted(t.name for t in (await files.list_tools()).tools),
        }
        data, files = Agent(data, sleep), Agent(files, sleep)
        # The subject is an entity with a name and an ABN: the one asked for, or
        # the first of the release.
        found, _ = await data.call(
            "search_entities", limit=100, **({"abn": abn} if abn else {})
        )
        entity = next(
            e
            for e in found["entities"]
            if e["identifiers"].get("entity.abn") and e["display_name"]
        )
        words = re.findall(r"[A-Za-z]{4,}", entity["display_name"] or "")
        subject = {
            "abn": entity["identifiers"]["entity.abn"],
            "entity_id": entity["entity_id"],
            "okf_path": entity["okf_path"],
            "word": max(words, key=len) if words else "a",
        }
        tasks = []
        for title, with_data, with_files in TASKS:
            by_data = await attempt(with_data, data, subject)
            by_files = await attempt(with_files, files, subject)
            agree = by_data["error"] is None and by_data["answer"] == by_files["answer"]
            tasks.append(
                {"task": title, "agree": agree, "data": by_data, "files": by_files}
            )
        return {
            "release": found["release"],
            "agent": "scripted plans, no model",
            "tools": tools,
            "subject": {key: subject[key] for key in ("abn", "entity_id", "word")},
            "tasks": tasks,
            "summary": {
                "tasks": len(tasks),
                "agreed": sum(task["agree"] for task in tasks),
                "calls": {
                    kind: sum(task[kind]["calls"] for task in tasks)
                    for kind in ("data", "files")
                },
            },
        }


def over_http(url, key):
    @asynccontextmanager
    async def connect(path):
        headers = {"Authorization": "Bearer " + key}
        async with httpx2.AsyncClient(headers=headers, timeout=60) as http:
            transport = streamable_http_client(url.rstrip("/") + path, http_client=http)
            async with Client(transport) as session:
                yield session

    return connect


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--url", default="http://localhost:8100")
    parser.add_argument(
        "--abn", help="The entity to ask about; the first one by default."
    )
    parser.add_argument("--output", help="Write the full record here as JSON.")
    arguments = parser.parse_args()
    key = os.environ.get("LINK_LENS_API_KEY")
    if not key:
        sys.exit("Set LINK_LENS_API_KEY to a key whose tier includes both toolsets.")
    record = asyncio.run(evaluate(over_http(arguments.url, key), arguments.abn))
    record["url"] = arguments.url
    if arguments.output:
        with open(arguments.output, "w") as file:
            json.dump(record, file, indent=2, ensure_ascii=False)
            file.write("\n")
    for task in record["tasks"]:
        print(
            f"{'ok  ' if task['agree'] else 'FAIL'} {task['task']}: "
            f"data {task['data']['calls']} calls, files {task['files']['calls']} calls"
        )
    print(json.dumps(record["summary"]))
    sys.exit(0 if record["summary"]["agreed"] == record["summary"]["tasks"] else 1)


if __name__ == "__main__":
    main()
