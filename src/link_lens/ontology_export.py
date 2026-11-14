"""Export an ontology version to LinkML, and from LinkML to SHACL and JSON Schema.

The registry is the source of truth; these files are generated views of one
version. The LinkML schema is plain data and needs no extra package. SHACL,
JSON Schema and linting use the `linkml` package from the `ontology` dependency
group (`uv sync --group ontology`), which the runtime image does not install.
"""

import re
import tempfile
from pathlib import Path

import yaml

# Placeholder namespace on a reserved example domain. Class and attribute IRIs in
# the generated SHACL start with it, so the owner must choose the real namespace
# before any client depends on those IRIs.
BASE = "https://linklens.example/ontology/"
RANGES = {
    "string": "string",
    "date": "date",
    "boolean": "boolean",
    "integer": "integer",
    "decimal": "decimal",
}
SCOPE_DESCRIPTIONS = {
    "entity": "A legal entity or other subject a source makes claims about.",
    "address": "An address as one source record states it; its fields stay together.",
    "service_location": "A place where a subject delivers a service.",
    "contact": "A contact point a source lists for a record.",
    "licence": "A licence or authorisation a source records for a subject.",
    "registration": "A registration a source records for a subject.",
    "financial_period": "Figures a source reports for one reporting period.",
}


def camel(text):
    return "".join(
        part.capitalize() for part in re.split(r"[^A-Za-z0-9]+", text) if part
    )


def number(bound):
    """A stored bound as a YAML number; integers stay integers."""
    return int(bound) if re.fullmatch(r"[+-]?\d+", bound) else float(bound)


def attribute_name(name, scope):
    """The concept's name inside its class: local when the namespace is the scope."""
    namespace, local = name.split(".", 1)
    return local if namespace == scope else f"{namespace}_{local}"


def linkml(document, ontology_hash):
    """The LinkML schema for one ontology version, as a dictionary.

    Scope becomes a class, a concept an attribute of that class, an enum concept
    a LinkML enum, `many` becomes `multivalued`, bounds become `minimum_value`
    and `maximum_value`, and the definition becomes the description. The
    `ConceptName` enum lists every concept, and `Observation` is one source claim
    about one of them.
    """
    concepts = document["concepts"]
    classes, enums = {}, {}
    for name, concept in concepts.items():
        attribute = {
            "description": concept["definition"],
            "range": RANGES.get(concept["type"]),
            "annotations": {"concept": name},
        }
        if concept["type"] == "enum":
            enum = camel(name) + "Value"
            enums[enum] = {
                "description": f"Values the ontology allows for {name}.",
                "permissible_values": {
                    value: {"description": f"{name} is {value}."}
                    for value in concept["values"]
                },
            }
            attribute["range"] = enum
        if concept["cardinality"] == "many":
            attribute["multivalued"] = True
        if concept["minimum"] is not None:
            attribute["minimum_value"] = number(concept["minimum"])
        if concept["maximum"] is not None:
            attribute["maximum_value"] = number(concept["maximum"])
        if concept["requires"]:
            attribute["annotations"]["requires"] = ", ".join(concept["requires"])
        scope = concept["scope"]
        classes.setdefault(
            camel(scope),
            {
                "description": SCOPE_DESCRIPTIONS.get(
                    scope, f"Claims in the {scope} scope."
                ),
                "attributes": {},
            },
        )["attributes"][attribute_name(name, scope)] = attribute

    enums["ConceptName"] = {
        "description": "Every concept of this ontology version.",
        "permissible_values": {
            name: {"description": concept["definition"]}
            for name, concept in concepts.items()
        },
    }
    classes["Observation"] = {
        "description": "One source claim: a concept and the value the source states.",
        "attributes": {
            "concept": {
                "description": "The concept the claim is about.",
                "range": "ConceptName",
                "required": True,
            },
            "value": {
                "description": "The value after the mapping's declared transformations.",
                "range": "string",
            },
        },
    }
    return {
        "id": BASE + ontology_hash,
        "name": "link_lens_ontology",
        "title": "Link Lens ontology " + document["version"],
        "description": (
            "Generated from the Link Lens ontology registry. Do not edit: change "
            "the ontology through a proposal and export it again."
        ),
        "version": document["version"],
        "annotations": {
            "ontology_hash": ontology_hash,
            "parent_hash": document["parent_hash"] or "",
        },
        "prefixes": {"linkml": "https://w3id.org/linkml/", "linklens": BASE},
        "default_prefix": "linklens",
        "default_range": "string",
        "imports": ["linkml:types"],
        "classes": classes,
        "enums": enums,
    }


def linkml_yaml(document, ontology_hash):
    return yaml.safe_dump(
        linkml(document, ontology_hash), sort_keys=False, allow_unicode=True, width=100
    )


def shacl(document, ontology_hash):
    from linkml.generators.shaclgen import ShaclGenerator

    return ShaclGenerator(linkml_yaml(document, ontology_hash)).serialize()


def json_schema(document, ontology_hash):
    from linkml.generators.jsonschemagen import JsonSchemaGenerator

    return JsonSchemaGenerator(
        linkml_yaml(document, ontology_hash), top_class="Observation"
    ).serialize()


# The same rules as `.linkmllint.yaml` in the repository root. Permissible values
# are data: concept names as registered and register values as published, so
# they keep their exact text and are exempt from naming conventions.
LINT_CONFIG = {
    "extends": "recommended",
    "rules": {
        "standard_naming": {
            "level": "warning",
            "exclude_type": ["permissible_value"],
        }
    },
}


def lint(schema_yaml):
    """Problems `linkml-lint` reports for a schema, warnings included."""
    from linkml.linter.linter import Linter

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "ontology.linkml.yaml"
        path.write_text(schema_yaml)
        return [
            {"level": str(p.level), "rule": p.rule_name, "message": p.message}
            for p in Linter(LINT_CONFIG).lint(str(path))
        ]


FORMATS = {"linkml": linkml_yaml, "shacl": shacl, "jsonschema": json_schema}
