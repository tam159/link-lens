"""Column types shared by the typed schemas."""

import re

from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.types import TypeDecorator

_HEX = re.compile(r"[0-9a-f]{64}\Z")


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
        if not isinstance(value, str) or not _HEX.match(value):
            raise ValueError("sha256 value must be 64 lowercase hex characters")
        return bytes.fromhex(value)

    def process_result_value(self, value, dialect):
        return None if value is None else bytes(value).hex()
