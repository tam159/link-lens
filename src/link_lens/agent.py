"""One bounded agent: explicit states, typed model tool calls, real revision and HIL."""

import json
import csv
import time
from typing import TypedDict
from pydantic import Field
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langgraph.errors import GraphInterrupt
from langsmith import traceable
from . import store
from .contracts import (
    StrictModel,
    ReaderSpec,
    MappingSpec,
    SemanticReview,
    content_hash,
)
from .settings import settings
from .ontology import resolve
from .readers import read_records, partition, inspect_resource
from .extraction import validate, extract
from .llm import call, BudgetExceeded
from .sandbox import explore


class AnalysisPlan(StrictModel):
    reader: ReaderSpec
    grain_hypothesis: str
    uncertainties: list[str]
    exploration_python: str | None = Field(
        default=None,
        description="Optional Python to inspect /work/input.json, which has records and documentation. Each record is {'values': {column_name: string_value}, 'locator': {...}}. Access record['values'].get(column_name), never numeric indexes. Records contain data only, not a header row. Print concise findings. No network, no installs. Never an extractor.",
    )


class State(TypedDict, total=False):
    run_id: str
    route: str
    feedback: str


def run_data(state):
    run = store.require("runs", state["run_id"])
    return (
        run,
        store.require("snapshots", run["snapshot_id"]),
        store.require("sources", run["source_id"]),
    )


def update(run, **changes):
    run.update(changes)
    store.put("runs", run["id"], run, run["source_id"], "onboarding")
    return run


def source_context(source, snapshot):
    text = {
        "title": source["metadata"]["title"],
        "publisher": (source["metadata"].get("organization") or {}).get("title"),
        "dataset_notes": snapshot["dataset_notes"][:10000],
        "publication_proxy": snapshot["observed_at"],
        "licence": snapshot["licence"],
        "documentation": [],
    }
    for doc in snapshot["documentation"]:
        if "pages" in doc:
            # Entire short publisher guides fit; include page numbers for evidence.
            text["documentation"].append({"url": doc["url"], "pages": doc["pages"]})
    return json.dumps(text, ensure_ascii=False)[:36000]


def safe_node(function):
    """Exceptions are isolated to one source and remain visible in persistent status."""

    def wrapped(state):
        start = time.monotonic()
        before = store.require("runs", state["run_id"])["active_seconds"]
        try:
            return function(state)
        except GraphInterrupt:
            raise
        except Exception as exc:
            # Framework interrupts pass through above; only operational errors stop a source.
            run = store.require("runs", state["run_id"])
            update(
                run,
                status="budget_exhausted"
                if isinstance(exc, BudgetExceeded)
                else "failed",
                error=f"{type(exc).__name__}: {str(exc)[:1600]}",
            )
            store.event(
                run["id"], "failure", {"node": function.__name__, "error": run["error"]}
            )
            return {"route": "end"}
        finally:
            elapsed = time.monotonic() - start
            run = store.require("runs", state["run_id"])
            already_accounted = run["active_seconds"] - before
            update(
                run,
                active_seconds=run["active_seconds"]
                + max(0, elapsed - already_accounted),
                timing_basis="Node wall time, excluding human wait and run queue; includes model and sandbox time once.",
            )
            store.event(
                run["id"],
                "node_execution",
                {"node": function.__name__, "wall_seconds": round(elapsed, 4)},
            )

    wrapped.__name__ = function.__name__
    return wrapped


@safe_node
def inspect_node(state):
    run, snapshot, source = run_data(state)
    if run.get("analysis_artifact"):
        return {"route": "explore"}
    if run.get("reader_attempts", 0) >= 3:
        raise BudgetExceeded(
            "Three structural reader attempts exhausted; no partitions or mapping fabricated"
        )
    update(run, reader_attempts=run.get("reader_attempts", 0) + 1, status="inspecting")
    inspection = inspect_resource(
        store.blob_path(snapshot["artifact_id"]),
        snapshot["format"],
        snapshot["receipt"]["partial"],
    )
    prompt = f"""Inspect this source. Select the data sheet/header/delimiter from actual resource evidence. Prefer the detected delimiter/encoding when the preview has coherent columns; publisher guides may describe an older format. The preview contains only the first six rows (always discovery). Do not assume the first Excel sheet is data. Propose a short Python investigation if useful. Input JSON records have `values` and `locator`; input documentation is a string. Investigation can count values and identify edge cases; it must NOT generate the final mapping.\nSOURCE:\n{source_context(source, snapshot)}\nSTRUCTURE:\n{json.dumps(inspection, ensure_ascii=False)[:16000]}"""
    if run.get("reader_feedback"):
        prompt += "\nPRIOR READER FAILURE (no records exposed):\n" + json.dumps(
            run["reader_feedback"]
        )
    plan = call(run["id"], AnalysisPlan, prompt, "inspect")
    try:
        headers, rows = read_records(
            store.blob_path(snapshot["artifact_id"]),
            plan.reader,
            snapshot["sha256"],
            snapshot["receipt"]["partial"],
            settings().sample_pool_size,
        )
    except (ValueError, UnicodeError, csv.Error, KeyError, StopIteration) as exc:
        feedback = {
            "reader": plan.reader.model_dump(),
            "error": f"{type(exc).__name__}: {str(exc)[:500]}",
        }
        update(store.require("runs", run["id"]), reader_feedback=feedback)
        store.event(run["id"], "reader_validation", {"passed": False, **feedback})
        return {"route": "inspect"}
    parts = partition(rows)
    artifact = store.json_blob(
        {"headers": headers, "reader": plan.reader.model_dump(), "partitions": parts},
        "partitioned-records.json",
    )
    analysis = store.json_blob(plan.model_dump(), "analysis.json")
    update(
        store.require("runs", run["id"]),
        status="inspected",
        analysis_artifact=analysis,
        partitions_artifact=artifact,
        partition_counts={k: len(v) for k, v in parts.items()},
        final_cursor=0,
    )
    store.event(
        run["id"],
        "inspect",
        {
            "partition_counts": {k: len(v) for k, v in parts.items()},
            "reader": plan.reader.model_dump(),
        },
    )
    return {"route": "explore"}


@traceable(run_type="tool", name="execute_discovery_python")
def python_tool(code, records, documentation):
    return explore(code, records, documentation)


@safe_node
def explore_node(state):
    run, snapshot, source = run_data(state)
    if run.get("exploration_artifact"):
        return {"route": "propose"}
    plan = store.read_json(run["analysis_artifact"])
    code = plan.get("exploration_python")
    if code:
        if run["python_calls"] >= settings().max_python_calls:
            raise BudgetExceeded("Python-call budget exhausted")
        update(run, python_calls=run["python_calls"] + 1, status="exploring")
        discovery = store.read_json(run["partitions_artifact"])["partitions"][
            "discovery"
        ]
        start = time.monotonic()
        try:
            result = python_tool(
                code, discovery[:300], source_context(source, snapshot)
            )
        except Exception as exc:
            result = {
                "exit_code": 1,
                "output": f"Exploration unavailable: {type(exc).__name__}: {str(exc)[:600]}",
            }
        result["code"] = code
        result["seconds"] = time.monotonic() - start
        artifact = store.json_blob(result, "exploration.json")
        run = store.require("runs", run["id"])
        update(
            run,
            exploration_artifact=artifact,
            active_seconds=run["active_seconds"] + result["seconds"],
        )
        store.event(
            run["id"],
            "exploration",
            {"artifact_id": artifact, "exit_code": result["exit_code"]},
        )
    return {"route": "propose"}


def proposal_context(run, snapshot, source, include_prior_critique=True):
    pack = store.read_json(run["partitions_artifact"])
    examples = pack["partitions"]["discovery"][:8]
    context = {
        "source": source_context(source, snapshot),
        "reader": pack["reader"],
        "headers": pack["headers"],
        "discovery_records": examples,
        "ontology": resolve(run.get("ontology_hash")),
        "ontology_hash": run.get("ontology_hash"),
        "extension_semantics": "Set ontology_hash to the supplied hash. New non-entity/address concepts require group names shared by related fields in the same source row. Include required companions (e.g. period and currency). indicator_categories takes source column to category values and an explicit truth marker argument. Typed numeric operations accept plain decimals only. Do not infer legal ownership from a site contact. Only registered concepts may be mapped.",
        "trusted_engine_semantics": {
            "abn": "Formatting removal then EXACTLY 11 digits and ABN checksum. Missing/0 -> no observation. Valid 9-digit ACN -> no observation, never converted.",
            "acn": "Formatting removal then EXACTLY 9 digits and ACN checksum. Missing/0 -> no observation. Valid 11-digit ABN -> no observation, never suffix-derived.",
            "identifier_exclusivity": "ABN and ACN accepted lengths are disjoint. The same mixed column may map to both; at most one can emit. A length condition is optional, not required for exclusivity.",
            "split": "Produces multiple values from an explicit separator; never infers list boundaries.",
            "constant": "Requires evidence for the chosen literal; does not infer legal meaning.",
            "conditional": "when/filters allow exact membership, nonempty and string length; no arbitrary expressions.",
            "provenance_and_linking": "Every emitted field retains the same snapshot+row source_record_id and source ID. Claims are not canonical entity assignments. Exact-ID linking is a later deterministic stage with compatible roles. subject_role unknown/reporting_group prevents entity linking. If holder/ownership is unsupported, use unknown and leave identifiers unmapped; a partial raw trading-name claim need not assert ownership.",
            "timestamps": "publication_proxy is an explicitly allowed policy: observations label observed_at_basis and timezone assumptions. It is not a claim of row change time. Missing timestamp quarantines. Disclosed publication proxy alone is not a blocker.",
            "sample_counts": "Exploration uses up to 300 discovery rows. Validation uses up to 250 different validation rows. Their counts are deliberately different, not evidence of dropped records.",
            "envelope": "The engine, not fields[], emits source_id, snapshot+row source_record_id, observed_at and basis, ingested_at, licence, extractor_version for EVERY observation. These are verified by the validator. They are not ontology target mappings and must not appear in fields[] or unmapped_fields.",
            "subject_roles": "licence_holder/service_provider/supplier describe the organisation whose claims a row states; they are allowed by the MappingSpec contract, not assertions of company incorporation. The resolver accepts those roles with valid explicit IDs and blocks unknown/reporting_group. Licence numbers never substitute for ABN/ACN. Do not require every licence holder to be a company.",
            "sentinels": "Literal unknown/other/international placeholders are not actual countries or legal values. Use field conditions or explicit enum mappings to omit such claims, or leave the column unmapped; preserve raw rows as evidence. Explicitly stating a limitation does not make a misleading canonical value valid.",
        },
        "analysis": store.read_json(run["analysis_artifact"]),
    }
    if run.get("exploration_artifact"):
        context["exploration"] = store.read_json(run["exploration_artifact"])["output"][
            :8000
        ]
    if run.get("mapping_id"):
        context["previous_mapping"] = store.require("mappings", run["mapping_id"])[
            "config"
        ]
    if run.get("validation"):
        context["validation_feedback"] = {
            k: v for k, v in run["validation"].items() if k != "output_examples"
        }
        context["validation_feedback"]["output_examples"] = [
            {k: o[k] for k in ["field", "value", "source_fields", "raw_value"]}
            for o in run["validation"].get("output_examples", [])[:4]
        ]
    if run.get("critique") and include_prior_critique:
        context["semantic_feedback"] = run["critique"]
    return json.dumps(context, ensure_ascii=False)


@safe_node
def propose_node(state):
    run, snapshot, source = run_data(state)
    if run["version"] >= settings().max_mapping_versions:
        update(
            run,
            status="needs_review",
            error="Maximum mapping versions reached; no extraction authorised",
        )
        return {"route": "end"}
    update(run, version=run["version"] + 1, status="proposing")
    prompt = (
        """Generate a MappingSpec using ONLY the schema operations. Keep the supplied reader unchanged: partitions are already frozen. List EVERY unmapped column, even empty unnamed columns. `abn` and `acn` operations validate identifiers and return no value for a valid identifier of the other type; do not infer ACN from an ABN suffix. A single mixed ABN/ACN column can therefore map to both. Preserve numeric IDs as strings; do not zero-pad damaged values. Do not map registration of a charity, trading name or licence to company date_registered. A revoked licence does not prove entity deregistration. Do not assume an organisation/site/provider label is a legal name. Use subject_label_field to retain raw identity labels even if no confident canonical name mapping exists. Do not infer company type from a suffix. The source envelope supplies publication timestamps and licence. All authority/field scores are provisional and require human review. Include documentation citations/page or exact header/sample evidence per mapped field. When docs justify row filters (current names, legal entity types), encode them. If a previous proposal failed, correct it using the feedback, or leave doubtful columns unmapped. Human feedback: """
        + state.get("feedback", "none")
        + "\n"
        + proposal_context(run, snapshot, source)
    )
    try:
        spec = call(run["id"], MappingSpec, prompt, "propose_mapping")
        if spec.ontology_hash is None and run.get("ontology_hash"):
            spec = MappingSpec.model_validate(
                {**spec.model_dump(), "ontology_hash": run["ontology_hash"]}
            )
        if spec.ontology_hash != run.get("ontology_hash"):
            raise ValueError("Mapping must use the run pinned ontology_hash")
    except ValueError as exc:
        update(
            store.require("runs", run["id"]),
            validation={"blocking_issues": [str(exc)[:1800]]},
        )
        return {"route": "propose", "feedback": str(exc)[:1800]}
    digest = content_hash(spec)
    key = f"{run['id']}:{run['version']}"
    mapping = {
        "id": key,
        "run_id": run["id"],
        "version": run["version"],
        "config_hash": digest,
        "config": spec.model_dump(),
        "generated_by": "runtime_agent",
        "model": run.get("model", settings().model),
        "created_at": store.now(),
        "status": "proposed",
    }
    store.put("mappings", key, mapping, run["id"], "mapping", immutable=True)
    update(store.require("runs", run["id"]), mapping_id=key, status="validating")
    return {"route": "validate", "feedback": ""}


@safe_node
def validate_node(state):
    run, snapshot, _ = run_data(state)
    mapping = store.require("mappings", run["mapping_id"])
    spec = MappingSpec.model_validate(mapping["config"])
    pack = store.read_json(run["partitions_artifact"])
    report = validate(
        spec, pack["headers"], pack["partitions"]["validation"][:250], snapshot
    )
    if spec.reader.model_dump() != pack["reader"]:
        report["blocking_issues"].append("Reader differs from frozen partition reader")
        report["passed"] = False
    update(run, validation=report)
    store.event(run["id"], "validation", {"version": run["version"], "report": report})
    return {"route": "critique" if report["passed"] else "propose"}


@safe_node
def critique_node(state):
    run, snapshot, source = run_data(state)
    prompt = (
        """Independently critique this mapping against source documentation and raw discovery evidence. Decide whether it is semantically acceptable for HUMAN REVIEW, not proven correct. Check grain/subject ownership, legal vs trading names, historic vs current names, registration/status semantics, service-location addresses, reporting groups, confidence and unsupported constants. Avoid speculative demands unsupported by the actual source. Separate blocking issues from disclosed limitations. Do not demand unsupported fields be mapped. Treat the supplied engine semantics as authoritative implementation facts. Do not block solely for stylistic grain wording when filters and status semantics are explicit and correct. An acceptable mapping can be deliberately partial. If any blocking issues exist, acceptable must be false.\n"""
        + proposal_context(run, snapshot, source, include_prior_critique=False)
    )
    if run.get("critique_format_error"):
        prompt += (
            "\nPrevious response did not match SemanticReview. Return ALL required fields, including empty warnings when appropriate. Error: "
            + run["critique_format_error"]
        )
    try:
        review = call(run["id"], SemanticReview, prompt, "semantic_critique")
    except ValueError as exc:
        latest = store.require("runs", run["id"])
        attempts = latest.get("critique_format_attempts", 0) + 1
        update(
            latest,
            critique_format_attempts=attempts,
            critique_format_error=str(exc)[:1800],
        )
        if attempts >= 2:
            raise
        return {"route": "critique"}
    update(store.require("runs", run["id"]), critique_format_error=None)
    update(store.require("runs", run["id"]), critique=review.model_dump())
    store.event(
        run["id"],
        "semantic_critique",
        {"version": run["version"], **review.model_dump()},
    )
    return {
        "route": "final"
        if review.acceptable and not review.blocking_issues
        else "propose"
    }


def review_markdown(run, snapshot, source, mapping):
    spec = MappingSpec.model_validate(mapping["config"])
    pack = store.read_json(run["partitions_artifact"])
    preview = extract(spec, pack["partitions"]["discovery"][:3], snapshot)
    lines = [
        f"# Mapping review: {source['metadata']['title']}",
        f"Config version **{mapping['version']}**, hash `{mapping['config_hash']}`.",
        f"Ontology: `{spec.ontology_hash or 'legacy v0.1'}`.",
        f"Licence: {snapshot['licence']}. Source snapshot: `{snapshot['sha256']}`.",
        f"Grain: {spec.record_grain}. Subject: **{spec.subject_role}**.",
        f"Reader: `{json.dumps(spec.reader.model_dump())}`.",
        "\n## Mappings\n",
        "| Source fields | Canonical field | Operations | Confidence | Evidence |",
        "|---|---|---|---|---|",
    ]
    for f in spec.fields:
        values = [
            ", ".join(f.source_fields) or "(constant)",
            f.canonical_field,
            ", ".join(o.op for o in f.transformations),
            str(f.confidence),
            f.evidence,
        ]
        lines.append(
            "| "
            + " | ".join(v.replace("|", "/").replace("\n", " ") for v in values)
            + " |"
        )
    lines += [
        "\n## Before / after\n",
        "```json",
        json.dumps(
            {
                "raw": pack["partitions"]["discovery"][:2],
                "observations": preview["observations"][:10],
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "\n## Checks\n",
        f"Validation: {run['validation']['records']} records; {run['validation']['quarantined_fields']} field issues.",
        f"Final test: {run['final_validation']['records']} previously withheld records; passed={run['final_validation']['passed']}.",
        f"Model calls: {run['model_calls']}; measured/reserved input/output: {run['input_tokens']}/{run['output_tokens']}; calculated cost: {run['calculated_cost_usd']}.",
        f"Pricing: {run['pricing_basis']}. Scores are uncalibrated, not measured accuracy.",
        "\n## Unmapped\n",
        *[f"- **{u.source_field}**: {u.reason}" for u in spec.unmapped_fields],
        "\n## Uncertainties\n",
        *[f"- {item}" for item in spec.limitations + run["critique"]["warnings"]],
        f"- Timestamp basis: {snapshot['observed_at_basis']}; naive source timestamps are explicitly labelled UTC assumptions.",
        "\nAccept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.",
    ]
    if run.get("trace_url"):
        lines.append(f"\n[LangSmith trace]({run['trace_url']})")
    return "\n".join(lines)


@safe_node
def final_node(state):
    run, snapshot, source = run_data(state)
    mapping = store.require("mappings", run["mapping_id"])
    pack = store.read_json(run["partitions_artifact"])
    cursor = run.get("final_cursor", 0)
    rows = pack["partitions"]["final"][cursor : cursor + 100]
    report = validate(
        MappingSpec.model_validate(mapping["config"]), pack["headers"], rows, snapshot
    )
    update(
        run,
        final_validation=report,
        final_cursor=cursor + len(rows),
        final_record_ids=[r["record_id"] for r in rows],
    )
    store.event(
        run["id"],
        "final_validation",
        {
            "version": run["version"],
            "report": report,
            "record_ids": [r["record_id"] for r in rows],
        },
    )
    if not report["passed"]:
        update(
            run,
            status="final_validation_failed",
            error="Final-test failure blocks approval; no automatic revision against final records",
        )
        return {"route": "end"}
    packet = review_markdown(run, snapshot, source, mapping)
    artifact = store.blob(packet.encode(), "text/markdown", "mapping-review.md")
    update(run, status="waiting_for_human", review_artifact=artifact)
    return {"route": "review"}


def record_approval(run, mapping, response):
    if not isinstance(response, list) or len(response) != 1:
        raise ValueError("Expected one Agent Inbox response")
    response = response[0]
    kind = response.get("type")
    if kind == "accept":
        args = response.get("args") or {}
        # Native Inbox Accept supplies null. Approval binds the paused stored mapping.
        # A CLI hash, when supplied, is checked; returned edits never replace config.
        if args and (
            not isinstance(args, dict)
            or args.get("config_hash") != mapping["config_hash"]
        ):
            raise ValueError("Approval references a different config hash")
        decision = "approved"
    elif kind == "ignore":
        decision = "deferred"
    elif kind == "response":
        decision = "revision_requested"
    else:
        raise ValueError("Direct config editing is disabled")
    key = content_hash(
        {
            "run_id": run["id"],
            "config_hash": mapping["config_hash"],
            "decision": decision,
        }
    )
    previous = store.get("approvals", key)
    if previous:
        return previous
    record = {
        "id": key,
        "run_id": run["id"],
        "config_hash": mapping["config_hash"],
        "mapping_id": mapping["id"],
        "decision": decision,
        "reviewer": settings().reviewer,
        "at": store.now(),
        "feedback": str(response.get("args", "")) if kind == "response" else "",
        "identity_basis": "configured local single-user identity, not authenticated multi-user identity",
    }
    store.put("approvals", key, record, run["id"], "approval", immutable=True)
    return record


@safe_node
def review_node(state):
    run, _, _ = run_data(state)
    mapping = store.require("mappings", run["mapping_id"])
    packet = store.blob_path(run["review_artifact"]).read_text()
    response = interrupt(
        [
            {
                "action_request": {
                    "action": "review_source_mapping",
                    "args": {
                        "source": run["source_slug"],
                        "config_hash": mapping["config_hash"],
                        "version": str(mapping["version"]),
                        "review_url": settings().api_url
                        + "/api/artifacts/"
                        + run["review_artifact"],
                    },
                },
                "config": {
                    "allow_accept": True,
                    "allow_respond": True,
                    "allow_ignore": True,
                    "allow_edit": False,
                },
                "description": packet,
            }
        ]
    )
    approval = record_approval(run, mapping, response)
    update(run, status=approval["decision"], approval_id=approval["id"])
    if approval["decision"] == "approved":
        return {"route": "extract"}
    if approval["decision"] == "revision_requested":
        return {"route": "propose", "feedback": approval["feedback"]}
    return {"route": "end"}


@safe_node
def extract_node(state):
    run, snapshot, _ = run_data(state)
    mapping = store.require("mappings", run["mapping_id"])
    approval = store.require("approvals", run["approval_id"])
    if (
        approval["decision"] != "approved"
        or approval["config_hash"] != mapping["config_hash"]
        or content_hash(mapping["config"]) != mapping["config_hash"]
        or mapping["config"].get("ontology_hash") != run.get("ontology_hash")
    ):
        raise ValueError("Exact mapping approval is required")
    pack = store.read_json(run["partitions_artifact"])
    rows = sorted(
        sum(pack["partitions"].values(), []),
        key=lambda r: (r["locator"]["sheet"], r["locator"]["row"]),
    )[:1000]
    result = extract(MappingSpec.model_validate(mapping["config"]), rows, snapshot)
    for o in result["observations"]:
        store.put("observations", o["id"], o, run["id"], "observation", immutable=True)
    artifact = store.json_blob(result, "extraction.json")
    update(
        run,
        status="completed",
        extraction_artifact=artifact,
        extracted_records=len(rows),
        observation_count=len(result["observations"]),
        completed_at=store.now(),
    )
    store.event(
        run["id"],
        "extraction",
        {
            "records": len(rows),
            "observations": len(result["observations"]),
            "issues": len(result["issues"]),
        },
    )
    return {"route": "end"}


def build_graph(checkpointer=None):
    builder = StateGraph(State)
    nodes = {
        "inspect": inspect_node,
        "explore": explore_node,
        "propose": propose_node,
        "validate": validate_node,
        "critique": critique_node,
        "final": final_node,
        "review": review_node,
        "extract": extract_node,
    }
    for name, function in nodes.items():
        builder.add_node(name, function)

    def entry(state):
        run = store.require("runs", state["run_id"])
        if run["status"] == "waiting_for_human":
            return "review"
        if run["status"] == "completed":
            return "end"
        return "inspect"

    builder.add_conditional_edges(
        START, entry, {"review": "review", "inspect": "inspect", "end": END}
    )
    destinations = {name: name for name in nodes}
    destinations["end"] = END
    for name in nodes:
        builder.add_conditional_edges(name, lambda state: state["route"], destinations)
    return builder.compile(checkpointer=checkpointer)


graph = (
    build_graph()
)  # Agent Server supplies its own persistent development checkpointer.
