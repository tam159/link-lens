"""Dagster code location for Link Lens.

Dagster runs the deterministic data flow by calling the `link_lens` library. It
holds no pipeline logic of its own, keeps no copy of application state, and
never records a mapping approval, an ontology promotion or a release: those
are a person's decisions, and Dagster only reacts to their rows.
"""
