import json
import pytest
from link_lens.runtime_compat import ResumeCompatibilityMiddleware


@pytest.mark.asyncio
async def test_native_inbox_null_goto_normalized():
    captured = {}

    async def app(scope, receive, send):
        captured.update(json.loads((await receive())["body"]))

    async def receive():
        return {
            "type": "http.request",
            "body": json.dumps(
                {
                    "command": {
                        "resume": [{"type": "accept", "args": None}],
                        "goto": None,
                        "update": None,
                    }
                }
            ).encode(),
        }

    async def send(message):
        pass

    await ResumeCompatibilityMiddleware(app)(
        {
            "type": "http",
            "method": "POST",
            "path": "/threads/test/runs/stream",
            "headers": [],
        },
        receive,
        send,
    )
    assert captured["command"] == {
        "resume": [{"type": "accept", "args": None}],
        "goto": [],
    }


def test_flush_registry_references_shared_saver(monkeypatch):
    import gc
    import weakref
    from types import SimpleNamespace
    from langgraph_runtime_inmem import checkpoint, _persistence
    from link_lens.runtime_compat import install_checkpoint_flush_guard

    class Dictionary(dict):
        def __init__(self, name):
            super().__init__({"live": True})
            self.filename = name

    shared = SimpleNamespace(
        **{k: Dictionary(k) for k in ("storage", "writes", "blobs")}
    )
    registry = {}

    def register(d):
        registry[d.filename] = weakref.ref(d)

    def factory(*args, **kwargs):
        for key in ("storage", "writes", "blobs"):
            register(Dictionary(key))
        return shared

    monkeypatch.setattr(checkpoint, "Checkpointer", factory)
    monkeypatch.setattr(_persistence, "register_persistent_dict", register)
    install_checkpoint_flush_guard()
    checkpoint.Checkpointer(unpack_hook=object())
    gc.collect()
    assert all(registry[k]() is getattr(shared, k) for k in registry)
