import re
from datetime import datetime, timezone
from functools import lru_cache
import yaml
from .contracts import MappingSpec, content_hash
from .settings import settings

ENGINE_VERSION = "extractor-1"


def valid_abn(value):
    if not re.fullmatch("[0-9]{11}", value) or value == "00000000000":
        return False
    digits = list(map(int, value))
    digits[0] -= 1
    return (
        sum(d * w for d, w in zip(digits, [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19])) % 89
        == 0
    )


def valid_acn(value):
    return (
        bool(re.fullmatch("[0-9]{9}", value))
        and value != "000000000"
        and (10 - sum(int(d) * w for d, w in zip(value[:8], range(8, 0, -1))) % 10) % 10
        == int(value[-1])
    )


def condition(row, rule):
    value = str(row.get(rule.field, "")).strip()
    if rule.op == "in":
        return value in rule.values
    if rule.op == "not_in":
        return value not in rule.values
    if rule.op == "nonempty":
        return bool(value)
    if rule.op == "length":
        return len(value) == rule.length
    return False


def operation(value, op):
    if op.op == "constant":
        return op.argument
    if value is None:
        return None
    if op.op == "join":
        return (
            (op.argument or " ").join(str(v).strip() for v in value if str(v).strip())
            if isinstance(value, list)
            else value
        )
    if isinstance(value, list):
        return [operation(v, op) for v in value]
    value = str(value).strip()
    if not value:
        return None
    if op.op == "trim":
        return value
    if op.op == "uppercase":
        return value.upper()
    if op.op == "lowercase":
        return value.lower()
    if op.op == "digits":
        # Formatting removal only: do not turn scientific notation into an identifier.
        if re.search("[^0-9 -]", value):
            raise ValueError("Identifier contains non-formatting characters")
        return re.sub("[ -]", "", value)
    if op.op in ("abn", "acn"):
        value = re.sub(r"[ -]", "", value)
        if value == "0":
            return None
        if op.op == "abn" and value.startswith("911111111"):
            raise ValueError("Pseudo-ABN used by ACNC reporting groups")
        # Mixed ABN/ACN source columns can map to both fields without falsifying either.
        if op.op == "abn" and len(value) == 9 and valid_acn(value):
            return None
        if op.op == "acn" and len(value) == 11 and valid_abn(value):
            return None
        if not (valid_abn(value) if op.op == "abn" else valid_acn(value)):
            raise ValueError(f"Invalid {op.op} checksum or shape")
        return value
    if op.op == "nzbn":
        if not re.fullmatch("[0-9]{13}", value):
            raise ValueError("Invalid NZBN shape")
        return value
    if op.op == "date":
        return datetime.strptime(value, op.argument or "%d/%m/%Y").date().isoformat()
    if op.op == "enum":
        if value not in op.values:
            raise ValueError("Unmapped enum value")
        return op.values[value]
    if op.op == "split":
        return [s.strip() for s in value.split(op.argument or ";") if s.strip()]
    if op.op == "postcode":
        if not re.fullmatch("[0-9]{4}", value):
            raise ValueError(
                "Postcode is not four preserved digits; do not invent leading zeros"
            )
        return value
    if op.op == "website":
        if not re.fullmatch(r"(https?://)?[A-Za-z0-9][^\s<>]*\.[^\s<>]+", value):
            raise ValueError("Unrecognised website representation")
        return value  # no invented scheme and no claim the site was verified live
    raise ValueError("Unsupported operation")


@lru_cache
def ontology():
    return yaml.safe_load(settings().ontology_path.read_text())


def timestamp(raw, fmt=None):
    value = (
        datetime.strptime(raw, fmt)
        if fmt
        else datetime.fromisoformat(raw.replace("Z", "+00:00"))
    )
    assumed = value.tzinfo is None
    if assumed:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(), assumed


def extract(spec: MappingSpec, rows, snapshot):
    observations = []
    issues = []
    skipped = []
    candidates = []
    digest = content_hash(spec)
    for row in rows:
        values = row["values"]
        ref = {"source_id": snapshot["source_id"], "source_record_id": row["record_id"]}
        if not all(condition(values, f) for f in spec.filters):
            skipped.append(
                {**ref, "reason": "Row does not satisfy approved config filters"}
            )
            continue
        candidates.append(
            {
                **ref,
                "subject_role": spec.subject_role,
                "label": values.get(spec.subject_label_field or ""),
                "raw_locator": row["locator"],
            }
        )
        raw_time = (
            values.get(spec.observed_at_field or "")
            if spec.timestamp_policy == "record_statement_else_publication"
            else None
        )
        basis = (
            "source record statement field"
            if raw_time
            else snapshot["observed_at_basis"]
        )
        raw_time = raw_time or snapshot.get("observed_at")
        try:
            if not raw_time:
                raise ValueError("No defensible source publication/statement timestamp")
            observed_at, assumed = timestamp(
                raw_time,
                spec.observed_at_format
                if basis == "source record statement field"
                else None,
            )
        except ValueError as exc:
            issues.append({**ref, "kind": "record_quarantine", "reason": str(exc)})
            continue
        for field in spec.fields:
            if not all(condition(values, c) for c in field.when):
                continue
            raw = [values.get(s, "") for s in field.source_fields]
            value = raw[0] if len(raw) == 1 else raw
            try:
                for op in field.transformations:
                    if value is None:
                        break
                    value = operation(value, op)
                result = value if isinstance(value, list) else [value]
                for v in result:
                    if v is None or v == "":
                        continue
                    group, key = field.canonical_field.split(".")
                    contract = ontology()[group][key]
                    if contract["type"] == "enum" and v not in contract["values"]:
                        raise ValueError("Value outside ontology enum")
                    if not isinstance(v, str):
                        raise ValueError("Canonical scalar must be a string")
                    if key == "abn" and not valid_abn(v):
                        raise ValueError("ABN target requires checksum validation")
                    if key == "acn" and not valid_acn(v):
                        raise ValueError("ACN target requires checksum validation")
                    if key == "nzbn" and not re.fullmatch("[0-9]{13}", v):
                        raise ValueError("Invalid NZBN")
                    if contract["type"] == "date":
                        datetime.strptime(v, "%Y-%m-%d")
                    observation = {
                        **ref,
                        "observed_at": observed_at,
                        "observed_at_basis": basis,
                        "timezone_assumption": "UTC assumed for timezone-naive source timestamp"
                        if assumed
                        else None,
                        "ingested_at": snapshot["receipt"]["retrieved_at"],
                        "licence": snapshot["licence"],
                        "extractor_version": ENGINE_VERSION + ":" + digest,
                        "field": field.canonical_field,
                        "value": v,
                        "source_fields": field.source_fields,
                        "raw_value": raw,
                        "raw_locator": row["locator"],
                        "snapshot_id": snapshot["id"],
                        "config_hash": digest,
                        "subject_role": spec.subject_role,
                        "source_kind": spec.source_kind,
                        "address_role": spec.address_role,
                        "confidence": {
                            "source_reliability": spec.source_reliability,
                            "field_confidence": field.confidence,
                        },
                        "confidence_kind": "uncalibrated mapping/source judgements",
                        "derivation_level": "L1",
                    }
                    observation["id"] = content_hash(observation)
                    observations.append(observation)
            except (ValueError, TypeError) as exc:
                issues.append(
                    {
                        **ref,
                        "kind": "field_quarantine",
                        "field": field.canonical_field,
                        "raw_value": raw,
                        "reason": str(exc),
                    }
                )
    return {
        "observations": observations,
        "issues": issues,
        "skipped": skipped,
        "candidates": candidates,
    }


def validate(spec, headers, rows, snapshot):
    blocking = []
    used = {s for f in spec.fields for s in f.source_fields}
    referenced = (
        used
        | {c.field for c in spec.filters}
        | {c.field for f in spec.fields for c in f.when}
    )
    if spec.subject_label_field:
        referenced.add(spec.subject_label_field)
    if spec.observed_at_field:
        referenced.add(spec.observed_at_field)
    missing = referenced - set(headers)
    if missing:
        blocking.append("Referenced columns absent: " + ", ".join(sorted(missing)))
    omitted = set(headers) - used - {u.source_field for u in spec.unmapped_fields}
    if omitted:
        blocking.append(
            "Every unused column must be listed unmapped: " + ", ".join(sorted(omitted))
        )
    if {u.source_field for u in spec.unmapped_fields} - set(headers):
        blocking.append("Unmapped list contains nonexistent columns")
    if not rows:
        blocking.append("Empty partition: independent validation is not established")
    result = (
        extract(spec, rows, snapshot)
        if not missing
        else {"observations": [], "issues": [], "skipped": [], "candidates": []}
    )
    if rows and not result["observations"]:
        blocking.append("No canonical observations emitted")
    if any(i["kind"] == "record_quarantine" for i in result["issues"]):
        blocking.append("Records have no usable source timestamp")
    return {
        "passed": not blocking,
        "blocking_issues": blocking,
        "records": len(rows),
        "observations": len(result["observations"]),
        "quarantined_fields": len(result["issues"]),
        "filtered_records": len(result["skipped"]),
        "error_examples": result["issues"][:8],
        "output_examples": result["observations"][:8],
        "quality_note": "Parse/type validation is not semantic ground truth or measured link precision.",
    }
