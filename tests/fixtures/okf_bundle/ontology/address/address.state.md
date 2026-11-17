---
type: Ontology Concept
title: address.state
description: The state or territory of an address.
generated:
  by: process:link-lens-exporter-1
  at: '2026-01-01T00:00:00+00:00'
tags:
- ontology
- address
ontology_hash: '0000000000000000000000000000000000000000000000000000000000000000'
---

# Definition

The state or territory of an address.

* Scope: address
* Type: enum
* Cardinality: one

# Allowed values

* NSW
* VIC

# Checks

* One of the allowed values. Applied by extraction.
* Stated outside any group. Applied by mapping validation.
* Kept with the other address fields of the same source record. Applied by profile assembly.
* Profiles choose one value, or none when equally authoritative claims disagree. Applied by profile assembly.
* The meaning in the definition, which a person checks when approving a mapping. No code checks this.
