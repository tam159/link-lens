"""Repository for the `identity` schema: entities, memberships, links, profiles.

A profile's fields and addresses are stored once, as child rows that also point
at the observation or source record they came from. The profile reads back with
them in place, exactly as it was written.
"""

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    Table,
    Text,
    any_,
    literal,
    select,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, insert

from . import evidence, ops
from .records import Field, RecordRef, RecordTable
from .types import Sha256, is_sha256

metadata = MetaData(schema="identity")
timestamp = DateTime(timezone=True)


def record_columns():
    return [
        Column("id", Text, primary_key=True),
        Column("owner_id", Text),
        Column("kind", Text),
        Column("batch_id", Text),
    ]


def record_tail():
    return [Column("extra", JSONB), Column("created_at", timestamp)]


entity = Table(
    "entity",
    metadata,
    *record_columns(),
    Column("entity_id", Text),
    Column("status", Text),
    Column("rule_version", Text),
    Column("identifiers", JSONB(none_as_null=True)),
    *record_tail(),
)
membership = Table(
    "membership",
    metadata,
    *record_columns(),
    Column("source_id", Text),
    Column("record_id", Sha256),
    Column("entity_id", Text),
    *record_tail(),
)
link = Table(
    "link",
    metadata,
    *record_columns(),
    Column("link_id", Sha256),
    Column("entity_key", Text),
    Column("rule", Text),
    Column("rule_version", Text),
    Column("score", Float),
    Column("score_kind", Text),
    Column("threshold", Float),
    Column("status", Text),
    Column("human_review_status", Text),
    Column("evidence", JSONB(none_as_null=True)),
    Column("a_source_id", Text),
    Column("a_record_id", Sha256),
    Column("b_source_id", Text),
    Column("b_record_id", Sha256),
    *record_tail(),
)
profile = Table(
    "profile",
    metadata,
    *record_columns(),
    Column("entity_key", Text),
    Column("profile_version", Sha256),
    Column("policy_version", Text),
    Column("status", Text),
    Column("uncertainties", JSONB(none_as_null=True)),
    *record_tail(),
)
profile_field = Table(
    "profile_field",
    metadata,
    Column("profile_id", Text, primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("concept_name", Text),
    Column("concept_id", BigInteger),
    Column("status", Text),
    Column("value", Text),
    Column("observation_source_id", Text),
    Column("observation_id", Sha256),
    Column("detail", JSONB),
)
profile_address = Table(
    "profile_address",
    metadata,
    Column("profile_id", Text, primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("role", Text),
    Column("source_id", Text),
    Column("record_id", Sha256),
    Column("detail", JSONB),
)


class LinkTable(RecordTable):
    def split(self, connection, payload):
        columns = super().split(connection, payload)
        evidence_ = payload.get("evidence")
        rule = evidence_.get("rule") if isinstance(evidence_, dict) else None
        # A projection of the evidence for queries; the evidence stays the record.
        columns["rule"] = rule if isinstance(rule, str) else None
        return columns


def first_provenance(field):
    """The observation a selected field cites first, if it cites one."""
    provenance = field.get("provenance") if isinstance(field, dict) else None
    first = provenance[0] if isinstance(provenance, list) and provenance else None
    return first if isinstance(first, dict) else {}


class ProfileTable(RecordTable):
    """Profiles whose `fields` and `addresses` live in child tables."""

    @staticmethod
    def typed_fields(payload):
        fields = payload.get("fields")
        if (
            isinstance(fields, dict)
            and fields
            and all(isinstance(value, dict) for value in fields.values())
        ):
            return fields
        return None

    @staticmethod
    def typed_addresses(payload):
        addresses = payload.get("addresses")
        if (
            isinstance(addresses, list)
            and addresses
            and all(isinstance(value, dict) for value in addresses)
        ):
            return addresses
        return None

    def split(self, connection, payload):
        rest = dict(payload)
        if self.typed_fields(payload) is not None:
            del rest["fields"]
        if self.typed_addresses(payload) is not None:
            del rest["addresses"]
        return super().split(connection, rest)

    def after_insert(self, connection, key, payload):
        fields = self.typed_fields(payload)
        addresses = self.typed_addresses(payload) or []
        cited = [first_provenance(field) for field in (fields or {}).values()]
        observation = evidence.observation
        ids = [c["id"] for c in cited if is_sha256(c.get("id"))]
        stored = (
            {
                (row.source_id, row.id): row.concept_id
                for row in connection.execute(
                    select(
                        observation.c.source_id,
                        observation.c.id,
                        observation.c.concept_id,
                    ).where(evidence.among(observation.c.id, ids))
                )
            }
            if ids
            else {}
        )
        if fields:
            rows = []
            for position, ((name, field), cite) in enumerate(
                zip(fields.items(), cited)
            ):
                reference = (cite.get("source_id"), cite.get("id"))
                found = reference in stored
                value = field.get("value")
                rows.append(
                    {
                        "profile_id": key,
                        "position": position,
                        "concept_name": name,
                        "concept_id": stored.get(reference),
                        "status": field.get("status")
                        if isinstance(field.get("status"), str)
                        else None,
                        "value": value if isinstance(value, str) else None,
                        "observation_source_id": reference[0] if found else None,
                        "observation_id": reference[1] if found else None,
                        "detail": field,
                    }
                )
            connection.execute(insert(profile_field), rows)
        if addresses:
            record = evidence.source_record
            rows = []
            for position, address in enumerate(addresses):
                inner = address.get("fields")
                cite = (
                    first_provenance(next(iter(inner.values())))
                    if isinstance(inner, dict) and inner
                    else {}
                )
                reference = (cite.get("source_id"), cite.get("source_record_id"))
                found = (
                    isinstance(reference[0], str)
                    and is_sha256(reference[1])
                    and connection.execute(
                        select(record.c.id).where(
                            record.c.source_id == reference[0],
                            record.c.id == reference[1],
                        )
                    ).first()
                    is not None
                )
                rows.append(
                    {
                        "profile_id": key,
                        "position": position,
                        "role": address.get("role")
                        if isinstance(address.get("role"), str)
                        else None,
                        "source_id": reference[0] if found else None,
                        "record_id": reference[1] if found else None,
                        "detail": address,
                    }
                )
            connection.execute(insert(profile_address), rows)

    def load(self, connection, rows):
        payloads = [self.join(row) for row in rows]
        keys = [row["id"] for row in rows]
        if not keys:
            return payloads
        chosen = literal(keys, ARRAY(Text))
        fields, addresses = {}, {}
        for child in connection.execute(
            select(
                profile_field.c.profile_id,
                profile_field.c.concept_name,
                profile_field.c.detail,
            )
            .where(profile_field.c.profile_id == any_(chosen))
            .order_by(profile_field.c.profile_id, profile_field.c.position)
        ):
            fields.setdefault(child.profile_id, {})[child.concept_name] = child.detail
        for child in connection.execute(
            select(profile_address.c.profile_id, profile_address.c.detail)
            .where(profile_address.c.profile_id == any_(chosen))
            .order_by(profile_address.c.profile_id, profile_address.c.position)
        ):
            addresses.setdefault(child.profile_id, []).append(child.detail)
        for key, payload in zip(keys, payloads):
            if key in fields:
                payload["fields"] = fields[key]
            if key in addresses:
                payload["addresses"] = addresses[key]
        return payloads


entities = RecordTable(
    "entities",
    entity,
    [
        Field("id", "entity_id", "text"),
        Field("status", "status", "text"),
        Field("identity_rule_version", "rule_version", "text"),
        Field("identifiers", "identifiers", "json"),
    ],
    batch=ops.batch,
)
memberships = RecordTable(
    "memberships",
    membership,
    [
        Field("batch_id", "batch_id", "text", references=ops.batch.c.id),
        Field("entity_id", "entity_id", "text"),
    ],
    append_only=True,
    refs=[RecordRef("record", "source_id", "record_id", evidence.source_record)],
    batch=ops.batch,
)
links = LinkTable(
    "links",
    link,
    [
        Field("id", "link_id", "sha256"),
        Field("canonical_entity_key", "entity_key", "text"),
        Field("rule_version", "rule_version", "text"),
        Field("confidence", "score", "float"),
        Field("confidence_kind", "score_kind", "text"),
        Field("threshold", "threshold", "float"),
        Field("status", "status", "text"),
        Field("human_review_status", "human_review_status", "text"),
        Field("evidence", "evidence", "json"),
    ],
    append_only=True,
    refs=[
        RecordRef(
            "source_a_record", "a_source_id", "a_record_id", evidence.source_record
        ),
        RecordRef(
            "source_b_record", "b_source_id", "b_record_id", evidence.source_record
        ),
    ],
    batch=ops.batch,
)
profiles = ProfileTable(
    "profiles",
    profile,
    [
        Field("canonical_entity_key", "entity_key", "text"),
        Field("profile_version", "profile_version", "sha256"),
        Field("policy_version", "policy_version", "text"),
        Field("status", "status", "text"),
        Field("uncertainties", "uncertainties", "json"),
    ],
    append_only=True,
    batch=ops.batch,
)
