"""Seeded human review, explicit unknowns, and reproducible denominators."""

import random
from . import store
from .contracts import ReviewLabel, content_hash


def worksheet(kind, batch_id="discovery", seed=159):
    batch = store.require("batches", batch_id)
    items = (
        batch["shortlist"]
        if kind == "triage"
        else store.read_json(batch["result_artifact"])["links"]
    )
    size = 20 if kind == "triage" else 50
    if len(items) < size:
        raise ValueError(f"Requires at least {size} {kind} items")
    selected = random.Random(seed).sample(
        sorted(items, key=lambda x: x.get("dataset_id", x.get("id"))), size
    )
    packet = {
        "kind": kind,
        "batch_id": batch_id,
        "seed": seed,
        "sampling": "Seeded simple random sample without replacement",
        "threshold": None if kind == "triage" else 0.99,
        "items": [
            {
                "item_id": i.get("dataset_id", i.get("id")),
                "evidence_to_review": i,
                "verdict": "",
                "reviewer": "",
                "evidence": "",
            }
            for i in selected
        ],
    }
    packet["id"] = content_hash({"kind": kind, "batch_id": batch_id, "seed": seed})
    store.put(
        "evaluations", packet["id"], packet, batch_id, "worksheet", immutable=True
    )
    return packet


def import_labels(worksheet_id, labels, *, reviewed=True, review_note=None):
    if not reviewed and not review_note:
        raise ValueError("Unreviewed responses require an explanation")
    sheet = store.require("evaluations", worksheet_id)
    allowed = {i["item_id"] for i in sheet["items"]}
    parsed = [ReviewLabel.model_validate(row) for row in labels]
    if len({p.item_id for p in parsed}) != len(parsed):
        raise ValueError("Duplicate item labels")
    if any(p.item_id not in allowed for p in parsed):
        raise ValueError("Label is outside this review worksheet")
    for label in parsed:
        value = {
            **label.model_dump(),
            "worksheet_id": worksheet_id,
            "labelled_at": store.now(),
            "reviewed": reviewed,
            "review_note": review_note,
        }
        # Retain revisions as separate events, current label is an explicit materialization.
        store.event(worksheet_id, "human_label", value)
        store.put(
            "evaluations",
            content_hash([worksheet_id, label.item_id]),
            value,
            worksheet_id,
            "human_label",
        )
    return report(worksheet_id)


def report(worksheet_id):
    sheet = store.require("evaluations", worksheet_id)
    labels = store.listing("evaluations", owner=worksheet_id, kind="human_label")
    verified = [label for label in labels if label.get("reviewed", True)]
    yes = sum(l["verdict"] == "yes" for l in verified)
    no = sum(l["verdict"] == "no" for l in verified)
    denominator = len(sheet["items"])
    resolved = yes + no
    return {
        "worksheet_id": worksheet_id,
        "kind": sheet["kind"],
        "sampling": sheet["sampling"],
        "seed": sheet["seed"],
        "threshold": sheet["threshold"],
        "sample_size": denominator,
        "submitted_responses": len(labels),
        "unreviewed_responses": len(labels) - len(verified),
        "evaluation_note": "Only evidence-reviewed labels count. Unreviewed selections remain unresolved.",
        "correct_or_relevant": yes,
        "incorrect_or_irrelevant": no,
        "unresolved": denominator - resolved,
        "reviewed_resolved": resolved,
        "precision_on_resolved": yes / resolved if resolved else None,
        "false_positive_rate_on_resolved": no / resolved if resolved else None,
        "confirmed_fraction_of_full_sample": yes / denominator,
        "status": "complete"
        if resolved == denominator
        else "incomplete; unknowns are not counted as correct",
    }


def import_ai_labels(worksheet_id, labels, *, evidence_artifact):
    """Keep assistant judgments in a separate namespace from human ground truth."""
    store.blob_path(evidence_artifact)
    sheet = store.require("evaluations", worksheet_id)
    allowed = {i["item_id"] for i in sheet["items"]}
    parsed = [ReviewLabel.model_validate(row) for row in labels]
    if len({p.item_id for p in parsed}) != len(parsed):
        raise ValueError("Duplicate item labels")
    if any(p.item_id not in allowed for p in parsed):
        raise ValueError("Label is outside this review worksheet")
    for label in parsed:
        value = {
            **label.model_dump(),
            "worksheet_id": worksheet_id,
            "review_type": "ai_assisted",
            "labelled_at": store.now(),
            "evidence_artifact": evidence_artifact,
        }
        store.event(worksheet_id, "ai_label", value)
        store.put(
            "evaluations",
            content_hash(["ai_label", worksheet_id, label.item_id]),
            value,
            worksheet_id,
            "ai_label",
        )
    return ai_report(worksheet_id)


def ai_report(worksheet_id):
    sheet = store.require("evaluations", worksheet_id)
    labels = store.listing("evaluations", owner=worksheet_id, kind="ai_label")
    yes = sum(l["verdict"] == "yes" for l in labels)
    no = sum(l["verdict"] == "no" for l in labels)
    total = len(sheet["items"])
    return {
        "worksheet_id": worksheet_id,
        "kind": sheet["kind"],
        "review_type": "ai_assisted",
        "sample_size": total,
        "sampling": sheet["sampling"],
        "seed": sheet["seed"],
        "threshold": sheet["threshold"],
        "assessed": len(labels),
        "supported": yes,
        "not_supported": no,
        "unresolved": total - yes - no,
        "resolved_denominator": yes + no,
        "support_fraction_on_resolved": yes / (yes + no) if yes + no else None,
        "negative_fraction_on_resolved": no / (yes + no) if yes + no else None,
        "human_requirement_satisfied": False,
        "limitation": "Assistant evidence audit; not human ground truth or measured human precision. Shared source errors and selection bias remain possible.",
    }
