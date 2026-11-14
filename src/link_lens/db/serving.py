"""Tables of the `serving` schema that are built per release, and `ops.release`."""

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    Table,
    Text,
)

from .types import Sha256

release = Table(
    "release",
    MetaData(schema="ops"),
    Column("id", BigInteger, primary_key=True),
    Column("batch_id", Text),
    Column("ontology_hash", Sha256),
    Column("released_by", Text),
    Column("released_at", DateTime(timezone=True)),
    Column("notes", Text),
)
metadata = MetaData(schema="serving")
okf_page = Table(
    "okf_page",
    metadata,
    Column("release_id", BigInteger, primary_key=True),
    Column("path", Text, primary_key=True),
    Column("type", Text),
    Column("title", Text),
    Column("description", Text),
    Column("tags", ARRAY(Text)),
    Column("status", Text),
    Column("entity_id", Text),
    Column("source_id", Text),
    Column("observation_source_id", Text),
    Column("observation_id", Sha256),
    Column("concept_name", Text),
)
okf_line = Table(
    "okf_line",
    metadata,
    Column("release_id", BigInteger, primary_key=True),
    Column("path", Text, primary_key=True),
    Column("line_no", Integer, primary_key=True),
    Column("line", Text),
    Column("source_id", Text),
)
okf_index = Table(
    "okf_index",
    metadata,
    Column("release_id", BigInteger, primary_key=True),
    Column("parent", Text, primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("label", Text),
    Column("target", Text),
    Column("is_folder", Boolean),
    Column("entry_count", Integer),
    Column("description", Text),
    Column("source_id", Text),
)
