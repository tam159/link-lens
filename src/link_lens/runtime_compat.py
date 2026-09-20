"""Narrow compatibility guards for the locked Agent Server development runtime.

runtime-inmem 0.34.1 registers temporary serializer saver dictionaries over the
shared saver entries, then discards them. Re-register the actual shared dictionaries.
Remove null optional command keys: LangGraph 1.2 expects goto to be iterable.
"""

import json


def install_checkpoint_flush_guard():
    from langgraph_runtime_inmem import checkpoint
    from langgraph_runtime_inmem._persistence import register_persistent_dict

    original = checkpoint.Checkpointer
    if getattr(original, "_link_lens_guard", False):
        return

    def guarded(*args, **kwargs):
        saver = original(*args, **kwargs)
        for field in ("storage", "writes", "blobs"):
            value = getattr(saver, field)
            if hasattr(value, "filename"):
                register_persistent_dict(value)
        return saver

    guarded._link_lens_guard = True
    checkpoint.Checkpointer = guarded


class ResumeCompatibilityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] == "http"
            and scope["method"] == "POST"
            and "/runs" in scope["path"]
        ):
            chunks = []
            while True:
                message = await receive()
                chunks.append(message.get("body", b""))
                if not message.get("more_body"):
                    break
            body = b"".join(chunks)
            try:
                value = json.loads(body)
                if isinstance(value.get("command"), dict):
                    value["command"] = {
                        k: v for k, v in value["command"].items() if v is not None
                    }
                    value["command"].setdefault("goto", [])
                    body = json.dumps(value).encode()
            except (ValueError, AttributeError):
                pass
            scope = {
                **scope,
                "headers": [
                    (k, v) for k, v in scope["headers"] if k != b"content-length"
                ]
                + [(b"content-length", str(len(body)).encode())],
            }
            delivered = False

            async def replacement():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": body, "more_body": False}
                return await receive()

            await self.app(scope, replacement, send)
        else:
            await self.app(scope, receive, send)
