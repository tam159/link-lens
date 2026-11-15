"""Column types shared by the typed schemas."""

import re

from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.types import TypeDecorator

_HEX = re.compile(r"[0-9a-f]{64}\Z")


def is_sha256(value):
    """Whether a value is a digest in the only form the store accepts."""
    return isinstance(value, str) and _HEX.match(value) is not None


class Sha256(TypeDecorator):
    """The `sha256` domain: 32 bytes in PostgreSQL, a 64-character hex string in Python.

    Only lowercase hex is accepted, so a value read back always equals the value
    written and existing IDs keep their exact text.
    """

    impl = BYTEA
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not is_sha256(value):
            raise ValueError("sha256 value must be 64 lowercase hex characters")
        return bytes.fromhex(value)

    def process_result_value(self, value, dialect):
        return None if value is None else bytes(value).hex()
