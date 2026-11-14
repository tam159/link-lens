"""Repository for the `evidence` schema: source records and observations.

An observation row holds what is specific to one claim. Everything a claim
shares with its record, snapshot, mapping config or concept is read through
those references. `render` rebuilds the observation the extractor produced;
anything a row could not derive exactly is kept in its `extra` column, so the
rebuilt observation always equals the stored one.
"""

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    MetaData,
    Table,
    Text,
    and_,
    any_,
    func,
    literal,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB

from . import catalog, onboarding
from . import ontology as registry
from .bulk import copy_insert
from .records import parse_time, render_time, same
from .types import Sha256, is_sha256

metadata = MetaData(schema="evidence")
timestamp = DateTime(timezone=True)

RECORD_STATEMENT = "source record statement field"
TIMEZONE_ASSUMED = "UTC assumed for timezone-naive source timestamp"
CONFIDENCE_KIND = "uncalibrated mapping/source judgements"

source_record = Table(
    "source_record",
    metadata,
    Column("source_id", Text, primary_key=True),
    Column("id", Sha256, primary_key=True),
    Column("snapshot_id", Text),
    Column("sheet", Text),
    Column("row_no", BigInteger),
    Column("locator", JSONB),
)
observation = Table(
    "observation",
    metadata,
    Column("source_id", Text, primary_key=True),
    Column("id", Sha256, primary_key=True),
    Column("record_id", Sha256),
    Column("concept_id", BigInteger),
    Column("config_hash", Sha256),
    Column("group_name", Text),
    Column("group_id", Sha256),
    Column("value", Text),
    Column("raw_value", JSONB),
    Column("source_fields", ARRAY(Text)),
    Column("field_confidence", Float),
    Column("observed_at", timestamp),
    Column("timestamp_basis", Text),
    Column("timezone_assumed", Boolean),
    Column("ingested_at", timestamp),
    Column("derivation_level", Text),
    Column("engine", Text),
    Column("extra", JSONB),
)
OBSERVATION_COLUMNS = [c.name for c in observation.columns]


def among(column, values):
    """`column = ANY(array)`: one array parameter, however many values."""
    return column == any_(literal(list(values), ARRAY(column.type)))


def stored_value(value):
    """An observation value as text: integers and booleans in their JSON form."""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def typed_value(text, datatype):
    if datatype == "integer":
        try:
            return int(text)
        except ValueError:
            return text
    if datatype == "boolean" and text in ("true", "false"):
        return text == "true"
    return text


def render(row):
    """The observation a row stands for, before its `extra` keys are applied.

    `row` holds the observation columns and the joined record, snapshot, mapping
    config and concept columns.
    """
    result = {
        "source_id": row["source_id"],
        "source_record_id": row["record_id"],
        "observed_at": render_time(row["observed_at"]),
        "observed_at_basis": RECORD_STATEMENT
        if row["timestamp_basis"] == "record"
        else row["snapshot_basis"],
        "timezone_assumption": TIMEZONE_ASSUMED if row["timezone_assumed"] else None,
        "ingested_at": render_time(row["ingested_at"]),
        "licence": row["licence"],
        "extractor_version": row["engine"] + ":" + row["config_hash"],
        "field": row["concept_name"],
        "value": typed_value(row["value"], row["datatype"]),
        "source_fields": list(row["source_fields"]),
        "raw_value": row["raw_value"],
        "raw_locator": row["locator"],
        "snapshot_id": row["snapshot_id"],
        "config_hash": row["config_hash"],
        "subject_role": row["subject_role"],
        "source_kind": row["source_kind"],
        "address_role": row["address_role"],
        "confidence": {
            "source_reliability": row["source_reliability"],
            "field_confidence": row["field_confidence"],
        },
        "confidence_kind": CONFIDENCE_KIND,
        "derivation_level": row["derivation_level"],
    }
    if row["config_ontology_hash"] is not None:
        result.update(
            ontology_hash=row["config_ontology_hash"],
            value_type=row["datatype"],
            cardinality=row["cardinality"],
        )
    if row["group_name"] is not None:
        result.update(
            scope=row["scope"], group_id=row["group_id"], group_name=row["group_name"]
        )
    result["id"] = row["id"]
    return result


def payload(row):
    return {**render(row), **row["extra"]}


def _statement():
    record, snap = source_record, catalog.snapshot
    config, concept = onboarding.mapping_config, registry.concept
    return (
        select(
            observation,
            record.c.snapshot_id,
            record.c.locator,
            snap.c.licence,
            snap.c.observed_at_basis.label("snapshot_basis"),
            config.c.subject_role,
            config.c.source_kind,
            config.c.address_role,
            config.c.source_reliability,
            config.c.ontology_hash.label("config_ontology_hash"),
            concept.c.name.label("concept_name"),
            concept.c.datatype,
            concept.c.cardinality,
            concept.c.scope,
        )
        .join(
            record,
            and_(
                record.c.source_id == observation.c.source_id,
                record.c.id == observation.c.record_id,
            ),
        )
        .join(snap, snap.c.id == record.c.snapshot_id)
        .join(config, config.c.config_hash == observation.c.config_hash)
        .join(concept, concept.c.id == observation.c.concept_id)
    )


def observations(connection, ids=None):
    """Stored observations as the extractor produced them, in ID order."""
    statement = _statement().order_by(observation.c.id)
    if ids is not None:
        statement = statement.where(among(observation.c.id, ids))
    for row in (
        connection.execution_options(stream_results=True).execute(statement).mappings()
    ):
        yield payload(row)


def count(connection):
    return connection.execute(
        select(func.count()).select_from(observation)
    ).scalar_one()


def _refuse(item, reason):
    raise ValueError(f"Observation {item.get('id')} cannot be stored: {reason}")


def insert_observations(connection, items, root_hash):
    """Store observations and their source records. Returns the number inserted.

    Observation IDs are content hashes, so an observation that is already stored
    is skipped. Each observation must reference a stored snapshot and mapping
    config and a concept of that config's ontology. `root_hash` is the packaged
    ontology used by configs without an `ontology_hash`.
    """
    items = list(items)
    if not items:
        return 0
    for item in items:
        for key in ("id", "source_record_id", "config_hash"):
            if not is_sha256(item.get(key)):
                _refuse(item, f"{key} is not a SHA-256 digest")

    config = onboarding.mapping_config
    configs = {
        row.config_hash: row
        for row in connection.execute(
            select(config).where(
                among(config.c.config_hash, {i["config_hash"] for i in items})
            )
        )
    }
    snap = catalog.snapshot
    snapshots = {
        row.id: row
        for row in connection.execute(
            select(snap.c.id, snap.c.licence, snap.c.observed_at_basis).where(
                snap.c.id.in_({i.get("snapshot_id") for i in items})
            )
        )
    }
    concepts = {}
    member, concept = registry.version_concept, registry.concept
    versions = {row.ontology_hash or root_hash for row in configs.values()}
    for row in connection.execute(
        select(member.c.version_hash, concept)
        .join(concept, concept.c.id == member.c.concept_id)
        .where(member.c.version_hash.in_(versions))
    ):
        concepts[row.version_hash, row.name] = row

    records, drafts = {}, []
    for item in items:
        stored_config = configs.get(item["config_hash"])
        if stored_config is None:
            _refuse(item, "its mapping config is not stored")
        if item.get("snapshot_id") not in snapshots:
            _refuse(item, "its snapshot is not stored")
        definition = concepts.get(
            (stored_config.ontology_hash or root_hash, item.get("field"))
        )
        if definition is None:
            _refuse(item, f"{item.get('field')} is not in the mapping's ontology")
        observed_at = parse_time(item.get("observed_at"))
        ingested_at = parse_time(item.get("ingested_at"))
        confidence = item.get("confidence")
        field_confidence = (
            confidence.get("field_confidence") if isinstance(confidence, dict) else None
        )
        version = item.get("extractor_version")
        suffix = ":" + item["config_hash"]
        if (
            observed_at is None
            or ingested_at is None
            or isinstance(field_confidence, bool)
            or not isinstance(field_confidence, (int, float))
            or not isinstance(version, str)
            or not isinstance(item.get("derivation_level"), str)
            or not isinstance(item.get("raw_locator"), dict)
            or not isinstance(item.get("source_fields"), list)
            or item.get("value") is None
            or "raw_value" not in item
        ):
            _refuse(item, "a required field is missing or malformed")
        grouped = isinstance(item.get("group_name"), str) and is_sha256(
            item.get("group_id")
        )
        locator = item["raw_locator"]
        row_no = locator.get("row")
        records.setdefault(
            (item["source_id"], item["source_record_id"]),
            {
                "source_id": item["source_id"],
                "id": item["source_record_id"],
                "snapshot_id": item["snapshot_id"],
                "sheet": locator.get("sheet")
                if isinstance(locator.get("sheet"), str)
                else None,
                "row_no": row_no
                if isinstance(row_no, int) and not isinstance(row_no, bool)
                else None,
                "locator": locator,
            },
        )
        drafts.append(
            (
                item,
                stored_config,
                definition,
                {
                    "source_id": item["source_id"],
                    "id": item["id"],
                    "record_id": item["source_record_id"],
                    "concept_id": definition.id,
                    "config_hash": item["config_hash"],
                    "group_name": item["group_name"] if grouped else None,
                    "group_id": item["group_id"] if grouped else None,
                    "value": stored_value(item["value"]),
                    "raw_value": item["raw_value"],
                    "source_fields": item["source_fields"],
                    "field_confidence": float(field_confidence),
                    "observed_at": observed_at,
                    "timestamp_basis": "record"
                    if item.get("observed_at_basis") == RECORD_STATEMENT
                    else "snapshot",
                    "timezone_assumed": item.get("timezone_assumption") is not None,
                    "ingested_at": ingested_at,
                    "derivation_level": item["derivation_level"],
                    "engine": version.removesuffix(suffix),
                },
            )
        )

    copy_insert(connection, source_record, records.values())
    # A record already stored may belong to another snapshot with the same bytes;
    # what is derived must come from the stored record, not from this load.
    stored_records = {}
    for source in {source for source, _ in records}:
        for row in connection.execute(
            select(source_record).where(
                source_record.c.source_id == source,
                among(source_record.c.id, [k for s, k in records if s == source]),
            )
        ):
            stored_records[row.source_id, row.id] = row
    missing = {r.snapshot_id for r in stored_records.values()} - snapshots.keys()
    if missing:
        for row in connection.execute(
            select(snap.c.id, snap.c.licence, snap.c.observed_at_basis).where(
                snap.c.id.in_(missing)
            )
        ):
            snapshots[row.id] = row

    rows = []
    for item, stored_config, definition, row in drafts:
        record = stored_records[item["source_id"], item["source_record_id"]]
        snapshot = snapshots[record.snapshot_id]
        expected = render(
            {
                **row,
                "snapshot_id": record.snapshot_id,
                "locator": record.locator,
                "licence": snapshot.licence,
                "snapshot_basis": snapshot.observed_at_basis,
                "subject_role": stored_config.subject_role,
                "source_kind": stored_config.source_kind,
                "address_role": stored_config.address_role,
                "source_reliability": stored_config.source_reliability,
                "config_ontology_hash": stored_config.ontology_hash,
                "concept_name": definition.name,
                "datatype": definition.datatype,
                "cardinality": definition.cardinality,
                "scope": definition.scope,
            }
        )
        absent = [key for key in expected if key not in item]
        if absent:
            _refuse(item, "it lacks " + ", ".join(absent))
        row["extra"] = {
            key: value
            for key, value in item.items()
            if key not in expected or not same(expected[key], value)
        }
        rows.append(row)
    return copy_insert(connection, observation, rows, OBSERVATION_COLUMNS)
