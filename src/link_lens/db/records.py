"""Tables that keep a store record exactly while exposing typed columns.

The store has always held one JSON document per key. A record table keeps that
document without loss: a field goes into its typed column when the value is
present and well formed, and into the table's JSON column otherwise. A reference
column is filled only when the row it points at exists, so foreign keys never
dangle and an unresolved reference stays visible in the JSON column. Reading
puts the document back together, key for key.
"""

import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from .types import is_sha256

INT8 = 2**63


def same(a, b):
    """Equal as JSON, so 1 and 1.0, or 1 and true, are different."""
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def same_column(a, b):
    """`same` for column values, which may be timestamps."""
    return json.dumps(a, sort_keys=True, default=str) == json.dumps(
        b, sort_keys=True, default=str
    )


def parse_time(value):
    """An ISO timestamp as an aware datetime; naive values are taken as UTC."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def render_time(value):
    return value.astimezone(UTC).isoformat()


class Field:
    """One payload key and the typed column that holds it when it fits."""

    def __init__(self, key, column, kind, references=None):
        self.key, self.column, self.kind, self.references = (
            key,
            column,
            kind,
            references,
        )

    def to_db(self, value):
        """The column value, or None when the payload value does not fit the type."""
        kind = self.kind
        if kind == "text":
            return value if isinstance(value, str) and "\x00" not in value else None
        if kind == "sha256":
            return value if is_sha256(value) else None
        if kind == "integer":
            fits = isinstance(value, int) and not isinstance(value, bool)
            return value if fits and -INT8 <= value < INT8 else None
        if kind == "float":
            fits = isinstance(value, (int, float)) and not isinstance(value, bool)
            return float(value) if fits and value == value else None
        if kind == "timestamp":
            return parse_time(value)
        if kind == "json":
            return value if isinstance(value, (dict, list)) else None
        if kind == "texts":
            fits = isinstance(value, list) and all(
                isinstance(v, str) and "\x00" not in v for v in value
            )
            return list(value) if fits else None
        raise ValueError(kind)

    def from_db(self, value):
        if self.kind == "texts":
            return list(value)
        return render_time(value) if self.kind == "timestamp" else value


class RecordRef:
    """A payload key holding `[source_id, record_id]`, kept as two columns.

    The pair is typed only when that source record is stored, so the composite
    foreign key to `evidence.source_record` always holds.
    """

    def __init__(self, key, source_column, record_column, source_record):
        self.key, self.source_column, self.record_column = (
            key,
            source_column,
            record_column,
        )
        self.source_record = source_record

    def split(self, connection, payload):
        value = payload.get(self.key)
        fits = (
            isinstance(value, list)
            and len(value) == 2
            and isinstance(value[0], str)
            and is_sha256(value[1])
        )
        table = self.source_record
        if (
            fits
            and connection.execute(
                select(table.c.id).where(
                    table.c.source_id == value[0], table.c.id == value[1]
                )
            ).first()
        ):
            return {self.source_column: value[0], self.record_column: value[1]}
        return {self.source_column: None, self.record_column: None}

    def join(self, row):
        if row[self.record_column] is None:
            return None
        return [row[self.source_column], row[self.record_column]]


class RecordTable:
    """Reads and writes store records in one typed table."""

    def __init__(
        self, name, table, fields, extra="extra", append_only=False, refs=(), batch=None
    ):
        self.name, self.table, self.fields = name, table, fields
        self.extra, self.append_only = extra, append_only
        # `refs` are record references; `batch` is the batch table when the row's
        # owner is a batch and the table has a `batch_id` column for it.
        self.refs, self.batch = list(refs), batch

    def statement(self):
        return select(self.table)

    def split(self, connection, payload):
        """Column values for a payload: typed where it fits, the rest as JSON."""
        columns, typed = {}, set()
        for field in self.fields:
            value = field.to_db(payload[field.key]) if field.key in payload else None
            if value is not None and field.references is not None:
                found = connection.execute(
                    select(field.references).where(field.references == value)
                ).first()
                value = value if found else None
            columns[field.column] = value
            if value is not None and same(field.from_db(value), payload[field.key]):
                typed.add(field.key)
        for ref in self.refs:
            pair = ref.split(connection, payload)
            columns.update(pair)
            if pair[ref.record_column] is not None:
                typed.add(ref.key)
        columns[self.extra] = {k: v for k, v in payload.items() if k not in typed}
        return columns

    def columns(self, connection, owner, payload):
        """All column values for a record; the owner fills a batch the payload omits."""
        values = self.split(connection, payload)
        for name, value in self.owner_columns(connection, owner).items():
            if values.get(name) is None:
                values[name] = value
        return values

    def owner_columns(self, connection, owner):
        """`batch_id` when the owner is a stored batch; nothing for other tables."""
        if self.batch is None:
            return {}
        found = connection.execute(
            select(self.batch.c.id).where(self.batch.c.id == owner)
        ).first()
        return {"batch_id": owner if found else None}

    def join(self, row):
        """The payload a row was written from."""
        extra = row[self.extra]
        payload = {
            field.key: field.from_db(row[field.column])
            for field in self.fields
            if row[field.column] is not None and field.key not in extra
        }
        for ref in self.refs:
            pair = ref.join(row)
            if pair is not None and ref.key not in extra:
                payload[ref.key] = pair
        return {**payload, **extra}

    def load(self, connection, rows):
        """Payloads for fetched rows, in order. Tables with child rows override it."""
        return [self.join(row) for row in rows]

    def after_insert(self, connection, key, payload):
        """Write rows derived from a newly inserted record. Nothing by default."""

    def _row(self, connection, key):
        row = connection.execute(self.statement().where(self.table.c.id == key)).first()
        return None if row is None else row._mapping

    def get(self, connection, key):
        row = self._row(connection, key)
        return None if row is None else self.load(connection, [row])[0]

    def put(
        self,
        connection,
        key,
        payload,
        owner="",
        kind="",
        immutable=False,
        created_at=None,
    ):
        existing = self._row(connection, key)
        if existing is not None:
            unchanged = self.load(connection, [existing])[0] == payload
            if immutable:
                if not unchanged:
                    raise ValueError(f"Immutable {self.name}/{key} already exists")
                return
            if self.append_only:
                if not unchanged:
                    raise ValueError(
                        f"{self.name}/{key} is append-only and already holds "
                        "a different record"
                    )
                return
            values = {
                "owner_id": owner,
                "kind": kind,
                **self.columns(connection, owner, payload),
            }
            # Writing the same record again changes nothing, not even a timestamp.
            if any(
                not same_column(existing[name], value) for name, value in values.items()
            ):
                connection.execute(
                    self.table.update().where(self.table.c.id == key).values(values)
                )
            return
        values = {"id": key, "owner_id": owner, "kind": kind}
        if created_at is not None:
            values["created_at"] = created_at
        inserted = connection.execute(
            insert(self.table)
            .values(**values, **self.columns(connection, owner, payload))
            # Only a concurrent insert of the same key is ignored; any other
            # uniqueness rule the record breaks is an error.
            .on_conflict_do_nothing(index_elements=["id"])
        ).rowcount
        if inserted:
            self.after_insert(connection, key, payload)

    def records(self, connection, owner=None, kind=None):
        """Records in the store's listing order: (id, owner, kind, payload, created_at)."""
        table = self.table
        statement = self.statement().order_by(table.c.created_at, table.c.id)
        if owner is not None:
            statement = statement.where(table.c.owner_id == owner)
        if kind is not None:
            statement = statement.where(table.c.kind == kind)
        rows = connection.execute(statement).mappings().all()
        for row, payload in zip(rows, self.load(connection, rows)):
            yield row["id"], row["owner_id"], row["kind"], payload, row["created_at"]

    def unresolved(self, connection):
        """Per field, the records whose value is not held in its typed column."""
        counts = {}
        for row in connection.execute(self.statement()).mappings():
            for field in self.fields:
                held_as_json = row[self.extra].get(field.key) is not None
                if held_as_json and row[field.column] is None:
                    counts[field.key] = counts.get(field.key, 0) + 1
        return counts
