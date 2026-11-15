"""Alerts to the team: one short message, naming the source and linking to the run.

An alert is posted to the incoming webhook in `LINK_LENS_ALERT_WEBHOOK_URL` as
`{"text": ...}`. Without one it is logged and not sent, so nothing is lost
silently and nothing fails. Sending never raises: an alert that cannot be
delivered must not stop the work it reports on. The webhook URL is never logged.
"""

import logging

import httpx

from . import logs
from .settings import settings

KINDS = {
    "run_failed": "Run failed",
    "check_failed": "Check failed",
    "drift": "Source drifted",
    "stale_source": "Source overdue",
    "budget": "Budget",
}


def message(kind, summary, source=None, link=None, details=None):
    """The text of an alert: what happened, to which source, and where to look."""
    if kind not in KINDS:
        raise ValueError(f"Unknown alert kind: {kind}")
    lines = [f"[Link Lens] {KINDS[kind]}: {summary}"]
    if source:
        lines.append(f"Source: {source}")
    for key, value in (details or {}).items():
        lines.append(f"{key}: {value}")
    if link:
        lines.append(link)
    return "\n".join(lines)


def send(kind, summary, source=None, link=None, details=None):
    """Post an alert. Returns whether it was delivered."""
    text = message(kind, summary, source, link, details)
    url = settings().alert_webhook_url
    fields = {"kind": kind, "source": source, "summary": summary[:200]}
    if not url:
        logs.event(
            "alert.unsent", logging.WARNING, reason="no webhook configured", **fields
        )
        return False
    try:
        response = httpx.post(url, json={"text": text}, timeout=10)
        response.raise_for_status()
    except httpx.HTTPError as error:
        logs.event(
            "alert.failed", logging.ERROR, error_type=type(error).__name__, **fields
        )
        return False
    logs.event("alert.sent", **fields)
    return True
