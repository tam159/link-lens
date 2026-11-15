"""What the product service reports about itself: a log line and metrics per request.

Each request gets an ID, returned as `X-Request-ID` and written to the log with
the route, the status, the time taken and who called: the key's prefix, the
client and the tier. The key itself is never logged. Metrics are counted per
interface, tier and status, in the Prometheus text format.
"""

import re
import threading
import time
import uuid

from .. import logs

REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
QUIET = ("/health", "/metrics")  # answered and counted, not logged


class Metrics:
    """Request counts and a latency histogram, per interface and tier."""

    def __init__(self):
        self.lock = threading.Lock()
        self.requests, self.buckets, self.seconds = {}, {}, {}

    def observe(self, interface, tier, status, seconds):
        with self.lock:
            key = (interface, tier, str(status))
            self.requests[key] = self.requests.get(key, 0) + 1
            series = (interface, tier)
            counts = self.buckets.setdefault(series, [0] * (len(BUCKETS) + 1))
            for position, bound in enumerate(BUCKETS):
                if seconds <= bound:
                    counts[position] += 1
            counts[-1] += 1
            self.seconds[series] = self.seconds.get(series, 0.0) + seconds

    def render(self):
        """The metrics in the Prometheus text exposition format."""
        with self.lock:
            lines = [
                "# HELP linklens_requests_total Requests answered.",
                "# TYPE linklens_requests_total counter",
            ]
            for (interface, tier, status), count in sorted(self.requests.items()):
                labels = f'interface="{interface}",tier="{tier}",status="{status}"'
                lines.append(f"linklens_requests_total{{{labels}}} {count}")
            lines += [
                "# HELP linklens_request_seconds Time to answer a request.",
                "# TYPE linklens_request_seconds histogram",
            ]
            for (interface, tier), counts in sorted(self.buckets.items()):
                labels = f'interface="{interface}",tier="{tier}"'
                for bound, count in zip([*BUCKETS, "+Inf"], counts, strict=True):
                    lines.append(
                        f'linklens_request_seconds_bucket{{{labels},le="{bound}"}} {count}'
                    )
                total = self.seconds[interface, tier]
                lines.append(f"linklens_request_seconds_sum{{{labels}}} {total:.6f}")
                lines.append(f"linklens_request_seconds_count{{{labels}}} {counts[-1]}")
            return "\n".join(lines) + "\n"


metrics = Metrics()


def label(value):
    """A tier name as a label value: nothing that could break the format."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(value))[:64]


def interface_of(path):
    if path.startswith("/v1"):
        return "rest"
    if path.startswith("/mcp"):
        return "mcp"
    return "other"


class Observe:
    """ASGI middleware: an ID, a log line and a metric for every HTTP request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope["headers"])
        given = headers.get(b"x-request-id", b"").decode("latin-1")
        request_id = given if REQUEST_ID.match(given) else uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id
        started, status = time.perf_counter(), [500]

        async def reply(message):
            if message["type"] == "http.response.start":
                status[0] = message["status"]
                message.setdefault("headers", []).append(
                    (b"x-request-id", request_id.encode("latin-1"))
                )
            await send(message)

        try:
            await self.app(scope, receive, reply)
        finally:
            seconds = time.perf_counter() - started
            state, path = scope.get("state", {}), scope["path"]
            principal = state.get("principal")
            interface = interface_of(path)
            tier = label(principal.tier) if principal else "none"
            metrics.observe(interface, tier, status[0], seconds)
            if path not in QUIET:
                route = getattr(scope.get("route"), "path", None)
                if route is None:
                    # An MCP mount is a fixed path; anything else matched no route.
                    route = path if interface == "mcp" else "unmatched"
                logs.event(
                    "request",
                    request_id=request_id,
                    interface=interface,
                    method=scope["method"],
                    # The route as declared, so an ID in a path is not a label.
                    route=route,
                    status=status[0],
                    ms=round(seconds * 1000, 1),
                    key_prefix=principal.key_prefix if principal else None,
                    client_id=principal.client_id if principal else None,
                    tier=principal.tier if principal else None,
                    **({"tool": state["tool"]} if state.get("tool") else {}),
                )
