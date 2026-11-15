"""The source is the only partition dimension. A snapshot is metadata, not a partition."""

import dagster as dg

sources = dg.DynamicPartitionsDefinition(name="source")
