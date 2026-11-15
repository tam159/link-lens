"""Structured logs: one JSON object per line on standard error.

Command results still go to standard output. Log lines are for whoever runs the
command, a person or an orchestrator: what ran, how it ended and how long it
took. Fields are passed explicitly; nothing is logged that a caller did not name.
"""

import json
import logging
import sys
from datetime import UTC, datetime

logger = logging.getLogger("link_lens")
# Messages of these errors are written by this code base and are safe to show.
# Other errors may quote a provider response or a request, so only their type is logged.
PLAIN_ERRORS = (ValueError, KeyError, FileNotFoundError)


class JsonLines(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {
                "at": datetime.fromtimestamp(record.created, UTC).isoformat(),
                "level": record.levelname.lower(),
                "event": record.getMessage(),
                **getattr(record, "fields", {}),
            },
            default=str,
        )


def configure():
    """Send link_lens log records to standard error as JSON lines, once."""
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonLines())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False


def event(name, level=logging.INFO, **fields):
    logger.log(level, name, extra={"fields": fields})


def error_fields(error):
    fields = {"error_type": type(error).__name__}
    if isinstance(error, PLAIN_ERRORS):
        fields["error"] = str(error)[:500]
    return fields
