"""Short-lived download links that the product service signs and serves itself.

A link is the artifact's hash and an expiry time, signed with a secret. Whoever
holds it can download that one artifact until it expires, without a key, the
way a link signed by an object store works.
"""

import base64
import hashlib
import hmac
import secrets
import time
from functools import lru_cache

from ..db import is_sha256
from ..settings import settings
from . import Problem


@lru_cache
def secret():
    configured = settings().link_secret
    return (configured or secrets.token_hex(32)).encode()


def signature(payload):
    return hmac.new(secret(), payload.encode(), hashlib.sha256).hexdigest()


def sign(sha, now=None):
    """A token for one artifact and the time it stops working."""
    expires = int(now or time.time()) + settings().link_ttl_seconds
    payload = f"{sha}.{expires}"
    token = base64.urlsafe_b64encode(f"{payload}.{signature(payload)}".encode())
    return token.decode().rstrip("="), expires


def verify(token, now=None):
    """The artifact a token names, if the token is genuine and still valid."""
    refused = Problem(404, "Not found", "The link is invalid or has expired.")
    try:
        decoded = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)).decode()
        sha, expires, signed = decoded.split(".")
        expires = int(expires)
    except ValueError as error:
        raise refused from error
    if not hmac.compare_digest(signed, signature(f"{sha}.{expires}")):
        raise refused
    if not is_sha256(sha) or expires < int(now or time.time()):
        raise refused
    return sha
