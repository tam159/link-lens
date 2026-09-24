"""Rate-limited progress on stderr; final CLI JSON remains machine-readable."""

import json
import sys
import time
from threading import Lock


class Progress:
    def __init__(self, enabled=True, interval=5):
        self.enabled = enabled
        self.interval = interval
        self.started = time.monotonic()
        self.last = {}
        self.lock = Lock()

    def __call__(self, stage, **details):
        if not self.enabled:
            return
        force = details.pop("force", False)
        with self.lock:
            now = time.monotonic()
            if not force and now - self.last.get(stage, -1e9) < self.interval:
                return
            self.last[stage] = now
            detail = " ".join(
                f"{key}={json.dumps(value, ensure_ascii=False)}"
                for key, value in details.items()
            )
            print(
                f"[enhance +{now - self.started:.0f}s] {stage} {detail}",
                file=sys.stderr,
                flush=True,
            )
